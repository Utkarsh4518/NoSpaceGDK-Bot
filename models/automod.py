"""Automod rule domain model."""

import datetime
from dataclasses import dataclass

@dataclass
class AutomodRuleModel:
    """Domain representation of an automod rule."""
    id: int | None
    guild_id: int
    rule_type: str  # 'spam', 'duplicate', 'mentions', 'links_invite', 'links_external', 'bad_words', 'caps', 'emojis', 'joins', 'reactions', 'files'
    config: str  # JSON serialized configuration
    is_enabled: bool
    created_at: datetime.datetime
