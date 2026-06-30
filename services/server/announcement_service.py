"""Announcement Service for manual and scheduled announcements."""

import asyncio
import datetime
import json
from typing import Any, Optional, Dict
import discord
from models.announcement import AnnouncementModel
from repository.announcement_repository import AnnouncementRepository
from services.base_service import BaseService
from utils.logger import logger

class AnnouncementService(BaseService):
    """Manages scheduled posts, custom embed setups, and link button attachments."""

    def __init__(self, bot: Any, announce_repo: AnnouncementRepository) -> None:
        self.bot = bot
        self.repo = announce_repo
        self.scheduler_task: Optional[asyncio.Task] = None

    def start_scheduler(self) -> None:
        """Launch the background loop checking for scheduled posts."""
        if not self.scheduler_task:
            self.scheduler_task = self.bot.loop.create_task(self._scheduler_loop())
            logger.info("AnnouncementService: Background scheduler started.")

    async def _scheduler_loop(self) -> None:
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.dispatch_scheduled()
            except Exception as e:
                logger.error(f"AnnouncementService: Error in scheduler loop: {e}", exc_info=True)
            await asyncio.sleep(20)

    async def create_announcement(
        self,
        guild_id: int,
        channel_id: int,
        message_text: Optional[str],
        embed_json: Optional[str],
        scheduled_at: Optional[datetime.datetime] = None
    ) -> AnnouncementModel:
        """Create a scheduled or immediate announcement."""
        # If immediate execution
        if not scheduled_at:
            announcement = await self.repo.create_announcement(guild_id, channel_id, message_text, embed_json, None, status="sent")
            await self._send_msg(guild_id, channel_id, message_text, embed_json)
            await self.repo.update_announcement(announcement.id, status="sent", sent_at=datetime.datetime.now(datetime.timezone.utc))
            return announcement

        # Otherwise schedule
        return await self.repo.create_announcement(guild_id, channel_id, message_text, embed_json, scheduled_at, status="pending")

    async def delete_announcement(self, announcement_id: int) -> None:
        """Cancel a scheduled announcement."""
        await self.repo.delete_announcement(announcement_id)

    async def dispatch_scheduled(self) -> None:
        """Polled function that dispatches pending scheduled announcements that have reached their time."""
        pending = await self.repo.get_pending_announcements()
        now = datetime.datetime.now(datetime.timezone.utc)

        for announce in pending:
            # If scheduled_at has passed
            if announce.scheduled_at and announce.scheduled_at <= now:
                logger.info(f"AnnouncementService: Dispatching scheduled announcement #{announce.id}")
                try:
                    await self._send_msg(announce.guild_id, announce.channel_id, announce.message_text, announce.embed_json)
                    await self.repo.update_announcement(announce.id, status="sent", sent_at=now)
                except Exception as e:
                    logger.error(f"AnnouncementService: Failed to dispatch announcement #{announce.id}: {e}")
                    await self.repo.update_announcement(announce.id, status="failed")

    async def _send_msg(self, guild_id: int, channel_id: int, text: Optional[str], embed_json_str: Optional[str]) -> None:
        """Helper to send custom message and/or embed to target channel."""
        guild = self.bot.get_guild(guild_id)
        if not guild:
            guild = await self.bot.fetch_guild(guild_id)
        if not guild:
            raise ValueError("Guild not found.")

        channel = guild.get_channel(channel_id)
        if not channel:
            channel = await guild.fetch_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            raise ValueError("Text channel not found.")

        embed = None
        view = None
        if embed_json_str:
            try:
                data = json.loads(embed_json_str)
                # Parse embed
                embed = discord.Embed.from_dict(data.get("embed", data))
                
                # Check for link button inside configuration json
                btn_label = data.get("button_label")
                btn_url = data.get("button_url")
                if btn_label and btn_url:
                    view = discord.ui.View()
                    view.add_item(discord.ui.Button(label=btn_label, url=btn_url))
            except Exception as e:
                logger.error(f"AnnouncementService: Failed to parse embed JSON: {e}")
                raise ValueError(f"Failed to parse embed JSON: {e}")

        await channel.send(content=text if text else None, embed=embed, view=view)
