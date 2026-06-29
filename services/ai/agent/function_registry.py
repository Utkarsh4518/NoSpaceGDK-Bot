"""Function Registry to auto-discover and map Agent tools."""

import importlib
import inspect
import os
import sys
from typing import Dict, List, Type
from services.ai.agent.base_tool import BaseTool
from utils.logger import logger

class FunctionRegistry:
    """Discovers, loads, and indexes tools available to the AI agent."""

    def __init__(self, tools_dir: str = "tools") -> None:
        """Initialize the registry.
        
        Args:
            tools_dir: Path to the directory containing tools, relative to project root.
        """
        self.tools_dir = tools_dir
        self._tools_classes: Dict[str, Type[BaseTool]] = {}
        self.discover_tools()

    def discover_tools(self) -> None:
        """Scan the tools directory and register all Tool classes."""
        self._tools_classes.clear()
        
        if not os.path.exists(self.tools_dir):
            logger.warning(f"FunctionRegistry: Tools directory '{self.tools_dir}' not found. Skipping discovery.")
            return

        for root, _, files in os.walk(self.tools_dir):
            for file in files:
                if file.endswith(".py") and not file.startswith("__"):
                    module_path = os.path.join(root, file)
                    module_name = module_path.replace(os.sep, ".")[:-3]
                    
                    try:
                        module = importlib.import_module(module_name)
                        for name, obj in inspect.getmembers(module):
                            if inspect.isclass(obj) and issubclass(obj, BaseTool) and obj is not BaseTool:
                                # We instantiate temporarily just to get the name, 
                                # but ideally the manager will manage instances.
                                # Since name is a property, we might need a classmethod,
                                # but for now we'll store the class and let ToolManager instantiate.
                                self._register_tool_class(obj)
                    except Exception as e:
                        logger.error(f"FunctionRegistry: Failed to load tools from {module_name}: {e}")

        logger.info(f"FunctionRegistry: Discovered {len(self._tools_classes)} tools.")

    def _register_tool_class(self, tool_class: Type[BaseTool]) -> None:
        """Register a Tool class internally."""
        try:
            # Create a temporary instance to read its name.
            # We assume it can be instantiated without complex args initially,
            # but tools might require dependencies.
            # For discovery, maybe we should rely on a class attribute or just store classes.
            # Since dependencies might be needed, let's assume tools accept **kwargs or no-args for basic instantiation,
            # or we mandate they set a class attribute for discovery.
            # But we can also just wait for the ToolManager to instantiate them.
            
            # To avoid instantiation issues during discovery, we can just keep a list of classes,
            # and ToolManager will instantiate them, which then extracts their 'name' property.
            
            # Let's add it to a list and index it later when instantiated.
            self._tools_classes[tool_class.__name__] = tool_class
        except Exception as e:
            logger.error(f"FunctionRegistry: Failed to register {tool_class.__name__}: {e}")

    def get_tool_classes(self) -> List[Type[BaseTool]]:
        """Return all discovered tool classes."""
        return list(self._tools_classes.values())
