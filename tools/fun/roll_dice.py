"""Roll Dice Tool for AI Agent."""

from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool
from services.fun.dice_service import DiceService

class RollDiceTool(BaseTool):
    """Tool for rolling a dice."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.dice: DiceService = service_container.get(DiceService)

    @property
    def name(self) -> str:
        return "roll_dice"

    @property
    def description(self) -> str:
        return "Roll a dice with a custom number of sides (default is 6)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sides": {
                    "type": "integer",
                    "description": "Number of sides on the dice."
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        sides = kwargs.get("sides", 6)
        try:
            result = await self.dice.roll(sides)
            return f"Rolled a d{sides} and got: **{result}**!"
        except Exception as e:
            return f"Error rolling dice: {str(e)}"
