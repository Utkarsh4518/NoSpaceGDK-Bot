"""Timeout User Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.moderation.moderation_service import ModerationService

class TimeoutTool(BaseTool):
    """Tool for timing out/muting a user in the server."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.mod: ModerationService = service_container.get(ModerationService)

    @property
    def name(self) -> str:
        return "timeout_user"

    @property
    def description(self) -> str:
        return "Time out (mute) a user for a specific duration. Use this when the user asks to timeout/mute someone."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the Discord user to timeout."
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "Timeout duration in seconds (default: 600 for 10 minutes)."
                },
                "reason": {
                    "type": "string",
                    "description": "The reason for the timeout."
                }
            },
            "required": ["user_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["moderate_members"]

    async def execute(self, **kwargs) -> Any:
        user_id = kwargs["user_id"]
        duration = kwargs.get("duration_seconds", 600)
        reason = kwargs.get("reason", "Timed out by AI Assistant.")
        moderator = kwargs["moderator"]
        channel = kwargs["channel"]
        
        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        target = guild.get_member(user_id)
        if not target:
            try:
                target = await guild.fetch_member(user_id)
            except discord.NotFound:
                return {"status": "error", "message": f"User with ID {user_id} not found in this server."}

        try:
            await self.mod.timeout_user(guild, target, moderator, duration, reason)
            return {
                "status": "success",
                "message": f"Successfully timed out {target} (ID: {user_id}) for {duration} seconds.",
                "reason": reason
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
