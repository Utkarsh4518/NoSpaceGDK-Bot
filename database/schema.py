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
    }
}
