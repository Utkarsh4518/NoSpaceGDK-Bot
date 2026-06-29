"""Guild players manager and lifecycle controller for NoSpaceFGK.

Maintains instances of BaseMusicPlayer across active Discord guilds.
"""

import asyncio
from typing import Dict, Optional
import discord
from services.music.base_player import BaseMusicPlayer
from utils.logger import logger


class PlayerManager:
    """Manages creation, destruction, and recovery of active BaseMusicPlayer sessions."""

    def __init__(self, bot: discord.Client) -> None:
        """Initialize the player manager.

        Args:
            bot: The Discord Client instance.
        """
        self.bot: discord.Client = bot
        self._players: Dict[int, BaseMusicPlayer] = {}
        self._lock: asyncio.Lock = asyncio.Lock()

    async def get_player(self, guild_id: int) -> BaseMusicPlayer:
        """Retrieve or create an active music player for a guild.

        Args:
            guild_id: Guild snowflake ID.

        Returns:
            The active BaseMusicPlayer instance.
        """
        async with self._lock:
            if guild_id in self._players:
                return self._players[guild_id]

            logger.info(f"Player manager: Creating player session for Guild {guild_id}.")
            player = BaseMusicPlayer(self.bot, guild_id)
            self._players[guild_id] = player
            return player

    async def remove_player(self, guild_id: int) -> bool:
        """Halt and destroy an active player for a guild.

        Args:
            guild_id: Guild snowflake ID.

        Returns:
            True if player existed and was destroyed, False otherwise.
        """
        async with self._lock:
            if guild_id not in self._players:
                return False

            logger.info(f"Player manager: Terminating player session for Guild {guild_id}.")
            player = self._players.pop(guild_id)
            try:
                await player.destroy()
            except Exception as e:
                logger.error(f"Player manager: Error during player destruction in Guild {guild_id}: {e}", exc_info=True)
            return True

    async def clean_all_players(self) -> None:
        """Halt and clean all active player sessions on bot shutdown."""
        logger.info("Player manager: Cleaning all active guild player sessions...")
        async with self._lock:
            guild_ids = list(self._players.keys())
            for g_id in guild_ids:
                player = self._players.pop(g_id)
                try:
                    await player.destroy()
                except Exception as e:
                    logger.error(f"Player manager: Error cleaning Guild {g_id}: {e}")
            logger.info("Player manager: All guild player sessions cleared.")

    async def recover_session(self, guild_id: int) -> Optional[BaseMusicPlayer]:
        """Placeholder for recovering player session after voice disconnects."""
        logger.info(f"Player manager: Session recovery triggered for Guild {guild_id} (Placeholder).")
        return None
