"""Compliment User Tool for AI Agent."""

import random
from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool

COMPLIMENTS = [
    "You're like a software update. Whenever I see you, I think, 'I can't wait to see what's new.'",
    "You have a great sense of humor!",
    "Your code is clean, and your syntax is beautiful.",
    "The world is a better place because you are in it."
]

class ComplimentTool(BaseTool):
    """Tool for sending a nice compliment to a user."""

    @property
    def name(self) -> str:
        return "compliment"

    @property
    def description(self) -> str:
        return "Compliment a user in the server."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "ID of the user to compliment."
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        user_id = kwargs.get("user_id")
        comp = random.choice(COMPLIMENTS)
        if user_id:
            return f"<@{user_id}>, {comp}"
        return comp
