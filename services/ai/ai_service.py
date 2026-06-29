"""AI Assistant Service coordinator facade."""

import time
from typing import Any, AsyncGenerator, Dict, List, Optional
from models.conversation import Conversation, Message
from services.ai.conversation_manager import ConversationManager
from services.ai.provider_router import AIProviderRouter
from services.ai.prompt_manager import PromptManager
from services.ai.token_manager import TokenManager
from utils.logger import logger


class AIService:
    """Main facade coordinator handling user AI prompt executions, history persistence,
    and cost log audits.
    """

    def __init__(
        self,
        conversation_manager: ConversationManager,
        provider_router: AIProviderRouter,
        prompt_manager: PromptManager,
        token_manager: TokenManager,
        default_model: str
    ) -> None:
        """Initialize AIService facade.

        Args:
            conversation_manager: History controller.
            provider_router: Swappable AI backend router.
            prompt_manager: Prompt builder.
            token_manager: Cost logger.
            default_model: Configured default fallback model.
        """
        self.conversations = conversation_manager
        self.providers = provider_router
        self.prompts = prompt_manager
        self.tokens = token_manager
        self._default_model = default_model
        logger.info("AI Service coordinator: Initialized.")

    async def get_conversation_history(
        self,
        target_id: int,
        target_type: str
    ) -> Conversation:
        """Load conversation session configuration and history.

        Args:
            target_id: Guild, channel, or user ID.
            target_type: 'guild', 'channel', or 'user'.

        Returns:
            Conversation entity.
        """
        return await self.conversations.get_or_create_conversation(
            target_id=target_id,
            target_type=target_type,
            default_model=self._default_model,
            default_provider=self.providers.default_provider_name
        )

    async def ask(
        self,
        guild_id: Optional[int],
        channel_id: int,
        user_id: int,
        prompt: str,
        target_type: str = "channel",
        system_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform a standard non-streaming AI completion request in context.

        Args:
            guild_id: Discord Guild snowflake.
            channel_id: Discord Channel snowflake.
            user_id: Discord User snowflake.
            prompt: User message content.
            target_type: Mapped context target ('guild', 'channel', or 'user').
            system_override: Temporary system prompt override.

        Returns:
            Dict containing response 'content' and cost audit data.
        """
        target_id = channel_id if target_type == "channel" else (guild_id if target_type == "guild" else user_id)
        conv = await self.get_conversation_history(target_id, target_type)

        # 1. Build system instructions
        system_prompt = await self.prompts.build_system_prompt(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            override_prompt=system_override
        )

        # 2. Build full message payloads
        payload = [{"role": "system", "content": system_prompt}]
        for msg in conv.messages:
            payload.append(msg.to_dict())

        # Append new user message
        payload.append({"role": "user", "content": prompt})

        # 3. Retrieve provider and execute chat query
        provider = self.providers.get_provider(conv.active_provider)
        start_time = time.perf_counter()
        
        try:
            result = await provider.chat(
                messages=payload,
                model=conv.active_model,
            )
            latency = time.perf_counter() - start_time
            
            content = result["content"]
            prompt_tokens = result["prompt_tokens"]
            completion_tokens = result["completion_tokens"]

            # Save messages in history
            user_msg = Message(role="user", content=prompt, prompt_tokens=0, completion_tokens=0)
            assistant_msg = Message(role="assistant", content=content, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

            await self.conversations.add_message(conv.id, user_msg)
            await self.conversations.add_message(conv.id, assistant_msg)

            # Log tokens consumption and cost stats
            cost = await self.tokens.log_usage(
                guild_id=guild_id,
                user_id=user_id,
                provider=conv.active_provider,
                model=conv.active_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )

            logger.info(
                f"AI Service: Completed chat context request for User {user_id} "
                f"on model {conv.active_provider}/{conv.active_model} in {latency:.2f}s."
            )

            return {
                "content": content,
                "provider": conv.active_provider,
                "model": conv.active_model,
                "cost": cost,
                "latency": latency,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }

        except Exception as e:
            logger.error(f"AI Service: Chat completion query failed: {e}")
            raise

    async def stream_ask(
        self,
        guild_id: Optional[int],
        channel_id: int,
        user_id: int,
        prompt: str,
        target_type: str = "channel",
        system_override: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Perform a streaming chat completion query in context.

        Args:
            guild_id: Discord Guild snowflake.
            channel_id: Discord Channel snowflake.
            user_id: Discord User snowflake.
            prompt: User query content.
            target_type: Context target type.
            system_override: Temporary override prompt.

        Yields:
            Dict containing delta changes and final cost stats.
        """
        target_id = channel_id if target_type == "channel" else (guild_id if target_type == "guild" else user_id)
        conv = await self.get_conversation_history(target_id, target_type)

        system_prompt = await self.prompts.build_system_prompt(
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            override_prompt=system_override
        )

        payload = [{"role": "system", "content": system_prompt}]
        for msg in conv.messages:
            payload.append(msg.to_dict())
        payload.append({"role": "user", "content": prompt})

        provider = self.providers.get_provider(conv.active_provider)
        full_content = []
        start_time = time.perf_counter()

        try:
            async for chunk in provider.stream_chat(
                messages=payload,
                model=conv.active_model,
            ):
                delta = chunk.get("delta", "")
                if delta:
                    full_content.append(delta)
                yield chunk

            # Dynamic summary logging on completion
            latency = time.perf_counter() - start_time
            content = "".join(full_content)

            prompt_tokens = provider.count_tokens(str(payload))
            completion_tokens = provider.count_tokens(content)

            # Persist logs
            user_msg = Message(role="user", content=prompt, prompt_tokens=0, completion_tokens=0)
            assistant_msg = Message(role="assistant", content=content, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

            await self.conversations.add_message(conv.id, user_msg)
            await self.conversations.add_message(conv.id, assistant_msg)

            cost = await self.tokens.log_usage(
                guild_id=guild_id,
                user_id=user_id,
                provider=conv.active_provider,
                model=conv.active_model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )

            # Yield final completion summary chunk
            yield {
                "done": True,
                "content": content,
                "provider": conv.active_provider,
                "model": conv.active_model,
                "cost": cost,
                "latency": latency,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }

        except Exception as e:
            logger.error(f"AI Service: Streaming completion failed: {e}")
            raise
