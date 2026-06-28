"""Professional logging configuration for the NoSpaceFGK bot.

Configures dual-channel output to console (via Rich for clean styling)
and daily rotating file handlers (regular log and a separate error log).
"""

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any
from rich.logging import RichHandler
from utils.constants import LOGS_DIR

# Base log format for files
FILE_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Configure dual-channel logging for the application.

    Creates logs/ directory if it doesn't exist. Registers a console
    handler using Rich and daily-rotating file handlers for general
    activity and errors.

    Args:
        level: The logging level to configure (e.g., DEBUG, INFO, WARNING, ERROR).
    """
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Root Logger Config
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. Console Logging (Rich Handler)
    console_handler = RichHandler(
        rich_tracebacks=True,
        omit_repeated_times=False,
        show_path=False
    )
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter("%(name)s | %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 2. Main File Logging (Daily Rotating)
    main_log_path = LOGS_DIR / "bot.log"
    main_file_handler = TimedRotatingFileHandler(
        filename=main_log_path,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    main_file_handler.setLevel(numeric_level)
    main_file_formatter = logging.Formatter(FILE_FORMAT)
    main_file_handler.setFormatter(main_file_formatter)
    root_logger.addHandler(main_file_handler)

    # 3. Error File Logging (Daily Rotating, only ERROR and CRITICAL)
    error_log_path = LOGS_DIR / "error.log"
    error_file_handler = TimedRotatingFileHandler(
        filename=error_log_path,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_formatter = logging.Formatter(FILE_FORMAT)
    error_file_handler.setFormatter(error_file_formatter)
    root_logger.addHandler(error_file_handler)


# Specific Application Logger
logger = logging.getLogger("NoSpaceFGK")


def log_startup(version: str) -> None:
    """Log bot initialization and startup event details.

    Args:
        version: The current version of the bot.
    """
    logger.info(f"=== Starting NoSpaceFGK (v{version}) ===")


def log_shutdown() -> None:
    """Log bot shutdown events."""
    logger.info("=== NoSpaceFGK Shutdown Gracefully ===")


def log_exception(error: Exception, message: str = "An unexpected exception occurred:") -> None:
    """Log details of a caught exception.

    Args:
        error: The caught exception instance.
        message: Contextual information about where the error was caught.
    """
    logger.error(f"{message} {error}", exc_info=error)


def log_command(user_id: int, guild_id: int | None, command_name: str, args: Any) -> None:
    """Placeholder logging function for tracking bot commands.

    Args:
        user_id: ID of the executing user.
        guild_id: ID of the guild where the command was run, or None if in DM.
        command_name: The name of the command.
        args: Arguments supplied to the command.
    """
    guild_str = f"Guild: {guild_id}" if guild_id else "DMs"
    logger.info(f"[COMMAND] User: {user_id} | {guild_str} | Command: {command_name} | Args: {args}")
