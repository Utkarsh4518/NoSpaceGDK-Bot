"""Tell Joke Tool for AI Agent."""

from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool
from services.fun.joke_service import JokeService

class TellJokeTool(BaseTool):
    """Tool for telling a joke by category."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.jokes: JokeService = service_container.get(JokeService)

    @property
    def name(self) -> str:
        return "tell_joke"

    @property
    def description(self) -> str:
        return "Tell a joke. Can specify a category like 'programmer', 'dad', 'dark', or 'general'."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["programmer", "dad", "dark", "general"],
                    "description": "Category of the joke."
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Any:
        category = kwargs.get("category", "general")
        try:
            joke = await self.jokes.get_joke(category)
            if joke.get("delivery"):
                return f"{joke['setup']}\n\n*Punchline:* {joke['delivery']}"
            return joke["setup"]
        except Exception as e:
            return f"Error fetching joke: {str(e)}"
