#!/usr/bin/env python3
"""
PRD Registry with Lazy Loading and Caching

Provides efficient on-demand loading of PRD documents with intelligent caching
to minimize memory usage and startup time for large PRD collections.

Author: Claude Code
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import logging
import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .parser import ParsedPRD, PRDParser, PRDValidationError
except ImportError:
    from parser import ParsedPRD, PRDParser, PRDValidationError

logger = logging.getLogger(__name__)


@dataclass
class PRDCacheEntry:
    """A cached PRD with metadata."""

    prd: ParsedPRD
    loaded_at: datetime
    last_accessed: datetime
    access_count: int = 0
    file_hash: str = ""

    def touch(self) -> None:
        """Update last accessed timestamp and increment access count."""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return (datetime.now() - self.loaded_at).total_seconds()

    def idle_seconds(self) -> float:
        """Get time since last access in seconds."""
        return (datetime.now() - self.last_accessed).total_seconds()


@dataclass
class RegistryStats:
    """Statistics for PRD registry operations."""

    total_prds: int = 0
    loaded_prds: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_load_time: float = 0.0
    avg_load_time: float = 0.0

    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate (0.0 to 1.0)."""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0


class PRDRegistry:
    """
    Registry for lazy-loading and caching PRD documents.

    Features:
    - Lazy loading: PRDs loaded only when requested
    - LRU cache: Least recently used eviction when cache is full
    - TTL cache: Time-based expiration of cached entries
    - Thread-safe: All operations protected by locks
    - File watching: Detects changes and reloads modified PRDs
    - Statistics: Track cache performance and usage patterns

    Usage:
        registry = PRDRegistry(
            prd_paths=["P:/projects/*/docs/PRD.md"],
            cache_size=50,
            ttl_seconds=3600
        )

        # Discover available PRDs (doesn't load them)
        registry.discover()

        # Load specific PRD on-demand
        prd = registry.get("yt_sync")

        # List all PRD names
        names = registry.list_prds()

        # Get cache statistics
        stats = registry.get_stats()
    """

    def __init__(
        self,
        prd_paths: list[str] | None = None,
        cache_size: int = 100,
        ttl_seconds: float | None = None,
        enable_file_watching: bool = True,
        base_path: str | None = None,
        include_tsk_directory: bool = True,
    ):
        """Initialize the PRD registry.

        Args:
            prd_paths: List of glob patterns to find PRD files
            cache_size: Maximum number of PRDs to cache in memory
            ttl_seconds: Time-to-live for cache entries (None = no expiration)
            enable_file_watching: Check file modification times on load
            base_path: Base path for resolving relative paths
            include_tsk_directory: If True, include active TSK directory in search paths
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.prd_paths = list(prd_paths) if prd_paths else []
        self.cache_size = cache_size
        self.ttl_seconds = ttl_seconds
        self.enable_file_watching = enable_file_watching
        self.include_tsk_directory = include_tsk_directory

        # Add TSK directory to search paths if enabled (FIX: PRDs belong in TSK, not __csf/docs/)
        if include_tsk_directory:
            tsk_path = self._get_active_tsk_directory()
            if tsk_path:
                # Add both PRD.md and prd.md variants
                self.prd_paths.append(str(tsk_path / "PRD.md"))
                self.prd_paths.append(str(tsk_path / "prd.md"))
                logger.debug(f"Added TSK directory to PRD search paths: {tsk_path}")

        # Cache storage
        self._cache: dict[str, PRDCacheEntry] = {}
        self._prd_files: dict[str, Path] = {}  # name -> file path mapping

        # Thread safety
        self._lock = threading.RLock()

        # Parser instance
        self.parser = PRDParser(base_path=str(self.base_path))

        # Statistics
        self.stats = RegistryStats()

        # File modification tracking
        self._file_mtimes: dict[str, float] = {}

        logger.info(
            f"PRDRegistry initialized: cache_size={cache_size}, "
            f"ttl={ttl_seconds}, file_watching={enable_file_watching}"
        )

    def discover(self, prd_paths: list[str] | None = None) -> int:
        """Discover PRD files without loading them.

        Args:
            prd_paths: Optional list of paths to search (overrides init)

        Returns:
            Number of PRD files discovered

        Example:
            >>> registry.discover(["P:/projects/*/docs/PRD.md"])
            15
        """
        search_paths = prd_paths or self.prd_paths

        if not search_paths:
            logger.warning("No PRD paths configured for discovery")
            return 0

        import glob

        discovered = 0
        with self._lock:
            for pattern in search_paths:
                # Handle both absolute and relative paths
                if not Path(pattern).is_absolute():
                    pattern = str(self.base_path / pattern)

                # Use glob to find matching files
                matches = glob.glob(pattern, recursive=True)

                for prd_file in matches:
                    prd_path = Path(prd_file)
                    if prd_path.is_file():
                        # Extract PRD name from filename or parent directory
                        prd_name = self._infer_prd_name(prd_path)

                        # Store mapping
                        self._prd_files[prd_name] = prd_path
                        discovered += 1

                        logger.debug(f"Discovered PRD: {prd_name} -> {prd_path}")

            self.stats.total_prds = len(self._prd_files)

        logger.info(f"Discovered {discovered} PRD files")
        return discovered

    def get(self, prd_name: str, force_reload: bool = False) -> ParsedPRD | None:
        """Get a PRD by name, loading it if necessary (lazy loading).

        Args:
            prd_name: Name of the PRD to load
            force_reload: Force reload even if cached

        Returns:
            ParsedPRD object or None if not found

        Example:
            >>> prd = registry.get("yt_sync")
            >>> print(prd.prd_name)
            'yt_sync'
        """
        with self._lock:
            # Check if PRD is known
            if prd_name not in self._prd_files:
                logger.warning(f"Unknown PRD: {prd_name}")
                return None

            # Check cache
            if not force_reload and prd_name in self._cache:
                entry = self._cache[prd_name]

                # Check if cache entry is still valid
                if self._is_cache_valid(entry):
                    entry.touch()
                    self.stats.cache_hits += 1
                    logger.debug(f"Cache hit: {prd_name}")
                    return entry.prd
                else:
                    # Cache expired or file changed
                    logger.debug(f"Cache expired/invalid: {prd_name}")
                    del self._cache[prd_name]
                    self.stats.evictions += 1

            # Cache miss - load PRD
            self.stats.cache_misses += 1
            return self._load_prd(prd_name)

    def get_by_path(self, prd_path: str) -> ParsedPRD | None:
        """Get a PRD by file path (bypasses discovery).

        Args:
            prd_path: Direct path to PRD file

        Returns:
            ParsedPRD object or None if not found

        Example:
            >>> prd = registry.get_by_path("P:/projects/yt_sync/docs/PRD.md")
        """
        prd_file = Path(prd_path)
        if not prd_file.is_absolute():
            prd_file = self.base_path / prd_file

        if not prd_file.exists():
            logger.error(f"PRD file not found: {prd_path}")
            return None

        # Infer name from path
        prd_name = self._infer_prd_name(prd_file)

        # Add to known files
        with self._lock:
            self._prd_files[prd_name] = prd_file
            self.stats.total_prds = len(self._prd_files)

        # Load using get()
        return self.get(prd_name)

    def list_prds(self, loaded_only: bool = False) -> list[str]:
        """List all PRD names.

        Args:
            loaded_only: If True, only return loaded PRDs

        Returns:
            List of PRD names

        Example:
            >>> all_prds = registry.list_prds()
            >>> loaded = registry.list_prds(loaded_only=True)
        """
        with self._lock:
            if loaded_only:
                return list(self._cache.keys())
            return list(self._prd_files.keys())

    def is_loaded(self, prd_name: str) -> bool:
        """Check if a PRD is currently loaded in cache.

        Args:
            prd_name: Name of the PRD

        Returns:
            True if PRD is in cache
        """
        with self._lock:
            return prd_name in self._cache

    def preload(self, prd_names: list[str] | None = None) -> int:
        """Preload specific PRDs or all discovered PRDs into cache.

        Args:
            prd_names: List of PRD names to load (None = load all)

        Returns:
            Number of PRDs successfully loaded

        Example:
            >>> registry.preload(["yt_sync", "vid_dup_ai"])
            2
        """
        with self._lock:
            if prd_names is None:
                prd_names = list(self._prd_files.keys())

        loaded_count = 0
        for name in prd_names:
            if self.get(name):
                loaded_count += 1

        logger.info(f"Preloaded {loaded_count}/{len(prd_names)} PRDs")
        return loaded_count

    def invalidate(self, prd_name: str) -> bool:
        """Invalidate cache entry for a specific PRD.

        Args:
            prd_name: Name of the PRD to invalidate

        Returns:
            True if entry was invalidated

        Example:
            >>> registry.invalidate("yt_sync")
            True
        """
        with self._lock:
            if prd_name in self._cache:
                del self._cache[prd_name]
                self.stats.evictions += 1
                logger.debug(f"Invalidated cache: {prd_name}")
                return True
            return False

    def clear_cache(self) -> int:
        """Clear all cached PRDs.

        Returns:
            Number of cache entries cleared

        Example:
            >>> registry.clear_cache()
            25
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self.stats.evictions += count
            logger.info(f"Cleared {count} cached PRDs")
            return count

    def get_stats(self) -> RegistryStats:
        """Get registry statistics.

        Returns:
            RegistryStats object with current statistics

        Example:
            >>> stats = registry.get_stats()
            >>> print(f"Cache hit rate: {stats.cache_hit_rate():.2%}")
        """
        with self._lock:
            # Calculate average load time
            if self.stats.loaded_prds > 0:
                self.stats.avg_load_time = (
                    self.stats.total_load_time / self.stats.loaded_prds
                )

            return self.stats

    def get_cache_info(self, prd_name: str) -> dict[str, Any] | None:
        """Get detailed cache information for a PRD.

        Args:
            prd_name: Name of the PRD

        Returns:
            Dictionary with cache info or None if not cached
        """
        with self._lock:
            if prd_name not in self._cache:
                return None

            entry = self._cache[prd_name]
            return {
                "prd_name": prd_name,
                "loaded_at": entry.loaded_at.isoformat(),
                "last_accessed": entry.last_accessed.isoformat(),
                "access_count": entry.access_count,
                "age_seconds": entry.age_seconds(),
                "idle_seconds": entry.idle_seconds(),
                "file_hash": entry.file_hash,
            }

    def get_loaded_prds_info(self) -> list[dict[str, Any]]:
        """Get information about all loaded PRDs.

        Returns:
            List of cache info dictionaries

        Example:
            >>> info = registry.get_loaded_prds_info()
            >>> for prd in sorted(info, key=lambda x: x['access_count'], reverse=True):
            ...     print(f"{prd['prd_name']}: {prd['access_count']} accesses")
        """
        with self._lock:
            return [self.get_cache_info(name) for name in self._cache.keys()]

    def evict_stale(self, max_idle_seconds: float = 3600) -> int:
        """Evict PRDs that haven't been accessed recently.

        Args:
            max_idle_seconds: Maximum idle time before eviction

        Returns:
            Number of PRDs evicted

        Example:
            >>> # Evict PRDs not accessed in last hour
            >>> registry.evict_stale(3600)
            5
        """
        with self._lock:
            to_evict = []
            for name, entry in self._cache.items():
                if entry.idle_seconds() > max_idle_seconds:
                    to_evict.append(name)

            for name in to_evict:
                del self._cache[name]
                self.stats.evictions += 1
                logger.debug(f"Evicted stale PRD: {name}")

            return len(to_evict)

    def iterate_loaded_prds(self) -> Iterator[tuple[str, ParsedPRD]]:
        """Iterate over all currently loaded PRDs.

        Yields:
            Tuples of (prd_name, parsed_prd)

        Example:
            >>> for name, prd in registry.iterate_loaded_prds():
            ...     print(f"{name}: {prd.total_requirements} requirements")
        """
        with self._lock:
            for name, entry in self._cache.items():
                entry.touch()  # Update access time
                yield name, entry.prd

    def search_requirements(
        self,
        query: str,
        search_titles: bool = True,
        search_descriptions: bool = True,
        case_sensitive: bool = False,
        loaded_only: bool = True,
    ) -> list[tuple[str, str, str]]:
        """Search for requirements across PRDs.

        Args:
            query: Search query string
            search_titles: Search in requirement titles
            search_descriptions: Search in descriptions
            case_sensitive: Use case-sensitive search
            loaded_only: Only search loaded PRDs (False = load all)

        Returns:
            List of (prd_name, req_id, matched_text) tuples

        Example:
            >>> results = registry.search_requirements("authentication")
            >>> for prd_name, req_id, text in results:
            ...     print(f"{prd_name}/{req_id}: {text}")
        """
        results = []
        prd_names = self.list_prds(loaded_only=loaded_only)

        # Load all PRDs if needed
        if not loaded_only:
            for name in prd_names:
                self.get(name)

        # Search
        for name in prd_names:
            prd = self.get(name)
            if not prd:
                continue

            all_reqs = prd.functional_requirements + prd.non_functional_requirements

            for req in all_reqs:
                # Search title
                if search_titles and req.title:
                    if self._matches_query(req.title, query, case_sensitive):
                        results.append((name, req.id, req.title))
                        continue

                # Search description
                if search_descriptions and req.description:
                    if self._matches_query(req.description, query, case_sensitive):
                        results.append((name, req.id, req.description))

        return results

    # Private methods

    def _load_prd(self, prd_name: str) -> ParsedPRD | None:
        """Load a PRD from disk (must be called with lock held)."""
        if prd_name not in self._prd_files:
            return None

        prd_path = self._prd_files[prd_name]

        try:
            start_time = time.time()

            # Parse PRD
            parsed_prd = self.parser.parse_prd_file(str(prd_path))

            load_time = time.time() - start_time

            # Calculate file hash
            file_hash = self._hash_file(prd_path)

            # Create cache entry
            entry = PRDCacheEntry(
                prd=parsed_prd,
                loaded_at=datetime.now(),
                last_accessed=datetime.now(),
                access_count=1,
                file_hash=file_hash,
            )

            # Evict old entries if cache is full
            self._evict_if_needed()

            # Add to cache
            self._cache[prd_name] = entry

            # Update stats
            self.stats.loaded_prds += 1
            self.stats.total_load_time += load_time

            # Track file modification time
            self._file_mtimes[prd_name] = prd_path.stat().st_mtime

            logger.info(
                f"Loaded PRD: {prd_name} ({parsed_prd.total_requirements} reqs) "
                f"in {load_time:.3f}s"
            )

            return parsed_prd

        except PRDValidationError as e:
            logger.error(f"Failed to load PRD {prd_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading PRD {prd_name}: {e}")
            return None

    def _is_cache_valid(self, entry: PRDCacheEntry) -> bool:
        """Check if cache entry is still valid."""
        # Check TTL
        if self.ttl_seconds is not None:
            if entry.age_seconds() > self.ttl_seconds:
                return False

        # Check file modification
        if self.enable_file_watching:
            prd_name = entry.prd.prd_name
            if prd_name in self._prd_files:
                prd_path = self._prd_files[prd_name]
                current_mtime = prd_path.stat().st_mtime

                # Check if file was modified
                if prd_name in self._file_mtimes:
                    if current_mtime > self._file_mtimes[prd_name]:
                        logger.debug(f"File modified: {prd_name}")
                        return False

        return True

    def _evict_if_needed(self) -> None:
        """Evict least recently used entries if cache is full."""
        if len(self._cache) < self.cache_size:
            return

        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].last_accessed)

        # Evict oldest entries
        num_to_evict = len(self._cache) - self.cache_size + 1
        for name, _ in sorted_entries[:num_to_evict]:
            del self._cache[name]
            self.stats.evictions += 1
            logger.debug(f"LRU eviction: {name}")

    def _infer_prd_name(self, prd_path: Path) -> str:
        """Infer PRD name from file path.

        Strategy:
        1. If parent is "docs", use grandparent name
        2. If parent is not "docs", use parent name
        3. Fall back to filename stem
        """
        # Try to get meaningful project name
        if prd_path.parent.name.lower() == "docs":
            # Path is like: .../project_name/docs/PRD.md
            if prd_path.parent.parent.name:
                return prd_path.parent.parent.name

        # Try parent directory name
        if prd_path.parent.name:
            parent_name = prd_path.parent.name
            if parent_name.lower() not in ("docs", "md", "markdown"):
                return parent_name

        # Fall back to filename without extension
        return prd_path.stem

    def _get_active_tsk_directory(self) -> Path | None:
        """Get the active TSK directory from TaskMaster database.

        Returns:
            Path to active TSK directory or None if no active TSK
        """
        try:
            db_path = Path("P:/.speckit/taskmaster/tasks.db")
            if not db_path.exists():
                return None

            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Get active TSK
            cursor.execute("SELECT id FROM tsk WHERE active = 1 LIMIT 1")
            result = cursor.fetchone()
            conn.close()

            if result:
                tsk_id = result[0]
                # TSK directory is in .speckit/memory/
                tsk_dir = Path("P:/__csf/.speckit/memory") / tsk_id
                if tsk_dir.exists():
                    return tsk_dir

        except Exception as e:
            logger.debug(f"Could not get active TSK directory: {e}")

        return None

    def _hash_file(self, file_path: Path) -> str:
        """Calculate hash of file contents."""
        try:
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                hasher.update(f.read())
            return hasher.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return ""

    def _matches_query(self, text: str, query: str, case_sensitive: bool) -> bool:
        """Check if text matches query."""
        if not case_sensitive:
            text = text.lower()
            query = query.lower()
        return query in text


