"""Music streaming extension for NoSpaceFGK.

Contains the MusicCog which will handle voice connection and audio playback in the future.
"""

import logging
from discord.ext import commands

logger = logging.getLogger("NoSpaceFGK.music")


class MusicCog(commands.Cog, name="Music"):
    """Cog for music streaming and audio management commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the music cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot
        logger.info("MusicCog initialized.")


async def setup(bot: commands.Bot) -> None:
    """Load the MusicCog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(MusicCog(bot))
