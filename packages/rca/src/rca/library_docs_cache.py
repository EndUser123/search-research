"""
Library Documentation Cache for Auto-Research

Lightweight caching system for external library documentation.
Stores fetched docs with timestamps for intelligent refresh.

This is Phase 2 (Option B) - CKS-aware caching.

Cache Schema:
{
    "library_docs": {
        "yt-dlp": {
            "content": "...documentation text...",
            "sources": ["url1", "url2"],
            "timestamp": "2025-12-27T02:20:00",
            "version": "2025.12.27",
            "fetched_at": 1735257200
        }
    }
}
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CachedDoc:
    """A cached library documentation entry."""

    library: str
    content: str
    sources: list[str]
    timestamp: str  # ISO format
    fetched_at: float  # Unix timestamp
    version: str = ""  # Optional version info

    @property
    def age_hours(self) -> float:
        """Age of cache entry in hours."""
        return (time.time() - self.fetched_at) / 3600

    def is_fresh(self, max_age_hours: float = 24) -> bool:
        """Check if cache entry is still fresh."""
        return self.age_hours < max_age_hours


class LibraryDocsCache:
    """Cache for library documentation with timestamp-based refresh."""

    DEFAULT_CACHE_DIR = "P:/__csf/.data/rca"
    DEFAULT_MAX_AGE_HOURS = 24
    CACHE_FILE = "library_docs_cache.json"

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        max_age_hours: float = DEFAULT_MAX_AGE_HOURS,
    ) -> None:
        """
        Initialize the library docs cache.

        PERF-003: Cache is loaded once at initialization and stored in memory.
        File is only reloaded if modified externally (detected via mtime).

        Args:
            cache_dir: Directory for cache file (default: __csf/.data/rca)
            max_age_hours: Hours before considering cache stale (default: 24)

        """
        if cache_dir is None:
            cache_dir = self.DEFAULT_CACHE_DIR

        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / self.CACHE_FILE
        self.max_age_hours = max_age_hours

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # PERF-003: Load existing cache once and track mtime
        self._cache: dict[str, dict[str, Any]] = self._load_cache()
        self._cache_file_mtime = self._get_file_mtime()

    def _get_file_mtime(self) -> float:
        """Get the modification time of the cache file."""
        if self.cache_file.exists():
            return self.cache_file.stat().st_mtime
        return 0.0

    def _load_cache(self) -> dict[str, dict[str, Any]]:
        """Load cache from disk."""
        try:
            return json.loads(self.cache_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load cache: %s", e)
            return {"library_docs": {}, "metadata": {"version": "1.0"}}

    def _save_cache(self) -> bool:
        """Save cache to disk."""
        try:
            self.cache_file.write_text(
                json.dumps(self._cache, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            # Update mtime after successful save
            self._cache_file_mtime = self._get_file_mtime()
        except OSError:
            logger.exception("Failed to save cache")
            return False
        else:
            return True

    def _reload_if_changed(self) -> bool:
        """
        Reload cache from disk if file has been modified externally.

        PERF-003: Only reload if mtime has changed since last load.
        This allows multiple processes to share the cache file.

        Returns:
            True if cache was reloaded, False otherwise

        """
        current_mtime = self._get_file_mtime()

        # No change or file doesn't exist yet
        if current_mtime == 0 or current_mtime <= self._cache_file_mtime:
            return False

        # File has been modified, reload
        try:
            new_cache = json.loads(self.cache_file.read_text(encoding="utf-8"))

            # Merge with existing in-memory cache
            # (In-memory writes take precedence over external changes)
            if "library_docs" not in new_cache:
                new_cache["library_docs"] = {}

            # Merge external entries that we don't have in memory
            external_libs = set(new_cache.get("library_docs", {}).keys())
            memory_libs = set(self._cache.get("library_docs", {}).keys())

            for lib in external_libs - memory_libs:
                self._cache.setdefault("library_docs", {})[lib] = new_cache["library_docs"][lib]

            # Update mtime
            self._cache_file_mtime = current_mtime
            logger.debug("Cache reloaded: %d new entries from external changes", len(external_libs - memory_libs))
            return True

        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to reload cache: %s", e)
            return False

    def get(self, library: str) -> CachedDoc | None:
        """
        Get cached documentation for a library.

        Args:
            library: Library name (e.g., "yt-dlp", "fastapi")

        Returns:
            CachedDoc if found and fresh, None otherwise

        """
        # Normalize library name
        lib_key = library.lower().replace("_", "-")

        if lib_key not in self._cache.get("library_docs", {}):
            return None

        doc_data = self._cache["library_docs"][lib_key]

        # Parse into CachedDoc
        doc = CachedDoc(
            library=lib_key,
            content=doc_data.get("content", ""),
            sources=doc_data.get("sources", []),
            timestamp=doc_data.get("timestamp", ""),
            fetched_at=doc_data.get("fetched_at", 0),
            version=doc_data.get("version", ""),
        )

        # Check if fresh
        if doc.is_fresh(self.max_age_hours):
            logger.debug("Cache HIT for %s (%.1fh old)", lib_key, doc.age_hours)
            return doc
        logger.debug("Cache STALE for %s (%.1fh old)", lib_key, doc.age_hours)
        return None

    def set(
        self,
        library: str,
        content: str,
        sources: list[str],
        version: str = "",
    ) -> bool:
        """
        Store documentation for a library.

        Args:
            library: Library name
            content: Documentation text
            sources: List of source URLs
            version: Optional version info

        Returns:
            True if saved successfully

        """
        # Normalize library name
        lib_key = library.lower().replace("_", "-")

        doc = CachedDoc(
            library=lib_key,
            content=content,
            sources=sources,
            timestamp=datetime.now(tz=UTC).isoformat(),
            fetched_at=time.time(),
            version=version,
        )

        if "library_docs" not in self._cache:
            self._cache["library_docs"] = {}

        self._cache["library_docs"][lib_key] = asdict(doc)
        return self._save_cache()

    def invalidate(self, library: str) -> bool:
        """
        Invalidate cache entry for a library.

        Args:
            library: Library name to invalidate

        Returns:
            True if invalidated

        """
        lib_key = library.lower().replace("_", "-")

        if lib_key in self._cache.get("library_docs", {}):
            del self._cache["library_docs"][lib_key]
            return self._save_cache()

        return False

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats

        """
        docs = self._cache.get("library_docs", {})
        total = len(docs)

        # Count fresh vs stale
        fresh = 0
        stale = 0
        total_size_kb = 0

        for doc_data in docs.values():
            fetched_at = doc_data.get("fetched_at", 0)
            age_hours = (time.time() - fetched_at) / 3600

            if age_hours < self.max_age_hours:
                fresh += 1
            else:
                stale += 1

            # Estimate size
            content_len = len(doc_data.get("content", ""))
            total_size_kb += content_len / 1024

        return {
            "total_entries": total,
            "fresh_entries": fresh,
            "stale_entries": stale,
            "estimated_size_kb": round(total_size_kb, 1),
            "max_age_hours": self.max_age_hours,
            "cache_file": str(self.cache_file),
        }

    def clear_stale(self) -> int:
        """
        Remove stale entries from cache.

        Returns:
            Number of entries removed

        """
        docs = self._cache.get("library_docs", {})
        removed = 0

        keys_to_remove = []
        for lib_key, doc_data in docs.items():
            fetched_at = doc_data.get("fetched_at", 0)
            age_hours = (time.time() - fetched_at) / 3600

            if age_hours >= self.max_age_hours:
                keys_to_remove.append(lib_key)
                removed += 1

        for key in keys_to_remove:
            del self._cache["library_docs"][key]

        if removed > 0:
            self._save_cache()

        return removed

    def clear_all(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if cleared

        """
        self._cache["library_docs"] = {}
        return self._save_cache()


def get_library_cache(max_age_hours: float = 24) -> LibraryDocsCache:
    """
    Get the default library docs cache instance.

    Args:
        max_age_hours: Hours before considering cache stale

    Returns:
        LibraryDocsCache instance

    """
    if (
        not hasattr(get_library_cache, "_cache")
        or get_library_cache._cache.max_age_hours != max_age_hours  # noqa: SLF001
    ):
        get_library_cache._cache = LibraryDocsCache(max_age_hours=max_age_hours)  # noqa: SLF001

    return get_library_cache._cache  # noqa: SLF001


def _test() -> None:
    """Run built-in tests."""
    import shutil
    import tempfile

    # Use temp directory for testing
    temp_dir = tempfile.mkdtemp()
    cache = LibraryDocsCache(cache_dir=temp_dir, max_age_hours=24)

    print("Library Docs Cache Tests")
    print("=" * 60)

    # Test 1: Cache miss
    result = cache.get("nonexistent")
    print(f"Test 1 - Cache miss: {'PASS' if result is None else 'FAIL'}")

    # Test 2: Set and get
    cache.set(
        "test-lib",
        "Test documentation content",
        ["https://example.com/docs"],
        version="1.0.0")

    result = cache.get("test-lib")
    print(
        f"Test 2 - Set/Get: {'PASS' if result and result.content.startswith('Test') else 'FAIL'}"
    )

    # Test 3: Normalization (underscore ≡ hyphen)
    result = cache.get("test_lib")  # underscore variant
    print(f"Test 3 - Normalization: {'PASS' if result is not None else 'FAIL'}")

    # Test 4: Stats
    stats = cache.get_stats()
    print(f"Test 4 - Stats: {stats['total_entries']} entries")

    # Test 5: Clear stale
    removed = cache.clear_stale()
    print(f"Test 5 - Clear stale: {removed} removed")

    # Cleanup
    shutil.rmtree(temp_dir)
    print("\nAll tests completed!")


if __name__ == "__main__":
    _test()
