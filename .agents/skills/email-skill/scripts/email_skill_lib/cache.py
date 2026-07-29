"""TTL cache for email scan results, with cross-platform file locking.

Files (created on first run):
    P:/.data/email-scan/cache.json  — the TTL-cached scan results.
    P:/.data/email-scan/cache.lock  — file lock used to serialize writers.

Default TTL: 15 minutes (900 seconds).

Concurrency model:
    - Multiple processes may call read_cache() concurrently without locks.
    - Writers (write_cache) acquire an exclusive cross-platform file lock
      (msvcrt.locking on Windows, fcntl.flock on POSIX) and use the host
      primitive atomic_write_with_lock for the actual write.
    - Stale lock recovery: if a lockfile exists with a PID+timestamp
      stamp older than STALE_LOCK_SECONDS (60s) AND that PID is no longer
      running, the next writer will steal the lock (delete the lockfile
      and retry). This guards against the crash-without-release case.

Two locking primitives are exposed:
    acquire_lock(timeout=30) -> bool
    release_lock()
These are for callers that need to hold the lock across multiple file
operations (e.g. read-check-write in a single critical section). Plain
write_cache() handles its own locking internally and is what most callers
should use.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Make the host primitive importable from P:/.agents/__lib/atomic_io.py.
# This package lives at P:/.agents/skills/email-skill/scripts/email_skill_lib/.
# Walking up: parents[0]=email_skill_lib, [1]=scripts, [2]=email-skill,
# [3]=skills, [4]=.agents. So parents[4] is P:/.agents.
_PKG_PARENT = Path(__file__).resolve().parents[4]
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))

from __lib.atomic_io import atomic_write_with_lock  # noqa: E402

CACHE_DIR = Path("P:/.data/email-scan")
CACHE_FILE = CACHE_DIR / "cache.json"
LOCK_FILE = CACHE_DIR / "cache.lock"
DEFAULT_TTL = 900  # 15 minutes
STALE_LOCK_SECONDS = 60

# Module-level state for explicit acquire_lock/release_lock pairs.
# Each PROCESS keeps its own fd in this dict. Cross-process, the OS-level
# lock (msvcrt/fcntl) is the actual coordination mechanism; this dict is
# only here so release_lock() knows which fd to close.
_LOCK_FD: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ensure_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _pid_alive(pid: int) -> bool:
    """Return True if `pid` is a running process on this host.

    On Windows: uses OpenProcess + GetExitCodeProcess (STILL_ACTIVE = 259).
    On POSIX:   uses os.kill(pid, 0) — signal 0 is a permissions/existence
                probe that doesn't actually send a signal.
    """
    if pid <= 0:
        return False
    try:
        if sys.platform == "win32":
            import ctypes  # type: ignore[import-not-found]

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if not handle:
                return False
            try:
                exit_code = ctypes.c_ulong()
                ok = kernel32.GetExitCodeProcess(
                    handle, ctypes.byref(exit_code)
                )
                return bool(ok) and exit_code.value == STILL_ACTIVE
            finally:
                kernel32.CloseHandle(handle)
        else:
            os.kill(pid, 0)
            return True
    except (OSError, ProcessLookupError, PermissionError):
        return False
    except Exception:
        return False


def _read_lock_info() -> Optional[tuple[int, float]]:
    """Read "<pid>:<timestamp>" from the lockfile. Returns None if missing/invalid."""
    try:
        if not LOCK_FILE.exists():
            return None
        text = LOCK_FILE.read_text(encoding="utf-8").strip()
        if not text:
            return None
        pid_str, ts_str = text.split(":", 1)
        return int(pid_str), float(ts_str)
    except (ValueError, OSError):
        return None


def _stamp_lock(fd: int) -> None:
    """Write "<pid>:<timestamp>" into the locked fd, truncating prior content."""
    stamp = f"{os.getpid()}:{time.time()}\n".encode("utf-8")
    try:
        os.lseek(fd, 0, os.SEEK_SET)
        os.ftruncate(fd, 0)
        os.write(fd, stamp)
    except OSError:
        # Non-fatal: stale recovery will still work via file existence.
        pass


def _steal_if_stale() -> None:
    """If lockfile's stamped PID is dead AND stamp is older than
    STALE_LOCK_SECONDS, remove the lockfile so the next acquire attempt
    starts fresh. Called between acquire attempts."""
    info = _read_lock_info()
    if info is None:
        return
    pid, ts = info
    if (time.time() - ts) < STALE_LOCK_SECONDS:
        return
    if _pid_alive(pid):
        return
    try:
        LOCK_FILE.unlink()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Public locking API (for callers holding the lock across multiple ops)
# ---------------------------------------------------------------------------


def acquire_lock(timeout: float = 30.0) -> bool:
    """Acquire exclusive cross-platform file lock with stale-recovery.

    Returns True if the lock was acquired within `timeout` seconds, False
    otherwise. The lock is released by release_lock() or by process exit
    (closing the fd releases the OS-level lock in both msvcrt and fcntl).

    The implementation:
      1. Open (or create) the lockfile with O_CREAT|O_RDWR.
      2. Try non-blocking lock on the fd.
      3. If lock fails, check if the existing stamp is stale+dead; if so,
         remove the lockfile and retry the open+lock.
      4. Once locked, stamp the fd with our PID and timestamp so future
         processes can detect a crashed-and-released holder.
      5. Store the fd in module state so release_lock() can find it.

    Cross-platform:
      - Windows: msvcrt.locking(fd, LK_NBLCK, 1) — non-blocking 1-byte
        exclusive lock. Released when the fd is closed.
      - POSIX:   fcntl.flock(fd, LOCK_EX | LOCK_NB) — non-blocking
        exclusive advisory lock. Released on close or LOCK_UN.
    """
    global _LOCK_FD
    _ensure_dir()
    deadline = time.time() + timeout

    while time.time() < deadline:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_RDWR, 0o644)
        acquired = False
        try:
            if sys.platform == "win32":
                import msvcrt  # type: ignore[import-not-found]
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    acquired = True
                except OSError:
                    acquired = False
            else:
                import fcntl  # type: ignore[import-not-found]
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                except OSError:
                    acquired = False

            if not acquired:
                os.close(fd)
                # Check if the holder died — if so, steal the lock.
                _steal_if_stale()
                time.sleep(0.1)
                continue

            # Lock held. Stamp our identity so future processes can detect
            # a crashed-and-unreleased holder (after STALE_LOCK_SECONDS).
            _stamp_lock(fd)
            _LOCK_FD = fd
            return True
        except Exception:
            try:
                os.close(fd)
            except OSError:
                pass
            time.sleep(0.1)

    return False


def release_lock() -> None:
    """Release the lock previously acquired by acquire_lock().

    Safe to call if no lock is held (no-op). Always closes the fd, which
    also releases the OS-level lock on both Windows and POSIX.
    """
    global _LOCK_FD
    fd = _LOCK_FD
    if fd is None:
        return
    _LOCK_FD = None
    try:
        if sys.platform != "win32":
            import fcntl  # type: ignore[import-not-found]
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except (IOError, OSError):
                pass
    finally:
        try:
            os.close(fd)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# TTL cache API
# ---------------------------------------------------------------------------


def _parse_scanned_at(s: Optional[str]) -> Optional[datetime]:
    """Parse the 'scanned_at' field of the cache. Returns UTC datetime or None."""
    if not s:
        return None
    try:
        if s.endswith("Z"):
            return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def read_cache(ttl_seconds: int = DEFAULT_TTL) -> Optional[dict]:
    """Return cached data if fresh (< ttl_seconds), None if stale or missing.

    A cache file is "fresh" when (now - scanned_at) <= ttl_seconds.
    If the file is missing, unparseable, missing scanned_at, or has an
    invalid timestamp, this returns None (caller should do a fresh scan).

    No locking is needed for reads — atomic_write_with_lock on the writer
    side guarantees readers never see a torn file.
    """
    _ensure_dir()
    if not CACHE_FILE.exists():
        return None
    try:
        raw = CACHE_FILE.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None

    ts = _parse_scanned_at(data.get("scanned_at"))
    if ts is None:
        return None

    age = (datetime.now(timezone.utc) - ts).total_seconds()
    if age > ttl_seconds:
        return None
    return data


def write_cache(data: dict) -> None:
    """Atomically write the cache with internal cross-platform locking.

    Stamps `scanned_at` with the current UTC time so the next read_cache
    can compute TTL freshness. The lock and atomic-rename are handled by
    the host primitive atomic_write_with_lock.

    The `data` dict is mutated in-place to add the scanned_at stamp.
    """
    _ensure_dir()
    data["scanned_at"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    atomic_write_with_lock(LOCK_FILE, CACHE_FILE, payload, timeout=30.0)