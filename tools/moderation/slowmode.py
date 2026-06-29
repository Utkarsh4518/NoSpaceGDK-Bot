"""Slowmode Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.moderation.moderation_service import ModerationService

class SlowmodeTool(BaseTool):
    """Tool for adjusting slowmode settings in channels."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.mod: ModerationService = service_container.get(ModerationService)

    @property
    def name(self) -> str:
        return "set_slowmode"

    @property
    def description(self) -> str:
        return "Set or remove the slowmode interval in the channel. Use this when the user asks to change or remove slowmode."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "delay_seconds": {
                    "type": "integer",
                    "description": "Slowmode delay in seconds. Set to 0 to turn off."
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for changing slowmode."
                }
            },
            "required": ["delay_seconds"]
        }

    @property
    def required_permissions(self) -> list:
        return ["manage_channels"]

    async def execute(self, **kwargs) -> Any:
        delay = kwargs["delay_seconds"]
        reason = kwargs.get("reason", "Slowmode updated by AI Assistant.")
        moderator = kwargs["moderator"]
        channel = kwargs["channel"]
        
        if not hasattr(channel, "edit"):
            return {"status": "error", "message": "This command can only be executed in text channels."}

        try:
            await self.mod.set_slowmode(channel, moderator, delay, reason)
            status_msg = f"set to {delay} seconds" if delay > 0 else "disabled"
            return {
                "status": "success",
                "message": f"Successfully {status_msg} slowmode in {channel.mention}.",
                "reason": reason
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
