"""Lightweight database migration runner for NoSpaceFGK.

Exposes the MigrationRunner class which applies table creation schemas,
tracks versioning records, and supports rollback operations.
"""

import aiosqlite
from database.connection import DatabaseManager
from database.schema import MIGRATIONS
from utils.logger import logger


class MigrationRunner:
    """Sequentially applies SQL migrations and handles rollbacks."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize the migration runner.

        Args:
            db: The active DatabaseManager instance.
        """
        self.db: DatabaseManager = db

    async def get_current_version(self) -> int:
        """Retrieve the currently applied schema version from the database.

        If the schema_version tracking table does not exist, it is initialized at version 0.

        Returns:
            The current schema version integer.
        """
        try:
            async with self.db.connection.execute(
                "SELECT MAX(version) FROM schema_version;"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] is not None else 0
        except aiosqlite.OperationalError:
            logger.info("Initializing schema version tracking table...")
            await self.db.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await self.db.commit()
            return 0

    async def run_migrations(self) -> None:
        """Scan available migrations and apply them sequentially up to the latest version."""
        current_version = await self.get_current_version()
        target_version = max(MIGRATIONS.keys()) if MIGRATIONS else 0

        if current_version >= target_version:
            logger.info(f"Database schema is up-to-date (Version: {current_version}).")
            return

        logger.info(f"Applying database migrations: Version {current_version} -> {target_version}...")

        for version in sorted(MIGRATIONS.keys()):
            if version <= current_version:
                continue

            logger.info(f"Applying migration version {version}...")
            migration = MIGRATIONS[version]

            await self.db.connection.executescript(migration["up"])

            # Record migration version
            await self.db.execute(
                "INSERT INTO schema_version (version) VALUES (?);",
                (version,)
            )
            await self.db.commit()
            logger.info(f"Migration version {version} applied successfully.")

    async def rollback_to(self, target_version: int) -> None:
        """Rollback database migrations down to the target version.

        Args:
            target_version: The version to roll back to.
        """
        current_version = await self.get_current_version()
        if target_version >= current_version:
            logger.warning(f"Rollback target version {target_version} is >= current version {current_version}. Skipping.")
            return

        logger.info(f"Rolling back database migrations: Version {current_version} -> {target_version}...")

        for version in sorted(MIGRATIONS.keys(), reverse=True):
            if version <= target_version or version > current_version:
                continue

            logger.info(f"Reverting migration version {version}...")
            migration = MIGRATIONS[version]

            await self.db.connection.executescript(migration["down"])

            # Remove migration version record
            await self.db.execute(
                "DELETE FROM schema_version WHERE version = ?;",
                (version,)
            )
            await self.db.commit()
            logger.info(f"Migration version {version} reverted successfully.")
