"""Domain models representing conversation histories and messages."""

import datetime
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    """A single chat message within a conversation."""
    role: str  # 'system', 'user', or 'assistant'
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    created_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

    def to_dict(self) -> dict:
        """Convert message details to a API compatible format."""
        return {
            "role": self.role,
            "content": self.content
        }


@dataclass
class Conversation:
    """An active conversation session tracking message history."""
    id: str  # Format: '{target_type}:{target_id}'
    target_id: int  # Guild ID, Channel ID, or User ID
    target_type: str  # 'guild', 'channel', or 'user'
    active_model: str
    active_provider: str
    messages: List[Message] = field(default_factory=list)
    created_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
