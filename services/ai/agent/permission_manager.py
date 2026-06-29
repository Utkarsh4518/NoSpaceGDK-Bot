"""Permission Manager for AI Agent Tools."""

import discord
from typing import Any
from services.ai.agent.base_tool import BaseTool
from utils.logger import logger

class PermissionManager:
    """Validates user permissions before allowing tool execution."""

    def __init__(self, bot: Any) -> None:
        """Initialize the PermissionManager.
        
        Args:
            bot: The Discord bot instance (needed to check owners, etc.)
        """
        self.bot = bot

    async def check_permissions(self, tool: BaseTool, user: discord.Member | discord.User, channel: discord.abc.Messageable) -> bool:
        """Check if the user has permission to execute the given tool.
        
        Args:
            tool: The tool to execute.
            user: The user requesting execution.
            channel: The channel where the request was made.
            
        Returns:
            True if permitted, False otherwise.
        """
        # Check owner requirement
        if tool.require_owner:
            is_owner = await self.bot.is_owner(user)
            if not is_owner:
                logger.warning(f"PermissionManager: User {user.id} denied access to {tool.name} (requires owner).")
                return False

        # Check specific discord permissions if in a guild
        if tool.required_permissions:
            if not isinstance(user, discord.Member):
                # Cannot check guild permissions in DMs
                logger.warning(f"PermissionManager: Tool {tool.name} requires guild permissions, but invoked in DM.")
                return False
                
            # We assume channel is a TextChannel or similar guild channel
            if isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.Thread)):
                perms = channel.permissions_for(user)
            else:
                perms = user.guild_permissions
                
            for req_perm in tool.required_permissions:
                if not getattr(perms, req_perm, False):
                    logger.warning(f"PermissionManager: User {user.id} denied access to {tool.name} (missing {req_perm}).")
                    return False
                    
        return True
