"""Track details validation, database serialization, and caching coordinator for NoSpaceFGK."""

from typing import List, Optional
from models.music import Track
from repositories.music_repository import MusicRepository
from services.cache_service import CacheService
from services.base_service import BaseService
from utils.logger import logger


class TrackManager(BaseService):
    """Coordinates persistent database storage and temporary cache caching for tracks."""

    def __init__(self, music_repo: MusicRepository, cache_service: CacheService) -> None:
        """Initialize the track manager.

        Args:
            music_repo: Persistent MusicRepository.
            cache_service: Fast CacheService instance.
        """
        self._repo: MusicRepository = music_repo
        self._cache: CacheService = cache_service

    async def get_track(self, uuid_str: str) -> Optional[Track]:
        """Fetch track data (check cache first, fallback to DB).

        Args:
            uuid_str: Song unique ID.

        Returns:
            The Track domain model or None.
        """
        cache_key = f"track:{uuid_str}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        track = await self._repo.get_by_uuid(uuid_str)
        if track:
            self._cache.set(cache_key, track)
        return track

    async def save_track(self, track: Track) -> Track:
        """Persist track data in repository and update cache.

        Args:
            track: Track configuration.

        Returns:
            The saved Track model.
        """
        saved = await self._repo.create_or_update(track)
        cache_key = f"track:{track.uuid}"
        self._cache.set(cache_key, saved)
        return saved

    async def cache_search_results(self, query: str, tracks: List[Track], ttl: Optional[float] = None) -> None:
        """Cache list of tracks for a search query.

        Args:
            query: The search term.
            tracks: List of matching Track models.
            ttl: Custom expiration limit.
        """
        cache_key = f"search:{query.lower()}"
        self._cache.set(cache_key, tracks, ttl=ttl)
        logger.info(f"Track manager: Cached {len(tracks)} search results for query '{query}'.")

    async def get_cached_search_results(self, query: str) -> Optional[List[Track]]:
        """Fetch cached search query results.

        Args:
            query: The search term.

        Returns:
            List of Track models, or None.
        """
        cache_key = f"search:{query.lower()}"
        cached = self._cache.get(cache_key)
        return cached  # type: ignore
