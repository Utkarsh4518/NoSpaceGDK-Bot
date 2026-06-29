"""Warning domain model."""

import datetime
from dataclasses import dataclass

@dataclass
class WarningModel:
    """Domain representation of a user warning."""
    id: int | None
    guild_id: int
    user_id: int
    moderator_id: int
    reason: str | None
    points: int
    is_expired: bool
    expires_at: datetime.datetime | None
    created_at: datetime.datetime
