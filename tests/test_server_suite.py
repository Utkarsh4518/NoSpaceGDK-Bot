"""Integration tests for Server Management Suite services and repositories."""

import asyncio
import datetime
import os
import unittest
import json
from pathlib import Path
import discord
from unittest.mock import AsyncMock, MagicMock

from database.connection import DatabaseManager
from repository.welcome_repository import WelcomeRepository
from repository.ticket_repository import TicketRepository
from repository.reaction_role_repository import ReactionRoleRepository
from repository.announcement_repository import AnnouncementRepository

from services.server.welcome_service import WelcomeService, interpolate_variables
from services.server.goodbye_service import GoodbyeService
from services.server.autorole_service import AutoroleService
from services.server.reaction_role_service import ReactionRoleService
from services.server.ticket_service import TicketService
from services.server.announcement_service import AnnouncementService
from services.server.verification_service import VerificationService
from services.cache_service import CacheService

class TestServerManagementSuite(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        import uuid
        self.db_id = uuid.uuid4().hex
        self.db_path = Path(f"tests/test_server_{self.db_id}.db")

        self.db = DatabaseManager(self.db_path)
        await self.db.connect()

        # Build Phase 11 Tables
        await self.db.connection.executescript("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                claimed_by INTEGER,
                category_id INTEGER,
                topic TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ticket_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                author_id INTEGER NOT NULL,
                author_name TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ticket_participants (
                ticket_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                PRIMARY KEY (ticket_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS reaction_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                emoji TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                group_name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reaction_role_messages (
                message_id INTEGER PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                title TEXT,
                description TEXT,
                group_name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'reaction'
            );

            CREATE TABLE IF NOT EXISTS welcome_settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                message_text TEXT,
                embed_json TEXT,
                dm_enabled INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS goodbye_settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER,
                message_text TEXT,
                embed_json TEXT,
                enabled INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS autoroles (
                guild_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (guild_id, role_id)
            );

            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_text TEXT,
                embed_json TEXT,
                scheduled_at TIMESTAMP,
                sent_at TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'pending'
            );

            CREATE TABLE IF NOT EXISTS verification_settings (
                guild_id INTEGER PRIMARY KEY,
                role_id INTEGER,
                channel_id INTEGER,
                enabled INTEGER DEFAULT 0,
                type TEXT NOT NULL DEFAULT 'button'
            );
        """)
        await self.db.commit()

        # Setup Repositories
        self.welcome_repo = WelcomeRepository(self.db)
        self.ticket_repo = TicketRepository(self.db)
        self.rr_repo = ReactionRoleRepository(self.db)
        self.announce_repo = AnnouncementRepository(self.db)

        # Setup Cache
        self.cache_service = CacheService(default_ttl=10.0)

        # Setup Services
        self.bot_mock = MagicMock()
        self.bot_mock.loop = asyncio.get_running_loop()
        self.bot_mock.is_closed = MagicMock(return_value=False)

        self.welcome_service = WelcomeService(self.welcome_repo, self.cache_service)
        self.goodbye_service = GoodbyeService(self.welcome_repo, self.cache_service)
        self.autorole_service = AutoroleService(self.welcome_repo, self.cache_service)
        self.rr_service = ReactionRoleService(self.bot_mock, self.rr_repo, self.cache_service)
        self.ticket_service = TicketService(self.bot_mock, self.ticket_repo, self.cache_service)
        self.announce_service = AnnouncementService(self.bot_mock, self.announce_repo)
        self.verify_service = VerificationService(self.bot_mock, self.welcome_repo, self.cache_service)

    async def asyncTearDown(self) -> None:
        if self.announce_service.scheduler_task:
            self.announce_service.scheduler_task.cancel()
            try:
                await self.announce_service.scheduler_task
            except asyncio.CancelledError:
                pass
        await self.db.disconnect()
        for _ in range(10):
            try:
                if self.db_path.exists():
                    os.remove(self.db_path)
                break
            except PermissionError:
                await asyncio.sleep(0.1)


    async def test_welcome_goodbye_autorole_settings(self) -> None:
        """Test welcome/goodbye configuration persistence and variable interpolation."""
        # 1. Test Welcome settings save & retrieve
        await self.welcome_service.save_settings(
            guild_id=123,
            channel_id=456,
            message_text="Welcome {user} to {server}! Total: {member_count}",
            embed_json='{"title": "Welcome to {server}"}',
            dm_enabled=True,
            enabled=True
        )

        settings = await self.welcome_service.get_settings(123)
        self.assertIsNotNone(settings)
        self.assertEqual(settings.channel_id, 456)
        self.assertEqual(settings.dm_enabled, True)
        self.assertEqual(settings.enabled, True)

        # Mock discord member
        member_mock = MagicMock()
        member_mock.mention = "<@789>"
        member_mock.name = "TestUser"
        member_mock.guild.name = "TestServer"
        member_mock.guild.member_count = 100

        # Test interpolation
        interpolated_text = interpolate_variables(settings.message_text, member_mock)
        self.assertEqual(interpolated_text, "Welcome <@789> to TestServer! Total: 100")

        # 2. Test Autoroles
        await self.autorole_service.add_autorole(123, 111)
        await self.autorole_service.add_autorole(123, 222)

        roles = await self.autorole_service.get_autoroles(123)
        self.assertEqual(len(roles), 2)
        self.assertIn(111, roles)
        self.assertIn(222, roles)

        await self.autorole_service.remove_autorole(123, 111)
        roles = await self.autorole_service.get_autoroles(123)
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0], 222)

    async def test_ticket_lifecycle(self) -> None:
        """Test support ticket creation, participants addition, messaging, and transcripts."""
        guild_mock = MagicMock()
        guild_mock.id = 999
        guild_mock.default_role = MagicMock()
        guild_mock.me = MagicMock()

        creator_mock = MagicMock()
        creator_mock.id = 888
        creator_mock.name = "TicketCreator"
        creator_mock.mention = "<@888>"

        support_role = MagicMock()
        support_role.id = 777

        # Mock channel creation
        channel_mock = AsyncMock(spec=discord.TextChannel)
        channel_mock.id = 555
        channel_mock.name = "ticket-ticketcreator"
        channel_mock.set_permissions = AsyncMock()
        guild_mock.create_text_channel = AsyncMock(return_value=channel_mock)
        guild_mock.get_channel = MagicMock(return_value=channel_mock)
        self.bot_mock.get_guild = MagicMock(return_value=guild_mock)

        # Create user ticket
        ticket = await self.ticket_service.create_user_ticket(
            guild=guild_mock,
            creator=creator_mock,
            support_role=support_role,
            topic="Banned account appeal"
        )

        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.creator_id, 888)
        self.assertEqual(ticket.channel_id, 555)
        self.assertEqual(ticket.topic, "Banned account appeal")
        self.assertEqual(ticket.status, "open")

        # Add message logs
        await self.ticket_service.log_ticket_message(555, creator_mock, "Hello, please help.")
        staff_mock = MagicMock()
        staff_mock.id = 666
        staff_mock.name = "StaffOne"
        staff_mock.guild = guild_mock
        await self.ticket_service.log_ticket_message(555, staff_mock, "Sure, what's wrong?")

        # Fetch messages
        messages = await self.ticket_repo.get_messages(ticket.id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].content, "Hello, please help.")
        self.assertEqual(messages[1].content, "Sure, what's wrong?")

        # Claim ticket
        claim_res = await self.ticket_service.claim_ticket(ticket.id, staff_mock)
        self.assertIn("Successfully claimed", claim_res)

        updated_ticket = await self.ticket_repo.get_ticket(ticket.id)
        self.assertEqual(updated_ticket.claimed_by, 666)

        # Close ticket and check transcript file creation
        transcript_file = await self.ticket_service.close_ticket(555, "Issue resolved.")
        self.assertIsNotNone(transcript_file)
        self.assertEqual(transcript_file.filename, f"ticket-{ticket.id}-transcript.txt")

        closed_ticket = await self.ticket_repo.get_ticket(ticket.id)
        self.assertEqual(closed_ticket.status, "closed")
        self.assertIsNotNone(closed_ticket.closed_at)

    async def test_reaction_roles_and_verification(self) -> None:
        """Test reaction roles configuration and verification system."""
        # 1. Reaction Roles
        await self.rr_service.create_setup(
            message_id=444,
            guild_id=111,
            channel_id=222,
            title="Choose Roles",
            description="Click buttons below.",
            group_name="PingGroup",
            type_="button"
        )

        await self.rr_service.add_role_mapping(111, 444, "📢", 555, "Announcements")
        mappings = await self.rr_service.get_reaction_roles(444)
        self.assertEqual(len(mappings), 1)
        self.assertEqual(mappings[0].emoji, "📢")
        self.assertEqual(mappings[0].role_id, 555)

        # 2. Verification setup
        await self.verify_service.save_settings(
            guild_id=111,
            role_id=888,
            channel_id=222,
            enabled=True
        )

        v_settings = await self.verify_service.get_settings(111)
        self.assertIsNotNone(v_settings)
        self.assertEqual(v_settings.role_id, 888)
        self.assertEqual(v_settings.enabled, True)

    async def test_scheduled_announcements(self) -> None:
        """Test immediate and scheduled announcements mapping."""
        # Setup mock channel sends
        self.bot_mock.get_guild = MagicMock()
        guild_mock = MagicMock()
        self.bot_mock.get_guild.return_value = guild_mock
        channel_mock = AsyncMock(spec=discord.TextChannel)
        guild_mock.get_channel.return_value = channel_mock

        # Create scheduled announcement
        future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)
        ann = await self.announce_service.create_announcement(
            guild_id=111,
            channel_id=222,
            message_text="Hello world scheduled",
            embed_json=None,
            scheduled_at=future_time
        )

        self.assertIsNotNone(ann)
        self.assertEqual(ann.status, "pending")
        self.assertEqual(ann.message_text, "Hello world scheduled")

        # Create immediate announcement
        immediate = await self.announce_service.create_announcement(
            guild_id=111,
            channel_id=222,
            message_text="Hello world immediate",
            embed_json=None,
            scheduled_at=None
        )
        self.assertEqual(immediate.status, "sent")
        channel_mock.send.assert_called_once_with(content="Hello world immediate", embed=None, view=None)
