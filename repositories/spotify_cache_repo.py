"""Repository for caching Spotify-to-YouTube resolved track matches."""

import datetime
from typing import Optional
from dataclasses import dataclass
from repositories.base_repository import BaseRepository
from utils.logger import logger


@dataclass
class SpotifyMatchRecord:
    """A cached Spotify-to-YouTube resolution entry."""
    spotify_id: str
    youtube_url: str
    track_title: str
    artist: str
    confidence: float
    resolved_at: datetime.datetime


class SpotifyCacheRepository(BaseRepository):
    """Manages persistent cache of resolved Spotify track IDs to YouTube URLs."""

    async def get_match(self, spotify_id: str) -> Optional[SpotifyMatchRecord]:
        """Retrieve a cached YouTube match for a Spotify track ID.

        Args:
            spotify_id: Spotify track ID.

        Returns:
            SpotifyMatchRecord or None.
        """
        query = """
            SELECT spotify_id, youtube_url, track_title, artist, confidence, resolved_at
            FROM spotify_match_cache WHERE spotify_id = ?;
        """
        async with self.db.connection.execute(query, (spotify_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            resolved_at = row[5]
            if isinstance(resolved_at, str):
                try:
                    resolved_at = datetime.datetime.fromisoformat(resolved_at.replace(" ", "T"))
                except ValueError:
                    resolved_at = datetime.datetime.now(datetime.timezone.utc)

            return SpotifyMatchRecord(
                spotify_id=row[0],
                youtube_url=row[1],
                track_title=row[2],
                artist=row[3],
                confidence=row[4],
                resolved_at=resolved_at
            )

    async def save_match(
        self,
        spotify_id: str,
        youtube_url: str,
        track_title: str,
        artist: str,
        confidence: float
    ) -> None:
        """Save a resolved Spotify-to-YouTube match.

        Args:
            spotify_id: Spotify track ID.
            youtube_url: Matched YouTube URL.
            track_title: Track title.
            artist: Artist name.
            confidence: Match confidence score (0.0 - 1.0).
        """
        query = """
            INSERT INTO spotify_match_cache (spotify_id, youtube_url, track_title, artist, confidence)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(spotify_id) DO UPDATE SET
                youtube_url = excluded.youtube_url,
                track_title = excluded.track_title,
                artist = excluded.artist,
                confidence = excluded.confidence,
                resolved_at = CURRENT_TIMESTAMP;
        """
        await self.db.execute(query, (spotify_id, youtube_url, track_title, artist, confidence))
        await self.db.commit()
        logger.info(f"Spotify cache: Saved match for '{track_title}' (ID: {spotify_id}, confidence: {confidence:.2f}).")
