"""Planner for AI Agent Tool execution."""

import json
from typing import Any, Dict, List, Optional
from utils.logger import logger

class Planner:
    """Parses intents and structures multi-step tool calls if needed.
    
    For Phase 8, this serves as an intent parser and structure normalizer 
    for LLMs that might output tool calls differently.
    """

    @staticmethod
    def parse_tool_calls(response_message: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and normalize tool calls from a provider's response message.
        
        Args:
            response_message: The message dictionary from the AI provider.
            
        Returns:
            A list of tool call dictionaries normalized to:
            {
                "id": "call_id",
                "name": "tool_name",
                "arguments": {"arg_key": "arg_val"}
            }
        """
        tool_calls = response_message.get("tool_calls", [])
        if not tool_calls:
            return []

        normalized_calls = []
        for call in tool_calls:
            try:
                # Handle OpenAI format natively:
                if "function" in call:
                    func = call["function"]
                    args = func.get("arguments", "{}")
                    if isinstance(args, str):
                        args = json.loads(args)
                        
                    normalized_calls.append({
                        "id": call.get("id", "unknown"),
                        "name": func.get("name"),
                        "arguments": args
                    })
                # Handle other potential formats here in the future
                else:
                    logger.warning(f"Planner: Unrecognized tool call format: {call}")
            except Exception as e:
                logger.error(f"Planner: Failed to parse tool call {call}: {e}")
                
        return normalized_calls
