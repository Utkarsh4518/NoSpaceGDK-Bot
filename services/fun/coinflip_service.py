"""Coinflip Service."""

import random
from services.base_service import BaseService

class CoinflipService(BaseService):
    """Flips a coin and returns heads or tails."""

    async def flip(self) -> str:
        return random.choice(["Heads", "Tails"])
