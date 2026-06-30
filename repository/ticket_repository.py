"""Ticket Repository for SQL persistence."""

import datetime
from typing import List, Optional
from models.ticket import TicketModel, TicketMessageModel
from repositories.base_repository import BaseRepository

class TicketRepository(BaseRepository):
    """Handles persistence for support tickets, participants, and transcript logging."""

    async def create_ticket(
        self,
        guild_id: int,
        creator_id: int,
        channel_id: int,
        category_id: Optional[int] = None,
        topic: Optional[str] = None
    ) -> TicketModel:
        """Create a new ticket record."""
        query = """
            INSERT INTO tickets (guild_id, creator_id, channel_id, category_id, topic, status)
            VALUES (?, ?, ?, ?, ?, 'open');
        """
        cursor = await self.db.execute(query, (guild_id, creator_id, channel_id, category_id, topic))
        await self.db.commit()
        
        return TicketModel(
            id=cursor.lastrowid,
            guild_id=guild_id,
            creator_id=creator_id,
            channel_id=channel_id,
            category_id=category_id,
            topic=topic,
            status="open",
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )

    async def get_ticket(self, ticket_id: int) -> Optional[TicketModel]:
        """Fetch a ticket by ID."""
        query = """
            SELECT id, guild_id, creator_id, channel_id, category_id, topic, status, claimed_by, created_at, closed_at
            FROM tickets WHERE id = ?;
        """
        async with self.db.connection.execute(query, (ticket_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_ticket(row)
        return None

    async def get_ticket_by_channel(self, channel_id: int) -> Optional[TicketModel]:
        """Fetch a ticket by channel ID."""
        query = """
            SELECT id, guild_id, creator_id, channel_id, category_id, topic, status, claimed_by, created_at, closed_at
            FROM tickets WHERE channel_id = ?;
        """
        async with self.db.connection.execute(query, (channel_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_ticket(row)
        return None

    async def get_active_ticket_by_user(self, guild_id: int, creator_id: int) -> Optional[TicketModel]:
        """Get an active ticket for a user to prevent duplicates."""
        query = """
            SELECT id, guild_id, creator_id, channel_id, category_id, topic, status, claimed_by, created_at, closed_at
            FROM tickets WHERE guild_id = ? AND creator_id = ? AND status = 'open';
        """
        async with self.db.connection.execute(query, (guild_id, creator_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_ticket(row)
        return None

    async def update_ticket(
        self,
        ticket_id: int,
        status: str,
        claimed_by: Optional[int] = None,
        closed_at: Optional[datetime.datetime] = None
    ) -> None:
        """Update ticket state."""
        closed_at_str = closed_at.isoformat() if closed_at else None
        query = """
            UPDATE tickets
            SET status = ?, claimed_by = ?, closed_at = ?
            WHERE id = ?;
        """
        await self.db.execute(query, (status, claimed_by, closed_at_str, ticket_id))
        await self.db.commit()

    async def add_participant(self, ticket_id: int, user_id: int) -> None:
        """Add a participant to the ticket."""
        query = "INSERT OR IGNORE INTO ticket_participants (ticket_id, user_id) VALUES (?, ?);"
        await self.db.execute(query, (ticket_id, user_id))
        await self.db.commit()

    async def remove_participant(self, ticket_id: int, user_id: int) -> None:
        """Remove a participant from the ticket."""
        query = "DELETE FROM ticket_participants WHERE ticket_id = ? AND user_id = ?;"
        await self.db.execute(query, (ticket_id, user_id))
        await self.db.commit()

    async def get_participants(self, ticket_id: int) -> List[int]:
        """Get all user IDs participating in the ticket."""
        query = "SELECT user_id FROM ticket_participants WHERE ticket_id = ?;"
        user_ids = []
        async with self.db.connection.execute(query, (ticket_id,)) as cursor:
            async for row in cursor:
                user_ids.append(row[0])
        return user_ids

    async def add_message(self, ticket_id: int, author_id: int, author_name: str, content: str) -> None:
        """Log a message for transcripts."""
        query = """
            INSERT INTO ticket_messages (ticket_id, author_id, author_name, content)
            VALUES (?, ?, ?, ?);
        """
        await self.db.execute(query, (ticket_id, author_id, author_name, content))
        await self.db.commit()

    async def get_messages(self, ticket_id: int) -> List[TicketMessageModel]:
        """Retrieve logged messages for transcript generation."""
        query = """
            SELECT id, ticket_id, author_id, author_name, content, created_at
            FROM ticket_messages
            WHERE ticket_id = ?
            ORDER BY created_at ASC;
        """
        messages = []
        async with self.db.connection.execute(query, (ticket_id,)) as cursor:
            async for row in cursor:
                messages.append(TicketMessageModel(
                    id=row[0],
                    ticket_id=row[1],
                    author_id=row[2],
                    author_name=row[3],
                    content=row[4],
                    created_at=datetime.datetime.fromisoformat(row[5]) if isinstance(row[5], str) else row[5]
                ))
        return messages

    def _row_to_ticket(self, row: tuple) -> TicketModel:
        created_at_dt = datetime.datetime.fromisoformat(row[8]) if isinstance(row[8], str) else row[8]
        closed_at_dt = None
        if row[9]:
            closed_at_dt = datetime.datetime.fromisoformat(row[9]) if isinstance(row[9], str) else row[9]

        return TicketModel(
            id=row[0],
            guild_id=row[1],
            creator_id=row[2],
            channel_id=row[3],
            category_id=row[4],
            topic=row[5],
            status=row[6],
            claimed_by=row[7],
            created_at=created_at_dt,
            closed_at=closed_at_dt
        )
