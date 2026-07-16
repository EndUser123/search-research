"""Lane claiming — binds a live execution context to a lane identity.

A process must claim a lane before routing messages.  Claims are filesystem-
backed with atomic exclusive-create for mutual exclusion.

Identity fields:
- lane_id            — which lane
- session_nonce      — random UUID per claim session (primary authority token)
- pid                — OS process ID
- process_start_time — ISO timestamp from the claiming process (detects PID reuse)
- created_at         — ISO timestamp when the claim was first created
- heartbeat_at       — ISO timestamp of last heartbeat (staleness detection)

Milestone 4 — terminal isolation + stale-writer fencing:
- terminal_id        — random per-terminal identity (isolates concurrent terminals)
- session_id         — random per-session identity
- workspace_id       — repository/workspace identity (rejects cross-workspace writes)
- fencing_epoch      — monotonically increasing per-lane counter; increments on
                       every replacement.  A writer whose epoch is older than the
                       on-disk epoch has been superseded and is rejected with a
                       fencing error, even if they still hold the old nonce.

Fail-closed invariants (Milestone 4):
- Claim creation, heartbeat, release, and replacement all validate the current
  session identity and fencing epoch when the caller supplies them.
- Stale or superseded writers receive a fencing error.
- PID reuse remains rejected.
- Wrong workspace, terminal, or session is rejected.
- Stale-lock reclamation never relies on mtime alone: an orphaned lock is
  reclaimed only when its holder process is verifiably dead (liveness failed).
- An expired claim is reclaimed only when the owner process is verifiably dead.
- All claim-file updates are atomic (write-temp + ``os.replace``); readers
  never observe partial JSON.
"""

from __future__ import annotations

import json
import os
import platform
import uuid
from dataclasses import dataclass, asdict, replace
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from .registry import RegistryError, lane_exists

_WINDOWS = platform.system() == "Windows"

CLAIM_TTL_SECONDS = 30       # default staleness threshold
STALE_LOCK_SECONDS = 5       # minimum age before an orphaned lock may be reclaimed


class ClaimError(PermissionError):
    """Claim operation failed."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _session_nonce() -> str:
    return uuid.uuid4().hex


def _random_id() -> str:
    return uuid.uuid4().hex


def _workspace_id(storage: Any) -> str:
    """Stable identity for the workspace backing *storage*.

    Derived from the resolved storage root so two terminals in the same
    workspace share an identity, and terminals in different workspaces differ.
    """
    import hashlib

    root_obj = getattr(storage, "root", None)
    try:
        root = str(Path(root_obj).resolve()) if root_obj else ""
    except Exception:
        root = str(root_obj) if root_obj else ""
    return hashlib.sha256(root.encode("utf-8")).hexdigest()[:16]


def _claim_path(storage: Any, lane_id: str) -> Path:
    return storage.root / lane_id / "claim.json"


def _lock_path(storage: Any, lane_id: str) -> Path:
    return storage.root / lane_id / "claim.lock"


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    """Atomically write *obj* as JSON to *path*.

    Writes to a sibling temp file, fsyncs, then ``os.replace`` so a reader
    never observes a partially-written file.  ``os.replace`` is atomic on the
    same filesystem on both POSIX and Windows.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _write_lock(storage: Any, lane_id: str, holder_pid: int) -> None:
    lock = _lock_path(storage, lane_id)
    lock.write_text(
        json.dumps({"pid": holder_pid, "at": _iso_now()}),
        encoding="utf-8",
    )


def _acquire_lock(storage: Any, lane_id: str, *, holder_pid: int | None = None) -> bool:
    """Try to acquire an exclusive filesystem lock via open("x").

    Returns True if the lock was acquired.  An orphaned lock is reclaimed only
    when its holder process is verifiably dead (Milestone 4: never reclaim on
    mtime alone — mtime is a minimum-age guard, liveness is the authority).
    """
    holder_pid = holder_pid or os.getpid()
    lock = _lock_path(storage, lane_id)
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        with lock.open("x", encoding="utf-8"):
            _write_lock(storage, lane_id, holder_pid)
        return True
    except FileExistsError:
        if not lock.exists():
            return False

        # Minimum-age guard: never reclaim a lock younger than the threshold,
        # even if the holder looks dead — avoids racing a live critical section.
        age = datetime.now(timezone.utc).timestamp() - lock.stat().st_mtime
        if age <= STALE_LOCK_SECONDS:
            return False

        # Read the recorded holder PID.  If we cannot determine the holder,
        # fail closed (do not steal an indeterminate lock).
        try:
            info = json.loads(lock.read_text(encoding="utf-8"))
            recorded_pid = int(info.get("pid", 0))
        except (OSError, ValueError, json.JSONDecodeError):
            return False

        # Authority gate: reclaim only when the holder process is dead.
        if recorded_pid and _process_exists(recorded_pid):
            return False  # holder still alive — do not steal the lock

        lock.unlink(missing_ok=True)
        try:
            with lock.open("x", encoding="utf-8"):
                _write_lock(storage, lane_id, holder_pid)
            return True
        except FileExistsError:
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
    terminal_id: str = ""
    session_id: str = ""
    workspace_id: str = ""
    fencing_epoch: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LaneClaim:
        required = {
            "lane_id", "session_nonce", "pid", "process_start_time",
            "created_at", "heartbeat_at",
        }
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
            terminal_id=str(data.get("terminal_id", "")),
            session_id=str(data.get("session_id", "")),
            workspace_id=str(data.get("workspace_id", "")),
            fencing_epoch=int(data.get("fencing_epoch", 1)),
        )


