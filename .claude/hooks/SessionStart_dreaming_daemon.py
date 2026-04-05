#!/usr/bin/env python3
"""
SessionStart hook: Auto-start dreaming daemon on session activation (T-010).

This hook ensures the dreaming daemon is running when a Claude Code session starts.
It performs health checks based on heartbeat age and auto-starts the daemon if needed.

Features:
- Heartbeat-based health checks (90s threshold)
- Windows-specific daemon startup (pythonw.exe, CREATE_NO_WINDOW)
- Latency measurement and instrumentation
- Upstream data source health monitoring
- Graceful degradation on errors

Usage:
    Called automatically by Claude Code on session start.
    Can be run manually for testing: python SessionStart_dreaming_daemon.py
"""

import logging
import random
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

# Import dreaming daemon modules
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
UPSTREAM_IDLE_WARNING_MINUTES = 10  # Warn if no new events for >10 minutes
LATENCY_WARNING_THRESHOLD_MS = 100  # Warn if state read takes >100ms

# Paths
HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / "state"
LOGS_DIR = HOOKS_DIR / "logs"
STATE_FILE = STATE_DIR / "dreaming-daemon-state.json"
EVENTS_FILE = LOGS_DIR / "principle-events.jsonl"


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
        state_path: Path to dreaming-daemon-state.json.

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


def check_upstream_health(events_path: Path) -> dict[str, Any]:
    """
    Check upstream data source health (principle-events.jsonl).

    Args:
        events_path: Path to principle-events.jsonl.

    Returns:
        Dict with status ("healthy", "stale", "missing") and age_minutes if stale.
    """
    try:
        if not events_path.exists():
            logger.warning(f"Upstream data source missing: {events_path}")
            return {"status": "missing", "age_minutes": None}

        # Check file modification time
        stat = events_path.stat()
        age_seconds = time.time() - stat.st_mtime
        age_minutes = age_seconds / 60

        if age_minutes > UPSTREAM_IDLE_WARNING_MINUTES:
            logger.warning(
                f"Upstream data source stale: {age_minutes:.1f} minutes old "
                f"(exceeds {UPSTREAM_IDLE_WARNING_MINUTES}min threshold)"
            )
            return {"status": "stale", "age_minutes": age_minutes}
        else:
            logger.debug(f"Upstream data source healthy: {age_minutes:.1f} minutes old")
            return {"status": "healthy", "age_minutes": age_minutes}

    except Exception as e:
        logger.error(f"Error checking upstream health: {e}")
        return {"status": "error", "age_minutes": None}


