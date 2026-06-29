"""Custom Discord bot class for NoSpaceFGK.

Defines the specialized commands.Bot subclass that manages extension loading,
slash command tree synchronization, latency logging, database lifecycle,
and lightweight dependency injection setups.
"""

import datetime
from pathlib import Path
from typing import Any
import discord
from discord.ext import commands
from config import BotConfig
from database.connection import DatabaseManager
from services.service_container import ServiceContainer
from utils.constants import COGS_DIR
from utils.exceptions import BotStartupError, CogLoadError, ExtensionError
from utils.logger import logger, log_exception, log_shutdown


class NoSpaceFGKBot(commands.Bot):
    """Custom Bot class containing setup hook, cog loader, and lifecycle handling.

    Extends commands.Bot to incorporate configuration, logging, database connections,
    and a dependency injection service container.
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
        self.tree.on_error = self.on_tree_error

        # Infrastructure placeholders
        self.container: ServiceContainer | None = None
        self.db: DatabaseManager | None = None

    async def on_interaction(self, interaction: discord.Interaction) -> None:
        """Fires on every interaction received.

        Injects the start time for tracking interaction latency.
        """
        if interaction.type == discord.InteractionType.application_command:
            import time
            interaction.extras["start_time"] = time.perf_counter()
        await self.process_application_commands(interaction)

    async def on_tree_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError
    ) -> None:
        """Handle slash command execution errors globally.

        Logs failure latency, user context, and exception details. Maps exceptions
        to custom user-facing embeds.
        """
        import time
        from utils.logger import log_command
        from utils.embeds import error_embed

        start_time = interaction.extras.get("start_time")
        execution_time = time.perf_counter() - start_time if start_time else 0.0

        command_name = interaction.command.name if interaction.command else "Unknown"

        # Log command failure context
        log_command(
            user_id=interaction.user.id,
            guild_id=interaction.guild.id if interaction.guild else None,
            channel_id=interaction.channel.id if interaction.channel else None,
            command_name=command_name,
            execution_time=execution_time,
            status="FAILED",
            exception=error
        )

        log_exception(error, f"Slash command '{command_name}' failed:")

        # Parse error type for user feedback
        embed_title = "Command Error"
        embed_desc = "An unexpected error occurred while processing your command."

        if isinstance(error, discord.app_commands.CommandOnCooldown):
            embed_title = "Command on Cooldown"
            embed_desc = f"This command is on cooldown. Please try again in {error.retry_after:.2f} seconds."
        elif isinstance(error, discord.app_commands.MissingPermissions):
            embed_title = "Missing Permissions"
            missing_perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed_desc = f"You do not have the required permissions to execute this command: {missing_perms}"
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            embed_title = "Bot Missing Permissions"
            missing_perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed_desc = f"The bot does not have the required permissions to execute this command: {missing_perms}"
        elif isinstance(error, discord.app_commands.CheckFailure):
            embed_title = "Permission Denied"
            error_str = str(error)
            if "is_owner_predicate" in error_str:
                embed_desc = "This command is restricted to bot owners only."
            elif "is_premium_predicate" in error_str:
                embed_desc = "This command is restricted to premium subscribers only."
            else:
                embed_desc = "You do not meet the requirements to execute this command."

        # Send response safely
        embed = error_embed(title=embed_title, description=embed_desc)
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
        except discord.HTTPException:
            pass

    async def setup_hook(self) -> None:
        """Coroutine executed during bot startup to load cogs and sync commands.

        Initializes dynamic loading of all extensions in the cogs directory and the events package.
        """
        self.start_time = datetime.datetime.now(datetime.timezone.utc)

        # 1. Initialize Database & Run Migrations
        self.db = DatabaseManager(self.config.database_path)
        await self.db.connect()

        from database.migration import MigrationRunner
        from database.seed import seed_database

        migration_runner = MigrationRunner(self.db)
        await migration_runner.run_migrations()

        # Seed initial defaults
        await seed_database(self.db, self.config.development_guild_id)

        # 2. Setup Dependency Injection (DI) Container & Register Services
        from services import (
            ConfigService, CacheService, LoggingService, ResponseService, BotService, MusicService
        )
        from services.music import (
            PlayerManager, ProviderManager, TrackManager
        )
        from repositories import (
            GuildRepository, UserRepository, SettingsRepository, UsageRepository,
            MusicRepository, PlaylistRepository, HistoryRepository
        )

        container = ServiceContainer()

        # Core Config & Cache singletons
        container.register(ConfigService, lambda: ConfigService(self.config))
        container.register(CacheService, lambda: CacheService(float(self.config.cache_ttl)))

        # Repositories (injecting active DatabaseManager)
        container.register(GuildRepository, lambda: GuildRepository(self.db))
        container.register(UserRepository, lambda: UserRepository(self.db))
        container.register(SettingsRepository, lambda: SettingsRepository(self.db))
        container.register(UsageRepository, lambda: UsageRepository(self.db))
        container.register(MusicRepository, lambda: MusicRepository(self.db))
        container.register(PlaylistRepository, lambda: PlaylistRepository(self.db))
        container.register(HistoryRepository, lambda: HistoryRepository(self.db))

        # Providers Manager setup
        def make_provider_manager() -> ProviderManager:
            pm = ProviderManager()
            from providers import YouTubeProvider, SpotifyProvider, SoundCloudProvider
            pm.register_provider("youtube", YouTubeProvider())
            pm.register_provider("spotify", SpotifyProvider())
            pm.register_provider("soundcloud", SoundCloudProvider())
            return pm

        container.register(ProviderManager, make_provider_manager)

        # Player lifecycle managers
        container.register(PlayerManager, lambda: PlayerManager(self))
        container.register(TrackManager, lambda: TrackManager(
            music_repo=container.get(MusicRepository),
            cache_service=container.get(CacheService)
        ))

        # Services
        container.register(LoggingService, lambda: LoggingService(
            container.get(UsageRepository)
        ))
        container.register(ResponseService, lambda: ResponseService())
        container.register(BotService, lambda: BotService(
            guild_repo=container.get(GuildRepository),
            user_repo=container.get(UserRepository),
            settings_repo=container.get(SettingsRepository),
            cache_service=container.get(CacheService)
        ))
        container.register(MusicService, lambda: MusicService(
            player_manager=container.get(PlayerManager),
            provider_manager=container.get(ProviderManager),
            track_manager=container.get(TrackManager),
            playlist_repo=container.get(PlaylistRepository),
            history_repo=container.get(HistoryRepository)
        ))

        self.container = container

        # 3. Load the events extension package first
        await self._load_events()

        # 4. Dynamic loading of cogs from the cogs directory
        await self._load_cogs()

        # 5. Synchronize slash command tree
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
        """Synchronize the command tree to a development guild if configured.

        If no development guild is configured, warns that global sync must be performed
        manually to prevent hitting rate limits during bot startup.
        """
        try:
            if self.config.development_guild_id:
                guild = discord.Object(id=self.config.development_guild_id)
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
                logger.info(f"Command tree synchronized to dev guild {self.config.development_guild_id}.")
            else:
                logger.warning(
                    "Automatic command sync skipped. No DEVELOPMENT_GUILD_ID was provided. "
                    "Global command tree must be synchronized manually (e.g. via a /sync command) "
                    "to prevent rate limits."
                )
        except Exception as e:
            log_exception(e, "Failed to synchronize application commands:")

    async def sync_tree(self, guild_id: int | None = None) -> None:
        """Synchronize application commands either globally or to a specific guild.

        This helper can be invoked by owner commands to trigger manual synchronization.

        Args:
            guild_id: The ID of the guild to sync commands to, or None for global sync.
        """
        try:
            if guild_id:
                guild = discord.Object(id=guild_id)
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synchronized {len(synced)} commands to guild {guild_id}.")
            else:
                synced = await self.tree.sync()
                logger.info(f"Synchronized {len(synced)} commands globally.")
        except Exception as e:
            log_exception(e, f"Failed to sync command tree (guild_id={guild_id}):")
            raise

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
        """Override close to log shutdown operations cleanly and close database handles."""
        logger.info("Closing Discord connection...")
        await super().close()
        if self.container:
            try:
                player_manager = self.container.get(PlayerManager)
                await player_manager.clean_all_players()
            except Exception as e:
                logger.error(f"Error cleaning player sessions on close: {e}")
        if self.db:
            await self.db.disconnect()
        log_shutdown()

