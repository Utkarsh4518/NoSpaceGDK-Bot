"""Database connection and lifecycle manager for NoSpaceFGK.

Handles async context bindings, WAL mode enablement, PRAGMA setup,
and execution queries via aiosqlite.
"""

from pathlib import Path
import aiosqlite
from utils.logger import logger


class DatabaseManager:
    """Manages active aiosqlite connection handles and operational setups."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the database manager.

        Args:
            db_path: Path where the SQLite file will reside.
        """
        self.db_path: Path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        """Open the SQLite connection, create folders, and configure optimization parameters."""
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
        """Close the active connection pool cleanly."""
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

    async def execute(self, sql: str, parameters: tuple = ()) -> aiosqlite.Cursor:
        """Execute an SQL statement.

        Args:
            sql: The target SQL query string.
            parameters: Query parameters tuple.

        Returns:
            The standard aiosqlite cursor result.
        """
        conn = self.connection
        logger.debug(f"[SQL EXECUTE] {sql} with params {parameters}")
        return await conn.execute(sql, parameters)

    async def commit(self) -> None:
        """Commit the current transactions."""
        conn = self.connection
        await conn.commit()
