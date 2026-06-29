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
    }
}
