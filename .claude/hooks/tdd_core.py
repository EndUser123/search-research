#!/usr/bin/env python3
from __future__ import annotations

"""
TDD Core - Shared state management for TDD enforcement.

Provides:
- Atomic state file operations with locking
- Pytest config parsing for test patterns
- Approval mechanism with expiry
- Audit logging
- Thread-safe state caching with TTL

State is keyed by TEST FILE (not impl file) to prevent cross-file contamination.
"""

import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
hooks_dir = Path(__file__).resolve().parent
import time
from collections.abc import Iterator

# Modern cross-platform file locking with proper error handling
# Uses a context manager pattern for safer lock handling
from contextlib import contextmanager
from typing import Any, cast

# File locking retry configuration
MAX_LOCK_RETRIES = 100
INITIAL_LOCK_RETRY_DELAY_MS = 1
MAX_LOCK_RETRY_DELAY_MS = 50
LOCK_TIMEOUT_MULTIPLIER = 1.3

# For Windows, use a separate lock file approach since msvcrt.locking()
# doesn't work well with temp file atomic writes
USE_LOCK_FILE = sys.platform == "win32"


@contextmanager
def _lock_file_lockfile(lock_file_path: Path, timeout: float = 5.0) -> Iterator[None]:
    """
    Cross-platform lock file-based synchronization.

    Uses a separate lock file with atomic mkdir/create for synchronization.
    This works better on Windows for coordinating atomic writes.

    Args:
        lock_file_path: Path to the lock file
        timeout: Maximum seconds to wait for lock

    Raises:
        OSError: If lock cannot be acquired within timeout
    """
    lock_id = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"
    start_time = time.time()
    retry_delay = INITIAL_LOCK_RETRY_DELAY_MS / 1000.0
    attempt = 0

    while True:
        attempt += 1
        elapsed = time.time() - start_time

        if elapsed >= timeout:
            raise OSError(
                f"Could not acquire lock on {lock_file_path} after {timeout}s "
                f"({attempt} attempts). Another process may be holding the lock."
            )

        try:
            # Try to create lock file exclusively (atomic operation)
            # On Windows, os.O_CREAT | os.O_EXCL makes this atomic
            fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as f:
                f.write(lock_id)
            # Lock acquired
            break
        except FileExistsError:
            # Lock file exists, check if it's stale
            try:
                # Check if lock file is older than 30 seconds (stale lock)
                lock_age = time.time() - lock_file_path.stat().st_mtime
                if lock_age > 30:
                    # Stale lock, try to remove it
                    try:
                        lock_file_path.unlink()
                    except OSError:
                        pass
                    # Continue to retry
                else:
                    # Valid lock, wait and retry
                    time.sleep(retry_delay)
                    retry_delay = min(
                        retry_delay * LOCK_TIMEOUT_MULTIPLIER,
                        MAX_LOCK_RETRY_DELAY_MS / 1000.0,
                    )

            except OSError:
                # Can't check stat, just wait and retry
                time.sleep(retry_delay)
                retry_delay = min(
                    retry_delay * LOCK_TIMEOUT_MULTIPLIER,
                    MAX_LOCK_RETRY_DELAY_MS / 1000.0,
                )

        except OSError:
            # Other error, wait and retry
            time.sleep(retry_delay)
            retry_delay = min(
                retry_delay * LOCK_TIMEOUT_MULTIPLIER, MAX_LOCK_RETRY_DELAY_MS / 1000.0
            )

    try:
        yield
    finally:
        # Release lock by removing lock file
        try:
            lock_file_path.unlink()
        except OSError:
            pass  # Lock already released or file doesn't exist


if sys.platform == "win32":
    import msvcrt

    @contextmanager
    def file_lock(
        f: Any, exclusive: bool = True, timeout: float = 5.0
    ) -> Iterator[None]:
        """
        Context manager for Windows file locking with exponential backoff retry.

        Uses msvcrt.locking() with retry logic for concurrent access safety.
        Implements exponential backoff to handle high-contention scenarios.

        Args:
            f: File object to lock
            exclusive: True for exclusive lock, False for shared
            timeout: Maximum seconds to wait for lock (default 5.0)

        Raises:
            OSError: If lock cannot be acquired within timeout
        """
        start_time = time.time()
        lock_type = msvcrt.LK_NBLCK if exclusive else msvcrt.LK_NBRLCK
        retry_delay = INITIAL_LOCK_RETRY_DELAY_MS / 1000.0  # Convert to seconds
        attempt = 0

        while True:
            try:
                msvcrt.locking(f.fileno(), lock_type, 1)
                break  # Lock acquired
            except OSError as e:
                attempt += 1
                elapsed = time.time() - start_time

                # Check timeout
                if elapsed >= timeout:
                    raise OSError(
                        f"Could not acquire file lock on {f.name} after {timeout}s "
                        f"({attempt} attempts). Another process may be holding the lock."
                    ) from e

                # Exponential backoff with cap
                current_delay = min(retry_delay, MAX_LOCK_RETRY_DELAY_MS / 1000.0)
                time.sleep(current_delay)
                retry_delay = min(
                    retry_delay * LOCK_TIMEOUT_MULTIPLIER,
                    MAX_LOCK_RETRY_DELAY_MS / 1000.0,
                )

        try:
            yield
        finally:
            try:
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass  # Already unlocked or file closed

    # Backward compatibility aliases
    def lock_file(f: Any, exclusive: bool = True) -> None:
        """Legacy function - use file_lock context manager instead."""
        start_time = time.time()
        lock_type = msvcrt.LK_NBLCK if exclusive else msvcrt.LK_NBRLCK
        retry_delay = INITIAL_LOCK_RETRY_DELAY_MS / 1000.0

        while True:
            try:
                msvcrt.locking(f.fileno(), lock_type, 1)
                return
            except OSError as e:
                if time.time() - start_time >= 5.0:
                    raise OSError(
                        f"Could not acquire file lock on {f.name}. "
                        "Another process may be holding the lock."
                    ) from e
                current_delay = min(retry_delay, MAX_LOCK_RETRY_DELAY_MS / 1000.0)
                time.sleep(current_delay)
                retry_delay = min(
                    retry_delay * LOCK_TIMEOUT_MULTIPLIER,
                    MAX_LOCK_RETRY_DELAY_MS / 1000.0,
                )

    def unlock_file(f: Any) -> None:
        """Legacy function - use file_lock context manager instead."""
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass  # Already unlocked

