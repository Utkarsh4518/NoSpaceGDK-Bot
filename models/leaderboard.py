"""Leaderboard and Game Statistics domain models."""

from dataclasses import dataclass

@dataclass
class GameStatistics:
    """Domain representation of a user's stats for a specific mini-game type."""
    guild_id: int
    user_id: int
    game_type: str
    wins: int
    losses: int
    ties: int
    longest_win_streak: int
    current_win_streak: int

@dataclass
class LeaderboardEntry:
    """Domain representation of a single leaderboard entry ranking."""
    guild_id: int
    user_id: int
    metric: str  # 'wins', 'memes_viewed', 'commands_used'
    value: int
    rank: int | None = None
