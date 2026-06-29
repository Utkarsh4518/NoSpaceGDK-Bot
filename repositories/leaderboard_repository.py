"""Leaderboard and Game Statistics Repository."""

import json
from typing import List, Optional
from models.leaderboard import GameStatistics, LeaderboardEntry
from repositories.base_repository import BaseRepository

class LeaderboardRepository(BaseRepository):
    """Handles persistence of rankings and game history statistics."""

    async def get_game_stats(self, guild_id: int, user_id: int, game_type: str) -> GameStatistics:
        query = """
            SELECT guild_id, user_id, game_type, wins, losses, ties, longest_win_streak, current_win_streak
            FROM game_statistics
            WHERE guild_id = ? AND user_id = ? AND game_type = ?;
        """
        async with self.db.connection.execute(query, (guild_id, user_id, game_type)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return GameStatistics(guild_id, user_id, game_type, 0, 0, 0, 0, 0)
            return GameStatistics(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7])

    async def record_game_result(self, guild_id: int, user_id: int, game_type: str, outcome: str) -> None:
        """Record game completion.
        
        Args:
            outcome: 'win', 'loss', or 'tie'
        """
        stats = await self.get_game_stats(guild_id, user_id, game_type)
        
        new_wins = stats.wins
        new_losses = stats.losses
        new_ties = stats.ties
        new_current_streak = stats.current_win_streak
        new_longest_streak = stats.longest_win_streak
        
        if outcome == "win":
            new_wins += 1
            new_current_streak += 1
            if new_current_streak > new_longest_streak:
                new_longest_streak = new_current_streak
        elif outcome == "loss":
            new_losses += 1
            new_current_streak = 0
        else: # tie
            new_ties += 1
            
        query = """
            INSERT INTO game_statistics (guild_id, user_id, game_type, wins, losses, ties, longest_win_streak, current_win_streak)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id, user_id, game_type) DO UPDATE SET
                wins = excluded.wins,
                losses = excluded.losses,
                ties = excluded.ties,
                longest_win_streak = excluded.longest_win_streak,
                current_win_streak = excluded.current_win_streak;
        """
        await self.db.execute(query, (guild_id, user_id, game_type, new_wins, new_losses, new_ties, new_longest_streak, new_current_streak))
        
        # Also update global wins metric in leaderboards
        if outcome == "win":
            await self.increment_leaderboard_value(guild_id, user_id, "wins")
            
        await self.db.commit()

    async def increment_leaderboard_value(self, guild_id: int, user_id: int, metric: str) -> None:
        query = """
            INSERT INTO leaderboards (guild_id, user_id, metric, value)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(guild_id, user_id, metric) DO UPDATE SET
                value = value + 1;
        """
        await self.db.execute(query, (guild_id, user_id, metric))
        await self.db.commit()

    async def get_top_users(self, guild_id: int, metric: str, limit: int = 10) -> List[LeaderboardEntry]:
        query = """
            SELECT guild_id, user_id, metric, value
            FROM leaderboards
            WHERE guild_id = ? AND metric = ?
            ORDER BY value DESC LIMIT ?;
        """
        entries = []
        async with self.db.connection.execute(query, (guild_id, metric, limit)) as cursor:
            async for idx, row in enumerate(cursor):
                entries.append(LeaderboardEntry(
                    guild_id=row[0],
                    user_id=row[1],
                    metric=row[2],
                    value=row[3],
                    rank=idx + 1
                ))
        return entries
