"""Reaction Role Service for handling button, select menu, and emoji reaction roles."""

from typing import List, Optional, Any
import discord
from models.reaction_role import ReactionRoleModel, ReactionRoleMessageModel
from repository.reaction_role_repository import ReactionRoleRepository
from services.base_service import BaseService
from services.cache_service import CacheService
from utils.logger import logger

class ReactionRoleService(BaseService):
    """Manages role assignment based on button clicks, select menus, and traditional reactions."""

    def __init__(self, bot: Any, rr_repo: ReactionRoleRepository, cache_service: CacheService) -> None:
        self.bot = bot
        self.repo = rr_repo
        self.cache = cache_service

    async def get_reaction_roles(self, message_id: int) -> List[ReactionRoleModel]:
        """Fetch role mappings for a message (with cache)."""
        cache_key = f"rr_mappings:{message_id}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        mappings = await self.repo.get_reaction_roles(message_id)
        self.cache.set(cache_key, mappings)
        return mappings

    async def create_setup(
        self,
        message_id: int,
        guild_id: int,
        channel_id: int,
        title: Optional[str],
        description: Optional[str],
        group_name: str,
        type_: str
    ) -> ReactionRoleMessageModel:
        """Register reaction role message setup."""
        setup = await self.repo.create_reaction_role_message(
            message_id=message_id,
            guild_id=guild_id,
            channel_id=channel_id,
            title=title,
            description=description,
            group_name=group_name,
            type_=type_
        )
        self.cache.delete(f"rr_message:{message_id}")
        return setup

    async def add_role_mapping(self, guild_id: int, message_id: int, emoji_or_id: str, role_id: int, group_name: str) -> ReactionRoleModel:
        """Add individual role mapping and invalidate caches."""
        mapping = await self.repo.add_reaction_role(guild_id, message_id, emoji_or_id, role_id, group_name)
        self.cache.delete(f"rr_mappings:{message_id}")
        return mapping

    async def remove_role_mapping(self, message_id: int, role_id: int) -> None:
        """Remove a role mapping and invalidate caches."""
        await self.repo.remove_reaction_role(message_id, role_id)
        self.cache.delete(f"rr_mappings:{message_id}")

    async def delete_setup(self, message_id: int) -> None:
        """Delete reaction role message configuration and invalidate caches."""
        await self.repo.delete_reaction_role_message(message_id)
        self.cache.delete(f"rr_message:{message_id}")
        self.cache.delete(f"rr_mappings:{message_id}")

    async def toggle_role(self, member: discord.Member, role_id: int) -> str:
        """Add or remove a role from a member safely, validating hierarchy."""
        guild = member.guild
        role = guild.get_role(role_id)
        if not role:
            return "Role not found."

        if role >= guild.me.top_role:
            return f"Cannot assign role **{role.name}** (above bot highest role)."

        try:
            if role in member.roles:
                await member.remove_roles(role, reason="Reaction Role toggle")
                return f"Successfully removed the role **{role.name}**."
            else:
                await member.add_roles(role, reason="Reaction Role toggle")
                return f"Successfully granted the role **{role.name}**."
        except discord.Forbidden:
            return "Missing permissions to assign this role."
        except Exception as e:
            return f"Failed to modify roles: {e}"

    async def register_all_persistent_views(self) -> None:
        """Re-register all persistent views (buttons & select menus) at bot startup."""
        try:
            configs = await self.repo.get_all_global_reaction_role_messages()
            logger.info(f"ReactionRoleService: Re-registering {len(configs)} persistent views...")
            for config in configs:
                view = await self.build_persistent_view(config)
                if view:
                    self.bot.add_view(view, message_id=config.message_id)
        except Exception as e:
            logger.error(f"ReactionRoleService: Error registering views: {e}", exc_info=True)

    async def build_persistent_view(self, config: ReactionRoleMessageModel) -> Optional[discord.ui.View]:
        """Construct the persistent View for a configuration."""
        mappings = await self.get_reaction_roles(config.message_id)
        if not mappings:
            return None

        if config.type == "button":
            return ReactionRoleButtonView(self, mappings)
        elif config.type == "select":
            return ReactionRoleSelectView(self, mappings, config.group_name)
        return None


class ReactionRoleButtonView(discord.ui.View):
    """Persistent View for button-based reaction roles."""

    def __init__(self, service: ReactionRoleService, mappings: List[ReactionRoleModel]) -> None:
        super().__init__(timeout=None)
        self.service = service

        for mapping in mappings:
            # Emoji parsing
            emoji = None
            if mapping.emoji.startswith("<") and mapping.emoji.endswith(">"):
                # Custom emoji format
                emoji = mapping.emoji
            elif len(mapping.emoji) > 0:
                emoji = mapping.emoji

            button = discord.ui.Button(
                label=f"Role: {mapping.group_name}" if not emoji else None,
                emoji=emoji,
                custom_id=f"rr:btn:{mapping.role_id}",
                style=discord.ButtonStyle.primary
            )
            button.callback = self.make_callback(mapping.role_id)
            self.add_item(button)

    def make_callback(self, role_id: int):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)
            res = await self.service.toggle_role(interaction.user, role_id)
            await interaction.followup.send(content=res, ephemeral=True)
        return callback


class ReactionRoleSelectView(discord.ui.View):
    """Persistent View for select-menu-based reaction roles."""

    def __init__(self, service: ReactionRoleService, mappings: List[ReactionRoleModel], group_name: str) -> None:
        super().__init__(timeout=None)
        self.service = service

        options = []
        for mapping in mappings:
            emoji = None
            if mapping.emoji.startswith("<") and mapping.emoji.endswith(">"):
                emoji = mapping.emoji
            elif len(mapping.emoji) > 0:
                emoji = mapping.emoji

            options.append(discord.SelectOption(
                label=f"Role ID: {mapping.role_id}",
                value=str(mapping.role_id),
                emoji=emoji,
                description=f"Select to toggle this role"
            ))

        select = discord.ui.Select(
            placeholder=f"Select a role from group '{group_name}'...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"rr:sel:{group_name}"
        )
        select.callback = self.callback
        self.add_item(select)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        select_item = interaction.data.get("values", [])
        if not select_item:
            await interaction.followup.send("No selection made.", ephemeral=True)
            return

        role_id = int(select_item[0])
        res = await self.service.toggle_role(interaction.user, role_id)
        await interaction.followup.send(content=res, ephemeral=True)
