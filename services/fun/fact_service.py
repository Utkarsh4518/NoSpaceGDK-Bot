"""Fact Service for random trivia facts."""

import aiohttp
from typing import Dict
from repositories.fun_repository import FunRepository
from services.base_service import BaseService
from utils.logger import logger

FALLBACK_FACTS = [
    "Honey never spoils. You can theoretically eat 3,000-year-old honey.",
    "Dead people can get goosebumps.",
    "A day on Venus is longer than a year on Venus.",
    "Bananas are berries, but strawberries aren't."
]

class FactService(BaseService):
    """Provides trivia facts."""

    def __init__(self, repo: FunRepository) -> None:
        self.repo = repo

    async def get_fact(self) -> str:
        """Fetch a random useless fact."""
        url = "https://uselessfacts.jsph.pl/api/v2/facts/random"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = data.get("text", "")
                        if text:
                            await self.repo.save_fact(text)
                            return text
        except Exception as e:
            logger.warning(f"FactService: API failed ({e}). Reverting to cache...")

        # Cache lookup
        cached = await self.repo.get_cached_fact()
        if cached:
            return cached.content

        # Local fallback
        import random
        return random.choice(FALLBACK_FACTS)
