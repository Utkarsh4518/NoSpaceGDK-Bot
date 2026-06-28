"""AI assistant extension for NoSpaceFGK.

Contains the AICog which will handle AI query responses and conversational logic in the future.
"""

import logging
from discord.ext import commands

logger = logging.getLogger("NoSpaceFGK.ai")


class AICog(commands.Cog, name="AI"):
    """Cog for interacting with AI models and providing conversational assistance."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the AI cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot
        logger.info("AICog initialized.")


async def setup(bot: commands.Bot) -> None:
    """Load the AICog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(AICog(bot))
