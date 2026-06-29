"""Moderation Case domain model."""

import datetime
from dataclasses import dataclass

@dataclass
class CaseModel:
    """Domain representation of a moderation action case."""
    id: int | None
    guild_id: int
    case_type: str  # 'warn', 'kick', 'ban', 'unban', 'timeout', 'untimeout', 'mute', 'unmute', 'lock', 'unlock'
    user_id: int
    moderator_id: int
    reason: str | None
    duration_seconds: int | None
    status: str  # 'active', 'expired', 'revoked'
    channel_id: int | None
    created_at: datetime.datetime
