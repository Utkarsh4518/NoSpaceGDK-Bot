"""YouTube search and metadata extractor using yt-dlp."""

import asyncio
import datetime
import re
import uuid
from typing import Any, Dict, List, Optional
import yt_dlp
from models.music import Track, Playlist
from providers.base_provider import BaseMusicProvider
from utils.logger import logger


class YouTubeProvider(BaseMusicProvider):
    """Integrates yt-dlp to query YouTube, parse playlists, and extract streams."""

    YOUTUBE_URL_REGEX = re.compile(
        r'^(?:https?://)?(?:www\.|music\.)?'
        r'(?:youtube\.com/(?:watch\?v=|v/|embed/|shorts/|playlist\?list=)|youtu\.be/)'
        r'([a-zA-Z0-9_-]{11}|[a-zA-Z0-9_-]{12,})'
    )

    def __init__(self) -> None:
        """Initialize the YouTube provider."""
        self.ytdl_opts: Dict[str, Any] = {
            "format": "bestaudio/best",
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "source_address": "0.0.0.0",
            "socket_timeout": 10,
            "retries": 5,
            "cookiefile": None,
            "extract_flat": False,
        }

    def _get_ytdl(self, custom_opts: Optional[Dict[str, Any]] = None) -> yt_dlp.YoutubeDL:
        """Get a YoutubeDL instance with given options.

        Args:
            custom_opts: Optional override configurations.

        Returns:
            YoutubeDL instance.
        """
        opts = self.ytdl_opts.copy()
        if custom_opts:
            opts.update(custom_opts)
        return yt_dlp.YoutubeDL(opts)

    async def search(self, query: str, limit: int = 10) -> List[Track]:
        """Search YouTube for a query.

        Args:
            query: The search keywords.
            limit: Maximum results to fetch.

        Returns:
            List of Track models.
        """
        logger.info(f"YouTube provider: Searching for '{query}' (limit: {limit}).")

        if self.validate_url(query):
            track = await self.get_track(query)
            return [track] if track else []

        opts = {"extract_flat": False, "noplaylist": True}
        ytdl = self._get_ytdl(opts)
        search_query = f"ytsearch{limit}:{query}"

        try:
            data = await asyncio.to_thread(ytdl.extract_info, search_query, download=False)
            tracks: List[Track] = []
            if "entries" in data:
                for entry in data["entries"]:
                    if not entry:
                        continue
                    tracks.append(self._parse_entry(entry))
            return tracks
        except Exception as e:
            logger.error(f"YouTube provider: Search error for '{query}': {e}", exc_info=True)
            return []

    async def get_track(self, url: str) -> Optional[Track]:
        """Extract a single YouTube video details by URL.

        Args:
            url: Video link.

        Returns:
            The Track model, or None.
        """
        logger.info(f"YouTube provider: Resolving track URL '{url}'.")
        ytdl = self._get_ytdl({"noplaylist": True})
        try:
            data = await asyncio.to_thread(ytdl.extract_info, url, download=False)
            if not data:
                return None
            return self._parse_entry(data)
        except Exception as e:
            logger.error(f"YouTube provider: Failed to resolve track URL '{url}': {e}")
            return None

    async def get_playlist(self, url: str) -> Optional[Playlist]:
        """Extract all tracks from a YouTube Playlist.

        Args:
            url: Playlist link.

        Returns:
            Playlist model containing tracks array, or None.
        """
        logger.info(f"YouTube provider: Resolving playlist URL '{url}'.")
        ytdl = self._get_ytdl({"extract_flat": True, "noplaylist": False})
        try:
            data = await asyncio.to_thread(ytdl.extract_info, url, download=False)
            if not data or "entries" not in data:
                return None

            playlist_tracks: List[Track] = []
            entries = data["entries"]

            for entry in entries:
                if not entry:
                    continue

                track_id = entry.get("id")
                track_url = entry.get("url") or f"https://www.youtube.com/watch?v={track_id}"

                playlist_tracks.append(
                    Track(
                        uuid=str(uuid.uuid4()),
                        title=entry.get("title") or "Unknown Track",
                        artist=entry.get("uploader") or "Unknown Artist",
                        duration=float(entry.get("duration") or 0.0),
                        thumbnail=entry.get("thumbnail"),
                        provider="youtube",
                        url=track_url,
                        requested_by=0,
                        added_at=datetime.datetime.now(datetime.timezone.utc),
                        isrc=None,
                        metadata={"youtube_id": track_id}
                    )
                )

            return Playlist(
                uuid=data.get("id") or str(uuid.uuid4()),
                name=data.get("title") or "YouTube Playlist",
                owner_id=0,
                tracks=playlist_tracks,
                updated_at=datetime.datetime.now(datetime.timezone.utc)
            )
        except Exception as e:
            logger.error(f"YouTube provider: Failed to resolve playlist URL '{url}': {e}", exc_info=True)
            return None

    async def get_stream(self, track: Track) -> str:
        """Extract direct audio stream URL.

        Args:
            track: Track configuration.

        Returns:
            The direct stream path/URL.
        """
        logger.info(f"YouTube provider: Extracting streaming URL for Track (UUID: {track.uuid}).")
        ytdl = self._get_ytdl({"noplaylist": True, "extract_flat": False})
        try:
            data = await asyncio.to_thread(ytdl.extract_info, track.url, download=False)
            if not data:
                raise ValueError("Could not extract stream metadata.")

            stream_url = data.get("url")
            if not stream_url:
                raise ValueError("No streaming stream URL found.")
            return stream_url
        except Exception as e:
            logger.error(f"YouTube provider: Stream extraction failed for '{track.url}': {e}")
            raise

    def validate_url(self, url: str) -> bool:
        """Verify URL string matches YouTube pattern.

        Args:
            url: Target web page link.

        Returns:
            True if URL matches, False otherwise.
        """
        return bool(self.YOUTUBE_URL_REGEX.match(url))

    def _parse_entry(self, entry: Dict[str, Any]) -> Track:
        """Parse raw yt-dlp entry into a Track domain model.

        Args:
            entry: Dictionary containing raw track details.

        Returns:
            The Track domain model.
        """
        duration = entry.get("duration")
        if duration is None:
            duration = 0.0

        return Track(
            uuid=str(uuid.uuid4()),
            title=entry.get("title") or "Unknown Track",
            artist=entry.get("uploader") or entry.get("artist") or "Unknown Artist",
            duration=float(duration),
            thumbnail=entry.get("thumbnail") or (entry.get("thumbnails")[0]["url"] if entry.get("thumbnails") else None),
            provider="youtube",
            url=entry.get("webpage_url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
            requested_by=0,
            added_at=datetime.datetime.now(datetime.timezone.utc),
            isrc=None,
            metadata={
                "youtube_id": entry.get("id"),
                "view_count": entry.get("view_count"),
                "like_count": entry.get("like_count"),
                "description": entry.get("description")
            }
        )
