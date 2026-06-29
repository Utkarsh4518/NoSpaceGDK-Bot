"""Domain models tracking AI token usage statistics and cost estimations."""

import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TokenUsage:
    """Detailed record of an API completion event's token counts and costs."""
    id: Optional[int]
    guild_id: Optional[int]
    user_id: int
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    used_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
