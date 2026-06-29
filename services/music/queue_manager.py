"""Thread-safe music QueueManager for NoSpaceFGK.

Manages FIFO track storage, history trails, repeat policies, and queue configurations
under thread-safe AsyncIO locks.
"""

import asyncio
import random
import uuid
import datetime
from typing import Any, Dict, List, Optional
from models.music import Track, QueueItem, RepeatMode
from utils.logger import logger


class QueueManager:
    """Manages playback track queues for a specific player session."""

    def __init__(self, max_length: int = 1000) -> None:
        """Initialize the queue manager.

        Args:
            max_length: Limit of elements inside the queue.
        """
        self.max_length: int = max_length
        self._queue: List[QueueItem] = []
        self._history: List[QueueItem] = []
        self._repeat_mode: RepeatMode = RepeatMode.NONE
        self._lock: asyncio.Lock = asyncio.Lock()

    async def add_track(self, track: Track, user_id: int) -> QueueItem:
        """Append a track to the end of the queue (FIFO).

        Args:
            track: Track details model.
            user_id: Discord Snowflake ID of requesting user.

        Returns:
            The created QueueItem.

        Raises:
            ValueError: If queue size exceeds max limit.
        """
        async with self._lock:
            if len(self._queue) >= self.max_length:
                raise ValueError("Queue length limit exceeded.")

            item = QueueItem(
                uuid=str(uuid.uuid4()),
                track=track,
                added_by=user_id,
                added_at=datetime.datetime.now(datetime.timezone.utc)
            )
            self._queue.append(item)
            logger.info(f"Queue operation: Added track '{track.title}' to queue (UUID: {item.uuid}).")
            return item

    async def insert_track(self, track: Track, user_id: int, position: int) -> QueueItem:
        """Insert track at a specific index.

        Args:
            track: Track model.
            user_id: Requesting user.
            position: Index position.

        Returns:
            The QueueItem.
        """
        async with self._lock:
            if len(self._queue) >= self.max_length:
                raise ValueError("Queue length limit exceeded.")

            item = QueueItem(
                uuid=str(uuid.uuid4()),
                track=track,
                added_by=user_id,
                added_at=datetime.datetime.now(datetime.timezone.utc)
            )
            pos = max(0, min(position, len(self._queue)))
            self._queue.insert(pos, item)
            logger.info(f"Queue operation: Inserted track '{track.title}' at position {pos}.")
            return item

    async def move_track(self, from_index: int, to_index: int) -> bool:
        """Move a queue item.

        Args:
            from_index: Origin index.
            to_index: Destination index.

        Returns:
            True if moved, False if index out of bounds.
        """
        async with self._lock:
            q_len = len(self._queue)
            if not (0 <= from_index < q_len) or not (0 <= to_index < q_len):
                return False

            item = self._queue.pop(from_index)
            self._queue.insert(to_index, item)
            logger.info(f"Queue operation: Moved track from index {from_index} to {to_index}.")
            return True

    async def remove_track(self, index_or_uuid: Any) -> Optional[QueueItem]:
        """Remove a track by index or UUID.

        Args:
            index_or_uuid: Integer index or String UUID.

        Returns:
            The removed QueueItem, or None.
        """
        async with self._lock:
            if isinstance(index_or_uuid, int):
                if 0 <= index_or_uuid < len(self._queue):
                    item = self._queue.pop(index_or_uuid)
                    logger.info(f"Queue operation: Removed track at index {index_or_uuid}.")
                    return item
            elif isinstance(index_or_uuid, str):
                for idx, item in enumerate(self._queue):
                    if item.uuid == index_or_uuid:
                        self._queue.pop(idx)
                        logger.info(f"Queue operation: Removed track with UUID {index_or_uuid}.")
                        return item
            return None

    async def get_next(self) -> Optional[QueueItem]:
        """Pop and retrieve the next track to play based on RepeatMode.

        Returns:
            The next QueueItem, or None if empty.
        """
        async with self._lock:
            if not self._queue:
                return None

            current_item = self._queue.pop(0)
            self._history.append(current_item)

            if len(self._history) > 100:
                self._history.pop(0)

            if self._repeat_mode == RepeatMode.ALL:
                new_item = QueueItem(
                    uuid=str(uuid.uuid4()),
                    track=current_item.track,
                    added_by=current_item.added_by,
                    added_at=datetime.datetime.now(datetime.timezone.utc)
                )
                self._queue.append(new_item)
            elif self._repeat_mode == RepeatMode.ONE:
                new_item = QueueItem(
                    uuid=str(uuid.uuid4()),
                    track=current_item.track,
                    added_by=current_item.added_by,
                    added_at=datetime.datetime.now(datetime.timezone.utc)
                )
                self._queue.insert(0, new_item)

            return current_item

    async def shuffle(self) -> None:
        """Shuffle the current upcoming queue items randomly."""
        async with self._lock:
            random.shuffle(self._queue)
            logger.info("Queue operation: Queue shuffled.")

    async def clear(self) -> None:
        """Clear all entries in the queue."""
        async with self._lock:
            self._queue.clear()
            logger.info("Queue operation: Queue cleared.")

    async def set_repeat_mode(self, mode: RepeatMode) -> None:
        """Set repeat policy.

        Args:
            mode: The RepeatMode Enum policy.
        """
        async with self._lock:
            self._repeat_mode = mode
            logger.info(f"Queue operation: Repeat mode updated to {mode.name}.")

    @property
    def repeat_mode(self) -> RepeatMode:
        """Access current repeat policy."""
        return self._repeat_mode

    @property
    def length(self) -> int:
        """Get queue length."""
        return len(self._queue)

    @property
    def queue(self) -> List[QueueItem]:
        """Return a read-only list of upcoming items."""
        return list(self._queue)

    @property
    def history(self) -> List[QueueItem]:
        """Return a read-only list of played history items."""
        return list(self._history)

    async def serialize(self) -> List[Dict[str, Any]]:
        """Serialize upcoming queue tracks.

        Returns:
            JSON-compatible list of dictionaries.
        """
        async with self._lock:
            serialized = []
            for item in self._queue:
                serialized.append({
                    "uuid": item.uuid,
                    "added_by": item.added_by,
                    "added_at": item.added_at.isoformat(),
                    "track": {
                        "uuid": item.track.uuid,
                        "title": item.track.title,
                        "artist": item.track.artist,
                        "duration": item.track.duration,
                        "thumbnail": item.track.thumbnail,
                        "provider": item.track.provider,
                        "url": item.track.url,
                        "requested_by": item.track.requested_by,
                        "isrc": item.track.isrc,
                        "metadata": item.track.metadata
                    }
                })
            return serialized
