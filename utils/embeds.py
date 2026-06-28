"""Standardized embed templates for the NoSpaceFGK bot.

This module provides helper functions to generate consistent, modern discord.Embed
responses for success, error, warning, and info states.
"""

import discord
from utils import constants

def success_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized success embed.

    Args:
        title: The title of the embed.
        description: The description message.

    Returns:
        A discord.Embed configured with the success color.
    """
    return discord.Embed(
        title=title,
        description=description,
        color=constants.COLOR_SUCCESS
    )


def error_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized error embed.

    Args:
        title: The title of the embed.
        description: The description message.

    Returns:
        A discord.Embed configured with the error color.
    """
    return discord.Embed(
        title=title,
        description=description,
        color=constants.COLOR_ERROR
    )


def warning_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized warning embed.

    Args:
        title: The title of the embed.
        description: The description message.

    Returns:
        A discord.Embed configured with the warning color.
    """
    return discord.Embed(
        title=title,
        description=description,
        color=constants.COLOR_WARNING
    )


def info_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized informational embed.

    Args:
        title: The title of the embed.
        description: The description message.

    Returns:
        A discord.Embed configured with the info color.
    """
    return discord.Embed(
        title=title,
        description=description,
        color=constants.COLOR_INFO
    )
