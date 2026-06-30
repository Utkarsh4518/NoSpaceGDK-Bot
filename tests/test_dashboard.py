"""Integration tests for the Web Dashboard backend API layer."""

import os
import unittest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from dashboard.backend.server import app

class TestDashboardAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        
        # Mock bot client instance
        self.bot_mock = MagicMock()
        self.bot_mock.guilds = []
        self.bot_mock.latency = 0.05
        self.bot_mock.start_time = None
        
        # Injected state
        app.state.bot = self.bot_mock

    def test_stats_endpoint(self):
        """Verify that /api/stats returns spec dictionary format."""
        response = self.client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("guild_count", data)
        self.assertIn("user_count", data)
        self.assertIn("latency_ms", data)
        self.assertIn("uptime_seconds", data)
        self.assertIn("platform", data)
        self.assertIn("python_version", data)
        self.assertIn("active_music_players", data)
        
        self.assertEqual(data["latency_ms"], 50.0)

    def test_auth_login_redirect(self):
        """Verify auth/login route correctly redirects to Discord OAuth2 URL."""
        # Set Client Secret temporarily for test
        from dashboard.backend.auth import auth_handler
        auth_handler.CLIENT_SECRET = "test_secret"
        auth_handler.CLIENT_ID = "test_id"
        
        response = self.client.get("/api/auth/login", follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertIn("discord.com/api/oauth2/authorize", response.headers["location"])
