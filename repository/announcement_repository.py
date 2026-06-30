"""Announcement Repository for SQL persistence."""

import datetime
from typing import List, Optional
from models.announcement import AnnouncementModel
from repositories.base_repository import BaseRepository

class AnnouncementRepository(BaseRepository):
    """Handles SQL persistence for scheduled/sent announcements."""

    async def create_announcement(
        self,
        guild_id: int,
        channel_id: int,
        message_text: Optional[str],
        embed_json: Optional[str],
        scheduled_at: Optional[datetime.datetime],
        status: str = "pending"
    ) -> AnnouncementModel:
        """Create a scheduled or instant announcement entry."""
        scheduled_at_str = scheduled_at.isoformat() if scheduled_at else None
        query = """
            INSERT INTO announcements (guild_id, channel_id, message_text, embed_json, scheduled_at, status)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        cursor = await self.db.execute(query, (guild_id, channel_id, message_text, embed_json, scheduled_at_str, status))
        await self.db.commit()
        
        return AnnouncementModel(
            id=cursor.lastrowid,
            guild_id=guild_id,
            channel_id=channel_id,
            message_text=message_text,
            embed_json=embed_json,
            scheduled_at=scheduled_at,
            status=status
        )

    async def get_announcement(self, announcement_id: int) -> Optional[AnnouncementModel]:
        """Fetch announcement by ID."""
        query = """
            SELECT id, guild_id, channel_id, message_text, embed_json, scheduled_at, sent_at, status
            FROM announcements
            WHERE id = ?;
        """
        async with self.db.connection.execute(query, (announcement_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_announcement(row)
        return None

    async def update_announcement(self, announcement_id: int, status: str, sent_at: Optional[datetime.datetime] = None) -> None:
        """Update status and dispatch timestamp for an announcement."""
        sent_at_str = sent_at.isoformat() if sent_at else None
        query = "UPDATE announcements SET status = ?, sent_at = ? WHERE id = ?;"
        await self.db.execute(query, (status, sent_at_str, announcement_id))
        await self.db.commit()

    async def get_pending_announcements(self) -> List[AnnouncementModel]:
        """Fetch all announcements that are pending and ready to send."""
        query = """
            SELECT id, guild_id, channel_id, message_text, embed_json, scheduled_at, sent_at, status
            FROM announcements
            WHERE status = 'pending';
        """
        announcements = []
        async with self.db.connection.execute(query) as cursor:
            async for row in cursor:
                announcements.append(self._row_to_announcement(row))
        return announcements

    async def delete_announcement(self, announcement_id: int) -> None:
        """Delete/cancel an announcement config."""
        query = "DELETE FROM announcements WHERE id = ?;"
        await self.db.execute(query, (announcement_id,))
        await self.db.commit()

    def _row_to_announcement(self, row: tuple) -> AnnouncementModel:
        scheduled_dt = datetime.datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5]
        sent_dt = datetime.datetime.fromisoformat(row[6]) if isinstance(row[6], str) else row[6]
        
        return AnnouncementModel(
            id=row[0],
            guild_id=row[1],
            channel_id=row[2],
            message_text=row[3],
            embed_json=row[4],
            scheduled_at=scheduled_dt,
            sent_at=sent_dt,
            status=row[7]
        )
