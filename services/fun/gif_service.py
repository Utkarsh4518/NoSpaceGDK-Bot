"""GIF Service for fetching reaction GIFs."""

from typing import Dict, List
import random
from services.base_service import BaseService

REACTION_GIFS: Dict[str, List[str]] = {
    "happy": [
        "https://media.giphy.com/media/26FPCt7zO1YY9YJ5C/giphy.gif",
        "https://media.giphy.com/media/l41YcGT5shJa0UXtK/giphy.gif",
        "https://media.giphy.com/media/5GovlczwksLDy/giphy.gif"
    ],
    "sad": [
        "https://media.giphy.com/media/9Y5BbDSkSTiY8/giphy.gif",
        "https://media.giphy.com/media/2WxWfiavndgc0/giphy.gif",
        "https://media.giphy.com/media/l378giAZgxPw3eO52/giphy.gif"
    ],
    "angry": [
        "https://media.giphy.com/media/11tIanz6Qy85CE/giphy.gif",
        "https://media.giphy.com/media/3o72FiXyc7OQLCgK5O/giphy.gif",
        "https://media.giphy.com/media/tXTqLBYNf0N7W/giphy.gif"
    ],
    "dance": [
        "https://media.giphy.com/media/l3V0lsGtTMSB5YNgc/giphy.gif",
        "https://media.giphy.com/media/14481cJ741Wygo/giphy.gif",
        "https://media.giphy.com/media/uS0xyrJuQsxEc/giphy.gif"
    ],
    "facepalm": [
        "https://media.giphy.com/media/3og0INyMQLH9f36dEs/giphy.gif",
        "https://media.giphy.com/media/8UGoOaR1lA1uaU50W1/giphy.gif"
    ],
    "shrug": [
        "https://media.giphy.com/media/Ky5g91K2uPxnFJB49E/giphy.gif",
        "https://media.giphy.com/media/WZoffPXV1w1Jm/giphy.gif"
    ]
}

class GifService(BaseService):
    """Provides categorized reaction GIFs."""

    async def get_reaction_gif(self, category: str) -> str:
        """Fetch a reaction GIF URL."""
        cat_clean = category.lower().strip()
        gifs = REACTION_GIFS.get(cat_clean, REACTION_GIFS["happy"])
        return random.choice(gifs)

    async def get_all_categories(self) -> List[str]:
        return list(REACTION_GIFS.keys())
