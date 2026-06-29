"""Ollama local AI Provider adapter using aiohttp for REST API requests."""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
from providers.ai.base_ai_provider import BaseAIProvider
from utils.logger import logger


class OllamaProvider(BaseAIProvider):
    """Adapter for local Ollama chat API endpoints."""

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        """Initialize local Ollama provider.

        Args:
            base_url: The local Ollama server address.
        """
        self._base_url = base_url.rstrip("/")
        self._models = ["llama3", "mistral", "phi3", "gemma"]
        logger.info(f"Ollama provider: Initialized with base URL '{self._base_url}'.")

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        target_model = model or "llama3"
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        url = f"{self._base_url}/api/chat"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"Ollama error status={resp.status}: {err_text}")

                    data = await resp.json()
                    content = data["message"]["content"]
                    
                    return {
                        "content": content,
                        "prompt_tokens": data.get("prompt_eval_count", self.count_tokens(str(messages))),
                        "completion_tokens": data.get("eval_count", self.count_tokens(content)),
                        "model": target_model
                    }
        except Exception as e:
            logger.error(f"Ollama provider: Chat request failed: {e}")
            raise

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        target_model = model or "llama3"
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        url = f"{self._base_url}/api/chat"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"Ollama error status={resp.status}: {err_text}")

                    async for line in resp.content:
                        line_str = line.decode("utf-8").strip()
                        if not line_str:
                            continue

                        try:
                            chunk = json.loads(line_str)
                            delta = chunk["message"].get("content", "")
                            
                            # Fetch final statistics on completion chunk
                            prompt_tokens = chunk.get("prompt_eval_count", 0) if chunk.get("done") else 0
                            completion_tokens = chunk.get("eval_count", 0) if chunk.get("done") else 0

                            if delta or chunk.get("done"):
                                yield {
                                    "delta": delta,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens
                                }
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"Ollama provider: Streaming request failed: {e}")
            raise

    async def list_models(self) -> List[str]:
        # Fetch locally pulled models from Ollama API
        url = f"{self._base_url}/api/tags"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m["name"] for m in data.get("models", [])]
                        if models:
                            return models
        except Exception:
            pass
        return self._models

    async def health_check(self) -> bool:
        # Simple health check endpoint for Ollama is the root page or tags
        url = f"{self._base_url}/api/tags"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=3) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
