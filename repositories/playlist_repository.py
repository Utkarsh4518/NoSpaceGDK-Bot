"""Playlist repository managing user-created collections of songs."""

import datetime
from typing import List, Optional
from models.music import Playlist, Track
from repositories.base_repository import BaseRepository
from repositories.music_repository import MusicRepository
from utils.logger import logger


class PlaylistRepository(BaseRepository):
    """Handles persistent storage and track indexing mapping for custom playlists."""

    async def get_by_uuid(self, uuid: str) -> Optional[Playlist]:
        """Fetch custom playlist details by its unique identifier.

        Args:
            uuid: Unique ID of playlist.

        Returns:
            The Playlist domain object or None.
        """
        query = "SELECT uuid, name, owner_id, updated_at FROM playlists WHERE uuid = ?;"
        async with self.db.connection.execute(query, (uuid,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            updated_at_val = row[3]
            if isinstance(updated_at_val, str):
                try:
                    updated_at_dt = datetime.datetime.fromisoformat(updated_at_val.replace(" ", "T"))
                except ValueError:
                    updated_at_dt = datetime.datetime.now(datetime.timezone.utc)
            else:
                updated_at_dt = datetime.datetime.now(datetime.timezone.utc)

            # Retrieve tracks sequentially by position
            tracks_query = """
                SELECT track_uuid FROM playlist_tracks
                WHERE playlist_uuid = ?
                ORDER BY position ASC;
            """
            track_uuids = []
            async with self.db.connection.execute(tracks_query, (uuid,)) as tr_cursor:
                async for tr_row in tr_cursor:
                    track_uuids.append(tr_row[0])

            music_repo = MusicRepository(self.db)
            tracks: List[Track] = []
            for t_uuid in track_uuids:
                track = await music_repo.get_by_uuid(t_uuid)
                if track:
                    tracks.append(track)

            return Playlist(
                uuid=row[0],
                name=row[1],
                owner_id=row[2],
                tracks=tracks,
                updated_at=updated_at_dt
            )

    async def create_or_update(self, playlist: Playlist) -> Playlist:
        """Save a playlist configuration and link associated tracks.

        Args:
            playlist: Playlist domain model configuration.

        Returns:
            The updated Playlist domain model.
        """
        # Save playlist details
        query = """
            INSERT INTO playlists (uuid, name, owner_id, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(uuid) DO UPDATE SET
                name = excluded.name,
                owner_id = excluded.owner_id,
                updated_at = CURRENT_TIMESTAMP;
        """
        await self.db.execute(query, (playlist.uuid, playlist.name, playlist.owner_id))

        music_repo = MusicRepository(self.db)
        for track in playlist.tracks:
            await music_repo.create_or_update(track)

        # Clear existing track relationships
        await self.db.execute("DELETE FROM playlist_tracks WHERE playlist_uuid = ?;", (playlist.uuid,))

        # Insert current tracks sequence
        insert_rel = """
            INSERT INTO playlist_tracks (playlist_uuid, track_uuid, position)
            VALUES (?, ?, ?);
        """
        for index, track in enumerate(playlist.tracks):
            await self.db.execute(insert_rel, (playlist.uuid, track.uuid, index))

        await self.db.commit()
        logger.info(f"Repository operation: Saved custom playlist (UUID: {playlist.uuid}, Name: {playlist.name}, TrackCount: {len(playlist.tracks)}).")
        return playlist

    async def delete(self, uuid: str) -> bool:
        """Remove a playlist.

        Args:
            uuid: Unique playlist ID.

        Returns:
            True if deleted, False otherwise.
        """
        query = "DELETE FROM playlists WHERE uuid = ?;"
        cursor = await self.db.execute(query, (uuid,))
        await self.db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Repository operation: Deleted playlist (UUID: {uuid}).")
        return deleted
