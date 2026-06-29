"""System and custom prompt template management service."""

from typing import Optional
from repositories.prompt_repository import PromptRepository
from utils.logger import logger


class PromptManager:
    """Combines and builds unified system prompts.

    Prioritizes prompt definitions:
        1. Temporary overrides
        2. Channel override (if configured)
        3. Guild override (if configured)
        4. User override (if in direct messages or configured)
        5. Developer default configured system prompt
    """

    def __init__(self, prompt_repo: PromptRepository, default_prompt: str) -> None:
        """Initialize PromptManager.

        Args:
            prompt_repo: Custom Prompt database repository.
            default_prompt: Configured default system instruction string.
        """
        self._repo = prompt_repo
        self._default = default_prompt
        logger.info("Prompt manager: Initialized.")

    async def build_system_prompt(
        self,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        override_prompt: Optional[str] = None
    ) -> str:
        """Build a consolidated system prompt.

        Args:
            guild_id: Guild context.
            channel_id: Channel context.
            user_id: User context.
            override_prompt: Direct override.

        Returns:
            The combined system instruction string.
        """
        if override_prompt:
            return override_prompt

        # Check channel override
        if channel_id:
            channel_prompt = await self._repo.get_prompt("channel", channel_id)
            if channel_prompt:
                return channel_prompt.prompt_text

        # Check guild override
        if guild_id:
            guild_prompt = await self._repo.get_prompt("guild", guild_id)
            if guild_prompt:
                return guild_prompt.prompt_text

        # Check user override
        if user_id:
            user_prompt = await self._repo.get_prompt("user", user_id)
            if user_prompt:
                return user_prompt.prompt_text

        return self._default

    async def set_guild_prompt(self, guild_id: int, prompt_text: str, updated_by: int) -> None:
        """Set a custom system prompt override for a guild.

        Args:
            guild_id: Discord Guild snowflake.
            prompt_text: system prompt override.
            updated_by: Discord User snowflake.
        """
        await self._repo.set_prompt("guild", guild_id, prompt_text, updated_by)

    async def delete_guild_prompt(self, guild_id: int) -> None:
        """Clear the custom system prompt override for a guild.

        Args:
            guild_id: Discord Guild snowflake.
        """
        await self._repo.delete_prompt("guild", guild_id)

    async def set_user_prompt(self, user_id: int, prompt_text: str, updated_by: int) -> None:
        """Set a custom system prompt override for a user.

        Args:
            user_id: Discord User snowflake.
            prompt_text: system prompt override.
            updated_by: User ID updating.
        """
        await self._repo.set_prompt("user", user_id, prompt_text, updated_by)

    async def delete_user_prompt(self, user_id: int) -> None:
        """Clear custom prompt configuration for a user."""
        await self._repo.delete_prompt("user", user_id)
