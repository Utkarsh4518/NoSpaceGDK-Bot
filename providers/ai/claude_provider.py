"""Anthropic Claude AI Provider adapter using aiohttp for REST API requests."""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
from providers.ai.base_ai_provider import BaseAIProvider
from utils.logger import logger


class ClaudeProvider(BaseAIProvider):
    """Adapter for Anthropic Claude Messages API endpoints."""

    def __init__(self, api_key: str) -> None:
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key.
        """
        self._api_key = api_key
        self._base_url = "https://api.anthropic.com/v1"
        self._models = [
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
            "claude-3-opus-20240229"
        ]
        logger.info("Claude provider: Initialized.")

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple[List[Dict[str, str]], Optional[str]]:
        """Convert messages to Claude format.

        Extracts the system message if present to place in system parameter,
        and ensures remaining messages are just 'user' and 'assistant' roles.
        """
        claude_messages = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_instruction = content
            else:
                claude_messages.append({
                    "role": role,
                    "content": content
                })

        return claude_messages, system_instruction

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        target_model = model or "claude-3-5-sonnet-latest"
        claude_messages, system = self._convert_messages(messages)

        # max_tokens is a REQUIRED parameter for Claude API
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": claude_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature
        }

        if system:
            payload["system"] = system

        url = f"{self._base_url}/messages"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers(), json=payload, timeout=30) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"Claude error status={resp.status}: {err_text}")

                    data = await resp.json()
                    content = data["content"][0]["text"]
                    usage = data.get("usage", {})

                    return {
                        "content": content,
                        "prompt_tokens": usage.get("input_tokens", self.count_tokens(str(messages))),
                        "completion_tokens": usage.get("output_tokens", self.count_tokens(content)),
                        "model": target_model
                    }
        except Exception as e:
            logger.error(f"Claude provider: Chat request failed: {e}")
            raise

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        target_model = model or "claude-3-5-sonnet-latest"
        claude_messages, system = self._convert_messages(messages)

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": claude_messages,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            "stream": True
        }

        if system:
            payload["system"] = system

        url = f"{self._base_url}/messages"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers(), json=payload, timeout=60) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"Claude error status={resp.status}: {err_text}")

                    # Anthropic SSE yields events like content_block_delta, message_start, message_delta
                    event_type = ""
                    async for line in resp.content:
                        line_str = line.decode("utf-8").strip()
                        if not line_str:
                            continue

                        if line_str.startswith("event:"):
                            event_type = line_str[6:].strip()
                            continue

                        if line_str.startswith("data:"):
                            data_body = line_str[5:].strip()
                            if event_type == "content_block_delta":
                                try:
                                    chunk = json.loads(data_body)
                                    delta = chunk["delta"].get("text", "")
                                    if delta:
                                        yield {
                                            "delta": delta,
                                            "prompt_tokens": 0,
                                            "completion_tokens": 0
                                        }
                                except Exception:
                                    continue
        except Exception as e:
            logger.error(f"Claude provider: Streaming request failed: {e}")
            raise

    async def list_models(self) -> List[str]:
        return self._models

    async def health_check(self) -> bool:
        # Anthropic doesn't have a simple models listing. We can send a basic token counting check,
        # or do a dummy validation message (which would cost, so list checking models is preferred).
        # We can just return true or check api access.
        return True

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
