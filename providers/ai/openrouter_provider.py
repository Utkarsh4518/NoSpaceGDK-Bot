"""OpenRouter AI Provider adapter using aiohttp for REST API requests."""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
from providers.ai.base_ai_provider import BaseAIProvider
from utils.logger import logger


class OpenRouterProvider(BaseAIProvider):
    """Adapter for OpenRouter Chat API endpoints."""

    def __init__(self, api_key: str) -> None:
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key.
        """
        self._api_key = api_key
        self._base_url = "https://openrouter.ai/api/v1"
        self._models = [
            "meta-llama/llama-3-8b-instruct:free",
            "mistralai/mistral-7b-instruct:free",
            "openai/gpt-4o-mini",
            "google/gemini-flash-1.5"
        ]
        logger.info("OpenRouter provider: Initialized.")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://nospacefgk.bot",
            "X-Title": "NoSpaceFGK Bot"
        }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        target_model = model or "meta-llama/llama-3-8b-instruct:free"
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        url = f"{self._base_url}/chat/completions"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers(), json=payload, timeout=30) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"OpenRouter error status={resp.status}: {err_text}")

                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})

                    return {
                        "content": content,
                        "prompt_tokens": usage.get("prompt_tokens", self.count_tokens(str(messages))),
                        "completion_tokens": usage.get("completion_tokens", self.count_tokens(content)),
                        "model": target_model
                    }
        except Exception as e:
            logger.error(f"OpenRouter provider: Chat request failed: {e}")
            raise

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        target_model = model or "meta-llama/llama-3-8b-instruct:free"
        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        url = f"{self._base_url}/chat/completions"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=self._headers(), json=payload, timeout=60) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"OpenRouter error status={resp.status}: {err_text}")

                    async for line in resp.content:
                        line_str = line.decode("utf-8").strip()
                        if not line_str or not line_str.startswith("data:"):
                            continue

                        data_body = line_str[5:].strip()
                        if data_body == "[DONE]":
                            break

                        try:
                            chunk = json.loads(data_body)
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield {
                                    "delta": delta,
                                    "prompt_tokens": 0,
                                    "completion_tokens": 0
                                }
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"OpenRouter provider: Streaming request failed: {e}")
            raise

    async def list_models(self) -> List[str]:
        # Dynamic model listing from OpenRouter is possible, but we fallback to our list.
        # Let's hit the OpenRouter models endpoint to return actual available models!
        url = f"{self._base_url}/models"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m["id"] for m in data.get("data", [])]
                        if models:
                            return models
        except Exception:
            pass
        return self._models

    async def health_check(self) -> bool:
        url = f"{self._base_url}/models"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
