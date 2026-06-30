"""Ticket domain models."""

import datetime
from dataclasses import dataclass
from typing import Optional

@dataclass
class TicketModel:
    """Domain representation of a support ticket."""
    id: Optional[int]
    guild_id: int
    channel_id: int
    creator_id: int
    status: str  # 'open', 'closed'
    claimed_by: Optional[int] = None
    category_id: Optional[int] = None
    topic: Optional[str] = None
    created_at: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)
    closed_at: Optional[datetime.datetime] = None

@dataclass
class TicketMessageModel:
    """Domain representation of a message inside a ticket (for transcripts)."""
    id: Optional[int]
    ticket_id: int
    author_id: int
    author_name: str
    content: str
    created_at: datetime.datetime = datetime.datetime.now(datetime.timezone.utc)

@dataclass
class TicketParticipantModel:
    """Domain representation of a ticket participant."""
    ticket_id: int
    user_id: int
