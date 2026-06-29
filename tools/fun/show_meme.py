"""Show Meme Tool for AI Agent."""

from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool
from services.fun.meme_service import MemeService

class ShowMemeTool(BaseTool):
    """Tool for showing a meme by category."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.memes: MemeService = service_container.get(MemeService)

    @property
    def name(self) -> str:
        return "show_meme"

    @property
    def description(self) -> str:
        return "Fetch and display a random meme. Categories: 'programming', 'wholesome', 'anime', 'gaming', 'science', 'space', 'general', 'technology'."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["programming", "wholesome", "anime", "gaming", "science", "space", "general", "technology"],
                    "description": "Meme category."
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        category = kwargs.get("category", "general")
        try:
            meme = await self.memes.get_meme(category)
            return {
                "title": meme["title"],
                "url": meme["url"],
                "subreddit": meme.get("subreddit", "unknown"),
                "post_link": meme.get("post_link", "")
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
