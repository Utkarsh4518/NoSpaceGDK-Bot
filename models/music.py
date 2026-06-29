"""Domain models and player state definitions for NoSpaceFGK Music Engine."""

import datetime
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class PlayerState(Enum):
    """Execution states of an active music player session."""
    IDLE = auto()
    CONNECTING = auto()
    BUFFERING = auto()
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()
    DISCONNECTED = auto()
    DESTROYED = auto()


class RepeatMode(Enum):
    """Queue replication repeat modes."""
    NONE = auto()
    ONE = auto()
    ALL = auto()


@dataclass
class Track:
    """Domain model representing a unique audio track definition."""
    uuid: str
    title: str
    artist: str
    duration: float  # Duration in seconds
    thumbnail: Optional[str]
    provider: str  # e.g., 'youtube', 'spotify', 'soundcloud'
    url: str
    requested_by: int  # Discord User Snowflake ID
    added_at: datetime.datetime
    isrc: Optional[str] = field(default=None)  # International Standard Recording Code placeholder
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Playlist:
    """Domain representation of a collection of tracks."""
    uuid: str
    name: str
    owner_id: int
    tracks: List[Track]
    updated_at: datetime.datetime


@dataclass
class QueueItem:
    """A track entry representation inside a queue."""
    uuid: str
    track: Track
    added_by: int
    added_at: datetime.datetime


@dataclass
class PlaybackOptions:
    """User-controlled player variables."""
    volume: float = 1.0  # Range: 0.0 - 2.0
    repeat_mode: RepeatMode = RepeatMode.NONE
    shuffle: bool = False
    crossfade: float = 0.0  # Duration in seconds
    eq_preset: Optional[str] = None


@dataclass
class VoiceSession:
    """State tracking of bot's active connection in guild voice channels."""
    guild_id: int
    channel_id: int
    session_id: Optional[str]
    latency: float = 0.0
    connected_at: Optional[datetime.datetime] = field(default=None)


@dataclass
class PlaybackHistory:
    """Record of a track playback session."""
    guild_id: int
    track_uuid: str
    played_by: int
    played_at: datetime.datetime
