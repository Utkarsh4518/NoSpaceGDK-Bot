"""Reusable autocomplete utilities for NoSpaceFGK.

Contains helper functions to handle search filtering and Choice conversions
for Discord slash command autocomplete prompts.
"""

from typing import Union, List, Tuple
from discord.app_commands import Choice


def filter_choices(
    choices: Union[List[str], List[Tuple[str, Union[str, int]]]],
    current: str
) -> List[Choice[Union[str, int]]]:
    """Filter choices based on a search term, limiting results to 25.

    Matches in a case-insensitive manner. Supports choices formatted as either
    plain strings or tuples of (name, value).

    Args:
        choices: The full list of static choices available.
        current: The user's typed search query.

    Returns:
        A list of discord.app_commands.Choice instances matching the query (max 25).
    """
    results: List[Choice[Union[str, int]]] = []
    query = current.lower()

    for item in choices:
        if isinstance(item, tuple):
            name, value = item
        else:
            name, value = item, item

        if query in name.lower():
            results.append(Choice(name=name, value=value))

        if len(results) >= 25:
            break

    return results
