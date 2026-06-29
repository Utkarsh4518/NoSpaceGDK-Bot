"""Core AI Agent that coordinates tool discovery, execution, and LLM communication."""

from typing import Any, Dict, Optional
import discord
from services.ai.agent.function_registry import FunctionRegistry
from services.ai.agent.tool_manager import ToolManager
from services.ai.agent.permission_manager import PermissionManager
from services.ai.agent.tool_executor import ToolExecutor
from services.ai.agent.planner import Planner
from utils.logger import logger

class Agent:
    """The central Agent coordinator.
    
    Acts as a middleware between the AIService and the tools, 
    detecting tool calls in LLM responses and executing them.
    """

    def __init__(self, bot: Any, service_container: Any) -> None:
        """Initialize the Agent.
        
        Args:
            bot: Discord bot instance.
            service_container: DI service container.
        """
        self.bot = bot
        self.services = service_container
        
        self.registry = FunctionRegistry(tools_dir="tools")
        self.tool_manager = ToolManager(registry=self.registry, service_container=self.services)
        self.permission_manager = PermissionManager(bot=self.bot)
        self.executor = ToolExecutor(tool_manager=self.tool_manager, permission_manager=self.permission_manager)
        
        logger.info("Agent Framework initialized successfully.")

    def get_tools_payload(self) -> list:
        """Get the payload representing available tools for the LLM."""
        return self.tool_manager.get_tools_payload()

    async def handle_tool_calls(
        self, 
        message_dict: Dict[str, Any], 
        user_id: int, 
        channel_id: int
    ) -> Optional[list]:
        """Check for tool calls in a response and execute them.
        
        Args:
            message_dict: The message dictionary from the AI provider.
            user_id: The ID of the user who made the request.
            channel_id: The ID of the channel where the request was made.
            
        Returns:
            A list of tool response messages to append to the context, 
            or None if no tool calls were made.
        """
        tool_calls = Planner.parse_tool_calls(message_dict)
        if not tool_calls:
            return None
            
        # Resolve user and channel from bot
        user = self.bot.get_user(user_id)
        if not user:
            # Fallback if not cached
            try:
                user = await self.bot.fetch_user(user_id)
            except Exception:
                user = None
                
        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                channel = None

        tool_responses = []
        for call in tool_calls:
            tool_id = call.get("id")
            tool_name = call.get("name")
            arguments = call.get("arguments", {})
            
            logger.info(f"Agent: Instructed to execute tool '{tool_name}' (ID: {tool_id})")
            
            result_str = await self.executor.execute(tool_name, arguments, user, channel)
            
            # Format the tool response as required by the OpenAI/standard tool calling schema
            tool_responses.append({
                "role": "tool",
                "tool_call_id": tool_id,
                "name": tool_name,
                "content": result_str
            })
            
        return tool_responses
