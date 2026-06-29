"""Custom command checks and predicates for NoSpaceFGK.

Contains logical evaluations for permissions, ownership, and subscriptions
called by slash command check frameworks.
"""

import discord
from utils.logger import logger


async def is_owner_predicate(interaction: discord.Interaction) -> bool:
    """Evaluate whether the interacting user is configured as a bot owner.

    Args:
        interaction: The invoking Interaction context.

    Returns:
        True if the user is an owner, False otherwise.
    """
    config = getattr(interaction.client, "config", None)
    if not config:
        logger.warning("Bot client does not have 'config' attribute initialized during check.")
        return False

    return interaction.user.id in config.owner_ids


async def is_premium_predicate(interaction: discord.Interaction) -> bool:
    """Placeholder predicate to evaluate premium subscription status.

    Currently defaults to True for all users.

    Args:
        interaction: The invoking Interaction context.

    Returns:
        True.
    """
    return True
