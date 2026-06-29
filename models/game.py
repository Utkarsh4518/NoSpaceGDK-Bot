"""Game Session domain model."""

import datetime
from dataclasses import dataclass
from typing import List

@dataclass
class GameSession:
    """Domain representation of an active or completed game session."""
    id: str
    guild_id: int
    channel_id: int
    game_type: str  # 'tictactoe', 'connectfour', 'hangman', 'trivia', 'guessnumber', 'reaction', 'memory'
    players: List[int]  # List of member snowflakes
    status: str  # 'active', 'finished', 'aborted'
    winner_id: int | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
