"""Controller identity and command authority.

A controller Claude session has its own identity, fencing epoch, and claim
nonce.  All controller-issued commands carry this identity so the local
controller process can validate authority before executing.

Architecture:
  Controller Claude  --(command)-->  Local Controller Process  --(UI)→  Target Lane
  (decides what)     (validated by identity fields)  (validates, serializes)  (executes)
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ControllerError(PermissionError):
    """Controller identity or authority validation failed."""


@dataclass(frozen=True)
class ControllerIdentity:
    """Identity of the controller Claude Code session."""

    controller_session_id: str
    controller_claim_nonce: str
    pid: int
    process_start_time: str
    fencing_epoch: int
    created_at: str
    heartbeat_at: str
    workspace_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ControllerIdentity:
        required = {
            "controller_session_id", "controller_claim_nonce", "pid",
            "process_start_time", "fencing_epoch", "created_at",
            "heartbeat_at", "workspace_id",
        }
        missing = required - set(data.keys())
        if missing:
            raise ControllerError(f"missing fields: {', '.join(sorted(missing))}")
        return cls(**data)


@dataclass(frozen=True)
class ControllerCommand:
    """A command from the controller Claude to the local controller process."""

    controller_session_id: str
    controller_claim_nonce: str
    controller_fencing_epoch: int
    command_id: str
    idempotency_key: str
    target_lane: str
    expected_lane_claim_nonce: str
    expected_lane_fencing_epoch: int
    operation: str          # "deliver", "verify", "correct", "bind", "status"
    handoff_id: str | None = None
    payload: str | None = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ControllerCommand:
        required = {
            "controller_session_id", "controller_claim_nonce",
            "controller_fencing_epoch", "command_id", "idempotency_key",
            "target_lane", "expected_lane_claim_nonce",
            "expected_lane_fencing_epoch", "operation",
        }
        missing = required - set(data.keys())
        if missing:
            raise ControllerError(f"command missing fields: {', '.join(sorted(missing))}")
        return cls(**data)


def create_controller_identity(
    controller_session_id: str | None = None,
    workspace_id: str | None = None,
) -> ControllerIdentity:
    """Create a new controller identity with random nonce and epoch 1."""
    from .registry import LANE_IDS

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return ControllerIdentity(
        controller_session_id=controller_session_id or uuid.uuid4().hex,
        controller_claim_nonce=uuid.uuid4().hex,
        pid=os.getpid(),
        process_start_time=_get_process_start_time(os.getpid()) or now,
        fencing_epoch=1,
        created_at=now,
        heartbeat_at=now,
        workspace_id=workspace_id or _workspace_id(),
    )


def validate_controller_command(
    command: ControllerCommand,
    identity: ControllerIdentity,
    *,
    seen_idempotency_keys: set[str] | None = None,
    target_fencing_epoch: int | None = None,
) -> None:
    """Fail-closed validation of a controller command.

    Raises ControllerError if any check fails.
    """
    # Session match
    if command.controller_session_id != identity.controller_session_id:
        raise ControllerError(
            f"controller session mismatch: "
            f"command={command.controller_session_id[:12]}... "
            f"identity={identity.controller_session_id[:12]}..."
        )
    # Nonce match
    if command.controller_claim_nonce != identity.controller_claim_nonce:
        raise ControllerError("controller claim nonce mismatch")
    # Fencing
    if command.controller_fencing_epoch < identity.fencing_epoch:
        raise ControllerError(
            f"stale controller epoch: command={command.controller_fencing_epoch} "
            f"current={identity.fencing_epoch}"
        )
    # Idempotency
    if seen_idempotency_keys is not None:
        if command.idempotency_key in seen_idempotency_keys:
            raise ControllerError(
                f"duplicate idempotency key: {command.idempotency_key[:16]}..."
            )
        seen_idempotency_keys.add(command.idempotency_key)
    # Target lane must be in standard set
    from .registry import LANE_IDS
    if command.target_lane not in LANE_IDS:
        raise ControllerError(
            f"invalid target lane: {command.target_lane} "
            f"(must be one of {LANE_IDS})"
        )


def _get_process_start_time(pid: int) -> str | None:
    """Get ISO-8601 creation time of a running process."""
    import platform
    if platform.system() != "Windows":
        return None
    import ctypes
    from ctypes import wintypes
    from datetime import timedelta

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None
    try:
        creation = wintypes.FILETIME()
        if not kernel32.GetProcessTimes(
            handle, ctypes.byref(creation),
            ctypes.byref(wintypes.FILETIME()),
            ctypes.byref(wintypes.FILETIME()),
            ctypes.byref(wintypes.FILETIME()),
        ):
            return None
        ns_100 = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        nt_epoch = datetime(1601, 1, 1, tzinfo=timezone.utc)
        return (nt_epoch + timedelta(microseconds=ns_100 // 10)).isoformat().replace("+00:00", "Z")
    finally:
        kernel32.CloseHandle(handle)


def _workspace_id() -> str:
    """Stable workspace identity from the repository root."""
    import hashlib
    try:
        root = str(Path("P:/").resolve())
    except Exception:
        root = "P:/"
    return hashlib.sha256(root.encode("utf-8")).hexdigest()[:16]