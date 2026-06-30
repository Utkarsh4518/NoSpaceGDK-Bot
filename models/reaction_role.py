"""Reaction Role domain models."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ReactionRoleModel:
    """Domain representation of a single emoji/button-to-role map."""
    id: Optional[int]
    guild_id: int
    message_id: int
    emoji: str
    role_id: int
    group_name: str

@dataclass
class ReactionRoleMessageModel:
    """Domain representation of a reaction role setup message."""
    message_id: int
    guild_id: int
    channel_id: int
    title: Optional[str]
    description: Optional[str]
    group_name: str
    type: str  # 'reaction', 'button', 'select'
