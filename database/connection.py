"""Database connection, pool, and transaction lifecycle manager for NoSpaceFGK.

Handles async context bindings, WAL mode enablement, PRAGMA setup,
and execution queries via aiosqlite, with strict thread-safe transaction isolation.
"""

import asyncio
import contextvars
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, Optional
import aiosqlite
from utils.logger import logger

# Context Variable to track the active transaction context within the current async Task
_active_transaction: contextvars.ContextVar[Optional['TransactionContext']] = contextvars.ContextVar("_active_transaction", default=None)


class TransactionContext:
    """Async context manager representing a transaction block (main or nested savepoint)."""

    def __init__(self, db_manager: 'DatabaseManager') -> None:
        self.db = db_manager
        self.token: Optional[contextvars.Token] = None
        self.savepoint_name: Optional[str] = None

    async def __aenter__(self) -> 'TransactionContext':
        parent_tx = _active_transaction.get()

        if parent_tx is None:
            # 1. Main transaction: Acquire write lock first to serialize writes across all async tasks
            await self.db._write_lock.acquire()
            logger.info("Database Transaction: [START] BEGIN TRANSACTION.")
            try:
                await self.db.connection.execute("BEGIN TRANSACTION;")
            except Exception as e:
                self.db._write_lock.release()
                raise e
            self.token = _active_transaction.set(self)
        else:
            # 2. Nested transaction: Utilize SQLite SAVEPOINTs to prevent transaction boundaries pollution
            self.savepoint_name = f"sp_{uuid.uuid4().hex}"
            logger.info(f"Database Transaction: [START] NESTED SAVEPOINT {self.savepoint_name}.")
            await self.db.connection.execute(f"SAVEPOINT {self.savepoint_name};")
            self.token = _active_transaction.set(self)

        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.token:
            _active_transaction.reset(self.token)

        try:
            if exc_type is not None:
                # Rollback on exception
                if self.savepoint_name:
                    logger.warning(f"Database Transaction: [ROLLBACK] Reverting nested savepoint {self.savepoint_name} due to: {exc_val}")
                    await self.db.connection.execute(f"ROLLBACK TO SAVEPOINT {self.savepoint_name};")
                    await self.db.connection.execute(f"RELEASE SAVEPOINT {self.savepoint_name};")
                else:
                    logger.warning(f"Database Transaction: [ROLLBACK] Reverting main transaction due to: {exc_val}")
                    await self.db.connection.execute("ROLLBACK;")
            else:
                # Commit on success
                if self.savepoint_name:
                    logger.info(f"Database Transaction: [COMMIT] Releasing nested savepoint {self.savepoint_name}.")
                    await self.db.connection.execute(f"RELEASE SAVEPOINT {self.savepoint_name};")
                else:
                    logger.info("Database Transaction: [COMMIT] Committing main transaction.")
                    await self.db.connection.execute("COMMIT;")
        finally:
            if not self.savepoint_name:
                # Release lock at the end of the main transaction
                self.db._write_lock.release()


class DatabaseManager:
    """Manages SQLite connections, query isolation, and transaction scoping."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the database manager.

        Args:
            db_path: Path where the SQLite file will reside.
        """
        self.db_path: Path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._write_lock: asyncio.Lock = asyncio.Lock()

    async def connect(self) -> None:
        """Open the SQLite connection, create folders, and configure WAL/Foreign Key setups."""
        if self._connection:
            return

        # Ensure parent directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)

        # Configure optimizations
        await self._connection.execute("PRAGMA journal_mode=WAL;")
        await self._connection.execute("PRAGMA foreign_keys=ON;")
        await self._connection.commit()

        logger.info(f"Database connection opened at: {self.db_path}")

    async def disconnect(self) -> None:
        """Close the active connection cleanly."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            logger.info("Database connection closed.")

    @property
    def connection(self) -> aiosqlite.Connection:
        """Access the raw aiosqlite Connection.

        Raises:
            RuntimeError: If connect() was not called first.
        """
        if not self._connection:
            raise RuntimeError("Database is not connected. Call connect() first.")
        return self._connection

    def transaction(self) -> TransactionContext:
        """Initialize a new transaction context block.

        Returns:
            TransactionContext context manager.
        """
        return TransactionContext(self)

    async def execute(self, sql: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Execute an SQL statement. Auto-commits if called outside explicit transactions.

        Args:
            sql: The target SQL query string.
            parameters: Query parameters tuple.

        Returns:
            The standard aiosqlite cursor result.
        """
        conn = self.connection
        tx = _active_transaction.get()

        if tx:
            # Under active transaction, execute directly on connection (lock already acquired by __aenter__)
            logger.debug(f"[SQL EXECUTE TX] {sql} with params {parameters}")
            return await conn.execute(sql, parameters)
        else:
            # Safe fallback outside transaction: acquire write lock, execute, and auto-commit
            logger.debug(f"[SQL EXECUTE SINGLE] {sql} with params {parameters}")
            async with self._write_lock:
                res = await conn.execute(sql, parameters)
                await conn.commit()
                return res

    async def commit(self) -> None:
        """Commit the current transactions. No-op if inside an active explicit transaction."""
        tx = _active_transaction.get()
        if tx:
            # The transaction context manager will commit automatically at the block exit.
            logger.debug("Database: Ignore explicit commit() inside transaction block.")
            return

        conn = self.connection
        await conn.commit()
