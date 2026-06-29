"""User repository managing database records for Discord members."""

import datetime
from typing import Optional
from models.domain import User
from schemas.validation import UserSchema
from repositories.base_repository import BaseRepository
from utils.logger import logger


class UserRepository(BaseRepository):
    """Handles persistence and verification rules for User models."""

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch a user by their ID.

        Args:
            user_id: The Discord member snowflake ID.

        Returns:
            The User domain object, or None.
        """
        query = "SELECT id, username, is_premium, created_at FROM users WHERE id = ?;"
        async with self.db.connection.execute(query, (user_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            created_at_val = row[3]
            if isinstance(created_at_val, str):
                try:
                    created_at_dt = datetime.datetime.fromisoformat(created_at_val.replace(" ", "T"))
                except ValueError:
                    created_at_dt = datetime.datetime.now(datetime.timezone.utc)
            else:
                created_at_dt = datetime.datetime.now(datetime.timezone.utc)

            return User(
                id=row[0],
                username=row[1],
                is_premium=bool(row[2]),
                created_at=created_at_dt
            )

    async def create_or_update(self, user_id: int, username: Optional[str], is_premium: bool = False) -> User:
        """Create or update user details in the database.

        Args:
            user_id: The Discord user ID.
            username: The display name or tag of the member.
            is_premium: Premium status flag.

        Returns:
            The upserted User domain model.
        """
        payload = {"id": user_id, "username": username, "is_premium": is_premium}
        validated = UserSchema.validate(payload)

        query = """
            INSERT INTO users (id, username, is_premium)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                username = excluded.username,
                is_premium = excluded.is_premium;
        """
        await self.db.execute(
            query,
            (validated["id"], validated["username"], 1 if validated["is_premium"] else 0)
        )
        await self.db.commit()

        user = await self.get_by_id(validated["id"])
        if not user:
            raise RuntimeError("Failed to retrieve user after persistence.")

        logger.info(f"Repository operation: Saved user profile (ID: {user_id}, Username: {username}, Premium: {is_premium}).")
        return user

    async def delete(self, user_id: int) -> bool:
        """Delete user profiles.

        Args:
            user_id: The Discord user ID.

        Returns:
            True if deleted, False otherwise.
        """
        query = "DELETE FROM users WHERE id = ?;"
        cursor = await self.db.execute(query, (user_id,))
        await self.db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Repository operation: Deleted user profile (ID: {user_id}).")
        return deleted
