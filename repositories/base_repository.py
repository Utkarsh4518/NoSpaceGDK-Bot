"""Base Repository definition for NoSpaceFGK.

Exposes the parent repository class that injects the database connection manager.
"""

from database.connection import DatabaseManager


class BaseRepository:
    """Base class for all persistent entity repositories."""

    def __init__(self, db: DatabaseManager) -> None:
        """Initialize the repository.

        Args:
            db: The DatabaseManager instance.
        """
        self.db: DatabaseManager = db
