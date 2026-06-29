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

        next_item = await self.queue.get_next()
        if not next_item:
            self._state = PlayerState.IDLE
            self.dispatch("QueueEmpty")
            logger.info(f"Player state: Queue is empty in Guild {self.guild_id}.")
            return

        self._current_track = next_item
        self._state = PlayerState.PLAYING
        logger.info(f"Player state: Started playing '{next_item.track.title}' (UUID: {next_item.uuid}) in Guild {self.guild_id}.")
        self.dispatch("TrackStart", next_item)

    async def pause(self) -> None:
        """Pause the current playback."""
        if self._state == PlayerState.PLAYING:
            self._state = PlayerState.PAUSED
            logger.info(f"Player state: Paused playback in Guild {self.guild_id}.")
            self.dispatch("TrackPause", self._current_track)

    async def resume(self) -> None:
        """Resume paused playback."""
        if self._state == PlayerState.PAUSED:
            self._state = PlayerState.PLAYING
            logger.info(f"Player state: Resumed playback in Guild {self.guild_id}.")
            self.dispatch("TrackResume", self._current_track)

    async def stop(self) -> None:
        """Stop playback and clear current track status."""
        self._state = PlayerState.STOPPED
        self._current_track = None
        logger.info(f"Player state: Stopped playback in Guild {self.guild_id}.")
        self.dispatch("TrackEnd", None)

    async def skip(self) -> None:
        """Skip current track and advance queue."""
        if not self._current_track:
            return

        skipped_track = self._current_track
        logger.info(f"Player state: Skipped track '{skipped_track.track.title}' in Guild {self.guild_id}.")
        self.dispatch("TrackSkip", skipped_track)

        # Advance queue
        await self.play()

    async def destroy(self) -> None:
        """Halt all playback operations and clear connections."""
        self._state = PlayerState.DESTROYED
        await self.stop()
        await self.queue.clear()
        await self.voice.leave_channel()
        logger.info(f"Player state: Destroyed player instance in Guild {self.guild_id}.")
        self.dispatch("PlayerDestroyed")
