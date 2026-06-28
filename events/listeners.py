"""Event listeners for the NoSpaceFGK bot.

Contains the EventsCog which registers listeners for standard Discord gateway events.
"""

import discord
from discord.ext import commands
from utils.logger import logger, log_exception


class EventsCog(commands.Cog, name="Events"):
    """Cog responsible for handling and logging core Discord events."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the events cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot: commands.Bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Fires when the bot successfully connects to Discord and is ready."""
        logger.info(f"Bot connected. Username: {self.bot.user} | ID: {self.bot.user.id}")
        logger.info(f"Gateway Latency: {self.bot.latency * 1000:.2f}ms")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Fires whenever a message is sent in a channel the bot can see.

        Args:
            message: The Message object containing details of the sent message.
        """
        # Avoid logging its own messages
        if message.author == self.bot.user:
            return

        # Simple activity log placeholder
        guild_str = f"Guild: {message.guild.name} ({message.guild.id})" if message.guild else "DMs"
        logger.debug(f"[MESSAGE] Author: {message.author} ({message.author.id}) | {guild_str} | Content: {message.content[:100]}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Fires whenever a traditional prefix command encounters an error.

        Args:
            ctx: The execution context of the command.
            error: The error that was raised.
        """
        # If command not found, usually we ignore or log as warning
        if isinstance(error, commands.CommandNotFound):
            logger.warning(f"Command not found: '{ctx.message.content}' from User: {ctx.author.id}")
            return

        # Log other errors
        log_exception(error, f"Command '{ctx.command}' failed in {ctx.channel}:")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Fires when a new member joins a guild.

        Args:
            member: The Member who joined.
        """
        logger.info(f"[MEMBER JOIN] Member: {member} ({member.id}) joined Guild: {member.guild.name} ({member.guild.id})")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Fires when a member leaves or is kicked from a guild.

        Args:
            member: The Member who left.
        """
        logger.info(f"[MEMBER LEAVE] Member: {member} ({member.id}) left Guild: {member.guild.name} ({member.guild.id})")
