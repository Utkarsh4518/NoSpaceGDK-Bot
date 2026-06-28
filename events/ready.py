"""Ready event listeners for NoSpaceFGK."""

import discord
from discord.ext import commands
from utils.logger import logger


class ReadyEvents(commands.Cog, name="ReadyEvents"):
    """Cog handling bot gateway connection and ready status."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the ready events cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Fires when the bot successfully connects to Discord and is ready."""
        logger.info(f"Bot connected. Username: {self.bot.user} | ID: {self.bot.user.id}")
        logger.info(f"Gateway Latency: {self.bot.latency * 1000:.2f}ms")
