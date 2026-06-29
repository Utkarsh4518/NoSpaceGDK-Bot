"""Audit Service for logging moderation actions to DB and Discord channels."""

import datetime
import json
from typing import Any, Optional
import discord
from services.base_service import BaseService
from repositories.guild_settings_repository import GuildSettingsRepository
from utils.logger import logger

class AuditService(BaseService):
    """Logs moderation events to DB and sends notifications to the audit channel."""

    def __init__(self, bot: Any, db: Any, settings_repo: GuildSettingsRepository) -> None:
        """Initialize AuditService.
        
        Args:
            bot: Discord bot instance.
            db: Active database connection manager.
            settings_repo: Guild settings repository.
        """
        self.bot = bot
        self.db = db
        self.settings = settings_repo

    async def log_action(
        self,
        guild_id: int,
        action_type: str,
        moderator: discord.Member | discord.User,
        target: discord.Member | discord.User | discord.abc.GuildChannel,
        reason: Optional[str] = None,
        extra_details: Optional[dict] = None
    ) -> None:
        """Log a moderation action to the database and send an audit log embed to the configured channel.
        
        Args:
            guild_id: Guild snowflake.
            action_type: Type of action ('warn', 'kick', 'ban', 'unban', 'timeout', 'mute', 'lock', etc.).
            moderator: The moderator responsible.
            target: The user or channel target of the action.
            reason: Optional justification.
            extra_details: Extra metadata dict.
        """
        details = extra_details or {}
        details.update({
            "moderator_name": str(moderator),
            "target_name": str(target),
            "reason": reason
        })
        details_str = json.dumps(details)
        
        # 1. Persist to DB
        query = """
            INSERT INTO moderation_audit_logs (guild_id, action_type, moderator_id, target_id, details)
            VALUES (?, ?, ?, ?, ?);
        """
        await self.db.execute(query, (guild_id, action_type, moderator.id, target.id, details_str))
        await self.db.commit()
        
        # 2. Dispatch to Discord channel
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                guild = await self.bot.fetch_guild(guild_id)
                
            guild_settings = await self.settings.get_settings(guild_id)
            if not guild_settings.audit_channel_id:
                return # No audit channel configured
                
            channel = guild.get_channel(guild_settings.audit_channel_id)
            if not channel:
                channel = await guild.fetch_channel(guild_settings.audit_channel_id)
                
            if not channel:
                logger.warning(f"AuditService: Audit channel {guild_settings.audit_channel_id} not found in guild {guild_id}.")
                return
                
            # Create Audit log Embed
            embed = self._create_audit_embed(action_type, moderator, target, reason, details)
            await channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"AuditService: Failed to dispatch audit embed: {e}", exc_info=True)

    def _create_audit_embed(
        self,
        action_type: str,
        moderator: discord.Member | discord.User,
        target: Any,
        reason: Optional[str],
        details: dict
    ) -> discord.Embed:
        """Create a beautiful Audit Log Embed."""
        # Color mapping based on action severity
        colors = {
            "warn": discord.Color.orange(),
            "kick": discord.Color.red(),
            "ban": discord.Color.dark_red(),
            "unban": discord.Color.green(),
            "timeout": discord.Color.gold(),
            "untimeout": discord.Color.green(),
            "mute": discord.Color.blue(),
            "unmute": discord.Color.green(),
            "lock": discord.Color.purple(),
            "unlock": discord.Color.green(),
            "lockdown": discord.Color.dark_purple(),
            "unlockdown": discord.Color.green(),
            "automod": discord.Color.dark_grey()
        }
        
        color = colors.get(action_type, discord.Color.greyple())
        
        embed = discord.Embed(
            title=f"Moderation Action: {action_type.upper()}",
            color=color,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        embed.add_field(name="Target User/Channel", value=f"{target.mention} (ID: {target.id})", inline=True)
        embed.add_field(name="Moderator", value=f"{moderator.mention} (ID: {moderator.id})", inline=True)
        
        if reason:
            embed.add_field(name="Reason", value=reason, inline=False)
            
        for k, v in details.items():
            if k not in ["moderator_name", "target_name", "reason"]:
                embed.add_field(name=k.replace("_", " ").title(), value=str(v), inline=True)
                
        embed.set_footer(text="NoSpaceFGK Enterprise Moderation System")
        return embed
