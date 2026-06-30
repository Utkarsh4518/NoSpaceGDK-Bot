"""Ticket Service for orchestrating private ticket lifecycles and transcripts."""

import datetime
import discord
from typing import Any, List, Optional
from models.ticket import TicketModel
from repository.ticket_repository import TicketRepository
from services.base_service import BaseService
from services.cache_service import CacheService
from utils.logger import logger

class TicketService(BaseService):
    """Orchestrates private channel creation, staff assignments, transcripts, and cleanup."""

    def __init__(self, bot: Any, ticket_repo: TicketRepository, cache_service: CacheService) -> None:
        self.bot = bot
        self.repo = ticket_repo
        self.cache = cache_service

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[TicketModel]:
        """Fetch ticket by channel ID (with cache)."""
        cache_key = f"ticket_channel:{channel_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        ticket = await self.repo.get_ticket_by_channel(channel_id)
        if ticket:
            self.cache.set(cache_key, ticket)
        return ticket

    async def create_user_ticket(
        self,
        guild: discord.Guild,
        creator: discord.Member,
        support_role: discord.Role,
        category: Optional[discord.CategoryChannel] = None,
        topic: Optional[str] = None
    ) -> TicketModel:
        """Create a private channel and register a new ticket."""
        # Check security: User cannot open duplicate open tickets
        existing = await self.repo.get_active_ticket_by_user(guild.id, creator.id)
        if existing:
            # Check if channel still exists in Discord
            existing_channel = guild.get_channel(existing.channel_id)
            if existing_channel:
                raise ValueError(f"You already have an open ticket in {existing_channel.mention}.")
            else:
                # Channel deleted manually, mark closed in DB
                await self.repo.update_ticket(existing.id, "closed", closed_at=datetime.datetime.now(datetime.timezone.utc))

        # Build Permission Overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            creator: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True, attach_files=True),
            support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True, manage_channels=True, manage_permissions=True)
        }

        channel_name = f"ticket-{creator.name.lower()}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=topic or f"Support ticket for {creator}."
        )

        ticket = await self.repo.create_ticket(
            guild_id=guild.id,
            creator_id=creator.id,
            channel_id=ticket_channel.id,
            category_id=category.id if category else None,
            topic=topic
        )

        # Log to participants
        await self.repo.add_participant(ticket.id, creator.id)

        # Send welcome panel inside the ticket channel
        embed = discord.Embed(
            title=f"Ticket #{ticket.id}",
            description=(
                f"Welcome {creator.mention}!\n"
                f"Support staff will be with you shortly. "
                f"You can use the buttons below to close or claim this ticket."
            ),
            color=discord.Color.blue()
        )
        if topic:
            embed.add_field(name="Topic", value=topic)
        
        view = TicketControlView(self, ticket.id)
        await ticket_channel.send(embed=embed, view=view)

        logger.info(f"TicketService: Created ticket channel {ticket_channel.name} (ID: {ticket_channel.id}) for user {creator.id}")
        return ticket

    async def claim_ticket(self, ticket_id: int, staff_member: discord.Member) -> str:
        """Assign staff member to a ticket, locking out other staff if necessary."""
        ticket = await self.repo.get_ticket(ticket_id)
        if not ticket or ticket.status != "open":
            return "Ticket is not open or does not exist."

        if ticket.claimed_by:
            claimed_user = self.bot.get_user(ticket.claimed_by) or f"ID {ticket.claimed_by}"
            return f"Ticket is already claimed by {claimed_user}."

        await self.repo.update_ticket(ticket_id, status="open", claimed_by=staff_member.id)
        self.cache.delete(f"ticket_channel:{ticket.channel_id}")

        guild = staff_member.guild
        channel = guild.get_channel(ticket.channel_id)
        if channel:
            # Grant staff member explicit manage/read overrides
            try:
                await channel.set_permissions(staff_member, read_messages=True, send_messages=True, read_message_history=True)
                await channel.send(
                    embed=discord.Embed(
                        description=f"Ticket has been claimed by {staff_member.mention}.",
                        color=discord.Color.green()
                    )
                )
            except discord.Forbidden:
                pass

        logger.info(f"TicketService: Ticket #{ticket_id} claimed by staff {staff_member.name} ({staff_member.id})")
        return f"Successfully claimed ticket #{ticket_id}."

    async def add_user_to_ticket(self, channel_id: int, member: discord.Member) -> None:
        """Grant a user read/write access to the ticket."""
        ticket = await self.get_ticket_by_channel(channel_id)
        if not ticket or ticket.status != "open":
            raise ValueError("This channel is not an active ticket.")

        guild = member.guild
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.set_permissions(member, read_messages=True, send_messages=True, read_message_history=True)
            await self.repo.add_participant(ticket.id, member.id)
            logger.info(f"TicketService: Added user {member.name} to ticket #{ticket.id}")

    async def remove_user_from_ticket(self, channel_id: int, member: discord.Member) -> None:
        """Remove a user's access from the ticket."""
        ticket = await self.get_ticket_by_channel(channel_id)
        if not ticket or ticket.status != "open":
            raise ValueError("This channel is not an active ticket.")

        if member.id == ticket.creator_id:
            raise ValueError("Cannot remove the ticket creator.")

        guild = member.guild
        channel = guild.get_channel(channel_id)
        if channel:
            await channel.set_permissions(member, overwrite=None)
            await self.repo.remove_participant(ticket.id, member.id)
            logger.info(f"TicketService: Removed user {member.name} from ticket #{ticket.id}")

    async def close_ticket(self, channel_id: int, reason: str = "Closed by staff.") -> discord.File:
        """Close the ticket, disable writes, and return a text transcript File."""
        ticket = await self.get_ticket_by_channel(channel_id)
        if not ticket or ticket.status != "open":
            raise ValueError("This channel is not an active ticket.")

        # Update Database
        now = datetime.datetime.now(datetime.timezone.utc)
        await self.repo.update_ticket(ticket.id, status="closed", closed_at=now)
        self.cache.delete(f"ticket_channel:{channel_id}")

        # Fetch messages to build transcript
        messages = await self.repo.get_messages(ticket.id)
        transcript_content = f"--- Transcript for Ticket #{ticket.id} ---\n"
        transcript_content += f"Created by: User ID {ticket.creator_id}\n"
        transcript_content += f"Closed at: {now.isoformat()} | Reason: {reason}\n"
        transcript_content += "---------------------------------------\n\n"
        for m in messages:
            timestamp = m.created_at.strftime("%Y-%m-%d %H:%M:%S")
            transcript_content += f"[{timestamp}] {m.author_name} ({m.author_id}): {m.content}\n"

        import io
        transcript_file = discord.File(
            fp=io.BytesIO(transcript_content.encode("utf-8")),
            filename=f"ticket-{ticket.id}-transcript.txt"
        )

        guild = self.bot.get_guild(ticket.guild_id)
        channel = guild.get_channel(channel_id) if guild else None
        if channel:
            # Change permissions to read-only for ticket creator
            try:
                creator = guild.get_member(ticket.creator_id)
                if creator:
                    await channel.set_permissions(creator, read_messages=True, send_messages=False, read_message_history=True)
                
                await channel.send(
                    embed=discord.Embed(
                        title="Ticket Closed",
                        description=f"This ticket has been closed.\nReason: *{reason}*",
                        color=discord.Color.red()
                    )
                )
            except discord.Forbidden:
                pass

        logger.info(f"TicketService: Ticket #{ticket.id} closed.")
        return transcript_file

    async def log_ticket_message(self, channel_id: int, author: discord.Member | discord.User, content: str) -> None:
        """Append message to ticket messages repository log."""
        ticket = await self.get_ticket_by_channel(channel_id)
        if ticket and ticket.status == "open":
            await self.repo.add_message(ticket.id, author.id, str(author), content)


