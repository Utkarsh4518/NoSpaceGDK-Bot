"""Moderation command extension for NoSpaceFGK.

Contains the ModerationCog which will manage guild rules, bans, kicks, and timeout logic in the future.
"""

import logging
from discord.ext import commands

logger = logging.getLogger("NoSpaceFGK.moderation")


class ModerationCog(commands.Cog, name="Moderation"):
    """Cog for executing administrative and moderation tasks."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the moderation cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot
        logger.info("ModerationCog initialized.")


async def setup(bot: commands.Bot) -> None:
    """Load the ModerationCog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(ModerationCog(bot))
