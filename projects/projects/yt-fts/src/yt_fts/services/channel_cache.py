"""
Channel Caching Service

Multi-tier caching for channel resolution results and metadata.
Provides memory, database, and optional Redis caching layers.
"""

import json
import sqlite3
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from yt_fts.utils import show_message
from yt_fts.utils.config import get_db_path


@dataclass
class CacheEntry:
    """Cache entry for channel resolution data."""
    channel_id: str
    channel_url: str | None
    channel_name: str | None
    resolution_method: str
    created_at: str
    last_accessed: str
    access_count: int
    ttl_seconds: int
    metadata: dict[str, Any]

    def __post_init__(self):
        """
        Initialize metadata dict if None (dataclass post-processor).
        """
        if self.metadata is None:
            self.metadata = {}

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl_seconds == 0:  # Never expires
            return False

        expiry_time = datetime.fromisoformat(self.created_at) + timedelta(seconds=self.ttl_seconds)
        return datetime.now(timezone.utc) > expiry_time

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        return cls(**data)


class MemoryCache:
    """In-memory LRU cache for fast channel resolution."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize the in-memory LRU cache.

        Args:
            max_size: Maximum number of entries to store
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []
        self._lock = threading.Lock()

    def get(self, key: str) -> CacheEntry | None:
        """Get entry from memory cache (thread-safe)."""
        with self._lock:
            entry = self._cache.get(key)
            if entry:
                if entry.is_expired():
                    self.delete(key)
                    return None

                # Update access tracking
                entry.last_accessed = datetime.now(timezone.utc).isoformat()
                entry.access_count += 1

                # Move to end of access order (LRU)
                if key in self._access_order:
                    self._access_order.remove(key)
                    self._access_order.append(key)

        return entry

    def put(self, key: str, entry: CacheEntry) -> None:
        """Put entry into memory cache (thread-safe)."""
        with self._lock:
            # Remove oldest entry if cache is full
            if len(self._cache) >= self.max_size and key not in self._cache:
                if self._access_order:
                    oldest_key = self._access_order.pop(0)
                    if oldest_key in self._cache:
                        del self._cache[oldest_key]

            # Update access order
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            self._cache[key] = entry

    def delete(self, key: str) -> None:
        """Delete entry from memory cache (thread-safe)."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)

    def clear(self) -> None:
        """Clear all entries (thread-safe)."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class DatabaseCache:
    """Persistent cache using SQLite database."""

    def __init__(self, db_path: str | None = None):
        """
        Initialize the persistent database cache.

        Args:
            db_path: Path to SQLite database file (uses default if None)
        """
        self.db_path = db_path or self._get_default_db_path()
        self._init_database()

    def _get_default_db_path(self) -> str:
        """Get default database path for channel cache."""
        # Use same directory as main database
        main_db_path = get_db_path()
        cache_dir = Path(main_db_path).parent
        cache_db_path = cache_dir / "channel_cache.db"
        return str(cache_db_path)

    def _init_database(self) -> None:
        """Initialize cache database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS channel_cache (
                    key TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    channel_url TEXT,
                    channel_name TEXT,
                    resolution_method TEXT,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    ttl_seconds INTEGER DEFAULT 3600,
                    metadata TEXT
                )
            """)

            # Create indexes separately
            conn.execute("CREATE INDEX IF NOT EXISTS idx_channel_cache_key ON channel_cache(key)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_channel_cache_channel_id ON channel_cache(channel_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_channel_cache_last_accessed ON channel_cache(last_accessed)")
            conn.commit()

    def get(self, key: str) -> CacheEntry | None:
        """Get entry from database cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM channel_cache WHERE key = ?
                """, (key,))

                row = cursor.fetchone()
                if row:
                    # Handle empty datetime strings from old cache entries
                    created_at = row["created_at"] or datetime.now(timezone.utc).isoformat()
                    last_accessed = row["last_accessed"] or datetime.now(timezone.utc).isoformat()

                    entry = CacheEntry(
                        channel_id=row["channel_id"],
                        channel_url=row["channel_url"],
                        channel_name=row["channel_name"],
                        resolution_method=row["resolution_method"],
                        created_at=created_at,
                        last_accessed=last_accessed,
                        access_count=row["access_count"],
                        ttl_seconds=row["ttl_seconds"],
                        metadata=json.loads(row["metadata"] or "{}")
                    )

                    if entry.is_expired():
                        self.delete(key)
                        return None

                    # Update access tracking
                    self._update_access(key)
                    return entry

        except Exception as e:
            show_message(f"Database cache get error: {e}")

        return None

    def put(self, key: str, entry: CacheEntry) -> None:
        """Put entry into database cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT OR REPLACE INTO channel_cache
                    (key, channel_id, channel_url, channel_name, resolution_method,
                     created_at, last_accessed, access_count, ttl_seconds, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    key, entry.channel_id, entry.channel_url, entry.channel_name,
                    entry.resolution_method, entry.created_at, entry.last_accessed,
                    entry.access_count, entry.ttl_seconds, json.dumps(entry.metadata)
                ))
                conn.commit()

        except Exception as e:
            show_message(f"Database cache put error: {e}")

    def delete(self, key: str) -> None:
        """Delete entry from database cache."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM channel_cache WHERE key = ?", (key,))
                conn.commit()

        except Exception as e:
            show_message(f"Database cache delete error: {e}")

    def _update_access(self, key: str) -> None:
        """Update access tracking for entry."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE channel_cache
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE key = ?
                """, (datetime.now(timezone.utc).isoformat(), key))
                conn.commit()

        except Exception as e:
            show_message(f"Database cache update error: {e}")

    def cleanup_expired(self) -> int:
        """Remove expired entries from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Find expired entries
                cursor.execute("""
                    DELETE FROM channel_cache
                    WHERE datetime(last_accessed) < datetime('now', '-' || ttl_seconds || ' seconds')
                """)

                deleted_count = cursor.rowcount
                conn.commit()
                return deleted_count

        except Exception as e:
            show_message(f"Database cache cleanup error: {e}")
            return 0

    def clear(self) -> None:
        """Clear all entries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM channel_cache")
                conn.commit()

        except Exception as e:
            show_message(f"Database cache clear error: {e}")


class ChannelCache:
    """
    Multi-tier channel caching service.

    Cache hierarchy:
    1. Memory cache (fastest, limited size)
    2. Database cache (persistent, larger size)
    3. Optional Redis cache (distributed, future)
    """

    def __init__(self,
                 memory_cache_size: int = 1000,
                 default_ttl: int = 3600,
                 enable_database: bool = True):
        """
        Initialize the hierarchical channel cache.

        Args:
            memory_cache_size: Maximum entries for in-memory cache
            default_ttl: Default time-to-live in seconds
            enable_database: Whether to enable persistent database cache
        """
        self.memory_cache = MemoryCache(memory_cache_size, default_ttl)
        self.database_cache = DatabaseCache() if enable_database else None
        self.default_ttl = default_ttl

    def get(self, key: str) -> CacheEntry | None:
        """Get entry from cache (memory first, then database)."""
        # Try memory cache first
        entry = self.memory_cache.get(key)
        if entry:
            return entry

        # Try database cache
        if self.database_cache:
            entry = self.database_cache.get(key)
            if entry:
                # Promote to memory cache
                self.memory_cache.put(key, entry)
                return entry

        return None

    def put(self, key: str, entry: CacheEntry) -> None:
        """Put entry into all cache layers."""
        self.memory_cache.put(key, entry)

        if self.database_cache:
            self.database_cache.put(key, entry)

    def delete(self, key: str) -> None:
        """Delete entry from all cache layers."""
        self.memory_cache.delete(key)

        if self.database_cache:
            self.database_cache.delete(key)

    def clear(self) -> None:
        """Clear all cache layers."""
        self.memory_cache.clear()

        if self.database_cache:
            self.database_cache.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "memory_cache_size": self.memory_cache.size(),
            "memory_cache_max_size": self.memory_cache.max_size,
            "database_cache_enabled": self.database_cache is not None
        }

        if self.database_cache:
            try:
                with sqlite3.connect(self.database_cache.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM channel_cache")
                    stats["database_cache_size"] = cursor.fetchone()[0]
            except Exception:
                stats["database_cache_size"] = "unknown"

        return stats

    def cleanup(self) -> dict[str, int]:
        """Clean up expired entries."""
        stats = {"memory_cleaned": 0, "database_cleaned": 0}

        # Memory cache cleanup happens automatically (LRU)
        self.memory_cache.size()

        # Database cache cleanup
        if self.database_cache:
            stats["database_cleaned"] = self.database_cache.cleanup_expired()

        return stats

    # UnifiedChannelProcessor integration methods
    async def get_channel_info(self, channel_id: str) -> Any | None:
        """
        Get channel information from cache.
        This method is for compatibility with UnifiedChannelProcessor.
        """
        # Try to get from cache using channel_id as key
        entry = self.get(channel_id)
        if entry:
            # Convert CacheEntry to ChannelInfo-like object
            from .unified_channel_processor import ChannelInfo
            return ChannelInfo(
                channel_id=entry.channel_id,
                name=entry.channel_name,
                url=entry.channel_url,
                handle=None,  # Not stored in cache
                subscriber_count=None,  # Not stored in cache
                video_count=None,  # Not stored in cache
                description=None,  # Not stored in cache
                thumbnail_url=None  # Not stored in cache
            )
        return None

    async def cache_channel_info(self, channel_id: str, channel_info: Any) -> None:
        """
        Cache channel information.
        This method is for compatibility with UnifiedChannelProcessor.
        """
        # Convert ChannelInfo to CacheEntry
        entry = CacheEntry(
            channel_id=channel_id,
            channel_url=getattr(channel_info, "url", None),
            channel_name=getattr(channel_info, "name", None),
            resolution_method="unified_processor",
            created_at=datetime.now(timezone.utc).isoformat(),
            last_accessed=datetime.now(timezone.utc).isoformat(),
            access_count=1,
            ttl_seconds=self.default_ttl,
            metadata={
                "subscriber_count": getattr(channel_info, "subscriber_count", None),
                "video_count": getattr(channel_info, "video_count", None),
                "description": getattr(channel_info, "description", None),
                "thumbnail_url": getattr(channel_info, "thumbnail_url", None),
                "handle": getattr(channel_info, "handle", None)
            }
        )

        # Store in cache
        self.put(channel_id, entry)

    async def cache_resolution(self, input_value: str, channel_id: str) -> None:
        """
        Cache input resolution mapping.
        Maps various input formats (@handle, URL, name) to channel_id.
        """
        # Create a cache entry for the resolution
        entry = CacheEntry(
            channel_id=channel_id,
            channel_url=None,  # Will be resolved later if needed
            channel_name=None,  # Will be resolved later if needed
            resolution_method="input_mapping",
            created_at=datetime.now(timezone.utc).isoformat(),
            last_accessed=datetime.now(timezone.utc).isoformat(),
            access_count=1,
            ttl_seconds=self.default_ttl,
            metadata={"input_type": "resolution_mapping"}
        )

        # Store the mapping
        self.put(input_value, entry)
