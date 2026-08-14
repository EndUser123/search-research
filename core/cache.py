"""Query Cache - LRU cache for repeated search queries."""

from __future__ import annotations

import hashlib
import json
import math
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .terminal_id import canonical_terminal_id


@dataclass
class CachedQuery:
    """Cached query with embedding and result."""

    query: str
    embedding: list[float]
    result: dict[str, Any]
    cached_from: str  # ISO timestamp
    timestamp: float  # epoch seconds for TTL

    def to_jsonl(self) -> str:
        """Serialize to JSON line format."""
        return json.dumps(asdict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CachedQuery":
        """Create CachedQuery from dictionary."""
        return cls(
            query=data["query"],
            embedding=data["embedding"],
            result=data["result"],
            cached_from=data["cached_from"],
            timestamp=data["timestamp"],
        )


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class EmbeddingCache:
    """L2 embedding-based cache with cosine similarity search."""

    def __init__(self, log_dir: str = "logs", ttl_seconds: int = 3600, initial_threshold: float = 0.95):
        """Initialize embedding cache.

        Args:
            log_dir: Directory for cache log files
            ttl_seconds: Time-to-live for cache entries
            initial_threshold: Starting similarity threshold (0.0 to 1.0)
        """
        self.ttl_seconds = ttl_seconds
        self._threshold = initial_threshold
        self._entries: list[CachedQuery] = []
        self._hits = 0
        self._queries = 0
        self.log_dir = log_dir
        self._cache_path = Path(log_dir) / "query_cache.jsonl"
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Create log directory if it doesn't exist."""
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

    @property
    def threshold(self) -> float:
        """Get current similarity threshold."""
        return self._threshold

    def _cosine_sim(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        return _cosine_sim(a, b)

    def find_similar(self, embedding: list[float]) -> "CachedQuery | None":
        """Find most similar cached query above threshold.

        Args:
            embedding: Query embedding to search for

        Returns:
            CachedQuery if similarity >= threshold, None otherwise
        """
        self._queries += 1

        # Filter out expired entries
        now = time.time()
        valid_entries = [
            entry for entry in self._entries
            if now - entry.timestamp < self.ttl_seconds
        ]

        # Find entry with highest similarity
        best_entry: "CachedQuery | None" = None
        best_similarity = -1.0

        for entry in valid_entries:
            sim = self._cosine_sim(embedding, entry.embedding)
            if sim > best_similarity:
                best_similarity = sim
                best_entry = entry

        # Check if best match meets threshold
        if best_entry is not None and best_similarity >= self._threshold:
            self._hits += 1
            result = best_entry
        else:
            result = None

        # Adaptive threshold logic (AT-1)
        if self._queries >= 100:
            hit_rate = self._hits / self._queries
            if hit_rate < 0.05:
                # Lower threshold by 0.05, floor at 0.80
                # Round to 2 decimal places to avoid floating point drift
                new_threshold = max(0.80, round(self._threshold - 0.05, 2))
                if new_threshold != self._threshold:
                    self._threshold = new_threshold
                    self._log_threshold_change()
                # Reset counters
                self._queries = 0
                self._hits = 0

        return result

    def store(self, query: str, embedding: list[float], result: dict[str, Any]) -> None:
        """Store a query with its embedding and result.

        Args:
            query: Search query string
            embedding: Query embedding vector
            result: Search results to cache
        """
        cached_query = CachedQuery(
            query=query,
            embedding=embedding,
            result=result,
            cached_from=datetime.now(timezone.utc).isoformat(),
            timestamp=time.time(),
        )
        self._entries.append(cached_query)
        self._append_to_log(cached_query)

    def _append_to_log(self, entry: "CachedQuery") -> None:
        """Append entry to JSONL log file. OSError-immune."""
        try:
            with open(self._cache_path, "a") as f:
                f.write(entry.to_jsonl() + "\n")
        except OSError:
            pass

    def _log_threshold_change(self) -> None:
        """Log threshold change to query_cache.jsonl."""
        try:
            meta_entry = {
                "_threshold": self._threshold,
                "_event": "threshold_change",
                "timestamp": time.time(),
            }
            with open(self._cache_path, "a") as f:
                f.write(json.dumps(meta_entry) + "\n")
        except OSError:
            pass


class QueryCache:
    """LRU cache for search queries with TTL.

    Uses a class-level registry so all QueryCache instances with the same
    terminal_id share the same cache storage. This ensures that within a
    terminal session, repeated QueryCache() instantiations hit the same cache.
    """

    # Class-level registry: terminal_id -> (cache_od, lock, cleanup_started)
    _registry: dict[str, tuple[OrderedDict[str, dict[str, Any]], threading.Lock, bool]] = {}
    _registry_lock = threading.Lock()
    _MAX_REGISTRY_SIZE = 16

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
            # Evict oldest entries if registry is full
            if len(QueryCache._registry) >= QueryCache._MAX_REGISTRY_SIZE:
                oldest_keys = list(QueryCache._registry.keys())[:len(QueryCache._registry) - QueryCache._MAX_REGISTRY_SIZE + 1]
                for key in oldest_keys:
                    del QueryCache._registry[key]
            if self._terminal_id not in QueryCache._registry:
                QueryCache._registry[self._terminal_id] = (
                    OrderedDict(),
                    threading.Lock(),
                    False,  # cleanup_started flag
                )
            self._cache, self._lock, self._cleanup_started = QueryCache._registry[self._terminal_id]

        self._hits = 0
        self._misses = 0
        self._start_cleanup_thread()

    def _start_cleanup_thread(self) -> None:
        """Start background thread to periodically remove expired entries."""
        # Only start cleanup thread once per terminal_id
        with QueryCache._registry_lock:
            if self._cleanup_started:
                return
            QueryCache._registry[self._terminal_id] = (
                self._cache,
                self._lock,
                True,  # Mark cleanup as started
            )

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
            if time.time() - entry["timestamp"] >= self.ttl_seconds:
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
