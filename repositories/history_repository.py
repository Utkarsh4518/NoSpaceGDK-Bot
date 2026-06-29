"""History repository managing playback history for Discord guilds."""

import datetime
from typing import List
from models.music import PlaybackHistory
from repositories.base_repository import BaseRepository
from utils.logger import logger


class HistoryRepository(BaseRepository):
    """Handles logging and querying guild playback histories in SQLite."""

    async def add_to_history(self, guild_id: int, track_uuid: str, played_by: int) -> PlaybackHistory:
        """Log a playback history entry.

        Args:
            guild_id: Discord server snowflake.
            track_uuid: Track UUID.
            played_by: Requesting user ID.

        Returns:
            The created PlaybackHistory model.
        """
        query = """
            INSERT INTO playback_history (guild_id, track_uuid, played_by)
            VALUES (?, ?, ?);
        """
        await self.db.execute(query, (guild_id, track_uuid, played_by))
        await self.db.commit()

        logger.info(f"Repository operation: Logged playback history (Guild: {guild_id}, Track: {track_uuid}).")
        return PlaybackHistory(
            guild_id=guild_id,
            track_uuid=track_uuid,
            played_by=played_by,
            played_at=datetime.datetime.now(datetime.timezone.utc)
        )

    async def get_by_guild(self, guild_id: int, limit: int = 50) -> List[PlaybackHistory]:
        """Fetch recent playback history records.

        Args:
            guild_id: Discord server snowflake.
            limit: Max records count.

        Returns:
            List of PlaybackHistory models.
        """
        query = """
            SELECT guild_id, track_uuid, played_by, played_at
            FROM playback_history
            WHERE guild_id = ?
            ORDER BY played_at DESC
            LIMIT ?;
        """
        history = []
        async with self.db.connection.execute(query, (guild_id, limit)) as cursor:
            async for row in cursor:
                played_at_val = row[3]
                if isinstance(played_at_val, str):
                    try:
                        played_at_dt = datetime.datetime.fromisoformat(played_at_val.replace(" ", "T"))
                    except ValueError:
                        played_at_dt = datetime.datetime.now(datetime.timezone.utc)
                else:
                    played_at_dt = datetime.datetime.now(datetime.timezone.utc)

                history.append(
                    PlaybackHistory(
                        guild_id=row[0],
                        track_uuid=row[1],
                        played_by=row[2],
                        played_at=played_at_dt
                    )
                )
        return history

    async def clear_guild_history(self, guild_id: int) -> bool:
        """Clear playback history for a guild.

        Args:
            guild_id: Discord server snowflake.

        Returns:
            True if records were deleted, False otherwise.
        """
        query = "DELETE FROM playback_history WHERE guild_id = ?;"
        cursor = await self.db.execute(query, (guild_id,))
        await self.db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Repository operation: Cleared playback history for Guild {guild_id}.")
        return deleted
