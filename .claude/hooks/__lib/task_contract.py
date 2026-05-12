#!/usr/bin/env python3
"""
task_contract - Terminal-scoped task contract storage for goal-fit gating.

Stores a minimal JSON contract describing what a debugging/implementation task
requires the assistant to produce (root_cause, fix, tests, verification).

Location: ~/.claude/.artifacts/{terminal_id}/hook_state/task_contract.json

v1: keyword-based enforcement with phase-mismatch and orthogonality guards.
v2: adds embedding-based semantic continuity, phase state machine, and
    evidence accumulation. V2 is backward-compatible; existing contracts
    auto-migrate on load.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

_CONTRACT_FILENAME = "task_contract.json"

VALID_OUTPUTS = frozenset({
    "root_cause",
    "fix",
    "tests",
    "verification_commands",
})


def _home() -> Path:
    return Path.home()


def _contract_path(terminal_id: str) -> Path:
    """Return the canonical Artifacts path for this terminal's contract."""
    return (
        _home()
        / ".claude"
        / ".artifacts"
        / terminal_id
        / "hook_state"
        / _CONTRACT_FILENAME
    )


def load_contract(terminal_id: str) -> dict[str, Any] | None:
    """Load the active task contract for this terminal.

    Auto-migrates v1 contracts to v2 schema on load (no embeddings in v2).
    Returns None if no contract exists or it is not active.
    """
    path = _contract_path(terminal_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") != "active":
            return None
        # Migrate v1 → v2 if needed (adds phase/evidence without embeddings)
        if "v2_schema_version" not in data:
            data = _migrate_to_v2(terminal_id, data)
        return data
    except (json.JSONDecodeError, OSError):
        return None


def _migrate_to_v2(terminal_id: str, contract: dict) -> dict:
    """Add v2 fields to a v1 contract and persist the migration.

    Migration is additive — all v1 fields are preserved.
    No embedding computation: semantic matching is now LLM-based.
    """
    from __lib.semantic_matcher_llm import extract_subject_tokens

    canonical_subject = extract_subject_tokens(contract.get("description", ""))

    now_iso = _now_iso()
    migrated: dict[str, Any] = {
        **contract,
        "canonical_subject": canonical_subject,
        # Safe default phase for migrated contracts: assume in-progress code work
        "phase": contract.get("phase", "implementation"),
        "phase_history": contract.get("phase_history", []),
        "evidence": contract.get(
            "evidence",
            {
                "files_modified": [],
                "tests_run": [],
                "verification_commands_executed": [],
                "git_commits": 0,
                "design_artifacts": [],
                "code_generated": False,
            },
        ),
        "v2_schema_version": "2.0",
        "migrated_from_v1": True,
        "last_updated_at": now_iso,
    }

    _save_raw(terminal_id, migrated)
    _log_v2_telemetry(terminal_id, "contract_migrated_to_v2", {
        "task_id": contract.get("task_id", "?"),
        "phase": migrated["phase"],
    })
    return migrated


def _save_raw(terminal_id: str, contract: dict) -> None:
    """Write contract to disk (used by migration)."""
    path = _contract_path(terminal_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(contract, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(path)


def save_contract(
    terminal_id: str,
    *,
    task_id: str,
    description: str,
    required_outputs: list[str],
    task_class: str | None = None,
    # ---- v2 fields (optional) ----
    canonical_subject: list[str] | None = None,
    phase: str = "exploration",
    evidence: dict | None = None,
    v2_schema_version: str | None = None,
) -> dict[str, Any]:
    """Create or update a task contract atomically.

    V1-compatible: all v2 fields are optional and default to sensible values.
    Semantic matching is LLM-based (semantic_matcher_llm.py), not embedding-based.

    Returns the saved contract dict.
    """
    from __lib.semantic_matcher_llm import extract_subject_tokens

    now_iso = _now_iso()
    existing = load_contract(terminal_id)
    # Preserve task_id on re-save of same task
    if existing and existing.get("task_id") == task_id:
        task_id = existing["task_id"]

    if canonical_subject is None:
        try:
            canonical_subject = extract_subject_tokens(description)
        except Exception:
            canonical_subject = []

    contract: dict[str, Any] = {
        "task_id": task_id,
        "description": description,
        "required_outputs": [o for o in required_outputs if o in VALID_OUTPUTS],
        "created_at": existing["created_at"] if existing else now_iso,
        "last_updated_at": now_iso,
        "status": "active",
        # V1: task class awareness
        **({} if task_class is None else {"task_class": task_class}),
        # V2 fields
        "canonical_subject": canonical_subject,
        "phase": phase,
        "phase_history": existing.get("phase_history", []) if existing else [],
        "evidence": evidence if evidence is not None else (existing.get("evidence") if existing else {
            "files_modified": [],
            "tests_run": [],
            "verification_commands_executed": [],
            "git_commits": 0,
            "design_artifacts": [],
            "code_generated": False,
        }),
        "provided_outputs": existing.get("provided_outputs", []) if existing else [],
        "v2_schema_version": v2_schema_version or "2.0",
    }

    path = _contract_path(terminal_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(contract, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(path)
    return contract


def update_phase(
    terminal_id: str,
    new_phase: str,
    *,
    phase_history: list[dict] | None = None,
) -> None:
    """Update the phase and optionally phase_history of an existing active contract."""
    existing = load_contract(terminal_id)
    if not existing:
        return
    if phase_history is not None:
        existing["phase_history"] = phase_history
    existing["phase"] = new_phase
    existing["last_updated_at"] = _now_iso()
    _save_raw(terminal_id, existing)


def update_evidence(terminal_id: str, evidence: dict) -> None:
    """Merge new evidence into the contract's evidence field."""
    existing = load_contract(terminal_id)
    if not existing:
        return
    from __lib.evidence_collector import accumulate
    existing["evidence"] = accumulate(existing.get("evidence", {}), evidence)
    existing["last_updated_at"] = _now_iso()
    _save_raw(terminal_id, existing)


def mark_provided_outputs(terminal_id: str, provided: list[str]) -> None:
    """Record which required outputs have been observed in this task.

    Updates the contract's provided_outputs list to track cross-turn state.
    Only adds new entries — already-recorded outputs are not duplicated.
    """
    existing = load_contract(terminal_id)
    if not existing:
        return
    current = set(existing.get("provided_outputs", []))
    current.update(provided)
    existing["provided_outputs"] = sorted(current)
    existing["last_updated_at"] = _now_iso()
    _save_raw(terminal_id, existing)


def supersede_contract(terminal_id: str, reason: str = "semantic_drift") -> None:
    """Mark a contract as superseded (V2 auto-supersede path)."""
    existing = load_contract(terminal_id)
    if not existing:
        return
    existing["status"] = "superseded"
    existing["phase"] = "superseded"
    existing["supersede_reason"] = reason
    existing["last_updated_at"] = _now_iso()
    _save_raw(terminal_id, existing)
    _log_v2_telemetry(terminal_id, "v2_auto_supersede", {
        "task_id": existing.get("task_id", "?"),
        "reason": reason,
    })


def clear_contract(terminal_id: str) -> None:
    """Mark the contract as completed (or delete it)."""
    path = _contract_path(terminal_id)
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["status"] = "completed"
        data["phase"] = data.get("phase", "complete")
        path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    except (json.JSONDecodeError, OSError):
        pass


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def _log_v2_telemetry(terminal_id: str, event: str, fields: dict) -> None:
    """Append V2 telemetry to the dedicated log file."""
    try:
        import os
        _hooks_dir = Path(os.environ.get(
            "CLAUDE_HOOKS_DIR",
            str(Path(__file__).parent.parent),
        ))
        log_path = _hooks_dir / "logs" / "diagnostics" / "task_contract_v2_telemetry.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        import time
        entry = {
            "timestamp": time.time(),
            "gate": "task_contract_v2",
            "event": event,
            "terminal_id": terminal_id,
            **fields,
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass
