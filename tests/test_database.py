"""Integration tests for concurrent database writes and transaction rollbacks."""

import asyncio
import os
import unittest
from pathlib import Path
from database.connection import DatabaseManager
from repositories.guild_repository import GuildRepository


class TestDatabaseTransactions(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.db_path = Path("tests/test_database.db")
        # Ensure clean state
        if self.db_path.exists():
            os.remove(self.db_path)

        self.db = DatabaseManager(self.db_path)
        await self.db.connect()

        # Run initialization schema
        await self.db.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await self.db.commit()

        self.guild_repo = GuildRepository(self.db)

    async def asyncTearDown(self) -> None:
        await self.db.disconnect()
        if self.db_path.exists():
            os.remove(self.db_path)

    async def test_concurrent_database_writes(self) -> None:
        """Verify that concurrent writes don't interleave or corrupt transaction boundaries."""
        async def insert_task(guild_id: int, name: str, should_fail: bool):
            try:
                async with self.db.transaction():
                    await self.db.execute(
                        "INSERT INTO guilds (id, name) VALUES (?, ?);", (guild_id, name)
                    )
                    await asyncio.sleep(0.05)  # Simulate other async processing
                    if should_fail:
                        raise ValueError("Simulated write failure")
            except ValueError:
                pass

        # Dispatch 5 concurrent tasks where some succeed and others fail
        tasks = [
            insert_task(1, "Guild One", False),
            insert_task(2, "Guild Two", True),  # Rollback
            insert_task(3, "Guild Three", False),
            insert_task(4, "Guild Four", True),   # Rollback
            insert_task(5, "Guild Five", False),
        ]
        await asyncio.gather(*tasks)

        # Query written records
        cursor = await self.db.execute("SELECT id, name FROM guilds ORDER BY id;")
        rows = await cursor.fetchall()

        # Should only contain 1, 3, 5. IDs 2 and 4 should be cleanly rolled back!
        written_ids = [r[0] for r in rows]
        self.assertEqual(written_ids, [1, 3, 5])

    async def test_transaction_rollback_integrity(self) -> None:
        """Verify that nested savepoint rollbacks don't corrupt the main transaction."""
        async with self.db.transaction():
            # Main insert
            await self.db.execute("INSERT INTO guilds (id, name) VALUES (?, ?);", (10, "Parent Guild"))
            
            try:
                # Nested savepoint transaction
                async with self.db.transaction():
                    await self.db.execute("INSERT INTO guilds (id, name) VALUES (?, ?);", (11, "Nested Guild"))
                    raise ValueError("Nested transaction rollback trigger")
            except ValueError:
                pass

            # Insert another on parent
            await self.db.execute("INSERT INTO guilds (id, name) VALUES (?, ?);", (12, "Another Parent Guild"))

        # Verify database contents
        cursor = await self.db.execute("SELECT id, name FROM guilds ORDER BY id;")
        rows = await cursor.fetchall()
        written_ids = [r[0] for r in rows]

        # 10 and 12 should persist, 11 must be rolled back!
        self.assertEqual(written_ids, [10, 12])
