"""Message and command completion event listeners for NoSpaceFGK."""

import time
import discord
from discord.ext import commands
from utils.logger import logger, log_command


class MessageEvents(commands.Cog, name="MessageEvents"):
    """Cog handling message-related events and command completions."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the message events cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Fires whenever a message is sent in a channel the bot can see.

        Args:
            message: The Message object containing details of the sent message.
        """
        # Avoid logging its own messages
        if message.author == self.bot.user:
            return

        # Trigger Automod message scan
        if hasattr(self.bot, "container") and self.bot.container:
            try:
                from services.moderation.automod_service import AutomodService
                automod = self.bot.container.get(AutomodService)
                if automod:
                    flagged = await automod.scan_message(message)
                    if flagged:
                        return
            except Exception as e:
                logger.error(f"MessageEvents: Failed to execute automod scan: {e}")

        guild_str = f"Guild: {message.guild.name} ({message.guild.id})" if message.guild else "DMs"
        logger.debug(f"[MESSAGE] Author: {message.author} ({message.author.id}) | {guild_str} | Content: {message.content[:100]}")

    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command
    ) -> None:
        """Fires when a slash command completes successfully.

        Logs execution time, guild, channel, user, and command details.
        """
        start_time = interaction.extras.get("start_time")
        execution_time = time.perf_counter() - start_time if start_time else 0.0

        log_command(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            channel_id=interaction.channel.id if interaction.channel else None,
            command_name=command.qualified_name,
            execution_time=execution_time,
            status="SUCCESS"
        )
