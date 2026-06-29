"""Moderation settings and statistics domain models."""

from dataclasses import dataclass
from typing import List

@dataclass
class GuildSettingsModel:
    """Domain representation of per-guild moderation configuration."""
    guild_id: int
    default_timeout_seconds: int
    default_warning_limit: int
    audit_channel_id: int | None
    moderator_roles: List[int]
    protected_roles: List[int]
    ignored_channels: List[int]
    ignored_roles: List[int]

@dataclass
class ModerationStatisticsModel:
    """Domain representation of a guild's moderation volume statistics."""
    guild_id: int
    total_warns: int
    total_kicks: int
    total_bans: int
    total_timeouts: int
    total_automod_triggers: int
