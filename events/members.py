"""Member join and leave event listeners for NoSpaceFGK."""

import discord
from discord.ext import commands
from utils.logger import logger


class MemberEvents(commands.Cog, name="MemberEvents"):
    """Cog handling guild member joins and leaves."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the member events cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot = bot

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
