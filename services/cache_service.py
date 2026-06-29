"""In-memory Cache service with custom TTL, stats tracking, and logs.

Emulates basic key-value operations for future Redis migration compatibility.
"""

import time
from typing import Any, Dict, Optional
from services.base_service import BaseService
from utils.logger import logger


class CacheService(BaseService):
    """TTL-backed temporary dictionary cache with hits/misses analytics."""

    def __init__(self, default_ttl: float) -> None:
        """Initialize the cache service.

        Args:
            default_ttl: Expiration duration fallback in seconds.
        """
        self.default_ttl: float = default_ttl
        self._store: Dict[str, Dict[str, Any]] = {}
        self._hits: int = 0
        self._misses: int = 0

    def get(self, key: str) -> Optional[Any]:
        """Fetch a value by key. Clears key automatically if expired.

        Args:
            key: Cached identifier string.

        Returns:
            The associated cached value or None.
        """
        if key not in self._store:
            self._misses += 1
            logger.debug(f"[CACHE MISS] Key: '{key}'")
            return None

        entry = self._store[key]
        if time.time() > entry["expires_at"]:
            del self._store[key]
            self._misses += 1
            logger.debug(f"[CACHE MISS] Key: '{key}' (Expired)")
            return None

        self._hits += 1
        logger.debug(f"[CACHE HIT] Key: '{key}'")
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Save a value with custom or default TTL.

        Args:
            key: Target identifier.
            value: Data to cache.
            ttl: Custom expiration seconds (optional).
        """
        chosen_ttl = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + chosen_ttl
        self._store[key] = {
            "value": value,
            "expires_at": expires_at
        }
        logger.debug(f"[CACHE SET] Key: '{key}' with TTL {chosen_ttl}s")

    def delete(self, key: str) -> bool:
        """Manually invalidate/evict a cache key.

        Args:
            key: Cached identifier.

        Returns:
            True if key existed and was deleted, False otherwise.
        """
        if key in self._store:
            del self._store[key]
            logger.debug(f"[CACHE DELETE] Key: '{key}' evicted.")
            return True
        return False

    def clear(self) -> None:
        """Wipe all keys from cache store."""
        self._store.clear()
        logger.debug("[CACHE CLEAR] Cache store completely cleared.")

    @property
    def stats(self) -> Dict[str, int]:
        """Retrieve telemetry measurements of cache performance.

        Returns:
            Dictionary containing hits count, misses count, and active cache size.
        """
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._store)
        }
