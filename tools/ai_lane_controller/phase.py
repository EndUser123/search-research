"""Lane phase state machine -- coordinates bidirectional message flow.

A lane moves through three phases::

    IDLE -> WAITING_FOR_CHATGPT -> WAITING_FOR_CLAUDE -> IDLE

ChromeEndpoint submits a user message -> phase becomes WAITING_FOR_CHATGPT.
Agent SDK daemon sees that phase, submits via SDK -> WAITING_FOR_CLAUDE.
ChromeEndpoint polls DOM for the response -> writes it -> back to IDLE.

Phase TTL and watchdog: if an endpoint crashes mid-transition the phase
stays stuck.  `recover_stale_phase` resets any phase that has been parked
longer than *max_dwell* back to IDLE so the next healthy endpoint can proceed.

Concurrency: all mutating phase operations acquire the lane lock (same
`claim.lock` used by `claim.py`), preventing two endpoints from
transitioning simultaneously.  Reads are lock-free (atomic writers).

Phase file: `.ai-lanes/<lane_id>/phase.json`
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .claim import _iso_now, _acquire_lock, _release_lock


# -- Constants ---------------------------------------------------------------

PHASE_IDLE = "IDLE"
PHASE_WAITING_FOR_CHATGPT = "WAITING_FOR_CHATGPT"
PHASE_WAITING_FOR_CLAUDE = "WAITING_FOR_CLAUDE"

ALL_PHASES = frozenset({PHASE_IDLE, PHASE_WAITING_FOR_CHATGPT, PHASE_WAITING_FOR_CLAUDE})

VALID_TRANSITIONS: dict[str, set[str]] = {
    PHASE_IDLE: {PHASE_WAITING_FOR_CHATGPT},
    PHASE_WAITING_FOR_CHATGPT: {PHASE_WAITING_FOR_CLAUDE},
    PHASE_WAITING_FOR_CLAUDE: {PHASE_IDLE},
}

DEFAULT_PHASE_TTL_SECONDS = 300


# -- Errors ------------------------------------------------------------------


class PhaseError(Exception):
    """Phase operation failed."""


class PhaseTransitionError(PhaseError):
    """Illegal phase transition."""


# -- State -------------------------------------------------------------------


@dataclass(frozen=True)
class PhaseState:
    """Snapshot of a lane's current phase."""

    lane_id: str
    phase: str
    fencing_epoch: int
    entered_at: str
    updated_at: str
    heartbeat_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "lane_id": self.lane_id,
            "phase": self.phase,
            "fencing_epoch": self.fencing_epoch,
            "entered_at": self.entered_at,
            "updated_at": self.updated_at,
            "heartbeat_at": self.heartbeat_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhaseState:
        required = {"lane_id", "phase", "fencing_epoch", "entered_at"}
        missing = required - set(data.keys())
        if missing:
            raise PhaseError(f"phase state missing fields: {', '.join(sorted(missing))}")
        return cls(
            lane_id=data["lane_id"],
            phase=data["phase"],
            fencing_epoch=int(data["fencing_epoch"]),
            entered_at=str(data["entered_at"]),
            updated_at=str(data.get("updated_at", data["entered_at"])),
            heartbeat_at=str(data.get("heartbeat_at", data["entered_at"])),
        )


# -- Path helpers ------------------------------------------------------------


def _phase_path(storage: Any, lane_id: str) -> Path:
    return storage.root / lane_id / "phase.json"


