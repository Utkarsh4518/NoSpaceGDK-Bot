"""Kick User Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.moderation.moderation_service import ModerationService

class KickTool(BaseTool):
    """Tool for kicking a user from the guild."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.mod: ModerationService = service_container.get(ModerationService)

    @property
    def name(self) -> str:
        return "kick_user"

    @property
    def description(self) -> str:
        return "Kick a user from the server. Use this when the user asks to kick someone."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the Discord user to kick."
                },
                "reason": {
                    "type": "string",
                    "description": "The reason for the kick."
                }
            },
            "required": ["user_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["kick_members"]

    async def execute(self, **kwargs) -> Any:
        user_id = kwargs["user_id"]
        reason = kwargs.get("reason", "Kicked by AI Assistant.")
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
            await self.mod.kick_user(guild, target, moderator, reason)
            return {
                "status": "success",
                "message": f"Successfully kicked {target} (ID: {user_id}) from the server.",
                "reason": reason
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
