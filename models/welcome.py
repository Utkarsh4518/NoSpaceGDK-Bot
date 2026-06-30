"""Welcome and Goodbye settings models."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class WelcomeSettingsModel:
    """Domain representation of guild welcome configuration."""
    guild_id: int
    channel_id: Optional[int] = None
    message_text: Optional[str] = None
    embed_json: Optional[str] = None
    dm_enabled: bool = False
    enabled: bool = False

@dataclass
class GoodbyeSettingsModel:
    """Domain representation of guild goodbye configuration."""
    guild_id: int
    channel_id: Optional[int] = None
    message_text: Optional[str] = None
    embed_json: Optional[str] = None
    enabled: bool = False

@dataclass
class AutoroleModel:
    """Domain representation of an autorole mapping."""
    guild_id: int
    role_id: int
