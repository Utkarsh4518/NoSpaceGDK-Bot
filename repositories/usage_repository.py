"""Usage and Audit logging repository managing audit records for NoSpaceFGK."""

import datetime
from typing import Optional
from models.domain import CommandUsage, AuditLog
from repositories.base_repository import BaseRepository
from utils.logger import logger


class UsageRepository(BaseRepository):
    """Handles persistence of CommandUsage and AuditLog models."""

    async def log_command_usage(
        self,
        user_id: int,
        guild_id: Optional[int],
        command_name: str,
        execution_time: float,
        status: str
    ) -> CommandUsage:
        """Create a command execution log.

        Args:
            user_id: User who ran the command.
            guild_id: Guild ID context.
            command_name: Name of command.
            execution_time: Latency in float seconds.
            status: SUCCESS or FAILED.

        Returns:
            The created CommandUsage domain model.
        """
        query = """
            INSERT INTO command_usages (user_id, guild_id, command_name, execution_time, status)
            VALUES (?, ?, ?, ?, ?);
        """
        cursor = await self.db.execute(
            query,
            (user_id, guild_id, command_name, execution_time, status)
        )
        await self.db.commit()

        insert_id = cursor.lastrowid
        logger.info(f"Repository operation: Logged command usage '{command_name}' by user {user_id} in {execution_time:.4f}s.")
        return CommandUsage(
            id=insert_id,
            user_id=user_id,
            guild_id=guild_id,
            command_name=command_name,
            execution_time=execution_time,
            status=status,
            executed_at=datetime.datetime.now(datetime.timezone.utc)
        )

    async def log_audit(self, action: str, user_id: int, details: Optional[str] = None) -> AuditLog:
        """Create a system audit log.

        Args:
            action: Action tag.
            user_id: Performing user ID.
            details: Extra metadata.

        Returns:
            The created AuditLog domain model.
        """
        query = """
            INSERT INTO audit_logs (action, user_id, details)
            VALUES (?, ?, ?);
        """
        cursor = await self.db.execute(query, (action, user_id, details))
        await self.db.commit()

        insert_id = cursor.lastrowid
        logger.info(f"Repository operation: Logged audit action '{action}' by user {user_id}.")
        return AuditLog(
            id=insert_id,
            action=action,
            user_id=user_id,
            details=details,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
