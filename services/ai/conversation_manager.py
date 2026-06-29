"""Conversation session controller."""

from typing import List, Optional
from models.conversation import Conversation, Message
from repositories.conversation_repository import ConversationRepository
from services.ai.context_manager import ContextManager
from utils.logger import logger


class ConversationManager:
    """Manages active conversation loading, database synchronization,
    and history limits trimming.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        context_manager: ContextManager
    ) -> None:
        """Initialize ConversationManager.

        Args:
            conversation_repo: DB Repository for conversation data.
            context_manager: Context trim evaluator.
        """
        self._repo = conversation_repo
        self._context = context_manager
        logger.info("Conversation manager: Initialized.")

    async def get_or_create_conversation(
        self,
        target_id: int,
        target_type: str,
        default_model: str,
        default_provider: str
    ) -> Conversation:
        """Retrieve existing conversation session, or construct a new one.

        Args:
            target_id: Guild ID, Channel ID, or User ID.
            target_type: 'guild', 'channel', or 'user'.
            default_model: Initial model setting.
            default_provider: Initial provider setting.

        Returns:
            The Conversation object loaded from SQLite.
        """
        conversation_id = f"{target_type}:{target_id}"
        conv = await self._repo.get_conversation(conversation_id)

        if not conv:
            logger.info(f"Conversation manager: Creating new conversation '{conversation_id}'.")
            conv = Conversation(
                id=conversation_id,
                target_id=target_id,
                target_type=target_type,
                active_model=default_model,
                active_provider=default_provider
            )
            await self._repo.save_conversation(conv)

        return conv

    async def update_settings(self, conversation_id: str, provider: str, model: str) -> None:
        """Update active model/provider settings for a conversation.

        Args:
            conversation_id: Session identifier.
            provider: Active AI provider.
            model: Active AI model.
        """
        conv = await self._repo.get_conversation(conversation_id)
        if conv:
            conv.active_provider = provider
            conv.active_model = model
            await self._repo.save_conversation(conv)
            logger.info(f"Conversation manager: Updated settings for '{conversation_id}' to {provider}/{model}.")

    async def add_message(self, conversation_id: str, message: Message) -> None:
        """Append a message to the conversation history and trim if necessary.

        Args:
            conversation_id: Conversation session identifier.
            message: Message object to persist.
        """
        await self._repo.add_message(conversation_id, message)
        
        # Prune message logs if they exceed config limits
        await self._repo.trim_messages(conversation_id, self._context.max_messages)

    async def clear_conversation(self, conversation_id: str) -> None:
        """Clear all conversation message history logs.

        Args:
            conversation_id: Conversation session identifier.
        """
        await self._repo.clear_conversation(conversation_id)
