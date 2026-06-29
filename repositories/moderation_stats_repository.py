"""Moderation Statistics Repository."""

from models.moderation import ModerationStatisticsModel
from repositories.base_repository import BaseRepository

class ModerationStatsRepository(BaseRepository):
    """Handles SQL queries for tracking moderation metrics."""

    async def get_stats(self, guild_id: int) -> ModerationStatisticsModel:
        query = """
            SELECT guild_id, total_warns, total_kicks, total_bans, total_timeouts, total_automod_triggers
            FROM moderation_statistics
            WHERE guild_id = ?;
        """
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                # Return zeroed stats
                return ModerationStatisticsModel(guild_id, 0, 0, 0, 0, 0)
            return ModerationStatisticsModel(row[0], row[1], row[2], row[3], row[4], row[5])

    async def increment_stat(self, guild_id: int, stat_name: str) -> None:
        """Increment a specific metric column safely using upsert.
        
        Args:
            guild_id: Guild snowflake.
            stat_name: Must be one of 'total_warns', 'total_kicks', 'total_bans', 'total_timeouts', 'total_automod_triggers'.
        """
        valid_stats = ['total_warns', 'total_kicks', 'total_bans', 'total_timeouts', 'total_automod_triggers']
        if stat_name not in valid_stats:
            raise ValueError(f"Invalid statistic column: {stat_name}")

        query = f"""
            INSERT INTO moderation_statistics (guild_id, {stat_name})
            VALUES (?, 1)
            ON CONFLICT(guild_id) DO UPDATE SET
                {stat_name} = {stat_name} + 1;
        """
        await self.db.execute(query, (guild_id,))
        await self.db.commit()
