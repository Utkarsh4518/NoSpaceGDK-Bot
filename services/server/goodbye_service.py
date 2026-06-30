"""Goodbye Service for handling departing members."""

import json
from typing import Optional
import discord
from models.welcome import GoodbyeSettingsModel
from repository.welcome_repository import WelcomeRepository
from services.base_service import BaseService
from services.cache_service import CacheService
from services.server.welcome_service import interpolate_variables
from utils.logger import logger

class GoodbyeService(BaseService):
    """Orchestrates announcements when a member leaves the guild."""

    def __init__(self, welcome_repo: WelcomeRepository, cache_service: CacheService) -> None:
        self.repo = welcome_repo
        self.cache = cache_service

    async def get_settings(self, guild_id: int) -> Optional[GoodbyeSettingsModel]:
        """Fetch settings with cache layer."""
        cache_key = f"goodbye_settings:{guild_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        settings = await self.repo.get_goodbye_settings(guild_id)
        if settings:
            self.cache.set(cache_key, settings)
        return settings

    async def save_settings(
        self,
        guild_id: int,
        channel_id: Optional[int],
        message_text: Optional[str],
        embed_json: Optional[str],
        enabled: bool
    ) -> GoodbyeSettingsModel:
        """Save settings and invalidate cache."""
        settings = await self.repo.save_goodbye_settings(
            guild_id=guild_id,
            channel_id=channel_id,
            message_text=message_text,
            embed_json=embed_json,
            enabled=enabled
        )
        self.cache.set(f"goodbye_settings:{guild_id}", settings)
        return settings

    async def handle_member_leave(self, member: discord.Member) -> None:
        """Dispatch goodbye announcements when a member leaves."""
        settings = await self.get_settings(member.guild.id)
        if not settings or not settings.enabled:
            return

        logger.info(f"GoodbyeService: Handling leave for user {member.name} in guild {member.guild.id}")

        msg_text = interpolate_variables(settings.message_text, member)
        embed = None
        if settings.embed_json:
            try:
                interpolated_json = interpolate_variables(settings.embed_json, member)
                embed_dict = json.loads(interpolated_json)
                embed = discord.Embed.from_dict(embed_dict)
            except Exception as e:
                logger.error(f"GoodbyeService: Invalid embed JSON: {e}")
                embed = discord.Embed(
                    title="Goodbye!",
                    description=f"**{member}** has left the server.",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=member.display_avatar.url)

        if settings.channel_id:
            channel = member.guild.get_channel(settings.channel_id)
            if not channel:
                try:
                    channel = await member.guild.fetch_channel(settings.channel_id)
                except discord.NotFound:
                    logger.warning(f"GoodbyeService: Configured channel {settings.channel_id} not found.")
                    channel = None

            if channel and isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(content=msg_text if msg_text else None, embed=embed)
                except discord.Forbidden:
                    logger.error(f"GoodbyeService: Missing permission to send to channel {settings.channel_id}")
