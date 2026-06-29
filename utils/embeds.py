"""Standardized embed templates for the NoSpaceFGK bot.

This module provides helper functions to generate consistent, modern discord.Embed
responses for success, error, warning, and info states.
"""

import datetime
import discord
from utils import constants


def _apply_theme(embed: discord.Embed) -> discord.Embed:
    """Helper to attach the unified bot footer and current timestamp.

    Args:
        embed: The target Embed instance.

    Returns:
        The styled Embed instance.
    """
    embed.set_footer(text=f"{constants.BOT_NAME} | v{constants.BOT_VERSION}")
    embed.timestamp = datetime.datetime.now(datetime.timezone.utc)
    return embed


def success_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized success embed.

    Args:
        title: The title of the embed.
        description: The description message.

    Returns:
        A discord.Embed configured with the success color.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=constants.COLOR_SUCCESS
    )
    return _apply_theme(embed)


def error_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized error embed.

    Args:
        title: The title of the embed.
        description: The description message.

    Returns:
        A discord.Embed configured with the error color.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=constants.COLOR_ERROR
    )
    return _apply_theme(embed)


def warning_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized warning embed.

    Args:
        title: The title of the embed.
        description: The description message.

    Returns:
        A discord.Embed configured with the warning color.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=constants.COLOR_WARNING
    )
    return _apply_theme(embed)


def info_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized informational embed.

    Args:
        title: The title of the embed.
        description: The description message.

    Returns:
        A discord.Embed configured with the info color.
    """
    embed = discord.Embed(
        title=title,
        description=description,
        color=constants.COLOR_INFO
    )
    return _apply_theme(embed)
