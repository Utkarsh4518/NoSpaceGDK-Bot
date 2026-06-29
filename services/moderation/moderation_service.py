"""Moderation Service Coordinator Facade for NoSpaceFGK bot."""

import datetime
from typing import Any, List, Optional
import discord
from repositories.guild_settings_repository import GuildSettingsRepository
from repositories.moderation_stats_repository import ModerationStatsRepository
from services.moderation.audit_service import AuditService
from services.moderation.case_service import CaseService
from services.moderation.warning_service import WarningService
from services.moderation.lockdown_service import LockdownService
from services.moderation.automod_service import AutomodService
from services.base_service import BaseService

class ModerationService(BaseService):
    """Facade for moderation rules execution, permission enforcement, and state auditing."""

    def __init__(
        self,
        bot: Any,
        settings_repo: GuildSettingsRepository,
        stats_repo: ModerationStatsRepository,
        audit_service: AuditService,
        case_service: CaseService,
        warning_service: WarningService,
        lockdown_service: LockdownService,
        automod_service: AutomodService
    ) -> None:
        self.bot = bot
        self.settings = settings_repo
        self.stats = stats_repo
        self.audit = audit_service
        self.cases = case_service
        self.warnings = warning_service
        self.lockdowns = lockdown_service
        self.automod = automod_service

    async def validate_hierarchy(self, moderator: discord.Member, target: discord.Member) -> None:
        """Enforces role level constraints, self moderation limits, and protected role configurations."""
        # 1. Self moderation block
        if moderator.id == target.id:
            raise ValueError("Self moderation is not permitted.")

        # 2. Owner moderation block
        is_owner = await self.bot.is_owner(target)
        if is_owner:
            raise ValueError("You cannot execute moderation actions on the bot owner.")

        # 3. Role hierarchy block (except if moderator is guild owner)
        if moderator.id != moderator.guild.owner_id:
            if moderator.top_role <= target.top_role:
                raise ValueError("Role hierarchy violation: Target has equal or higher role hierarchy.")

        # 4. Bot hierarchy block
        bot_member = moderator.guild.me
        if bot_member.top_role <= target.top_role:
            raise ValueError("Bot hierarchy violation: Target has equal or higher role hierarchy than the bot.")

        # 5. Protected roles check
        guild_settings = await self.settings.get_settings(moderator.guild.id)
        for role in target.roles:
            if role.id in guild_settings.protected_roles:
                raise ValueError("Protected role violation: Target belongs to a protected role group.")

    async def ban_user(self, guild: discord.Guild, target: discord.Member | discord.User, moderator: discord.Member | discord.User, reason: Optional[str] = None) -> None:
        if isinstance(moderator, discord.Member) and isinstance(target, discord.Member):
            await self.validate_hierarchy(moderator, target)

        await guild.ban(target, reason=reason)
        await self.cases.create_case(guild.id, "ban", target, moderator, reason)

    async def unban_user(self, guild: discord.Guild, target_id: int, moderator: discord.Member | discord.User, reason: Optional[str] = None) -> None:
        # Fetch banned user to confirm and get name
        try:
            ban_entry = await guild.fetch_ban(discord.Object(id=target_id))
            target = ban_entry.user
        except discord.NotFound:
            raise ValueError("User is not currently banned in this guild.")
            
        await guild.unban(target, reason=reason)
        await self.cases.create_case(guild.id, "unban", target, moderator, reason)

    async def kick_user(self, guild: discord.Guild, target: discord.Member, moderator: discord.Member | discord.User, reason: Optional[str] = None) -> None:
        if isinstance(moderator, discord.Member):
            await self.validate_hierarchy(moderator, target)

        await target.kick(reason=reason)
        await self.cases.create_case(guild.id, "kick", target, moderator, reason)

    async def timeout_user(self, guild: discord.Guild, target: discord.Member, moderator: discord.Member | discord.User, duration_seconds: int, reason: Optional[str] = None) -> None:
        if isinstance(moderator, discord.Member):
            await self.validate_hierarchy(moderator, target)

        duration = datetime.timedelta(seconds=duration_seconds)
        await target.timeout(duration, reason=reason)
        await self.cases.create_case(guild.id, "timeout", target, moderator, reason, duration_seconds=duration_seconds)

    async def untimeout_user(self, guild: discord.Guild, target: discord.Member, moderator: discord.Member | discord.User, reason: Optional[str] = None) -> None:
        if isinstance(moderator, discord.Member):
            await self.validate_hierarchy(moderator, target)

        await target.timeout(None, reason=reason)
        await self.cases.create_case(guild.id, "untimeout", target, moderator, reason)

    async def mute_user(self, guild: discord.Guild, target: discord.Member, moderator: discord.Member | discord.User, reason: Optional[str] = None) -> None:
        if isinstance(moderator, discord.Member):
            await self.validate_hierarchy(moderator, target)

        # 1. Fetch or create "Muted" role
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            muted_role = await guild.create_role(name="Muted", reason="Automatic Muted role creation.")
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    try:
                        await channel.set_permissions(muted_role, send_messages=False, add_reactions=False)
                    except discord.Forbidden:
                        pass

        await target.add_roles(muted_role, reason=reason)
        await self.cases.create_case(guild.id, "mute", target, moderator, reason)

    async def unmute_user(self, guild: discord.Guild, target: discord.Member, moderator: discord.Member | discord.User, reason: Optional[str] = None) -> None:
        if isinstance(moderator, discord.Member):
            await self.validate_hierarchy(moderator, target)

        muted_role = discord.utils.get(guild.roles, name="Muted")
        if not muted_role:
            raise ValueError("Muted role not configured in this server.")

        await target.remove_roles(muted_role, reason=reason)
        await self.cases.create_case(guild.id, "unmute", target, moderator, reason)

    async def purge_messages(self, channel: discord.TextChannel, moderator: discord.Member | discord.User, limit: int, target_user: Optional[discord.Member] = None, reason: Optional[str] = None) -> int:
        def check(m):
            return target_user is None or m.author.id == target_user.id

        deleted = await channel.purge(limit=limit, check=check, reason=reason)
        
        # Log to audit
        target_obj = target_user if target_user else channel
        await self.audit.log_action(
            guild_id=channel.guild.id,
            action_type="purge",
            moderator=moderator,
            target=target_obj,
            reason=reason or f"Purged {len(deleted)} messages.",
            extra_details={"channel_id": channel.id, "messages_deleted": len(deleted)}
        )
        return len(deleted)

    async def change_nickname(self, target: discord.Member, moderator: discord.Member | discord.User, nickname: Optional[str], reason: Optional[str] = None) -> None:
        if isinstance(moderator, discord.Member):
            await self.validate_hierarchy(moderator, target)

        await target.edit(nick=nickname, reason=reason)
        await self.audit.log_action(
            guild_id=target.guild.id,
            action_type="nickname",
            moderator=moderator,
            target=target,
            reason=reason or f"Changed nickname to: {nickname}",
            extra_details={"new_nickname": nickname}
        )

    async def set_slowmode(self, channel: discord.TextChannel, moderator: discord.Member | discord.User, delay_seconds: int, reason: Optional[str] = None) -> None:
        await channel.edit(slowmode_delay=delay_seconds, reason=reason)
        await self.audit.log_action(
            guild_id=channel.guild.id,
            action_type="slowmode",
            moderator=moderator,
            target=channel,
            reason=reason or f"Updated slowmode to {delay_seconds} seconds.",
            extra_details={"slowmode_delay": delay_seconds}
        )
