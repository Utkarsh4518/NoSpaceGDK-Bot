"""Case Repository for managing moderation action audit cases."""

import datetime
from typing import List, Optional
from models.case import CaseModel
from repositories.base_repository import BaseRepository

class CaseRepository(BaseRepository):
    """Handles SQL persistence for moderation cases."""

    async def create(
        self,
        guild_id: int,
        case_type: str,
        user_id: int,
        moderator_id: int,
        reason: Optional[str],
        duration_seconds: Optional[int] = None,
        channel_id: Optional[int] = None
    ) -> CaseModel:
        query = """
            INSERT INTO cases (guild_id, case_type, user_id, moderator_id, reason, duration_seconds, status, channel_id)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?);
        """
        cursor = await self.db.execute(query, (guild_id, case_type, user_id, moderator_id, reason, duration_seconds, channel_id))
        await self.db.commit()
        
        return CaseModel(
            id=cursor.lastrowid,
            guild_id=guild_id,
            case_type=case_type,
            user_id=user_id,
            moderator_id=moderator_id,
            reason=reason,
            duration_seconds=duration_seconds,
            status='active',
            channel_id=channel_id,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )

    async def get_by_id(self, case_id: int) -> Optional[CaseModel]:
        query = """
            SELECT id, guild_id, case_type, user_id, moderator_id, reason, duration_seconds, status, channel_id, created_at
            FROM cases
            WHERE id = ?;
        """
        async with self.db.connection.execute(query, (case_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return self._row_to_model(row)

    async def search(
        self,
        guild_id: int,
        user_id: Optional[int] = None,
        moderator_id: Optional[int] = None,
        case_type: Optional[str] = None,
        limit: int = 50
    ) -> List[CaseModel]:
        query = """
            SELECT id, guild_id, case_type, user_id, moderator_id, reason, duration_seconds, status, channel_id, created_at
            FROM cases
            WHERE guild_id = ?
        """
        params = [guild_id]
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if moderator_id:
            query += " AND moderator_id = ?"
            params.append(moderator_id)
        if case_type:
            query += " AND case_type = ?"
            params.append(case_type)
            
        query += " ORDER BY id DESC LIMIT ?;"
        params.append(limit)
        
        cases = []
        async with self.db.connection.execute(query, tuple(params)) as cursor:
            async for row in cursor:
                cases.append(self._row_to_model(row))
        return cases

    async def update_status(self, case_id: int, status: str) -> bool:
        query = "UPDATE cases SET status = ? WHERE id = ?;"
        cursor = await self.db.execute(query, (status, case_id))
        await self.db.commit()
        return cursor.rowcount > 0

    def _row_to_model(self, row: tuple) -> CaseModel:
        created_at_dt = datetime.datetime.fromisoformat(row[9])
        return CaseModel(
            id=row[0],
            guild_id=row[1],
            case_type=row[2],
            user_id=row[3],
            moderator_id=row[4],
            reason=row[5],
            duration_seconds=row[6],
            status=row[7],
            channel_id=row[8],
            created_at=created_at_dt
        )
