"""Active chat session context manager."""

from typing import List
from models.conversation import Message
from utils.logger import logger


class ContextManager:
    """Manages context message bounds and trims conversation logs when limits are reached."""

    def __init__(self, max_messages: int = 20) -> None:
        """Initialize ContextManager.

        Args:
            max_messages: Maximum messages to keep in history context.
        """
        self._max_messages = max_messages
        logger.info(f"Context manager: Initialized with max context messages={max_messages}.")

    def should_trim(self, messages: List[Message]) -> bool:
        """Verify if history size exceeds configured limits.

        Args:
            messages: List of active conversation Message items.

        Returns:
            True if trimming is required, False otherwise.
        """
        # We always keep the system message, so we evaluate the remaining messages
        chat_messages = [m for m in messages if m.role != "system"]
        return len(chat_messages) > self._max_messages

    def trim(self, messages: List[Message]) -> List[Message]:
        """Prune active chat messages array down to context limits.

        Keeps the system message intact at index 0.

        Args:
            messages: Unpruned messages array.

        Returns:
            Trimmed messages array.
        """
        system_msgs = [m for m in messages if m.role == "system"]
        chat_msgs = [m for m in messages if m.role != "system"]

        if len(chat_msgs) <= self._max_messages:
            return messages

        # Retain only the most recent N chat messages
        trimmed_chat = chat_msgs[-self._max_messages:]
        logger.info(f"Context manager: Pruned message history array to {self._max_messages} elements.")

        return system_msgs + trimmed_chat

    @property
    def max_messages(self) -> int:
        """Maximum configured history messages limit."""
        return self._max_messages
