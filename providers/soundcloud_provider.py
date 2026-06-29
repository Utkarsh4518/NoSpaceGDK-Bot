"""SoundCloud search and streaming source provider placeholder."""

from typing import List, Optional
from models.music import Track, Playlist
from providers.base_provider import BaseMusicProvider


class SoundCloudProvider(BaseMusicProvider):
    """SoundCloud integration adapter placeholder raising NotImplementedError."""

    async def search(self, query: str, limit: int = 10) -> List[Track]:
        raise NotImplementedError("SoundCloudProvider search is not implemented yet.")

    async def get_track(self, url: str) -> Optional[Track]:
        raise NotImplementedError("SoundCloudProvider get_track is not implemented yet.")

    async def get_playlist(self, url: str) -> Optional[Playlist]:
        raise NotImplementedError("SoundCloudProvider get_playlist is not implemented yet.")

    async def get_stream(self, track: Track) -> str:
        raise NotImplementedError("SoundCloudProvider get_stream is not implemented yet.")

    def validate_url(self, url: str) -> bool:
        raise NotImplementedError("SoundCloudProvider validate_url is not implemented yet.")
