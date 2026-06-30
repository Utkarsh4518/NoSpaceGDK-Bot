"""Database Schema definitions and migrations query maps for NoSpaceFGK.

Contains SQL scripts for applying (UP) and rolling back (DOWN) sequential schema versions.
"""

from typing import Dict, TypedDict


class MigrationScript(TypedDict):
    """Container for upgrade and downgrade schema migration steps."""
    up: str
    down: str


# Schema Migrations Dictionary (Sequential Keys)
MIGRATIONS: Dict[int, MigrationScript] = {
    1: {
        "up": """
            CREATE TABLE IF NOT EXISTS guilds (
                id INTEGER PRIMARY KEY,
                prefix TEXT NOT NULL DEFAULT '!',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                is_premium INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "down": """
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS guilds;
        """
    },
    2: {
        "up": """
            CREATE TABLE IF NOT EXISTS bot_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS command_usages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER,
                command_name TEXT NOT NULL,
                execution_time REAL NOT NULL,
                status TEXT NOT NULL,
                executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                details TEXT,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "down": """
            DROP TABLE IF EXISTS audit_logs;
            DROP TABLE IF EXISTS command_usages;
            DROP TABLE IF EXISTS bot_settings;
        """
    },
    3: {
        "up": """
            CREATE TABLE IF NOT EXISTS music_tracks (
                uuid TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                artist TEXT NOT NULL,
                duration REAL NOT NULL,
                thumbnail TEXT,
                provider TEXT NOT NULL,
                url TEXT NOT NULL,
                requested_by INTEGER NOT NULL,
                isrc TEXT,
                metadata TEXT,
                added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS playlists (
                uuid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_id INTEGER NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_uuid TEXT NOT NULL,
                track_uuid TEXT NOT NULL,
                position INTEGER NOT NULL,
                PRIMARY KEY (playlist_uuid, track_uuid),
                FOREIGN KEY (playlist_uuid) REFERENCES playlists (uuid) ON DELETE CASCADE,
                FOREIGN KEY (track_uuid) REFERENCES music_tracks (uuid) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS playback_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                track_uuid TEXT NOT NULL,
                played_by INTEGER NOT NULL,
                played_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (track_uuid) REFERENCES music_tracks (uuid) ON DELETE CASCADE
            );
        """,
        "down": """
            DROP TABLE IF EXISTS playback_history;
            DROP TABLE IF EXISTS playlist_tracks;
            DROP TABLE IF EXISTS playlists;
            DROP TABLE IF EXISTS music_tracks;
        """
    },
    4: {
        "up": """
            CREATE TABLE IF NOT EXISTS spotify_match_cache (
                spotify_id TEXT PRIMARY KEY,
                youtube_url TEXT NOT NULL,
                track_title TEXT NOT NULL,
                artist TEXT NOT NULL,
                confidence REAL NOT NULL,
                resolved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS spotify_imports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spotify_url TEXT NOT NULL,
                spotify_type TEXT NOT NULL,
                track_count INTEGER NOT NULL DEFAULT 0,
                imported_by INTEGER NOT NULL,
                guild_id INTEGER NOT NULL,
                imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "down": """
            DROP TABLE IF EXISTS spotify_imports;
            DROP TABLE IF EXISTS spotify_match_cache;
        """
    },
    5: {
        "up": """
            CREATE TABLE IF NOT EXISTS ai_conversations (
                id TEXT PRIMARY KEY,
                target_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                active_model TEXT NOT NULL,
                active_provider TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ai_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL DEFAULT 0,
                completion_tokens INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES ai_conversations (id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ai_prompts (
                id TEXT PRIMARY KEY,
                target_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS ai_token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                total_tokens INTEGER NOT NULL,
                estimated_cost REAL NOT NULL,
                used_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "down": """
            DROP TABLE IF EXISTS ai_token_usage;
            DROP TABLE IF EXISTS ai_prompts;
            DROP TABLE IF EXISTS ai_messages;
            DROP TABLE IF EXISTS ai_conversations;
        """
    },
    6: {
        "up": """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                points INTEGER DEFAULT 1,
                is_expired INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                case_type TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                duration_seconds INTEGER,
                status TEXT NOT NULL DEFAULT 'active',
                channel_id INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS timeouts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                duration_seconds INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS bans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS kicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                moderator_id INTEGER NOT NULL,
                original_overwrites TEXT,
                is_active INTEGER DEFAULT 1,
                expires_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS automod_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                rule_type TEXT NOT NULL,
                config TEXT NOT NULL,
                is_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS moderation_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                moderator_id INTEGER NOT NULL,
                target_id INTEGER,
                details TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS moderation_statistics (
                guild_id INTEGER PRIMARY KEY,
                total_warns INTEGER DEFAULT 0,
                total_kicks INTEGER DEFAULT 0,
                total_bans INTEGER DEFAULT 0,
                total_timeouts INTEGER DEFAULT 0,
                total_automod_triggers INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                default_timeout_seconds INTEGER DEFAULT 3600,
                default_warning_limit INTEGER DEFAULT 3,
                audit_channel_id INTEGER,
                moderator_roles TEXT,
                protected_roles TEXT,
                ignored_channels TEXT,
                ignored_roles TEXT
            );
        """,
        "down": """
            DROP TABLE IF EXISTS guild_settings;
            DROP TABLE IF EXISTS moderation_statistics;
            DROP TABLE IF EXISTS moderation_audit_logs;
            DROP TABLE IF EXISTS automod_rules;
            DROP TABLE IF EXISTS locks;
            DROP TABLE IF EXISTS kicks;
            DROP TABLE IF EXISTS bans;
            DROP TABLE IF EXISTS timeouts;
            DROP TABLE IF EXISTS cases;
            DROP TABLE IF EXISTS warnings;
        """
    },
    7: {
        "up": """
            CREATE TABLE IF NOT EXISTS memes_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                title TEXT,
                url TEXT NOT NULL,
                post_link TEXT,
                subreddit TEXT,
                nsfw INTEGER DEFAULT 0,
                cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS jokes_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                setup TEXT NOT NULL,
                delivery TEXT,
                cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS quotes_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT,
                cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS facts_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                cached_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                players TEXT NOT NULL,
                status TEXT NOT NULL,
                winner_id INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS game_statistics (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                game_type TEXT NOT NULL,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                ties INTEGER DEFAULT 0,
                longest_win_streak INTEGER DEFAULT 0,
                current_win_streak INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, game_type)
            );

            CREATE TABLE IF NOT EXISTS leaderboards (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                metric TEXT NOT NULL,
                value INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id, metric)
            );

            CREATE TABLE IF NOT EXISTS fun_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER NOT NULL,
                command_name TEXT NOT NULL,
                executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "down": """
            DROP TABLE IF EXISTS fun_usage;
            DROP TABLE IF EXISTS leaderboards;
            DROP TABLE IF EXISTS game_statistics;
            DROP TABLE IF EXISTS games;
            DROP TABLE IF EXISTS facts_cache;
            DROP TABLE IF EXISTS quotes_cache;
            DROP TABLE IF EXISTS jokes_cache;
            DROP TABLE IF EXISTS memes_cache;
        """
    },
    8: {
        "up": """
            ALTER TABLE ai_messages ADD COLUMN tool_calls TEXT;
            ALTER TABLE ai_messages ADD COLUMN tool_call_id TEXT;
            ALTER TABLE ai_messages ADD COLUMN name TEXT;
            ALTER TABLE ai_messages ADD COLUMN provider TEXT;
            ALTER TABLE ai_messages ADD COLUMN model TEXT;
            ALTER TABLE ai_messages ADD COLUMN latency REAL;
            ALTER TABLE ai_messages ADD COLUMN reasoning_metadata TEXT;
            
            ALTER TABLE ai_conversations ADD COLUMN state TEXT;
        """,
        "down": """
            SELECT 1;
        """
    },
    9: {
        "up": """
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
        """,
        "down": """
            DROP TABLE IF EXISTS verification_settings;
            DROP TABLE IF EXISTS announcements;
            DROP TABLE IF EXISTS autoroles;
            DROP TABLE IF EXISTS goodbye_settings;
            DROP TABLE IF EXISTS welcome_settings;
            DROP TABLE IF EXISTS reaction_role_messages;
            DROP TABLE IF EXISTS reaction_roles;
            DROP TABLE IF EXISTS ticket_participants;
            DROP TABLE IF EXISTS ticket_messages;
            DROP TABLE IF EXISTS tickets;
        """
    }
}

