"""AI Memory and context aggregation service."""

from typing import Dict, List, Optional
from models.conversation import Message
from utils.logger import logger


class MemoryManager:
    """Consolidates short-term conversation context, summary caches,
    and placeholder interfaces for long-term memory retrieval.
    """

    def __init__(self) -> None:
        """Initialize MemoryManager."""
        self._summaries: Dict[str, str] = {}
        self._long_term_store: Dict[str, Dict[str, str]] = {}
        logger.info("Memory manager: Initialized.")

    def get_summary(self, conversation_id: str) -> Optional[str]:
        """Fetch cached conversation summary.

        This is a placeholder for conversation summarization logic.
        """
        return self._summaries.get(conversation_id)

    def set_summary(self, conversation_id: str, summary: str) -> None:
        """Store a conversation summary cache."""
        self._summaries[conversation_id] = summary
        logger.debug(f"Memory manager: Stored summary for '{conversation_id}'.")

    def retrieve_long_term(self, user_id: int, query: str) -> List[str]:
        """Retrieve memories from long-term memory.

        Placeholder for future vector/RAG memory lookup.
        """
        logger.debug(f"Memory manager: Retrieve long term memory for User {user_id} using query '{query}'.")
        return []

    def store_long_term(self, user_id: int, key: str, value: str) -> None:
        """Persist key-value state to long-term memory.

        Placeholder for future long term persistence.
        """
        if str(user_id) not in self._long_term_store:
            self._long_term_store[str(user_id)] = {}
        self._long_term_store[str(user_id)][key] = value
        logger.debug(f"Memory manager: Stored user memory for User {user_id} ({key}={value}).")
