"""Google Gemini AI Provider adapter using aiohttp for REST API requests."""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional
import aiohttp
from providers.ai.base_ai_provider import BaseAIProvider
from utils.logger import logger


class GeminiProvider(BaseAIProvider):
    """Adapter for Google Gemini API endpoints."""

    def __init__(self, api_key: str) -> None:
        """Initialize Google Gemini provider.

        Args:
            api_key: Gemini API key.
        """
        self._api_key = api_key
        self._base_url = "https://generativelanguage.googleapis.com/v1beta"
        self._models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
        logger.info("Gemini provider: Initialized.")

    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Convert standard message roles (system, user, assistant) to Gemini format.

        Extracts the system message if present to place in systemInstructions.
        """
        gemini_contents = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_instruction = content
            else:
                # Map 'assistant' role to 'model', map 'user' role to 'user'
                gemini_role = "model" if role == "assistant" else "user"
                gemini_contents.append({
                    "role": gemini_role,
                    "parts": [{"text": content}]
                })

        return gemini_contents, system_instruction

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        target_model = model or "gemini-1.5-flash"
        contents, system_instruction = self._convert_messages(messages)

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        url = f"{self._base_url}/models/{target_model}:generateContent?key={self._api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=30) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"Gemini error status={resp.status}: {err_text}")

                    data = await resp.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        raise Exception("Gemini returned empty candidate choices.")

                    content = candidates[0]["content"]["parts"][0]["text"]
                    
                    # Estimate tokens
                    return {
                        "content": content,
                        "prompt_tokens": self.count_tokens(str(messages)),
                        "completion_tokens": self.count_tokens(content),
                        "model": target_model
                    }
        except Exception as e:
            logger.error(f"Gemini provider: Chat request failed: {e}")
            raise

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        target_model = model or "gemini-1.5-flash"
        contents, system_instruction = self._convert_messages(messages)

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        url = f"{self._base_url}/models/{target_model}:streamGenerateContent?key={self._api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as resp:
                    if resp.status != 200:
                        err_text = await resp.text()
                        raise Exception(f"Gemini error status={resp.status}: {err_text}")

                    # Gemini returns streamed content as a JSON array that is populated piece by piece.
                    # We can parse the chunks manually or scan for text fields inside.
                    # Usually, streamGenerateContent returns chunks of SSE (or a json stream).
                    async for line in resp.content:
                        line_str = line.decode("utf-8").strip()
                        if not line_str:
                            continue

                        # Clean up formatting brackets for streaming JSON
                        if line_str.startswith("[") or line_str.startswith(","):
                            line_str = line_str[1:].strip()
                        if line_str.endswith("]"):
                            line_str = line_str[:-1].strip()

                        if not line_str:
                            continue

                        try:
                            chunk = json.loads(line_str)
                            parts = chunk["candidates"][0]["content"]["parts"]
                            delta = "".join(p.get("text", "") for p in parts)
                            if delta:
                                yield {
                                    "delta": delta,
                                    "prompt_tokens": 0,
                                    "completion_tokens": 0
                                }
                        except Exception:
                            # Not a complete json chunk yet, wait for next buffer lines
                            continue
        except Exception as e:
            logger.error(f"Gemini provider: Streaming request failed: {e}")
            raise

    async def list_models(self) -> List[str]:
        return self._models

    async def health_check(self) -> bool:
        # Simple query model listing to check health
        url = f"{self._base_url}/models?key={self._api_key}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as resp:
                    return resp.status == 200
        except Exception:
            return False

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)
