"""Music providers selection coordinator for NoSpaceFGK.

Registers active search and stream providers, validating URLs and matching
queries to target services.
"""

from typing import Dict, Optional
from providers.base_provider import BaseMusicProvider
from utils.logger import logger


class ProviderManager:
    """Manages active music search/streaming adapters registration and selections."""

    def __init__(self) -> None:
        """Initialize the provider manager."""
        self._providers: Dict[str, BaseMusicProvider] = {}

    def register_provider(self, name: str, provider: BaseMusicProvider) -> None:
        """Register a provider adapter.

        Args:
            name: Key name identifier (e.g., 'youtube').
            provider: Concrete BaseMusicProvider instance.
        """
        self._providers[name.lower()] = provider
        logger.info(f"Provider manager: Registered provider adapter '{name}'.")

    def get_provider(self, name: str) -> Optional[BaseMusicProvider]:
        """Fetch a registered provider.

        Args:
            name: Key identifier.

        Returns:
            The BaseMusicProvider instance, or None.
        """
        return self._providers.get(name.lower())

    def resolve_provider_by_url(self, url: str) -> Optional[BaseMusicProvider]:
        """Select provider based on URL format check.

        Args:
            url: Song/Playlist webpage link.

        Returns:
            Matched BaseMusicProvider instance, or None.
        """
        for name, provider in self._providers.items():
            try:
                if provider.validate_url(url):
                    logger.info(f"Provider manager: Matched URL '{url}' to provider '{name}'.")
                    return provider
            except NotImplementedError:
                pass
        return None
