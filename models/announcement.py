"""Announcement domain models."""

import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class AnnouncementModel:
    """Domain representation of an announcement."""
    id: Optional[int]
    guild_id: int
    channel_id: int
    message_text: Optional[str] = None
    embed_json: Optional[str] = None
    scheduled_at: Optional[datetime.datetime] = None
    sent_at: Optional[datetime.datetime] = None
    status: str = "pending"  # 'pending', 'sent', 'failed', 'cancelled'
