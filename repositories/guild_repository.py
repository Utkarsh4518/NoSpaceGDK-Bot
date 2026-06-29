"""Guild repository managing database records for Discord server configs."""

import datetime
from typing import Optional
from models.domain import Guild
from schemas.validation import GuildSchema
from repositories.base_repository import BaseRepository
from utils.logger import logger


class GuildRepository(BaseRepository):
    """Handles persistence and verification rules for Guild models."""

    async def get_by_id(self, guild_id: int) -> Optional[Guild]:
        """Fetch a guild by its ID.

        Args:
            guild_id: The Discord snowflake ID.

        Returns:
            The Guild domain object, or None.
        """
        query = "SELECT id, prefix, created_at FROM guilds WHERE id = ?;"
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            created_at_val = row[2]
            if isinstance(created_at_val, str):
                # SQLite timestamp strings sometimes have space instead of T, handle cleanly
                try:
                    created_at_dt = datetime.datetime.fromisoformat(created_at_val.replace(" ", "T"))
                except ValueError:
                    created_at_dt = datetime.datetime.now(datetime.timezone.utc)
            else:
                created_at_dt = datetime.datetime.now(datetime.timezone.utc)

            return Guild(
                id=row[0],
                prefix=row[1],
                created_at=created_at_dt
            )

    async def create_or_update(self, guild_id: int, prefix: str) -> Guild:
        """Create or update a guild configuration in the database.

        Args:
            guild_id: The Discord guild ID.
            prefix: Command prefix character.

        Returns:
            The upserted Guild domain model.
        """
        payload = {"id": guild_id, "prefix": prefix}
        validated = GuildSchema.validate(payload)

        query = """
            INSERT INTO guilds (id, prefix)
            VALUES (?, ?)
            ON CONFLICT(id) DO UPDATE SET prefix = excluded.prefix;
        """
        await self.db.execute(query, (validated["id"], validated["prefix"]))
        await self.db.commit()

        guild = await self.get_by_id(validated["id"])
        if not guild:
            raise RuntimeError("Failed to retrieve guild after persistence.")

        logger.info(f"Repository operation: Saved guild configuration (ID: {guild_id}, Prefix: {prefix}).")
        return guild

    async def delete(self, guild_id: int) -> bool:
        """Delete guild configs.

        Args:
            guild_id: The Discord guild ID.

        Returns:
            True if deleted, False otherwise.
        """
        query = "DELETE FROM guilds WHERE id = ?;"
        cursor = await self.db.execute(query, (guild_id,))
        await self.db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Repository operation: Deleted guild configuration (ID: {guild_id}).")
        return deleted
