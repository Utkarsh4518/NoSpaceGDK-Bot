"""Base Music Provider interface definitions for NoSpaceFGK bot.

Specifies abstract contract APIs for searching, mapping URLs, and extracting
audio playback streams from third-party services.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from models.music import Track, Playlist


class BaseMusicProvider(ABC):
    """Abstract parent outlining standard provider operations."""

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Track]:
        """Perform search query on the service.

        Args:
            query: User text input.
            limit: Maximum result entries to return.

        Returns:
            List of parsed Track models.
        """
        pass

    @abstractmethod
    async def get_track(self, url: str) -> Optional[Track]:
        """Resolve a track resource by its original URL.

        Args:
            url: Song webpage URL.

        Returns:
            Resolved Track object, or None.
        """
        pass

    @abstractmethod
    async def get_playlist(self, url: str) -> Optional[Playlist]:
        """Resolve a playlist URL.

        Args:
            url: Playlist webpage link.

        Returns:
            Resolved Playlist object containing Track array, or None.
        """
        pass

    @abstractmethod
    async def get_stream(self, track: Track) -> str:
        """Retrieve stream audio source link.

        Args:
            track: Track configuration.

        Returns:
            Audio source path or URL.
        """
        pass

    @abstractmethod
    def validate_url(self, url: str) -> bool:
        """Verify URL string matches formatting rules for this provider.

        Args:
            url: Target web page link.

        Returns:
            True if URL matches provider domain rules, False otherwise.
        """
        pass
