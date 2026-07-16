"""Controller-only state I/O for the context controller.

Two responsibilities, clearly separated:

1. **Envelope reader (read-only)** — wraps `SnapshotFileStorage.load_handoff()`
   so the rest of the controller does not import the snapshot plugin directly.
   Fail-open: any error → `None` envelope. The renderer treats `None` as
   "no prior context" and omits envelope-derived lines.

2. **Controller-only `policy.json` I/O** — persists `phase` + `context_health`
   counters. This is the **only** file the controller writes. Writes are
   serialized within the process via a per-terminal `threading.Lock`, and
   the file itself is written via `atomic_write` (temp + rename) so a crash
   mid-write cannot corrupt the file. Terminal isolation is per-directory
   (each terminal id gets its own subdirectory and its own lock).

The controller never writes envelope-derived fields. A `ValueError` is
raised by `save_policy_state` if the input dict contains any forbidden key.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Use absolute imports rather than `..file_lock_manager` so the controller
# does not depend on `hooks` being importable as a parent package. Tests
# (conftest.py sys.path injection) and the hook runtime both add
# `P:/.claude/hooks/` to `sys.path`, making absolute imports resolve uniformly.
#
# `terminal_detection` is a thin shim that re-exports the two detect* helpers
# but NOT `resolve_terminal_key`. The real `resolve_terminal_key` lives in
# `__lib.terminal_detection`, so we import from there directly to avoid the
# shim masking the symbol.
from file_lock_manager import atomic_write
from __lib.terminal_detection import resolve_terminal_key

logger = logging.getLogger(__name__)

# ---- Schema constants -----------------------------------------------------

PHASE_DEFAULT = "general"
VALID_PHASES = frozenset(
    {"research", "planning", "implementation", "review", "debugging", "handoff", "general"}
)

POLICY_SCHEMA_VERSION = 1

# Defense-in-depth: the controller's policy.json must never carry
# envelope-derived fields. If a future caller tries to write one of these,
# save_policy_state raises ValueError *before* touching disk.
#
# The set is the union of fields documented in the resume_snapshot schema
# (verified against PreCompact_snapshot_capture.py:920-946) plus the
# top-level envelope wrapper fields.
FORBIDDEN_POLICY_KEYS = frozenset(
    {
        # resume_snapshot fields
        "goal",
        "next_step",
        "active_files",
        "blockers",
        "open_questions",
        "recent_decisions",
        "verification",
        "recent_changes",
        "transcript_path",
        "transcript_chain",
        "pending_operations",
        "last_user_message",
        "user_message_locator",
        "decision_refs",
        "evidence_refs",
        "tasks_snapshot",
        "prompt_enhancement",
        "message_intent",
        "goal_origin",
        "active_skill",
        "session_chain",
        "progress_percent",
        "progress_state",
        "quality_score",
        "consumed_at",
        "consumed_by_session_id",
        "rejected_at",
        "rejected_by_session_id",
        "rejection_reason",
        "snapshot_id",
        "source_session_id",
        "status",
        "created_at",
        "expires_at",
        "n_1_transcript_path",
        "n_2_transcript_path",
        # top-level envelope keys
        "resume_snapshot",
        "decision_register",
        "evidence_index",
        "checksum",
    }
)

# Health counters allowed in policy.json
ALLOWED_HEALTH_KEYS = frozenset(
    {
        "turn_count",
        "large_outputs",
        "phase_turns",
        "should_compact",
        "should_start_fresh",
    }
)

# Default file-system roots (used when caller does not pass state_root / project_root)
DEFAULT_STATE_ROOT = Path("P:/.claude/state/context-controller")
DEFAULT_PROJECT_ROOT = Path("P:/")


# ---- Per-terminal lock registry -------------------------------------------
#
# The controller may be called concurrently from multiple threads in the
# same process (e.g. a router that fans out to several hooks at once). A
# process-wide registry of per-terminal locks gives us correct serialization
# without coupling to the cross-process `file_lock_manager.acquire_lock`
# (which is session-scoped and adds a `_get_session_id()` dependency).

_terminal_locks: dict[str, threading.Lock] = {}
_terminal_locks_meta_lock = threading.Lock()


def _get_terminal_lock(safe_terminal_id: str) -> threading.Lock:
    """Return a process-wide lock for this terminal id, creating it lazily."""
    with _terminal_locks_meta_lock:
        lock = _terminal_locks.get(safe_terminal_id)
        if lock is None:
            lock = threading.Lock()
            _terminal_locks[safe_terminal_id] = lock
        return lock


# ---- ContextHealth dataclass ----------------------------------------------


@dataclass(frozen=True)
class ContextHealth:
    """Counters and flags for context-budget health.

    The plan defines this as controller-only state; envelope-derived facts
    never enter this struct.
    """

    turn_count: int = 0
    large_outputs: int = 0
    phase_turns: int = 0
    should_compact: bool = False
    should_start_fresh: bool = False

    def __add__(self, other: "ContextHealth") -> "ContextHealth":
        """Element-wise addition. Booleans OR together."""
        if not isinstance(other, ContextHealth):
            return NotImplemented
        return ContextHealth(
            turn_count=self.turn_count + other.turn_count,
            large_outputs=self.large_outputs + other.large_outputs,
            phase_turns=self.phase_turns + other.phase_turns,
            should_compact=self.should_compact or other.should_compact,
            should_start_fresh=self.should_start_fresh or other.should_start_fresh,
        )


# ---- Snapshot plugin resolver (lazy, fail-open) ---------------------------


def _try_import_snapshot_storage() -> Any | None:
    """Best-effort import of the snapshot plugin's storage class.

    Adds the snapshot plugin's `__lib` directory to `sys.path` once, then
    imports `snapshot_files.SnapshotFileStorage`. Returns the class on
    success, `None` on any failure (ImportError, OSError, etc.).

    Tests monkeypatch this to inject a `FakeSnapshotFileStorage` that reads
    from `tmp_path` instead of the real artifacts root.
    """
    try:
        snapshot_lib = (
            Path("P:/packages/.claude-marketplace/plugins/snapshot")
            / "scripts"
            / "hooks"
            / "__lib"
        )
        lib_str = str(snapshot_lib)
        if lib_str not in sys.path:
            sys.path.insert(0, lib_str)
        from snapshot_files import SnapshotFileStorage  # type: ignore[import-not-found]

        return SnapshotFileStorage
    except Exception as exc:  # noqa: BLE001 — fail-open by design
        logger.debug("[context_controller.state] snapshot import failed: %s", exc)
        return None


# ---- Envelope reader ------------------------------------------------------


def read_handoff_envelope(
    terminal_id: str,
    *,
    project_root: Path | None = None,
) -> dict[str, Any] | None:
    """Read the latest snapshot handoff envelope for this terminal.

    Returns the full envelope dict (top-level keys: schema_version,
    resume_snapshot, decision_register, evidence_index, checksum) or `None`
    on missing/corrupt/expired envelope. Never raises.

    The envelope is treated as read-only. The controller never writes back
    to it. When the snapshot plugin cannot be imported (e.g. CI without
    the plugin), this returns `None` and the renderer falls back to
    "no prior context".
    """
    if not terminal_id or not terminal_id.strip():
        logger.warning("[context_controller.state] read_handoff_envelope: empty terminal_id")
        return None

    storage_cls = _try_import_snapshot_storage()
    if storage_cls is None:
        return None

    try:
        # Sanitize the terminal id through the canonical resolver. This also
        # validates it (raises ValueError on path-traversal / null bytes).
        try:
            safe_id = resolve_terminal_key(terminal_id)
        except ValueError as exc:
            logger.warning(
                "[context_controller.state] terminal_id failed validation: %s", exc
            )
            return None

        root = Path(project_root) if project_root is not None else DEFAULT_PROJECT_ROOT
        storage = storage_cls(root, safe_id)
        payload = storage.load_handoff()
        return payload
    except Exception as exc:  # noqa: BLE001 — fail-open by design
        logger.warning(
            "[context_controller.state] read_handoff_envelope failed: %s", exc,
            exc_info=False,
        )
        return None


# ---- Policy state path helpers --------------------------------------------


def _policy_path(terminal_id: str, state_root: Path) -> tuple[Path, str]:
    """Resolve the per-terminal policy.json path under `state_root`.

    Sanitizes the terminal id through `resolve_terminal_key` so a caller
    cannot inject path separators into the file path. Raises `ValueError`
    on invalid input.

    Returns a (path, safe_id) tuple. The safe_id is returned so callers
    can index the per-terminal lock registry without re-sanitizing.
    """
    safe_id = resolve_terminal_key(terminal_id)
    return Path(state_root) / safe_id / "policy.json", safe_id


def _default_policy() -> dict[str, Any]:
    """Return a fresh, in-memory default policy dict."""
    return {
        "schema_version": POLICY_SCHEMA_VERSION,
        "phase": PHASE_DEFAULT,
        "context_health": asdict(ContextHealth()),
        "updated_at": "",
    }


# ---- Policy I/O -----------------------------------------------------------


def _validate_policy_dict(policy: dict[str, Any]) -> None:
    """Reject envelope-derived keys. Defense-in-depth.

    Called before any disk write. A `ValueError` is raised if any forbidden
    key is present in the policy dict. This is a hard guard: it is never
    bypassed by `save_policy_state`.
    """
    if not isinstance(policy, dict):
        raise ValueError(
            f"policy must be a dict, got {type(policy).__name__}"
        )

    bad = sorted(set(policy.keys()) & FORBIDDEN_POLICY_KEYS)
    if bad:
        raise ValueError(
            "policy.json must not contain envelope-derived fields: "
            f"{bad}. The controller is read-only against the handoff envelope."
        )

    if "phase" in policy and policy["phase"] not in VALID_PHASES:
        raise ValueError(
            f"invalid phase {policy['phase']!r}; must be one of {sorted(VALID_PHASES)}"
        )

    if "context_health" in policy:
        health = policy["context_health"]
        if not isinstance(health, dict):
            raise ValueError(
                f"context_health must be a dict, got {type(health).__name__}"
            )
        bad_health = sorted(set(health.keys()) - ALLOWED_HEALTH_KEYS)
        if bad_health:
            raise ValueError(
                f"context_health contains unknown fields: {bad_health}"
            )


def _coerce_health(health: Any) -> dict[str, Any]:
    """Best-effort coerce an input health value into the canonical dict shape.

    Accepts either a `ContextHealth` dataclass or a dict. Returns a fresh
    dict with only the allowed keys. Missing keys default to 0 / False.
    """
    if isinstance(health, ContextHealth):
        return asdict(health)
    if isinstance(health, dict):
        return {k: health[k] for k in ALLOWED_HEALTH_KEYS if k in health}
    raise ValueError(
        f"context_health must be ContextHealth or dict, got {type(health).__name__}"
    )


def load_policy_state(
    terminal_id: str,
    *,
    state_root: Path,
) -> dict[str, Any]:
    """Load the controller-only policy.json for this terminal.

    Returns defaults on missing or corrupt file. Never raises. Corrupt JSON
    is treated as if the file did not exist (with a warn log).
    """
    try:
        path, _ = _policy_path(terminal_id, state_root)
    except ValueError as exc:
        logger.warning("[context_controller.state] load: %s", exc)
        return _default_policy()

    if not path.exists():
        return _default_policy()

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning(
            "[context_controller.state] corrupt policy.json at %s: %s — using defaults",
            path,
            exc,
        )
        return _default_policy()

    if not isinstance(data, dict):
        logger.warning(
            "[context_controller.state] policy.json is not a dict: %s — using defaults",
            path,
        )
        return _default_policy()

    # Merge with defaults so missing keys are filled in. Drop unknown keys
    # silently (forward compat).
    defaults = _default_policy()
    merged: dict[str, Any] = {}
    for k in defaults:
        if k in data and k != "context_health":
            merged[k] = data[k]
    if "context_health" in data and isinstance(data["context_health"], dict):
        merged["context_health"] = {
            k: data["context_health"].get(k, defaults["context_health"][k])
            for k in ALLOWED_HEALTH_KEYS
        }
    else:
        merged["context_health"] = dict(defaults["context_health"])
    merged.setdefault("phase", PHASE_DEFAULT)
    if merged["phase"] not in VALID_PHASES:
        merged["phase"] = PHASE_DEFAULT
    return merged


def save_policy_state(
    terminal_id: str,
    policy: dict[str, Any],
    *,
    state_root: Path,
) -> bool:
    """Atomically write policy.json. Returns True on success.

    Validates the policy dict against `FORBIDDEN_POLICY_KEYS` and
    `ALLOWED_HEALTH_KEYS` before writing. Raises `ValueError` on any
    envelope-derived or unknown key. Returns False on I/O failure
    (no exception propagates from the writer).
    """
    _validate_policy_dict(policy)

    try:
        path, safe_id = _policy_path(terminal_id, state_root)
    except ValueError as exc:
        logger.warning("[context_controller.state] save: %s", exc)
        return False

    # Defensive copy + canonical-shape normalization
    payload = {
        "schema_version": POLICY_SCHEMA_VERSION,
        "phase": policy.get("phase", PHASE_DEFAULT),
        "context_health": _coerce_health(policy.get("context_health", {})),
        "updated_at": policy.get("updated_at", ""),
    }

    lock = _get_terminal_lock(safe_id)
    with lock:
        try:
            target_dir = path.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            atomic_write(
                path,
                json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
            )
            return True
        except OSError as exc:
            logger.warning(
                "[context_controller.state] save_policy_state I/O failure for %s: %s",
                path,
                exc,
            )
            return False


def update_policy_state(
    terminal_id: str,
    *,
    state_root: Path,
    phase: str | None = None,
    health_delta: ContextHealth | None = None,
    touch_updated_at: bool = True,
) -> dict[str, Any]:
    """Load, merge, save, and return the merged policy dict.

    Args:
        terminal_id: per-terminal key.
        state_root: policy root directory (tests pass `tmp_path`).
        phase: if not None, replaces the current phase and resets
            `phase_turns` to 0 (only on a CHANGE).
        health_delta: if not None, element-wise added to current counters.
        touch_updated_at: when True, set `updated_at` to the current UTC
            ISO-8601 string before save. When False, leave the existing
            `updated_at` untouched (used by tests that want determinism).

    Returns:
        The merged policy dict as it was just written to disk (or as it
        would be written, if the save was skipped).

    Atomicity: the per-terminal `threading.Lock` serializes the load +
    save within this process, so two concurrent updates cannot lose
    writes to the policy file. Cross-process safety is provided by
    `atomic_write` (temp + rename) — if the process crashes mid-write,
    the rename never happened, so the file is either the old version
    or the new version, never a half-written one.
    """
    if phase is not None and phase not in VALID_PHASES:
        raise ValueError(
            f"invalid phase {phase!r}; must be one of {sorted(VALID_PHASES)}"
        )
    if health_delta is not None and not isinstance(health_delta, ContextHealth):
        raise ValueError(
            f"health_delta must be ContextHealth, got {type(health_delta).__name__}"
        )

    try:
        path, safe_id = _policy_path(terminal_id, state_root)
    except ValueError as exc:
        logger.warning("[context_controller.state] update: %s", exc)
        return _default_policy()

    lock = _get_terminal_lock(safe_id)
    with lock:
        current = load_policy_state(terminal_id, state_root=state_root)

        # Merge phase
        if phase is not None and phase != current.get("phase"):
            current["phase"] = phase
            # Plan: "phase: if not None, replaces the current phase and
            # resets phase_turns to 0." So phase_turns resets only on a
            # CHANGE.
            current["context_health"]["phase_turns"] = 0
        elif phase is not None:
            current["phase"] = phase  # explicit no-op; keep current phase_turns

        # Merge health delta
        if health_delta is not None:
            existing = ContextHealth(**current["context_health"])
            current["context_health"] = asdict(existing + health_delta)

        if touch_updated_at:
            current["updated_at"] = datetime.now(UTC).isoformat()

        # Validate before write; on failure, return the in-memory state
        # and do not touch disk. (Forbidden keys should never appear here
        # because we only ever merge our own fields, but the guard stays
        # for defense.)
        try:
            _validate_policy_dict(current)
        except ValueError as exc:
            logger.error(
                "[context_controller.state] update_policy_state produced invalid "
                "policy: %s — returning without writing",
                exc,
            )
            return current

        try:
            target_dir = path.parent
            target_dir.mkdir(parents=True, exist_ok=True)
            atomic_write(
                path,
                json.dumps(current, indent=2, ensure_ascii=False, sort_keys=True),
            )
        except OSError as exc:
            logger.warning(
                "[context_controller.state] update_policy_state I/O failure for %s: %s",
                path,
                exc,
            )
    return current


# ---- Re-exports -----------------------------------------------------------

__all__ = [
    "ALLOWED_HEALTH_KEYS",
    "ContextHealth",
    "DEFAULT_PROJECT_ROOT",
    "DEFAULT_STATE_ROOT",
    "FORBIDDEN_POLICY_KEYS",
    "PHASE_DEFAULT",
    "POLICY_SCHEMA_VERSION",
    "VALID_PHASES",
    "_try_import_snapshot_storage",  # exported for tests
    "load_policy_state",
    "read_handoff_envelope",
    "save_policy_state",
    "update_policy_state",
]
