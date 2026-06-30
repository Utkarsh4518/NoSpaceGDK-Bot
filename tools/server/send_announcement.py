"""Send Announcement Tool for AI Agent."""

import datetime
from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.server.announcement_service import AnnouncementService

class SendAnnouncementTool(BaseTool):
    """Tool for sending or scheduling announcements."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.announce_service: AnnouncementService = service_container.get(AnnouncementService)

    @property
    def name(self) -> str:
        return "send_announcement"

    @property
    def description(self) -> str:
        return (
            "Send an announcement immediately or schedule one. Use this when the user asks to post, "
            "send, or schedule an announcement/message/embed to a specific channel."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the target text channel."
                },
                "message_text": {
                    "type": "string",
                    "description": "Optional body text of the announcement."
                },
                "embed_json": {
                    "type": "string",
                    "description": "Optional JSON configuration for the embed (can contain button_label/button_url fields)."
                },
                "scheduled_at": {
                    "type": "string",
                    "description": "Optional ISO 8601 string (UTC) to schedule the post (e.g. 2026-06-30T15:00:00Z)."
                }
            },
            "required": ["channel_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["mention_everyone"]

    async def execute(self, **kwargs) -> Any:
        channel_id = kwargs["channel_id"]
        message_text = kwargs.get("message_text")
        embed_json = kwargs.get("embed_json")
        scheduled_at_str = kwargs.get("scheduled_at")
        channel = kwargs["channel"]

        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        target_channel = guild.get_channel(channel_id)
        if not target_channel or not isinstance(target_channel, discord.TextChannel):
            return {"status": "error", "message": "Target channel not found or is not a text channel."}

        scheduled_at = None
        if scheduled_at_str:
            try:
                # Remove trailing Z if present for fromisoformat
                cleaned_str = scheduled_at_str.replace("Z", "+00:00")
                scheduled_at = datetime.datetime.fromisoformat(cleaned_str)
            except Exception as e:
                return {"status": "error", "message": f"Invalid ISO 8601 timestamp format for scheduled_at: {e}"}

        try:
            announcement = await self.announce_service.create_announcement(
                guild_id=guild.id,
                channel_id=channel_id,
                message_text=message_text,
                embed_json=embed_json,
                scheduled_at=scheduled_at
            )
            
            if scheduled_at:
                return {
                    "status": "success",
                    "message": f"Successfully scheduled announcement #{announcement.id} for {scheduled_at_str}.",
                    "announcement_id": announcement.id
                }
            else:
                return {
                    "status": "success",
                    "message": "Successfully sent announcement immediately.",
                    "announcement_id": announcement.id
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
