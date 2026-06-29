"""Settings repository managing database records for global bot parameters."""

import datetime
from typing import Optional
from models.domain import BotSettings
from schemas.validation import SettingsSchema
from repositories.base_repository import BaseRepository
from utils.logger import logger


class SettingsRepository(BaseRepository):
    """Handles persistence and verification rules for global BotSettings."""

    async def get_by_key(self, key: str) -> Optional[BotSettings]:
        """Fetch setting by configuration key.

        Args:
            key: Config item key.

        Returns:
            The BotSettings domain model, or None.
        """
        query = "SELECT key, value, updated_at FROM bot_settings WHERE key = ?;"
        async with self.db.connection.execute(query, (key,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            updated_at_val = row[2]
            if isinstance(updated_at_val, str):
                try:
                    updated_at_dt = datetime.datetime.fromisoformat(updated_at_val.replace(" ", "T"))
                except ValueError:
                    updated_at_dt = datetime.datetime.now(datetime.timezone.utc)
            else:
                updated_at_dt = datetime.datetime.now(datetime.timezone.utc)

            return BotSettings(
                key=row[0],
                value=row[1],
                updated_at=updated_at_dt
            )

    async def create_or_update(self, key: str, value: str) -> BotSettings:
        """Create or update setting parameter in database.

        Args:
            key: Config parameter key name.
            value: Configuration value string.

        Returns:
            The upserted BotSettings domain model.
        """
        payload = {"key": key, "value": value}
        validated = SettingsSchema.validate(payload)

        query = """
            INSERT INTO bot_settings (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP;
        """
        await self.db.execute(query, (validated["key"], validated["value"]))
        await self.db.commit()

        setting = await self.get_by_key(validated["key"])
        if not setting:
            raise RuntimeError("Failed to retrieve setting after persistence.")

        logger.info(f"Repository operation: Saved setting (Key: {key}, Value: {value}).")
        return setting

    async def delete(self, key: str) -> bool:
        """Delete setting parameters.

        Args:
            key: Config key name.

        Returns:
            True if deleted, False otherwise.
        """
        query = "DELETE FROM bot_settings WHERE key = ?;"
        cursor = await self.db.execute(query, (key,))
        await self.db.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Repository operation: Deleted setting key (Key: {key}).")
        return deleted
