"""Meme Service for fetching and caching memes."""

import aiohttp
from typing import Any, Dict, Optional
from repositories.fun_repository import FunRepository
from services.base_service import BaseService
from utils.logger import logger

FALLBACK_MEMES = {
    "programming": [
        {"title": "There are 10 types of people: those who understand binary and those who don't", "url": "https://i.imgur.com/8Qh1C0x.png", "subreddit": "programmerhumor", "post_link": "https://reddit.com/r/programmerhumor"},
        {"title": "Fixing bugs in production", "url": "https://i.imgur.com/fL3sT9v.gif", "subreddit": "programmerhumor", "post_link": "https://reddit.com/r/programmerhumor"}
    ],
    "general": [
        {"title": "Distracted Boyfriend", "url": "https://i.imgur.com/H5XW2PZ.jpg", "subreddit": "memes", "post_link": "https://reddit.com/r/memes"},
        {"title": "Drake Hotline Bling", "url": "https://i.imgur.com/U83P4Jc.jpg", "subreddit": "memes", "post_link": "https://reddit.com/r/memes"}
    ],
    "anime": [
        {"title": "Is this a pigeon?", "url": "https://i.imgur.com/r3PUpkP.jpg", "subreddit": "animemes", "post_link": "https://reddit.com/r/animemes"}
    ]
}

class MemeService(BaseService):
    """Fetches memes from external APIs and manages caching."""

    def __init__(self, repo: FunRepository) -> None:
        self.repo = repo

    async def get_meme(self, category: str = "general") -> Dict[str, Any]:
        """Fetch a meme from the API. If API is down, fallback to local cache or hardcoded lists."""
        category_clean = category.lower().strip()
        # Map categories to subreddits if using the meme-api
        subreddits = {
            "programming": "programmerhumor",
            "wholesome": "wholesomememes",
            "anime": "animemes",
            "gaming": "gamingmemes",
            "science": "sciencememes",
            "space": "spacememes",
            "general": "memes",
            "technology": "technologymemes"
        }
        
        sub = subreddits.get(category_clean, "memes")
        url = f"https://meme-api.com/gimme/{sub}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # Save to cache
                        await self.repo.save_meme(
                            category=category_clean,
                            title=data.get("title"),
                            url=data.get("url"),
                            post_link=data.get("postLink"),
                            subreddit=data.get("subreddit"),
                            nsfw=data.get("nsfw", False)
                        )
                        return {
                            "title": data.get("title"),
                            "url": data.get("url"),
                            "post_link": data.get("postLink"),
                            "subreddit": data.get("subreddit")
                        }
        except Exception as e:
            logger.warning(f"MemeService: API request failed ({e}). Falling back to cache...")
            
        # Cache Lookup Fallback
        cached = await self.repo.get_cached_meme(category_clean)
        if cached:
            return {
                "title": cached.title,
                "url": cached.url,
                "post_link": cached.post_link,
                "subreddit": cached.subreddit
            }
            
        # Hardcoded fallback list
        fallbacks = FALLBACK_MEMES.get(category_clean, FALLBACK_MEMES["general"])
        import random
        return random.choice(fallbacks)
