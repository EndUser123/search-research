"""Lane-scoped UI input mutex for the terminal adapter.

Each lane gets its OWN mutex file so up to N lanes can inject concurrently
into N separate Claude terminals without contending.  Lock path::

    P:/.ai-lanes/controller/locks/ui-input-<lane_id>.lock

A bridge holds its lane's mutex while injecting a message.  Other bridges
on other lanes are unaffected.  Within one lane, the mutex serializes
access so two poll cycles can't inject at once.

Stale-lock safe: the holder's PID is recorded and checked for liveness.
A dead bridge PID is reclaimed (lock deleted) on the next acquire attempt.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

AI_LANE_ROOT = Path("P:/.ai-lanes")
LOCKS_DIR = AI_LANE_ROOT / "controller" / "locks"


class UIMutexError(RuntimeError):
    """Mutex operation failed."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_own_pid() -> int:
    return os.getpid()


def _lane_lock_path(lane_id: str) -> Path:
    """Return the per-lane UI mutex path.

    Lane-scoped: each lane has its own file, so concurrent lanes don't
    contend.  The lane_id is sanitized to a filename-safe slug.
    """
    slug = "".join(c if c.isalnum() or c in "-_" else "_" for c in lane_id)
    return LOCKS_DIR / f"ui-input-{slug}.lock"


def acquire_ui_mutex(
    lane_id: str,
    pid: int | None = None,
    *,
    timeout_s: float = 30.0,
    poll_interval: float = 0.1,
) -> Path:
    """Acquire the UI input mutex for *lane_id* via exclusive-create.

    Blocks up to *timeout_s*.  Returns the lock path on success.  Raises
    ``UIMutexError`` on timeout.  A stale lock (dead holder PID) is
    reclaimed automatically.
    """
    pid = pid or _get_own_pid()
    lock_path = _lane_lock_path(lane_id)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout_s
    holder_pid = 0

    while time.monotonic() < deadline:
        try:
            with lock_path.open("x", encoding="utf-8") as f:
                json.dump({
                    "lane_id": lane_id,
                    "pid": pid,
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
        f"could not acquire UI mutex for lane '{lane_id}' within "
        f"{timeout_s}s (held by PID {holder_pid or 'unknown'})"
    )


def release_ui_mutex(lane_id: str, pid: int | None = None) -> None:
    """Release the UI mutex for *lane_id*.

    Only the holding PID may release.  Idempotent if not held.
    """
    pid = pid or _get_own_pid()
    lock_path = _lane_lock_path(lane_id)
    if not lock_path.exists():
        return
    try:
        data = json.loads(lock_path.read_text(encoding="utf-8"))
        holder_pid = int(data.get("pid", 0))
        if holder_pid != pid:
            raise UIMutexError(
                f"cannot release UI mutex for lane '{lane_id}': held by PID "
                f"{holder_pid}, caller is PID {pid}"
            )
        lock_path.unlink(missing_ok=True)
    except (OSError, ValueError, json.JSONDecodeError):
        lock_path.unlink(missing_ok=True)


def is_ui_mutex_held(lane_id: str) -> bool:
    """Check if the UI mutex for *lane_id* is currently held by a live process."""
    lock_path = _lane_lock_path(lane_id)
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
    lane_id: str,
    timeout_s: float = 60.0,
    poll_interval: float = 0.5,
) -> bool:
    """Block until the lane's mutex is released (or timeout)."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if not is_ui_mutex_held(lane_id):
            return True
        time.sleep(poll_interval)
    return False


def _process_exists(pid: int) -> bool:
    """Check if a process with this PID is running."""
    import platform
    if platform.system() == "Windows":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if h:
            ctypes.windll.kernel32.CloseHandle(h)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False