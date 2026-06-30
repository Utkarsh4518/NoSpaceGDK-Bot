"""Member join and leave event listeners for NoSpaceFGK."""

import discord
from discord.ext import commands
from services.server import WelcomeService, GoodbyeService, AutoroleService
from utils.logger import logger



class MemberEvents(commands.Cog, name="MemberEvents"):
    """Cog handling guild member joins and leaves."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the member events cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot = bot
        self.welcome = bot.container.get(WelcomeService)
        self.goodbye = bot.container.get(GoodbyeService)
        self.autorole = bot.container.get(AutoroleService)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Fires when a new member joins a guild.

        Args:
            member: The Member who joined.
        """
        logger.info(f"[MEMBER JOIN] Member: {member} ({member.id}) joined Guild: {member.guild.name} ({member.guild.id})")
        # Welcome message
        try:
            await self.welcome.welcome_member(member)
        except Exception as e:
            logger.error(f"MemberEvents: Welcome handler failed: {e}")

        # Autoroles
        try:
            await self.autorole.assign_autoroles(member)
        except Exception as e:
            logger.error(f"MemberEvents: Autorole handler failed: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Fires when a member leaves or is kicked from a guild.

        Args:
            member: The Member who left.
        """
        logger.info(f"[MEMBER LEAVE] Member: {member} ({member.id}) left Guild: {member.guild.name} ({member.guild.id})")
        # Goodbye message
        try:
            await self.goodbye.handle_member_leave(member)
        except Exception as e:
            logger.error(f"MemberEvents: Goodbye handler failed: {e}")

