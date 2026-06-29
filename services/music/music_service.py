"""High-level Music Service coordinator for NoSpaceFGK bot.

Registered in the DI container. Provides cogs with simple unified access APIs.
"""

from typing import List, Optional
from models.music import Track, Playlist, QueueItem, PlaybackHistory
from repositories.playlist_repository import PlaylistRepository
from repositories.history_repository import HistoryRepository
from services.music.player_manager import PlayerManager
from services.music.provider_manager import ProviderManager
from services.music.track_manager import TrackManager
from services.music.base_player import BaseMusicPlayer
from services.base_service import BaseService
from utils.logger import logger


class MusicService(BaseService):
    """Facade service orchestrating all internal music systems operations."""

    def __init__(
        self,
        player_manager: PlayerManager,
        provider_manager: ProviderManager,
        track_manager: TrackManager,
        playlist_repo: PlaylistRepository,
        history_repo: HistoryRepository
    ) -> None:
        """Initialize the music service.

        Args:
            player_manager: Guild player session allocator.
            provider_manager: External providers registry.
            track_manager: Caching and metadata loader.
            playlist_repo: Custom user playlists repository.
            history_repo: Playback history repository.
        """
        self.players: PlayerManager = player_manager
        self.providers: ProviderManager = provider_manager
        self.tracks: TrackManager = track_manager
        self.playlists: PlaylistRepository = playlist_repo
        self.history: HistoryRepository = history_repo

    async def get_player(self, guild_id: int) -> BaseMusicPlayer:
        """Get or create the player session for a guild.

        Args:
            guild_id: Guild snowflake ID.

        Returns:
            The guild's active player.
        """
        return await self.players.get_player(guild_id)

    async def search(self, query: str, provider_name: str = "youtube", limit: int = 10) -> List[Track]:
        """Query tracks using a registered provider (checking cache first).

        Args:
            query: The search term or URL.
            provider_name: The name of the registered provider (default: 'youtube').
            limit: Maximum result entries count.

        Returns:
            List of matching Track models.

        Raises:
            ValueError: If the provider is not registered.
        """
        cached = await self.tracks.get_cached_search_results(query)
        if cached:
            return cached

        provider = None
        if "http://" in query or "https://" in query:
            provider = self.providers.resolve_provider_by_url(query)

        if not provider:
            provider = self.providers.get_provider(provider_name)

        if not provider:
            raise ValueError(f"Music provider '{provider_name}' is not registered.")

        logger.info(f"Music service: Invoking provider search for query '{query}' via provider '{provider.__class__.__name__}'.")
        results = await provider.search(query, limit)

        for track in results:
            await self.tracks.save_track(track)

        await self.tracks.cache_search_results(query, results)
        return results

    async def log_playback(self, guild_id: int, track: Track, user_id: int) -> PlaybackHistory:
        """Log a played track in the database history.

        Args:
            guild_id: Guild snowflake ID.
            track: The Track model played.
            user_id: User who requested the song.

        Returns:
            The recorded PlaybackHistory model.
        """
        await self.tracks.save_track(track)
        return await self.history.add_to_history(guild_id, track.uuid, user_id)
