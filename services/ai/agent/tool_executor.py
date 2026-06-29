"""Tool Executor for AI Agent."""

import time
from typing import Any, Dict
import discord
from services.ai.agent.base_tool import BaseTool
from services.ai.agent.tool_manager import ToolManager
from services.ai.agent.permission_manager import PermissionManager
from services.ai.agent.validator import Validator
from utils.logger import logger

class ToolExecutor:
    """Handles the safe execution of tools and formats their responses."""

    def __init__(self, tool_manager: ToolManager, permission_manager: PermissionManager) -> None:
        """Initialize the ToolExecutor.
        
        Args:
            tool_manager: Manager that holds initialized tools.
            permission_manager: Validator for user permissions.
        """
        self.tools = tool_manager
        self.permissions = permission_manager
        self._cooldowns: Dict[str, float] = {}

    def _get_cooldown_key(self, tool_name: str, user_id: int) -> str:
        return f"{tool_name}:{user_id}"

    def _check_cooldown(self, tool: BaseTool, user_id: int) -> float:
        """Check if a tool is on cooldown for a user.
        
        Returns:
            Remaining cooldown time in seconds, or 0 if not on cooldown.
        """
        if tool.cooldown_seconds <= 0:
            return 0.0
            
        key = self._get_cooldown_key(tool.name, user_id)
        last_used = self._cooldowns.get(key, 0.0)
        elapsed = time.time() - last_used
        
        if elapsed < tool.cooldown_seconds:
            return tool.cooldown_seconds - elapsed
        return 0.0

    def _set_cooldown(self, tool: BaseTool, user_id: int) -> None:
        """Apply cooldown for a user."""
        if tool.cooldown_seconds > 0:
            key = self._get_cooldown_key(tool.name, user_id)
            self._cooldowns[key] = time.time()

    async def execute(self, tool_name: str, args: Dict[str, Any], user: discord.Member | discord.User, channel: discord.abc.Messageable) -> str:
        """Execute a tool safely.
        
        Args:
            tool_name: Name of the tool to execute.
            args: Arguments for the tool.
            user: User who requested the tool (via LLM).
            channel: Channel where the request was made.
            
        Returns:
            String representation of the execution result, to be fed back to the LLM.
        """
        try:
            tool = self.tools.get_tool(tool_name)
        except ValueError as e:
            logger.error(f"ToolExecutor: {e}")
            return f"Error: Tool '{tool_name}' not found."

        # 1. Check Permissions
        has_perm = await self.permissions.check_permissions(tool, user, channel)
        if not has_perm:
            return f"Error: User does not have permission to execute '{tool_name}'."

        # 2. Check Cooldown
        remaining_cd = self._check_cooldown(tool, user.id)
        if remaining_cd > 0:
            return f"Error: Tool '{tool_name}' is on cooldown. Please wait {remaining_cd:.1f} seconds."

        # 3. Validate Arguments
        try:
            Validator.validate_args(tool, args)
            await tool.validate(**args)
        except ValueError as e:
            return f"Error validating arguments for '{tool_name}': {str(e)}"

        # 4. Execute
        try:
            logger.info(f"ToolExecutor: Executing '{tool_name}' with args {args} for user {user.id}")
            result = await tool.execute(moderator=user, channel=channel, **args)
            
            # Apply cooldown upon successful execution
            self._set_cooldown(tool, user.id)
            
            if isinstance(result, dict):
                return str(result)
            return str(result)
            
        except Exception as e:
            logger.error(f"ToolExecutor: Error executing '{tool_name}': {e}", exc_info=True)
            return f"Error executing '{tool_name}': {str(e)}"
