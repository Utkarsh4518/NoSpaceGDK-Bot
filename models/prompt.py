"""Domain models representing custom system prompts and configuration templates."""

import datetime
from dataclasses import dataclass, field


@dataclass
class Prompt:
    """Custom prompt configurations for guilds, channels, or users."""
    id: str  # Format: '{target_type}:{target_id}'
    target_id: int  # Guild, channel, or user ID
    target_type: str  # 'guild', 'channel', or 'user'
    prompt_text: str
    created_by: int  # Discord User Snowflake ID
    updated_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
