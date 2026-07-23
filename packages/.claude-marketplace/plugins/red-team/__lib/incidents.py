"""Incident writer for /red-team Phase 3 self-improvement.

Same append+fsync JSONL pattern as telemetry.py. An incident is a durable
record of a /red-team run misfire: miss, overfire, misroute, malformed output,
stale state, latency spike. Operator-authored (post-hoc), not auto-captured.

State path: P:/.artifacts/red-team/incidents.jsonl
Override: RED_TEAM_STATE_DIR

CLI:
  python incidents.py add --category <c> --run-id <id> --summary "..." \
      [--expected ... --observed ... --impact ... --evidence ... --root-cause ...]
  python incidents.py list [--status open] [--category routing]
  python incidents.py resolve <id>
  python incidents.py convert <id>     # mark converted_to_eval=true
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from telemetry import _next_seq, get_state_dir
from telemetry_schema import (
    VALID_INCIDENT_CATEGORIES,
    VALID_INCIDENT_STATUSES,
    validate_incident,
)


def get_incidents_path(root: Optional[Path] = None) -> Path:
    return get_state_dir(root) / "incidents.jsonl"


def _incident_id(summary: str, run_id: str, ts: int) -> str:
    raw = f"{run_id}|{summary}|{ts}"
    return "inc-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def append_incident(record: dict, state_root: Optional[Path] = None) -> None:
    errors = validate_incident(record)
    if errors:
        raise ValueError("invalid incident: " + "; ".join(errors))
    path = get_incidents_path(state_root)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def add_incident(
    category: str,
    run_id: str,
    summary: str,
    session_id: str = "",
    expected: str = "",
    observed: str = "",
    impact: str = "",
    evidence: str = "",
    candidate_root_cause: str = "",
    state_root: Optional[Path] = None,
) -> dict:
    now = time.time()
    record = {
        "ts": int(now),
        "ts_ms": int(now * 1000),
        "seq": _next_seq(),
        "incident_id": _incident_id(summary, run_id, int(now)),
        "run_id": run_id,
        "session_id": session_id,
        "category": category,
        "summary": summary,
        "expected": expected,
        "observed": observed,
        "impact": impact,
        "evidence": evidence,
        "candidate_root_cause": candidate_root_cause,
        "converted_to_eval": False,
        "status": "open",
    }
    append_incident(record, state_root)
    return record


def list_incidents(
    status: Optional[str] = None,
    category: Optional[str] = None,
    state_root: Optional[Path] = None,
) -> list[dict]:
    """Return incidents filtered by status/category. Latest-first."""
    path = get_incidents_path(state_root)
    if not path.exists():
        return []
    # Track latest status per incident_id (records are append-only; status
    # changes append new lines with the same incident_id).
    latest: dict[str, dict] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict) or "incident_id" not in obj:
                continue
            latest[obj["incident_id"]] = obj
    out = list(latest.values())
    if status:
        out = [r for r in out if r.get("status") == status]
    if category:
        out = [r for r in out if r.get("category") == category]
    out.sort(key=lambda r: r.get("ts", 0), reverse=True)
    return out


def _status_change(
    incident_id: str,
    new_status: str,
    mutator: str,
    state_root: Optional[Path] = None,
) -> dict:
    """Append a new line for the same incident_id reflecting a status change."""
    if new_status not in VALID_INCIDENT_STATUSES:
        raise ValueError(f"invalid status '{new_status}'")
    current = None
    for r in list_incidents(state_root=state_root):
        if r.get("incident_id") == incident_id:
            current = r
            break
    if current is None:
        raise KeyError(f"incident_id '{incident_id}' not found")
    now = time.time()
    record = dict(current)
    record.update({
        "ts": int(now),
        "ts_ms": int(now * 1000),
        "seq": _next_seq(),
        "status": new_status,
        "mutator": mutator,
    })
    if mutator == "convert":
        record["converted_to_eval"] = True
    append_incident(record, state_root)
    return record


def resolve(incident_id: str, state_root: Optional[Path] = None) -> dict:
    return _status_change(incident_id, "fixed", "resolve", state_root)


def mark_converted(incident_id: str, state_root: Optional[Path] = None) -> dict:
    return _status_change(incident_id, "fixed", "convert", state_root)


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(prog="incidents.py", description="/red-team incident writer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="record a new incident")
    p_add.add_argument("--category", required=True, choices=VALID_INCIDENT_CATEGORIES)
    p_add.add_argument("--run-id", required=True)
    p_add.add_argument("--session-id", default="")
    p_add.add_argument("--summary", required=True)
    p_add.add_argument("--expected", default="")
    p_add.add_argument("--observed", default="")
    p_add.add_argument("--impact", default="")
    p_add.add_argument("--evidence", default="")
    p_add.add_argument("--root-cause", default="")

    p_list = sub.add_parser("list", help="list incidents")
    p_list.add_argument("--status", default=None, choices=VALID_INCIDENT_STATUSES)
    p_list.add_argument("--category", default=None, choices=VALID_INCIDENT_CATEGORIES)

    p_resolve = sub.add_parser("resolve", help="mark incident fixed")
    p_resolve.add_argument("incident_id")

    p_convert = sub.add_parser("convert", help="mark incident converted_to_eval=true")
    p_convert.add_argument("incident_id")

    args = parser.parse_args(argv)
    if args.cmd == "add":
        rec = add_incident(
            category=args.category,
            run_id=args.run_id,
            summary=args.summary,
            session_id=args.session_id,
            expected=args.expected,
            observed=args.observed,
            impact=args.impact,
            evidence=args.evidence,
            candidate_root_cause=args.root_cause,
        )
        print(json.dumps(rec, ensure_ascii=True))
        return 0
    if args.cmd == "list":
        for rec in list_incidents(status=args.status, category=args.category):
            print(json.dumps(rec, ensure_ascii=True))
        return 0
    if args.cmd == "resolve":
        print(json.dumps(resolve(args.incident_id), ensure_ascii=True))
        return 0
    if args.cmd == "convert":
        print(json.dumps(mark_converted(args.incident_id), ensure_ascii=True))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