def acquire_startup_mutex() -> Any | None:
    """
    Acquire Windows mutex for daemon startup coordination.

    Uses randomized backoff (50-150ms jitter) to desynchronize concurrent attempts.
    Implements retry logic (max 3 attempts) with exponential backoff.

    Returns:
        Mutex handle if acquired, None if pywin32 unavailable or all retries failed.

    Mutex coordination prevents race conditions when multiple terminals start
    simultaneously and attempt to launch the daemon.
    """
    if not PYWIN32_AVAILABLE:
        logger.debug("pywin32 unavailable - skipping mutex coordination")
        return None

    # Mutex name: Global scope ensures system-wide coordination
    mutex_name = "Global\\ClaudeDaemonStartup"

    # Retry configuration
    max_retries = 3
    backoff_delays = [0.050, 0.100, 0.150]  # Exponential backoff: 50ms, 100ms, 150ms

    for attempt in range(max_retries):
        # Apply randomized jitter before acquisition attempt
        jitter = random.uniform(0.050, 0.150)  # 50-150ms jitter
        time.sleep(jitter)

        try:
            # Try to create mutex (fail immediately if exists)
            mutex_handle = win32event.CreateMutexW(
                None,  # Security attributes
                False,  # Initial owner (don't own immediately)
                mutex_name,
            )

            if not mutex_handle:
                logger.error(f"Failed to create mutex (attempt {attempt + 1}/{max_retries})")
                continue

            # Check if mutex already existed
            error_code = win32api.GetLastError() if "win32api" in dir() else 0

            if error_code == winerror.ERROR_ALREADY_EXISTS:
                # Mutex exists - another terminal is starting daemon
                logger.debug(f"Startup mutex busy (attempt {attempt + 1}/{max_retries})")

                if attempt < max_retries - 1:
                    # Retry with backoff
                    backoff = backoff_delays[attempt]
                    logger.debug(f"Retrying in {backoff * 1000:.0f}ms...")
                    time.sleep(backoff)
                else:
                    # Last retry failed - give up
                    logger.warning("Failed to acquire startup mutex after max retries")
                    win32api.CloseHandle(mutex_handle)
                    return None
            else:
                # Mutex created successfully - we own the startup
                logger.info("Acquired startup mutex for daemon startup")
                return mutex_handle

        except Exception as e:
            logger.error(f"Error acquiring mutex (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Retry with backoff on error
                backoff = backoff_delays[attempt]
                time.sleep(backoff)
            else:
                # All retries failed
                return None

    # All retries exhausted
    return None


def release_startup_mutex(mutex_handle: Any) -> None:
    """
    Release Windows mutex after daemon startup complete.

    Args:
        mutex_handle: Handle to mutex (from acquire_startup_mutex).
    """
    if mutex_handle is None:
        return

    try:
        if hasattr(win32event, "ReleaseMutex"):
            win32event.ReleaseMutex(mutex_handle)
        if hasattr(win32event, "CloseHandle"):
            win32event.CloseHandle(mutex_handle)
        logger.debug("Released startup mutex")
    except Exception as e:
        logger.error(f"Error releasing mutex: {e}")
        # Ignore errors during cleanup


def start_daemon(project_root: Path, config: dict, mutex_handle: Any | None = None) -> int | None:
    """
    Start the dreaming daemon and return its PID.

    Args:
        project_root: Project root directory.
        config: Daemon configuration dict.
        mutex_handle: Optional mutex handle for startup coordination (Phase 2).

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

        # Build command: python -m dreaming_daemon --daemon-type dreaming
        # Note: dreaming_daemon.py is in hooks directory
        cmd = [python_exe, "-m", "dreaming_daemon", "--daemon-type", "dreaming"]

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

        logger.info(f"Started dreaming daemon PID {proc.pid}")

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

    Enhanced with Phase 2 multi-terminal coordination using Windows mutex.

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
    logger.debug(f"Config loaded: {config}")

    # Check if daemon is healthy
    if is_daemon_healthy(STATE_FILE):
        logger.debug("Daemon is healthy - no action needed")

        # Check upstream data source health (warning only)
        upstream_health = check_upstream_health(EVENTS_FILE)
        if upstream_health["status"] == "stale":
            logger.warning(
                f"Upstream idle: {upstream_health['age_minutes']:.1f} minutes "
                f"(threshold: {UPSTREAM_IDLE_WARNING_MINUTES}min)"
            )

        hook_latency = (time.perf_counter() - hook_start) * 1000

        # Log to diagnostics
        if DIAGNOSTICS_AVAILABLE and log_hook_invocation:
            try:
                log_hook_invocation(
                    hook_name="SessionStart_dreaming_daemon",
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
            "upstream_status": upstream_health["status"],
        }

    # Daemon is unhealthy or missing - start it with coordination
    logger.info("Daemon is unhealthy or missing - starting with coordination...")

    # Phase 2: Acquire startup mutex to prevent race conditions
    mutex_handle = acquire_startup_mutex()

    # Check again if another terminal started the daemon while we waited for mutex
    if is_daemon_healthy(STATE_FILE):
        logger.info("Another terminal started daemon - releasing mutex and returning healthy")

        # Release mutex
        if mutex_handle is not None:
            release_startup_mutex(mutex_handle)

        # Check upstream data source health (warning only)
        upstream_health = check_upstream_health(EVENTS_FILE)

        hook_latency = (time.perf_counter() - hook_start) * 1000
        logger.debug(f"Hook completed in {hook_latency:.2f}ms")

        # Hook protocol: print empty dict
        print({})

        return {
            "status": "healthy",
            "project_root": str(project_root),
            "hook_latency_ms": hook_latency,
            "upstream_status": upstream_health["status"],
        }

    # Start daemon (mutex_handle will be released inside start_daemon)
    pid = start_daemon(project_root, config, mutex_handle)
    if not pid:
        logger.error("Failed to start daemon")

        # Check if daemon became healthy despite failure (race condition)
        if is_daemon_healthy(STATE_FILE):
            logger.info(
                "Daemon is healthy despite startup failure - likely started by another terminal"
            )
            upstream_health = check_upstream_health(EVENTS_FILE)

            hook_latency = (time.perf_counter() - hook_start) * 1000
            print({})

            return {
                "status": "healthy",
                "project_root": str(project_root),
                "hook_latency_ms": hook_latency,
                "upstream_status": upstream_health["status"],
            }

        return {
            "status": "failed",
            "project_root": str(project_root),
            "error": "Failed to start daemon",
        }

    logger.info(f"Daemon started successfully (PID {pid})")

    # Check upstream data source health
    upstream_health = check_upstream_health(EVENTS_FILE)

    hook_latency = (time.perf_counter() - hook_start) * 1000
    logger.debug(f"Hook completed in {hook_latency:.2f}ms")

    # Hook protocol: print empty dict
    print({})

    return {
        "status": "started",
        "pid": pid,
        "project_root": str(project_root),
        "hook_latency_ms": hook_latency,
        "upstream_status": upstream_health["status"],
    }


if __name__ == "__main__":
    result = main()
    # Debug logging (commented out for production - hook should be silent)
    # logger.debug(f"Hook result: {result}")
