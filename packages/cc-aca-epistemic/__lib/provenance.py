"""Provenance tracking and verification for factual claims."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from state import detect_terminal_id, read_state, write_state


def record_observation(fact: dict[str, Any], terminal_id: Optional[str] = None) -> None:
    """Record an observed fact in terminal-scoped state."""
    if terminal_id is None:
        terminal_id = detect_terminal_id()

    observations = read_state("observed_facts.json", terminal_id)
    if not isinstance(observations, dict):
        observations = {"facts": []}

    if "facts" not in observations:
        observations["facts"] = []

    if "ts" not in fact:
        fact["ts"] = datetime.now(timezone.utc).isoformat()

    observations["facts"].append(fact)
    write_state(observations, "observed_facts.json", terminal_id)


def verify_provenance(
    proposed_facts: list[dict[str, Any]], terminal_id: Optional[str] = None
) -> list[dict[str, Any]]:
    """Check which proposed facts have provenance.

    Returns list of unverified facts:
    [{
        'entity': 'Mi-Devstral',
        'field': 'quota',
        'value': '4500/5h',
        'reason': 'no provenance found'
    }]
    """
    if terminal_id is None:
        terminal_id = detect_terminal_id()

    observations = read_state("observed_facts.json", terminal_id)
    observed_list = observations.get("facts", []) if isinstance(observations, dict) else []

    unverified: list[dict[str, Any]] = []

    for proposed in proposed_facts:
        entity = proposed.get("entity", "")
        field = proposed.get("field", "")
        value = proposed.get("value", "")

        if _is_placeholder_value(value):
            continue

        found = False
        for observed in observed_list:
            if (
                observed.get("entity") == entity
                and observed.get("field") == field
                and observed.get("value") == value
            ):
                found = True
                break

        if not found:
            unverified.append({
                "entity": entity,
                "field": field,
                "value": value,
                "reason": "no provenance found",
            })

    return unverified


def record_edit_provenance(
    file_path: str,
    success: bool,
    reason: str = "",
    terminal_id: Optional[str] = None,
) -> None:
    """Record whether an edit was allowed or blocked."""
    if terminal_id is None:
        terminal_id = detect_terminal_id()

    edit_log = read_state("edit_provenance.json", terminal_id)
    if not isinstance(edit_log, dict):
        edit_log = {"edits": []}

    if "edits" not in edit_log:
        edit_log["edits"] = []

    edit_log["edits"].append({
        "file": file_path,
        "allowed": success,
        "reason": reason,
        "ts": datetime.now(timezone.utc).isoformat(),
    })

    write_state(edit_log, "edit_provenance.json", terminal_id)


def is_stale_observation(fact: dict[str, Any], max_age_seconds: int = 3600) -> bool:
    """Check if an observed fact is too old."""
    ts_str = fact.get("ts", "")
    if not ts_str:
        return True

    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - ts
        return age.total_seconds() > max_age_seconds
    except (ValueError, TypeError):
        return True


def _is_placeholder_value(value: str) -> bool:
    """Check if value is a placeholder."""
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    placeholders = {"none", "null", "unknown", "todo", "n/a", ""}
    return normalized in placeholders
