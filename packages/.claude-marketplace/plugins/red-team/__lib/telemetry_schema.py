"""Schema validators for /red-team Phase 3 self-improvement layer.

Pure logic, no I/O — sibling to findings_schema.py. Two record types:

- Telemetry line: one per /red-team run, appended to telemetry.jsonl.
- Incident record: one per noted run misfire, appended to incidents.jsonl.

Both reuse the existing findings vocabulary (BLOCK|REVISE|NIT severity,
PROCEED|REVISE|BLOCK verdict) — no new ontology.
"""
from __future__ import annotations
from typing import Any

REQUIRED_TELEMETRY_FIELDS = (
    "ts", "ts_ms", "seq", "session_id", "run_id", "verdict", "operator_outcome",
)
VALID_VERDICTS = ("PROCEED", "REVISE", "BLOCK")
VALID_OPERATOR_OUTCOMES = ("accepted", "partial", "overridden", "unknown")

REQUIRED_INCIDENT_FIELDS = (
    "ts", "ts_ms", "seq", "incident_id", "run_id", "category", "summary", "status",
)
VALID_INCIDENT_CATEGORIES = (
    "routing", "formatting", "critic-calibration",
    "specialist-miss", "stale-state", "latency", "other",
    # self-review-overlook: the orchestrator was reviewing its own prior
    # implementation output and missed a real defect (scope, dead code,
    # claim mismatch). Captured when the user pushes back and a re-run
    # surfaces the missed defect. Becomes a high-priority incident because
    # the same context that drafted the code cannot be trusted to re-review
    # it without external pressure.
    "self-review-overlook",
    # specialist-honest-fail: the specialist honestly reported WRITE_FAILED
    # instead of fake-reporting a path. Distinct from specialist-miss (where
    # the specialist reported a path but no file was written) because the
    # specialist's reason is preserved and the failure mode is "write failed"
    # not "specialist skipped the write". Pairs with FM-4 step 1's incident
    # logging in commands/red-team.md.
    "specialist-honest-fail",
)
VALID_INCIDENT_STATUSES = ("open", "triaged", "fixed", "rejected")


def validate_telemetry(line: Any) -> list[str]:
    """Return validation error strings; empty list = valid."""
    if not isinstance(line, dict):
        return ["telemetry line is not a dict"]
    errors: list[str] = []
    for field in REQUIRED_TELEMETRY_FIELDS:
        if field not in line:
            errors.append(f"telemetry missing required field '{field}'")
    verdict = line.get("verdict")
    if verdict is not None and verdict not in VALID_VERDICTS:
        errors.append(f"telemetry verdict '{verdict}' not in {VALID_VERDICTS}")
    outcome = line.get("operator_outcome")
    if outcome is not None and outcome not in VALID_OPERATOR_OUTCOMES:
        errors.append(f"telemetry operator_outcome '{outcome}' not in {VALID_OPERATOR_OUTCOMES}")
    counts = line.get("counts")
    if counts is not None and not isinstance(counts, dict):
        errors.append("telemetry counts must be a dict")
    return errors


def validate_incident(record: Any) -> list[str]:
    """Return validation error strings; empty list = valid."""
    if not isinstance(record, dict):
        return ["incident record is not a dict"]
    errors: list[str] = []
    for field in REQUIRED_INCIDENT_FIELDS:
        if field not in record:
            errors.append(f"incident missing required field '{field}'")
    cat = record.get("category")
    if cat is not None and cat not in VALID_INCIDENT_CATEGORIES:
        errors.append(f"incident category '{cat}' not in {VALID_INCIDENT_CATEGORIES}")
    status = record.get("status")
    if status is not None and status not in VALID_INCIDENT_STATUSES:
        errors.append(f"incident status '{status}' not in {VALID_INCIDENT_STATUSES}")
    return errors
