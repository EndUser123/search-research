#!/usr/bin/env python3
"""
SessionStart hook: Auto-start search daemon on session activation.

This hook ensures the search daemon is running when a Claude Code session starts.
It performs health checks based on heartbeat age and auto-starts the daemon if needed.

The search daemon manages search operations and indexing, providing fast semantic
search capabilities for CKS and CHS.

Features:
- Heartbeat-based health checks (90s threshold)
- Windows-specific daemon startup (pythonw.exe, CREATE_NO_WINDOW)
- Latency measurement and instrumentation
- Graceful degradation on errors

Usage:
    Called automatically by Claude Code on session start.
    Can be run manually for testing: python SessionStart_search_daemon.py
"""

import logging
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Try to import diagnostics logger for timing logs
try:
    from cc_diagnostic_logger import log_hook_invocation

    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False
    log_hook_invocation = None

# Import dreaming daemon modules (shared with dreaming daemon)
from dreaming_config import load_config
from dreaming_state import load_state

# Try to import pywin32 for Windows mutex (optional - graceful degradation if missing)
try:
    import win32api
    import win32event
    import winerror

    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    logging.warning("pywin32 not available - multi-terminal coordination disabled")

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants
HEARTBEAT_HEALTHY_THRESHOLD_SECONDS = 90  # Daemon is healthy if heartbeat < 90s old
LATENCY_WARNING_THRESHOLD_MS = 100  # Warn if state read takes >100ms

# Paths
HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / "state"
STATE_FILE = STATE_DIR / "search-daemon-state.json"

# Import daemon config for mutex and PID file paths
try:
    from config.daemon_config import get_daemon_config

    DAEMON_CONFIG = get_daemon_config("search")
    MUTEX_NAME = DAEMON_CONFIG["mutex_name"]
    PID_FILE = STATE_DIR / DAEMON_CONFIG["pid_file"]
except (ImportError, KeyError) as e:
    logger.warning(f"Could not load daemon config: {e}")
    MUTEX_NAME = r"Global\ClaudeSearchDaemon"
    PID_FILE = STATE_DIR / "search-daemon.pid"


def get_project_root() -> Path:
    """Find project root by searching for marker files."""
    script_path = Path(__file__).resolve()
    current = script_path.parent

    # Search upward for project root markers
    for _ in range(10):  # Max 10 levels up
        markers = [
            current / ".claude",
            current / "CLAUDE.md",
            current / "src",
            current / "pyproject.toml",
        ]
        if any(m.exists() for m in markers):
            return current
        parent = current.parent
        if parent == current:  # Reached filesystem root
            break
        current = parent

    # Fallback: use script's parent.parent.parent (hook → .claude → project)
    return script_path.parent.parent.parent


def measure_latency(func, *args, **kwargs) -> tuple[Any, float]:
    """
    Measure function execution time in milliseconds.

    Args:
        func: Function to execute.
        *args: Positional arguments for func.
        **kwargs: Keyword arguments for func.

    Returns:
        Tuple of (result, latency_ms)

    Raises:
        Exceptions from func are propagated.
    """
    start = time.perf_counter()
    try:
        result = func(*args, **kwargs)
        return result, (time.perf_counter() - start) * 1000
    except Exception as e:
        # Re-raise with latency info
        latency_ms = (time.perf_counter() - start) * 1000
        logger.error(f"Function {func.__name__} failed after {latency_ms:.2f}ms: {e}")
        raise


def is_daemon_healthy(state_path: Path) -> bool:
    """
    Check if daemon is healthy based on heartbeat age.

    Args:
        state_path: Path to search-daemon-state.json.

    Returns:
        True if daemon is healthy (heartbeat < 90s old), False otherwise.
    """
    try:
        if not state_path.exists():
            logger.debug("Daemon state file missing - daemon not running")
            return False

        # Load state with latency measurement
        state, latency_ms = measure_latency(load_state, state_path)

        # Log latency warnings
        if latency_ms > LATENCY_WARNING_THRESHOLD_MS:
            logger.warning(
                f"State file read took {latency_ms:.2f}ms "
                f"(exceeds {LATENCY_WARNING_THRESHOLD_MS}ms threshold)"
            )

        # Check heartbeat
        if not state.heartbeat:
            logger.debug("No heartbeat in state file - daemon unhealthy")
            return False

        # Parse heartbeat timestamp
        try:
            heartbeat_time = datetime.fromisoformat(state.heartbeat)
            age_seconds = (datetime.now(UTC) - heartbeat_time).total_seconds()

            if age_seconds < HEARTBEAT_HEALTHY_THRESHOLD_SECONDS:
                logger.debug(f"Daemon healthy - heartbeat {age_seconds:.0f}s old")
                return True
            else:
                logger.debug(
                    f"Daemon unhealthy - heartbeat {age_seconds:.0f}s old "
                    f"(exceeds {HEARTBEAT_HEALTHY_THRESHOLD_SECONDS}s threshold)"
                )
                return False

        except (ValueError, OSError) as e:
            logger.error(f"Error parsing heartbeat timestamp: {e}")
            return False

    except Exception as e:
        logger.error(f"Error checking daemon health: {e}")
        return False


