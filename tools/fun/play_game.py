"""Play Game Tool for AI Agent."""

from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool

class PlayGameTool(BaseTool):
    """Tool suggesting interactive game commands."""

    @property
    def name(self) -> str:
        return "play_game"

    @property
    def description(self) -> str:
        return "Guide the user to start a mini-game. Tells them to use the `/games` commands."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "game_type": {
                    "type": "string",
                    "enum": ["tictactoe", "connectfour", "hangman", "trivia", "guessnumber", "reaction", "memory"],
                    "description": "The name of the mini-game."
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        game_type = kwargs.get("game_type")
        if game_type:
            return f"To play **{game_type}**, please run the slash command: `/games start game_type:{game_type}`."
        return "You can play interactive mini-games like TicTacToe, Connect Four, Hangman, Trivia, Guess Number, Reaction Speed, or Memory Game by running: `/games start`."
