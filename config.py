"""Configuration loader and validator for the NoSpaceFGK bot.

Loads environment variables from `.env`, validates required fields,
coerces types, and provides clean default fallback values.
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from utils.exceptions import ConfigurationError
from utils.helpers import parse_csv_to_integers, is_integer


@dataclass(frozen=True)
class BotConfig:
    """Read-only container for validated bot configuration.

    This ensures that configuration is immutable and typed correctly.
    """
    discord_token: str
    client_id: int
    bot_prefix: str
    log_level: str
    owner_ids: list[int]
    development_guild_id: int | None


def load_config() -> BotConfig:
    """Load configuration from environment variables and validate them.

    Loads the `.env` file first, then reads and checks each config field.

    Returns:
        A validated, read-only BotConfig instance.

    Raises:
        ConfigurationError: If any required parameters are missing or invalid.
    """
    # Load .env file
    load_dotenv()

    # 1. Validate DISCORD_TOKEN
    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token:
        raise ConfigurationError("Required environment variable 'DISCORD_TOKEN' is missing.")

    # 2. Validate CLIENT_ID
    client_id_raw = os.getenv("CLIENT_ID")
    if not client_id_raw:
        raise ConfigurationError("Required environment variable 'CLIENT_ID' is missing.")
    if not is_integer(client_id_raw):
        raise ConfigurationError(f"Environment variable 'CLIENT_ID' must be an integer, got: '{client_id_raw}'")
    client_id = int(client_id_raw)

    # 3. Handle BOT_PREFIX (Default: '!')
    bot_prefix = os.getenv("BOT_PREFIX", "!")

    # 4. Handle LOG_LEVEL (Default: 'INFO')
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        log_level = "INFO"

    # 5. Handle OWNER_IDS (Required, CSV of integers)
    owner_ids_raw = os.getenv("OWNER_IDS")
    if not owner_ids_raw:
        raise ConfigurationError("Required environment variable 'OWNER_IDS' is missing or empty.")
    owner_ids = parse_csv_to_integers(owner_ids_raw)
    if not owner_ids:
        raise ConfigurationError(
            f"Environment variable 'OWNER_IDS' must be a comma-separated list of integer IDs, got: '{owner_ids_raw}'"
        )

    # 6. Handle DEVELOPMENT_GUILD_ID (Optional, integer)
    dev_guild_raw = os.getenv("DEVELOPMENT_GUILD_ID")
    development_guild_id: int | None = None
    if dev_guild_raw:
        if not is_integer(dev_guild_raw):
            raise ConfigurationError(
                f"Environment variable 'DEVELOPMENT_GUILD_ID' must be an integer, got: '{dev_guild_raw}'"
            )
        development_guild_id = int(dev_guild_raw)

    return BotConfig(
        discord_token=discord_token,
        client_id=client_id,
        bot_prefix=bot_prefix,
        log_level=log_level,
        owner_ids=owner_ids,
        development_guild_id=development_guild_id
    )
