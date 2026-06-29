"""Purge Messages Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.moderation.moderation_service import ModerationService

class PurgeTool(BaseTool):
    """Tool for purging messages from a channel."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.mod: ModerationService = service_container.get(ModerationService)

    @property
    def name(self) -> str:
        return "purge_messages"

    @property
    def description(self) -> str:
        return "Delete a specified number of messages in the channel. Can optionally target a specific user's messages. Use this when the user asks to clean up or delete messages."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of messages to scan and delete."
                },
                "target_user_id": {
                    "type": "integer",
                    "description": "Snowflake ID of a specific user to delete messages for."
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for purging."
                }
            },
            "required": ["limit"]
        }

    @property
    def required_permissions(self) -> list:
        return ["manage_messages"]

    async def execute(self, **kwargs) -> Any:
        limit = kwargs["limit"]
        target_user_id = kwargs.get("target_user_id")
        reason = kwargs.get("reason", "Messages purged by AI Assistant.")
        moderator = kwargs["moderator"]
        channel = kwargs["channel"]
        
        if not isinstance(channel, discord.TextChannel):
            return {"status": "error", "message": "This command can only be executed in text channels."}

        target_user = None
        if target_user_id:
            target_user = channel.guild.get_member(target_user_id)
            if not target_user:
                try:
                    target_user = await channel.guild.fetch_member(target_user_id)
                except discord.NotFound:
                    return {"status": "error", "message": f"User with ID {target_user_id} not found in this guild."}

        try:
            deleted_count = await self.mod.purge_messages(channel, moderator, limit, target_user, reason)
            return {
                "status": "success",
                "message": f"Successfully deleted {deleted_count} messages from {channel.mention}.",
                "reason": reason
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
