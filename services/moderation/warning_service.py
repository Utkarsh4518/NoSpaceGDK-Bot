"""Warning Service for managing warning actions and escalations."""

import datetime
from typing import List, Optional
import discord
from models.warning import WarningModel
from repositories.warning_repository import WarningRepository
from repositories.guild_settings_repository import GuildSettingsRepository
from services.moderation.case_service import CaseService
from services.base_service import BaseService

class WarningService(BaseService):
    """Manages warnings and executes automated escalations."""

    def __init__(
        self,
        warning_repo: WarningRepository,
        settings_repo: GuildSettingsRepository,
        case_service: CaseService
    ) -> None:
        self.warnings = warning_repo
        self.settings = settings_repo
        self.cases = case_service

    async def warn_user(
        self,
        guild_id: int,
        user: discord.Member,
        moderator: discord.Member | discord.User,
        reason: Optional[str],
        points: int = 1
    ) -> WarningModel:
        # 1. Create warning record in DB
        warning = await self.warnings.create(
            guild_id=guild_id,
            user_id=user.id,
            moderator_id=moderator.id,
            reason=reason,
            points=points
        )
        
        # 2. Log Case
        await self.cases.create_case(
            guild_id=guild_id,
            case_type="warn",
            user=user,
            moderator=moderator,
            reason=reason
        )
        
        # 3. Check and apply escalation
        await self._check_escalation(guild_id, user, moderator)
        
        return warning

    async def get_warnings(self, guild_id: int, user_id: int, active_only: bool = True) -> List[WarningModel]:
        if active_only:
            return await self.warnings.get_active_by_user(guild_id, user_id)
        return await self.warnings.get_all_by_user(guild_id, user_id)

    async def clear_warnings(self, guild_id: int, user_id: int) -> int:
        return await self.warnings.clear_active(guild_id, user_id)

    async def _check_escalation(self, guild_id: int, user: discord.Member, moderator: discord.Member | discord.User) -> None:
        """Evaluate warning count and trigger automatic escalation punishments."""
        active_warnings = await self.get_warnings(guild_id, user.id, active_only=True)
        total_points = sum(w.points for w in active_warnings)
        
        settings = await self.settings.get_settings(guild_id)
        limit = settings.default_warning_limit
        
        # Automatic escalations based on threshold limits:
        # Tier 1 (limit points): Native Discord Timeout for 1 hour.
        # Tier 2 (limit + 2 points): Guild Kick.
        # Tier 3 (limit + 4 points): Guild Ban.
        if total_points >= limit + 4:
            # Escalation Ban
            reason = f"Automated Escalation: User exceeded warning limit + 4 ({total_points}/{limit} warning points)."
            try:
                await user.ban(reason=reason)
                await self.cases.create_case(guild_id, "ban", user, moderator, reason)
            except discord.Forbidden:
                pass
        elif total_points >= limit + 2:
            # Escalation Kick
            reason = f"Automated Escalation: User exceeded warning limit + 2 ({total_points}/{limit} warning points)."
            try:
                await user.kick(reason=reason)
                await self.cases.create_case(guild_id, "kick", user, moderator, reason)
            except discord.Forbidden:
                pass
        elif total_points >= limit:
            # Escalation Timeout (1 Hour)
            reason = f"Automated Escalation: User reached warning limit ({total_points}/{limit} warning points)."
            duration = datetime.timedelta(hours=1)
            try:
                await user.timeout(duration, reason=reason)
                await self.cases.create_case(guild_id, "timeout", user, moderator, reason, duration_seconds=3600)
            except discord.Forbidden:
                pass
