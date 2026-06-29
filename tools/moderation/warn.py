"""Warn User Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.moderation.moderation_service import ModerationService

class WarnTool(BaseTool):
    """Tool for warning a user."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.mod: ModerationService = service_container.get(ModerationService)

    @property
    def name(self) -> str:
        return "warn_user"

    @property
    def description(self) -> str:
        return "Warn a user in the server. Use this when the user asks to warn someone."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the Discord user to warn."
                },
                "reason": {
                    "type": "string",
                    "description": "The reason for the warning."
                },
                "points": {
                    "type": "integer",
                    "description": "The severity points for this warning (default: 1)."
                }
            },
            "required": ["user_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["kick_members"]  # Warn requires moderator-level perms

    async def execute(self, **kwargs) -> Any:
        user_id = kwargs["user_id"]
        reason = kwargs.get("reason", "Warned by AI Assistant.")
        points = kwargs.get("points", 1)
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
            await self.mod.validate_hierarchy(moderator, target)
            warning = await self.mod.warnings.warn_user(guild.id, target, moderator, reason, points)
            return {
                "status": "success",
                "message": f"Successfully warned {target} (ID: {user_id}).",
                "warning_id": warning.id,
                "points": points,
                "reason": reason
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
