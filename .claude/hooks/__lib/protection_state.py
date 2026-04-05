#!/usr/bin/env python3
r"""
Protection State Management for Library Code Protection

Manages persistent storage of characterization data.

Storage Structure:
    P:\.claude\hooks\__lib\.state/
    ├── characterization/
    │   ├── session_manager.json
    │   ├── task_identity_manager.json
    │   └── token_budget.json
    ├── call_graphs/
    │   └── *.dot files
    └── test_snapshots/
        └── *.json files

The state manager handles:
- Saving/loading characterizations
- Terminal isolation
- Cache invalidation
- State cleanup
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Type hint import (avoids circular import at runtime)
if TYPE_CHECKING:
    from characterization_engine import CharacterizationData
else:
    CharacterizationData = None  # type: ignore[assignment]

# Add parent directory to path
# NOTE: Scoped path mutation - restored after import (AC-003 compliance)
_lib_path_added = False
_original_path = sys.path.copy()
lib_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(lib_dir))
_lib_path_added = True

# Runtime import (protected against circular import)
try:
    # Import at runtime for actual use (TYPE_CHECKING only provides type hints)
    from characterization_engine import CharacterizationData as _CharacterizationData
    CharacterizationData = _CharacterizationData  # type: ignore[misc, assignment]
except ImportError:
    # CharacterizationEngine is optional - protection_state can work standalone
    # Keep CharacterizationData as None for type checking, handle at runtime
    pass
except RecursionError:
    # Circular import is a real error - don't silently fail (Task #179)
    # Re-raise with clearer message
    raise ImportError(
        "Circular import detected: protection_state <-> characterization_engine. "
        "This indicates a module dependency cycle that must be resolved."
    ) from None
finally:
    # Restore original path after import (scope control)
    if _lib_path_added:
        sys.path = _original_path

# State directory structure
STATE_DIR = Path(__file__).resolve().parent / ".state"
CHARACTERIZATION_DIR = STATE_DIR / "characterization"
CALL_GRAPHS_DIR = STATE_DIR / "call_graphs"
TEST_SNAPSHOTS_DIR = STATE_DIR / "test_snapshots"

# Current schema version for state files (Task #182 - migration support)
# Increment when state structure changes incompatibly.
STATE_SCHEMA_VERSION = 1

# Supported schema versions for backward compatibility
_MIN_SUPPORTED_SCHEMA_VERSION = 1


# ============================================================================
# FILE LOCKING (Task #176 - Race condition prevention)
# ============================================================================

# Platform-specific imports
if sys.platform != 'win32':
    import fcntl
else:
    import msvcrt


@contextmanager
def _file_lock(lock_path: Path, timeout: float = 5.0):
    """
    Cross-platform file locking with timeout.

    Prevents race conditions when multiple processes/terminals access
    the same state file concurrently.

    Args:
        lock_path: Path to lock file (will be created if needed)
        timeout: Maximum seconds to wait for lock

    Yields:
        True if lock acquired, False if timeout

    Raises:
        TimeoutError: If lock cannot be acquired within timeout
    """
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_file = None
    acquired = False
    start_time = time.time()

    try:
        lock_file = open(lock_path, 'w')

        # Try to acquire lock with timeout and exponential backoff
        backoff = 0.01  # Start with 10ms
        while True:
            try:
                if sys.platform == 'win32':
                    # Windows: msvcrt.locking
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    # Unix: fcntl.flock with exclusive lock
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except (OSError, BlockingIOError):
                # Lock held by another process
                if time.time() - start_time >= timeout:
                    raise TimeoutError(f"Could not acquire lock on {lock_path} within {timeout}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, 0.5)  # Exponential backoff, max 500ms

        yield True

    finally:
        if lock_file and acquired:
            try:
                if sys.platform == 'win32':
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            except Exception:
                pass  # Best-effort unlock
            lock_file.close()
            # Clean up lock file if empty
            try:
                if lock_path.exists():
                    lock_path.unlink()
            except Exception:
                pass


class StateManager:
    """
    Manages persistent state for library protection system.

    Usage:
        manager = StateManager()
        manager.save_characterization(data)
        data = manager.load_characterization(module_path)
    """

    def __init__(self, terminal_id: str | None = None):
        """
        Initialize state manager.

        Args:
            terminal_id: Terminal ID for isolation (auto-detected if None)
        """
        self.terminal_id = terminal_id or self._detect_terminal_id()

        # Create state directories with secure permissions (owner-only: 0700)
        CHARACTERIZATION_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        CALL_GRAPHS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
        TEST_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)

        # Hash cache: {state_key: {"sha256": str, "ast_hash": str|None}}
        self._hash_cache: dict[str, dict[str, str | None]] = {}
        # Cache stats for monitoring
        self._cache_stats = {"hits": 0, "misses": 0}

    def _detect_terminal_id(self) -> str:
        """Detect terminal ID for isolation.

        Fallback uses UUID instead of PID to prevent collision when:
        - Process terminates and OS reuses PID
        - New process with same PID incorrectly accesses old state

        UUID provides collision resistance regardless of PID reuse.
        """
        try:
            hooks_dir = Path(__file__).resolve().parent.parent
            sys.path.insert(0, str(hooks_dir))
            from __lib.terminal_detection import detect_terminal_id
            return detect_terminal_id()
        except Exception:
            # Use UUID instead of PID to prevent collision (Task #234)
            # Shortened to 8 chars for readability while maintaining uniqueness
            return f"fallback_{uuid.uuid4().hex[:8]}"

    def _get_state_key(self, module_path: str) -> str:
        """Generate state key for module."""
        # Use hash of module path as key
        return hashlib.sha256(module_path.encode()).hexdigest()[:16]

    # Hash cache methods

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file content.

        Uses same method as CharacterizationEngine for consistency:
        read_text(encoding="utf-8") then encode() to bytes.
        """
        path = Path(file_path)
        if not path.exists():
            return ""
        try:
            # Use same method as CharacterizationEngine for consistent hashes
            content = path.read_text(encoding="utf-8")
            return hashlib.sha256(content.encode()).hexdigest()
        except OSError:
            return ""

    def _save_file_hash(self, module_path: str, sha256: str, ast_hash: str | None = None) -> None:
        """Store file hash in in-memory cache."""
        key = self._get_state_key(module_path)
        self._hash_cache[key] = {"sha256": sha256, "ast_hash": ast_hash}

    def _load_file_hash(self, module_path: str) -> dict[str, str | None] | None:
        """Load file hash from in-memory cache."""
        key = self._get_state_key(module_path)
        return self._hash_cache.get(key)

    def get_cached_checksum(self, module_path: str) -> str | None:
        """
        Get cached checksum for module.

        Args:
            module_path: Path to module

        Returns:
            Cached SHA256 checksum or None if not cached
        """
        cached = self._load_file_hash(module_path)
        if cached:
            self._cache_stats["hits"] += 1
            return cached.get("sha256")
        self._cache_stats["misses"] += 1
        return None

    def is_checksum_valid(self, module_path: str, expected_checksum: str) -> bool:
        """
        Validate module checksum against expected value.

        Args:
            module_path: Path to module file
            expected_checksum: Expected SHA256 checksum

        Returns:
            True if checksums match, False otherwise
        """
        actual_hash = self._compute_file_hash(module_path)
        return actual_hash == expected_checksum

    def clear_hash_cache(self, module_path: str | None = None) -> int:
        """
        Clear hash cache entries.

        Args:
            module_path: Specific module to clear, or None to clear all

        Returns:
            Number of entries cleared
        """
        if module_path is None:
            count = len(self._hash_cache)
            self._hash_cache.clear()
            return count
        key = self._get_state_key(module_path)
        if key in self._hash_cache:
            del self._hash_cache[key]
            return 1
        return 0

    def get_hash_cache_stats(self) -> dict[str, Any]:
        """
        Get hash cache statistics.

        Returns:
            Dict with hits, misses, size, and hit_rate
        """
        total = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = self._cache_stats["hits"] / total if total > 0 else 0.0
        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "size": len(self._hash_cache),
            "hit_rate": hit_rate,
        }

    def save_characterization(self, data: Any) -> Path:
        """
        Save characterization data to disk with atomic write and file locking.

        Uses atomic write pattern: write to temp file + rename.
        Prevents TOCTOU vulnerabilities and race conditions (Task #176).

        Args:
            data: CharacterizationData instance

        Returns:
            Path to saved file
        """
        key = self._get_state_key(data.module_path)
        state_file = CHARACTERIZATION_DIR / f"{key}.json"
        lock_file = CHARACTERIZATION_DIR / f"{key}.lock"

        # Add terminal_id to the data for tracking
        state_data = {
            "schema_version": STATE_SCHEMA_VERSION,  # Task #182 - schema version for migration
            "characterization": json.loads(data.to_json()) if hasattr(data, "to_json") else data,
            "terminal_id": self.terminal_id,
            "saved_at": datetime.now().isoformat(),
        }

        # Atomic write pattern with file locking (Task #176)
        with _file_lock(lock_file, timeout=5.0):
            # Write to temporary file first
            temp_file = state_file.with_suffix('.tmp')
            temp_file.write_text(json.dumps(state_data, indent=2, default=str), encoding="utf-8")
            temp_file.chmod(0o600)

            # Atomic rename (overwrites target if exists)
            temp_file.replace(state_file)

        # Cache checksum for fast validation (address SEC-PLAN-004)
        checksum = getattr(data, "checksum", None)
        ast_hash = getattr(data, "ast_hash", None)
        if checksum:
            self._save_file_hash(data.module_path, checksum, ast_hash)

        return state_file

    def load_characterization(self, module_path: str) -> Any:
        """
        Load characterization data from disk with file locking (Task #176).

        Args:
            module_path: Path to module

        Returns:
            CharacterizationData or None if not found

        Note:
            Checks hash cache for quick validation before full load.
            Returns None if file hash doesn't match cached value (SEC-PLAN-004).
            Validates schema version and migrates if needed (Task #182).
        """
        key = self._get_state_key(module_path)
        state_file = CHARACTERIZATION_DIR / f"{key}.json"
        lock_file = CHARACTERIZATION_DIR / f"{key}.lock"

        if not state_file.exists():
            return None

        # Fast path: Check cached hash first (outside lock for performance)
        cached_hash = self.get_cached_checksum(module_path)
        if cached_hash:
            # Verify file hasn't changed since cached (SEC-PLAN-004 validation)
            current_hash = self._compute_file_hash(module_path)
            if current_hash and current_hash != cached_hash:
                # File changed since cache - invalidate and force re-characterization
                self.clear_hash_cache(module_path)
                return None

        try:
            # Read with file locking to prevent race conditions (Task #176)
            with _file_lock(lock_file, timeout=5.0):
                content = state_file.read_text(encoding="utf-8")
                state_data = json.loads(content)

            # Check schema version (Task #182 - migration support)
            schema_version = state_data.get("schema_version", 0)  # 0 means pre-versioning
            if schema_version < _MIN_SUPPORTED_SCHEMA_VERSION:
                # State file too old - not supported, force re-characterization
                return None
            if schema_version > STATE_SCHEMA_VERSION:
                # State file from future version - not supported
                return None
            if schema_version < STATE_SCHEMA_VERSION:
                # Migration needed - for now, force re-characterization
                # Future: Implement _migrate_state_v0_to_v1, etc.
                return None

            # Extract characterization from state wrapper
            char_data = state_data.get("characterization", {})

            # Validate checksum against current file (task #172 - stale state prevention)
            stored_checksum = char_data.get("checksum")
            if stored_checksum:
                current_hash = self._compute_file_hash(module_path)
                if current_hash and current_hash != stored_checksum:
                    # File changed since state was saved - invalidate stale state
                    self.clear_hash_cache(module_path)
                    return None

            if CharacterizationData and "module_path" in char_data:
                return CharacterizationData.from_json(json.dumps(char_data))

            return char_data

        except TimeoutError:
            # Lock timeout - return None rather than blocking indefinitely
            return None
        except (OSError, json.JSONDecodeError):
            return None

    def has_characterization(self, module_path: str) -> bool:
        """Check if characterization exists for module."""
        key = self._get_state_key(module_path)
        state_file = CHARACTERIZATION_DIR / f"{key}.json"
        return state_file.exists()

    def delete_characterization(self, module_path: str) -> bool:
        """
        Delete characterization data for module.

        Args:
            module_path: Path to module

        Returns:
            True if deleted, False if not found
        """
        key = self._get_state_key(module_path)
        state_file = CHARACTERIZATION_DIR / f"{key}.json"

        if state_file.exists():
            state_file.unlink()
            # Also remove from hash cache
            self.clear_hash_cache(module_path)
            return True
        return False

    def list_characterizations(self) -> list[dict[str, Any]]:
        """
        List all stored characterizations.

        Returns:
            List of characterization metadata
        """
        results = []

        for state_file in CHARACTERIZATION_DIR.glob("*.json"):
            try:
                content = state_file.read_text(encoding="utf-8")
                state_data = json.loads(content)
                char_data = state_data.get("characterization", {})

                results.append({
                    "module_path": char_data.get("module_path", "unknown"),
                    "captured_at": char_data.get("captured_at", "unknown"),
                    "checksum": char_data.get("checksum", ""),
                    "saved_at": state_data.get("saved_at", "unknown"),
                    "terminal_id": state_data.get("terminal_id", "unknown"),
                })
            except (OSError, json.JSONDecodeError):
                continue

        return results

    def save_call_graph(self, module_path: str, dot_content: str) -> Path:
        """
        Save call graph as DOT file.

        Args:
            module_path: Path to module
            dot_content: GraphViz DOT format content

        Returns:
            Path to saved file
        """
        key = self._get_state_key(module_path)
        dot_file = CALL_GRAPHS_DIR / f"{key}.dot"

        dot_file.write_text(dot_content, encoding="utf-8")
        # Set secure file permissions (owner-only: 0600) - cross-platform
        dot_file.chmod(0o600)
        return dot_file

    def load_call_graph(self, module_path: str) -> str | None:
        """Load call graph DOT content."""
        key = self._get_state_key(module_path)
        dot_file = CALL_GRAPHS_DIR / f"{key}.dot"

        if dot_file.exists():
            return dot_file.read_text(encoding="utf-8")
        return None

    def cleanup_old_state(self, max_age_hours: int = 24) -> int:
        """
        Clean up old state files.

        Args:
            max_age_hours: Maximum age in hours to keep

        Returns:
            Number of files cleaned up
        """
        cleaned = 0
        cutoff_time = time.time() - (max_age_hours * 3600)

        for state_dir in [CHARACTERIZATION_DIR, CALL_GRAPHS_DIR, TEST_SNAPSHOTS_DIR]:
            for state_file in state_dir.glob("*"):
                if state_file.is_file():
                    try:
                        if state_file.stat().st_mtime < cutoff_time:
                            state_file.unlink()
                            cleaned += 1
                    except OSError:
                        continue

        return cleaned

    def clear_all_state(self) -> int:
        """
        Clear all state files for current terminal.

        Returns:
            Number of files deleted
        """
        deleted = 0

        for state_dir in [CHARACTERIZATION_DIR, CALL_GRAPHS_DIR, TEST_SNAPSHOTS_DIR]:
            for state_file in state_dir.glob("*"):
                try:
                    # Only delete files from this terminal
                    if state_file.suffix == ".json":
                        content = state_file.read_text(encoding="utf-8")
                        state_data = json.loads(content)
                        if state_data.get("terminal_id") == self.terminal_id:
                            state_file.unlink()
                            deleted += 1
                    else:
                        # Non-JSON files (DOT, etc) - clean by age
                        state_file.unlink()
                        deleted += 1
                except (OSError, json.JSONDecodeError):
                    continue

        return deleted

    def get_state_size_mb(self) -> float:
        """Get total size of state directory in MB."""
        total_bytes = 0

        for state_dir in [CHARACTERIZATION_DIR, CALL_GRAPHS_DIR, TEST_SNAPSHOTS_DIR]:
            for item in state_dir.rglob("*"):
                if item.is_file():
                    try:
                        total_bytes += item.stat().st_size
                    except OSError:
                        continue

        return total_bytes / (1024 * 1024)


