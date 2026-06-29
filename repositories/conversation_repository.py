"""Repository for storing and retrieving AI conversations and message history."""

import datetime
import json
from typing import List, Optional
from models.conversation import Conversation, Message
from repositories.base_repository import BaseRepository
from utils.logger import logger


class ConversationRepository(BaseRepository):
    """Manages SQLite storage for conversation sessions and their message history."""

    async def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Fetch a conversation structure and its history.

        Args:
            conversation_id: Unique string identifier ('target_type:target_id').

        Returns:
            Conversation instance or None.
        """
        # Load conversation meta
        query = """
            SELECT id, target_id, target_type, active_model, active_provider, state, created_at, updated_at
            FROM ai_conversations WHERE id = ?;
        """
        async with self.db.connection.execute(query, (conversation_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None

            # Load message history
            messages = await self.get_messages(conversation_id)

            def parse_date(val) -> datetime.datetime:
                if isinstance(val, str):
                    try:
                        return datetime.datetime.fromisoformat(val.replace(" ", "T"))
                    except ValueError:
                        pass
                return datetime.datetime.now(datetime.timezone.utc)

            state_dict = json.loads(row[5]) if row[5] else None

            return Conversation(
                id=row[0],
                target_id=row[1],
                target_type=row[2],
                active_model=row[3],
                active_provider=row[4],
                messages=messages,
                state=state_dict,
                created_at=parse_date(row[6]),
                updated_at=parse_date(row[7])
            )

    async def save_conversation(self, conv: Conversation) -> None:
        """Create or update conversation metadata.

        Args:
            conv: The Conversation entity.
        """
        query = """
            INSERT INTO ai_conversations (id, target_id, target_type, active_model, active_provider, state, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                active_model = excluded.active_model,
                active_provider = excluded.active_provider,
                state = excluded.state,
                updated_at = CURRENT_TIMESTAMP;
        """
        state_json = json.dumps(conv.state) if conv.state else None
        
        async with self.db.transaction():
            await self.db.execute(query, (
                conv.id, conv.target_id, conv.target_type, conv.active_model, conv.active_provider, state_json
            ))

    async def get_messages(self, conversation_id: str, limit: Optional[int] = None) -> List[Message]:
        """Load messages associated with a conversation.

        Args:
            conversation_id: Conversation session identifier.
            limit: Optional maximum count to fetch.

        Returns:
            List of parsed Message entities.
        """
        limit_clause = f"LIMIT {limit}" if limit else ""
        query = f"""
            SELECT role, content, prompt_tokens, completion_tokens, created_at,
                   tool_calls, tool_call_id, name, provider, model, latency, reasoning_metadata
            FROM ai_messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            {limit_clause};
        """
        messages: List[Message] = []
        async with self.db.connection.execute(query, (conversation_id,)) as cursor:
            async for row in cursor:
                created_at = row[4]
                if isinstance(created_at, str):
                    try:
                        created_at = datetime.datetime.fromisoformat(created_at.replace(" ", "T"))
                    except ValueError:
                        created_at = datetime.datetime.now(datetime.timezone.utc)

                tool_calls = json.loads(row[5]) if row[5] else None
                reasoning = json.loads(row[11]) if row[11] else None

                messages.append(Message(
                    role=row[0],
                    content=row[1],
                    prompt_tokens=row[2],
                    completion_tokens=row[3],
                    created_at=created_at,
                    tool_calls=tool_calls,
                    tool_call_id=row[6],
                    name=row[7],
                    provider=row[8],
                    model=row[9],
                    latency=row[10],
                    reasoning_metadata=reasoning
                ))
        return messages

    async def add_message(self, conversation_id: str, message: Message) -> None:
        """Append a single message record to the conversation with full attributes.

        Args:
            conversation_id: The conversation ID.
            message: The Message to append.
        """
        query = """
            INSERT INTO ai_messages (
                conversation_id, role, content, prompt_tokens, completion_tokens,
                tool_calls, tool_call_id, name, provider, model, latency, reasoning_metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        tool_calls_json = json.dumps(message.tool_calls) if message.tool_calls else None
        reasoning_json = json.dumps(message.reasoning_metadata) if message.reasoning_metadata else None

        async with self.db.transaction():
            await self.db.execute(query, (
                conversation_id,
                message.role,
                message.content,
                message.prompt_tokens,
                message.completion_tokens,
                tool_calls_json,
                message.tool_call_id,
                message.name,
                message.provider,
                message.model,
                message.latency,
                reasoning_json
            ))
            # Update updated_at for conversation
            update_query = "UPDATE ai_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?;"
            await self.db.execute(update_query, (conversation_id,))

    async def clear_conversation(self, conversation_id: str) -> None:
        """Delete all messages associated with a conversation.

        Args:
            conversation_id: Conversation ID to clear.
        """
        query = "DELETE FROM ai_messages WHERE conversation_id = ?;"
        async with self.db.transaction():
            await self.db.execute(query, (conversation_id,))
        logger.info(f"Conversation repository: Cleared messages for '{conversation_id}'.")

    async def trim_messages(self, conversation_id: str, max_messages: int) -> int:
        """Retain only the most recent N messages, deleting older records.

        Args:
            conversation_id: Target conversation session.
            max_messages: Message count limit.

        Returns:
            Number of deleted messages.
        """
        query = """
            SELECT id FROM ai_messages
            WHERE conversation_id = ?
            ORDER BY created_at DESC;
        """
        ids: List[int] = []
        async with self.db.connection.execute(query, (conversation_id,)) as cursor:
            async for row in cursor:
                ids.append(row[0])

        if len(ids) <= max_messages:
            return 0

        # Keep the top max_messages, delete the rest
        to_delete = ids[max_messages:]
        placeholders = ",".join("?" for _ in to_delete)
        delete_query = f"DELETE FROM ai_messages WHERE id IN ({placeholders});"
        
        async with self.db.transaction():
            await self.db.execute(delete_query, to_delete)

        logger.info(f"Conversation repository: Trimmed {len(to_delete)} old messages from '{conversation_id}'.")
        return len(to_delete)
