"""Roast User Tool for AI Agent."""

import random
from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool

ROASTS = [
    "I'd roast you, but my mom said I'm not allowed to burn trash.",
    "You have a face for radio and a voice for silent movies.",
    "Your secrets are always safe with me. I never even listen to them.",
    "You're the reason the gene pool needs a lifeguard."
]

class RoastTool(BaseTool):
    """Tool for roasting a user."""

    @property
    def name(self) -> str:
        return "roast"

    @property
    def description(self) -> str:
        return "Roast a user with a funny comeback."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "ID of the user to roast."
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        user_id = kwargs.get("user_id")
        roast_text = random.choice(ROASTS)
        if user_id:
            return f"<@{user_id}>, {roast_text}"
        return roast_text
