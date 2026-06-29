"""Voice connections lifecycle manager for NoSpaceFGK bot.

Coordinates joins, leaves, and reconnections to Discord guild voice channels.
"""

import asyncio
import discord
from typing import Optional
from models.music import VoiceSession
from utils.logger import logger


class VoiceManager:
    """Manages active Discord VoiceClient handles for a specific guild."""

    def __init__(self, bot: discord.Client, guild_id: int) -> None:
        """Initialize the voice manager.

        Args:
            bot: The Discord Client instance.
            guild_id: Guild snowflake ID.
        """
        self.bot: discord.Client = bot
        self.guild_id: int = guild_id
        self._voice_client: Optional[discord.VoiceClient] = None
        self._session: Optional[VoiceSession] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    async def join_channel(self, channel: discord.VoiceChannel, timeout: float = 10.0) -> discord.VoiceClient:
        """Connect the bot to a Voice Channel.

        Args:
            channel: Target VoiceChannel.
            timeout: Connect timeout limit.

        Returns:
            The connected VoiceClient.
        """
        async with self._lock:
            if self._voice_client and self._voice_client.is_connected():
                if self._voice_client.channel.id == channel.id:
                    return self._voice_client

                logger.info(f"Voice lifecycle: Moving voice client from {self._voice_client.channel.name} to {channel.name}.")
                await self._voice_client.move_to(channel)
                return self._voice_client

            logger.info(f"Voice lifecycle: Connecting to voice channel '{channel.name}' (ID: {channel.id})...")
            try:
                self._voice_client = await channel.connect(timeout=timeout, reconnect=True)
                self._session = VoiceSession(
                    guild_id=self.guild_id,
                    channel_id=channel.id,
                    session_id=self._voice_client.session_id,
                    latency=self._voice_client.latency
                )
                logger.info(f"Voice lifecycle: Successfully connected to voice channel '{channel.name}'.")
                return self._voice_client
            except asyncio.TimeoutError as e:
                logger.error(f"Voice lifecycle: Connection to channel '{channel.name}' timed out.")
                raise TimeoutError(f"Failed to connect to voice channel within {timeout}s.") from e

    async def leave_channel(self) -> bool:
        """Disconnect the voice client from the guild's voice channel."""
        async with self._lock:
            if not self._voice_client:
                return False

            logger.info(f"Voice lifecycle: Disconnecting from voice in Guild {self.guild_id}.")
            try:
                await self._voice_client.disconnect(force=True)
            except Exception as e:
                logger.warning(f"Voice lifecycle: Disconnect warning: {e}")
            finally:
                self._voice_client = None
                self._session = None
            return True

    async def reconnect(self) -> Optional[discord.VoiceClient]:
        """Attempt to re-establish the connection."""
        async with self._lock:
            if self._voice_client and not self._voice_client.is_connected():
                logger.info("Voice lifecycle: Programmatic voice reconnection triggered.")
                channel = self._voice_client.channel
                await self.leave_channel()
                return await self.join_channel(channel)
            return self._voice_client

    @property
    def is_connected(self) -> bool:
        """Check if connection is established."""
        return self._voice_client is not None and self._voice_client.is_connected()

    @property
    def voice_client(self) -> Optional[discord.VoiceClient]:
        """Access raw discord.VoiceClient."""
        return self._voice_client

    @property
    def session(self) -> Optional[VoiceSession]:
        """Access VoiceSession metadata details."""
        return self._session

    def update_state(self) -> None:
        """Invoked when voice states are modified to synchronize latencies."""
        if self._voice_client and self._session:
            self._session.latency = self._voice_client.latency
            logger.debug(f"Voice lifecycle: Synchronized voice state (Latency: {self._voice_client.latency * 1000:.2f}ms).")
