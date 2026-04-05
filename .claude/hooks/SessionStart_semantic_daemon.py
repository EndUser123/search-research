#!/usr/bin/env python3
"""
SessionStart hook: Auto-start unified semantic daemon on session activation.

This hook ensures the semantic daemon is running when a Claude Code session starts.
It handles multi-terminal coordination using Windows mutex synchronization.
"""

import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants
DAEMON_MUTEX_NAME = "Global\\CSF_Semantic_Daemon_Startup"
DAEMON_DISCOVERY_FILE = "data/semantic_daemon_discovery.json"
# PROJECT_ROOT marker files (search upward from hook to find)


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


def is_daemon_running() -> bool:
    """Check if daemon is already running via discovery file."""
    try:
        project_root = get_project_root()
        discovery_file = project_root / DAEMON_DISCOVERY_FILE

        if not discovery_file.exists():
            return False

        data = json.loads(discovery_file.read_text(encoding="utf-8"))
        pipe_name = data.get("pipe_name")

        if not pipe_name:
            return False

        # Try to connect to named pipe to verify daemon is alive
        try:
            import win32file

            handle = win32file.CreateFile(
                pipe_name,
                win32file.GENERIC_READ,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None,
            )
            win32file.CloseHandle(handle)
            return True
        except Exception:
            # Pipe not accessible - daemon likely dead
            return False

    except Exception as e:
        logger.debug(f"Error checking daemon status: {e}")
        return False


def kill_stale_daemons(current_pid: int | None = None) -> None:
    """Kill all daemon processes except the one specified in discovery file.

    Args:
        current_pid: Explicit PID to preserve. If None, reads from discovery file.
    """
    try:
        import psutil

        # CRITICAL: Read discovery file FIRST to get canonical PID
        if current_pid is None:
            try:
                project_root = get_project_root()
                discovery_file = project_root / DAEMON_DISCOVERY_FILE
                if discovery_file.exists():
                    data = json.loads(discovery_file.read_text(encoding="utf-8"))
                    current_pid = data.get("pid")
                    if current_pid:
                        logger.debug(f"Preserving canonical daemon PID {current_pid} from discovery file")
            except Exception as e:
                logger.debug(f"Could not read PID from discovery file: {e}")

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.cmdline()
                if not cmdline:
                    continue

                # Match both: pythonw.exe -m src.daemons.unified_semantic_daemon
                # And: python.exe -m daemons.unified_semantic_daemon (old hook behavior)
                cmdline_str = " ".join(cmdline)
                if "unified_semantic_daemon" not in cmdline_str.lower():
                    continue

                # Don't kill the canonical daemon (from discovery file or explicit)
                if current_pid is not None and proc.pid == current_pid:
                    logger.debug(f"Preserving canonical daemon PID {current_pid}")
                    continue

                # Kill stale daemon
                logger.info(f"Killing stale daemon PID {proc.pid}: {cmdline_str[:80]}")
                proc.terminate()
                proc.wait(timeout=5)

            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.debug(f"Could not terminate process: {e}")

    except Exception as e:
        logger.warning(f"Error killing stale daemons: {e}")


def start_daemon(project_root: Path) -> int | None:
    """Start the semantic daemon and return its PID."""
    try:
        # Use pythonw.exe (no console window)
        python_exe = (
            sys.executable.replace("python.exe", "pythonw.exe")
            if "python.exe" in sys.executable
            else sys.executable
        )

        proc = subprocess.Popen(
            [python_exe, "-m", "src.daemons.unified_semantic_daemon"],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
        )

        logger.info(f"Started semantic daemon PID {proc.pid}")
        return proc.pid

    except Exception as e:
        logger.error(f"Failed to start daemon: {e}")
        return None


def check_daemon_health(project_root: Path) -> bool:
    """Quick health check - can we reach the daemon?

    Returns True if daemon responds to queries, False otherwise.
    Used to detect silent daemon failures after startup.
    """
    try:
        import sys

        sys.path.insert(0, str(project_root))
        from daemons.daemon_client import DaemonClient

        client = DaemonClient(auto_start=False, timeout=1.0)
        result = client.search("cks", "test", limit=1)
        return result is not None
    except Exception as e:
        logger.warning(f"Daemon health check failed: {e}")
        return False