def _atomic_write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(obj, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


# -- Read --------------------------------------------------------------------


def get_phase(storage: Any, lane_id: str) -> PhaseState | None:
    """Return the current phase for *lane_id*, or *None* if uninitialised."""
    path = _phase_path(storage, lane_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return PhaseState.from_dict(data)
    except (OSError, json.JSONDecodeError, PhaseError):
        return None


# -- Mutating operations (all acquire the lane lock) -------------------------


def _init_phase(storage: Any, lane_id: str) -> PhaseState:
    """Initialise phase file to IDLE.  Idempotent.  Caller MUST hold lock."""
    path = _phase_path(storage, lane_id)
    if path.exists():
        return PhaseState.from_dict(
            json.loads(path.read_text(encoding="utf-8"))
        )
    now = _iso_now()
    state = PhaseState(
        lane_id=lane_id,
        phase=PHASE_IDLE,
        fencing_epoch=1,
        entered_at=now,
        updated_at=now,
        heartbeat_at=now,
    )
    _atomic_write_json(path, state.to_dict())
    return state


def set_phase(
    storage: Any,
    lane_id: str,
    phase: str,
    *,
    fencing_epoch: int | None = None,
) -> PhaseState:
    """Directly set the phase without transition validation (watchdog recovery)."""
    if phase not in ALL_PHASES:
        raise PhaseError(f"unknown phase '{phase}'")

    if not _acquire_lock(storage, lane_id):
        raise PhaseError(f"could not acquire lock for lane '{lane_id}'")

    try:
        current = get_phase(storage, lane_id)
        now = _iso_now()
        next_epoch = fencing_epoch if fencing_epoch is not None else (
            (current.fencing_epoch + 1) if current else 1
        )
        state = PhaseState(
            lane_id=lane_id,
            phase=phase,
            fencing_epoch=next_epoch,
            entered_at=now,
            updated_at=now,
            heartbeat_at=now,
        )
        _atomic_write_json(_phase_path(storage, lane_id), state.to_dict())
        _log_phase_event(storage, lane_id, state, "set")
        return state
    finally:
        _release_lock(storage, lane_id)


def transition_phase(
    storage: Any,
    lane_id: str,
    from_phase: str,
    to_phase: str,
) -> PhaseState:
    """Validate and perform a phase transition under the lane lock."""
    allowed = VALID_TRANSITIONS.get(from_phase)
    if allowed is None or to_phase not in allowed:
        raise PhaseTransitionError(
            f"transition '{from_phase}' -> '{to_phase}' is not allowed"
        )

    if not _acquire_lock(storage, lane_id):
        raise PhaseError(f"could not acquire lock for lane '{lane_id}'")

    try:
        current = get_phase(storage, lane_id)
        if current is None:
            now = _iso_now()
            state = PhaseState(
                lane_id=lane_id,
                phase=to_phase,
                fencing_epoch=1,
                entered_at=now,
                updated_at=now,
                heartbeat_at=now,
            )
            _atomic_write_json(_phase_path(storage, lane_id), state.to_dict())
            _log_phase_event(storage, lane_id, state, "transition")
            return state

        if current.phase != from_phase:
            raise PhaseError(
                f"phase mismatch for lane '{lane_id}': "
                f"expected '{from_phase}', got '{current.phase}'"
            )

        now = _iso_now()
        state = replace(
            current,
            phase=to_phase,
            updated_at=now,
            heartbeat_at=now,
        )
        _atomic_write_json(_phase_path(storage, lane_id), state.to_dict())
        _log_phase_event(storage, lane_id, state, "transition")
        return state
    finally:
        _release_lock(storage, lane_id)


def phase_heartbeat(
    storage: Any,
    lane_id: str,
) -> PhaseState:
    """Refresh the heartbeat on the current phase under the lock."""
    if not _acquire_lock(storage, lane_id):
        raise PhaseError(f"could not acquire lock for lane '{lane_id}'")

    try:
        current = get_phase(storage, lane_id)
        if current is None:
            current = _init_phase(storage, lane_id)

        now = _iso_now()
        state = replace(current, updated_at=now, heartbeat_at=now)
        _atomic_write_json(_phase_path(storage, lane_id), state.to_dict())
        _log_phase_event(storage, lane_id, state, "heartbeat")
        return state
    finally:
        _release_lock(storage, lane_id)


def recover_stale_phase(
    storage: Any,
    lane_id: str,
    *,
    max_dwell: int = DEFAULT_PHASE_TTL_SECONDS,
) -> PhaseState | None:
    """Reset a stale non-IDLE phase to IDLE, or return None.

    Double-checks under the lock before writing to defeat races.
    """
    current = get_phase(storage, lane_id)
    if current is None or current.phase == PHASE_IDLE:
        return None

    now = datetime.now(timezone.utc)
    entered = datetime.fromisoformat(current.entered_at.replace("Z", "+00:00"))
    if (now - entered).total_seconds() <= max_dwell:
        return None  # Still fresh

    if not _acquire_lock(storage, lane_id):
        return None  # Another process active -- don't fight for recovery.

    try:
        recheck = get_phase(storage, lane_id)
        if recheck is None or recheck.phase != current.phase:
            return None
        entered2 = datetime.fromisoformat(recheck.entered_at.replace("Z", "+00:00"))
        if (now - entered2).total_seconds() <= max_dwell:
            return None

        now_str = _iso_now()
        state = PhaseState(
            lane_id=lane_id,
            phase=PHASE_IDLE,
            fencing_epoch=recheck.fencing_epoch + 1,
            entered_at=now_str,
            updated_at=now_str,
            heartbeat_at=now_str,
        )
        _atomic_write_json(_phase_path(storage, lane_id), state.to_dict())
        _log_phase_event(storage, lane_id, state, "recovery")
        return state
    finally:
        _release_lock(storage, lane_id)


# -- Event logging -----------------------------------------------------------


def _log_phase_event(
    storage: Any,
    lane_id: str,
    state: PhaseState,
    action: str,
) -> None:
    """Append a phase-transition event to the lane's event log."""
    try:
        storage.append_event(lane_id, {
            "type": "phase_transition",
            "lane_id": lane_id,
            "phase": state.phase,
            "fencing_epoch": state.fencing_epoch,
            "action": action,
            "timestamp": _iso_now(),
        })
    except Exception:
        pass  # Non-critical -- logging failure must not break transitions.