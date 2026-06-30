"""Verification domain models."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class VerificationSettingsModel:
    """Domain representation of verification settings."""
    guild_id: int
    role_id: Optional[int] = None
    channel_id: Optional[int] = None
    enabled: bool = False
    type: str = "button"  # 'button' (basic math captcha)
