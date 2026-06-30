"""Server Management Cog for NoSpaceFGK."""

import datetime
import json
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

from decorators.command_dec import guild_only_command
from services.server import (
    WelcomeService, GoodbyeService, AutoroleService, ReactionRoleService,
    TicketService, AnnouncementService, VerificationService
)
from utils.embeds import success_embed, error_embed, info_embed, warning_embed
from utils.logger import logger
from services.server.welcome_service import interpolate_variables

class ServerCog(commands.Cog, name="Server"):
    """Cog handling server configuration: welcomes, autoroles, tickets, reaction roles, announcements and verification."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.welcome_service: WelcomeService = bot.container.get(WelcomeService)
        self.goodbye_service: GoodbyeService = bot.container.get(GoodbyeService)
        self.autorole_service: AutoroleService = bot.container.get(AutoroleService)
        self.rr_service: ReactionRoleService = bot.container.get(ReactionRoleService)
        self.ticket_service: TicketService = bot.container.get(TicketService)
        self.announce_service: AnnouncementService = bot.container.get(AnnouncementService)
        self.verify_service: VerificationService = bot.container.get(VerificationService)
        logger.info("ServerCog fully initialized.")

    # ==========================================
    # WELCOME SYSTEM
    # ==========================================
    welcome_group = app_commands.Group(name="welcome", description="Configure server welcome messages.")

    @welcome_group.command(name="setup", description="Setup server welcome settings.")
    @app_commands.describe(
        channel="Target channel for welcome messages.",
        message_text="Welcome text template (supports {user}, {username}, {server}, {member_count}).",
        embed_title="Optional welcome embed title.",
        embed_description="Optional welcome embed description.",
        embed_image_url="Optional welcome embed banner image URL.",
        embed_thumbnail_url="Optional welcome embed thumbnail URL.",
        dm_enabled="Send the welcome notification directly to member DMs.",
        enabled="Enable or disable the welcome system."
    )
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message_text: Optional[str] = None,
        embed_title: Optional[str] = None,
        embed_description: Optional[str] = None,
        embed_image_url: Optional[str] = None,
        embed_thumbnail_url: Optional[str] = None,
        dm_enabled: bool = False,
        enabled: bool = True
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            # Build embed JSON if embed properties are set
            embed_json = None
            if embed_title or embed_description or embed_image_url or embed_thumbnail_url:
                embed_dict = {"title": embed_title or "Welcome!"}
                if embed_description:
                    embed_dict["description"] = embed_description
                if embed_image_url:
                    embed_dict["image"] = {"url": embed_image_url}
                if embed_thumbnail_url:
                    embed_dict["thumbnail"] = {"url": embed_thumbnail_url}
                embed_json = json.dumps(embed_dict)

            await self.welcome_service.save_settings(
                guild_id=interaction.guild_id,
                channel_id=channel.id,
                message_text=message_text,
                embed_json=embed_json,
                dm_enabled=dm_enabled,
                enabled=enabled
            )
            await interaction.followup.send(
                embed=success_embed(
                    "Welcome Settings Updated",
                    f"Successfully configured welcomes in {channel.mention}.\n"
                    f"DM Welcome: **{dm_enabled}** | Enabled: **{enabled}**"
                )
            )
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Setup Error", str(e)))

    @welcome_group.command(name="test", description="Test the welcome configuration by welcoming yourself.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_test(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.welcome_service.welcome_member(interaction.user)
            await interaction.followup.send(embed=success_embed("Welcome Test", "Triggered welcome simulation successfully."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Test Error", str(e)))

    @welcome_group.command(name="disable", description="Disable the welcome system.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def welcome_disable(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            settings = await self.welcome_service.get_settings(interaction.guild_id)
            channel_id = settings.channel_id if settings else None
            await self.welcome_service.save_settings(
                guild_id=interaction.guild_id,
                channel_id=channel_id,
                message_text=settings.message_text if settings else None,
                embed_json=settings.embed_json if settings else None,
                dm_enabled=settings.dm_enabled if settings else False,
                enabled=False
            )
            await interaction.followup.send(embed=success_embed("Welcome System Disabled", "Successfully disabled welcomes."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    # ==========================================
    # GOODBYE SYSTEM
    # ==========================================
    goodbye_group = app_commands.Group(name="goodbye", description="Configure server goodbye messages.")

    @goodbye_group.command(name="setup", description="Setup server goodbye settings.")
    @app_commands.describe(
        channel="Target channel for goodbye messages.",
        message_text="Goodbye text template (supports {user}, {username}, {server}, {member_count}).",
        embed_title="Optional goodbye embed title.",
        embed_description="Optional goodbye embed description.",
        embed_image_url="Optional goodbye embed banner image.",
        enabled="Enable or disable the goodbye system."
    )
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def goodbye_setup(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message_text: Optional[str] = None,
        embed_title: Optional[str] = None,
        embed_description: Optional[str] = None,
        embed_image_url: Optional[str] = None,
        enabled: bool = True
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            embed_json = None
            if embed_title or embed_description or embed_image_url:
                embed_dict = {"title": embed_title or "Goodbye!"}
                if embed_description:
                    embed_dict["description"] = embed_description
                if embed_image_url:
                    embed_dict["image"] = {"url": embed_image_url}
                embed_json = json.dumps(embed_dict)

            await self.goodbye_service.save_settings(
                guild_id=interaction.guild_id,
                channel_id=channel.id,
                message_text=message_text,
                embed_json=embed_json,
                enabled=enabled
            )
            await interaction.followup.send(
                embed=success_embed("Goodbye Settings Updated", f"Successfully configured goodbye notifications in {channel.mention}.")
            )
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Setup Error", str(e)))

    @goodbye_group.command(name="test", description="Test goodbye settings by departing yourself.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def goodbye_test(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.goodbye_service.handle_member_leave(interaction.user)
            await interaction.followup.send(embed=success_embed("Goodbye Test", "Triggered goodbye simulation successfully."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Test Error", str(e)))

    @goodbye_group.command(name="disable", description="Disable goodbye messages.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_guild=True)
    async def goodbye_disable(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            settings = await self.goodbye_service.get_settings(interaction.guild_id)
            channel_id = settings.channel_id if settings else None
            await self.goodbye_service.save_settings(
                guild_id=interaction.guild_id,
                channel_id=channel_id,
                message_text=settings.message_text if settings else None,
                embed_json=settings.embed_json if settings else None,
                enabled=False
            )
            await interaction.followup.send(embed=success_embed("Goodbye System Disabled", "Successfully disabled goodbyes."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    # ==========================================
    # AUTOROLE
    # ==========================================
    autorole_group = app_commands.Group(name="autorole", description="Configure roles assigned to joining members.")

    @autorole_group.command(name="add", description="Add a role to the autorole list.")
    @app_commands.describe(role="Role to assign automatically.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole_add(self, interaction: discord.Interaction, role: discord.Role) -> None:
        await interaction.response.defer(ephemeral=True)
        # Validate hierarchy
        if role >= interaction.guild.me.top_role:
            await interaction.followup.send(embed=error_embed("Hierarchy Error", f"Cannot add **{role.name}** because it is equal or higher than bot top role."))
            return

        try:
            await self.autorole_service.add_autorole(interaction.guild_id, role.id)
            await interaction.followup.send(embed=success_embed("Autorole Added", f"Added **{role.name}** to joining roles."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @autorole_group.command(name="remove", description="Remove a role from the autorole list.")
    @app_commands.describe(role="Role to remove.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole_remove(self, interaction: discord.Interaction, role: discord.Role) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.autorole_service.remove_autorole(interaction.guild_id, role.id)
            await interaction.followup.send(embed=success_embed("Autorole Removed", f"Removed **{role.name}** from joining roles."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @autorole_group.command(name="list", description="List all autoroles configured.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def autorole_list(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            role_ids = await self.autorole_service.get_autoroles(interaction.guild_id)
            if not role_ids:
                await interaction.followup.send(embed=info_embed("Autoroles List", "No autoroles are currently configured."))
                return

            desc = []
            for rid in role_ids:
                role = interaction.guild.get_role(rid)
                if role:
                    desc.append(f"• {role.mention} (ID: `{rid}`)")
                else:
                    desc.append(f"• *Unknown Role* (ID: `{rid}`)")

            await interaction.followup.send(embed=info_embed("Configured Autoroles", "\n".join(desc)))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    # ==========================================
    # REACTION ROLES
    # ==========================================
    reactionrole_group = app_commands.Group(name="reactionrole", description="Configure reaction role messages.")

    @reactionrole_group.command(name="create", description="Create a new reaction role panel.")
    @app_commands.describe(
        channel="Target channel.",
        title="Title of panel.",
        description="Description body.",
        group_name="Group configuration tag name.",
        type="Format style: 'button', 'select', or 'reaction'."
    )
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rr_create(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        description: str,
        group_name: str,
        type: str
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        if type not in ["button", "select", "reaction"]:
            await interaction.followup.send(embed=error_embed("Invalid Type", "Type must be one of: 'button', 'select', or 'reaction'."))
            return

        embed = discord.Embed(title=title, description=description, color=discord.Color.purple())

        try:
            msg = await channel.send(embed=embed)
            await self.rr_service.create_setup(
                message_id=msg.id,
                guild_id=interaction.guild_id,
                channel_id=channel.id,
                title=title,
                description=description,
                group_name=group_name,
                type_=type
            )
            await interaction.followup.send(embed=success_embed("Reaction Role Panel Created", f"Successfully posted panel (Message ID: `{msg.id}`) in {channel.mention}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @reactionrole_group.command(name="add", description="Add emoji/role mapping to reaction role message.")
    @app_commands.describe(
        message_id="The message ID of reaction role panel.",
        emoji="Emoji or ID for buttons.",
        role="Role to toggle.",
        label="Optional label for buttons/selects."
    )
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rr_add(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role,
        label: Optional[str] = None
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.followup.send(embed=error_embed("Error", "Invalid message ID format."))
            return

        # Validate hierarchy
        if role >= interaction.guild.me.top_role:
            await interaction.followup.send(embed=error_embed("Hierarchy Error", f"Cannot map **{role.name}** (equal or higher than bot highest role)."))
            return

        try:
            setup = await self.rr_service.repo.get_reaction_role_message(msg_id)
            if not setup:
                await interaction.followup.send(embed=error_embed("Not Found", f"No reaction role config found for message ID `{msg_id}`."))
                return

            await self.rr_service.add_role_mapping(
                guild_id=interaction.guild_id,
                message_id=msg_id,
                emoji_or_id=emoji,
                role_id=role.id,
                group_name=label or role.name
            )

            # Re-fetch view and edit message
            guild = interaction.guild
            channel = guild.get_channel(setup.channel_id)
            if channel:
                msg = await channel.fetch_message(msg_id)
                if msg:
                    if setup.type == "reaction":
                        await msg.add_reaction(emoji)
                    else:
                        view = await self.rr_service.build_persistent_view(setup)
                        if view:
                            await msg.edit(view=view)
                            self.bot.add_view(view, message_id=msg_id)

            await interaction.followup.send(embed=success_embed("Role Added", f"Mapped role **{role.name}** to emoji/id **{emoji}** for panel `{msg_id}`."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @reactionrole_group.command(name="remove", description="Remove role mapping from reaction role message.")
    @app_commands.describe(message_id="Panel Message ID.", role="Role to remove.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rr_remove(self, interaction: discord.Interaction, message_id: str, role: discord.Role) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.followup.send(embed=error_embed("Error", "Invalid message ID format."))
            return

        try:
            setup = await self.rr_service.repo.get_reaction_role_message(msg_id)
            if not setup:
                await interaction.followup.send(embed=error_embed("Not Found", f"No config found for panel `{msg_id}`."))
                return

            await self.rr_service.remove_role_mapping(msg_id, role.id)

            # Update view on the message
            guild = interaction.guild
            channel = guild.get_channel(setup.channel_id)
            if channel:
                msg = await channel.fetch_message(msg_id)
                if msg and setup.type in ["button", "select"]:
                    view = await self.rr_service.build_persistent_view(setup)
                    await msg.edit(view=view or discord.ui.View())

            await interaction.followup.send(embed=success_embed("Role Mapping Removed", f"Successfully removed mapping for role **{role.name}**."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @reactionrole_group.command(name="delete", description="Delete the reaction role panel config.")
    @app_commands.describe(message_id="Panel Message ID.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def rr_delete(self, interaction: discord.Interaction, message_id: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            msg_id = int(message_id)
        except ValueError:
            await interaction.followup.send(embed=error_embed("Error", "Invalid message ID format."))
            return

        try:
            setup = await self.rr_service.repo.get_reaction_role_message(msg_id)
            if not setup:
                await interaction.followup.send(embed=error_embed("Not Found", "Panel config not found."))
                return

            await self.rr_service.delete_setup(msg_id)

            # Try deleting the message from channel
            guild = interaction.guild
            channel = guild.get_channel(setup.channel_id)
            if channel:
                try:
                    msg = await channel.fetch_message(msg_id)
                    await msg.delete()
                except discord.NotFound:
                    pass

            await interaction.followup.send(embed=success_embed("Panel Deleted", f"Successfully deleted panel `{msg_id}` config and message."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    # ==========================================
    # TICKET SYSTEM
    # ==========================================
    ticket_cog_group = app_commands.Group(name="ticket", description="Configure and manage the ticket system.")

    @ticket_cog_group.command(name="panel", description="Send a ticket creation panel message.")
    @app_commands.describe(
        title="Title of the ticket panel.",
        description="Description body.",
        support_role="Staff/Support role authorized to handle tickets.",
        category="Category channel to create tickets under.",
        channel="Optional channel to post the panel (defaults to current)."
    )
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_panel(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str,
        support_role: discord.Role,
        category: Optional[discord.CategoryChannel] = None,
        channel: Optional[discord.TextChannel] = None
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.followup.send(embed=error_embed("Error", "Must specify a text channel."))
            return

        embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
        from services.server.ticket_service import TicketPanelOpenView
        view = TicketPanelOpenView(self.ticket_service, support_role, category)

        try:
            msg = await target_channel.send(embed=embed, view=view)
            self.bot.add_view(view, message_id=msg.id)
            await interaction.followup.send(embed=success_embed("Ticket Panel Created", f"Successfully posted panel in {target_channel.mention}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @app_commands.command(name="close", description="Close the current support ticket.")
    @app_commands.describe(reason="Reason for closing the ticket.")
    @guild_only_command()
    async def ticket_close(self, interaction: discord.Interaction, reason: str = "Closed by command.") -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            transcript = await self.ticket_service.close_ticket(interaction.channel_id, reason)
            await interaction.followup.send("Ticket closed. Transcript generated.", file=transcript)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @app_commands.command(name="add", description="Add a member to the support ticket.")
    @app_commands.describe(member="Member to add.")
    @guild_only_command()
    async def ticket_add(self, interaction: discord.Interaction, member: discord.Member) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.ticket_service.add_user_to_ticket(interaction.channel_id, member)
            await interaction.followup.send(embed=success_embed("User Added", f"Successfully granted access to {member.mention}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @app_commands.command(name="remove", description="Remove a member from the support ticket.")
    @app_commands.describe(member="Member to remove.")
    @guild_only_command()
    async def ticket_remove(self, interaction: discord.Interaction, member: discord.Member) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.ticket_service.remove_user_from_ticket(interaction.channel_id, member)
            await interaction.followup.send(embed=success_embed("User Removed", f"Successfully revoked access from {member.mention}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @app_commands.command(name="rename", description="Rename the ticket channel.")
    @app_commands.describe(name="New channel name.")
    @guild_only_command()
    async def ticket_rename(self, interaction: discord.Interaction, name: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
            if not ticket or ticket.status != "open":
                await interaction.followup.send(embed=error_embed("Error", "Not an active ticket channel."))
                return

            await interaction.channel.edit(name=name.lower())
            await interaction.followup.send(embed=success_embed("Channel Renamed", f"Successfully renamed ticket channel to **{name.lower()}**."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @app_commands.command(name="transcript", description="Generate a transcript of the ticket conversation.")
    @guild_only_command()
    async def ticket_transcript(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
            if not ticket:
                await interaction.followup.send(embed=error_embed("Error", "Not a ticket channel."))
                return

            messages = await self.ticket_service.repo.get_messages(ticket.id)
            transcript_content = f"--- Transcript for Ticket #{ticket.id} ---\n"
            for m in messages:
                transcript_content += f"[{m.created_at}] {m.author_name}: {m.content}\n"

            import io
            file = discord.File(io.BytesIO(transcript_content.encode("utf-8")), filename=f"transcript-{ticket.id}.txt")
            await interaction.followup.send("Here is the ticket transcript:", file=file)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @app_commands.command(name="delete", description="Delete the current ticket channel.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def ticket_delete(self, interaction: discord.Interaction) -> None:
        try:
            ticket = await self.ticket_service.get_ticket_by_channel(interaction.channel_id)
            if not ticket:
                await interaction.response.send_message(embed=error_embed("Error", "Not a ticket channel."), ephemeral=True)
                return

            await interaction.response.send_message("Deleting channel in 3 seconds...", ephemeral=True)
            await asyncio.sleep(3)
            await interaction.channel.delete()
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    # ==========================================
    # ANNOUNCEMENTS
    # ==========================================
    announce_cog_group = app_commands.Group(name="announce", description="Manage guild announcements.")

    @announce_cog_group.command(name="send", description="Send an announcement immediately.")
    @app_commands.describe(
        channel="Target text channel.",
        message="Message body content.",
        embed_title="Optional embed title.",
        embed_description="Optional embed description.",
        button_label="Optional button label.",
        button_url="Optional button link URL (requires label)."
    )
    @guild_only_command()
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def announce_send(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message: Optional[str] = None,
        embed_title: Optional[str] = None,
        embed_description: Optional[str] = None,
        button_label: Optional[str] = None,
        button_url: Optional[str] = None
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            embed_json = None
            if embed_title or embed_description or (button_label and button_url):
                embed_dict = {}
                if embed_title or embed_description:
                    embed_dict["embed"] = {
                        "title": embed_title or "Announcement",
                        "description": embed_description or ""
                    }
                if button_label and button_url:
                    embed_dict["button_label"] = button_label
                    embed_dict["button_url"] = button_url
                embed_json = json.dumps(embed_dict)

            await self.announce_service.create_announcement(
                guild_id=interaction.guild_id,
                channel_id=channel.id,
                message_text=message,
                embed_json=embed_json,
                scheduled_at=None
            )
            await interaction.followup.send(embed=success_embed("Announcement Dispatched", f"Announcement successfully sent to {channel.mention}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @announce_cog_group.command(name="schedule", description="Schedule an announcement.")
    @app_commands.describe(
        channel="Target channel.",
        time_delay="Time delay (e.g. 10m, 1h, 1d).",
        message="Message content.",
        embed_title="Optional embed title.",
        embed_description="Optional embed description."
    )
    @guild_only_command()
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def announce_schedule(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        time_delay: str,
        message: Optional[str] = None,
        embed_title: Optional[str] = None,
        embed_description: Optional[str] = None
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        # Parse delay
        from cogs.moderation import parse_duration
        try:
            seconds = parse_duration(time_delay)
        except ValueError as ve:
            await interaction.followup.send(embed=error_embed("Invalid Delay", str(ve)))
            return

        scheduled_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=seconds)

        try:
            embed_json = None
            if embed_title or embed_description:
                embed_json = json.dumps({
                    "title": embed_title or "Announcement",
                    "description": embed_description or ""
                })

            announcement = await self.announce_service.create_announcement(
                guild_id=interaction.guild_id,
                channel_id=channel.id,
                message_text=message,
                embed_json=embed_json,
                scheduled_at=scheduled_at
            )
            await interaction.followup.send(
                embed=success_embed(
                    "Announcement Scheduled",
                    f"Announcement #{announcement.id} scheduled for {scheduled_at.strftime('%Y-%m-%d %H:%M:%S')} (Delay: {time_delay})."
                )
            )
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @announce_cog_group.command(name="delete", description="Cancel a scheduled announcement.")
    @app_commands.describe(announcement_id="ID of scheduled announcement.")
    @guild_only_command()
    @app_commands.checks.has_permissions(mention_everyone=True)
    async def announce_delete(self, interaction: discord.Interaction, announcement_id: int) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.announce_service.delete_announcement(announcement_id)
            await interaction.followup.send(embed=success_embed("Announcement Cancelled", f"Successfully cancelled announcement #{announcement_id}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    # ==========================================
    # VERIFICATION
    # ==========================================
    verify_cog_group = app_commands.Group(name="verify", description="Manage member verification settings.")

    @verify_cog_group.command(name="setup", description="Setup server verification panel.")
    @app_commands.describe(channel="Channel to post verification panel.", role="Role to assign upon successful verification.")
    @guild_only_command()
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role) -> None:
        await interaction.response.defer(ephemeral=True)
        if role >= interaction.guild.me.top_role:
            await interaction.followup.send(embed=error_embed("Hierarchy Error", "The verification role must be below the bot's highest role."))
            return

        try:
            await self.verify_service.send_verification_panel(interaction.guild, channel.id, role.id)
            # Re-register views
            from services.server.verification_service import VerificationLaunchView
            view = VerificationLaunchView(self.verify_service, role.id)
            self.bot.add_view(view)
            
            await interaction.followup.send(embed=success_embed("Verification Gate Configured", f"Successfully posted panel in {channel.mention}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))

    @verify_cog_group.command(name="disable", description="Disable verification settings.")
    @guild_only_command()
    @app_commands.checks.has_permissions(administrator=True)
    async def verify_disable(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.verify_service.save_settings(interaction.guild_id, None, None, False)
            await interaction.followup.send(embed=success_embed("Verification Disabled", "Successfully disabled captcha gate verification."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Error", str(e)))


async def setup(bot: commands.Bot) -> None:
    """Load Server cog."""
    await bot.add_cog(ServerCog(bot))