# Convenience functions

def save_characterization(data: Any, terminal_id: str | None = None) -> Path:
    """Save characterization data."""
    manager = StateManager(terminal_id)
    return manager.save_characterization(data)


def load_characterization(module_path: str, terminal_id: str | None = None) -> Any:
    """Load characterization data."""
    manager = StateManager(terminal_id)
    return manager.load_characterization(module_path)


def has_characterization(module_path: str, terminal_id: str | None = None) -> bool:
    """Check if characterization exists."""
    manager = StateManager(terminal_id)
    return manager.has_characterization(module_path)


def get_cached_checksum(module_path: str, terminal_id: str | None = None) -> str | None:
    """Get cached checksum for module."""
    manager = StateManager(terminal_id)
    return manager.get_cached_checksum(module_path)


def is_checksum_valid(module_path: str, expected_checksum: str, terminal_id: str | None = None) -> bool:
    """Validate module checksum against expected value."""
    manager = StateManager(terminal_id)
    return manager.is_checksum_valid(module_path, expected_checksum)


def clear_hash_cache(module_path: str | None = None, terminal_id: str | None = None) -> int:
    """Clear hash cache entries."""
    manager = StateManager(terminal_id)
    return manager.clear_hash_cache(module_path)


def get_hash_cache_stats(terminal_id: str | None = None) -> dict[str, Any]:
    """Get hash cache statistics."""
    manager = StateManager(terminal_id)
    return manager.get_hash_cache_stats()


__all__ = [
    "StateManager",
    "save_characterization",
    "load_characterization",
    "has_characterization",
    # Hash cache methods
    "get_cached_checksum",
    "is_checksum_valid",
    "clear_hash_cache",
    "get_hash_cache_stats",
]
