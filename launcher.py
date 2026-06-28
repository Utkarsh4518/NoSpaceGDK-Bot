"""Application launcher for the NoSpaceFGK Discord Bot.

Verifies the system environment, loads validated configurations,
initializes professional logging, and boots the custom bot instance.
"""

import asyncio
import sys
import discord
from config import load_config, BotConfig
from bot import NoSpaceFGKBot
from utils.constants import BOT_VERSION
from utils.exceptions import ConfigurationError
from utils.logger import setup_logging, log_startup, log_exception, logger


def verify_python_version() -> None:
    """Ensure the executing Python environment is version 3.12 or higher.

    Raises:
        RuntimeError: If the Python version is unsupported.
    """
    required = (3, 12)
    current = sys.version_info
    if current < required:
        error_msg = (
            f"Unsupported Python version {current.major}.{current.minor}. "
            f"NoSpaceFGK requires Python {required[0]}.{required[1]} or higher.\n"
        )
        sys.stderr.write(error_msg)
        sys.exit(1)


async def start_application(config: BotConfig) -> None:
    """Initialize and start the custom bot client.

    Args:
        config: The validated read-only configuration instance.
    """
    bot = NoSpaceFGKBot(config=config)

    try:
        async with bot:
            logger.info("Connecting to Discord gateway...")
            await bot.start(config.discord_token)
    except discord.LoginFailure as e:
        log_exception(e, "Discord gateway authentication failed:")
        sys.exit(1)
    except Exception as e:
        log_exception(e, "Fatal exception caught in application event loop:")
        sys.exit(1)


def main() -> None:
    """Main execution entry point.

    Performs environment validation, loads config, boots loggers, and runs the bot loop.
    """
    # 1. Verify Python Version (>= 3.12)
    verify_python_version()

    # 2. Load Configuration
    try:
        config = load_config()
    except ConfigurationError as e:
        # Fallback stderr printer as logger isn't configured yet
        sys.stderr.write(f"CRITICAL: Failed to load configuration: {e}\n")
        sys.exit(1)

    # 3. Setup Professional Logging
    try:
        setup_logging(level=config.log_level)
        log_startup(version=BOT_VERSION)
    except Exception as e:
        sys.stderr.write(f"CRITICAL: Failed to initialize logging: {e}\n")
        sys.exit(1)

    # 4. Launch Bot inside the event loop
    try:
        asyncio.run(start_application(config))
    except KeyboardInterrupt:
        logger.info("Bot execution interrupted by user (KeyboardInterrupt). Exiting gracefully.")
    except Exception as e:
        log_exception(e, "Fatal application startup error:")
        sys.exit(1)


if __name__ == "__main__":
    main()
