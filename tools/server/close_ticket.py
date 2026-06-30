"""Close Ticket Tool for AI Agent."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.base_tool import BaseTool
from services.server.ticket_service import TicketService

class CloseTicketTool(BaseTool):
    """Tool for closing a support ticket."""

    def __init__(self, service_container: Any) -> None:
        self.services = service_container
        self.ticket_service: TicketService = service_container.get(TicketService)

    @property
    def name(self) -> str:
        return "close_ticket"

    @property
    def description(self) -> str:
        return "Close the support ticket in the current channel. Use this when the user asks to close, solve, or resolve a ticket."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Optional reason for closing the support ticket."
                }
            }
        }

    async def execute(self, **kwargs) -> Any:
        reason = kwargs.get("reason", "Closed by AI Assistant.")
        channel = kwargs["channel"]

        guild = getattr(channel, "guild", None)
        if not guild:
            return {"status": "error", "message": "This command can only be executed within a server."}

        try:
            # Check if this is a ticket channel
            ticket = await self.ticket_service.get_ticket_by_channel(channel.id)
            if not ticket:
                return {"status": "error", "message": "This channel is not an active ticket channel."}

            # Generate transcript and close
            transcript_file = await self.ticket_service.close_ticket(channel.id, reason)
            return {
                "status": "success",
                "message": f"Successfully closed ticket #{ticket.id}.",
                "reason": reason
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
