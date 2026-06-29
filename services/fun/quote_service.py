"""Quote Service for fetching quotes and showerthoughts."""

import aiohttp
from typing import Any, Dict
from repositories.fun_repository import FunRepository
from services.base_service import BaseService
from utils.logger import logger

FALLBACK_QUOTES = {
    "motivation": [
        {"content": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
        {"content": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill"}
    ],
    "showerthought": [
        {"content": "Your alarm sound is technically your theme song since it starts every episode of your day.", "author": "Reddit User"},
        {"content": "Watering plants is just teaching them how to drink.", "author": "Reddit User"}
    ],
    "general": [
        {"content": "Be yourself; everyone else is already taken.", "author": "Oscar Wilde"}
    ]
}

class QuoteService(BaseService):
    """Provides motivational quotes and shower thoughts."""

    def __init__(self, repo: FunRepository) -> None:
        self.repo = repo

    async def get_quote(self, category: str = "general") -> Dict[str, str]:
        """Fetch a quote by category: 'motivation', 'showerthought', 'general'."""
        category_clean = category.lower().strip()
        
        url = "https://api.quotable.io/quotes/random"
        if category_clean == "showerthought":
            url = "https://www.reddit.com/r/showerthoughts/random.json"
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content, author = "", ""
                        
                        if category_clean == "showerthought" and isinstance(data, list):
                            # Reddit random JSON parsing
                            post = data[0].get("data", {}).get("children", [{}])[0].get("data", {})
                            content = post.get("title", "")
                            author = f"u/{post.get('author', 'anonymous')}"
                        elif isinstance(data, list):
                            content = data[0].get("content", "")
                            author = data[0].get("author", "")
                            
                        if content:
                            await self.repo.save_quote(category_clean, content, author)
                            return {"content": content, "author": author}
        except Exception as e:
            logger.warning(f"QuoteService: API request failed ({e}). Reverting to cache...")

        # Cache lookup
        cached = await self.repo.get_cached_quote(category_clean)
        if cached:
            return {"content": cached.content, "author": cached.author or "Unknown"}

        # Fallback list
        import random
        quotes = FALLBACK_QUOTES.get(category_clean, FALLBACK_QUOTES["general"])
        return random.choice(quotes)
