"""Warning Repository for managing user warning database records."""

import datetime
from typing import List, Optional
from models.warning import WarningModel
from repositories.base_repository import BaseRepository

class WarningRepository(BaseRepository):
    """Handles SQL persistence for user warnings."""

    async def create(self, guild_id: int, user_id: int, moderator_id: int, reason: Optional[str], points: int = 1, expires_in_days: int = 30) -> WarningModel:
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=expires_in_days)
        query = """
            INSERT INTO warnings (guild_id, user_id, moderator_id, reason, points, is_expired, expires_at)
            VALUES (?, ?, ?, ?, ?, 0, ?);
        """
        cursor = await self.db.execute(query, (guild_id, user_id, moderator_id, reason, points, expires_at.isoformat()))
        await self.db.commit()
        
        return WarningModel(
            id=cursor.lastrowid,
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            reason=reason,
            points=points,
            is_expired=False,
            expires_at=expires_at,
            created_at=datetime.datetime.now(datetime.timezone.utc)
        )

    async def get_active_by_user(self, guild_id: int, user_id: int) -> List[WarningModel]:
        # Expire past warnings first
        await self.expire_past_warnings(guild_id)
        
        query = """
            SELECT id, guild_id, user_id, moderator_id, reason, points, is_expired, expires_at, created_at
            FROM warnings
            WHERE guild_id = ? AND user_id = ? AND is_expired = 0;
        """
        warnings = []
        async with self.db.connection.execute(query, (guild_id, user_id)) as cursor:
            async for row in cursor:
                warnings.append(self._row_to_model(row))
        return warnings

    async def get_all_by_user(self, guild_id: int, user_id: int) -> List[WarningModel]:
        query = """
            SELECT id, guild_id, user_id, moderator_id, reason, points, is_expired, expires_at, created_at
            FROM warnings
            WHERE guild_id = ? AND user_id = ?;
        """
        warnings = []
        async with self.db.connection.execute(query, (guild_id, user_id)) as cursor:
            async for row in cursor:
                warnings.append(self._row_to_model(row))
        return warnings

    async def clear_active(self, guild_id: int, user_id: int) -> int:
        query = "UPDATE warnings SET is_expired = 1 WHERE guild_id = ? AND user_id = ? AND is_expired = 0;"
        cursor = await self.db.execute(query, (guild_id, user_id))
        await self.db.commit()
        return cursor.rowcount

    async def expire_past_warnings(self, guild_id: int) -> int:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        query = "UPDATE warnings SET is_expired = 1 WHERE guild_id = ? AND is_expired = 0 AND expires_at < ?;"
        cursor = await self.db.execute(query, (guild_id, now))
        await self.db.commit()
        return cursor.rowcount

    def _row_to_model(self, row: tuple) -> WarningModel:
        expires_at_dt = None
        if row[7]:
            expires_at_dt = datetime.datetime.fromisoformat(row[7])
        created_at_dt = datetime.datetime.fromisoformat(row[8])
        
        return WarningModel(
            id=row[0],
            guild_id=row[1],
            user_id=row[2],
            moderator_id=row[3],
            reason=row[4],
            points=row[5],
            is_expired=bool(row[6]),
            expires_at=expires_at_dt,
            created_at=created_at_dt
        )
