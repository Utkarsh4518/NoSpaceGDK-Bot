"""Create Ticket Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.server.ticket_service import TicketService

class CreateTicketTool(BaseTool):
    """Tool for creating a support ticket."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.ticket_service: TicketService = service_container.get(TicketService)

    @property
    def name(self) -> str:
        return "create_ticket"

    @property
    def description(self) -> str:
        return "Create a private ticket channel for support. Use this when the user asks to open/create a support ticket."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Optional topic or reason for opening the support ticket."
                }
            }
        }

    async def execute(self, **kwargs) -> Any:
        topic = kwargs.get("topic")
        moderator = kwargs["moderator"]
        channel = kwargs["channel"]

        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        # Resolve support role (look for a role named "Support Staff", "Moderator", or similar; fallback to first non-default role or default role)
        support_role = None
        for role in guild.roles:
            if role.name.lower() in ["support staff", "staff", "support", "helper", "moderator"]:
                support_role = role
                break
        
        if not support_role:
            # Fallback to guild default support role or create/use standard moderator permissions role
            support_role = guild.default_role

        try:
            ticket = await self.ticket_service.create_user_ticket(
                guild=guild,
                creator=moderator,
                support_role=support_role,
                topic=topic
            )
            ticket_channel = guild.get_channel(ticket.channel_id)
            return {
                "status": "success",
                "message": f"Successfully created ticket #{ticket.id}.",
                "channel_id": ticket.channel_id,
                "channel_mention": ticket_channel.mention if ticket_channel else f"ID {ticket.channel_id}"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
