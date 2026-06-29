"""Configuration service wrapping the bot's static setup properties."""

from config import BotConfig
from services.base_service import BaseService


class ConfigService(BaseService):
    """Binds immutable configurations to service layer components."""

    def __init__(self, config: BotConfig) -> None:
        """Initialize the config service.

        Args:
            config: Validated BotConfig properties.
        """
        self._config: BotConfig = config

    @property
    def config(self) -> BotConfig:
        """Retrieve the immutable bot configurations."""
        return self._config
