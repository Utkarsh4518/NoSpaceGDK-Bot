"""Standardized response service to construct and format user feedback."""

import discord
from services.base_service import BaseService
from utils import embeds


class ResponseService(BaseService):
    """Provides formatted embed instances utilizing the bot's design system colors."""

    def success_embed(self, title: str, description: str) -> discord.Embed:
        """Get success embed.

        Args:
            title: Title text.
            description: Description body.

        Returns:
            Formatted discord.Embed.
        """
        return embeds.success_embed(title, description)

    def error_embed(self, title: str, description: str) -> discord.Embed:
        """Get error embed.

        Args:
            title: Title text.
            description: Description body.

        Returns:
            Formatted discord.Embed.
        """
        return embeds.error_embed(title, description)

    def warning_embed(self, title: str, description: str) -> discord.Embed:
        """Get warning embed.

        Args:
            title: Title text.
            description: Description body.

        Returns:
            Formatted discord.Embed.
        """
        return embeds.warning_embed(title, description)

    def info_embed(self, title: str, description: str) -> discord.Embed:
        """Get info embed.

        Args:
            title: Title text.
            description: Description body.

        Returns:
            Formatted discord.Embed.
        """
        return embeds.info_embed(title, description)