else:
    import fcntl

    @contextmanager
    def file_lock(
        f: Any, exclusive: bool = True, timeout: float = 5.0
    ) -> Iterator[None]:
        """
        Context manager for Unix file locking with exponential backoff retry.

        Uses fcntl.flock() with proper blocking behavior.
        Implements exponential backoff to handle high-contention scenarios.

        Args:
            f: File object to lock
            exclusive: True for exclusive lock, False for shared
            timeout: Maximum seconds to wait for lock (default 5.0)

        Raises:
            OSError: If lock cannot be acquired within timeout
        """
        # On Unix, flock() can block indefinitely, so we use non-blocking with retry
        start_time = time.time()
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        retry_delay = INITIAL_LOCK_RETRY_DELAY_MS / 1000.0
        attempt = 0

        while True:
            try:
                fcntl.flock(f, lock_type | fcntl.LOCK_NB)
                break  # Lock acquired
            except OSError as e:
                attempt += 1
                elapsed = time.time() - start_time

                # Check timeout
                if elapsed >= timeout:
                    raise OSError(
                        f"Could not acquire file lock on {f.name} after {timeout}s "
                        f"({attempt} attempts). Another process may be holding the lock."
                    ) from e

                # Exponential backoff with cap
                current_delay = min(retry_delay, MAX_LOCK_RETRY_DELAY_MS / 1000.0)
                time.sleep(current_delay)
                retry_delay = min(
                    retry_delay * LOCK_TIMEOUT_MULTIPLIER,
                    MAX_LOCK_RETRY_DELAY_MS / 1000.0),

        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    # Backward compatibility aliases
    def lock_file(f: Any, exclusive: bool = True) -> None:
        """Legacy function - use file_lock context manager instead."""
        start_time = time.time()
        lock_type = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        retry_delay = INITIAL_LOCK_RETRY_DELAY_MS / 1000.0

        while True:
            try:
                fcntl.flock(f, lock_type | fcntl.LOCK_NB)
                return
            except OSError as e:
                if time.time() - start_time >= 5.0:
                    raise OSError(
                        f"Could not acquire file lock on {f.name}. "
                        "Another process may be holding the lock."
                    ) from e
                current_delay = min(retry_delay, MAX_LOCK_RETRY_DELAY_MS / 1000.0)
                time.sleep(current_delay)
                retry_delay = min(
                    retry_delay * LOCK_TIMEOUT_MULTIPLIER,
                    MAX_LOCK_RETRY_DELAY_MS / 1000.0),

    def unlock_file(f: Any) -> None:
        """Legacy function - use file_lock context manager instead."""
        fcntl.flock(f, fcntl.LOCK_UN)


# Configuration
TDD_STATE_TTL_HOURS = 24
APPROVAL_TTL_MINUTES = 5
# CACHE_TTL_SECONDS removed - no longer using in-memory cache
# Legacy log directory - kept for debug/audit logs (shared across terminals)
# TDD state files now live at P:/.claude/state/tdd/{terminal_id}/
_LOG_DIR = hooks_dir / "hooks/.state/tdd-state"
TDD_ENABLED_FILE = _LOG_DIR / "tdd-enabled"  # Guard file for /tdd on/off
AUDIT_LOG = _LOG_DIR / "tdd_audit.log"
DEBUG_LOG = _LOG_DIR / "tdd_debug.log"
DEBUG_ENABLED = True  # TEMP: hardcoded for debugging. Revert to: os.environ.get("TDD_DEBUG", "").lower() in ("1", "true", "yes")

# Output parsing patterns for test result detection
PYTEST_PATTERNS = {
    "failed": re.compile(r"(\d+)\s+failed"),
    "passed": re.compile(r"(\d+)\s+passed"),
    "error": re.compile(r"(\d+)\s+error"),
    "collected": re.compile(r"collected\s+(\d+)\s+item"),
}

UNITTEST_PATTERNS = {
    "failed": re.compile(r"FAILED\s*\(.*failures=(\d+)"),
    "error": re.compile(r"FAILED\s*\(.*errors=(\d+)"),
    "ok": re.compile(r"^OK$", re.MULTILINE),
    "ran": re.compile(r"Ran\s+(\d+)\s+test"),
}


def debug_log(message: str) -> None:
    """Log debug message if DEBUG_ENABLED."""
    if not DEBUG_ENABLED:
        return
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        with open(DEBUG_LOG, "a") as f:
            f.write(f"{timestamp} {message}\n")
    except OSError:
        pass


def is_tdd_enabled() -> bool:
    """Check if TDD enforcement is enabled.

    Priority order:
    1. TDD_FORCE_DISABLED env var → False
    2. TDD_FORCE_ENABLED env var → True
    3. settings.json tdd.enforcement_mode == "enforced" → True
    4. settings.json tdd.enforcement_mode == "disabled" → False
    5. Guard file exists (tdd-enabled) → True (for /tdd on/off toggle)
    6. Default → False
    """
    # Env var overrides
    if os.environ.get("TDD_FORCE_DISABLED", "").lower() in ("1", "true", "yes"):
        return False
    if os.environ.get("TDD_FORCE_ENABLED", "").lower() in ("1", "true", "yes"):
        return True

    # Check settings.json enforcement_mode
    settings_path = hooks_dir.parent / "settings.json"
    if settings_path.exists():
        try:
            with open(settings_path) as f:
                settings = json.load(f)
            mode = settings.get("tdd", {}).get("enforcement_mode", "")
            if mode == "enforced":
                return True
            elif mode == "disabled":
                return False
            # mode == "optional" or unset → fall through to guard file
        except (json.JSONDecodeError, OSError):
            pass  # Settings unreadable, fall through

    # Guard file for /tdd on/off toggle (when mode is "optional")
    return TDD_ENABLED_FILE.exists()


