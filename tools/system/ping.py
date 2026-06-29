"""Ping Tool for testing AI Agent Framework."""

from typing import Any, Dict
from services.ai.agent.base_tool import BaseTool

class PingTool(BaseTool):
    """A simple tool to test the agent function calling."""
    
    @property
    def name(self) -> str:
        return "ping_system"
        
    @property
    def description(self) -> str:
        return "Ping the bot's system to check if it is responsive. Use this when the user asks to ping the system or check responsiveness."
        
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
        
    async def execute(self, **kwargs) -> Any:
        return {"status": "success", "message": "Pong! System is fully operational and responsive."}
