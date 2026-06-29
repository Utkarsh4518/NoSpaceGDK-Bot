"""Enterprise Moderation Cog for NoSpaceFGK."""

import re
from typing import List, Optional
import discord
from discord import app_commands
from discord.ext import commands

from decorators.command_dec import guild_only_command, cooldown_command
from services.moderation.moderation_service import ModerationService
from utils.embeds import success_embed, error_embed, info_embed, warning_embed
from utils.logger import logger

def parse_duration(duration_str: str) -> int:
    """Parse duration strings like 10m, 1h, 2d to seconds."""
    match = re.match(r"^(\d+)([smhd])$", duration_str.strip().lower())
    if not match:
        raise ValueError("Invalid duration format. Use e.g. 10m, 2h, 1d.")
        
    value, unit = match.groups()
    val = int(value)
    
    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400
    }
    return val * multipliers[unit]

class ModerationCog(commands.Cog, name="Moderation"):
    """Cog handling enterprise guild moderation and automated rules control."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.mod: ModerationService = bot.container.get(ModerationService)
        logger.info("ModerationCog fully initialized.")

    @app_commands.command(name="warn", description="Warn a member for a violation.")
    @app_commands.describe(member="Member to warn.", reason="Reason for the warning.", points="Warning points (default: 1).")
    @guild_only_command()
    @app_commands.checks.has_permissions(kick_members=True)
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str, points: int = 1) -> None:
        """Apply a warning point structure to a user and check for escalations."""
        await interaction.response.defer(ephemeral=True)
        try:
            warning = await self.mod.warnings.warn_user(
                guild_id=interaction.guild_id,
                user=member,
                moderator=interaction.user,
                reason=reason,
                points=points
            )
            embed = success_embed(
                "User Warned ⚠️",
                f"Successfully warned **{member}** for: *{reason}*\nSeverity Points: **{points}**"
            )
            embed.set_footer(text=f"Case ID auto-logged | Warning ID: {warning.id}")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="warnings", description="View warnings history for a member.")
    @app_commands.describe(member="Target member.", active_only="Filter only active warnings.")
    @guild_only_command()
    @app_commands.checks.has_permissions(kick_members=True)
    async def warnings(self, interaction: discord.Interaction, member: discord.Member, active_only: bool = False) -> None:
        """Fetch and list warnings records from DB."""
        await interaction.response.defer(ephemeral=True)
        try:
            warns = await self.mod.warnings.get_warnings(interaction.guild_id, member.id, active_only=active_only)
            if not warns:
                await interaction.followup.send(embed=info_embed("Warning History", f"**{member}** has no active or past warnings."))
                return
                
            desc = []
            for w in warns:
                status = "🟢 Active" if not w.is_expired else "🔴 Expired"
                date_str = w.created_at.strftime("%Y-%m-%d %H:%M")
                desc.append(f"• **ID {w.id}** ({date_str}) | Points: **{w.points}** | Status: {status}\n  Reason: *{w.reason}*")
                
            embed = info_embed(f"Warning History for {member}", "\n\n".join(desc))
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="clearwarnings", description="Clear active warnings for a member.")
    @app_commands.describe(member="Target member.")
    @guild_only_command()
    @app_commands.checks.has_permissions(ban_members=True)
    async def clearwarnings(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Clear all active warnings (mark as expired)."""
        await interaction.response.defer(ephemeral=True)
        try:
            cleared_count = await self.mod.warnings.clear_warnings(interaction.guild_id, member.id)
            embed = success_embed("Warnings Cleared", f"Successfully cleared **{cleared_count}** active warnings for **{member}**.")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(member="Member to kick.", reason="Reason for the kick.")
    @guild_only_command()
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        """Kick a member and log the event."""
        await interaction.response.defer(ephemeral=True)
        try:
            await self.mod.kick_user(interaction.guild, member, interaction.user, reason)
            embed = success_embed("User Kicked", f"Successfully kicked **{member}** from the server.\nReason: *{reason}*")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(member="Member or User ID to ban.", reason="Reason for the ban.")
    @guild_only_command()
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        """Ban a member and log the event."""
        await interaction.response.defer(ephemeral=True)
        try:
            await self.mod.ban_user(interaction.guild, member, interaction.user, reason)
            embed = success_embed("User Banned", f"Successfully banned **{member}** from the server.\nReason: *{reason}*")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="unban", description="Unban a user from the server by their ID.")
    @app_commands.describe(user_id="ID of banned user.", reason="Reason for unbanning.")
    @guild_only_command()
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(self, interaction: discord.Interaction, user_id: str, reason: str) -> None:
        """Unban user by snowflake ID."""
        await interaction.response.defer(ephemeral=True)
        try:
            uid = int(user_id)
            await self.mod.unban_user(interaction.guild, uid, interaction.user, reason)
            embed = success_embed("User Unbanned", f"Successfully unbanned user ID **{user_id}**.\nReason: *{reason}*")
            await interaction.followup.send(embed=embed)
        except ValueError:
            await interaction.followup.send(embed=error_embed("Moderation Error", "Invalid user ID provided."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="timeout", description="Apply a communication timeout to a member.")
    @app_commands.describe(member="Member to timeout.", duration="Duration string (e.g. 10m, 1h, 1d).", reason="Reason.")
    @guild_only_command()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str) -> None:
        """Apply native timeout restriction."""
        await interaction.response.defer(ephemeral=True)
        try:
            secs = parse_duration(duration)
            await self.mod.timeout_user(interaction.guild, member, interaction.user, secs, reason)
            embed = success_embed("User Timed Out", f"Successfully timed out **{member}** for **{duration}**.\nReason: *{reason}*")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="untimeout", description="Remove a communication timeout from a member.")
    @app_commands.describe(member="Member to untimeout.", reason="Reason.")
    @guild_only_command()
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        """Revoke native timeout restriction."""
        await interaction.response.defer(ephemeral=True)
        try:
            await self.mod.untimeout_user(interaction.guild, member, interaction.user, reason)
            embed = success_embed("Timeout Removed", f"Successfully removed timeout for **{member}**.\nReason: *{reason}*")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="mute", description="Mute a member via Muted role.")
    @app_commands.describe(member="Member to mute.", reason="Reason.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def mute(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.mod.mute_user(interaction.guild, member, interaction.user, reason)
            await interaction.followup.send(embed=success_embed("Member Muted", f"Successfully muted **{member}** via Muted role.\nReason: *{reason}*"))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="unmute", description="Unmute a member via Muted role removal.")
    @app_commands.describe(member="Member to unmute.", reason="Reason.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_roles=True)
    async def unmute(self, interaction: discord.Interaction, member: discord.Member, reason: str) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.mod.unmute_user(interaction.guild, member, interaction.user, reason)
            await interaction.followup.send(embed=success_embed("Member Unmuted", f"Successfully unmuted **{member}**.\nReason: *{reason}*"))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Moderation Error", str(e)))

    @app_commands.command(name="purge", description="Purge messages in this channel.")
    @app_commands.describe(limit="Number of messages to clear.", target_user="Target a specific user's messages.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, limit: int, target_user: Optional[discord.Member] = None) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            deleted = await self.mod.purge_messages(interaction.channel, interaction.user, limit, target_user)
            await interaction.followup.send(embed=success_embed("Purge Completed", f"Successfully deleted **{deleted}** messages."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Purge Failed", str(e)))

    @app_commands.command(name="slowmode", description="Set slowmode delay in seconds for this channel.")
    @app_commands.describe(delay_seconds="Delay in seconds (0 to turn off).")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(self, interaction: discord.Interaction, delay_seconds: int) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.mod.set_slowmode(interaction.channel, interaction.user, delay_seconds)
            status = f"set to {delay_seconds} seconds" if delay_seconds > 0 else "disabled"
            await interaction.followup.send(embed=success_embed("Slowmode Updated", f"Successfully {status} slowmode delay in this channel."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Slowmode Error", str(e)))

    @app_commands.command(name="nick", description="Change a member's nickname.")
    @app_commands.describe(member="Target member.", nickname="New nickname (leave empty to reset).")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nick(self, interaction: discord.Interaction, member: discord.Member, nickname: Optional[str] = None) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            await self.mod.change_nickname(member, interaction.user, nickname)
            status = f"updated to: **{nickname}**" if nickname else "reset to default"
            await interaction.followup.send(embed=success_embed("Nickname Changed", f"Successfully {status} for **{member}**."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Nickname Error", str(e)))

    @app_commands.command(name="lock", description="Lock this channel.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            success = await self.mod.lockdowns.lock_channel(interaction.guild, interaction.channel, interaction.user)
            if success:
                await interaction.followup.send(embed=success_embed("Channel Locked", "This channel has been successfully locked down."))
            else:
                await interaction.followup.send(embed=error_embed("Lock Failed", "Failed to lock the channel."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Lock Error", str(e)))

    @app_commands.command(name="unlock", description="Unlock this channel.")
    @guild_only_command()
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            success = await self.mod.lockdowns.unlock_channel(interaction.guild, interaction.channel)
            if success:
                await interaction.followup.send(embed=success_embed("Channel Unlocked", "This channel has been successfully unlocked."))
            else:
                await interaction.followup.send(embed=error_embed("Unlock Failed", "Failed to unlock the channel."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Unlock Error", str(e)))

    @app_commands.command(name="lockdown", description="Guild, Category, or Channel wide lockdown activation.")
    @app_commands.describe(scope="Scope of lockdown: 'guild', 'category', 'channel'", target_id="Snowflake ID of target category/channel (leave empty for current channel).")
    @guild_only_command()
    @app_commands.checks.has_permissions(administrator=True)
    async def lockdown(self, interaction: discord.Interaction, scope: str, target_id: Optional[str] = None) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            scope_clean = scope.lower().strip()
            guild = interaction.guild
            
            if scope_clean == "guild":
                await self.mod.lockdowns.lock_guild(guild, interaction.user)
                await interaction.followup.send(embed=success_embed("Guild Lockdown", "Successfully activated guild-wide lockdown. All standard text/voice channels restricted."))
            elif scope_clean == "category":
                if not target_id:
                    return await interaction.followup.send(embed=error_embed("Lockdown Error", "Category ID is required to execute category lockdown."))
                category = guild.get_channel(int(target_id))
                if not isinstance(category, discord.CategoryChannel):
                    return await interaction.followup.send(embed=error_embed("Lockdown Error", "Invalid Category ID provided."))
                await self.mod.lockdowns.lock_category(guild, category, interaction.user)
                await interaction.followup.send(embed=success_embed("Category Lockdown", f"Successfully locked down all channels in category **{category.name}**."))
            else: # channel
                chan = guild.get_channel(int(target_id)) if target_id else interaction.channel
                await self.mod.lockdowns.lock_channel(guild, chan, interaction.user)
                await interaction.followup.send(embed=success_embed("Channel Lockdown", f"Successfully locked down channel: {chan.mention}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Lockdown Error", str(e)))

    @app_commands.command(name="unlockdown", description="Unlock guild, category, or channel wide lockdowns.")
    @app_commands.describe(scope="Scope to unlock: 'guild', 'category', 'channel'", target_id="ID of target.")
    @guild_only_command()
    @app_commands.checks.has_permissions(administrator=True)
    async def unlockdown(self, interaction: discord.Interaction, scope: str, target_id: Optional[str] = None) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            scope_clean = scope.lower().strip()
            guild = interaction.guild
            
            if scope_clean == "guild":
                await self.mod.lockdowns.unlock_guild(guild)
                await interaction.followup.send(embed=success_embed("Guild Unlocked", "Successfully deactivated guild-wide lockdown. Permission overwrites restored."))
            elif scope_clean == "category":
                if not target_id:
                    return await interaction.followup.send(embed=error_embed("Lockdown Error", "Category ID is required."))
                category = guild.get_channel(int(target_id))
                if not isinstance(category, discord.CategoryChannel):
                    return await interaction.followup.send(embed=error_embed("Lockdown Error", "Invalid Category ID."))
                await self.mod.lockdowns.unlock_category(guild, category)
                await interaction.followup.send(embed=success_embed("Category Unlocked", f"Successfully restored permissions for category **{category.name}**."))
            else:
                chan = guild.get_channel(int(target_id)) if target_id else interaction.channel
                await self.mod.lockdowns.unlock_channel(guild, chan)
                await interaction.followup.send(embed=success_embed("Channel Unlocked", f"Successfully unlocked channel: {chan.mention}."))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Lockdown Error", str(e)))

    @app_commands.command(name="modstats", description="Show moderation statistics for this server.")
    @guild_only_command()
    @app_commands.checks.has_permissions(kick_members=True)
    async def modstats(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            stats = await self.mod.stats.get_stats(interaction.guild_id)
            embed = info_embed(
                f"Moderation Statistics for {interaction.guild.name} 📊",
                f"**Total Warnings Issued**: `{stats.total_warns}`\n"
                f"**Total Kicks Executed**: `{stats.total_kicks}`\n"
                f"**Total Bans Executed**: `{stats.total_bans}`\n"
                f"**Total Timeouts Applied**: `{stats.total_timeouts}`\n"
                f"**Total Automod Rule Triggers**: `{stats.total_automod_triggers}`"
            )
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Statistics Error", str(e)))

    @app_commands.command(name="case", description="Look up details of a specific moderation case by its ID.")
    @app_commands.describe(case_id="The unique Case ID.")
    @guild_only_command()
    @app_commands.checks.has_permissions(kick_members=True)
    async def case(self, interaction: discord.Interaction, case_id: int) -> None:
        await interaction.response.defer(ephemeral=True)
        try:
            c = await self.mod.cases.get_case(case_id)
            if not c or c.guild_id != interaction.guild_id:
                return await interaction.followup.send(embed=error_embed("Case Lookup Failed", f"Case #{case_id} not found in this server."))
                
            embed = info_embed(
                f"Case #{c.id}: {c.case_type.upper()} 📄",
                f"**Target User ID**: `{c.user_id}`\n"
                f"**Moderator ID**: `{c.moderator_id}`\n"
                f"**Status**: `{c.status}`\n"
                f"**Reason**: *{c.reason}*\n"
                f"**Timestamp**: `{c.created_at.strftime('%Y-%m-%d %H:%M:%S')}`"
            )
            if c.duration_seconds:
                embed.description += f"\n**Duration**: `{c.duration_seconds} seconds`"
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Case Lookup Error", str(e)))

async def setup(bot: commands.Bot) -> None:
    """Load the ModerationCog into the bot."""
    await bot.add_cog(ModerationCog(bot))
