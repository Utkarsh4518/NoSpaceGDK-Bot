"""Tool Manager for managing and instantiating Agent tools."""

from typing import Any, Dict, List, Type
from services.ai.agent.base_tool import BaseTool
from services.ai.agent.function_registry import FunctionRegistry
from utils.logger import logger

class ToolManager:
    """Manages instantiated tools and their lifecycle."""

    def __init__(self, registry: FunctionRegistry, service_container: Any) -> None:
        """Initialize the ToolManager.
        
        Args:
            registry: The FunctionRegistry containing discovered tool classes.
            service_container: The DI container to inject dependencies into tools.
        """
        self.registry = registry
        self.services = service_container
        self._tools: Dict[str, BaseTool] = {}
        
        self.load_tools()

    def load_tools(self) -> None:
        """Instantiate all discovered tools and index them by name."""
        self._tools.clear()
        classes = self.registry.get_tool_classes()
        
        for tool_class in classes:
            try:
                # We inject the service container so tools can access any service.
                # If a tool doesn't accept arguments, it can just ignore it, but ideally
                # all tools accept **kwargs or explicitly accept service_container.
                try:
                    tool_instance = tool_class(service_container=self.services)
                except TypeError:
                    # Fallback for tools that don't need dependencies
                    tool_instance = tool_class()
                
                name = tool_instance.name
                if name in self._tools:
                    logger.warning(f"ToolManager: Tool with name '{name}' already exists. Overwriting.")
                
                self._tools[name] = tool_instance
            except Exception as e:
                logger.error(f"ToolManager: Failed to instantiate tool {tool_class.__name__}: {e}")
                
        logger.info(f"ToolManager: Successfully loaded {len(self._tools)} tools.")

    def get_tool(self, name: str) -> BaseTool:
        """Retrieve a tool by name."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found.")
        return self._tools[name]

    def get_all_tools(self) -> List[BaseTool]:
        """Retrieve all registered tools."""
        return list(self._tools.values())
        
    def get_tools_payload(self) -> List[Dict[str, Any]]:
        """Get the payload representation for all tools to send to the provider."""
        return [tool.register() for tool in self._tools.values()]
