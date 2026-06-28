"""Owner command extension for NoSpaceFGK.

Contains the OwnerCog which will handle administrative bot actions like hot-reloading extensions,
modifying configs, or shutting down the bot in the future.
"""

import logging
from discord.ext import commands

logger = logging.getLogger("NoSpaceFGK.owner")


class OwnerCog(commands.Cog, name="Owner"):
    """Cog designed specifically for bot developer operations and debugging."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the owner cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot
        logger.info("OwnerCog initialized.")


async def setup(bot: commands.Bot) -> None:
    """Load the OwnerCog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(OwnerCog(bot))