class TicketPanelOpenView(discord.ui.View):
    """View containing the 'Open Ticket' button sent in ticket panels."""

    def __init__(self, service: TicketService, support_role: discord.Role, category: Optional[discord.CategoryChannel] = None) -> None:
        super().__init__(timeout=None)
        self.service = service
        self.support_role = support_role
        self.category = category

    @discord.ui.button(label="Open Ticket", emoji="✉️", custom_id="ticket_open_btn", style=discord.ButtonStyle.success)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        try:
            ticket = await self.service.create_user_ticket(
                guild=interaction.guild,
                creator=interaction.user,
                support_role=self.support_role,
                category=self.category
            )
            channel = interaction.guild.get_channel(ticket.channel_id)
            await interaction.followup.send(f"Ticket created! Go to {channel.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)


class TicketControlView(discord.ui.View):
    """View containing Claim and Close controls sent inside ticket channels."""

    def __init__(self, service: TicketService, ticket_id: int) -> None:
        super().__init__(timeout=None)
        self.service = service
        self.ticket_id = ticket_id

    @discord.ui.button(label="Claim", emoji="🙋‍♂️", custom_id="ticket_claim_btn", style=discord.ButtonStyle.primary)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await self.service.claim_ticket(self.ticket_id, interaction.user)
        await interaction.followup.send(content=res, ephemeral=True)

    @discord.ui.button(label="Close", emoji="🔒", custom_id="ticket_close_btn", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Open a simple reason Modal
        modal = TicketCloseModal(self.service, interaction.channel.id)
        await interaction.response.send_modal(modal)


class TicketCloseModal(discord.ui.Modal, title="Close Ticket"):
    """Modal to prompt for a close reason."""

    reason_input = discord.ui.TextInput(
        label="Reason for closing",
        style=discord.TextStyle.short,
        placeholder="e.g. Issue resolved.",
        default="Resolved.",
        required=True
    )

    def __init__(self, service: TicketService, channel_id: int) -> None:
        super().__init__()
        self.service = service
        self.channel_id = channel_id

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            reason = self.reason_input.value
            transcript = await self.service.close_ticket(self.channel_id, reason)
            await interaction.followup.send("Ticket closed successfully. Transcript attached.", file=transcript, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
