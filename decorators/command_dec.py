"""Reusable decorators for slash commands in NoSpaceFGK.

Encapsulates checks, cooldowns, and permissions in clean, reusable decorators.
"""

from typing import Callable, TypeVar, Any
from discord import app_commands
from checks.custom_checks import is_owner_predicate, is_premium_predicate

T = TypeVar("T", bound=Callable[..., Any])


def is_owner() -> Callable[[T], T]:
    """Decorator to restrict command execution to configured bot owners.

    Returns:
        A discord.app_commands.check wrapper.
    """
    return app_commands.check(is_owner_predicate)


def is_premium() -> Callable[[T], T]:
    """Decorator to restrict command execution to premium subscribers (placeholder).

    Returns:
        A discord.app_commands.check wrapper.
    """
    return app_commands.check(is_premium_predicate)


def guild_only_command() -> Callable[[T], T]:
    """Decorator to restrict a command to server/guild channels only.

    Returns:
        The discord.app_commands.guild_only decorator.
    """
    return app_commands.guild_only()


def cooldown_command(rate: int, per: float) -> Callable[[T], T]:
    """Decorator to configure invocation cooldowns on a command.

    Args:
        rate: Number of allowed invocations before trigger.
        per: Duration of the cooldown period in seconds.

    Returns:
        A discord.app_commands.checks.cooldown decorator.
    """
    return app_commands.checks.cooldown(rate, per)


def permission_check(**perms: bool) -> Callable[[T], T]:
    """Decorator to require specific permissions from the invoking member.

    Args:
        perms: Keyword permissions (e.g. manage_messages=True).

    Returns:
        A discord.app_commands.checks.has_permissions decorator.
    """
    return app_commands.checks.has_permissions(**perms)
