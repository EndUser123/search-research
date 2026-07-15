"""Lane claiming — binds a live execution context to a lane identity.

A process must claim a lane before routing messages.  Claims are filesystem-
backed with atomic exclusive-create for mutual exclusion.

Identity fields:
- lane_id          — which lane
- session_nonce    — random UUID per claim session
- pid              — OS process ID
- process_start_time — ISO timestamp from the claiming process (detects PID reuse)
- created_at       — ISO timestamp when the claim was first created
- heartbeat_at     — ISO timestamp of last heartbeat (staleness detection)
"""

from __future__ import annotations

import json
import os
import platform
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from .registry import RegistryError, lane_exists

_WINDOWS = platform.system() == "Windows"

CLAIM_TTL_SECONDS = 30       # default staleness threshold
STALE_LOCK_SECONDS = 5       # reclaim lock file after this duration


class ClaimError(PermissionError):
    """Claim operation failed."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _session_nonce() -> str:
    return uuid.uuid4().hex


def _claim_path(storage: Any, lane_id: str) -> Path:
    return storage.root / lane_id / "claim.json"


def _lock_path(storage: Any, lane_id: str) -> Path:
    return storage.root / lane_id / "claim.lock"


def _acquire_lock(storage: Any, lane_id: str) -> bool:
    """Try to acquire an exclusive filesystem lock via open("x").

    Returns True if the lock was acquired.  Recovers stale locks older
    than STALE_LOCK_SECONDS.
    """
    lock = _lock_path(storage, lane_id)
    try:
        lock.parent.mkdir(parents=True, exist_ok=True)
        with lock.open("x", encoding="utf-8"):
            lock.write_text(_iso_now(), encoding="utf-8")
        return True
    except FileExistsError:
        if lock.exists():
            age = (datetime.now(timezone.utc).timestamp() - lock.stat().st_mtime)
            if age > STALE_LOCK_SECONDS:
                lock.unlink(missing_ok=True)
                try:
                    with lock.open("x", encoding="utf-8"):
                        lock.write_text(_iso_now(), encoding="utf-8")
                    return True
                except FileExistsError:
                    return False
        return False


def _release_lock(storage: Any, lane_id: str) -> None:
    _lock_path(storage, lane_id).unlink(missing_ok=True)


def _stale_seconds(heartbeat_at: str, now: datetime | None = None) -> float:
    n = now or datetime.now(timezone.utc)
    hb = datetime.fromisoformat(heartbeat_at.replace("Z", "+00:00"))
    return (n - hb).total_seconds()


@dataclass(frozen=True)
class LaneClaim:
    """An active claim binding a process to a lane."""

    lane_id: str
    session_nonce: str
    pid: int
    process_start_time: str
    created_at: str
    heartbeat_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LaneClaim:
        required = {"lane_id", "session_nonce", "pid", "process_start_time", "created_at", "heartbeat_at"}
        missing = required - set(data.keys())
        if missing:
            raise ClaimError(f"claim missing fields: {', '.join(sorted(missing))}")
        return cls(
            lane_id=data["lane_id"],
            session_nonce=data["session_nonce"],
            pid=int(data["pid"]),
            process_start_time=data["process_start_time"],
            created_at=data["created_at"],
            heartbeat_at=data["heartbeat_at"],
        )


def claim_lane(
    lane_id: str,
    storage: Any,
    lanes: list[Any],
    *,
    pid: int | None = None,
    process_start_time: str | None = None,
    ttl: int = CLAIM_TTL_SECONDS,
) -> LaneClaim:
    """Atomically claim *lane_id*.

    Raises
    ------
    RegistryError
        If *lane_id* is unknown or disabled.
    ClaimError
        If the lane is already claimed by a different active process,
        or if PID reuse is detected (same PID, different process_start_time).
    """
    if not lane_exists(lanes, lane_id):
        raise RegistryError(f"cannot claim: unknown or disabled lane '{lane_id}'")

    pid = pid or os.getpid()
    if process_start_time is None:
        actual = _get_process_start_time(pid)
        process_start_time = actual if actual is not None else _iso_now()

    if not _acquire_lock(storage, lane_id):
        raise ClaimError(f"could not acquire lock for lane '{lane_id}'")

    try:
        claim_path = _claim_path(storage, lane_id)
        existing: LaneClaim | None = None
        if claim_path.exists():
            existing = LaneClaim.from_dict(
                json.loads(claim_path.read_text(encoding="utf-8"))
            )

        if existing is not None:
            age = _stale_seconds(existing.heartbeat_at)
            if age <= ttl:
                # Claim appears active.  Check PID reuse.
                if existing.pid == pid:
                    if existing.process_start_time != process_start_time:
                        raise ClaimError(
                            f"PID {pid} was recycled: process_start_time mismatch"
                        )
                    raise ClaimError(
                        f"lane '{lane_id}' already claimed by this process "
                        f"(nonce={existing.session_nonce[:12]}...)"
                    )
                raise ClaimError(
                    f"lane '{lane_id}' already claimed by PID {existing.pid} "
                    f"(heartbeat age={age:.0f}s, TTL={ttl}s)"
                )

        now = _iso_now()
        claim = LaneClaim(
            lane_id=lane_id,
            session_nonce=_session_nonce(),
            pid=pid,
            process_start_time=process_start_time,
            created_at=now,
            heartbeat_at=now,
        )
        claim_path.write_text(
            json.dumps(claim.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return claim
    finally:
        _release_lock(storage, lane_id)


def release_claim(
    lane_id: str,
    session_nonce: str,
    storage: Any,
    *,
    ttl: int = CLAIM_TTL_SECONDS,
) -> None:
    """Release the active claim for *lane_id*.

    Raises ClaimError if no active claim exists or the nonce does not match.
    """
    if not _acquire_lock(storage, lane_id):
        raise ClaimError(f"could not acquire lock for lane '{lane_id}'")

    try:
        claim = get_active_claim(lane_id, storage, ttl=ttl)
        if claim is None:
            raise ClaimError(f"no active claim for lane '{lane_id}'")
        if claim.session_nonce != session_nonce:
            raise ClaimError(
                f"session_nonce mismatch for lane '{lane_id}'"
            )
        _claim_path(storage, lane_id).unlink(missing_ok=True)
    finally:
        _release_lock(storage, lane_id)


def get_active_claim(
    lane_id: str,
    storage: Any,
    *,
    ttl: int = CLAIM_TTL_SECONDS,
) -> LaneClaim | None:
    """Return the active claim for *lane_id*, or *None* if unclaimed/stale."""
    claim_path = _claim_path(storage, lane_id)
    if not claim_path.exists():
        return None
    data = json.loads(claim_path.read_text(encoding="utf-8"))
    claim = LaneClaim.from_dict(data)
    if _stale_seconds(claim.heartbeat_at) > ttl:
        return None
    return claim


def heartbeat_claim(
    lane_id: str,
    session_nonce: str,
    storage: Any,
    *,
    ttl: int = CLAIM_TTL_SECONDS,
) -> LaneClaim:
    """Refresh the heartbeat on an active claim.

    Raises ClaimError if no active claim exists or the nonce does not match.
    """
    claim = get_active_claim(lane_id, storage, ttl=ttl)
    if claim is None:
        raise ClaimError(f"no active claim for lane '{lane_id}'")
    if claim.session_nonce != session_nonce:
        raise ClaimError(f"session_nonce mismatch for lane '{lane_id}'")

    updated = LaneClaim(
        lane_id=claim.lane_id,
        session_nonce=claim.session_nonce,
        pid=claim.pid,
        process_start_time=claim.process_start_time,
        created_at=claim.created_at,
        heartbeat_at=_iso_now(),
    )
    _claim_path(storage, lane_id).write_text(
        json.dumps(updated.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    storage.append_event(lane_id, {
        "type": "heartbeat",
        "lane_id": lane_id,
        "session_nonce": session_nonce[:12] + "...",
        "pid": claim.pid,
        "status": "acknowledged",
        "timestamp": _iso_now(),
    })
    return updated


def require_claim(
    lane_id: str,
    storage: Any,
    *,
    ttl: int = CLAIM_TTL_SECONDS,
) -> LaneClaim:
    """Return the active claim, or raise *ClaimError*."""
    claim = get_active_claim(lane_id, storage, ttl=ttl)
    if claim is None:
        raise ClaimError(f"lane '{lane_id}' is not claimed or claim is stale")
    return claim

# -- process liveness -------------------------------------------------------


def _process_exists(pid: int) -> bool:
    """Check if a process with this PID is running (signal 0 probe)."""
    if _WINDOWS:
        # ``os.kill(pid, 0)`` is not a reliable existence probe on Windows;
        # it returns false even for the current process under this runtime.
        # The process-time query is already the authoritative Windows probe.
        return _get_process_start_time(pid) is not None
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _get_process_start_time(pid: int) -> str | None:
    """Get ISO-8601 creation time of a running process, or None if not found.

    On Windows uses ctypes + kernel32 to avoid subprocess overhead.
    On POSIX returns None (not yet supported -- fails closed).
    """
    if not _WINDOWS:
        return None

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = [
        wintypes.DWORD, wintypes.BOOL, wintypes.DWORD,
    ]
    kernel32.GetProcessTimes.restype = wintypes.BOOL
    kernel32.GetProcessTimes.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME),
    ]
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None

    try:
        creation = wintypes.FILETIME()
        exit_t = wintypes.FILETIME()
        kernel_t = wintypes.FILETIME()
        user_t = wintypes.FILETIME()

        if not kernel32.GetProcessTimes(
            handle,
            ctypes.byref(creation),
            ctypes.byref(exit_t),
            ctypes.byref(kernel_t),
            ctypes.byref(user_t),
        ):
            return None

        ns_100 = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        nt_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
        return (nt_epoch + timedelta(microseconds=ns_100 // 10)).isoformat().replace(
            "+00:00", "Z"
        )
    finally:
        kernel32.CloseHandle(handle)


def verify_process_liveness(claim: LaneClaim) -> tuple[bool, str]:
    """Check if the process that owns *claim* is still alive.

    Returns
    -------
    (True, "") if the process exists and has not been recycled.
    (False, reason_code) otherwise.

    Reason codes:

    * "process_not_found" -- PID does not exist in the OS.
    * "pid_recycled" -- PID exists but start time does not match
      (the recorded process identity has been recycled by a new process).
    """
    if not _process_exists(claim.pid):
        return False, "process_not_found"

    actual_start = _get_process_start_time(claim.pid)
    if actual_start is None:
        return False, "process_not_found"

    t1 = datetime.fromisoformat(actual_start.replace("Z", "+00:00"))
    t2 = datetime.fromisoformat(claim.process_start_time.replace("Z", "+00:00"))

    diff = abs((t1 - t2).total_seconds())
    if diff > 2.0:
        return False, "pid_recycled"

    return True, ""
