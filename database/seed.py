"""Database seeder to load test data for NoSpaceFGK.

Populates default global settings, development guild mappings, and sample users
if the database tables are empty.
"""

from database.connection import DatabaseManager
from utils.logger import logger


async def seed_database(db: DatabaseManager, dev_guild_id: int | None) -> None:
    """Insert default entries if respective tables are empty.

    Args:
        db: The DatabaseManager instance.
        dev_guild_id: The development guild ID configured in .env, or None.
    """
    # 1. Seed Bot Settings
    async with db.connection.execute("SELECT COUNT(*) FROM bot_settings;") as cursor:
        row = await cursor.fetchone()
        if row and row[0] == 0:
            logger.info("Seeding default bot settings...")
            settings = [
                ("maintenance_mode", "false"),
                ("premium_role_id", "0"),
                ("max_cache_size", "1000")
            ]
            await db.connection.executemany(
                "INSERT INTO bot_settings (key, value) VALUES (?, ?);",
                settings
            )
            await db.commit()

    # 2. Seed Guild
    async with db.connection.execute("SELECT COUNT(*) FROM guilds;") as cursor:
        row = await cursor.fetchone()
        if row and row[0] == 0 and dev_guild_id:
            logger.info(f"Seeding development guild ID: {dev_guild_id}...")
            await db.connection.execute(
                "INSERT INTO guilds (id, prefix) VALUES (?, ?);",
                (dev_guild_id, "!")
            )
            await db.commit()

    # 3. Seed Users
    async with db.connection.execute("SELECT COUNT(*) FROM users;") as cursor:
        row = await cursor.fetchone()
        if row and row[0] == 0:
            logger.info("Seeding sample users...")
            users = [
                (123456789012345678, "ExampleOwner", 1),
                (987654321098765432, "RegularUser", 0)
            ]
            await db.connection.executemany(
                "INSERT INTO users (id, username, is_premium) VALUES (?, ?, ?);",
                users
            )
            await db.commit()

    logger.info("Database seeding verification completed.")
