"""Unit + integration tests for incidents.py + telemetry_schema.validate_incident.

Per Test Strategy Contract:
- Unit: schema validation, add/list filtering, status transitions, dedup.
- Integration: real-fs CLI subprocess (add → list → resolve).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from incidents import add_incident, list_incidents, mark_converted, resolve
from telemetry_schema import validate_incident

_HERE = Path(__file__).resolve().parent
_LIB = _HERE.parent / "__lib"


def _valid_record(**overrides):
    r = {
        "ts": int(time.time()),
        "ts_ms": int(time.time() * 1000),
        "seq": 1,
        "incident_id": "inc-abc",
        "run_id": "r1",
        "category": "routing",
        "summary": "specialist X missed",
        "status": "open",
    }
    r.update(overrides)
    return r


# --- Unit: schema validation ---

def test_validate_incident_accepts_valid():
    assert validate_incident(_valid_record()) == []


@pytest.mark.parametrize("missing", ["incident_id", "run_id", "category", "summary", "status"])
def test_validate_incident_rejects_missing_required(missing):
    r = _valid_record()
    del r[missing]
    errors = validate_incident(r)
    assert any(missing in e for e in errors)


def test_validate_incident_rejects_bad_category_and_status():
    assert validate_incident(_valid_record(category="bogus"))
    assert validate_incident(_valid_record(status="bogus"))


# --- Unit: add/list/status-changes via the API ---

def test_add_and_list_roundtrip(tmp_path):
    root = tmp_path / "state"
    rec = add_incident(category="routing", run_id="run-1", summary="missed perf issue",
                       state_root=root)
    assert rec["status"] == "open"
    assert rec["converted_to_eval"] is False
    listed = list_incidents(state_root=root)
    assert len(listed) == 1
    assert listed[0]["incident_id"] == rec["incident_id"]


def test_self_review_overlook_category_accepted(tmp_path):
    """The self-review-overlook category must be a valid incident category so
    that post-verdict overrides (user pushes back after the fact) can be
    recorded. The override pattern is the single highest-signal indicator that
    the self-review mode failed its own bias check."""
    root = tmp_path / "state"
    rec = add_incident(
        category="self-review-overlook", run_id="r1",
        summary="Orchestrator missed dead prompting-toolkit ref in ai_cli.py",
        expected="claim-refuter to catch via repo-wide grep",
        observed="claim was unverified; user surfaced it after verdict",
        evidence="grep -rn prompting_toolkit -> cc-skills-ai-api/ai_cli.py:4532",
        candidate_root_cause="scope-completeness claim skipped",
        state_root=root,
    )
    assert rec["status"] == "open"
    listed = list_incidents(category="self-review-overlook", state_root=root)
    assert len(listed) == 1
    assert listed[0]["category"] == "self-review-overlook"


def test_list_filters_by_status_and_category(tmp_path):
    root = tmp_path / "state"
    add_incident(category="routing", run_id="r1", summary="a", state_root=root)
    add_incident(category="latency", run_id="r2", summary="b", state_root=root)
    assert len(list_incidents(state_root=root)) == 2
    assert len(list_incidents(category="routing", state_root=root)) == 1
    assert len(list_incidents(status="open", state_root=root)) == 2
    assert len(list_incidents(status="fixed", state_root=root)) == 0


def test_resolve_marks_fixed_and_lists_latest(tmp_path):
    root = tmp_path / "state"
    rec = add_incident(category="routing", run_id="r1", summary="x", state_root=root)
    resolved = resolve(rec["incident_id"], state_root=root)
    assert resolved["status"] == "fixed"
    # list_incidents collapses to latest record per incident_id
    open_only = list_incidents(status="open", state_root=root)
    fixed_only = list_incidents(status="fixed", state_root=root)
    assert len(open_only) == 0
    assert len(fixed_only) == 1


def test_mark_converted_sets_flag(tmp_path):
    root = tmp_path / "state"
    rec = add_incident(category="critic-calibration", run_id="r1", summary="misclassified", state_root=root)
    converted = mark_converted(rec["incident_id"], state_root=root)
    assert converted["converted_to_eval"] is True
    assert converted["status"] == "fixed"


def test_resolve_unknown_id_raises(tmp_path):
    with pytest.raises(KeyError):
        resolve("inc-does-not-exist", state_root=tmp_path / "state")


# --- Integration: CLI subprocess ---

def test_cli_add_then_list(tmp_path):
    env = dict(os.environ, RED_TEAM_STATE_DIR=str(tmp_path / "state"))
    add = subprocess.run(
        [sys.executable, str(_LIB / "incidents.py"), "add",
         "--category", "routing", "--run-id", "r1", "--session-id", "s1",
         "--summary", "missed an auth hole",
         "--evidence", "run_dir/critic.json"],
        capture_output=True, text=True, env=env,
    )
    assert add.returncode == 0, f"stderr: {add.stderr}"
    rec = json.loads(add.stdout)
    assert rec["incident_id"].startswith("inc-")

    lst = subprocess.run(
        [sys.executable, str(_LIB / "incidents.py"), "list", "--status", "open"],
        capture_output=True, text=True, env=env,
    )
    assert lst.returncode == 0, f"stderr: {lst.stderr}"
    lines = [json.loads(l) for l in lst.stdout.splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0]["summary"] == "missed an auth hole"

    inc_path = tmp_path / "state" / "red-team" / "incidents.jsonl"
    assert inc_path.exists()