def normalize_path(file_path: str) -> str:
    """Normalize path to canonical form for consistent hashing.

    - Converts to absolute path
    - Converts backslashes to forward slashes
    - Lowercases on Windows for case-insensitive matching
    """
    if not file_path:
        return ""

    path = Path(file_path)

    # Make absolute if relative
    if not path.is_absolute():
        path = Path.cwd() / path

    # Resolve to canonical form (resolves .., symlinks)
    try:
        path = path.resolve()
    except OSError:
        pass  # Path might not exist yet

    # Convert to forward slashes
    normalized = path.as_posix()

    # Lowercase on Windows for case-insensitive comparison
    if sys.platform == "win32":
        normalized = normalized.lower()

    debug_log(f"normalize_path: {file_path!r} -> {normalized!r}")
    return normalized


def find_project_root(start_path: str | Path) -> Path | None:
    """Find project root by walking up from start_path looking for config files.

    Prioritizes .git as the true project boundary (repository root) to ensure
    all files within the same repository resolve to the same root, even if
    there are nested project structures with their own config files.
    """
    path = Path(start_path)

    # If it's a file, start from its parent
    if path.is_file() or not path.exists():
        path = path.parent

    # First pass: look for .git (repository root - highest priority)
    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            debug_log(f"find_project_root: found .git at {parent}")
            return parent
        # Stop at drive root
        if parent == parent.parent:
            break

    # Second pass: look for other project markers
    other_markers = ["pyproject.toml", "pytest.ini", "setup.cfg", "setup.py"]

    for parent in [path] + list(path.parents):
        for marker in other_markers:
            if (parent / marker).exists():
                debug_log(f"find_project_root: found {marker} at {parent}")
                return parent
        # Stop at drive root
        if parent == parent.parent:
            break

    debug_log(f"find_project_root: no project root found from {start_path}")
    return None


def find_test_file(impl_file: str) -> str | None:
    """Find the corresponding test file for an implementation file.

    Maps implementation files to test files using common patterns:
    - src/module.py → tests/test_module.py
    - module.py → tests/test_module.py
    - package/module.py → tests/test_module.py or tests/package/test_module.py

    Args:
        impl_file: Path to implementation file

    Returns:
        Path to test file if found, None otherwise
    """
    impl_path = Path(impl_file)

    # Get the stem (filename without extension)
    stem = impl_path.stem

    # Common test directories to check
    project_root = find_project_root(impl_path)
    if not project_root:
        return None

    test_dirs = [
        project_root / "tests",
        project_root / "test",
        impl_path.parent.parent / "tests",
    ]

    # Test file name patterns
    test_patterns = [f"test_{stem}.py", f"{stem}_test.py"]

    for test_dir in test_dirs:
        if not test_dir.exists():
            continue
        for pattern in test_patterns:
            test_file = test_dir / pattern
            if test_file.exists():
                debug_log(f"find_test_file: found {test_file} for {impl_file}")
                return str(test_file)

    # Check package-specific tests (e.g., package/subpackage/module.py → tests/package/subpackage/test_module.py)
    rel_path = (
        impl_path.relative_to(project_root)
        if impl_path.is_relative_to(project_root)
        else impl_path
    )

    if "src" in rel_path.parts or "__csf" in rel_path.parts:
        # Skip src/ or __csf/ in path for test lookup
        parts = list(rel_path.parts)
        try:
            src_idx = parts.index("src") if "src" in parts else parts.index("__csf")
            parts = parts[src_idx + 1 :]  # Remove src/ or __csf/
        except ValueError:
            pass

        for test_dir in test_dirs:
            if not test_dir.exists():
                continue
            for pattern in test_patterns:
                test_file = test_dir / Path(*parts[:-1]) / pattern
                if test_file.exists():
                    debug_log(f"find_test_file: found {test_file} for {impl_file}")
                    return str(test_file)

    debug_log(f"find_test_file: no test file found for {impl_file}")
    return None


class TDDPhase(Enum):
    """TDD Cycle phases."""

    IDLE = "idle"
    DISCOVER = "discover"  # Phase 0: Understand code before testing
    AWAITING_RED = "awaiting_red"
    RED_CONFIRMED = "red_confirmed"
    GREEN_CONFIRMED = "green_confirmed"
    REFACTORING = "refactoring"

    @classmethod
    def from_string(cls, value: str) -> TDDPhase:
        """Safely parse phase string, defaulting to IDLE for invalid values."""
        if not value:
            return cls.IDLE

        # Try direct enum lookup
        try:
            return cls(value)
        except ValueError:
            pass

        # Handle legacy/abbreviated values
        legacy_map = {
            "green": cls.GREEN_CONFIRMED,
            "red": cls.RED_CONFIRMED,
            "awaiting": cls.AWAITING_RED,
            "refactor": cls.REFACTORING,
            "discover": cls.DISCOVER,
        }
        if value.lower() in legacy_map:
            debug_log(f"TDDPhase.from_string: converted legacy value {value!r}")
            return legacy_map[value.lower()]

        debug_log(f"TDDPhase.from_string: invalid value {value!r}, defaulting to IDLE")
        return cls.IDLE


