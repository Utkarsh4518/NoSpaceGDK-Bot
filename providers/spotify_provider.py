"""Spotify metadata provider for NoSpaceFGK bot.

Fetches track, album, playlist, and artist metadata from the Spotify Web API
using spotipy. This provider NEVER returns playable audio streams. All audio
must be routed through YouTube after matching.
"""

import asyncio
import datetime
import re
import uuid
from typing import Any, Dict, List, Optional

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from models.music import Track, Playlist
from providers.base_provider import BaseMusicProvider
from utils.logger import logger


class SpotifyProvider(BaseMusicProvider):
    """Spotify Web API metadata scraper.

    Extracts structured track, album, playlist, and artist metadata
    using client-credentials authentication. Audio playback is NOT
    handled by this provider — all tracks must be resolved to YouTube.
    """

    SPOTIFY_URL_REGEX = re.compile(
        r'^(?:https?://)?(?:open\.)?spotify\.com/'
        r'(?:intl-[a-z]{2}/)?' 
        r'(track|album|playlist|artist)/([a-zA-Z0-9]+)'
    )
    SPOTIFY_URI_REGEX = re.compile(
        r'^spotify:(track|album|playlist|artist):([a-zA-Z0-9]+)$'
    )

    def __init__(self, client_id: str, client_secret: str) -> None:
        """Initialize the Spotify provider with API credentials.

        Args:
            client_id: Spotify application Client ID.
            client_secret: Spotify application Client Secret.
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._sp: Optional[spotipy.Spotify] = None
        logger.info("Spotify provider: Initialized.")

    async def _ensure_client(self) -> spotipy.Spotify:
        """Lazily initialize the authenticated spotipy client.

        Returns:
            An authenticated spotipy.Spotify instance.
        """
        if self._sp is None:
            auth_manager = SpotifyClientCredentials(
                client_id=self._client_id,
                client_secret=self._client_secret
            )
            self._sp = spotipy.Spotify(auth_manager=auth_manager)
            logger.info("Spotify provider: Authenticated with Spotify Web API.")
        return self._sp

    def validate_url(self, url: str) -> bool:
        """Verify URL matches Spotify domain patterns or URI format.

        Args:
            url: URL or URI string.

        Returns:
            True if a valid Spotify identifier.
        """
        return bool(self.SPOTIFY_URL_REGEX.match(url) or self.SPOTIFY_URI_REGEX.match(url))

    def parse_spotify_identifier(self, url: str) -> Optional[Dict[str, str]]:
        """Parse a Spotify URL or URI into its type and ID.

        Args:
            url: Spotify URL or URI string.

        Returns:
            Dict with 'type' and 'id' keys, or None.
        """
        match = self.SPOTIFY_URL_REGEX.match(url)
        if match:
            return {"type": match.group(1), "id": match.group(2)}

        match = self.SPOTIFY_URI_REGEX.match(url)
        if match:
            return {"type": match.group(1), "id": match.group(2)}

        return None

    async def search(self, query: str, limit: int = 10) -> List[Track]:
        """Search Spotify for tracks matching a query.

        Args:
            query: Search keywords.
            limit: Maximum results.

        Returns:
            List of Track metadata models (no stream URLs).
        """
        sp = await self._ensure_client()
        logger.info(f"Spotify provider: Searching for '{query}' (limit: {limit}).")

        try:
            results = await asyncio.to_thread(sp.search, q=query, limit=limit, type="track")
            tracks: List[Track] = []

            if results and "tracks" in results and results["tracks"]["items"]:
                for item in results["tracks"]["items"]:
                    tracks.append(self._parse_track_item(item))

            logger.info(f"Spotify provider: Search returned {len(tracks)} results.")
            return tracks
        except Exception as e:
            logger.error(f"Spotify provider: Search error for '{query}': {e}", exc_info=True)
            return []

    async def get_track(self, url: str) -> Optional[Track]:
        """Fetch metadata for a single Spotify track.

        Args:
            url: Spotify track URL or URI.

        Returns:
            Track metadata model, or None.
        """
        parsed = self.parse_spotify_identifier(url)
        if not parsed or parsed["type"] != "track":
            logger.warning(f"Spotify provider: Not a valid track URL: '{url}'.")
            return None

        sp = await self._ensure_client()
        logger.info(f"Spotify provider: Resolving track ID '{parsed['id']}'.")

        try:
            item = await asyncio.to_thread(sp.track, parsed["id"])
            if not item:
                return None
            return self._parse_track_item(item)
        except Exception as e:
            logger.error(f"Spotify provider: Failed to resolve track '{parsed['id']}': {e}")
            return None

    async def get_album(self, url: str) -> Optional[List[Track]]:
        """Fetch all tracks from a Spotify album.

        Args:
            url: Spotify album URL or URI.

        Returns:
            List of Track metadata models maintaining album order, or None.
        """
        parsed = self.parse_spotify_identifier(url)
        if not parsed or parsed["type"] != "album":
            logger.warning(f"Spotify provider: Not a valid album URL: '{url}'.")
            return None

        sp = await self._ensure_client()
        logger.info(f"Spotify provider: Resolving album ID '{parsed['id']}'.")

        try:
            album_data = await asyncio.to_thread(sp.album, parsed["id"])
            if not album_data:
                return None

            album_name = album_data.get("name", "Unknown Album")
            album_art = self._get_best_image(album_data.get("images", []))
            album_artists = self._format_artists(album_data.get("artists", []))

            tracks: List[Track] = []
            items = album_data.get("tracks", {}).get("items", [])

            # Handle pagination for albums with >50 tracks
            while True:
                for item in items:
                    tracks.append(self._parse_album_track_item(
                        item, album_name, album_art, album_artists
                    ))

                next_page = album_data.get("tracks", {}).get("next")
                if not next_page:
                    break

                album_data["tracks"] = await asyncio.to_thread(sp.next, album_data["tracks"])
                items = album_data["tracks"].get("items", [])

            logger.info(f"Spotify provider: Album '{album_name}' resolved with {len(tracks)} tracks.")
            return tracks
        except Exception as e:
            logger.error(f"Spotify provider: Failed to resolve album '{parsed['id']}': {e}", exc_info=True)
            return None

    async def get_playlist(self, url: str) -> Optional[Playlist]:
        """Fetch all tracks from a Spotify playlist.

        Args:
            url: Spotify playlist URL or URI.

        Returns:
            Playlist model containing Track metadata models, or None.
        """
        parsed = self.parse_spotify_identifier(url)
        if not parsed or parsed["type"] != "playlist":
            logger.warning(f"Spotify provider: Not a valid playlist URL: '{url}'.")
            return None

        sp = await self._ensure_client()
        logger.info(f"Spotify provider: Resolving playlist ID '{parsed['id']}'.")

        try:
            playlist_data = await asyncio.to_thread(sp.playlist, parsed["id"])
            if not playlist_data:
                return None

            playlist_name = playlist_data.get("name", "Spotify Playlist")

            tracks: List[Track] = []
            results = playlist_data.get("tracks", {})
            items = results.get("items", [])

            while True:
                for item in items:
                    track_data = item.get("track")
                    if not track_data or track_data.get("type") != "track":
                        continue  # Skip podcast episodes or None entries
                    tracks.append(self._parse_track_item(track_data))

                if not results.get("next"):
                    break

                results = await asyncio.to_thread(sp.next, results)
                items = results.get("items", [])

            logger.info(f"Spotify provider: Playlist '{playlist_name}' resolved with {len(tracks)} tracks.")

            return Playlist(
                uuid=parsed["id"],
                name=playlist_name,
                owner_id=0,
                tracks=tracks,
                updated_at=datetime.datetime.now(datetime.timezone.utc)
            )
        except Exception as e:
            logger.error(f"Spotify provider: Failed to resolve playlist '{parsed['id']}': {e}", exc_info=True)
            return None

    async def get_artist_top_tracks(self, url: str, limit: int = 20) -> Optional[List[Track]]:
        """Fetch an artist's top tracks from Spotify.

        Args:
            url: Spotify artist URL or URI.
            limit: Maximum tracks to return (capped at 20).

        Returns:
            List of Track metadata models, or None.
        """
        parsed = self.parse_spotify_identifier(url)
        if not parsed or parsed["type"] != "artist":
            logger.warning(f"Spotify provider: Not a valid artist URL: '{url}'.")
            return None

        sp = await self._ensure_client()
        logger.info(f"Spotify provider: Resolving top tracks for artist ID '{parsed['id']}'.")

        try:
            results = await asyncio.to_thread(sp.artist_top_tracks, parsed["id"])
            if not results or "tracks" not in results:
                return None

            tracks: List[Track] = []
            for item in results["tracks"][:min(limit, 20)]:
                tracks.append(self._parse_track_item(item))

            # Fetch artist name for logging
            artist_data = await asyncio.to_thread(sp.artist, parsed["id"])
            artist_name = artist_data.get("name", "Unknown Artist") if artist_data else "Unknown Artist"

            logger.info(f"Spotify provider: Artist '{artist_name}' top tracks resolved with {len(tracks)} tracks.")
            return tracks
        except Exception as e:
            logger.error(f"Spotify provider: Failed to resolve artist '{parsed['id']}': {e}", exc_info=True)
            return None

    async def get_stream(self, track: Track) -> str:
        """Spotify does NOT provide direct audio streams.

        Raises:
            NotImplementedError: Always. Spotify tracks must be
                resolved through YouTube matching.
        """
        raise NotImplementedError(
            "Spotify provider does not support direct audio streaming. "
            "Resolve tracks through the YouTube matching service."
        )

    def _parse_track_item(self, item: Dict[str, Any]) -> Track:
        """Parse a Spotify API track object into a Track model.

        Args:
            item: Raw Spotify track data dict.

        Returns:
            Track domain model.
        """
        artists = self._format_artists(item.get("artists", []))
        album_data = item.get("album", {})
        thumbnail = self._get_best_image(album_data.get("images", []))
        duration_ms = item.get("duration_ms", 0)

        return Track(
            uuid=str(uuid.uuid4()),
            title=item.get("name", "Unknown Track"),
            artist=artists,
            duration=duration_ms / 1000.0,
            thumbnail=thumbnail,
            provider="spotify",
            url=item.get("external_urls", {}).get("spotify", ""),
            requested_by=0,
            added_at=datetime.datetime.now(datetime.timezone.utc),
            isrc=item.get("external_ids", {}).get("isrc"),
            metadata={
                "spotify_id": item.get("id"),
                "album_name": album_data.get("name"),
                "album_type": album_data.get("album_type"),
                "release_date": album_data.get("release_date"),
                "popularity": item.get("popularity"),
                "explicit": item.get("explicit", False),
                "track_number": item.get("track_number"),
                "disc_number": item.get("disc_number"),
            }
        )

    def _parse_album_track_item(
        self,
        item: Dict[str, Any],
        album_name: str,
        album_art: Optional[str],
        album_artists: str
    ) -> Track:
        """Parse a Spotify album track item (which lacks full album metadata).

        Args:
            item: Raw Spotify simplified track data dict.
            album_name: Parent album name.
            album_art: Parent album artwork URL.
            album_artists: Formatted album artist string.

        Returns:
            Track domain model.
        """
        artists = self._format_artists(item.get("artists", []))
        duration_ms = item.get("duration_ms", 0)

        return Track(
            uuid=str(uuid.uuid4()),
            title=item.get("name", "Unknown Track"),
            artist=artists or album_artists,
            duration=duration_ms / 1000.0,
            thumbnail=album_art,
            provider="spotify",
            url=item.get("external_urls", {}).get("spotify", ""),
            requested_by=0,
            added_at=datetime.datetime.now(datetime.timezone.utc),
            isrc=item.get("external_ids", {}).get("isrc"),
            metadata={
                "spotify_id": item.get("id"),
                "album_name": album_name,
                "track_number": item.get("track_number"),
                "disc_number": item.get("disc_number"),
            }
        )

    @staticmethod
    def _format_artists(artists: List[Dict[str, Any]]) -> str:
        """Join multiple artist names into a comma-separated string.

        Args:
            artists: List of Spotify artist objects.

        Returns:
            Formatted artist string.
        """
        if not artists:
            return "Unknown Artist"
        return ", ".join(a.get("name", "Unknown") for a in artists)

    @staticmethod
    def _get_best_image(images: List[Dict[str, Any]]) -> Optional[str]:
        """Select the highest resolution image URL.

        Args:
            images: List of Spotify image objects.

        Returns:
            URL string of the best image, or None.
        """
        if not images:
            return None
        # Spotify returns images sorted largest first
        return images[0].get("url")
