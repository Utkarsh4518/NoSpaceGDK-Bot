"""Spotify metadata and query details provider placeholder."""

from typing import List, Optional
from models.music import Track, Playlist
from providers.base_provider import BaseMusicProvider


class SpotifyProvider(BaseMusicProvider):
    """Spotify integration adapter placeholder raising NotImplementedError."""

    async def search(self, query: str, limit: int = 10) -> List[Track]:
        raise NotImplementedError("SpotifyProvider search is not implemented yet.")

    async def get_track(self, url: str) -> Optional[Track]:
        raise NotImplementedError("SpotifyProvider get_track is not implemented yet.")

    async def get_playlist(self, url: str) -> Optional[Playlist]:
        raise NotImplementedError("SpotifyProvider get_playlist is not implemented yet.")

    async def get_stream(self, track: Track) -> str:
        raise NotImplementedError("SpotifyProvider get_stream is not implemented yet.")

    def validate_url(self, url: str) -> bool:
        raise NotImplementedError("SpotifyProvider validate_url is not implemented yet.")
