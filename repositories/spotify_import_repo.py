"""Repository for tracking Spotify import operations."""

import datetime
from typing import List
from dataclasses import dataclass
from repositories.base_repository import BaseRepository
from utils.logger import logger


@dataclass
class SpotifyImportRecord:
    """Record of a Spotify playlist/album/artist import operation."""
    id: int
    spotify_url: str
    spotify_type: str
    track_count: int
    imported_by: int
    guild_id: int
    imported_at: datetime.datetime


class SpotifyImportRepository(BaseRepository):
    """Manages persistent logging of Spotify import operations."""

    async def log_import(
        self,
        spotify_url: str,
        spotify_type: str,
        track_count: int,
        imported_by: int,
        guild_id: int
    ) -> None:
        """Log a Spotify import operation.

        Args:
            spotify_url: The original Spotify URL.
            spotify_type: Type of import (track, album, playlist, artist).
            track_count: Number of tracks imported.
            imported_by: Discord user snowflake.
            guild_id: Discord guild snowflake.
        """
        query = """
            INSERT INTO spotify_imports (spotify_url, spotify_type, track_count, imported_by, guild_id)
            VALUES (?, ?, ?, ?, ?);
        """
        await self.db.execute(query, (spotify_url, spotify_type, track_count, imported_by, guild_id))
        await self.db.commit()
        logger.info(f"Spotify import: Logged {spotify_type} import ({track_count} tracks) for Guild {guild_id}.")

    async def get_recent_imports(self, guild_id: int, limit: int = 10) -> List[SpotifyImportRecord]:
        """Fetch recent Spotify imports for a guild.

        Args:
            guild_id: Discord guild snowflake.
            limit: Max records.

        Returns:
            List of SpotifyImportRecord models.
        """
        query = """
            SELECT id, spotify_url, spotify_type, track_count, imported_by, guild_id, imported_at
            FROM spotify_imports
            WHERE guild_id = ?
            ORDER BY imported_at DESC
            LIMIT ?;
        """
        records: List[SpotifyImportRecord] = []
        async with self.db.connection.execute(query, (guild_id, limit)) as cursor:
            async for row in cursor:
                imported_at = row[6]
                if isinstance(imported_at, str):
                    try:
                        imported_at = datetime.datetime.fromisoformat(imported_at.replace(" ", "T"))
                    except ValueError:
                        imported_at = datetime.datetime.now(datetime.timezone.utc)

                records.append(SpotifyImportRecord(
                    id=row[0],
                    spotify_url=row[1],
                    spotify_type=row[2],
                    track_count=row[3],
                    imported_by=row[4],
                    guild_id=row[5],
                    imported_at=imported_at
                ))
        return records
