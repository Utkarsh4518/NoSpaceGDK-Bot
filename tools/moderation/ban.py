"""Ban User Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.moderation.moderation_service import ModerationService

class BanTool(BaseTool):
    """Tool for banning a user from the guild."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.mod: ModerationService = service_container.get(ModerationService)

    @property
    def name(self) -> str:
        return "ban_user"

    @property
    def description(self) -> str:
        return "Ban a user from the server. Use this when the user asks to ban someone."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the Discord user to ban."
                },
                "reason": {
                    "type": "string",
                    "description": "The reason for the ban."
                }
            },
            "required": ["user_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["ban_members"]

    async def execute(self, **kwargs) -> Any:
        user_id = kwargs["user_id"]
        reason = kwargs.get("reason", "Banned by AI Assistant.")
        moderator = kwargs["moderator"]
        channel = kwargs["channel"]
        
        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        # Resolve target member
        target = guild.get_member(user_id)
        if not target:
            try:
                target = await guild.fetch_member(user_id)
            except discord.NotFound:
                # If target is not in the guild, we can ban them globally (hackban)
                try:
                    target = await self.services.bot.fetch_user(user_id)
                except discord.NotFound:
                    return {"status": "error", "message": f"User with ID {user_id} was not found."}

        try:
            await self.mod.ban_user(guild, target, moderator, reason)
            return {
                "status": "success",
                "message": f"Successfully banned {target} (ID: {user_id}) from the server.",
                "reason": reason
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
