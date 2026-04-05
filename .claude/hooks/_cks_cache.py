"""CKS result caching to reduce query overhead.

Session-level cache with TTL to avoid repeated CKS queries
for identical trigger phrases during a development session.

Uses file-based persistence to survive between hook subprocess calls.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any


class CKSCache:
    """Cache CKS query results with TTL and file persistence."""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize cache with time-to-live.

        Args:
            ttl_seconds: Cache entry expiration (default 1 hour)
        """
        self.cache_file = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state")) / "cks_cache.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk if available."""
        self._memory_cache: dict[str, tuple] = {}
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    data = json.load(f)
                    current_time = time.time()
                    # Filter expired entries
                    for key, (result_b64, ts) in data.items():
                        if current_time - ts < self.ttl:
                            self._memory_cache[key] = (result_b64, ts)
            except (OSError, json.JSONDecodeError):
                pass  # Start fresh

    def _save_cache(self) -> None:
        """Persist cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._memory_cache, f)
        except OSError:
            pass  # Fail silently

    def get(self, query: str) -> Any | None:
        """Get cached result if available and not expired.

        Args:
            query: Search query string

        Returns:
            Cached result or None if miss/expired
        """
        key = hashlib.md5(query.encode()).hexdigest()
        if key in self._memory_cache:
            result, ts = self._memory_cache[key]
            if time.time() - ts < self.ttl:
                self.hits += 1
                return result
            else:
                # Expired entry
                del self._memory_cache[key]
                self._save_cache()
        self.misses += 1
        return None

    def set(self, query: str, result: Any) -> None:
        """Cache a result.

        Args:
            query: Search query string
            result: Result to cache (must be JSON-serializable)
        """
        key = hashlib.md5(query.encode()).hexdigest()
        self._memory_cache[key] = (result, time.time())
        self._save_cache()

    def stats(self) -> str:
        """Return cache statistics.

        Returns:
            Formatted stats string
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return f"Cache: {self.hits} hits, {self.misses} misses ({hit_rate:.1f}% hit rate)"

    def clear(self) -> None:
        """Clear all cached results."""
        self._memory_cache.clear()
        self.hits = 0
        self.misses = 0
        if self.cache_file.exists():
            self.cache_file.unlink()


# Global cache instance (per session)
_cache = CKSCache(ttl_seconds=3600)


def get_cache() -> CKSCache:
    """Get the global cache instance."""
    return _cache


def maybe_clear_cache() -> None:
    """Clear cache if CLEAR_CKS_CACHE environment variable is set."""
    if os.environ.get('CLEAR_CKS_CACHE'):
        _cache.clear()
        print("[CKS] Cache cleared via environment variable")