class TDDState:
    """Manages TDD state for a specific test file."""

    def __init__(self, test_file: str | None = None):
        # Normalize test file path for consistent hashing
        self.test_file = normalize_path(test_file) if test_file else None
        self.state_file = self._resolve_state_file(self.test_file)
        self._ensure_state_dir()
        # NO CACHE - removed to prevent cross-process stale state issues
        debug_log(
            f"TDDState.__init__: test_file={self.test_file!r}, state_file={self.state_file}"
        )

    def _ensure_state_dir(self) -> None:
        """Create state directory if needed."""
        # Create the terminal-isolated directory for this instance
        # The state_file path already includes the terminal_id, so we just need to create parent
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def _resolve_state_file(self, test_file: str | None) -> Path:
        """Resolve state file path - keyed by TEST file with TERMINAL isolation.

        Terminal isolation: Using terminal_id ensures different terminal sessions
        have separate TDD state, preventing cross-terminal contamination.

        Worktree isolation: Removed cwd from hash - terminal_id provides all needed isolation.
        """
        # Import terminal detection for isolation
        from __lib.terminal_detection import detect_terminal_id

        # Get terminal ID for isolation
        terminal_id = detect_terminal_id()

        # Terminal-isolated state directory
        state_dir = Path("P:/.claude/state/tdd") / terminal_id
        state_dir.mkdir(parents=True, exist_ok=True)

        if test_file:
            # Use only test_file for keying (no cwd) - terminal_id provides isolation
            file_key = hashlib.md5(test_file.encode()).hexdigest()[:12]
            return state_dir / f"tdd.{file_key}.json"
        return state_dir / "tdd.default.json"

    def load(self) -> dict[str, Any]:
        """Load state with file locking - NO CACHE for cross-process consistency."""
        # Direct file read every time - no cache to avoid stale state across processes
        if not self.state_file.exists():
            debug_log(f"TDDState.load: {self.state_file} not found, returning default")
            return self._default_state()

        lock_file_path = self.state_file.with_suffix(".lock")

        try:
            # Acquire cross-process lock (shared access via same lock file)
            with _lock_file_lockfile(lock_file_path, timeout=10.0):
                with open(self.state_file) as f:
                    state = cast(dict[str, Any], json.load(f))

                # Check TTL
                if self._is_expired(state):
                    debug_log("TDDState.load: state expired, returning default")
                    return self._default_state()

                debug_log(
                    f"TDDState.load: loaded phase={state.get('phase')}, test_file={state.get('test_file')}"
                )

                return state

        except json.JSONDecodeError as e:
            # Re-raise with context for proper error handling
            # Include path twice - once as-is for str(state_file) matching, once with detail
            error_msg = (
                f"JSON decode error at {self.state_file}: {e.msg} "
                f"(line {e.lineno}, column {e.colno})"
            )

            debug_log(f"TDDState.load: {error_msg}")
            raise json.JSONDecodeError(
                msg=error_msg,
                doc=e.doc,
                pos=e.pos
            ) from e
        except OSError as e:
            # Re-raise with context for proper error handling
            error_msg = f"OS error reading {self.state_file}: {e}"
            debug_log(f"TDDState.load: {error_msg}")
            raise OSError(error_msg) from e

    def save(self, state: dict[str, Any]) -> None:
        """Save state with atomic write pattern and cross-process file locking.

        Uses a lock file for synchronization to handle Windows file locking issues.
        The write pattern ensures no corruption under concurrent access:

        1. Acquire lock file (cross-process synchronization)
        2. Write to temporary file in same directory
        3. Fsync to ensure data is written to disk
        4. Rename temp file to target file (atomic within lock protection)
        5. Release lock file

        The lock file approach is used on Windows because msvcrt.locking()
        doesn't coordinate properly with Path.replace() for atomic writes.
        """
        state["updated_at"] = datetime.now().isoformat()

        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        debug_log(
            f"TDDState.save: phase={state.get('phase')}, test_file={state.get('test_file')} -> {self.state_file}"
        )

        # Use lock file for cross-process synchronization
        lock_file_path = self.state_file.with_suffix(".lock")

        try:
            # Acquire cross-process lock
            with _lock_file_lockfile(lock_file_path, timeout=10.0):
                # Create temporary file in same directory as target for atomic rename
                temp_file = self.state_file.with_suffix(".tmp")

                try:
                    # Write to temp file
                    with open(temp_file, "w") as f:
                        json.dump(state, f, indent=2)
                        f.flush()
                        os.fsync(f.fileno())  # Ensure data is written to disk

                    # Atomic rename (safe within lock protection)
                    temp_file.replace(self.state_file)

                    debug_log(f"TDDState.save: successfully saved to {self.state_file}")

                except Exception:
                    # Clean up temp file on error
                    if temp_file.exists():
                        try:
                            temp_file.unlink()
                        except OSError:
                            pass  # Best effort cleanup
                    raise

        except Exception as e:
            debug_log(f"TDDState.save: error saving state: {e}")
            raise

    def _default_state(self) -> dict[str, Any]:
        """Create fresh IDLE state."""
        return {
            "phase": TDDPhase.IDLE.value,
            "test_file": self.test_file,
            "impl_files": [],
            "last_test_result": None,
            "last_test_exit_code": None,
            "last_test_time": None,
            "approval": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "discovery_evidence": {
                "static_analysis": {"files_read": [], "imports_found": []},
                "dynamic_analysis": {
                    "baseline_command": None,
                    "baseline_results": None,
                },
                "timestamp": None,
                "complete": False,
            },
        }

    def _is_expired(self, state: dict[str, Any]) -> bool:
        """Check if state has expired based on TTL."""
        created_str = state.get("created_at")
        if not created_str:
            return True
        try:
            created = datetime.fromisoformat(created_str)
            return datetime.now() - created > timedelta(hours=TDD_STATE_TTL_HOURS)
        except ValueError:
            return True


