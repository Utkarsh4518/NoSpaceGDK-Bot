"""Argument Validator for AI Agent Tools."""

from typing import Any, Dict
import jsonschema
from services.ai.agent.base_tool import BaseTool
from utils.logger import logger

class Validator:
    """Validates arguments against a tool's JSON schema."""

    @staticmethod
    def validate_args(tool: BaseTool, args: Dict[str, Any]) -> bool:
        """Validate the provided arguments against the tool's schema.
        
        Args:
            tool: The tool to validate against.
            args: The arguments parsed from the LLM.
            
        Returns:
            True if valid, raises ValueError if invalid.
        """
        schema = tool.parameters
        
        # If the schema is completely empty, it might mean no parameters expected.
        # But properly formed it should be {"type": "object", "properties": {}}
        if not schema:
            if args:
                logger.warning(f"Validator: Tool {tool.name} expects no args, but got {args}")
            return True

        try:
            jsonschema.validate(instance=args, schema=schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            logger.error(f"Validator: Tool {tool.name} argument validation failed: {e.message}")
            raise ValueError(f"Invalid arguments for tool '{tool.name}': {e.message}")
