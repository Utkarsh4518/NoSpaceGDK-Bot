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
        default_model: str,
        agent: Any = None
    ) -> None:
        """Initialize AIService facade.

        Args:
            conversation_manager: History controller.
            provider_router: Swappable AI backend router.
            prompt_manager: Prompt builder.
            token_manager: Cost logger.
            default_model: Configured default fallback model.
            agent: AI Agent for function calling.
        """
        self.conversations = conversation_manager
        self.providers = provider_router
        self.prompts = prompt_manager
        self.tokens = token_manager
        self._default_model = default_model
        self.agent = agent
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
        # Dynamically prepend system instructions first, then append other history messages
        payload = [{"role": "system", "content": system_prompt}]
        for msg in conv.messages:
            # Skip system/developer messages stored in history to prevent duplicates
            if msg.role in ("system", "developer"):
                continue
            payload.append(msg.to_dict())

        # Append new user message
        payload.append({"role": "user", "content": prompt})

        # Track history list to write sequentially to the database
        history_to_save: List[Message] = []
        
        # Save user message first
        user_msg = Message(role="user", content=prompt)
        history_to_save.append(user_msg)

        # 3. Retrieve provider and execute chat query
        provider = self.providers.get_provider(conv.active_provider)
        start_time = time.perf_counter()
        
        tools_payload = self.agent.get_tools_payload() if self.agent else None
        
        total_prompt_tokens = 0
        total_completion_tokens = 0
        
        try:
            for _ in range(5):
                step_start = time.perf_counter()
                result = await provider.chat(
                    messages=payload,
                    model=conv.active_model,
                    tools=tools_payload
                )
                step_latency = time.perf_counter() - step_start
                
                content = result.get("content", "") or ""
                p_tokens = result.get("prompt_tokens", 0)
                c_tokens = result.get("completion_tokens", 0)
                total_prompt_tokens += p_tokens
                total_completion_tokens += c_tokens
                
                tool_responses = None
                if self.agent and result.get("tool_calls"):
                    tool_responses = await self.agent.handle_tool_calls(result, user_id, channel_id)
                    
                if tool_responses:
                    # Save assistant message with tool calls
                    assistant_tool_msg = Message(
                        role="assistant",
                        content=content,
                        prompt_tokens=p_tokens,
                        completion_tokens=c_tokens,
                        tool_calls=result.get("tool_calls"),
                        provider=conv.active_provider,
                        model=conv.active_model,
                        latency=step_latency
                    )
                    history_to_save.append(assistant_tool_msg)

                    # Append to active payload
                    payload.append({
                        "role": "assistant",
                        "content": content,
                        "tool_calls": result.get("tool_calls")
                    })
                    
                    # Save each tool response message
                    for resp in tool_responses:
                        tool_msg = Message(
                            role="tool",
                            content=resp.get("content", ""),
                            tool_call_id=resp.get("tool_call_id"),
                            name=resp.get("name")
                        )
                        history_to_save.append(tool_msg)
                        payload.append(resp)
                    continue
                else:
                    # Save final assistant reply message
                    assistant_final_msg = Message(
                        role="assistant",
                        content=content,
                        prompt_tokens=p_tokens,
                        completion_tokens=c_tokens,
                        provider=conv.active_provider,
                        model=conv.active_model,
                        latency=step_latency
                    )
                    history_to_save.append(assistant_final_msg)
                    break

            latency = time.perf_counter() - start_time

            # Write all messages generated in this block to conversation database history
            for msg in history_to_save:
                await self.conversations.add_message(conv.id, msg)

            # Log tokens consumption and cost stats
            cost = await self.tokens.log_usage(
                guild_id=guild_id,
                user_id=user_id,
                provider=conv.active_provider,
                model=conv.active_model,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens
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
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens
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
            if msg.role in ("system", "developer"):
                continue
            payload.append(msg.to_dict())
        payload.append({"role": "user", "content": prompt})

        provider = self.providers.get_provider(conv.active_provider)
        full_content = []
        start_time = time.perf_counter()
        tools_payload = self.agent.get_tools_payload() if self.agent else None

        history_to_save: List[Message] = []
        history_to_save.append(Message(role="user", content=prompt))

        try:
            # Tool call loop (max 5 iterations)
            for i in range(5):
                has_tool_call = False
                tool_calls_buffer = {}
                step_start = time.perf_counter()
                
                async for chunk in provider.stream_chat(
                    messages=payload,
                    model=conv.active_model,
                    tools=tools_payload
                ):
                    delta = chunk.get("delta", "")
                    t_calls = chunk.get("tool_calls", [])
                    
                    if t_calls:
                        has_tool_call = True
                        for tc in t_calls:
                            idx = tc.get("index", 0)
                            if idx not in tool_calls_buffer:
                                tool_calls_buffer[idx] = tc
                            else:
                                if "function" in tc and "arguments" in tc["function"]:
                                    if "function" not in tool_calls_buffer[idx]:
                                        tool_calls_buffer[idx]["function"] = {"arguments": ""}
                                    tool_calls_buffer[idx]["function"]["arguments"] += tc["function"]["arguments"]
                    
                    if not has_tool_call and delta:
                        full_content.append(delta)
                        yield chunk
                
                step_latency = time.perf_counter() - step_start
                        
                if has_tool_call and self.agent:
                    # Reconstruct tool calls
                    formatted_tool_calls = list(tool_calls_buffer.values())
                    result_simulated = {"tool_calls": formatted_tool_calls}
                    
                    # Save intermediate assistant tool call message
                    assistant_tool_msg = Message(
                        role="assistant",
                        content="",
                        tool_calls=formatted_tool_calls,
                        provider=conv.active_provider,
                        model=conv.active_model,
                        latency=step_latency
                    )
                    history_to_save.append(assistant_tool_msg)

                    tool_responses = await self.agent.handle_tool_calls(result_simulated, user_id, channel_id)
                    if tool_responses:
                        payload.append({
                            "role": "assistant",
                            "content": "",
                            "tool_calls": formatted_tool_calls
                        })
                        for resp in tool_responses:
                            tool_msg = Message(
                                role="tool",
                                content=resp.get("content", ""),
                                tool_call_id=resp.get("tool_call_id"),
                                name=resp.get("name")
                            )
                            history_to_save.append(tool_msg)
                            payload.append(resp)
                        full_content.clear()
                        continue
                        
                # If no tool call, we are done
                content = "".join(full_content)
                assistant_final_msg = Message(
                    role="assistant",
                    content=content,
                    provider=conv.active_provider,
                    model=conv.active_model,
                    latency=step_latency
                )
                history_to_save.append(assistant_final_msg)
                break

            latency = time.perf_counter() - start_time
            content = "".join(full_content)

            prompt_tokens = provider.count_tokens(str(payload))
            completion_tokens = provider.count_tokens(content)

            # Assign tokens to final assistant message
            if history_to_save and history_to_save[-1].role == "assistant":
                history_to_save[-1].prompt_tokens = prompt_tokens
                history_to_save[-1].completion_tokens = completion_tokens

            # Persist all generated messages sequentially
            for msg in history_to_save:
                await self.conversations.add_message(conv.id, msg)

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
