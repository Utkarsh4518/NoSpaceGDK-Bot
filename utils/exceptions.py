"""Custom exceptions for the NoSpaceFGK Discord Bot.

This module defines the exception hierarchy used throughout the bot,
allowing for structured error handling and precise exception logging.
"""

class NoSpaceFGKError(Exception):
    """Base exception class for all errors related to NoSpaceFGK."""

    def __init__(self, message: str) -> None:
        """Initialize the base exception.

        Args:
            message: A detailed error message describing the failure.
        """
        super().__init__(message)
        self.message = message


class ConfigurationError(NoSpaceFGKError):
    """Raised when configuration validation fails or is missing required values."""


class BotStartupError(NoSpaceFGKError):
    """Raised when the bot fails to initialize or start up properly."""


class CogLoadError(NoSpaceFGKError):
    """Raised when loading or unloading a Discord Cog fails."""


class ExtensionError(NoSpaceFGKError):
    """Raised when loading, unloading, or reloading a bot extension fails."""
