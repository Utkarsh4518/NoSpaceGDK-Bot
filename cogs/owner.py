"""Owner command extension for NoSpaceFGK.

Contains the OwnerCog which handles administrative bot actions like hot-reloading extensions,
modifying configs, or syncing command trees.
"""

import logging
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands
from decorators.command_dec import is_owner
from utils.embeds import success_embed, info_embed, error_embed

logger = logging.getLogger("NoSpaceFGK.owner")


class OwnerCog(commands.Cog, name="Owner"):
    """Cog designed specifically for bot developer operations and debugging."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the owner cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot = bot
        logger.info("OwnerCog initialized.")

    @app_commands.command(name="sync", description="Synchronize application slash commands.")
    @is_owner()
    async def sync(
        self,
        interaction: discord.Interaction,
        action: Literal["guild", "global", "current", "clear"]
    ) -> None:
        """Sync application commands globally or to the current guild.

        Args:
            interaction: The invoking interaction context.
            action: The sync operation to perform.
        """
        # Defer the response as syncing can take a few seconds
        await interaction.response.defer(ephemeral=True)

        bot_instance = self.bot

        try:
            if action == "guild":
                if not interaction.guild:
                    embed = error_embed("Sync Failed", "This command can only be executed in a server.")
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

                await bot_instance.sync_tree(guild_id=interaction.guild.id)
                embed = success_embed(
                    "Sync Success",
                    f"Command tree successfully synchronized locally to guild **{interaction.guild.name}**."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action == "global":
                await bot_instance.sync_tree()
                embed = success_embed(
                    "Sync Success",
                    "Command tree successfully synchronized globally."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action == "clear":
                # Clear global tree cache
                bot_instance.tree.clear_commands(guild=interaction.guild)
                embed = success_embed(
                    "Sync Success",
                    "Command tree cache successfully cleared."
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action == "current":
                cogs_loaded = ", ".join(f"`{cog}`" for cog in bot_instance.cogs.keys()) or "*None*"
                extensions_loaded = ", ".join(f"`{ext}`" for ext in bot_instance.extensions.keys()) or "*None*"
                dev_guild = bot_instance.config.development_guild_id
                dev_guild_str = f"`{dev_guild}`" if dev_guild else "*Not Configured*"

                embed = info_embed(
                    "Bot Sync & Extension Status",
                    "Current operational and configuration loading details."
                )
                embed.add_field(name="Loaded Cogs", value=cogs_loaded, inline=False)
                embed.add_field(name="Loaded Extensions", value=extensions_loaded, inline=False)
                embed.add_field(name="Development Guild ID", value=dev_guild_str, inline=True)
                embed.add_field(name="Ping (Latency)", value=f"`{bot_instance.latency * 1000:.2f}ms`", inline=True)

                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Failed to execute sync operation '{action}': {e}", exc_info=True)
            embed = error_embed("Sync Error", f"Failed to execute operation: {e}")
            await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the OwnerCog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(OwnerCog(bot))
