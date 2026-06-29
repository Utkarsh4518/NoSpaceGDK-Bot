"""Repository for custom system prompt overrides and configurations."""

import datetime
from typing import Optional
from models.prompt import Prompt
from repositories.base_repository import BaseRepository
from utils.logger import logger


class PromptRepository(BaseRepository):
    """Manages custom developer, guild, channel, or user prompt overrides in SQLite."""

    async def get_prompt(self, target_type: str, target_id: int) -> Optional[Prompt]:
        """Fetch custom prompt configurations for a target.

        Args:
            target_type: 'guild', 'channel', or 'user'.
            target_id: The Discord snowflake ID.

        Returns:
            Prompt instance or None.
        """
        prompt_id = f"{target_type}:{target_id}"
        query = """
            SELECT id, target_id, target_type, prompt_text, created_by, updated_at
            FROM ai_prompts WHERE id = ?;
        """
        async with self.db.connection.execute(query, (prompt_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            updated_at = row[5]
            if isinstance(updated_at, str):
                try:
                    updated_at = datetime.datetime.fromisoformat(updated_at.replace(" ", "T"))
                except ValueError:
                    updated_at = datetime.datetime.now(datetime.timezone.utc)

            return Prompt(
                id=row[0],
                target_id=row[1],
                target_type=row[2],
                prompt_text=row[3],
                created_by=row[4],
                updated_at=updated_at
            )

    async def set_prompt(self, target_type: str, target_id: int, prompt_text: str, created_by: int) -> None:
        """Save a prompt configuration override.

        Args:
            target_type: 'guild', 'channel', or 'user'.
            target_id: Discord snowflake ID.
            prompt_text: Custom text content of the prompt.
            created_by: User ID who updated the prompt.
        """
        prompt_id = f"{target_type}:{target_id}"
        query = """
            INSERT INTO ai_prompts (id, target_id, target_type, prompt_text, created_by, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                prompt_text = excluded.prompt_text,
                created_by = excluded.created_by,
                updated_at = CURRENT_TIMESTAMP;
        """
        await self.db.execute(query, (prompt_id, target_id, target_type, prompt_text, created_by))
        await self.db.commit()
        logger.info(f"Prompt repository: Saved custom prompt override for '{prompt_id}'.")

    async def delete_prompt(self, target_type: str, target_id: int) -> None:
        """Delete custom prompt configuration override.

        Args:
            target_type: 'guild', 'channel', or 'user'.
            target_id: Discord snowflake ID.
        """
        prompt_id = f"{target_type}:{target_id}"
        query = "DELETE FROM ai_prompts WHERE id = ?;"
        await self.db.execute(query, (prompt_id,))
        await self.db.commit()
        logger.info(f"Prompt repository: Deleted prompt override for '{prompt_id}'.")
