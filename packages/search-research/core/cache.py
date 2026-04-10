"""Query Cache - LRU cache for repeated search queries."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from collections import OrderedDict
from typing import Any

from .terminal_id import canonical_terminal_id


class QueryCache:
    """LRU cache for search queries with TTL.

    Uses a class-level registry so all QueryCache instances with the same
    terminal_id share the same cache storage. This ensures that within a
    terminal session, repeated QueryCache() instantiations hit the same cache.
    """

    # Class-level registry: terminal_id -> (cache_od, lock)
    _registry: dict[str, tuple[OrderedDict[str, dict[str, Any]], threading.Lock]] = {}
    _registry_lock = threading.Lock()

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 3600,  # Updated from 300 to 3600 (PERF-002)
    ):
        """Initialize query cache.

        Args:
            max_size: Maximum number of cached queries
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._terminal_id = canonical_terminal_id()

        # All instances with same terminal_id share cache + lock
        with QueryCache._registry_lock:
            if self._terminal_id not in QueryCache._registry:
                QueryCache._registry[self._terminal_id] = (
                    OrderedDict(),
                    threading.Lock(),
                )
            self._cache, self._lock = QueryCache._registry[self._terminal_id]

        self._hits = 0
        self._misses = 0
        self._start_cleanup_thread()

    def _start_cleanup_thread(self) -> None:
        """Start background thread to periodically remove expired entries."""
        def cleanup_loop() -> None:
            while True:
                time.sleep(60)  # Check every 60 seconds
                self._sweep_expired()

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    def _sweep_expired(self) -> None:
        """Remove all expired entries."""
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now - entry["timestamp"] >= self.ttl_seconds
            ]
            for key in expired_keys:
                del self._cache[key]

    def _hash_query(self, query: str, **kwargs: Any) -> str:
        """Create hash from query string and options."""
        # Normalize query
        normalized = query.strip().lower()

        # Include options in hash
        options = sorted(kwargs.items())
        key_data = json.dumps({"q": normalized, "opts": options, "tid": self._terminal_id}, sort_keys=True)
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def get(self, query: str, **kwargs: Any) -> list[dict[str, Any]] | None:
        """
        Get cached results for query.

        Args:
            query: Search query string
            **kwargs: Additional query options

        Returns:
            Cached results or None if not found/expired
        """
        key = self._hash_query(query, **kwargs)

        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            entry = self._cache[key]

            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry["results"]

    def set(self, query: str, results: list[dict[str, Any]], **kwargs: Any) -> None:
        """
        Cache results for query.

        Args:
            query: Search query string
            results: Search results to cache
            **kwargs: Additional query options
        """
        key = self._hash_query(query, **kwargs)

        with self._lock:
            # Enforce size limit
            if len(self._cache) >= self.max_size:
                # Remove oldest (first) item
                self._cache.popitem(last=False)

            self._cache[key] = {
                "results": results,
                "timestamp": time.time(),
                "query": query,
                "kwargs": kwargs,
            }

    def invalidate(self) -> None:
        """Invalidate all cache entries."""
        with self._lock:
            self._cache.clear()

    def clear(self) -> None:
        """Clear all cache entries (alias for invalidate)."""
        self.invalidate()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "ttl_seconds": self.ttl_seconds,
            }
