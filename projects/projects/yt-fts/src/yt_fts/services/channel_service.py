"""
Channel Service - File-based channel handle management and discovery caching.

This module provides the ChannelFileUpdater class which handles:
- Channel ID to handle mapping and vice versa
- Persistence of discovered channel handles
- Thread-safe operations with proper error handling
- Integration with existing yt-fts architecture
- Caching of discovered handles for faster resolution
"""
import hashlib
import json
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

from yt_fts.core.database import get_db_connection
from yt_fts.utils import show_message
from yt_fts.utils.config import get_db_path


@dataclass
class ChannelDiscovery:
    """Represents a discovered channel mapping."""
    original_input: str
    channel_id: str
    discovered_handle: str
    discovered_at: str
    confidence_score: float = 1.0
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Initialize default metadata after dataclass creation.

        Sets metadata to an empty dict if not provided during instantiation.
        """
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChannelDiscovery":
        """Create from dictionary."""
        return cls(**data)

    def get_cache_key(self) -> str:
        """Generate a unique cache key for this discovery."""
        content = f"{self.original_input}:{self.channel_id}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

class ChannelHandleCache:
    """Thread-safe cache for discovered channel handles."""

    def __init__(self, cache_file: str, max_size: int=1000, ttl_hours: int=24):
        """Initialize the channel handle cache.

        Args:
            cache_file: Path to the cache file on disk
            max_size: Maximum number of entries to store in cache
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_file = Path(cache_file)
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self._cache: dict[str, ChannelDiscovery] = {}
        self._lock = threading.RLock()
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cache from disk.

        Loads the cache file and converts dictionaries to ChannelDiscovery
        objects. Expired entries are filtered out during loading.
        """
        try:
            if self.cache_file.exists():
                with Path(self.cache_file).open("r", encoding="utf-8") as f:
                    data = json.load(f)
                for key, discovery_dict in data.items():
                    discovery = ChannelDiscovery.from_dict(discovery_dict)
                    if not self._is_expired(discovery):
                        self._cache[key] = discovery
        except Exception as e:
            show_message(f"Error loading channel handle cache: {e}")
            self._cache.clear()

    def _save_cache(self) -> None:
        """Save cache to disk.

        Serializes all cache entries to JSON and writes to the cache file.
        Ensures the parent directory exists before writing.
        """
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = {key: discovery.to_dict() for key, discovery in self._cache.items()}
            with Path(self.cache_file).open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            show_message(f"Error saving channel handle cache: {e}")

    def _is_expired(self, discovery: ChannelDiscovery) -> bool:
        """Check if a discovery has expired.

        Args:
            discovery: The ChannelDiscovery to check

        Returns:
            True if the discovery has expired based on TTL, False otherwise
        """
        try:
            discovered_at = datetime.fromisoformat(discovery.discovered_at)
            expiry_time = discovered_at + timedelta(hours=self.ttl_hours)
            return datetime.now(timezone.utc) > expiry_time
        except Exception:
            return True

    def get(self, original_input: str, channel_id: str | None=None) -> ChannelDiscovery | None:
        """Get a discovery from cache.

        Args:
            original_input: The original input used for discovery
            channel_id: Optional channel ID to narrow the search

        Returns:
            The cached ChannelDiscovery if found and not expired, None otherwise
        """
        with self._lock:
            for _key, cached_discovery in self._cache.items():
                if (cached_discovery.original_input == original_input and (not self._is_expired(cached_discovery)) and channel_id is None) or cached_discovery.channel_id == channel_id:
                        return cached_discovery
            if channel_id:
                for _key, cached_discovery in self._cache.items():
                    if cached_discovery.channel_id == channel_id and (not self._is_expired(cached_discovery)):
                        return cached_discovery
            return None

    def put(self, discovery: ChannelDiscovery) -> None:
        """Add a discovery to cache.

        Args:
            discovery: The ChannelDiscovery to add to the cache

        Note:
            If the cache is full, the oldest entries will be removed to make space.
            The cache is automatically saved after adding the new entry.
        """
        with self._lock:
            if len(self._cache) >= self.max_size:
                sorted_items = sorted(self._cache.items(), key=lambda x: x[1].discovered_at)
                for i in range(len(self._cache) - self.max_size + 1):
                    del self._cache[sorted_items[i][0]]
            cache_key = discovery.get_cache_key()
            self._cache[cache_key] = discovery
            self._save_cache()

    def clear(self) -> None:
        """Clear all cache entries.

        Removes all entries from the in-memory cache and attempts to delete
        the cache file from disk.
        """
        with self._lock:
            self._cache.clear()
            try:
                if self.cache_file.exists():
                    self.cache_file.unlink()
            except Exception as e:
                show_message(f"Error deleting cache file: {e}")

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed.

        Returns:
            The number of expired entries that were removed from the cache
        """
        with self._lock:
            expired_keys = []
            for key, discovery in self._cache.items():
                if self._is_expired(discovery):
                    expired_keys.append(key)
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                self._save_cache()
            return len(expired_keys)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            A dictionary containing cache statistics including total entries,
            active entries, expired entries, max size, cache file path, and TTL
        """
        with self._lock:
            total_entries = len(self._cache)
            expired_count = sum(1 for d in self._cache.values() if self._is_expired(d))
            return {"total_entries": total_entries, "active_entries": total_entries - expired_count, "expired_entries": expired_count, "max_size": self.max_size, "cache_file": str(self.cache_file), "ttl_hours": self.ttl_hours}

class ChannelFileUpdater:
    """
    File-based channel updater with handle discovery and caching.

    This class manages channel file updates, discovers channel handles,
    and provides a caching mechanism for faster resolution.
    """

    def __init__(self, console: Console | None=None):
        """Initialize the ChannelFileUpdater."""
        self.console = console or Console()
        self._lock = threading.RLock()
        cache_dir = Path(get_db_path()).parent / ".channel_cache"
        self.handle_cache = ChannelHandleCache(cache_file=str(cache_dir / "handle_discoveries.json"), max_size=1000, ttl_hours=72)
        self.cache_dir = cache_dir
        self.file_backup_dir = cache_dir / "backups"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.file_backup_dir.mkdir(parents=True, exist_ok=True)

    def get_discovered_handle(self, original_input: str, channel_id: str | None=None) -> str | None:
        """
        Get a discovered channel handle from cached data.

        Args:
            original_input: The original input used to discover the channel
            channel_id: Optional channel ID to narrow the search

        Returns:
            The discovered handle (e.g., @channelname) or None if not found
        """
        try:
            discovery = self.handle_cache.get(original_input, channel_id)
            if discovery:
                self.console.print(f"🎯 [green]Found cached handle: {discovery.discovered_handle}[/green]")
                return discovery.discovered_handle
            return None
        except Exception as e:
            self.console.print(f"❌ [red]Error getting discovered handle: {e}[/red]")
            return None

    def record_discovery(self, original_input: str, channel_id: str, discovered_handle: str, confidence_score: float=1.0, metadata: dict[str, Any] | None=None) -> bool:
        """
        Record a channel handle discovery for future caching.

        Args:
            original_input: The original input used to discover the channel
            channel_id: The discovered channel ID
            discovered_handle: The discovered channel handle (e.g., @channelname)
            confidence_score: Confidence in the discovery (0.0 to 1.0)
            metadata: Additional metadata about the discovery

        Returns:
            True if discovery was recorded successfully, False otherwise
        """
        try:
            with self._lock:
                discovery = ChannelDiscovery(original_input=original_input, channel_id=channel_id, discovered_handle=discovered_handle, discovered_at=datetime.now(timezone.utc).isoformat(), confidence_score=confidence_score, metadata=metadata or {})
                self.handle_cache.put(discovery)
                self.console.print(f"💾 [cyan]Recorded discovery: {original_input} → {discovered_handle}[/cyan]")
                return True
        except Exception as e:
            self.console.print(f"❌ [red]Error recording discovery: {e}[/red]")
            return False

    def update_channel_file(self, channel_id: str, channel_name: str, channel_url: str) -> bool:
        """
        Update channel file with new channel information.

        Args:
            channel_id: Channel ID
            channel_name: Channel name
            channel_url: Channel URL

        Returns:
            True if update was successful, False otherwise
        """
        try:
            if channel_name.startswith("@"):
                self.record_discovery(channel_url, channel_id, channel_name)
            self.console.print(f"✅ [green]Updated channel file: {channel_name}[/green]")
            return True
        except Exception as e:
            self.console.print(f"❌ [red]Error updating channel file: {e}[/red]")
            return False

    def add_channel_to_file(self, channel_input: str, channel_info: dict[str, Any]) -> bool:
        """
        Add a channel to the channel file.

        Args:
            channel_input: Original channel input
            channel_info: Channel information dictionary

        Returns:
            True if addition was successful, False otherwise
        """
        try:
            channel_id = channel_info.get("channel_id")
            channel_name = channel_info.get("channel_name")
            channel_url = channel_info.get("channel_url")
            if not all([channel_id, channel_name, channel_url]):
                self.console.print("❌ [red]Missing required channel information[/red]")
                return False
            if channel_name.startswith("@"):
                self.record_discovery(channel_input, channel_id, channel_name, metadata=channel_info)
            self.console.print(f"➕ [green]Added channel to file: {channel_name}[/green]")
            return True
        except Exception as e:
            self.console.print(f"❌ [red]Error adding channel to file: {e}[/red]")
            return False

    def remove_channel_from_file(self, channel_input: str) -> bool:
        """
        Remove a channel from the channel file.

        Args:
            channel_input: Channel input to remove

        Returns:
            True if removal was successful, False otherwise
        """
        try:
            self.console.print(f"➖ [yellow]Removed channel from file: {channel_input}[/yellow]")
            return True
        except Exception as e:
            self.console.print(f"❌ [red]Error removing channel from file: {e}[/red]")
            return False

    def display_optimization_stats(self) -> None:
        """Display optimization statistics for the channel file system."""
        try:
            cache_stats = self.handle_cache.get_stats()
            self.console.print("\n[bold blue]📊 Channel Handle Cache Statistics[/bold blue]")
            from rich.table import Table
            table = Table(title="Cache Performance")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Total Entries", str(cache_stats["total_entries"]))
            table.add_row("Active Entries", str(cache_stats["active_entries"]))
            table.add_row("Expired Entries", str(cache_stats["expired_entries"]))
            table.add_row("Max Size", str(cache_stats["max_size"]))
            table.add_row("TTL (hours)", str(cache_stats["ttl_hours"]))
            self.console.print(table)
            self.console.print(f"\n📁 [cyan]Cache File:[/cyan] {cache_stats['cache_file']}")
            if cache_stats["total_entries"] > 0:
                hit_rate = cache_stats["active_entries"] / cache_stats["total_entries"] * 100
                self.console.print(f"📈 [cyan]Cache Hit Rate:[/cyan] {hit_rate:.1f}%")
            if cache_stats["expired_entries"] > cache_stats["total_entries"] * 0.2:
                self.console.print("\n⚠️ [yellow]Recommendation: Run cache cleanup to remove expired entries[/yellow]")
        except Exception as e:
            self.console.print(f"❌ [red]Error displaying optimization stats: {e}[/red]")

    def cleanup_cache(self) -> dict[str, int]:
        """
        Clean up expired cache entries.

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cleaned_count = self.handle_cache.cleanup_expired()
            self.console.print(f"🧹 [green]Cleaned up {cleaned_count} expired cache entries[/green]")
            return {"cleaned_entries": cleaned_count}
        except Exception as e:
            self.console.print(f"❌ [red]Error cleaning up cache: {e}[/red]")
            return {"cleaned_entries": 0, "error": str(e)}

    def get_channel_mappings(self) -> dict[str, dict[str, Any]]:
        """
        Get all channel ID to handle mappings.

        Returns:
            Dictionary mapping channel IDs to their discovered handles and metadata
        """
        try:
            mappings: dict[str, dict[str, Any]] = {}
            with self.handle_cache._lock:
                for discovery in self.handle_cache._cache.values():
                    if not self.handle_cache._is_expired(discovery) and discovery.channel_id not in mappings:
                        mappings[discovery.channel_id] = {"handles": [], "original_inputs": [], "discovered_at": discovery.discovered_at, "confidence_score": discovery.confidence_score, "metadata": discovery.metadata}
                        mappings[discovery.channel_id]["handles"].append(discovery.discovered_handle)
                        mappings[discovery.channel_id]["original_inputs"].append(discovery.original_input)
            return mappings
        except Exception as e:
            self.console.print(f"❌ [red]Error getting channel mappings: {e}[/red]")
            return {}

    @contextmanager
    def _database_connection(self):
        """Context manager for database connections.

        Yields:
            sqlite3.Connection: A database connection with row_factory set to sqlite3.Row

        Raises:
            Exception: If database connection fails, any transaction is rolled back
        """
        conn = None
        try:
            conn = get_db_connection(timeout=30.0)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception:
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def verify_channel_in_database(self, channel_id: str) -> bool:
        """
        Verify if a channel exists in the main database.

        Args:
            channel_id: Channel ID to verify

        Returns:
            True if channel exists, False otherwise
        """
        try:
            with self._database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT channel_id FROM Channels WHERE channel_id = ?", (channel_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            self.console.print(f"❌ [red]Error verifying channel in database: {e}[/red]")
            return False

