"""Domain models representing conversation histories and messages."""

import datetime
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Message:
    """A single chat message within a conversation."""
    role: str  # 'system', 'developer', 'user', 'assistant', or 'tool'
    content: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    created_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    latency: Optional[float] = None
    reasoning_metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert message details to an API compatible format."""
        d = {
            "role": self.role,
            "content": self.content
        }
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class Conversation:
    """An active conversation session tracking message history."""
    id: str  # Format: '{target_type}:{target_id}'
    target_id: int  # Guild ID, Channel ID, or User ID
    target_type: str  # 'guild', 'channel', or 'user'
    active_model: str
    active_provider: str
    messages: List[Message] = field(default_factory=list)
    state: Optional[dict] = None
    created_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at: datetime.datetime = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
