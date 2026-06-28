"""Events package for the NoSpaceFGK bot.

Exposes the setup function to load event listener cogs dynamically.
"""

from discord.ext import commands
from events.listeners import EventsCog


async def setup(bot: commands.Bot) -> None:
    """Load the events listener cog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(EventsCog(bot))
