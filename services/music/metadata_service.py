"""Spotify metadata caching service.

Provides an in-memory TTL cache for Spotify metadata fetched via
the SpotifyProvider, preventing redundant API calls for recently
accessed tracks, albums, and artists.
"""

import datetime
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models.music import Track
from utils.logger import logger


@dataclass
class CacheEntry:
    """Single cache entry with TTL tracking."""
    data: Any
    expires_at: float


class MetadataService:
    """In-memory metadata cache with configurable TTL.

    Caches Spotify track lists, album metadata, and artist top tracks
    to reduce Spotify API call volume.
    """

    def __init__(self, ttl: int = 600) -> None:
        """Initialize the metadata cache.

        Args:
            ttl: Time-to-live for cache entries in seconds (default: 600s / 10 min).
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._ttl = ttl
        logger.info(f"Metadata service: Initialized with TTL={ttl}s.")

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a cached value if it exists and has not expired.

        Args:
            key: Cache key.

        Returns:
            Cached value, or None if expired or missing.
        """
        entry = self._cache.get(key)
        if entry is None:
            return None

        if time.monotonic() > entry.expires_at:
            del self._cache[key]
            logger.debug(f"Metadata service: Cache expired for key '{key}'.")
            return None

        logger.debug(f"Metadata service: Cache hit for key '{key}'.")
        return entry.data

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache with TTL.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        self._cache[key] = CacheEntry(
            data=value,
            expires_at=time.monotonic() + self._ttl
        )
        logger.debug(f"Metadata service: Cached key '{key}' (TTL: {self._ttl}s).")

    def get_spotify_tracks(self, spotify_id: str) -> Optional[List[Track]]:
        """Retrieve cached Spotify track list.

        Args:
            spotify_id: Spotify resource identifier.

        Returns:
            List of Track models, or None.
        """
        return self.get(f"spotify:tracks:{spotify_id}")

    def set_spotify_tracks(self, spotify_id: str, tracks: List[Track]) -> None:
        """Cache a list of Spotify tracks.

        Args:
            spotify_id: Spotify resource identifier.
            tracks: List of Track models.
        """
        self.set(f"spotify:tracks:{spotify_id}", tracks)

    def get_resolved_track(self, spotify_id: str) -> Optional[Track]:
        """Retrieve a cached YouTube-resolved track for a Spotify ID.

        Args:
            spotify_id: Spotify track ID.

        Returns:
            Resolved YouTube Track, or None.
        """
        return self.get(f"spotify:resolved:{spotify_id}")

    def set_resolved_track(self, spotify_id: str, track: Track) -> None:
        """Cache a YouTube-resolved track for a Spotify ID.

        Args:
            spotify_id: Spotify track ID.
            track: YouTube Track model.
        """
        self.set(f"spotify:resolved:{spotify_id}", track)

    def clear_expired(self) -> int:
        """Remove all expired entries from the cache.

        Returns:
            Number of entries removed.
        """
        now = time.monotonic()
        expired_keys = [k for k, v in self._cache.items() if now > v.expires_at]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Metadata service: Cleared {len(expired_keys)} expired entries.")
        return len(expired_keys)

    @property
    def size(self) -> int:
        """Current number of entries in the cache."""
        return len(self._cache)
