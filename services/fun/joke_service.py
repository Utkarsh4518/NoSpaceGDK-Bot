"""Joke Service for fetching jokes with categories."""

import aiohttp
from typing import Any, Dict, Optional
from repositories.fun_repository import FunRepository
from services.base_service import BaseService
from utils.logger import logger

FALLBACK_JOKES = {
    "programmer": [
        {"setup": "Why do programmers wear glasses?", "delivery": "Because they can't C#."},
        {"setup": "There are 10 types of people in the world:", "delivery": "Those who understand binary, and those who don't."}
    ],
    "dad": [
        {"setup": "Why don't scientists trust atoms?", "delivery": "Because they make up everything!"},
        {"setup": "What do you call a fake noodle?", "delivery": "An impasta."}
    ],
    "dark": [
        {"setup": "My wife told me to stop impersonating a flamingo.", "delivery": "I had to put my foot down."}
    ],
    "general": [
        {"setup": "Why did the scarecrow win an award?", "delivery": "Because he was outstanding in his field!"}
    ]
}

class JokeService(BaseService):
    """Fetches jokes from public APIs and fallback cache."""

    def __init__(self, repo: FunRepository) -> None:
        self.repo = repo

    async def get_joke(self, category: str = "general") -> Dict[str, str]:
        """Fetch a joke by category: 'programmer', 'dad', 'dark', 'general'."""
        category_clean = category.lower().strip()
        
        url = "https://official-joke-api.appspot.com/random_joke"
        headers = {"Accept": "application/json"}
        
        if category_clean == "dad":
            url = "https://icanhazdadjoke.com/"
        elif category_clean == "programmer":
            url = "https://official-joke-api.appspot.com/jokes/programming/random"
        elif category_clean == "dark":
            url = "https://v2.jokeapi.dev/joke/Dark?type=twopart"
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        setup, delivery = "", ""
                        
                        if category_clean == "dad":
                            setup = data.get("joke", "")
                            delivery = None
                        elif category_clean == "programmer" and isinstance(data, list):
                            setup = data[0].get("setup", "")
                            delivery = data[0].get("punchline", "")
                        elif category_clean == "dark":
                            setup = data.get("setup", "")
                            delivery = data.get("delivery", "")
                        else: # general or official joke api
                            setup = data.get("setup", "")
                            delivery = data.get("punchline", "")
                            
                        if setup:
                            await self.repo.save_joke(category_clean, setup, delivery)
                            return {"setup": setup, "delivery": delivery or ""}
        except Exception as e:
            logger.warning(f"JokeService: API failed ({e}). Reverting to cache...")

        # Cache lookup
        cached = await self.repo.get_cached_joke(category_clean)
        if cached:
            return {"setup": cached.setup, "delivery": cached.delivery or ""}

        # Local fallback
        import random
        joke_list = FALLBACK_JOKES.get(category_clean, FALLBACK_JOKES["general"])
        return random.choice(joke_list)
