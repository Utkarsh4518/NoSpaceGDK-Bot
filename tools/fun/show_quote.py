"""Show Quote Tool for AI Agent."""

from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool
from services.fun.quote_service import QuoteService

class ShowQuoteTool(BaseTool):
    """Tool for showing a quote by category."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.quotes: QuoteService = service_container.get(QuoteService)

    @property
    def name(self) -> str:
        return "show_quote"

    @property
    def description(self) -> str:
        return "Show a random quote or shower thought. Categories: 'motivation', 'showerthought', 'general'."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["motivation", "showerthought", "general"],
                    "description": "Category of quote."
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        category = kwargs.get("category", "general")
        try:
            quote = await self.quotes.get_quote(category)
            return {
                "content": quote["content"],
                "author": quote.get("author", "Unknown")
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
