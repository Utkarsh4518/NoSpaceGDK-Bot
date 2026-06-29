"""Dice Service."""

import random
from services.base_service import BaseService

class DiceService(BaseService):
    """Rolls a dice with a configurable number of sides."""

    async def roll(self, sides: int = 6) -> int:
        if sides < 1:
            raise ValueError("Sides must be greater than 0.")
        return random.randint(1, sides)
