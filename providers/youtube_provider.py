"""YouTube music search and playback stream provider placeholder."""

from typing import List, Optional
from models.music import Track, Playlist
from providers.base_provider import BaseMusicProvider


class YouTubeProvider(BaseMusicProvider):
    """YouTube integration adapter placeholder raising NotImplementedError."""

    async def search(self, query: str, limit: int = 10) -> List[Track]:
        raise NotImplementedError("YouTubeProvider search is not implemented yet.")

    async def get_track(self, url: str) -> Optional[Track]:
        raise NotImplementedError("YouTubeProvider get_track is not implemented yet.")

    async def get_playlist(self, url: str) -> Optional[Playlist]:
        raise NotImplementedError("YouTubeProvider get_playlist is not implemented yet.")

    async def get_stream(self, track: Track) -> str:
        raise NotImplementedError("YouTubeProvider get_stream is not implemented yet.")

    def validate_url(self, url: str) -> bool:
        raise NotImplementedError("YouTubeProvider validate_url is not implemented yet.")
