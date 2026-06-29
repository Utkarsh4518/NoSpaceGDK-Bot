"""Flip Coin Tool for AI Agent."""

from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool
from services.fun.coinflip_service import CoinflipService

class FlipCoinTool(BaseTool):
    """Tool for flipping a coin."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.coinflip: CoinflipService = service_container.get(CoinflipService)

    @property
    def name(self) -> str:
        return "flip_coin"

    @property
    def description(self) -> str:
        return "Flip a coin. Returns Heads or Tails."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        try:
            result = await self.coinflip.flip()
            return f"Coin Flip Result: **{result}**!"
        except Exception as e:
            return f"Error: {str(e)}"
