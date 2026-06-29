"""Domain models for NoSpaceFGK bot.

Defines pure domain entities using dataclasses to represent data structures
free from direct infrastructure dependencies.
"""

import datetime
from dataclasses import dataclass


@dataclass
class User:
    """Domain representation of a Discord User."""
    id: int
    username: str | None
    is_premium: bool
    created_at: datetime.datetime


@dataclass
class Guild:
    """Domain representation of a Discord Guild (Server)."""
    id: int
    prefix: str
    created_at: datetime.datetime


@dataclass
class BotSettings:
    """Domain representation of a global bot setting (key-value)."""
    key: str
    value: str
    updated_at: datetime.datetime


@dataclass
class CommandUsage:
    """Domain representation of a slash command execution audit record."""
    id: int | None
    user_id: int
    guild_id: int | None
    command_name: str
    execution_time: float
    status: str
    executed_at: datetime.datetime


@dataclass
class AuditLog:
    """Domain representation of a system audit log record."""
    id: int | None
    action: str
    user_id: int
    details: str | None
    timestamp: datetime.datetime