def acquire_startup_mutex() -> Any | None:
    """
    Acquire Windows mutex for daemon startup coordination.

    Prevents multiple terminals from starting the daemon simultaneously.

    Returns:
        Mutex handle if acquired, None if pywin32 unavailable or mutex already exists.
    """
    if not PYWIN32_AVAILABLE:
        logger.debug("pywin32 unavailable - skipping mutex acquisition")
        return None

    try:
        mutex_handle = win32event.CreateMutexW(None, False, MUTEX_NAME)
        last_error = win32api.GetLastError()

        if last_error == winerror.ERROR_ALREADY_EXISTS:
            logger.debug("Startup mutex already exists - another terminal is starting daemon")
            win32api.CloseHandle(mutex_handle)
            return None

        logger.debug("Acquired startup mutex for daemon startup")
        return mutex_handle

    except Exception as e:
        logger.error(f"Failed to acquire startup mutex: {e}")
        return None


def release_startup_mutex(mutex_handle: Any) -> None:
    """
    Release Windows mutex after daemon startup complete.

    Args:
        mutex_handle: Mutex handle to release.
    """
    if not PYWIN32_AVAILABLE or mutex_handle is None:
        return

    try:
        win32api.CloseHandle(mutex_handle)
        logger.debug("Released startup mutex")
    except Exception as e:
        logger.error(f"Failed to release startup mutex: {e}")


def start_daemon(project_root: Path, config: dict, mutex_handle: Any | None = None) -> int | None:
    """
    Start the search daemon and return its PID.

    Args:
        project_root: Project root directory.
        config: Daemon configuration dict.
        mutex_handle: Optional mutex handle for startup coordination.

    Returns:
        PID of started daemon, or None if startup failed.
    """
    try:
        # Determine python executable
        # On Windows, use pythonw.exe to avoid console window
        if sys.platform == "win32" and "python.exe" in sys.executable:
            python_exe = sys.executable.replace("python.exe", "pythonw.exe")
        else:
            python_exe = sys.executable

        # Build command: python -m dreaming_daemon --daemon-type search
        # Note: dreaming_daemon.py is in hooks directory
        cmd = [python_exe, "-m", "dreaming_daemon", "--daemon-type", "search"]

        # Set up creation flags for Windows (no console window)
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW

        # Start daemon process
        proc = subprocess.Popen(
            cmd,
            cwd=HOOKS_DIR,  # Run from hooks directory so -m dreaming_daemon works
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )

        logger.info(f"Started search daemon PID {proc.pid}")

        # Release mutex after successful startup
        if mutex_handle is not None:
            release_startup_mutex(mutex_handle)

        return proc.pid

    except Exception as e:
        logger.error(f"Failed to start daemon: {e}")

        # Release mutex on failure
        if mutex_handle is not None:
            release_startup_mutex(mutex_handle)

        return None


def main() -> dict[str, Any]:
    """
    Hook entry point - check daemon health and start if needed.

    Returns:
        Dict with status and metadata.

        Status values:
        - "healthy": Daemon is running and healthy
        - "started": Daemon was started successfully
        - "failed": Daemon startup failed
    """
    hook_start = time.perf_counter()

    # Get project root
    project_root = get_project_root()
    logger.debug(f"Project root: {project_root}")

    # Load configuration
    config = load_config()

    # Check if daemon is already healthy
    if is_daemon_healthy(STATE_FILE):
        logger.info("Search daemon is healthy - no action needed")

        hook_latency = (time.perf_counter() - hook_start) * 1000
        logger.debug(f"Hook completed in {hook_latency:.2f}ms")

        # Log to diagnostics
        if DIAGNOSTICS_AVAILABLE and log_hook_invocation:
            try:
                log_hook_invocation(
                    hook_name="SessionStart_search_daemon",
                    event_type="SessionStart",
                    action="pass",
                    reason=f"Daemon healthy, latency: {hook_latency:.0f}ms",
                    duration_ms=hook_latency,
                )
            except Exception:
                pass

        # Hook protocol: print empty dict
        print({})

        return {
            "status": "healthy",
            "project_root": str(project_root),
            "hook_latency_ms": hook_latency,
        }

    # Daemon not healthy - attempt to start it
    logger.info("Search daemon not healthy - attempting to start it")

    # Acquire startup mutex (Phase 2: multi-terminal coordination)
    mutex_handle = acquire_startup_mutex()

    # Double-check health after acquiring mutex (another terminal may have started it)
    if is_daemon_healthy(STATE_FILE):
        logger.info("Daemon became healthy while waiting for mutex")

        if mutex_handle is not None:
            release_startup_mutex(mutex_handle)

        hook_latency = (time.perf_counter() - hook_start) * 1000
        print({})

        return {
            "status": "healthy",
            "project_root": str(project_root),
            "hook_latency_ms": hook_latency,
        }

    # Start daemon (mutex_handle will be released inside start_daemon)
    pid = start_daemon(project_root, config, mutex_handle)
    if not pid:
        logger.error("Failed to start search daemon")

        # Check if daemon became healthy despite failure (race condition)
        if is_daemon_healthy(STATE_FILE):
            logger.info(
                "Daemon is healthy despite startup failure - likely started by another terminal"
            )

            hook_latency = (time.perf_counter() - hook_start) * 1000
            print({})

            return {
                "status": "healthy",
                "project_root": str(project_root),
                "hook_latency_ms": hook_latency,
            }

        return {
            "status": "failed",
            "project_root": str(project_root),
            "error": "Failed to start daemon",
        }

    logger.info(f"Search daemon started successfully (PID {pid})")

    hook_latency = (time.perf_counter() - hook_start) * 1000
    logger.debug(f"Hook completed in {hook_latency:.2f}ms")

    # Hook protocol: print empty dict
    print({})

    return {
        "status": "started",
        "pid": pid,
        "project_root": str(project_root),
        "hook_latency_ms": hook_latency,
    }


if __name__ == "__main__":
    result = main()
    # Debug logging (commented out for production - hook should be silent)
    # logger.debug(f"Hook result: {result}")