# Convenience functions


def create_registry(
    prd_paths: list[str],
    cache_size: int = 100,
    ttl_seconds: float | None = None,
) -> PRDRegistry:
    """
    Create and initialize a PRD registry.

    Args:
        prd_paths: List of glob patterns to find PRD files
        cache_size: Maximum cache size
        ttl_seconds: Cache TTL (None = no expiration)

    Returns:
        Initialized PRDRegistry with discovered PRDs

    Example:
        >>> registry = create_registry(["P:/projects/*/docs/PRD.md"])
        >>> print(f"Found {len(registry.list_prds())} PRDs")
    """
    registry = PRDRegistry(
        prd_paths=prd_paths,
        cache_size=cache_size,
        ttl_seconds=ttl_seconds,
    )
    registry.discover()
    return registry


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Example: Create registry with common PRD locations
    registry = create_registry(
        [
            r"P:/projects/*/docs/PRD.md",
            r"P:/projects/*/PRD.md",
        ]
    )

    print(f"\nDiscovered {len(registry.list_prds())} PRD files:")
    for name in sorted(registry.list_prds()):
        print(f"  - {name}")

    # Load a specific PRD
    if len(registry.list_prds()) > 0:
        sample_name = registry.list_prds()[0]
        print(f"\nLoading {sample_name}...")
        prd = registry.get(sample_name)

        if prd:
            print(f"\nPRD: {prd.prd_name}")
            print(f"Total Requirements: {prd.total_requirements}")
            print(f"Functional: {len(prd.functional_requirements)}")
            print(f"Non-Functional: {len(prd.non_functional_requirements)}")

    # Show statistics
    stats = registry.get_stats()
    print("\nCache Statistics:")
    print(f"  Total PRDs: {stats.total_prds}")
    print(f"  Loaded: {stats.loaded_prds}")
    print(f"  Cache hits: {stats.cache_hits}")
    print(f"  Cache misses: {stats.cache_misses}")
    print(f"  Hit rate: {stats.cache_hit_rate():.2%}")
    print(f"  Avg load time: {stats.avg_load_time:.3f}s")
