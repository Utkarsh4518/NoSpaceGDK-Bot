"""AI Assistant Cog for NoSpaceFGK.

Handles conversational commands, provider state updates, prompt configs,
and token usage logging.
"""

import asyncio
import time
from typing import List, Optional
import discord
from discord import app_commands
from discord.ext import commands

from decorators.command_dec import guild_only_command, cooldown_command
from services.ai.ai_service import AIService
from ui.pagination import PaginationView
from utils.embeds import success_embed, error_embed, info_embed
from utils.helpers import format_duration
from utils.logger import logger


class AICog(commands.Cog, name="AI"):
    """Cog for interacting with swappable AI providers and conversation models."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the AI assistant cog."""
        self.bot = bot
        self.ai: AIService = bot.container.get(AIService)
        logger.info("AICog fully initialized.")

    @app_commands.command(name="chat", description="Chat with the AI assistant (remembers history).")
    @app_commands.describe(prompt="Your message to the AI assistant.")
    @cooldown_command(rate=1, per=2.0)
    async def chat(self, interaction: discord.Interaction, prompt: str) -> None:
        """Standard conversation command using active provider/model in context."""
        await interaction.response.defer()
        
        guild_id = interaction.guild_id
        channel_id = interaction.channel_id
        user_id = interaction.user.id
        
        # Check target context (guild channel or DMs)
        target_type = "channel" if guild_id else "user"
        
        try:
            # We attempt streaming to make the response feel extremely premium.
            # To prevent hitting Discord rate limits, we buffer updates every 1.5 seconds.
            full_reply = []
            last_update = time.monotonic()
            message_obj = None
            
            # Send initial placeholder
            placeholder_embed = info_embed(
                "AI Assistant 🤖",
                "*Thinking...*"
            )
            placeholder_embed.set_footer(text="Connecting to provider...")
            message_obj = await interaction.followup.send(embed=placeholder_embed)

            done_payload = None

            async for chunk in self.ai.stream_ask(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                prompt=prompt,
                target_type=target_type
            ):
                if chunk.get("done"):
                    done_payload = chunk
                    break

                delta = chunk.get("delta", "")
                if delta:
                    full_reply.append(delta)

                # Edit message periodically (every 1.5 seconds) to avoid rate limits
                now = time.monotonic()
                if now - last_update >= 1.5:
                    current_text = "".join(full_reply)
                    if current_text.strip():
                        embed = info_embed(
                            "AI Assistant 🤖",
                            current_text + " ▌"
                        )
                        embed.set_footer(text="Streaming response...")
                        try:
                            await message_obj.edit(embed=embed)
                        except discord.HTTPException:
                            pass
                    last_update = now

            # If streaming succeeded, show final output
            if done_payload:
                content = done_payload["content"]
                cost = done_payload["cost"]
                latency = done_payload["latency"]
                model = done_payload["model"]
                provider = done_payload["provider"]

                # Break response if it exceeds Discord's 4096 character embed description limit
                if len(content) > 4000:
                    content = content[:3950] + "\n\n*(Truncated due to length)*"

                embed = success_embed(
                    "AI Assistant 🤖",
                    content
                )
                embed.set_footer(
                    text=f"Provider: {provider} | Model: {model} | Cost: ${cost:.6f} | Time: {latency:.2f}s"
                )
                await message_obj.edit(embed=embed)
            else:
                # Streaming returned no terminal chunk, fall back to simple ask
                raise Exception("Streaming completed without completion statistics.")

        except Exception as e:
            logger.error(f"Chat command failed: {e}", exc_info=True)
            # Try to fetch non-streaming fallback
            try:
                result = await self.ai.ask(
                    guild_id=guild_id,
                    channel_id=channel_id,
                    user_id=user_id,
                    prompt=prompt,
                    target_type=target_type
                )
                content = result["content"]
                cost = result["cost"]
                model = result["model"]
                provider = result["provider"]

                embed = success_embed("AI Assistant 🤖", content)
                embed.set_footer(text=f"Provider: {provider} | Model: {model} | Cost: ${cost:.6f}")
                await interaction.followup.send(embed=embed)
            except Exception as inner_err:
                logger.error(f"AI fallback request failed: {inner_err}")
                await interaction.followup.send(
                    embed=error_embed(
                        "AI Error",
                        f"An error occurred while generating response: {inner_err}"
                    )
                )

    @app_commands.command(name="ask", description="Ask a one-off question (no history memory).")
    @app_commands.describe(prompt="Your question.")
    @cooldown_command(rate=1, per=2.0)
    async def ask(self, interaction: discord.Interaction, prompt: str) -> None:
        """Single turn query bypasses history storage but utilizes active settings."""
        await interaction.response.defer()
        
        guild_id = interaction.guild_id
        channel_id = interaction.channel_id
        user_id = interaction.user.id
        target_type = "channel" if guild_id else "user"

        try:
            # Send message using ask facade and temporary context overrides
            result = await self.ai.ask(
                guild_id=guild_id,
                channel_id=channel_id,
                user_id=user_id,
                prompt=prompt,
                target_type=target_type
            )
            
            # Instantly clear conversation after appending (making it a single turn)
            conv = await self.ai.get_conversation_history(
                target_id=channel_id if target_type == "channel" else user_id,
                target_type=target_type
            )
            await self.ai.conversations.clear_conversation(conv.id)

            content = result["content"]
            cost = result["cost"]
            latency = result["latency"]
            model = result["model"]
            provider = result["provider"]

            embed = success_embed("AI Q&A 💬", content)
            embed.set_footer(
                text=f"Provider: {provider} | Model: {model} | Cost: ${cost:.6f} | Latency: {latency:.2f}s"
            )
            if len(prompt) > 80:
                embed.description = f"**Question:** *{prompt[:77]}...*\n\n{content}"
            else:
                embed.description = f"**Question:** *{prompt}*\n\n{content}"

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Ask command failed: {e}")
            await interaction.followup.send(
                embed=error_embed("AI Error", f"Failed to complete one-off response: {e}")
            )

    @app_commands.command(name="resetchat", description="Clear all chat history memory for this channel.")
    @guild_only_command()
    async def resetchat(self, interaction: discord.Interaction) -> None:
        """Clear conversation log history."""
        conv = await self.ai.get_conversation_history(interaction.channel_id, "channel")
        await self.ai.conversations.clear_conversation(conv.id)
        
        await interaction.response.send_message(
            embed=success_embed(
                "Conversation Reset",
                "Successfully cleared chat history memory for this channel."
            )
        )

    @app_commands.command(name="model", description="Configure active model for this conversation.")
    @app_commands.describe(model_name="Select or type the model name to swap to.")
    @guild_only_command()
    async def model(self, interaction: discord.Interaction, model_name: str) -> None:
        """Swaps active AI model for this channel's context."""
        conv = await self.ai.get_conversation_history(interaction.channel_id, "channel")
        provider_name = conv.active_provider
        
        # Verify model name is supported by active provider
        provider = self.ai.providers.get_provider(provider_name)
        available_models = await provider.list_models()
        
        # Simple cleanup search match
        matched_model = None
        for m in available_models:
            if model_name.lower().strip() == m.lower().strip():
                matched_model = m
                break
        
        if not matched_model:
            # Fallback direct override if user manually specified a valid custom string
            matched_model = model_name

        await self.ai.conversations.update_settings(
            conversation_id=conv.id,
            provider=provider_name,
            model=matched_model
        )

        await interaction.response.send_message(
            embed=success_embed(
                "Model Swapped",
                f"Successfully set active model to **{matched_model}** for this channel."
            )
        )

    @model.autocomplete("model_name")
    async def model_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        """Autocomplete helper for active provider models list."""
        guild_id = interaction.guild_id
        channel_id = interaction.channel_id
        target_id = channel_id if guild_id else interaction.user.id
        target_type = "channel" if guild_id else "user"
        
        # Fetch active provider
        conv = await self.ai.get_conversation_history(target_id, target_type)
        provider = self.ai.providers.get_provider(conv.active_provider)
        
        models = await provider.list_models()
        return [
            app_commands.Choice(name=m, value=m)
            for m in models
            if current.lower() in m.lower()
        ][:25]

    @app_commands.command(name="providers", description="Show active AI providers status and configuration.")
    async def providers(self, interaction: discord.Interaction) -> None:
        """Summarize configured and active providers registration states."""
        await interaction.response.defer()
        
        providers = self.ai.providers.list_available_providers()
        default_p = self.ai.providers.default_provider_name
        
        desc = []
        for name in ["gemini", "openai", "claude", "openrouter", "ollama"]:
            status = "🟢 Active" if name in providers else "🔴 Disabled"
            desc.append(f"• **{name.capitalize()}**: {status}")

        embed = info_embed(
            "AI Providers Status ⚙️",
            "\n".join(desc) + f"\n\n**Default Configuration Provider**: `{default_p}`"
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="systemprompt", description="View or customize the system prompt override.")
    @app_commands.describe(prompt="New custom system prompt text (leave empty to reset/view).")
    @guild_only_command()
    async def systemprompt(self, interaction: discord.Interaction, prompt: Optional[str] = None) -> None:
        """Set or view custom system prompt template overrides."""
        guild_id = interaction.guild_id
        
        if prompt is None:
            # View active prompt
            active_prompt = await self.ai.prompts.build_system_prompt(guild_id=guild_id)
            custom_check = await self.ai.prompts._repo.get_prompt("guild", guild_id)
            
            status_text = "Custom override active:" if custom_check else "Default configuration active:"
            
            embed = info_embed(
                "Active System Prompt 📑",
                f"**{status_text}**\n```\n{active_prompt}\n```"
            )
            await interaction.response.send_message(embed=embed)
            return

        if prompt.strip().lower() in ("reset", "clear", "default"):
            await self.ai.prompts.delete_guild_prompt(guild_id)
            await interaction.response.send_message(
                embed=success_embed(
                    "System Prompt Reset",
                    "Cleared custom system prompt override. Default prompt restored."
                )
            )
            return

        # Save new override
        await self.ai.prompts.set_guild_prompt(
            guild_id=guild_id,
            prompt_text=prompt,
            updated_by=interaction.user.id
        )
        
        embed = success_embed(
            "System Prompt Updated",
            f"Successfully updated custom system prompt override for this server:\n```\n{prompt}\n```"
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="history", description="Show recent chat history for this channel.")
    @guild_only_command()
    async def history(self, interaction: discord.Interaction) -> None:
        """View conversation logs history with paginated navigation."""
        conv = await self.ai.get_conversation_history(interaction.channel_id, "channel")
        messages = conv.messages

        if not messages:
            await interaction.response.send_message(
                embed=info_embed("Conversation History", "No recent chat history in this channel.")
            )
            return

        # Split history messages into chunks of 10 items
        page_size = 10
        chunks = [messages[i:i + page_size] for i in range(0, len(messages), page_size)]
        embeds = []

        # Get aggregate usage stats for the conversation session
        total_p = sum(m.prompt_tokens for m in messages)
        total_c = sum(m.completion_tokens for m in messages)

        for idx, chunk in enumerate(chunks):
            desc = []
            for msg in chunk:
                icon = "👤" if msg.role == "user" else "🤖"
                prefix = "**User**" if msg.role == "user" else "**Assistant**"
                
                content_preview = msg.content
                if len(content_preview) > 120:
                    content_preview = content_preview[:117] + "..."
                
                desc.append(f"{icon} {prefix}: *{content_preview}*")

            embed = info_embed(
                f"Conversation History for #{interaction.channel.name}",
                "\n\n".join(desc)
            )
            embed.set_footer(
                text=f"Session total tokens: {total_p + total_c} (In: {total_p}, Out: {total_c}) | Page {idx + 1}/{len(chunks)}"
            )
            embeds.append(embed)

        view = PaginationView(interaction.user.id, embeds)
        await interaction.response.send_message(embed=embeds[0], view=view)
        view.message = await interaction.original_response()


async def setup(bot: commands.Bot) -> None:
    """Load the AICog into the bot."""
    await bot.add_cog(AICog(bot))
