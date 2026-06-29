"""Show Warnings Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.moderation.moderation_service import ModerationService

class ShowWarningsTool(BaseTool):
    """Tool for listing a user's warnings."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.mod: ModerationService = service_container.get(ModerationService)

    @property
    def name(self) -> str:
        return "show_warnings"

    @property
    def description(self) -> str:
        return "Show active and expired warnings of a specific user. Use this when the user asks to see warnings or warning history of a member."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The Snowflake ID of the Discord user."
                },
                "active_only": {
                    "type": "boolean",
                    "description": "If true, show only active warnings. Default is false (shows all)."
                }
            },
            "required": ["user_id"]
        }

    @property
    def required_permissions(self) -> list:
        return ["kick_members"]

    async def execute(self, **kwargs) -> Any:
        user_id = kwargs["user_id"]
        active_only = kwargs.get("active_only", False)
        channel = kwargs["channel"]
        
        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        try:
            warnings = await self.mod.warnings.get_warnings(guild.id, user_id, active_only=active_only)
            warning_list = []
            for w in warnings:
                status = "Active" if not w.is_expired else "Expired"
                created_str = w.created_at.strftime("%Y-%m-%d %H:%M:%S")
                warning_list.append({
                    "id": w.id,
                    "points": w.points,
                    "reason": w.reason,
                    "moderator_id": w.moderator_id,
                    "status": status,
                    "date": created_str
                })
            
            return {
                "status": "success",
                "user_id": user_id,
                "warnings_count": len(warning_list),
                "warnings": warning_list
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