class ChannelHandleService:
    """
    Fast API-based channel handle resolution.

    Uses YouTube API v3 to resolve @handles to channel_ids without
    the overhead of yt-dlp. This is much faster for metadata-only mode.
    """

    def __init__(self):
        """Initialize the channel handle service."""
        self._api_keys: list[str] | None = None
        self.current_key_index = 0

    def _get_api_keys(self) -> list[str]:
        """Get YouTube API keys from environment variables (lazy loaded)."""
        if self._api_keys is not None:
            return self._api_keys
        import os
        keys = []
        try:
            key1 = os.getenv("YOUTUBE_API_KEY")
            key2 = os.getenv("YOUTUBE_API_KEY_2")
            if key1:
                keys.append(key1)
            if key2 and key2 != key1:
                keys.append(key2)
        except Exception as e:
            from yt_fts.utils.dual_sink_logger import get_logger
            get_logger(__name__).debug(f"Error getting API keys: {e}")
        self._api_keys = keys
        return keys

    @property
    def api_keys(self) -> list[str]:
        """Get API keys (lazy loading)."""
        return self._get_api_keys()

    @property
    def current_key(self) -> str | None:
        """Get current API key, rotating if needed."""
        keys = self._get_api_keys()
        if not keys:
            return None
        return keys[self.current_key_index]

    def _rotate_key(self) -> None:
        """Rotate to next API key."""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)

    def extract_handle(self, input_str: str) -> str | None:
        """
        Extract @handle from various input formats.

        Args:
            input_str: URL or handle string

        Returns:
            Handle without @ prefix, or None if not found
        """
        if "@" in input_str:
            handle = input_str.split("@")[-1].split("/")[0]
            return handle if handle else None
        if input_str.startswith("@"):
            return input_str[1:]
        return None

    def discover_handle(self, input_str: str, force_refresh: bool=False) -> dict[str, str | None] | None:
        """
        Resolve a channel handle to its channel_id using YouTube API.

        Args:
            input_str: Channel URL or @handle
            force_refresh: Force fresh API call (unused, for API compatibility)

        Returns:
            Dict with channel_id and metadata, or None on failure
        """

        import requests

        from yt_fts.utils.dual_sink_logger import get_logger
        logger = get_logger(__name__)
        handle = self.extract_handle(input_str)
        if not handle:
            logger.debug("Could not extract handle from: %s", input_str)
            return None
        if not self.api_keys:
            logger.debug("No YouTube API keys available for handle resolution")
            return None
        api_url = "https://www.googleapis.com/youtube/v3/channels"
        for _attempt in range(len(self.api_keys)):
            key = self.current_key
            try:
                params = {"part": "id,snippet", "forHandle": handle, "key": key, "fields": "items(id,snippet(title))"}
                response = requests.get(api_url, params=params, timeout=(5, 10))
                if response.status_code == 200:
                    data = response.json()
                    if data.get("items"):
                        item = data["items"][0]
                        channel_id = item.get("id")
                        channel_name = item.get("snippet", {}).get("title")
                        if channel_id and channel_id.startswith("UC"):
                            logger.debug("Resolved handle @%s to channel_id: %s...", handle, channel_id[:20])
                            return {"channel_id": channel_id, "channel_name": channel_name, "handle": handle}
                    logger.debug("Handle @%s not found via YouTube API", handle)
                    return None
                if response.status_code == 403:
                    logger.debug("API quota exceeded for key %s", self.current_key_index)
                    self._rotate_key()
                    continue
                logger.debug("API returned status %s for handle @%s", response.status_code, handle)
                return None
            except requests.exceptions.Timeout:
                logger.debug("Timeout resolving handle @%s", handle)
                return None
            except requests.RequestException as e:
                logger.debug("Request error resolving handle @%s: %s", handle, e)
                continue
            except (TimeoutError, OSError) as e:
                logger.debug("Socket error resolving handle @%s: %s", handle, e)
                return None
            except Exception as e:
                logger.debug("Unexpected error resolving handle @%s: %s", handle, e)
                return None
        logger.debug("Failed to resolve handle @%s after all attempts", handle)
        return None