class TDDConfig:
    """Reads test configuration from pytest.ini or pyproject.toml."""

    def __init__(self, project_root: Path | None = None, file_hint: str | None = None):
        """Initialize config.

        Args:
            project_root: Explicit project root path
            file_hint: A file path to use for finding project root if not specified
        """
        if project_root:
            self.project_root = project_root
        elif file_hint:
            self.project_root = find_project_root(file_hint) or Path.cwd()
        else:
            self.project_root = Path.cwd()

        self._config = self._load_config()
        debug_log(
            f"TDDConfig.__init__: project_root={self.project_root}, configured={self.is_configured()}"
        )

    def _load_config(self) -> dict[str, Any]:
        """Load pytest config from project files."""
        config = {
            "testpaths": [],
            "python_files": ["test_*.py", "*_test.py"],
            "python_classes": ["Test*"],
            "python_functions": ["test_*"],
        }

        # Try pyproject.toml first
        pyproject = self.project_root / "pyproject.toml"
        if pyproject.exists():
            try:
                # Python 3.11+ has tomllib built-in
                import tomllib

                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                pytest_config = (
                    data.get("tool", {}).get("pytest", {}).get("ini_options", {})
                )

                if pytest_config:
                    config.update(pytest_config)
                    return config
            except ImportError:
                pass  # tomllib not available
            except (OSError, tomllib.TOMLDecodeError):
                pass  # Invalid TOML or file read error

        # Try pytest.ini
        pytest_ini = self.project_root / "pytest.ini"
        if pytest_ini.exists():
            try:
                import configparser

                parser = configparser.ConfigParser()
                parser.read(pytest_ini)
                if "pytest" in parser:
                    for key in ["testpaths", "python_files"]:
                        if key in parser["pytest"]:
                            value = parser["pytest"][key]
                            config[key] = [v.strip() for v in value.split()]
            except (OSError, configparser.Error):
                pass  # Invalid INI or file read error

        return config

    def is_test_file(self, file_path: str) -> bool:
        """Check if file matches test patterns from features.config."""
        path = Path(file_path)
        name = path.name.lower()

        # Check python_files patterns
        for pattern in self._config.get("python_files", []):
            pattern_lower = pattern.lower()
            if pattern_lower.startswith("*") and name.endswith(pattern_lower[1:]):
                debug_log(f"is_test_file: {file_path} matches pattern {pattern}")
                return True
            if pattern_lower.endswith("*") and name.startswith(pattern_lower[:-1]):
                debug_log(f"is_test_file: {file_path} matches pattern {pattern}")
                return True
            if "*" in pattern_lower:
                # Convert glob to regex
                regex = pattern_lower.replace(".", r"\.").replace("*", ".*")
                if re.match(regex, name):
                    debug_log(f"is_test_file: {file_path} matches regex {regex}")
                    return True

        # Check testpaths directories
        path_str = path.as_posix().lower()
        for testpath in self._config.get("testpaths", []):
            if testpath.lower() in path_str:
                debug_log(f"is_test_file: {file_path} in testpath {testpath}")
                return True

        # Fallback: common patterns
        if name.startswith("test_") or name.endswith("_test.py"):
            debug_log(f"is_test_file: {file_path} matches fallback pattern")
            return True
        if (
            "/tests/" in path_str
            or "/test/" in path_str
            or "\\tests\\" in file_path.lower()
            or "\\test\\" in file_path.lower()
        ):
            debug_log(f"is_test_file: {file_path} in tests directory")
            return True

        debug_log(f"is_test_file: {file_path} is NOT a test file")
        return False

    def is_configured(self) -> bool:
        """Check if pytest config exists in project."""
        configured = (
            (self.project_root / "pyproject.toml").exists()
            or (self.project_root / "pytest.ini").exists()
            or (self.project_root / "setup.cfg").exists()
        )

        debug_log(f"is_configured: {configured} (project_root={self.project_root})")
        return configured


class TDDApproval:
    """Manages human approval for escape hatch."""

    @staticmethod
    def grant(state: dict[str, Any], reason: str = "human_override") -> dict[str, Any]:
        """Grant approval for current phase transition."""
        state["approval"] = {
            "approved_at": datetime.now().isoformat(),
            "expires_at": (
                datetime.now() + timedelta(minutes=APPROVAL_TTL_MINUTES)
            ).isoformat(),
            "reason": reason,
        }
        TDDApproval._audit_log(
            "APPROVAL_GRANTED", state.get("test_file", "unknown"), reason
        )

        return state

    @staticmethod
    def is_valid(state: dict[str, Any]) -> bool:
        """Check if current approval is still valid."""
        approval = state.get("approval")
        if not approval:
            return False
        try:
            expires = datetime.fromisoformat(approval["expires_at"])
            return datetime.now() < expires
        except (KeyError, ValueError):
            return False

    @staticmethod
    def clear(state: dict[str, Any]) -> dict[str, Any]:
        """Clear approval after use or expiry."""
        if state.get("approval"):
            TDDApproval._audit_log(
                "APPROVAL_CLEARED", state.get("test_file", "unknown"), "used_or_expired"
            )

            state["approval"] = None
        return state

    @staticmethod
    def _audit_log(event: str, test_file: str, reason: str) -> None:
        """Append to audit log."""
        try:
            AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().isoformat()
            with open(AUDIT_LOG, "a") as f:
                f.write(f"{timestamp} {event} {test_file} reason={reason}\n")
        except OSError:
            pass  # Don't fail on audit log errors


