"""Artifact enforcement for Stop — verifies mechanism claims against tool-use log.

Blocks unverified runtime claims (e.g., "hooks co-fired") unless tool_use_log
shows the correct artifact was actually accessed during the current turn.

Type: type:command (subprocess gate)
Layer-aware: uses CLAIM_LAYER_MAP for precise artifact requirements

This is a STOP gate (runs at response time, not during tool execution).
It enforces that mechanism claims are backed by actual artifact access.
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data






import json
import os
import re
import sys
from pathlib import Path

_HOOKS_DIR = _hooks_dir  # from bootstrap — resolves to P:/.claude/hooks/
_STATE_DIR = _HOOKS_DIR / ".state"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from claim_layer_map import CLAIM_LAYER_MAP, get_block_message
from __lib.claim_type import _read_claim_type, _safe_id


def _get_tool_use_log_path(terminal_id: str) -> Path:
    """Return path to tool-use log file."""
    safe_id = _safe_id(terminal_id or "unknown")
    return _STATE_DIR / f"tool_use_log_{safe_id}.jsonl"


def _read_tool_use_log(terminal_id: str) -> list[dict]:
    """Read tool-use log entries for this terminal.

    Returns list of entries with 'accessed' field listing file paths.
    """
    log_path = _get_tool_use_log_path(terminal_id)
    if not log_path.exists():
        return []
    entries = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return entries


def _check_artifact_access(tool_log_entries: list[dict], artifact: str) -> bool:
    """Check if any tool log entry accessed the given artifact.

    Handles both exact filename matches and pattern matches.
    e.g., 'stop_gate_telemetry.jsonl' matches 'stop_gate_telemetry.jsonl'
          '*.jsonl' matches any .jsonl file
    """
    for entry in tool_log_entries:
        accessed = entry.get("accessed", [])
        for path in accessed:
            # Normalize path for comparison
            path_normalized = path.replace("\\", "/").lower()
            artifact_normalized = artifact.replace("\\", "/").lower()
            if artifact_normalized in path_normalized or path_normalized.endswith(artifact_normalized):
                return True
            # Handle glob patterns
            if "*" in artifact_normalized:
                import fnmatch
                if fnmatch.fnmatch(path_normalized, artifact_normalized):
                    return True
    return False


def _check_claim_keywords(response: str) -> list[str]:
    """Extract claim keywords from response that require artifact verification.

    Scans for mechanism-related claims that map to CLAIM_LAYER_MAP entries.
    """
    text_lower = response.lower()
    found_claims = []

    # Map keywords to CLAIM_LAYER_MAP keys
    keyword_map = {
        "co-fire": "co-fire",
        "co fire": "co-fire",
        "same turn": "co-fire",
        "overlap": "co-fire",
        "operating_rules_and_behavior_contract": "operating_rules_and_behavior_contract",
        "age guard": "age_guard_fired",
        "age_guard": "age_guard_fired",
        "stop gate warn": "stop_gate_warn_count",
        "gate fired": "gate_fired",
        "gate_fired": "gate_fired",
    }

    for keyword, claim_key in keyword_map.items():
        if keyword in text_lower:
            found_claims.append(claim_key)

    return found_claims


def run(data: dict) -> dict | None:
    """Main entry point — called by Stop router.

    Returns:
        None if no mechanism claims detected (allow)
        Block dict if claims require verification but artifacts not accessed
    """
    # Only run for mechanism_investigation claim type
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)

    if claim_type != "mechanism_investigation":
        return None  # Only enforce on mechanism claims

    response = data.get("response", "")
    if not response:
        return None

    # Check for mechanism claims in response
    claim_keywords = _check_claim_keywords(response)
    if not claim_keywords:
        return None  # No artifact-requiring claims

    # Read tool-use log for this terminal
    tool_log = _read_tool_use_log(terminal_id)

    # Check each claim's artifact requirements
    for claim_key in claim_keywords:
        if claim_key not in CLAIM_LAYER_MAP:
            continue

        required_artifacts = CLAIM_LAYER_MAP[claim_key].get("required", [])
        block_msg = get_block_message(claim_key)

        for artifact in required_artifacts:
            if not _check_artifact_access(tool_log, artifact):
                # Artifact not accessed — block
                return {
                    "decision": "block",
                    "reason": block_msg or f"Mechanism claim '{claim_key}' requires {artifact} but it was not accessed.",
                    "blocking_hook": "Stop_artifact_enforcement",
                }

    return None


def _resolve_scope_ids(data: dict) -> tuple[str, str]:
    """Resolve session_id and terminal_id from Stop hook data."""
    session_obj = data.get("session")
    nested_session_id = ""
    nested_terminal_id = ""
    if isinstance(session_obj, dict):
        nested_session_id = str(
            session_obj.get("id")
            or session_obj.get("session_id")
            or session_obj.get("sessionId")
            or ""
        )
        nested_terminal_id = str(
            session_obj.get("terminal_id") or session_obj.get("terminalId") or ""
        )
    session_id = (
        nested_session_id
        or data.get("session_id")
        or data.get("sessionId")
        or ""
    )
    terminal_id = (
        nested_terminal_id
        or data.get("terminal_id")
        or data.get("terminalId")
        or ""
    )
    return str(session_id), str(terminal_id)


# Subprocess entry point (called from Stop.py router)
if __name__ == "__main__":
    input_data = json.loads(sys.stdin.read())
    result = run(input_data)
    if result:
        print(json.dumps(_normalize_stdout(result)))
        sys.exit(2)  # Block
    else:
        print("{}")
        sys.exit(0)  # Allow