def wait_for_daemon_discovery(project_root: Path, timeout: float = 5.0) -> bool:
    """Wait for daemon to write discovery file."""
    import time

    discovery_file = project_root / DAEMON_DISCOVERY_FILE
    start = time.time()

    while time.time() - start < timeout:
        if discovery_file.exists():
            try:
                data = json.loads(discovery_file.read_text(encoding="utf-8"))
                if data.get("pipe_name"):
                    return True
            except Exception:
                pass
        time.sleep(0.1)

    return False


def main() -> dict[str, Any]:
    """Hook entry point."""
    project_root = get_project_root()
    logger.debug(f"Project root: {project_root}")

    # Step 1: Check if daemon is already running
    if is_daemon_running():
        logger.debug("Daemon already running - skipping startup")
        return {"status": "already_running", "project_root": str(project_root)}

    # Step 2: Kill any stale daemon processes
    kill_stale_daemons()

    # Step 3: Multi-terminal synchronization using mutex with retry
    #
    # PROBLEM: Multiple terminals opening simultaneously race to start daemon
    #   - Terminal A checks daemon → not running
    #   - Terminal B checks daemon → not running (A hasn't finished yet)
    #   - Both start daemons → multiple PIDs, resource waste
    #
    # SOLUTION: Windows mutex with randomized backoff
    #   - Mutex is system-wide synchronization primitive
    #   - First terminal creates mutex, starts daemon
    #   - Other terminals see mutex exists, wait briefly with jitter
    #   - Jitter (50-150ms random) prevents synchronized retries
    #   - After wait, check if daemon is now running
    #   - If not, retry (max 3 attempts with 50ms backoff)
    #
    # TRADE-OFFS:
    #   - 100ms base wait: Daemon starts in ~100ms on modern machines
    #   - 50-150ms jitter: Prevents retry collisions, may be short on slow machines
    #   - 3 retries: Balances startup time vs. reliability
    #   - Max total wait: ~500ms (100ms + jitter) × 3 attempts
    #
    import random
    import time

    import win32api
    import win32event
    import winerror

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Try to create mutex (fails if another terminal is starting)
            mutex = win32event.CreateMutex(None, False, DAEMON_MUTEX_NAME)
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                # Another terminal is starting - wait briefly with jitter
                jitter = random.randint(50, 150)
                wait_time = 100 + jitter
                logger.debug(f"Another terminal is starting daemon - waiting {wait_time}ms...")

                # Instrumentation: Measure actual mutex wait time
                import time
                wait_start = time.time()
                win32event.WaitForSingleObject(mutex, wait_time)
                wait_duration = time.time() - wait_start
                logger.debug(f"Mutex wait: {wait_duration*1000:.0f}ms (attempt {attempt + 1}/{max_retries})")
                win32api.CloseHandle(mutex)

                # Check if daemon is now running after the wait
                if is_daemon_running():
                    logger.debug("Daemon started by another terminal - skipping startup")
                    return {"status": "started_by_other", "project_root": str(project_root)}

                # Retry if not last attempt
                if attempt < max_retries - 1:
                    logger.debug(f"Daemon not ready, retry {attempt + 1}/{max_retries}")
                    time.sleep(0.05)  # Brief sleep before retry
                    continue

            # Break if we got the mutex or daemon is running
            break

        except Exception as e:
            logger.warning(f"Mutex attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(0.05)
                continue
            # Continue without mutex protection on final failure

    # Step 4: Start the daemon
    pid = start_daemon(project_root)
    if not pid:
        return {"status": "failed", "project_root": str(project_root), "error": "Failed to start daemon"}

    # Step 5: Wait for discovery file
    if wait_for_daemon_discovery(project_root):
        # Step 6: Health check - verify daemon is actually responding
        if check_daemon_health(project_root):
            logger.info(f"Daemon started successfully and is ready (PID {pid})")
            return {"status": "started", "pid": pid, "project_root": str(project_root)}
        else:
            logger.warning(f"Daemon started but health check failed (PID {pid})")
            return {"status": "started_unhealthy", "pid": pid, "project_root": str(project_root)}
    else:
        logger.warning(f"Daemon started but discovery file not found after timeout (PID {pid})")
        return {"status": "started_no_discovery", "pid": pid, "project_root": str(project_root)}


if __name__ == "__main__":
    result = main()
    # Don't print anything - this is a hook
