"""Welcome Service for handling new member notifications."""

import json
from typing import Any, Optional
import discord
from models.welcome import WelcomeSettingsModel
from repository.welcome_repository import WelcomeRepository
from services.base_service import BaseService
from services.cache_service import CacheService
from utils.logger import logger

def interpolate_variables(text: Optional[str], member: discord.Member) -> str:
    """Safely replace placeholders in message templates without raising KeyError."""
    if not text:
        return ""
    replacements = {
        "{user}": member.mention,
        "{username}": member.name,
        "{server}": member.guild.name,
        "{member_count}": str(member.guild.member_count),
    }
    result = text
    for key, val in replacements.items():
        result = result.replace(key, val)
    return result

class WelcomeService(BaseService):
    """Orchestrates welcoming new guild members via text, embeds, and DMs."""

    def __init__(self, welcome_repo: WelcomeRepository, cache_service: CacheService) -> None:
        self.repo = welcome_repo
        self.cache = cache_service

    async def get_settings(self, guild_id: int) -> Optional[WelcomeSettingsModel]:
        """Fetch settings with cache layer."""
        cache_key = f"welcome_settings:{guild_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        settings = await self.repo.get_welcome_settings(guild_id)
        if settings:
            self.cache.set(cache_key, settings)
        return settings

    async def save_settings(
        self,
        guild_id: int,
        channel_id: Optional[int],
        message_text: Optional[str],
        embed_json: Optional[str],
        dm_enabled: bool,
        enabled: bool
    ) -> WelcomeSettingsModel:
        """Save settings and invalidate cache."""
        settings = await self.repo.save_welcome_settings(
            guild_id=guild_id,
            channel_id=channel_id,
            message_text=message_text,
            embed_json=embed_json,
            dm_enabled=dm_enabled,
            enabled=enabled
        )
        self.cache.set(f"welcome_settings:{guild_id}", settings)
        return settings

    async def welcome_member(self, member: discord.Member) -> None:
        """Dispatch welcome announcements when a member joins."""
        settings = await self.get_settings(member.guild.id)
        if not settings or not settings.enabled:
            return

        logger.info(f"WelcomeService: Welcoming user {member.name} to guild {member.guild.id}")
        
        # Build embed & message text
        msg_text = interpolate_variables(settings.message_text, member)
        embed = None
        if settings.embed_json:
            try:
                interpolated_json = interpolate_variables(settings.embed_json, member)
                embed_dict = json.loads(interpolated_json)
                embed = discord.Embed.from_dict(embed_dict)
            except Exception as e:
                logger.error(f"WelcomeService: Invalid embed JSON: {e}")
                embed = discord.Embed(
                    title="Welcome!",
                    description=f"Welcome {member.mention} to **{member.guild.name}**!",
                    color=discord.Color.blue()
                )
                embed.set_thumbnail(url=member.display_avatar.url)

        # Dispatch to Channel
        if settings.channel_id:
            channel = member.guild.get_channel(settings.channel_id)
            if not channel:
                try:
                    channel = await member.guild.fetch_channel(settings.channel_id)
                except discord.NotFound:
                    logger.warning(f"WelcomeService: Configured channel {settings.channel_id} not found.")
                    channel = None
            
            if channel and isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(content=msg_text if msg_text else None, embed=embed)
                except discord.Forbidden:
                    logger.error(f"WelcomeService: Missing permission to send to channel {settings.channel_id}")

        # Dispatch to DMs
        if settings.dm_enabled:
            try:
                await member.send(content=msg_text if msg_text else None, embed=embed)
            except discord.Forbidden:
                logger.info(f"WelcomeService: User {member.id} has closed DMs. Skipped DM Welcome.")
