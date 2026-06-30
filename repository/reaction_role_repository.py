"""Reaction Role Repository for SQL persistence."""

from typing import List, Optional
from models.reaction_role import ReactionRoleModel, ReactionRoleMessageModel
from repositories.base_repository import BaseRepository

class ReactionRoleRepository(BaseRepository):
    """Handles SQL persistence for Reaction Roles (emoji, buttons, select menus mappings)."""

    async def create_reaction_role_message(
        self,
        message_id: int,
        guild_id: int,
        channel_id: int,
        title: Optional[str],
        description: Optional[str],
        group_name: str,
        type_: str
    ) -> ReactionRoleMessageModel:
        """Register a reaction role message config."""
        query = """
            INSERT OR REPLACE INTO reaction_role_messages (message_id, guild_id, channel_id, title, description, group_name, type)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        await self.db.execute(query, (message_id, guild_id, channel_id, title, description, group_name, type_))
        await self.db.commit()
        
        return ReactionRoleMessageModel(
            message_id=message_id,
            guild_id=guild_id,
            channel_id=channel_id,
            title=title,
            description=description,
            group_name=group_name,
            type=type_
        )

    async def get_reaction_role_message(self, message_id: int) -> Optional[ReactionRoleMessageModel]:
        """Fetch a reaction role message config by ID."""
        query = """
            SELECT message_id, guild_id, channel_id, title, description, group_name, type
            FROM reaction_role_messages
            WHERE message_id = ?;
        """
        async with self.db.connection.execute(query, (message_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return ReactionRoleMessageModel(*row)
        return None

    async def add_reaction_role(self, guild_id: int, message_id: int, emoji: str, role_id: int, group_name: str) -> ReactionRoleModel:
        """Add a specific role mapping to an emoji/custom_id."""
        query = """
            INSERT OR REPLACE INTO reaction_roles (guild_id, message_id, emoji, role_id, group_name)
            VALUES (?, ?, ?, ?, ?);
        """
        cursor = await self.db.execute(query, (guild_id, message_id, emoji, role_id, group_name))
        await self.db.commit()
        
        return ReactionRoleModel(
            id=cursor.lastrowid,
            guild_id=guild_id,
            message_id=message_id,
            emoji=emoji,
            role_id=role_id,
            group_name=group_name
        )

    async def remove_reaction_role(self, message_id: int, role_id: int) -> None:
        """Remove a specific role mapping from a message."""
        query = "DELETE FROM reaction_roles WHERE message_id = ? AND role_id = ?;"
        await self.db.execute(query, (message_id, role_id))
        await self.db.commit()

    async def get_reaction_roles(self, message_id: int) -> List[ReactionRoleModel]:
        """Get all role mappings associated with a message."""
        query = "SELECT id, guild_id, message_id, emoji, role_id, group_name FROM reaction_roles WHERE message_id = ?;"
        roles = []
        async with self.db.connection.execute(query, (message_id,)) as cursor:
            async for row in cursor:
                roles.append(ReactionRoleModel(*row))
        return roles

    async def delete_reaction_role_message(self, message_id: int) -> None:
        """Delete a reaction role config entirely."""
        async with self.db.transaction():
            await self.db.execute("DELETE FROM reaction_roles WHERE message_id = ?;", (message_id,))
            await self.db.execute("DELETE FROM reaction_role_messages WHERE message_id = ?;", (message_id,))

    async def get_all_reaction_role_messages(self, guild_id: int) -> List[ReactionRoleMessageModel]:
        """Fetch all active reaction role message configurations for a guild."""
        query = """
            SELECT message_id, guild_id, channel_id, title, description, group_name, type
            FROM reaction_role_messages
            WHERE guild_id = ?;
        """
        messages = []
        async with self.db.connection.execute(query, (guild_id,)) as cursor:
            async for row in cursor:
                messages.append(ReactionRoleMessageModel(*row))
        return messages
        
    async def get_all_global_reaction_role_messages(self) -> List[ReactionRoleMessageModel]:
        """Fetch all reaction role messages across all guilds (useful for startup persistent views)."""
        query = """
            SELECT message_id, guild_id, channel_id, title, description, group_name, type
            FROM reaction_role_messages;
        """
        messages = []
        async with self.db.connection.execute(query) as cursor:
            async for row in cursor:
                messages.append(ReactionRoleMessageModel(*row))
        return messages