class TestResultParser:
    """Parses test runner output to determine pass/fail."""

    # Python error patterns that indicate test failure
    ERROR_PATTERNS = [
        re.compile(r"ModuleNotFoundError:", re.IGNORECASE),
        re.compile(r"ImportError:", re.IGNORECASE),
        re.compile(r"SyntaxError:", re.IGNORECASE),
        re.compile(r"NameError:", re.IGNORECASE),
        re.compile(r"AttributeError:", re.IGNORECASE),
        re.compile(r"TypeError:", re.IGNORECASE),
        re.compile(r"AssertionError:", re.IGNORECASE),
        re.compile(r"FAILED\s+\w+", re.IGNORECASE),  # pytest FAILED marker
        re.compile(r"ERROR\s+\w+", re.IGNORECASE),  # pytest ERROR marker
    ]

    @staticmethod
    def parse(stdout: str, stderr: str, exit_code: int) -> dict[str, Any]:
        """Parse test output and return structured result."""
        combined = stdout + "\n" + stderr
        result: dict[str, Any] = {
            "exit_code": exit_code,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "total": 0,
            "is_test_output": False,
            "verdict": "unknown",
        }

        # Check for Python error patterns first (handles piped commands where exit code is wrong)
        for pattern in TestResultParser.ERROR_PATTERNS:
            if pattern.search(combined):
                result["is_test_output"] = True
                result["errors"] = 1
                result["verdict"] = "failed"
                debug_log(f"TestResultParser: detected error pattern {pattern.pattern}")
                # Don't return yet - continue to get more detail from pytest patterns

        # Try pytest patterns
        for key, pattern in PYTEST_PATTERNS.items():
            match = pattern.search(combined)
            if match:
                result["is_test_output"] = True
                if key == "failed":
                    result["failed"] = int(match.group(1))
                elif key == "passed":
                    result["passed"] = int(match.group(1))
                elif key == "error":
                    result["errors"] = int(match.group(1))
                elif key == "collected":
                    result["total"] = int(match.group(1))

        # Try unittest patterns if pytest didn't match
        if not result["is_test_output"]:
            for key, pattern in UNITTEST_PATTERNS.items():
                match = pattern.search(combined)
                if match:
                    result["is_test_output"] = True
                    if key == "failed":
                        result["failed"] = int(match.group(1))
                    elif key == "error":
                        result["errors"] = int(match.group(1))
                    elif key == "ran":
                        result["total"] = int(match.group(1))
                    elif key == "ok":
                        result["verdict"] = "passed"

        # Determine verdict (re-evaluate based on all evidence)
        if result["is_test_output"]:
            if (
                cast(int, result.get("failed", 0)) > 0
                or cast(int, result.get("errors", 0)) > 0
            ):
                result["verdict"] = "failed"
            elif cast(int, result.get("passed", 0)) > 0:
                result["verdict"] = "passed"
            elif (
                result["verdict"] != "failed"
            ):  # Don't override error pattern detection
                if exit_code != 0:
                    result["verdict"] = "failed"
                else:
                    result["verdict"] = "passed"
        else:
            # Fallback to exit code only
            result["verdict"] = "failed" if exit_code != 0 else "unknown"

        debug_log(
            f"TestResultParser.parse: exit_code={exit_code}, verdict={result['verdict']}, is_test_output={result['is_test_output']}, failed={result['failed']}, errors={result['errors']}"
        )

        return result


# Bash file-write patterns to guard
BASH_WRITE_PATTERNS = [
    re.compile(r">\s*['\"]?[\w./-]+\.py['\"]?"),  # > file.py
    re.compile(r"cat\s*>\s*['\"]?[\w./-]+\.py"),  # cat > file.py
    re.compile(r"echo\s+.*>\s*['\"]?[\w./-]+\.py"),  # echo ... > file.py
    re.compile(r"tee\s+['\"]?[\w./-]+\.py"),  # tee file.py
    re.compile(r"printf\s+.*>\s*['\"]?[\w./-]+\.py"),  # printf > file.py
    # Python heredocs (bypass TDD by embedding Python in Bash)
    re.compile(r"python\s*<<\s*['\"]?EOF['\"]?"),  # python << 'EOF' or python << "EOF"
    re.compile(r"python\s*<<\s*['\"]?HEREDOC['\"]?"),  # python << 'HEREDOC"
    re.compile(r"python\s*-c\s*['\"]\.write\s*\("),  # python -c "...write("
    re.compile(r"python\s*-c\s*['\"]\.write_text\s*\("),  # python -c "...write_text("
    re.compile(r"Path\s*\([^)]+\)\.write_text\s*\("),  # Path(...).write_text(
    re.compile(r"open\s*\([^)]+,\s*['\"]w['\"]"),  # open(..., 'w')
]


def detect_bash_file_write(command: str) -> str | None:
    """Detect if bash command writes to a Python file. Returns filename or None."""
    for pattern in BASH_WRITE_PATTERNS:
        match = pattern.search(command)
        if match:
            # Extract filename from match
            # This is approximate - covers common cases
            file_match = re.search(r"[\w./-]+\.py", match.group())
            if file_match:
                return file_match.group()
    return None


def is_test_command(command: str) -> bool:
    """Check if bash command runs tests."""
    test_indicators = [
        "pytest",
        "python -m pytest",
        "python -m unittest",
        "npm test",
        "yarn test",
        "pnpm test",
        "go test",
        "cargo test",
        "mvn test",
        "gradle test",
    ]
    command_lower = command.lower()
    return any(indicator in command_lower for indicator in test_indicators)


def extract_test_file_from_command(command: str) -> str | None:
    """Extract test file path from a test command.

    Looks for patterns like:
    - pytest tests/test_foo.py
    - pytest path/to/test_foo.py
    - python -m pytest tests/test_foo.py
    - pytest tests/test_foo.py::TestClass::test_method  (node ID — strip suffix)
    """
    import shlex

    try:
        parts = shlex.split(command)
    except ValueError:
        parts = command.split()

    for part in parts:
        # Strip pytest node ID suffix (::Class::method) so targeted runs and
        # full-suite runs resolve to the same state file key.
        file_part = part.split("::")[0] if "::" in part else part
        file_part_lower = file_part.lower()
        if file_part_lower.endswith(".py"):
            name = Path(file_part).name.lower()
            if name.startswith("test_") or name.endswith("_test.py"):
                debug_log(f"extract_test_file_from_command: found {file_part} (from {part!r})")
                return normalize_path(file_part)

    debug_log(f"extract_test_file_from_command: no test file found in {command[:50]}")
    return None


