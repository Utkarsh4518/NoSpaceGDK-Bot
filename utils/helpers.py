"""Helper utilities for the NoSpaceFGK bot.

This module houses general-purpose convenience functions to reduce code duplication
and simplify common operations.
"""

from typing import Any


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
