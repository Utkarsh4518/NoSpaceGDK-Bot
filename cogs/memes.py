"""Meme command extension for NoSpaceFGK.

Contains the MemesCog which will handle command generators for image macro formatting and text memes in the future.
"""

import logging
from discord.ext import commands

logger = logging.getLogger("NoSpaceFGK.memes")


class MemesCog(commands.Cog, name="Memes"):
    """Cog for generating memes, joke formatting, and entertainment commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the memes cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot
        logger.info("MemesCog initialized.")


async def setup(bot: commands.Bot) -> None:
    """Load the MemesCog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(MemesCog(bot))