def find_pytest_json_report(project_root: Path | None = None) -> dict[str, Any] | None:
    """Find and parse the most recent pytest-json-report output.

    pytest-json-report writes to .report.json by default.
    Returns parsed JSON or None if not found/invalid.
    """
    search_paths: list[Path] = []

    if project_root:
        search_paths.append(project_root / ".report.json")
        search_paths.append(project_root / "report.json")
        search_paths.append(project_root / ".pytest_cache" / "report.json")

    # Also check common locations
    search_paths.extend(
        [
            Path.cwd() / ".report.json",
            PROJECT_ROOT / "__csf" / ".report.json",
            PROJECT_ROOT / "__csf" / "report.json",
        ]
    )

    for report_path in search_paths:
        if report_path.exists():
            try:
                # Check if report is recent (within last 30 seconds)
                import time

                mtime = report_path.stat().st_mtime
                age = time.time() - mtime
                if age > 30:
                    debug_log(
                        f"find_pytest_json_report: {report_path} too old ({age:.1f}s)"
                    )

                    continue

                with open(report_path) as f:
                    data = cast(dict[str, Any], json.load(f))
                debug_log(
                    f"find_pytest_json_report: found recent report at {report_path}"
                )

                return data
            except (json.JSONDecodeError, OSError) as e:
                debug_log(f"find_pytest_json_report: error reading {report_path}: {e}")
                continue

    debug_log("find_pytest_json_report: no recent report found")
    return None


def parse_pytest_json_report(report: dict[str, Any]) -> dict[str, Any]:
    """Parse pytest-json-report output into our result format."""
    result: dict[str, Any] = {
        "exit_code": report.get("exitcode", 0),
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "total": 0,
        "is_test_output": True,
        "verdict": "unknown",
    }

    summary = report.get("summary", {})
    result["passed"] = summary.get("passed", 0)
    result["failed"] = summary.get("failed", 0)
    result["errors"] = summary.get("error", 0)
    result["total"] = summary.get("total", 0)

    # Determine verdict
    if result["failed"] > 0 or result["errors"] > 0:
        result["verdict"] = "failed"
    elif result["passed"] > 0:
        result["verdict"] = "passed"
    elif report.get("exitcode", 0) != 0:
        result["verdict"] = "failed"
    else:
        result["verdict"] = "passed"

    debug_log(
        f"parse_pytest_json_report: verdict={result['verdict']}, passed={result['passed']}, failed={result['failed']}"
    )

    return result


def find_state_for_impl(impl_file: str) -> TDDState | None:
    """Find TDD state that includes this impl file."""
    from __lib.terminal_detection import detect_terminal_id

    terminal_id = detect_terminal_id()
    state_dir = Path("P:/.claude/state/tdd") / terminal_id

    if not state_dir.exists():
        return None

    # Normalize for comparison
    impl_normalized = normalize_path(impl_file)

    for state_file in state_dir.glob("tdd.*.json"):
        if state_file.name == "tdd.default.json":
            continue
        try:
            with open(state_file) as f:
                state = cast(dict[str, Any], json.load(f))
            impl_files = state.get("impl_files", [])
            # Check both raw and normalized
            if impl_file in impl_files or impl_normalized in impl_files:
                debug_log(f"find_state_for_impl: found state for {impl_file}")
                return TDDState(state.get("test_file"))
        except (json.JSONDecodeError, OSError):
            continue

    debug_log(f"find_state_for_impl: no state found for {impl_file}")
    return None


def find_active_tdd_cycle() -> TDDState | None:
    """Find any active TDD cycle (not IDLE) across all terminal directories."""
    # Import terminal detection
    from __lib.terminal_detection import detect_terminal_id

    # Get terminal-isolated state directory
    terminal_id = detect_terminal_id()
    state_dir = Path("P:/.claude/state/tdd") / terminal_id

    if not state_dir.exists():
        debug_log("find_active_tdd_cycle: terminal state directory does not exist")
        return None

    for state_file in state_dir.glob("tdd.*.json"):
        try:
            with open(state_file) as f:
                state = cast(dict[str, Any], json.load(f))
            phase = state.get("phase", TDDPhase.IDLE.value)
            if phase != TDDPhase.IDLE.value:
                test_file = state.get("test_file")
                debug_log(
                    f"find_active_tdd_cycle: found active cycle phase={phase}, test_file={test_file}"
                )

                return TDDState(test_file)
        except (json.JSONDecodeError, OSError):
            continue

    debug_log("find_active_tdd_cycle: no active cycle found")
    return None


def cleanup_expired_states() -> None:
    """Remove expired state files across all terminal directories."""
    # Use parent of STATE_DIR as the base TDD state directory
    tdd_base_dir = Path("P:/.claude/state/tdd")
    if not tdd_base_dir.exists():
        return

    cutoff = datetime.now() - timedelta(hours=TDD_STATE_TTL_HOURS)

    # Scan all terminal subdirectories
    for terminal_dir in tdd_base_dir.iterdir():
        if not terminal_dir.is_dir():
            continue

        for state_file in terminal_dir.glob("tdd.*.json"):
            try:
                with open(state_file) as f:
                    state = cast(dict[str, Any], json.load(f))
                created_str = state.get("created_at")
                if created_str:
                    created = datetime.fromisoformat(created_str)
                    if created < cutoff:
                        state_file.unlink()
                        debug_log(f"cleanup_expired_states: deleted {state_file}")
            except (json.JSONDecodeError, OSError, ValueError):
                pass  # Skip invalid files


