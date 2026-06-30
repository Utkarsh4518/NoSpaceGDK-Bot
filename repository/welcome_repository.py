"""Welcome, Goodbye, Autorole, and Verification Repository."""

from typing import List, Optional
from models.welcome import WelcomeSettingsModel, GoodbyeSettingsModel
from models.verification import VerificationSettingsModel
from repositories.base_repository import BaseRepository

class WelcomeRepository(BaseRepository):
    """Handles settings for welcome/goodbye notifications, autoroles, and verification."""

    async def save_welcome_settings(
        self,
        guild_id: int,
        channel_id: Optional[int],
        message_text: Optional[str],
        embed_json: Optional[str],
        dm_enabled: bool,
        enabled: bool
    ) -> WelcomeSettingsModel:
        """Create or update welcome settings."""
        query = """
            INSERT OR REPLACE INTO welcome_settings (guild_id, channel_id, message_text, embed_json, dm_enabled, enabled)
            VALUES (?, ?, ?, ?, ?, ?);
        """
        await self.db.execute(query, (guild_id, channel_id, message_text, embed_json, int(dm_enabled), int(enabled)))
        await self.db.commit()
        return WelcomeSettingsModel(
            guild_id=guild_id,
            channel_id=channel_id,
            message_text=message_text,
            embed_json=embed_json,
            dm_enabled=dm_enabled,
            enabled=enabled
        )

    async def get_welcome_settings(self, guild_id: int) -> Optional[WelcomeSettingsModel]:
        """Fetch welcome settings for a guild."""
        query = "SELECT guild_id, channel_id, message_text, embed_json, dm_enabled, enabled FROM welcome_settings WHERE guild_id = ?;"
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return WelcomeSettingsModel(
                    guild_id=row[0],
                    channel_id=row[1],
                    message_text=row[2],
                    embed_json=row[3],
                    dm_enabled=bool(row[4]),
                    enabled=bool(row[5])
                )
        return None

    async def save_goodbye_settings(
        self,
        guild_id: int,
        channel_id: Optional[int],
        message_text: Optional[str],
        embed_json: Optional[str],
        enabled: bool
    ) -> GoodbyeSettingsModel:
        """Create or update goodbye settings."""
        query = """
            INSERT OR REPLACE INTO goodbye_settings (guild_id, channel_id, message_text, embed_json, enabled)
            VALUES (?, ?, ?, ?, ?);
        """
        await self.db.execute(query, (guild_id, channel_id, message_text, embed_json, int(enabled)))
        await self.db.commit()
        return GoodbyeSettingsModel(
            guild_id=guild_id,
            channel_id=channel_id,
            message_text=message_text,
            embed_json=embed_json,
            enabled=enabled
        )

    async def get_goodbye_settings(self, guild_id: int) -> Optional[GoodbyeSettingsModel]:
        """Fetch goodbye settings for a guild."""
        query = "SELECT guild_id, channel_id, message_text, embed_json, enabled FROM goodbye_settings WHERE guild_id = ?;"
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return GoodbyeSettingsModel(
                    guild_id=row[0],
                    channel_id=row[1],
                    message_text=row[2],
                    embed_json=row[3],
                    enabled=bool(row[4])
                )
        return None

    async def add_autorole(self, guild_id: int, role_id: int) -> None:
        """Add a role to the guild's autoroles."""
        query = "INSERT OR IGNORE INTO autoroles (guild_id, role_id) VALUES (?, ?);"
        await self.db.execute(query, (guild_id, role_id))
        await self.db.commit()

    async def remove_autorole(self, guild_id: int, role_id: int) -> None:
        """Remove a role from the guild's autoroles."""
        query = "DELETE FROM autoroles WHERE guild_id = ? AND role_id = ?;"
        await self.db.execute(query, (guild_id, role_id))
        await self.db.commit()

    async def get_autoroles(self, guild_id: int) -> List[int]:
        """Fetch all autoroles for a guild."""
        query = "SELECT role_id FROM autoroles WHERE guild_id = ?;"
        role_ids = []
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            async for row in cursor:
                role_ids.append(row[0])
        return role_ids

    async def save_verification_settings(
        self,
        guild_id: int,
        role_id: Optional[int],
        channel_id: Optional[int],
        enabled: bool,
        type_: str = "button"
    ) -> VerificationSettingsModel:
        """Create or update verification settings."""
        query = """
            INSERT OR REPLACE INTO verification_settings (guild_id, role_id, channel_id, enabled, type)
            VALUES (?, ?, ?, ?, ?);
        """
        await self.db.execute(query, (guild_id, role_id, channel_id, int(enabled), type_))
        await self.db.commit()
        return VerificationSettingsModel(
            guild_id=guild_id,
            role_id=role_id,
            channel_id=channel_id,
            enabled=enabled,
            type=type_
        )

    async def get_verification_settings(self, guild_id: int) -> Optional[VerificationSettingsModel]:
        """Fetch verification settings for a guild."""
        query = "SELECT guild_id, role_id, channel_id, enabled, type FROM verification_settings WHERE guild_id = ?;"
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return VerificationSettingsModel(
                    guild_id=row[0],
                    role_id=row[1],
                    channel_id=row[2],
                    enabled=bool(row[3]),
                    type=row[4]
                )
        return None
