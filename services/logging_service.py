"""Logging and audit trails service interfacing user metrics tracking repositories."""

from typing import Optional
from repositories.usage_repository import UsageRepository
from services.base_service import BaseService


class LoggingService(BaseService):
    """Bridges runtime events to database persistent logs repository."""

    def __init__(self, usage_repo: UsageRepository) -> None:
        """Initialize the logging service.

        Args:
            usage_repo: Custom UsageRepository instance.
        """
        self._repo: UsageRepository = usage_repo

    async def log_command(
        self,
        user_id: int,
        guild_id: Optional[int],
        command_name: str,
        execution_time: float,
        status: str
    ) -> None:
        """Write command execution records to persistent logs.

        Args:
            user_id: Discord ID of user running the command.
            guild_id: Guild context.
            command_name: Command path tag.
            execution_time: Round-trip delay in seconds.
            status: Command result status (SUCCESS / FAILED).
        """
        await self._repo.log_command_usage(
            user_id=user_id,
            guild_id=guild_id,
            command_name=command_name,
            execution_time=execution_time,
            status=status
        )

    async def log_audit(self, action: str, user_id: int, details: Optional[str] = None) -> None:
        """Write system audit records.

        Args:
            action: Descriptive action string.
            user_id: Originating Discord user.
            details: Extra parameters of event context.
        """
        await self._repo.log_audit(
            action=action,
            user_id=user_id,
            details=details
        )
