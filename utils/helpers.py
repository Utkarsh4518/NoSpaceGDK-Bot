"""Helper utilities for the NoSpaceFGK bot.

This module houses general-purpose convenience functions to reduce code duplication
and simplify common operations.
"""

import datetime
from typing import Any
import discord


def is_integer(value: Any) -> bool:
    """Check if a given value can be parsed as an integer.

    Args:
        value: The value to inspect.

    Returns:
        True if the value is an integer or string representation of an integer, False otherwise.
    """
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


def parse_csv_to_integers(csv_str: str) -> list[int]:
    """Parse a comma-separated string into a list of integers.

    Strips any whitespace surrounding each element. Invalid values are ignored.

    Args:
        csv_str: A comma-separated string of values.

    Returns:
        A list of successfully parsed integers.
    """
    if not csv_str.strip():
        return []

    parsed = []
    for item in csv_str.split(","):
        clean_item = item.strip()
        if is_integer(clean_item):
            parsed.append(int(clean_item))
    return parsed


def format_duration(seconds: float) -> str:
    """Format a duration in seconds into a human-readable string.

    Args:
        seconds: The duration in seconds.

    Returns:
        A human-readable string (e.g. '2h 15m 30s' or '45s').
    """
    total_seconds = int(round(seconds))
    if total_seconds < 0:
        return "0s"

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds_int = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds_int > 0 or not parts:
        parts.append(f"{seconds_int}s")

    return " ".join(parts)


def format_timestamp(dt: datetime.datetime, style: str = "f") -> str:
    """Generate a Discord formatted timestamp.

    Args:
        dt: The datetime object.
        style: The Discord timestamp format style identifier.

    Returns:
        The Discord markdown timestamp string (e.g. '<t:1609459200:R>').
    """
    timestamp = int(dt.timestamp())
    return f"<t:{timestamp}:{style}>"


def format_file_size(bytes_count: int) -> str:
    """Format bytes count into a human-readable file size string.

    Args:
        bytes_count: The size in bytes.

    Returns:
        A string formatted (e.g. '1.50 MB' or '340 B').
    """
    if bytes_count < 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(bytes_count)
    unit_idx = 0
    while size >= 1024.0 and unit_idx < len(units) - 1:
        size /= 1024.0
        unit_idx += 1

    if unit_idx == 0:
        return f"{int(size)} B"
    return f"{size:.2f} {units[unit_idx]}"


def escape_markdown(text: str) -> str:
    """Escape standard markdown characters in a text string.

    Args:
        text: The raw text string.

    Returns:
        The escaped text safe from markdown rendering.
    """
    return discord.utils.escape_markdown(text)


def snowflake_to_datetime(snowflake: int) -> datetime.datetime:
    """Convert a Discord Snowflake ID into a datetime object.

    Args:
        snowflake: The Discord Snowflake ID.

    Returns:
        A timezone-aware datetime object representing the Snowflake's creation time.
    """
    return discord.utils.snowflake_time(snowflake)
