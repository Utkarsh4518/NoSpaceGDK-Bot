"""Base Tool Interface for AI Agent."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from utils.logger import logger

class BaseTool(ABC):
    """Abstract interface for all AI Agent tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool (must be unique)."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does, used by the AI to decide when to call it."""
        pass

    @property
    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        """JSON Schema defining the expected parameters for this tool."""
        pass

    @property
    def required_permissions(self) -> List[str]:
        """List of discord permission strings required to execute this tool."""
        return []

    @property
    def require_owner(self) -> bool:
        """If True, only the bot owner can execute this tool."""
        return False

    @property
    def cooldown_seconds(self) -> int:
        """Cooldown in seconds per user for this tool."""
        return 0

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the tool with the provided arguments.
        
        Args:
            **kwargs: The parameters parsed from the AI's function call.
            
        Returns:
            The result of the tool execution, typically a dict or string.
        """
        pass

    async def validate(self, **kwargs) -> bool:
        """Validate the arguments before execution.
        
        Args:
            **kwargs: The parameters parsed from the AI's function call.
            
        Returns:
            True if arguments are valid, raises ValueError otherwise.
        """
        return True

    def register(self) -> Dict[str, Any]:
        """Returns the dictionary representation of the tool for the AI provider."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }
