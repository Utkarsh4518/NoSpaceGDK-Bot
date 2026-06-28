"""Custom Discord bot class for NoSpaceFGK.

Defines the specialized commands.Bot subclass that manages extension loading,
slash command tree synchronization, latency logging, and graceful shutdown.
"""

import datetime
from pathlib import Path
from typing import Any
import discord
from discord.ext import commands
from config import BotConfig
from utils.constants import COGS_DIR
from utils.exceptions import BotStartupError, CogLoadError, ExtensionError
from utils.logger import logger, log_exception, log_shutdown


class NoSpaceFGKBot(commands.Bot):
    """Custom Bot class containing setup hook, cog loader, and lifecycle handling.

    Extends commands.Bot to incorporate custom configuration and logging integration.
    """

    def __init__(self, config: BotConfig, *args: Any, **kwargs: Any) -> None:
        """Initialize the custom bot instance.

        Args:
            config: The validated read-only BotConfig data.
            args: Positional arguments forwarded to commands.Bot.
            kwargs: Keyword arguments forwarded to commands.Bot.
        """
        # Configure intents (enable members and messages for standard operations)
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=config.bot_prefix,
            intents=intents,
            application_id=config.client_id,
            *args,
            **kwargs
        )
        self.config: BotConfig = config
        self.start_time: datetime.datetime | None = None

    async def setup_hook(self) -> None:
        """Coroutine executed during bot startup to load cogs and sync commands.

        Initializes dynamic loading of all extensions in the cogs directory and the events package.
        """
        self.start_time = datetime.datetime.now(datetime.timezone.utc)

        # 1. Load the events extension package first
        await self._load_events()

        # 2. Dynamic loading of cogs from the cogs directory
        await self._load_cogs()

        # 3. Synchronize slash command tree
        await self.sync_commands()

    async def _load_events(self) -> None:
        """Import and register the events listener extension.

        Raises:
            ExtensionError: If the events package fails to load.
        """
        try:
            await self.load_extension("events")
            logger.info("Events package successfully loaded.")
        except Exception as e:
            log_exception(e, "Failed to load events package:")
            raise ExtensionError(f"Failed to load events package: {e}") from e

    async def _load_cogs(self) -> None:
        """Scan the cogs directory and load all valid python files as extensions.

        Raises:
            CogLoadError: If any of the cog extensions fail to load.
        """
        if not COGS_DIR.exists() or not COGS_DIR.is_dir():
            logger.warning(f"Cogs directory '{COGS_DIR}' not found. Skipping cog loading.")
            return

        for filepath in COGS_DIR.glob("*.py"):
            if filepath.name.startswith("_"):
                continue

            extension_name = f"cogs.{filepath.stem}"
            try:
                await self.load_extension(extension_name)
                logger.info(f"Cog loaded: {extension_name}")
            except Exception as e:
                log_exception(e, f"Failed to load cog extension {extension_name}:")
                raise CogLoadError(f"Failed to load cog {extension_name}: {e}") from e

    async def sync_commands(self) -> None:
        """Synchronize the command tree globally or to a development guild.

        Uses the DEVELOPMENT_GUILD_ID configuration to sync commands instantly
        during development, avoiding global rate limits.
        """
        try:
            if self.config.development_guild_id:
                guild = discord.Object(id=self.config.development_guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Command tree synchronized to dev guild {self.config.development_guild_id}.")
            else:
                await self.tree.sync()
                logger.info("Command tree synchronized globally.")
        except Exception as e:
            log_exception(e, "Failed to synchronize application commands:")

    async def reload_all_extensions(self) -> None:
        """Reload all loaded cogs and event listeners.

        This allows runtime updates to be applied without restarting the bot process.
        """
        logger.info("Reloading all extensions...")

        # Reload events extension
        try:
            await self.reload_extension("events")
            logger.info("Events package reloaded.")
        except Exception as e:
            log_exception(e, "Failed to reload events package:")

        # Scan and reload cogs
        for filepath in COGS_DIR.glob("*.py"):
            if filepath.name.startswith("_"):
                continue
            extension_name = f"cogs.{filepath.stem}"
            try:
                if extension_name in self.extensions:
                    await self.reload_extension(extension_name)
                    logger.info(f"Cog reloaded: {extension_name}")
                else:
                    await self.load_extension(extension_name)
                    logger.info(f"Cog loaded: {extension_name}")
            except Exception as e:
                log_exception(e, f"Failed to reload cog {extension_name}:")

    async def close(self) -> None:
        """Override close to log shutdown operations cleanly."""
        logger.info("Closing Discord connection...")
        await super().close()
        log_shutdown()
