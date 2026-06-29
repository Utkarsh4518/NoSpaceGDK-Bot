"""Lock Channel Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.moderation.moderation_service import ModerationService

class LockTool(BaseTool):
    """Tool for locking down a channel."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.mod: ModerationService = service_container.get(ModerationService)

    @property
    def name(self) -> str:
        return "lock_channel"

    @property
    def description(self) -> str:
        return "Lock a channel. Prevents normal members from typing in it. Use this when the user asks to lock this channel."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the channel to lock (uses current channel if not provided)."
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the lockdown."
                }
            },
            "required": []
        }

    @property
    def required_permissions(self) -> list:
        return ["manage_channels"]

    async def execute(self, **kwargs) -> Any:
        moderator = kwargs["moderator"]
        channel = kwargs["channel"]
        channel_id = kwargs.get("channel_id")
        reason = kwargs.get("reason", "Locked by AI Assistant.")
        
        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        target_channel = channel
        if channel_id:
            target_channel = guild.get_channel(channel_id)
            if not target_channel:
                try:
                    target_channel = await guild.fetch_channel(channel_id)
                except discord.NotFound:
                    return {"status": "error", "message": f"Channel with ID {channel_id} not found."}

        try:
            success = await self.mod.lockdowns.lock_channel(guild, target_channel, moderator, reason)
            if success:
                return {
                    "status": "success",
                    "message": f"Successfully locked channel {target_channel.mention} (ID: {target_channel.id}).",
                    "reason": reason
                }
            return {"status": "error", "message": "Failed to lock the channel."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
