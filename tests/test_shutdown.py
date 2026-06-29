"""Integration tests for sequential graceful shutdown sequence."""

import asyncio
import os
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from bot import NoSpaceFGKBot
from config import BotConfig
from database.connection import DatabaseManager
from services.service_container import ServiceContainer
from services.music.player_manager import PlayerManager
from services.cache_service import CacheService


class TestGracefulShutdown(unittest.IsolatedAsyncioTestCase):

    async def test_shutdown_lifecycle_sequence(self) -> None:
        """Verify that shutdown completes in order, cleaning resources and tasks."""
        # 1. Setup mock config & connection path
        config = BotConfig(
            discord_token="dummy_token",
            client_id=123,
            bot_prefix="!",
            log_level="INFO",
            owner_ids=[456],
            development_guild_id=None,
            database_path=Path("tests/test_shutdown.db"),
            cache_ttl=60,
            spotify_client_id=None,
            spotify_client_secret=None,
            openai_api_key=None,
            gemini_api_key=None,
            anthropic_api_key=None,
            openrouter_api_key=None,
            ollama_base_url="http://localhost:11434",
            ai_provider="openai",
            default_model="gpt-4",
            max_context_messages=20,
            system_prompt="system"
        )

        db_path = Path("tests/test_shutdown.db")
        if db_path.exists():
            os.remove(db_path)

        bot = NoSpaceFGKBot(config=config)
        
        # Mock dependency container & services
        bot.container = ServiceContainer()
        
        mock_player_manager = MagicMock()
        mock_player_manager.clean_all_players = AsyncMock()
        bot.container.register(PlayerManager, lambda: mock_player_manager)

        mock_cache = MagicMock()
        mock_cache.clear = MagicMock()
        bot.container.register(CacheService, lambda: mock_cache)

        bot.db = DatabaseManager(db_path)
        await bot.db.connect()

        # Mock super().close() to prevent attempting live gateway socket close
        bot._close_mock = AsyncMock()
        
        # We temporarily patch close to check invocation order
        invocation_order = []

        async def clean_players_spy():
            invocation_order.append("clean_players")

        mock_player_manager.clean_all_players.side_effect = clean_players_spy

        def clear_cache_spy():
            invocation_order.append("clear_cache")

        mock_cache.clear.side_effect = clear_cache_spy

        async def disconnect_db_spy():
            invocation_order.append("disconnect_db")
            # Call original method
            await bot.db.connection.close()
            bot.db._connection = None

        bot.db.disconnect = disconnect_db_spy

        async def close_gateway_spy(*args, **kwargs):
            invocation_order.append("close_gateway")
            await bot._close_mock()

        bot._close_mock.side_effect = lambda: None
        
        # Monkeypatch the super close logic inside bot's class hierarchy for this test
        import discord
        discord.Client.close = close_gateway_spy

        # 2. Trigger the Graceful Shutdown
        await bot.close()

        # 3. Verify ordering:
        # Expected sequence: clean_players -> clear_cache -> disconnect_db -> close_gateway
        self.assertEqual(
            invocation_order,
            ["clean_players", "clear_cache", "disconnect_db", "close_gateway"]
        )

        # Ensure database is disconnected
        self.assertIsNone(bot.db._connection)

        # Cleanup db file
        if db_path.exists():
            os.remove(db_path)
