"""Autorole Service for automatically assigning roles to new members."""

from typing import List
import discord
from repository.welcome_repository import WelcomeRepository
from services.base_service import BaseService
from services.cache_service import CacheService
from utils.logger import logger

class AutoroleService(BaseService):
    """Manages role assignments for new members joining the server."""

    def __init__(self, welcome_repo: WelcomeRepository, cache_service: CacheService) -> None:
        self.repo = welcome_repo
        self.cache = cache_service

    async def get_autoroles(self, guild_id: int) -> List[int]:
        """Fetch autorole IDs with cache layer."""
        cache_key = f"autoroles:{guild_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        roles = await self.repo.get_autoroles(guild_id)
        self.cache.set(cache_key, roles)
        return roles

    async def add_autorole(self, guild_id: int, role_id: int) -> None:
        """Add a role to the autorole list and clear cache."""
        await self.repo.add_autorole(guild_id, role_id)
        self.cache.delete(f"autoroles:{guild_id}")

    async def remove_autorole(self, guild_id: int, role_id: int) -> None:
        """Remove a role from the autorole list and clear cache."""
        await self.repo.remove_autorole(guild_id, role_id)
        self.cache.delete(f"autoroles:{guild_id}")

    async def assign_autoroles(self, member: discord.Member) -> None:
        """Assign all configured autoroles to the joining member."""
        role_ids = await self.get_autoroles(member.guild.id)
        if not role_ids:
            return

        guild = member.guild
        me = guild.me
        bot_top_role = me.top_role

        roles_to_add = []
        for rid in role_ids:
            role = guild.get_role(rid)
            if not role:
                logger.warning(f"AutoroleService: Role {rid} not found in guild {guild.id}")
                continue

            # Validate hierarchy: bot role must be higher than target role
            if role >= bot_top_role:
                logger.warning(
                    f"AutoroleService: Cannot assign role {role.name} ({rid}) "
                    f"because it is higher than or equal to bot's highest role ({bot_top_role.name})."
                )
                continue

            roles_to_add.append(role)

        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="NoSpaceFGK Autorole System")
                logger.info(f"AutoroleService: Successfully assigned roles to {member.name} ({member.id})")
            except discord.Forbidden:
                logger.error(f"AutoroleService: Missing permission to assign roles to {member.name} ({member.id})")
            except Exception as e:
                logger.error(f"AutoroleService: Failed to assign roles: {e}")
