"""
SessionFileCache - Thread-safe file-based cache with TTL and mtime invalidation.

Caches JSON file contents with TTL-based expiration and automatic
invalidation on file modification.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from time import time
from typing import Any


class SessionFileCache:
    """Thread-safe cache for JSON files with TTL and mtime-based invalidation."""

    def __init__(self, ttl: int = 60) -> None:
        """Initialize cache with default TTL in seconds.

        Args:
            ttl: Default time-to-live for cache entries in seconds.
        """
        self._cache: dict[str, Any] = {}
        self._mtimes: dict[str, float] = {}
        self._timestamps: dict[str, float] = {}
        self._ttl: int = ttl
        self._lock: threading.Lock = threading.Lock()

    def get(self, file_path: Path | str, default: Any | None = None) -> Any:
        """Get cached JSON data or read from file.

        Args:
            file_path: Path to JSON file.
            default: Value to return if file doesn't exist or is invalid.

        Returns:
            Cached data, freshly read data, or default value.
        """
        # Normalize path
        path_str = str(file_path)
        path = Path(file_path)

        with self._lock:
            now = time()

            # Check cache validity
            if self._is_cache_valid(path_str, path, now):
                return self._cache[path_str]

            # Cache miss or invalid - try to read file
            data = self._read_file(path, default)

            # Update cache if read succeeded
            if data is not default:
                self._update_cache(path_str, path, data, now)

            return data

    def _is_cache_valid(self, path_str: str, path: Path, now: float) -> bool:
        """Check if cached entry is still valid.

        Args:
            path_str: String representation of file path.
            path: Path object for mtime checking.
            now: Current timestamp.

        Returns:
            True if cache is valid, False otherwise.
        """
        if path_str not in self._cache:
            return False

        # Check TTL expiration
        if self._timestamps[path_str] + self._ttl <= now:
            return False

        # Check file modification time
        try:
            current_mtime = path.stat().st_mtime
            if self._mtimes.get(path_str) != current_mtime:
                return False
        except OSError:
            # File doesn't exist or can't stat
            return False

        return True

    def _read_file(self, path: Path, default: Any | None) -> Any:
        """Read and parse JSON file.

        Args:
            path: Path to JSON file.
            default: Value to return on error.

        Returns:
            Parsed data or default value.
        """
        try:
            text = path.read_text()
            return json.loads(text)
        except (OSError, json.JSONDecodeError):
            return default

    def _update_cache(self, path_str: str, path: Path, data: Any, now: float) -> None:
        """Update cache with new data.

        Args:
            path_str: String representation of file path.
            path: Path object for mtime.
            data: Data to cache.
            now: Current timestamp.
        """
        self._cache[path_str] = data
        self._timestamps[path_str] = now
        try:
            self._mtimes[path_str] = path.stat().st_mtime
        except OSError:
            self._mtimes[path_str] = 0.0

    def clear(self, file_path: Path | str | None = None) -> None:
        """Clear cache for specific file or all files.

        Args:
            file_path: Path to clear, or None to clear all.
        """
        with self._lock:
            if file_path is None:
                self._cache.clear()
                self._mtimes.clear()
                self._timestamps.clear()
            else:
                path_str = str(file_path)
                self._cache.pop(path_str, None)
                self._mtimes.pop(path_str, None)
                self._timestamps.pop(path_str, None)

    def set_ttl(self, ttl: int) -> None:
        """Set default TTL in seconds.

        Args:
            ttl: Time-to-live in seconds.
        """
        with self._lock:
            self._ttl = ttl

    def get_ttl(self) -> int:
        """Get current TTL in seconds.

        Returns:
            Current TTL value.
        """
        return self._ttl
    def get_json(self, file_path: Path | str, default: Any | None = None) -> Any:
        """Alias for get() for backward compatibility with tests.

        Args:
            file_path: Path to JSON file.
            default: Value to return if file doesn't exist or is invalid.

        Returns:
            Cached data, freshly read data, or default value.
        """
        return self.get(file_path, default)
