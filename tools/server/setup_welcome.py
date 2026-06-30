"""Setup Welcome Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.server.welcome_service import WelcomeService

class SetupWelcomeTool(BaseTool):
    """Tool for configuring server welcome messages."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.welcome_service: WelcomeService = service_container.get(WelcomeService)

    @property
    def name(self) -> str:
        return "setup_welcome"

    @property
    def description(self) -> str:
        return "Configure or update the server welcome settings. Use this when the user asks to setup, enable, or configure welcome notifications."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the channel where welcome messages should be posted."
                },
                "message_text": {
                    "type": "string",
                    "description": "Optional welcome message text (supports placeholders: {user}, {username}, {server}, {member_count})."
                },
                "embed_json": {
                    "type": "string",
                    "description": "Optional raw JSON string representing the welcome embed."
                },
                "dm_enabled": {
                    "type": "boolean",
                    "description": "If true, also sends the welcome message to the member's DMs."
                },
                "enabled": {
                    "type": "boolean",
                    "description": "Whether the welcome system should be enabled."
                }
            },
            "required": ["channel_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["manage_guild"]

    async def execute(self, **kwargs) -> Any:
        channel_id = kwargs["channel_id"]
        message_text = kwargs.get("message_text")
        embed_json = kwargs.get("embed_json")
        dm_enabled = kwargs.get("dm_enabled", False)
        enabled = kwargs.get("enabled", True)
        channel = kwargs["channel"]

        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        # Verify channel exists
        target_channel = guild.get_channel(channel_id)
        if not target_channel:
            return {"status": "error", "message": f"Channel with ID {channel_id} not found."}

        try:
            settings = await self.welcome_service.save_settings(
                guild_id=guild.id,
                channel_id=channel_id,
                message_text=message_text,
                embed_json=embed_json,
                dm_enabled=dm_enabled,
                enabled=enabled
            )
            return {
                "status": "success",
                "message": f"Successfully configured welcome settings in channel {target_channel.name}.",
                "dm_enabled": settings.dm_enabled,
                "enabled": settings.enabled
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
