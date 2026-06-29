"""Game Service for managing mini-games and stats updates."""

from typing import Dict, List, Optional
import uuid
import datetime
from repositories.leaderboard_repository import LeaderboardRepository
from services.base_service import BaseService
from models.game import GameSession

class GameService(BaseService):
    """Coordinates starting games, checking lobby conflicts, and registering win/losses."""

    def __init__(self, leaderboard_repo: LeaderboardRepository) -> None:
        self.leaderboards = leaderboard_repo
        
        # In-memory sessions index: { session_id: GameSession }
        self._sessions: Dict[str, GameSession] = {}

    def get_session(self, session_id: str) -> Optional[GameSession]:
        return self._sessions.get(session_id)

    async def create_session(self, guild_id: int, channel_id: int, game_type: str, players: List[int]) -> GameSession:
        """Create a new game session. Check for duplicate player conflicts first."""
        # Check if any player is already in an active session
        for session in self._sessions.values():
            if session.status == "active":
                for player in players:
                    if player in session.players:
                        # Find player's username or just ID
                        raise ValueError(f"Player ID {player} is already in an active game session.")

        session_id = str(uuid.uuid4())
        session = GameSession(
            id=session_id,
            guild_id=guild_id,
            channel_id=channel_id,
            game_type=game_type,
            players=players,
            status="active",
            winner_id=None,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc)
        )
        self._sessions[session_id] = session
        return session

    async def end_session(self, session_id: str, winner_id: Optional[int] = None, aborted: bool = False) -> None:
        """Terminate session and register stats."""
        session = self.get_session(session_id)
        if not session or session.status != "active":
            return

        session.status = "aborted" if aborted else "finished"
        session.winner_id = winner_id
        session.updated_at = datetime.datetime.now(datetime.timezone.utc)
        
        # Save updates to stats repositories if finished cleanly
        if not aborted and len(session.players) > 0:
            if len(session.players) == 1:
                # Single-player game (like Hangman, Reaction speed, Memory game)
                # If winner_id is set to user_id, it is a Win. Otherwise a Loss.
                user_id = session.players[0]
                outcome = "win" if winner_id == user_id else "loss"
                await self.leaderboards.record_game_result(session.guild_id, user_id, session.game_type, outcome)
            else:
                # Multiplayer game (TicTacToe, Connect Four)
                for player_id in session.players:
                    if winner_id is None:
                        outcome = "tie"
                    else:
                        outcome = "win" if player_id == winner_id else "loss"
                    await self.leaderboards.record_game_result(session.guild_id, player_id, session.game_type, outcome)

        # Cleanup memory session after recording
        self._sessions.pop(session_id, None)
