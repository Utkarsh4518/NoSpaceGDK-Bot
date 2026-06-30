"""Verification Service with basic anti-bot captcha challenge modal."""

import random
from typing import Any, Optional
import discord
from models.verification import VerificationSettingsModel
from repository.welcome_repository import WelcomeRepository
from services.base_service import BaseService
from services.cache_service import CacheService
from utils.logger import logger

class VerificationService(BaseService):
    """Manages server verification settings and captcha gatekeeping."""

    def __init__(self, bot: Any, welcome_repo: WelcomeRepository, cache_service: CacheService) -> None:
        self.bot = bot
        self.repo = welcome_repo
        self.cache = cache_service

    async def get_settings(self, guild_id: int) -> Optional[VerificationSettingsModel]:
        """Fetch verification settings with caching."""
        cache_key = f"verification_settings:{guild_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        settings = await self.repo.get_verification_settings(guild_id)
        if settings:
            self.cache.set(cache_key, settings)
        return settings

    async def save_settings(
        self,
        guild_id: int,
        role_id: Optional[int],
        channel_id: Optional[int],
        enabled: bool,
        type_: str = "button"
    ) -> VerificationSettingsModel:
        """Save settings and invalidate cache."""
        settings = await self.repo.save_verification_settings(
            guild_id=guild_id,
            role_id=role_id,
            channel_id=channel_id,
            enabled=enabled,
            type_=type_
        )
        self.cache.set(f"verification_settings:{guild_id}", settings)
        return settings

    async def send_verification_panel(self, guild: discord.Guild, channel_id: int, role_id: int) -> None:
        """Send verification message panel with the Verify button."""
        channel = guild.get_channel(channel_id)
        if not channel:
            channel = await guild.fetch_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            raise ValueError("Verification channel must be a text channel.")

        role = guild.get_role(role_id)
        if not role:
            raise ValueError("Target verification role not found.")

        # Invalidate/update settings
        await self.save_settings(guild.id, role_id, channel_id, enabled=True)

        embed = discord.Embed(
            title="Server Verification Gate 🛡️",
            description=(
                "Welcome to the server!\n"
                "To prevent bot raids, you must complete a basic captcha challenge "
                "before getting full server permissions.\n\n"
                "Click the **Verify** button below to begin."
            ),
            color=discord.Color.gold()
        )

        view = VerificationLaunchView(self, role_id)
        await channel.send(embed=embed, view=view)
        logger.info(f"VerificationService: Setup panel in channel {channel.name} ({channel.id}) for role {role.name}")


class VerificationLaunchView(discord.ui.View):
    """View containing the 'Verify' button sent in verification channels."""

    def __init__(self, service: VerificationService, role_id: int) -> None:
        super().__init__(timeout=None)
        self.service = service
        self.role_id = role_id

    @discord.ui.button(label="Verify", emoji="✅", custom_id="verify_btn", style=discord.ButtonStyle.success)
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Open dynamic verification captcha modal
        modal = VerificationCaptchaModal(interaction.guild, self.role_id)
        await interaction.response.send_modal(modal)


class VerificationCaptchaModal(discord.ui.Modal, title="Anti-Bot Captcha Check"):
    """Modal displaying a dynamic random math challenge."""

    def __init__(self, guild: discord.Guild, role_id: int) -> None:
        super().__init__()
        self.guild = guild
        self.role_id = role_id

        # Generate challenge
        self.num1 = random.randint(1, 9)
        self.num2 = random.randint(1, 9)
        self.correct_answer = self.num1 + self.num2

        # Create input
        self.answer_input = discord.ui.TextInput(
            label=f"What is {self.num1} + {self.num2} = ?",
            style=discord.TextStyle.short,
            placeholder="Type your numeric answer here...",
            required=True
        )
        self.add_item(self.answer_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_input = self.answer_input.value.strip()

        try:
            val = int(user_input)
        except ValueError:
            await interaction.followup.send("Invalid input. You must type a valid number.", ephemeral=True)
            return

        if val != self.correct_answer:
            await interaction.followup.send(
                f"❌ Incorrect answer. ({self.num1} + {self.num2} = {self.correct_answer}). Please try again.",
                ephemeral=True
            )
            return

        # Grant role
        role = self.guild.get_role(self.role_id)
        if not role:
            await interaction.followup.send("❌ Setup error: Verification role no longer exists.", ephemeral=True)
            return

        if role >= self.guild.me.top_role:
            await interaction.followup.send(
                "❌ Permission error: Bot's highest role is lower than target verification role. Contact admin.",
                ephemeral=True
            )
            return

        try:
            await interaction.user.add_roles(role, reason="Passed anti-bot captcha verification.")
            await interaction.followup.send("✅ Verification successful! You have been granted access to the server.", ephemeral=True)
            logger.info(f"VerificationService: User {interaction.user.name} ({interaction.user.id}) successfully verified in guild {self.guild.id}")
        except discord.Forbidden:
            await interaction.followup.send("❌ Error: Missing permission to assign verification role.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)
            logger.error(f"VerificationService: Failed to assign role: {e}")