def _validate_writer_identity(
    existing: LaneClaim,
    *,
    session_nonce: str,
    terminal_id: str | None = None,
    session_id: str | None = None,
    workspace_id: str | None = None,
    fencing_epoch: int | None = None,
) -> None:
    """Fail-closed validation of a writer against the on-disk claim.

    Raises ClaimError with a distinct reason for each mismatch:
    - fencing epoch older than on-disk  -> superseded/fenced writer
    - session_nonce mismatch            -> session_nonce mismatch
    - workspace mismatch                -> wrong workspace
    - terminal mismatch                 -> wrong terminal
    - session mismatch                  -> wrong session
    """
    # Fencing first: a writer whose epoch does not match the current claim
    # has been superseded, even if they still hold the old nonce.
    if fencing_epoch is not None and int(fencing_epoch) != existing.fencing_epoch:
        raise ClaimError(
            f"fencing epoch mismatch for lane '{existing.lane_id}': "
            f"writer epoch {fencing_epoch} != current epoch "
            f"{existing.fencing_epoch} (superseded writer)"
        )

    if existing.session_nonce != session_nonce:
        raise ClaimError(
            f"session_nonce mismatch for lane '{existing.lane_id}'"
        )

    if (
        workspace_id is not None
        and existing.workspace_id
        and existing.workspace_id != workspace_id
    ):
        raise ClaimError(
            f"wrong workspace for lane '{existing.lane_id}': "
            f"writer workspace {workspace_id} != claim workspace "
            f"{existing.workspace_id}"
        )

    if (
        terminal_id is not None
        and existing.terminal_id
        and existing.terminal_id != terminal_id
    ):
        raise ClaimError(
            f"wrong terminal for lane '{existing.lane_id}': "
            f"writer terminal {terminal_id} != claim terminal "
            f"{existing.terminal_id}"
        )

    if (
        session_id is not None
        and existing.session_id
        and existing.session_id != session_id
    ):
        raise ClaimError(
            f"wrong session for lane '{existing.lane_id}': "
            f"writer session {session_id} != claim session "
            f"{existing.session_id}"
        )


def claim_lane(
    lane_id: str,
    storage: Any,
    lanes: list[Any],
    *,
    pid: int | None = None,
    process_start_time: str | None = None,
    terminal_id: str | None = None,
    session_id: str | None = None,
    workspace_id: str | None = None,
    ttl: int = CLAIM_TTL_SECONDS,
) -> LaneClaim:
    """Atomically claim *lane_id*, establishing terminal/session/workspace identity.

    On a successful new claim the returned claim carries a fresh
    ``fencing_epoch`` (1 for a brand-new lane, or one greater than the
    superseded claim's epoch when reclaiming a dead owner).

    Raises
    ------
    RegistryError
        If *lane_id* is unknown or disabled.
    ClaimError
        If the lane is already claimed by a live process, if PID reuse is
        detected, if an expired claim's owner is still alive (cannot reclaim),
        or if the lock cannot be acquired.
    """
    if not lane_exists(lanes, lane_id):
        raise RegistryError(f"cannot claim: unknown or disabled lane '{lane_id}'")

    pid = pid or os.getpid()
    if process_start_time is None:
        actual = _get_process_start_time(pid)
        process_start_time = actual if actual is not None else _iso_now()
    terminal_id = terminal_id or _random_id()
    session_id = session_id or _random_id()
    workspace_id = workspace_id or _workspace_id(storage)

    if not _acquire_lock(storage, lane_id):
        raise ClaimError(f"could not acquire lock for lane '{lane_id}'")

    try:
        claim_path = _claim_path(storage, lane_id)
        existing: LaneClaim | None = None
        if claim_path.exists():
            try:
                existing = LaneClaim.from_dict(
                    json.loads(claim_path.read_text(encoding="utf-8"))
                )
            except (OSError, json.JSONDecodeError, ClaimError):
                # Corrupt/partial claim file — treat as absent and overwrite.
                existing = None

        next_epoch = 1
        if existing is not None:
            age = _stale_seconds(existing.heartbeat_at)
            if age <= ttl:
                # Claim appears active.  Check PID reuse / duplicate first.
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

            # Claim is expired.  Reclaim only when the owner is verifiably dead
            # (Milestone 4): never reclaim a live-but-slow owner.
            # Use _process_exists directly (not verify_process_liveness) because
            # the recorded process_start_time may differ from the real one (e.g.
            # test backdating).  We only need to know if the PID is still in the
            # process table — if it is, treat the owner as alive and refuse takeover.
            if _process_exists(existing.pid):
                raise ClaimError(
                    f"lane '{lane_id}' claim expired (age={age:.0f}s, TTL={ttl}s) "
                    f"but owner PID {existing.pid} is still alive; cannot reclaim"
                )
            next_epoch = existing.fencing_epoch + 1

        now = _iso_now()
        claim = LaneClaim(
            lane_id=lane_id,
            session_nonce=_session_nonce(),
            pid=pid,
            process_start_time=process_start_time,
            created_at=now,
            heartbeat_at=now,
            terminal_id=terminal_id,
            session_id=session_id,
            workspace_id=workspace_id,
            fencing_epoch=next_epoch,
        )
        _atomic_write_json(claim_path, claim.to_dict())
        return claim
    finally:
        _release_lock(storage, lane_id)


