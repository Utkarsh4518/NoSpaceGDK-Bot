"""AI Provider routing and registry service."""

from typing import Dict, List, Optional
from providers.ai.base_ai_provider import BaseAIProvider
from utils.logger import logger


class AIProviderRouter:
    """Maintains registered AI provider adapters and routes execution queries."""

    def __init__(self, default_provider_name: str) -> None:
        """Initialize AIProviderRouter.

        Args:
            default_provider_name: Fallback active provider name.
        """
        self._providers: Dict[str, BaseAIProvider] = {}
        self._default_name = default_provider_name
        logger.info(f"AI Provider router: Initialized. Default: '{default_provider_name}'.")

    def register_provider(self, name: str, provider: BaseAIProvider) -> None:
        """Register an AI provider adapter.

        Args:
            name: Lowercase string name (e.g. 'gemini', 'openai').
            provider: Subclass instance of BaseAIProvider.
        """
        self._providers[name.lower()] = provider
        logger.info(f"AI Provider router: Registered adapter for '{name}'.")

    def get_provider(self, name: Optional[str] = None) -> BaseAIProvider:
        """Retrieve a registered provider.

        Args:
            name: Optional provider name (defaults to default configuration).

        Returns:
            The requested BaseAIProvider adapter.

        Raises:
            ValueError: If no providers are configured or requested provider is missing.
        """
        target = (name or self._default_name).lower()
        provider = self._providers.get(target)
        if not provider:
            if self._providers:
                # Fallback to the first available provider if the requested one is missing
                fallback_name = list(self._providers.keys())[0]
                logger.warning(
                    f"AI Provider router: Requested provider '{target}' not found. "
                    f"Falling back to first active provider '{fallback_name}'."
                )
                return self._providers[fallback_name]
            
            raise ValueError(f"No active AI providers registered. Check your API credentials in .env.")
        
        return provider

    def list_available_providers(self) -> List[str]:
        """Fetch list of all configured and registered providers.

        Returns:
            List of provider names.
        """
        return list(self._providers.keys())

    @property
    def default_provider_name(self) -> str:
        """Default active provider configuration."""
        return self._default_name
