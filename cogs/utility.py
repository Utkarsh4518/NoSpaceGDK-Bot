"""Utility command extension for NoSpaceFGK.

Contains the UtilityCog which will manage auxiliary features, statistics, and system queries in the future.
"""

import logging
from discord.ext import commands

logger = logging.getLogger("NoSpaceFGK.utility")


class UtilityCog(commands.Cog, name="Utility"):
    """Cog for hosting utility functions, system tools, and information commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the utility cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot
        logger.info("UtilityCog initialized.")


async def setup(bot: commands.Bot) -> None:
    """Load the UtilityCog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(UtilityCog(bot))
