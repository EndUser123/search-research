from __future__ import annotations

"""
Caching system for iCHS - Command result caching with TTL support.

Enhancements vs. previous version:
- Atomic writes (temp file + os.replace) to avoid partial/corrupted reads
- Optional namespace to disambiguate keys between different callers
- Optional max_entries eviction (oldest-first) to cap disk usage
- More robust JSON serialization (default=str)
- UTC timestamps (ISO 8601) with an additional epoch field for easier math
- Logging instead of silent pass on errors
- parents=True for cache dir creation
- Better typing with Generic[T]
"""

import hashlib
import json
import logging
import os
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Generic, TypeVar, Union

T = TypeVar("T")
PathLike = Union[str, os.PathLike, Path]


def _now_utc() -> datetime:
    return datetime.now(UTC)


def _to_epoch(ts: datetime) -> float:
    return ts.timestamp()


def _parse_timestamp(payload: dict[str, Any]) -> datetime | None:
    """Support both new ('ts' epoch) and legacy ('timestamp' ISO) fields."""
    if "ts" in payload and isinstance(payload["ts"], (int, float)):
        try:
            return datetime.fromtimestamp(float(payload["ts"]), tz=UTC)
        except (ValueError, OSError):
            return None
    iso = payload.get("timestamp")
    if isinstance(iso, str):
        try:
            # fromisoformat supports timezone-aware strings; if naive, assume UTC
            dt = datetime.fromisoformat(iso)
            return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
        except ValueError:
            return None
    return None


class CommandCache(Generic[T]):
    """Caching system for command results to improve performance.

    Notes:
        - Results should be JSON-serializable. Non-serializable objects are stringified by default.
        - Files are written atomically; corrupted files are removed on read.
        - TTL expiration is enforced on read and by clear_expired().
        - Optional max_entries enforces a soft LRU via file mtime (oldest first).
    """

    def __init__(
        self,
        cache_dir: PathLike = ".ichs_cache",
        ttl_hours: int = 24,
        namespace: str | None = None,
        max_entries: int | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        """
        Initialize the cache system.

        Args:
            cache_dir: Directory to store cache files (created if missing).
            ttl_hours: Time-to-live for cache entries in hours.
            namespace: Optional string to namespace keys (reduces accidental collisions).
            max_entries: Optional cap on number of cache files; oldest are evicted after set.
            logger: Optional logger; defaults to module logger.
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
        self.namespace = namespace or ""
        self.max_entries = max_entries
        self.log = logger or logging.getLogger(__name__)

    def get_cache_key(self, command: str) -> str:
        """Generate a cache key for the given command (namespaced)."""
        # Namespacing reduces collisions across different command domains
        payload = f"{self.namespace}::{command}" if self.namespace else command
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

    def _path_for_key(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.json"

    def get(self, command: str) -> T | None:
        """
        Get cached result for a command.

        Args:
            command: The command to look up.

        Returns:
            Cached result if available and not expired, None otherwise.
        """
        cache_key = self.get_cache_key(command)
        cache_file = self._path_for_key(cache_key)

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, encoding="utf-8") as f:
                cached_data: dict[str, Any] = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            # If cache is corrupted or unreadable, remove it
            self._safe_unlink(cache_file, reason=f"corrupted/unreadable ({e})")
            return None

        cache_time = _parse_timestamp(cached_data)
        if cache_time is None:
            # Missing/invalid timestamp -> treat as corrupted
            self._safe_unlink(cache_file, reason="invalid timestamp")
            return None

        if _now_utc() - cache_time > self.ttl:
            self._safe_unlink(cache_file, reason="expired")
            return None

        try:
            return cached_data["result"]  # type: ignore[return-value]
        except KeyError:
            self._safe_unlink(cache_file, reason="missing result")
            return None

    def set(self, command: str, result: T) -> None:
        """
        Cache the result of a command.

        Args:
            command: The command that was executed.
            result: The result to cache (should be JSON-serializable; non-serializable types are stringified).
        """
        cache_key = self.get_cache_key(command)
        cache_file = self._path_for_key(cache_key)

        now = _now_utc()
        cache_data: dict[str, Any] = {
            "timestamp": now.isoformat(),
            "ts": _to_epoch(now),  # epoch seconds included for robustness
            "result": result,
        }

        # Atomic write: write to a temp file then replace.
        try:
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=str(self.cache_dir), prefix=cache_file.name + ".", suffix=".tmp"
            )
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_file:
                    json.dump(
                        cache_data, tmp_file, ensure_ascii=False, indent=2, default=str
                    )
                    tmp_file.flush()
                    os.fsync(tmp_file.fileno())
                os.replace(tmp_path, cache_file)
            finally:
                # If replace failed above, ensure temp file is removed
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
        except (OSError, TypeError) as e:
            # TypeError: non-serializable object (still possible if default=str fails)
            self.log.debug("Cache write failed for %s: %s", cache_file, e)
            return

        # Optional eviction to cap number of files
        if self.max_entries is not None:
            try:
                self._enforce_limits()
            except Exception as e:
                self.log.debug("Cache eviction failed: %s", e)

    def delete(self, command: str) -> bool:
        """Delete a specific cache entry; returns True if a file was removed."""
        cache_key = self.get_cache_key(command)
        cache_file = self._path_for_key(cache_key)
        return self._safe_unlink(cache_file, reason="delete()")

    def clear_expired(self) -> None:
        """Remove all expired cache entries."""
        now = _now_utc()
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, encoding="utf-8") as f:
                    cached_data = json.load(f)
                cache_time = _parse_timestamp(cached_data)
                if cache_time is None or now - cache_time > self.ttl:
                    self._safe_unlink(cache_file, reason="expired/invalid in sweep")
            except (json.JSONDecodeError, KeyError, ValueError, OSError):
                self._safe_unlink(cache_file, reason="corrupted in sweep")

    def clear_all(self) -> None:
        """Clear all cache entries."""
        for cache_file in self.cache_dir.glob("*.json"):
            self._safe_unlink(cache_file, reason="clear_all")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))

        total_entries = 0
        total_size = 0
        for f in cache_files:
            try:
                if f.exists():
                    st = f.stat()
                    total_entries += 1
                    total_size += st.st_size
            except OSError:
                # Skip files that disappeared mid-iteration
                continue

        return {
            "total_entries": total_entries,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "dir": str(self.cache_dir),
            "ttl_hours": round(self.ttl.total_seconds() / 3600, 2),
            "namespace": self.namespace or None,
            "max_entries": self.max_entries,
        }

    def _enforce_limits(self) -> None:
        """Evict oldest files if max_entries is set and exceeded."""
        if self.max_entries is None:
            return
        files = [f for f in self.cache_dir.glob("*.json") if f.exists()]
        if len(files) <= self.max_entries:
            return
        # Sort by modification time (oldest first)
        files.sort(key=lambda p: p.stat().st_mtime)
        to_remove = files[: max(0, len(files) - self.max_entries)]
        for f in to_remove:
            self._safe_unlink(f, reason="eviction (max_entries)")

    def _safe_unlink(self, path: Path, reason: str = "") -> bool:
        """Try to remove a file and log failures; return True if removed."""
        try:
            path.unlink(
                missing_ok=True
            )  # Python 3.8+: emulate with try/except if needed
            return True
        except TypeError:
            # missing_ok not supported (older Python)
            try:
                if path.exists():
                    path.unlink()
                    return True
            except OSError as e:
                self.log.debug("Failed to remove %s (%s): %s", path, reason, e)
        except OSError as e:
            self.log.debug("Failed to remove %s (%s): %s", path, reason, e)
        return False
