"""Verify User Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.server.verification_service import VerificationService

class VerifyUserTool(BaseTool):
    """Tool for manually verifying a user or retrieving/configuring settings."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.verify_service: VerificationService = service_container.get(VerificationService)

    @property
    def name(self) -> str:
        return "verify_user"

    @property
    def description(self) -> str:
        return (
            "Manually verify a user in the server by assigning the verification role, "
            "or retrieve/modify verification settings."
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the user to verify."
                },
                "role_id": {
                    "type": "integer",
                    "description": "Optional: Configure verification role for setup."
                },
                "channel_id": {
                    "type": "integer",
                    "description": "Optional: Configure verification channel for setup."
                }
            },
            "required": ["user_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["manage_roles"]

    async def execute(self, **kwargs) -> Any:
        user_id = kwargs["user_id"]
        role_id = kwargs.get("role_id")
        channel_id = kwargs.get("channel_id")
        channel = kwargs["channel"]

        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        # If user also specified role_id and channel_id, they want to setup the gate
        if role_id and channel_id:
            try:
                await self.verify_service.send_verification_panel(guild, channel_id, role_id)
                return {
                    "status": "success",
                    "message": f"Successfully set up verification gate in channel ID {channel_id} with role ID {role_id}."
                }
            except Exception as e:
                return {"status": "error", "message": f"Failed to setup verification panel: {e}"}

        # Otherwise, manually verify a single user
        target = guild.get_member(user_id)
        if not target:
            try:
                target = await guild.fetch_member(user_id)
            except discord.NotFound:
                return {"status": "error", "message": f"User with ID {user_id} not found in this server."}

        settings = await self.verify_service.get_settings(guild.id)
        if not settings or not settings.role_id:
            return {"status": "error", "message": "Verification role is not configured for this server."}

        role = guild.get_role(settings.role_id)
        if not role:
            return {"status": "error", "message": f"Configured verification role (ID: {settings.role_id}) not found."}

        if role >= guild.me.top_role:
            return {"status": "error", "message": "Bot's highest role is lower than or equal to target verification role."}

        try:
            await target.add_roles(role, reason="Manually verified by AI Assistant.")
            return {
                "status": "success",
                "message": f"Successfully verified user {target} (ID: {user_id}) manually.",
                "role_name": role.name
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
