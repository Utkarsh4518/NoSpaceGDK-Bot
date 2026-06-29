"""Abstract Base AI Provider interface for the NoSpaceFGK bot.

Specifies abstract contract APIs for chat completion, streaming completion,
model listing, token counting, and health status checking.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional


class BaseAIProvider(ABC):
    """Abstract class outlining standard operations for all AI backend adapters."""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Perform a standard non-streaming chat request.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Target model name override.
            temperature: Sampling temperature (0.0 to 1.0).
            max_tokens: Maximum tokens in response.

        Returns:
            Dict containing response:
                - 'content': str
                - 'prompt_tokens': int
                - 'completion_tokens': int
                - 'model': str
        """
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Perform a streaming chat request yielding delta changes.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Target model name override.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.

        Yields:
            Dict containing:
                - 'delta': str
                - 'prompt_tokens': int (only yielded on final chunk or estimated)
                - 'completion_tokens': int (only yielded on final chunk or estimated)
        """
        pass

    async def embeddings(self, text: str) -> List[float]:
        """Generate vector embedding representation for text.

        This is a placeholder method for future implementation.

        Args:
            text: Input string.

        Returns:
            List of float values.
        """
        return []

    @abstractmethod
    async def list_models(self) -> List[str]:
        """Fetch list of models supported by this provider.

        Returns:
            List of model names.
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify the provider API is accessible and healthy.

        Returns:
            True if healthy, False otherwise.
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count or estimate the number of tokens in a string.

        Args:
            text: The target string.

        Returns:
            Token count estimate.
        """
        pass
