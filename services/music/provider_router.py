"""Provider router for automatic URL dispatch.

Determines which music provider should handle a given query or URL,
routing Spotify, YouTube, SoundCloud, and plain text searches to
the appropriate provider.
"""

import re
from enum import Enum, auto
from typing import Optional

from providers.youtube_provider import YouTubeProvider
from providers.spotify_provider import SpotifyProvider
from utils.logger import logger


class ProviderType(Enum):
    """Identifies which provider to route a request to."""
    YOUTUBE = auto()
    SPOTIFY = auto()
    SOUNDCLOUD = auto()
    SEARCH = auto()
    UNKNOWN = auto()


class ProviderRouter:
    """Routes user queries/URLs to the correct music provider.

    Detection order:
        1. YouTube URL patterns
        2. Spotify URL/URI patterns
        3. SoundCloud URL patterns (placeholder)
        4. Plain text -> default to YouTube search
    """

    SOUNDCLOUD_REGEX = re.compile(
        r'^(?:https?://)?(?:www\.)?soundcloud\.com/'
    )

    def __init__(
        self,
        youtube_provider: YouTubeProvider,
        spotify_provider: Optional[SpotifyProvider] = None
    ) -> None:
        """Initialize the provider router.

        Args:
            youtube_provider: YouTube provider instance.
            spotify_provider: Optional Spotify provider instance
                (None if credentials are not configured).
        """
        self._youtube = youtube_provider
        self._spotify = spotify_provider
        logger.info(
            f"Provider router: Initialized "
            f"(Spotify: {'enabled' if spotify_provider else 'disabled'})."
        )

    def detect(self, query: str) -> ProviderType:
        """Detect which provider should handle a query.

        Args:
            query: User-supplied URL or search query.

        Returns:
            ProviderType indicating the appropriate provider.
        """
        query = query.strip()

        # 1. YouTube URL check
        if self._youtube.validate_url(query):
            logger.debug(f"Provider router: Detected YouTube URL: '{query}'.")
            return ProviderType.YOUTUBE

        # 2. Spotify URL/URI check
        if self._spotify and self._spotify.validate_url(query):
            logger.debug(f"Provider router: Detected Spotify URL: '{query}'.")
            return ProviderType.SPOTIFY

        # 3. SoundCloud URL check (placeholder)
        if self.SOUNDCLOUD_REGEX.match(query):
            logger.debug(f"Provider router: Detected SoundCloud URL: '{query}'.")
            return ProviderType.SOUNDCLOUD

        # 4. Generic HTTP/HTTPS URL (unknown provider)
        if query.startswith(("http://", "https://")):
            logger.debug(f"Provider router: Unknown URL provider: '{query}'.")
            return ProviderType.UNKNOWN

        # 5. Plain text search query -> YouTube search
        logger.debug(f"Provider router: Plain text query, routing to YouTube search.")
        return ProviderType.SEARCH

    @property
    def spotify_enabled(self) -> bool:
        """Check if Spotify is available."""
        return self._spotify is not None

    @property
    def youtube_provider(self) -> YouTubeProvider:
        """Access the YouTube provider."""
        return self._youtube

    @property
    def spotify_provider(self) -> Optional[SpotifyProvider]:
        """Access the Spotify provider (may be None)."""
        return self._spotify
