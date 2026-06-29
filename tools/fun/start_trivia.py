"""Start Trivia Tool for AI Agent."""

from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool

class StartTriviaTool(BaseTool):
    """Tool suggesting trivia commands."""

    @property
    def name(self) -> str:
        return "start_trivia"

    @property
    def description(self) -> str:
        return "Guide the user to start a Trivia game. Tells them to use the `/games start game_type:trivia` command."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        return "To start a Trivia game, please run: `/games start game_type:trivia`."
