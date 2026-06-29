"""Integration tests for complete AI Conversation and Message history persistence."""

import datetime
import os
import unittest
from pathlib import Path
from database.connection import DatabaseManager
from models.conversation import Conversation, Message
from repositories.conversation_repository import ConversationRepository


class TestAIPersistence(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.db_path = Path("tests/test_ai.db")
        if self.db_path.exists():
            os.remove(self.db_path)

        self.db = DatabaseManager(self.db_path)
        await self.db.connect()

        # Create Tables to match current schema
        await self.db.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id TEXT PRIMARY KEY,
                target_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                active_model TEXT NOT NULL,
                active_provider TEXT NOT NULL,
                state TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await self.db.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL DEFAULT 0,
                completion_tokens INTEGER NOT NULL DEFAULT 0,
                tool_calls TEXT,
                tool_call_id TEXT,
                name TEXT,
                provider TEXT,
                model TEXT,
                latency REAL,
                reasoning_metadata TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE CASCADE
            );
            """
        )
        await self.db.commit()

        self.repo = ConversationRepository(self.db)

    async def asyncTearDown(self) -> None:
        await self.db.disconnect()
        if self.db_path.exists():
            os.remove(self.db_path)

    async def test_complete_conversation_persistence(self) -> None:
        """Verify that all conversation state properties, tool calls, and latencies are saved and reloaded."""
        conv = Conversation(
            id="channel:12345",
            target_id=12345,
            target_type="channel",
            active_model="gpt-4",
            active_provider="openai",
            state={"context_depth": 2, "flags": ["debug", "premium"]}
        )
        await self.repo.save_conversation(conv)

        # 1. Create message list with diverse attributes
        user_msg = Message(role="user", content="What is the weather?")
        tool_call_msg = Message(
            role="assistant",
            content="",
            tool_calls=[{"id": "call_999", "type": "function", "function": {"name": "get_weather", "arguments": '{"city": "Paris"}'}}],
            provider="openai",
            model="gpt-4",
            latency=0.45
        )
        tool_resp_msg = Message(
            role="tool",
            content='{"weather": "sunny", "temp": 22}',
            tool_call_id="call_999",
            name="get_weather"
        )
        assistant_final_msg = Message(
            role="assistant",
            content="It is sunny and 22 degrees in Paris.",
            prompt_tokens=150,
            completion_tokens=45,
            provider="openai",
            model="gpt-4",
            latency=1.20,
            reasoning_metadata={"confidence": 0.99}
        )

        # Write them to DB
        await self.repo.add_message(conv.id, user_msg)
        await self.repo.add_message(conv.id, tool_call_msg)
        await self.repo.add_message(conv.id, tool_resp_msg)
        await self.repo.add_message(conv.id, assistant_final_msg)

        # 2. Reload conversation from DB
        loaded_conv = await self.repo.get_conversation("channel:12345")
        self.assertIsNotNone(loaded_conv)
        self.assertEqual(loaded_conv.active_model, "gpt-4")
        self.assertEqual(loaded_conv.active_provider, "openai")
        self.assertEqual(loaded_conv.state, {"context_depth": 2, "flags": ["debug", "premium"]})

        messages = loaded_conv.messages
        self.assertEqual(len(messages), 4)

        # Assert User Message properties
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "What is the weather?")

        # Assert Tool Call Message properties
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, "")
        self.assertEqual(messages[1].tool_calls, [{"id": "call_999", "type": "function", "function": {"name": "get_weather", "arguments": '{"city": "Paris"}'}}])
        self.assertEqual(messages[1].provider, "openai")
        self.assertEqual(messages[1].model, "gpt-4")
        self.assertEqual(messages[1].latency, 0.45)

        # Assert Tool Response Message properties
        self.assertEqual(messages[2].role, "tool")
        self.assertEqual(messages[2].content, '{"weather": "sunny", "temp": 22}')
        self.assertEqual(messages[2].tool_call_id, "call_999")
        self.assertEqual(messages[2].name, "get_weather")

        # Assert Assistant Final Message properties
        self.assertEqual(messages[3].role, "assistant")
        self.assertEqual(messages[3].content, "It is sunny and 22 degrees in Paris.")
        self.assertEqual(messages[3].prompt_tokens, 150)
        self.assertEqual(messages[3].completion_tokens, 45)
        self.assertEqual(messages[3].provider, "openai")
        self.assertEqual(messages[3].model, "gpt-4")
        self.assertEqual(messages[3].latency, 1.20)
        self.assertEqual(messages[3].reasoning_metadata, {"confidence": 0.99})
