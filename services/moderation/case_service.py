"""Case Service for managing cases and incrementing stats."""

from typing import List, Optional
import discord
from models.case import CaseModel
from repositories.case_repository import CaseRepository
from repositories.moderation_stats_repository import ModerationStatsRepository
from services.moderation.audit_service import AuditService
from services.base_service import BaseService

class CaseService(BaseService):
    """Coordinates case creation, resolution, and statistics updating."""

    def __init__(
        self,
        case_repo: CaseRepository,
        stats_repo: ModerationStatsRepository,
        audit_service: AuditService
    ) -> None:
        self.cases = case_repo
        self.stats = stats_repo
        self.audit = audit_service

    async def create_case(
        self,
        guild_id: int,
        case_type: str,
        user: discord.Member | discord.User,
        moderator: discord.Member | discord.User,
        reason: Optional[str],
        duration_seconds: Optional[int] = None,
        channel_id: Optional[int] = None
    ) -> CaseModel:
        # 1. Save case to DB
        case = await self.cases.create(
            guild_id=guild_id,
            case_type=case_type,
            user_id=user.id,
            moderator_id=moderator.id,
            reason=reason,
            duration_seconds=duration_seconds,
            channel_id=channel_id
        )
        
        # 2. Increment stats
        stat_map = {
            "warn": "total_warns",
            "kick": "total_kicks",
            "ban": "total_bans",
            "timeout": "total_timeouts",
            "automod": "total_automod_triggers"
        }
        stat_col = stat_map.get(case_type)
        if stat_col:
            await self.stats.increment_stat(guild_id, stat_col)
            
        # 3. Log to audit channel
        extra_details = {"case_id": case.id}
        if duration_seconds:
            extra_details["duration"] = f"{duration_seconds} seconds"
        await self.audit.log_action(
            guild_id=guild_id,
            action_type=case_type,
            moderator=moderator,
            target=user,
            reason=reason,
            extra_details=extra_details
        )
        
        return case

    async def get_case(self, case_id: int) -> Optional[CaseModel]:
        return await self.cases.get_by_id(case_id)

    async def search_cases(
        self,
        guild_id: int,
        user_id: Optional[int] = None,
        moderator_id: Optional[int] = None,
        case_type: Optional[str] = None
    ) -> List[CaseModel]:
        return await self.cases.search(
            guild_id=guild_id,
            user_id=user_id,
            moderator_id=moderator_id,
            case_type=case_type
        )