# ==============================================================================
# AUTO-REGRESSION: Run related tests after GREEN phase
# ==============================================================================


def get_git_changed_files() -> list[str]:
    """Get list of changed Python files in this session (last 30 minutes)."""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD@{'30 minutes ago'}"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path.cwd()
        )

        if result.returncode == 0:
            return [f for f in result.stdout.strip().split("\n") if f.endswith(".py")]
    except (OSError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass  # Git not available or subprocess failed
    return []


def find_related_tests(changed_files: list[str]) -> list[str]:
    """Find test files related to changed source files.

    Rules:
    - src/X.py → tests/test_X.py
    - src/X/y.py → tests/X/test_y.py or tests/test_X.py
    - tests/test_X.py → run other tests in same directory
    """
    related = set()
    project_root = Path.cwd()

    for changed in changed_files:
        changed_path = Path(changed)
        rel_path = (
            changed_path.relative_to(project_root)
            if changed_path.is_absolute()
            else changed_path
        )

        parts = rel_path.parts
        if parts[0] == "src":
            # src/module/file.py → tests/test_module.py
            module = parts[1] if len(parts) > 1 else None

            if module:
                # Pattern 1: tests/test_{module}.py
                test_path = project_root / "tests" / f"test_{module}.py"
                if test_path.exists():
                    related.add(str(test_path))

                # Pattern 2: tests/{module}/test_*.py
                test_dir = project_root / "tests" / module
                if test_dir.is_dir():
                    for test_file in test_dir.glob("test_*.py"):
                        related.add(str(test_file))

                # Pattern 3: tests/test_*.py containing module name
                tests_dir = project_root / "tests"
                if tests_dir.is_dir():
                    for test_file in tests_dir.glob("test_*.py"):
                        if module in test_file.stem:
                            related.add(str(test_file))

        elif parts[0] == "tests":
            # If test file changed, run other tests in same directory
            test_dir = project_root / "tests"
            if test_dir.is_dir():
                for test_file in test_dir.glob("test_*.py"):
                    if test_file != changed_path:
                        related.add(str(test_file))

    return sorted(related)


def should_run_integration_tests(changed_files: list[str]) -> bool:
    """Determine if integration tests should run based on what changed.

    Integration tests run when:
    - Core utilities changed (lib/, utils/, core/)
    - Database/storage layers changed
    - API interfaces changed
    - Hooks changed
    """
    core_patterns = [
        "/lib/",
        "/utils/",
        "/core/",
        "/database/",
        "/storage/",
        "/api/",
        "/backends/",
        "/hooks/",
        "instant_check.py",
        "tdd_core.py",
    ]

    for file in changed_files:
        for pattern in core_patterns:
            if pattern in file or f"/{pattern}" in file:
                return True
    return False


def run_regression_tests(
    impl_file: str, test_file: str | None = None
) -> dict[str, Any]:
    """Run regression tests after GREEN phase.

    Args:
        impl_file: The implementation file that was just modified
        test_file: The test file that just passed

    Returns:
        Dict with 'passed', 'output', 'related_count', 'integration_ran'
    """
    import subprocess

    # Get changed files to find related tests
    changed_files = get_git_changed_files()
    if not changed_files:
        return {
            "passed": True,
            "output": "No recent changes detected",
            "related_count": 0,
            "integration_ran": False,
        }

    # Find related tests
    related_tests = find_related_tests(changed_files)

    # Exclude the test file that just passed (already ran)
    if test_file:
        test_path = Path(test_file).resolve()
        related_tests = [t for t in related_tests if Path(t).resolve() != test_path]

    # Check if we should run integration tests
    run_integration = should_run_integration_tests(changed_files)

    results = []
    all_passed = True

    # Run related tests
    if related_tests:
        limit = int(os.getenv("TDD_REGRESSION_MAX_TESTS", "10"))
        related_tests = related_tests[:limit]

        debug_log(f"run_regression_tests: running {len(related_tests)} related test(s)")

        cmd = ["python", "-m", "pytest", "-v", "--tb=short"] + related_tests
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute max
                cwd=Path.cwd()
            )

            if result.returncode != 0:
                all_passed = False
                results.append(
                    {
                        "type": "related",
                        "passed": False,
                        "output": result.stdout + result.stderr,
                        "count": len(related_tests),
                    }
                )

        except subprocess.TimeoutExpired:
            all_passed = False
            results.append(
                {
                    "type": "related",
                    "passed": False,
                    "output": "Tests timed out",
                    "count": len(related_tests),
                }
            )

        except Exception as e:
            all_passed = False
            results.append(
                {
                    "type": "related",
                    "passed": False,
                    "output": str(e),
                    "count": len(related_tests),
                }
            )

    # Run integration tests if needed
    integration_output = ""
    if run_integration:
        debug_log("run_regression_tests: running integration tests")
        cmd = ["python", "-m", "pytest", "-v", "-k", "integration", "--tb=short"]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute max
                cwd=Path.cwd()
            )

            if result.returncode != 0:
                all_passed = False
                integration_output = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            all_passed = False
            integration_output = "Integration tests timed out"
        except Exception as e:
            all_passed = False
            integration_output = str(e)

    # Build output
    output_parts = []
    if all_passed:
        if related_tests:
            output_parts.append(f"✓ {len(related_tests)} related test(s) passed")
        if run_integration:
            output_parts.append("✓ Integration tests passed")
        if not output_parts:
            output_parts.append("No regression issues detected")
    else:
        if related_tests:
            output_parts.append("⚠ Some regression tests failed")
        if run_integration:
            output_parts.append("⚠ Integration tests failed")

    return {
        "passed": all_passed,
        "output": "\n".join(output_parts),
        "details": results,
        "integration_output": integration_output if not all_passed else "",
        "related_count": len(related_tests),
        "integration_ran": run_integration,
    }
