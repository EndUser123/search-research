#!/usr/bin/env python3
"""
task_contract - Terminal-scoped task contract storage for goal-fit gating.

Stores a minimal JSON contract describing what a debugging/implementation task
requires the assistant to produce (root_cause, fix, tests, verification_commands).

Location: ~/.claude/.artifacts/{terminal_id}/hook_state/task_contract.json

v1 scope: contract-style debugging/fix tasks only. Not every turn.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Use the canonical Artifacts path: ~/.claude/.artifacts/{terminal_id}/hook_state/
# This matches hook_state_manager.py and the spec requirement.

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
    return _home() / ".claude" / ".artifacts" / terminal_id / "hook_state" / _CONTRACT_FILENAME


def load_contract(terminal_id: str) -> dict[str, Any] | None:
    """Load the active task contract for this terminal.

    Returns None if no contract exists or it is not active.
    """
    path = _contract_path(terminal_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("status") != "active":
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def save_contract(
    terminal_id: str,
    *,
    task_id: str,
    description: str,
    required_outputs: list[str],
) -> dict[str, Any]:
    """Create or update a task contract atomically.

    If a contract already exists with the same task_id, last_updated_at is
    refreshed and description/required_outputs are updated. If task_id differs,
    the previous contract is replaced.

    Returns the saved contract dict.
    """
    now_iso = _now_iso()
    existing = load_contract(terminal_id)
    # Preserve task_id on re-save of same task
    if existing and existing.get("task_id") == task_id:
        task_id = existing["task_id"]

    contract = {
        "task_id": task_id,
        "description": description,
        "required_outputs": [o for o in required_outputs if o in VALID_OUTPUTS],
        "created_at": existing["created_at"] if existing else now_iso,
        "last_updated_at": now_iso,
        "status": "active",
    }
    path = _contract_path(terminal_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(contract, ensure_ascii=True, indent=2), encoding="utf-8")
    tmp.replace(path)
    return contract


def clear_contract(terminal_id: str) -> None:
    """Mark the contract as completed (or delete it)."""
    path = _contract_path(terminal_id)
    if not path.exists():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["status"] = "completed"
        path.write_text(json.dumps(data, ensure_ascii=True, indent=2), encoding="utf-8")
    except (json.JSONDecodeError, OSError):
        pass


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