def release_claim(
    lane_id: str,
    session_nonce: str,
    storage: Any,
    *,
    ttl: int = CLAIM_TTL_SECONDS,
    terminal_id: str | None = None,
    session_id: str | None = None,
    workspace_id: str | None = None,
    fencing_epoch: int | None = None,
) -> None:
    """Release the active claim for *lane_id* after fail-closed identity validation.

    Raises ClaimError if no active claim exists, the nonce does not match, or
    the supplied terminal/session/workspace/fencing identity does not match the
    on-disk claim.
    """
    if not _acquire_lock(storage, lane_id):
        raise ClaimError(f"could not acquire lock for lane '{lane_id}'")

    try:
        claim = get_active_claim(lane_id, storage, ttl=ttl)
        if claim is None:
            raise ClaimError(f"no active claim for lane '{lane_id}'")
        _validate_writer_identity(
            claim,
            session_nonce=session_nonce,
            terminal_id=terminal_id,
            session_id=session_id,
            workspace_id=workspace_id,
            fencing_epoch=fencing_epoch,
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
    """Return the active claim for *lane_id*, or *None* if unclaimed/stale.

    Reads are safe against concurrent atomic writers: a partially-written
    file is never observed because writers use temp+``os.replace``.  A corrupt
    file is treated as no active claim rather than raising.
    """
    claim_path = _claim_path(storage, lane_id)
    if not claim_path.exists():
        return None
    try:
        data = json.loads(claim_path.read_text(encoding="utf-8"))
        claim = LaneClaim.from_dict(data)
    except (OSError, json.JSONDecodeError, ClaimError):
        return None
    if _stale_seconds(claim.heartbeat_at) > ttl:
        return None
    return claim


def heartbeat_claim(
    lane_id: str,
    session_nonce: str,
    storage: Any,
    *,
    ttl: int = CLAIM_TTL_SECONDS,
    terminal_id: str | None = None,
    session_id: str | None = None,
    workspace_id: str | None = None,
    fencing_epoch: int | None = None,
) -> LaneClaim:
    """Refresh the heartbeat on an active claim under the lock.

    Holds the lane lock for the duration of the read-validate-write cycle
    (Milestone 4: previously this wrote without the lock, racing concurrent
    claim/release).  Performs fail-closed identity + fencing validation and
    an atomic write.

    Raises ClaimError if no active claim exists, the nonce does not match, or
    the supplied terminal/session/workspace/fencing identity does not match.
    """
    if not _acquire_lock(storage, lane_id):
        raise ClaimError(f"could not acquire lock for lane '{lane_id}'")

    try:
        claim = get_active_claim(lane_id, storage, ttl=ttl)
        if claim is None:
            raise ClaimError(f"no active claim for lane '{lane_id}'")
        _validate_writer_identity(
            claim,
            session_nonce=session_nonce,
            terminal_id=terminal_id,
            session_id=session_id,
            workspace_id=workspace_id,
            fencing_epoch=fencing_epoch,
        )

        updated = replace(claim, heartbeat_at=_iso_now())
        _atomic_write_json(_claim_path(storage, lane_id), updated.to_dict())

        storage.append_event(lane_id, {
            "type": "heartbeat",
            "lane_id": lane_id,
            "session_nonce": session_nonce[:12] + "...",
            "pid": claim.pid,
            "fencing_epoch": claim.fencing_epoch,
            "status": "acknowledged",
            "timestamp": _iso_now(),
        })
        return updated
    finally:
        _release_lock(storage, lane_id)


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
