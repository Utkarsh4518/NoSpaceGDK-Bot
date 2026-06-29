"""Utility command extension for NoSpaceFGK.

Contains the UtilityCog which hosts general and utility slash commands.
"""

import datetime
import logging
import platform
import time
import discord
from discord import app_commands
from discord.ext import commands
from decorators.command_dec import guild_only_command, cooldown_command
from utils.embeds import success_embed, info_embed, error_embed
from utils.helpers import format_duration, format_timestamp

logger = logging.getLogger("NoSpaceFGK.utility")


class UtilityCog(commands.Cog, name="Utility"):
    """Cog for hosting utility functions, system tools, and information commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the utility cog.

        Args:
            bot: The target Bot instance.
        """
        self.bot = bot
        logger.info("UtilityCog initialized.")

    @app_commands.command(name="ping", description="Check the bot's latency and round-trip speed.")
    async def ping(self, interaction: discord.Interaction) -> None:
        """Ping command checking latency."""
        start_time = time.perf_counter()
        await interaction.response.defer(ephemeral=True)
        end_time = time.perf_counter()

        gateway_latency = self.bot.latency * 1000
        api_latency = (end_time - start_time) * 1000

        embed = success_embed(
            title="Pong! 🏓",
            description=f"**Gateway Latency**: `{gateway_latency:.2f}ms`\n**API Round-trip**: `{api_latency:.2f}ms`"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="about", description="Display details about NoSpaceFGK.")
    async def about(self, interaction: discord.Interaction) -> None:
        """About command displaying bot details."""
        embed = info_embed(
            title="About NoSpaceFGK",
            description="NoSpaceFGK is a modular, production-ready Discord assistant designed for music, AI, utility, and administrative operations."
        )
        embed.add_field(name="Library", value=f"discord.py v{discord.__version__}", inline=True)
        embed.add_field(name="Python Version", value=platform.python_version(), inline=True)
        embed.add_field(name="Developers", value="[Utkarsh](https://github.com/Utkarsh4518)", inline=True)
        embed.add_field(name="Architecture", value="Clean Modular Cog-based architecture with dynamic event discovery.", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="help", description="Browse available command categories.")
    async def help_command(self, interaction: discord.Interaction) -> None:
        """Dynamic interactive help paging system."""
        from ui.pagination import PaginationView

        embeds = []

        # Home Page Embed
        home_embed = info_embed(
            title="Help Directory - Home",
            description="Welcome to **NoSpaceFGK**! Use the buttons below to browse available slash commands by category."
        )
        home_embed.add_field(
            name="How to use",
            value="Navigate pages using ⬅️ and ➡️. Use 🏠 to return home, and ❌ to close the menu.",
            inline=False
        )
        embeds.append(home_embed)

        total_commands = 0
        categories_list = []

        for cog_name, cog in self.bot.cogs.items():
            cog_commands = cog.get_app_commands()
            if not cog_commands:
                continue

            categories_list.append(cog_name)
            total_commands += len(cog_commands)

            cog_embed = info_embed(
                title=f"Help Directory - {cog_name}",
                description=f"Commands registered in the `{cog_name}` category."
            )
            for cmd in cog_commands:
                if isinstance(cmd, discord.app_commands.Group):
                    cog_embed.add_field(
                        name=f"/{cmd.name} [group]",
                        value=f"{cmd.description or 'No description.'}\n*Subcommands: {', '.join(sub.name for sub in cmd.commands)}*",
                        inline=False
                    )
                else:
                    cog_embed.add_field(
                        name=f"/{cmd.name}",
                        value=cmd.description or "No description.",
                        inline=False
                    )
            embeds.append(cog_embed)

        home_embed.add_field(name="Categories", value=", ".join(f"`{c}`" for c in categories_list) or "*None*", inline=True)
        home_embed.add_field(name="Total Commands", value=f"`{total_commands}`", inline=True)

        view = PaginationView(author_id=interaction.user.id, embeds=embeds)
        await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)
        view.message = await interaction.original_response()

    @app_commands.command(name="invite", description="Generate invite link for NoSpaceFGK.")
    async def invite(self, interaction: discord.Interaction) -> None:
        """Invite link generation command."""
        permissions = discord.Permissions(administrator=True)
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=("bot", "applications.commands")
        )
        embed = info_embed(
            title="Invite NoSpaceFGK",
            description=f"Invite the bot to your server using this link:\n[**Add to Server**]({invite_url})"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="support", description="Join the official NoSpaceFGK support server.")
    async def support(self, interaction: discord.Interaction) -> None:
        """Support channel helper command."""
        support_url = "https://discord.gg/your_support_server_code"
        embed = info_embed(
            title="Support Discord",
            description=f"Need help or want to suggest new features?\n[**Join Support Server**]({support_url})"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="serverinfo", description="Display information about the current guild.")
    @guild_only_command()
    async def serverinfo(self, interaction: discord.Interaction) -> None:
        """Server details statistics command."""
        guild = interaction.guild
        if not guild:
            return

        created_at = format_timestamp(guild.created_at, "F")
        features_str = ", ".join(f"`{f}`" for f in guild.features) or "*None*"

        embed = info_embed(
            title=f"Server Info - {guild.name}",
            description=f"Information and statistics for server ID: `{guild.id}`"
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Owner", value=f"{guild.owner} (ID: `{guild.owner_id}`)", inline=False)
        embed.add_field(name="Created At", value=created_at, inline=False)
        embed.add_field(name="Members Count", value=f"Total: `{guild.member_count}`", inline=True)
        embed.add_field(name="Channels", value=f"Text: `{len(guild.text_channels)}` | Voice: `{len(guild.voice_channels)}`", inline=True)
        embed.add_field(name="Verification Level", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="Features", value=features_str, inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="userinfo", description="Display detailed information about a member.")
    @app_commands.describe(member="The member to inspect.")
    @guild_only_command()
    async def userinfo(self, interaction: discord.Interaction, member: discord.Member = None) -> None:
        """Inspect detailed member parameters."""
        target_member = member or interaction.user  # type: ignore

        # We need to coerce type correctly if executed in guild
        if not isinstance(target_member, discord.Member):
            return

        created_at = format_timestamp(target_member.created_at, "F")
        joined_at = format_timestamp(target_member.joined_at, "F") if target_member.joined_at else "*Unknown*"
        roles_str = ", ".join(r.mention for r in target_member.roles[1:][::-1]) or "*None*"

        embed = info_embed(
            title=f"User Info - {target_member}",
            description=f"User details for ID: `{target_member.id}`"
        )
        embed.set_thumbnail(url=target_member.display_avatar.url)
        embed.add_field(name="Display Name", value=target_member.display_name, inline=True)
        embed.add_field(name="Bot Account?", value="Yes" if target_member.bot else "No", inline=True)
        embed.add_field(name="Created At", value=created_at, inline=False)
        embed.add_field(name="Joined Server", value=joined_at, inline=False)
        embed.add_field(name="Roles", value=roles_str, inline=False)

        perms = [p[0].replace("_", " ").title() for p in target_member.guild_permissions if p[1]]
        top_perms = ", ".join(perms[:8]) + ("..." if len(perms) > 8 else "")
        embed.add_field(name="Key Permissions", value=top_perms or "*None*", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="View the avatar image of a member.")
    @app_commands.describe(member="The member whose avatar you want to view.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None) -> None:
        """Display target member's avatar."""
        target = member or interaction.user

        embed = info_embed(
            title=f"Avatar - {target}",
            description=f"[**Download Original**]({target.display_avatar.url})"
        )
        embed.set_image(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="botinfo", description="Display statistics and details about NoSpaceFGK.")
    async def botinfo(self, interaction: discord.Interaction) -> None:
        """Display current bot processes information."""
        uptime_str = "*Unknown*"
        bot_instance = self.bot

        if bot_instance.start_time:
            uptime_seconds = (datetime.datetime.now(datetime.timezone.utc) - bot_instance.start_time).total_seconds()
            uptime_str = format_duration(uptime_seconds)

        embed = info_embed(
            title="NoSpaceFGK Status Info",
            description="System metrics and runtime stats."
        )
        embed.add_field(name="Guilds Joined", value=f"`{len(bot_instance.guilds)}`", inline=True)
        embed.add_field(name="Total Users Count", value=f"`{len(bot_instance.users)}`", inline=True)
        embed.add_field(name="System Platform", value=f"`{platform.system()} ({platform.release()})`", inline=False)
        embed.add_field(name="Bot Uptime", value=uptime_str, inline=False)
        embed.add_field(name="Gateway Latency", value=f"`{bot_instance.latency * 1000:.2f}ms`", inline=True)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="uptime", description="Check how long the bot has been running.")
    async def uptime(self, interaction: discord.Interaction) -> None:
        """Display total bot uptime."""
        bot_instance = self.bot

        if not bot_instance.start_time:
            embed = error_embed("Uptime Info", "Start time was not correctly logged.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        uptime_seconds = (datetime.datetime.now(datetime.timezone.utc) - bot_instance.start_time).total_seconds()
        uptime_str = format_duration(uptime_seconds)

        embed = success_embed(
            title="Bot Uptime",
            description=f"NoSpaceFGK has been running for **{uptime_str}**."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    """Load the UtilityCog into the bot.

    Args:
        bot: The target Bot instance.
    """
    await bot.add_cog(UtilityCog(bot))
