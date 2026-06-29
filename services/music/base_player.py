"""Base Music Player coordinator class for NoSpaceFGK bot.

Binds voice managers, queue managers, and audio controls. Emits internal lifecycle events.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
import discord
from models.music import PlayerState, QueueItem
from services.music.queue_manager import QueueManager
from services.music.voice_manager import VoiceManager
from services.music.audio_manager import AudioManager
from utils.logger import logger


class BaseMusicPlayer:
    """Orchestrates track playback queues, volume adjustments, and voice channels."""

    def __init__(self, bot: discord.Client, guild_id: int) -> None:
        """Initialize the base player.

        Args:
            bot: The Discord Client instance.
            guild_id: Guild snowflake ID.
        """
        self.bot: discord.Client = bot
        self.guild_id: int = guild_id

        self.queue: QueueManager = QueueManager()
        self.voice: VoiceManager = VoiceManager(bot, guild_id)
        self.audio: AudioManager = AudioManager()

        self._state: PlayerState = PlayerState.IDLE
        self._current_track: Optional[QueueItem] = None
        self._start_time: Optional[float] = None
        self._paused_at: Optional[float] = None
        self._paused_duration: float = 0.0

        self._listeners: Dict[str, List[Callable[..., Any]]] = {
            "TrackStart": [],
            "TrackEnd": [],
            "TrackPause": [],
            "TrackResume": [],
            "TrackSkip": [],
            "QueueEmpty": [],
            "QueueUpdated": [],
            "PlayerDestroyed": []
        }

    def add_listener(self, event_name: str, callback: Callable[..., Any]) -> None:
        """Register a callback for internal playback events.

        Args:
            event_name: Internal event string.
            callback: Async callable hook.
        """
        if event_name in self._listeners:
            self._listeners[event_name].append(callback)

    def dispatch(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """Trigger event callbacks asynchronously in the background.

        Args:
            event_name: The event identifier string.
            args: Positional event args.
            kwargs: Keyword event args.
        """
        if event_name not in self._listeners:
            return

        logger.debug(f"Player Event: Dispatching event '{event_name}' in Guild {self.guild_id}.")
        for listener in self._listeners[event_name]:
            asyncio.create_task(listener(*args, **kwargs))

    @property
    def state(self) -> PlayerState:
        """Retrieve current execution state of the player session."""
        return self._state

    @property
    def current_track(self) -> Optional[QueueItem]:
        """Retrieve active playing track."""
        return self._current_track

    async def play(self) -> None:
        """Start or resume playback of the queue."""
        if self._state == PlayerState.PAUSED:
            await self.resume()
            return

        if not self.voice.is_connected:
            self._state = PlayerState.DISCONNECTED
            logger.warning(f"Player state: Play failed in Guild {self.guild_id} (Not connected to voice).")
            return

        if self.voice.voice_client and self.voice.voice_client.is_playing():
            self.voice.voice_client.stop()

        self._state = PlayerState.BUFFERING
        next_item = await self.queue.get_next()
        if not next_item:
            self._state = PlayerState.IDLE
            self._current_track = None
            self.dispatch("QueueEmpty")
            logger.info(f"Player state: Queue is empty in Guild {self.guild_id}.")
            return

        self._current_track = next_item
        logger.info(f"Player state: Fetching stream for '{next_item.track.title}'...")

        try:
            from services.music.provider_manager import ProviderManager
            provider_manager = self.bot.container.get(ProviderManager)
            provider = provider_manager.get_provider(next_item.track.provider)
            if not provider:
                raise ValueError(f"No registered provider found for '{next_item.track.provider}'.")

            stream_url = await provider.get_stream(next_item.track)
            audio_source = self.audio.create_audio_source(stream_url)

            self._start_time = asyncio.get_running_loop().time()
            self._paused_duration = 0.0
            self._paused_at = None
            self._state = PlayerState.PLAYING
            self.voice.voice_client.play(
                audio_source,
                after=lambda e: self._on_track_end(e)
            )

            logger.info(f"Player state: Playing '{next_item.track.title}' (UUID: {next_item.uuid}) in Guild {self.guild_id}.")
            self.dispatch("TrackStart", next_item)
        except Exception as e:
            logger.error(f"Player state: Failed to play '{next_item.track.title}': {e}", exc_info=True)
            self._state = PlayerState.IDLE
            self.bot.loop.call_soon_threadsafe(
                asyncio.create_task,
                self._advance_queue()
            )

    def _on_track_end(self, error: Optional[Exception]) -> None:
        """Invoked by VoiceClient when a track finishes playing."""
        if error:
            logger.error(f"Voice Client: Playback finished with error in Guild {self.guild_id}: {error}")

        self.bot.loop.call_soon_threadsafe(
            asyncio.create_task,
            self._advance_queue()
        )

    async def _advance_queue(self) -> None:
        """Handle track completion logic and advance to the next track."""
        old_track = self._current_track
        if old_track:
            self.dispatch("TrackEnd", old_track)
            try:
                from repositories.history_repository import HistoryRepository
                history_repo = self.bot.container.get(HistoryRepository)
                await history_repo.add_to_history(
                    self.guild_id,
                    old_track.track.uuid,
                    old_track.added_by
                )
            except Exception as ex:
                logger.error(f"Player state: History logger write failed: {ex}")

        if self._state == PlayerState.DESTROYED:
            return

        self._state = PlayerState.IDLE
        self._current_track = None
        await self.play()

    async def pause(self) -> None:
        """Pause the current playback."""
        if self._state == PlayerState.PLAYING and self.voice.voice_client:
            self.voice.voice_client.pause()
            self._paused_at = asyncio.get_running_loop().time()
            self._state = PlayerState.PAUSED
            logger.info(f"Player state: Paused playback in Guild {self.guild_id}.")
            self.dispatch("TrackPause", self._current_track)

    async def resume(self) -> None:
        """Resume paused playback."""
        if self._state == PlayerState.PAUSED and self.voice.voice_client:
            self.voice.voice_client.resume()
            if self._paused_at is not None:
                self._paused_duration += asyncio.get_running_loop().time() - self._paused_at
                self._paused_at = None
            self._state = PlayerState.PLAYING
            logger.info(f"Player state: Resumed playback in Guild {self.guild_id}.")
            self.dispatch("TrackResume", self._current_track)

    async def stop(self) -> None:
        """Stop playback and clear current track status."""
        if self.voice.voice_client and (self.voice.voice_client.is_playing() or self.voice.voice_client.is_paused()):
            self.voice.voice_client.stop()
        self._state = PlayerState.STOPPED
        self._current_track = None
        logger.info(f"Player state: Stopped playback in Guild {self.guild_id}.")

    async def skip(self) -> None:
        """Skip current track and advance queue."""
        if not self._current_track:
            return

        skipped_track = self._current_track
        logger.info(f"Player state: Skipped track '{skipped_track.track.title}' in Guild {self.guild_id}.")
        self.dispatch("TrackSkip", skipped_track)

        if self.voice.voice_client and (self.voice.voice_client.is_playing() or self.voice.voice_client.is_paused()):
            self.voice.voice_client.stop()
        else:
            await self._advance_queue()

    async def destroy(self) -> None:
        """Halt all playback operations and clear connections."""
        self._state = PlayerState.DESTROYED
        await self.stop()
        await self.queue.clear()
        await self.voice.leave_channel()
        logger.info(f"Player state: Destroyed player instance in Guild {self.guild_id}.")
        self.dispatch("PlayerDestroyed")

    @property
    def position(self) -> float:
        """Get elapsed playback position of the current track in seconds."""
        if not self._start_time:
            return 0.0
        loop = asyncio.get_event_loop()
        if self._state == PlayerState.PAUSED and self._paused_at:
            return self._paused_at - self._start_time - self._paused_duration
        return loop.time() - self._start_time - self._paused_duration

