"""Guild Settings Repository."""

import json
from typing import List, Optional
from models.moderation import GuildSettingsModel
from repositories.base_repository import BaseRepository

class GuildSettingsRepository(BaseRepository):
    """Handles SQL persistence for per-guild moderation settings."""

    async def get_settings(self, guild_id: int) -> GuildSettingsModel:
        query = """
            SELECT guild_id, default_timeout_seconds, default_warning_limit, audit_channel_id,
                   moderator_roles, protected_roles, ignored_channels, ignored_roles
            FROM guild_settings
            WHERE guild_id = ?;
        """
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                # Return default settings (or create them)
                return await self.create_default(guild_id)
            return self._row_to_model(row)

    async def create_default(self, guild_id: int) -> GuildSettingsModel:
        default_settings = GuildSettingsModel(
            guild_id=guild_id,
            default_timeout_seconds=3600, # 1 hour
            default_warning_limit=3,
            audit_channel_id=None,
            moderator_roles=[],
            protected_roles=[],
            ignored_channels=[],
            ignored_roles=[]
        )
        await self.save_settings(default_settings)
        return default_settings

    async def save_settings(self, settings: GuildSettingsModel) -> None:
        query = """
            INSERT INTO guild_settings (
                guild_id, default_timeout_seconds, default_warning_limit, audit_channel_id,
                moderator_roles, protected_roles, ignored_channels, ignored_roles
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                default_timeout_seconds = excluded.default_timeout_seconds,
                default_warning_limit = excluded.default_warning_limit,
                audit_channel_id = excluded.audit_channel_id,
                moderator_roles = excluded.moderator_roles,
                protected_roles = excluded.protected_roles,
                ignored_channels = excluded.ignored_channels,
                ignored_roles = excluded.ignored_roles;
        """
        await self.db.execute(query, (
            settings.guild_id,
            settings.default_timeout_seconds,
            settings.default_warning_limit,
            settings.audit_channel_id,
            json.dumps(settings.moderator_roles),
            json.dumps(settings.protected_roles),
            json.dumps(settings.ignored_channels),
            json.dumps(settings.ignored_roles)
        ))
        await self.db.commit()

    def _row_to_model(self, row: tuple) -> GuildSettingsModel:
        return GuildSettingsModel(
            guild_id=row[0],
            default_timeout_seconds=row[1],
            default_warning_limit=row[2],
            audit_channel_id=row[3],
            moderator_roles=json.loads(row[4] or "[]"),
            protected_roles=json.loads(row[5] or "[]"),
            ignored_channels=json.loads(row[6] or "[]"),
            ignored_roles=json.loads(row[7] or "[]")
        )
