"""Error event listeners for NoSpaceFGK."""

import discord
from discord.ext import commands
from utils.logger import logger, log_exception


class ErrorEvents(commands.Cog, name="ErrorEvents"):
    """Cog handling traditional command execution errors and exceptions."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the error events cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Fires whenever a traditional prefix command encounters an error.

        Args:
            ctx: The execution context of the command.
            error: The error that was raised.
        """
        if isinstance(error, commands.CommandNotFound):
            logger.warning(f"Command not found: '{ctx.message.content}' from User: {ctx.author.id}")
            return

        log_exception(error, f"Prefix command '{ctx.command}' failed:")
