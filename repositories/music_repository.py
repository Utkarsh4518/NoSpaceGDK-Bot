"""Music tracks repository managing DB records for individual song metadata."""

import datetime
import json
from typing import Optional
from models.music import Track
from repositories.base_repository import BaseRepository
from utils.logger import logger


class MusicRepository(BaseRepository):
    """Handles persistent storage and retrieval of music Track domain models."""

    async def get_by_uuid(self, uuid: str) -> Optional[Track]:
        """Retrieve a Track details by its UUID.

        Args:
            uuid: Unique ID of track.

        Returns:
            The Track domain model or None.
        """
        query = """
            SELECT uuid, title, artist, duration, thumbnail, provider, url,
                   requested_by, isrc, metadata, added_at
            FROM music_tracks WHERE uuid = ?;
        """
        async with self.db.connection.execute(query, (uuid,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            added_at_val = row[10]
            if isinstance(added_at_val, str):
                try:
                    added_at_dt = datetime.datetime.fromisoformat(added_at_val.replace(" ", "T"))
                except ValueError:
                    added_at_dt = datetime.datetime.now(datetime.timezone.utc)
            else:
                added_at_dt = datetime.datetime.now(datetime.timezone.utc)

            metadata_dict = {}
            if row[9]:
                try:
                    metadata_dict = json.loads(row[9])
                except json.JSONDecodeError:
                    pass

            return Track(
                uuid=row[0],
                title=row[1],
                artist=row[2],
                duration=row[3],
                thumbnail=row[4],
                provider=row[5],
                url=row[6],
                requested_by=row[7],
                isrc=row[8],
                metadata=metadata_dict,
                added_at=added_at_dt
            )

    async def create_or_update(self, track: Track) -> Track:
        """Save track parameters in the database.

        Args:
            track: The Track domain model instance.

        Returns:
            The upserted Track domain model.
        """
        metadata_str = json.dumps(track.metadata)
        query = """
            INSERT INTO music_tracks (uuid, title, artist, duration, thumbnail, provider, url, requested_by, isrc, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uuid) DO UPDATE SET
                title = excluded.title,
                artist = excluded.artist,
                duration = excluded.duration,
                thumbnail = excluded.thumbnail,
                provider = excluded.provider,
                url = excluded.url,
                requested_by = excluded.requested_by,
                isrc = excluded.isrc,
                metadata = excluded.metadata;
        """
        await self.db.execute(
            query,
            (
                track.uuid, track.title, track.artist, track.duration,
                track.thumbnail, track.provider, track.url, track.requested_by,
                track.isrc, metadata_str
            )
        )
        await self.db.commit()

        logger.info(f"Repository operation: Saved track metadata (UUID: {track.uuid}, Title: {track.title}).")
        return track

    async def delete(self, uuid: str) -> bool:
        """Remove a track metadata record.

        Args:
            uuid: Unique ID.

        Returns:
            True if deleted, False otherwise.
        """
        query = "DELETE FROM music_tracks WHERE uuid = ?;"
        cursor = await self.db.execute(query, (uuid,))
        await self.db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Repository operation: Deleted track (UUID: {uuid}).")
        return deleted
