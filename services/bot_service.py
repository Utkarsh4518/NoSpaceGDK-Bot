"""Core Bot settings and user coordination service for NoSpaceFGK."""

from typing import Optional
from models.domain import Guild, User, BotSettings
from repositories.guild_repository import GuildRepository
from repositories.user_repository import UserRepository
from repositories.settings_repository import SettingsRepository
from services.cache_service import CacheService
from services.base_service import BaseService


class BotService(BaseService):
    """Coordinates business operations for configuration records, user premium statuses, and prefixes."""

    def __init__(
        self,
        guild_repo: GuildRepository,
        user_repo: UserRepository,
        settings_repo: SettingsRepository,
        cache_service: CacheService
    ) -> None:
        """Initialize the bot service.

        Args:
            guild_repo: Guild config database mapper.
            user_repo: User details database mapper.
            settings_repo: Settings key-value database mapper.
            cache_service: Cache service instance.
        """
        self._guild_repo = guild_repo
        self._user_repo = user_repo
        self._settings_repo = settings_repo
        self._cache = cache_service

    async def get_guild_prefix(self, guild_id: int) -> str:
        """Retrieve command prefix for guild (checking cache first).

        Args:
            guild_id: Discord server snowflake.

        Returns:
            The prefix character string.
        """
        cache_key = f"prefix:{guild_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return str(cached)

        guild = await self._guild_repo.get_by_id(guild_id)
        prefix = guild.prefix if guild else "!"

        self._cache.set(cache_key, prefix)
        return prefix

    async def set_guild_prefix(self, guild_id: int, prefix: str) -> Guild:
        """Update guild command prefix.

        Args:
            guild_id: Discord server snowflake.
            prefix: Custom prefix string.

        Returns:
            The updated Guild model.
        """
        guild = await self._guild_repo.create_or_update(guild_id, prefix)

        cache_key = f"prefix:{guild_id}"
        self._cache.delete(cache_key)
        return guild

    async def is_user_premium(self, user_id: int) -> bool:
        """Check if user premium status flag is enabled.

        Args:
            user_id: Discord member snowflake.

        Returns:
            Boolean status flag.
        """
        cache_key = f"premium:{user_id}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return bool(cached)

        user = await self._user_repo.get_by_id(user_id)
        is_prem = user.is_premium if user else False

        self._cache.set(cache_key, is_prem)
        return is_prem

    async def set_user_premium(self, user_id: int, username: Optional[str], is_premium: bool) -> User:
        """Update user premium status record.

        Args:
            user_id: Discord user snowflake.
            username: Member tag.
            is_premium: Premium flag.

        Returns:
            The updated User model.
        """
        user = await self._user_repo.create_or_update(user_id, username, is_premium)

        cache_key = f"premium:{user_id}"
        self._cache.delete(cache_key)
        return user

    async def get_bot_setting(self, key: str) -> Optional[str]:
        """Fetch global bot configuration item.

        Args:
            key: Target parameter name.

        Returns:
            The configured value, or None.
        """
        cache_key = f"setting:{key}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return str(cached)

        setting = await self._settings_repo.get_by_key(key)
        val = setting.value if setting else None

        if val is not None:
            self._cache.set(cache_key, val)
        return val

    async def set_bot_setting(self, key: str, value: str) -> BotSettings:
        """Set or update global configuration parameter.

        Args:
            key: Config parameter key.
            value: Configuration setting.

        Returns:
            The updated BotSettings model.
        """
        setting = await self._settings_repo.create_or_update(key, value)

        cache_key = f"setting:{key}"
        self._cache.delete(cache_key)
        return setting
