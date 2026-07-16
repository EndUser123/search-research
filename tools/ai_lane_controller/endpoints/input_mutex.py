"""UIMutex wrapper for the terminal adapter.

Coordinates input injection with the user's interactive Claude Code session.

When the bridge holds the mutex:
- A UserPromptSubmit hook blocks new input from the user
- The bridge injects the ChatGPT message into Claude's terminal
- On completion, the bridge releases the mutex

Interrupt detection:
- The user can delete the ui-input.lock file to signal "stop"
- The bridge polls the lock file; if it disappears, injection stops
- A PowerShell helper (bridge_interrupt.ps1) does the deletion
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Canonical lock path — matches scheduler.py
AI_LANE_ROOT = Path("P:/.ai-lanes")
CANONICAL_LOCK = AI_LANE_ROOT / "controller" / "locks" / "ui-input.lock"


class UIMutexError(RuntimeError):
    """Mutex operation failed."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_own_pid() -> int:
    return os.getpid()


def acquire_ui_mutex(
    pid: int | None = None,
    *,
    workspace_id: str = "",
    timeout_s: float = 30.0,
    poll_interval: float = 0.1,
) -> Path:
    """Acquire the UI input mutex via exclusive-create.

    Blocks for up to *timeout_s* seconds.  Returns the lock file path on
    success.  Raises ``UIMutexError`` on timeout or workspace mismatch.

    The lock file contains:
        {"pid": <int>, "process_start_time": <iso>, "workspace_id": <str>, "at": <iso>}
    """
    from .win_console_api import get_console_pids

    pid = pid or _get_own_pid()
    lock_path = CANONICAL_LOCK
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        try:
            with lock_path.open("x", encoding="utf-8") as f:
                json.dump({
                    "pid": pid,
                    "process_start_time": _iso_now(),
                    "workspace_id": workspace_id,
                    "at": _iso_now(),
                    "bridge": True,
                }, f, ensure_ascii=False)
                f.write("\n")
            return lock_path
        except FileExistsError:
            if not lock_path.exists():
                continue
            try:
                data = json.loads(lock_path.read_text(encoding="utf-8"))
                holder_pid = int(data.get("pid", 0))
                if holder_pid and not _process_exists(holder_pid):
                    lock_path.unlink(missing_ok=True)
                    continue
            except (OSError, ValueError, json.JSONDecodeError):
                lock_path.unlink(missing_ok=True)
                continue
        time.sleep(poll_interval)

    raise UIMutexError(
        f"could not acquire UI mutex within {timeout_s}s "
        f"(held by PID {holder_pid if 'holder_pid' in dir() else 'unknown'})"
    )


def release_ui_mutex(pid: int | None = None) -> None:
    """Release the UI input mutex (delete the lock file).

    Only succeeds if the lock is held by *pid* (defaults to current process).
    Raises ``UIMutexError`` if held by a different process.
    """
    pid = pid or _get_own_pid()
    lock_path = CANONICAL_LOCK
    if not lock_path.exists():
        return  # Not held — idempotent release

    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        holder_pid = int(data.get("pid", 0))
        if holder_pid != pid:
            raise UIMutexError(
                f"cannot release UI mutex: held by PID {holder_pid}, "
                f"caller is PID {pid}"
            )
        lock_path.unlink(missing_ok=True)
    except (OSError, ValueError, json.JSONDecodeError):
        lock_path.unlink(missing_ok=True)


def is_ui_mutex_held() -> bool:
    """Check if the UI input mutex is currently held.

    Returns False if the lock file doesn't exist or the holder is dead.
    """
    lock_path = CANONICAL_LOCK
    if not lock_path.exists():
        return False
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        holder_pid = int(data.get("pid", 0))
        if holder_pid and _process_exists(holder_pid):
            return True
        lock_path.unlink(missing_ok=True)
        return False
    except (OSError, ValueError, json.JSONDecodeError):
        lock_path.unlink(missing_ok=True)
        return False


def wait_for_mutex_release(
    timeout_s: float = 60.0,
    poll_interval: float = 0.5,
) -> bool:
    """Block until the mutex is released (or timeout).  Returns True if released."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not is_ui_mutex_held():
            return True
        time.sleep(poll_interval)
    return False


def monitor_interrupt(pid: int, poll_interval: float = 0.5) -> None:
    """Poll the lock file; if it disappears or PID changes, stop.

    Intended to run in a background thread alongside the injection loop.
    When the lock is lost, the caller should abort the current injection,
    release all resources, and reset the lane phase.
    """
    while True:
        if not CANONICAL_LOCK.exists():
            raise InterruptedError("UI mutex lock file deleted")
        try:
            data = json.loads(CANONICAL_LOCK.read_text(encoding="utf-8"))
            if int(data.get("pid", 0)) != pid:
                raise InterruptedError("UI mutex acquired by another process")
        except (OSError, ValueError, json.JSONDecodeError):
            raise InterruptedError("UI mutex lock file corrupt or missing")
        time.sleep(poll_interval)


def _process_exists(pid: int) -> bool:
    """Check if a process with this PID is running."""
    import platform
    if platform.system() == "Windows":
        import ctypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False