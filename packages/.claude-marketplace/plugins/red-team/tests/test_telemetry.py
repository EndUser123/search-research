"""Unit + integration tests for telemetry.py + telemetry_schema.py.

Per Test Strategy Contract:
- Unit: pure schema validation, derive_from_critic pure transform, defensive
  parsing of missing/garbled critic.json.
- Integration: real-fs write via the CLI (subprocess) — proves the boundary
  (filesystem + process) that a unit test cannot reach.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from telemetry import commit, derive_from_critic, get_telemetry_path, recent
from telemetry_schema import validate_telemetry

_HERE = Path(__file__).resolve().parent
_LIB = _HERE.parent / "__lib"


def _valid_line(**overrides):
    line = {
        "ts": int(time.time()),
        "ts_ms": int(time.time() * 1000),
        "seq": 1,
        "session_id": "s1",
        "run_id": "r1",
        "verdict": "REVISE",
        "operator_outcome": "unknown",
    }
    line.update(overrides)
    return line


# --- Unit: schema validation ---

def test_validate_telemetry_accepts_valid_line():
    assert validate_telemetry(_valid_line()) == []


@pytest.mark.parametrize("missing", ["ts", "seq", "session_id", "run_id", "verdict", "operator_outcome"])
def test_validate_telemetry_rejects_missing_required(missing):
    line = _valid_line()
    del line[missing]
    errors = validate_telemetry(line)
    assert any(missing in e for e in errors), f"expected error for missing {missing}; got {errors}"


def test_validate_telemetry_rejects_invalid_verdict():
    errors = validate_telemetry(_valid_line(verdict="MAYBE"))
    assert any("verdict" in e for e in errors)


def test_validate_telemetry_rejects_invalid_operator_outcome():
    errors = validate_telemetry(_valid_line(operator_outcome="maybe"))
    assert any("operator_outcome" in e for e in errors)


def test_validate_telemetry_rejects_non_dict():
    assert validate_telemetry("not a dict")


# --- Unit: derive_from_critic (pure transform, defensive) ---

def _write_critic(d: dict, run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    critic = run_dir / "critic.json"
    critic.write_text(json.dumps(d), encoding="utf-8")
    return critic


def test_derive_from_critic_counts_severities(tmp_path):
    run_dir = tmp_path / "run1"
    _write_critic({
        "findings": [
            {"severity": "BLOCK", "category": "auth"},
            {"severity": "BLOCK", "category": "auth"},
            {"severity": "REVISE", "category": "perf"},
            {"severity": "NIT"},
            {"severity": "BLOCK", "verification_status": "NON_REPRODUCIBLE", "category": "auth"},
        ],
        "conflicts_resolved_count": 2,
    }, run_dir)
    out = derive_from_critic(run_dir)
    assert out["counts"] == {"BLOCK": 3, "REVISE": 1, "NIT": 1, "suppressed": 1}
    assert out["critic_conflicts_resolved"] == 2
    assert out["top_categories"][0] == "auth"  # 3 occurrences


def test_derive_from_critic_missing_file_returns_parse_error(tmp_path):
    out = derive_from_critic(tmp_path / "no_such")
    assert "parse_error" in out
    assert out["counts"] == {}
    assert out["top_categories"] == []


def test_derive_from_critic_garbled_json_returns_parse_error(tmp_path):
    run_dir = tmp_path / "garbled"
    _write_critic({}, run_dir)  # create dir
    (run_dir / "critic.json").write_text("{not json", encoding="utf-8")
    out = derive_from_critic(run_dir)
    assert "parse_error" in out
    assert "unreadable" in out["parse_error"]


def test_derive_from_critic_not_a_dict(tmp_path):
    run_dir = tmp_path / "listcritic"
    run_dir.mkdir(parents=True)
    (run_dir / "critic.json").write_text("[1,2,3]", encoding="utf-8")
    out = derive_from_critic(run_dir)
    assert "parse_error" in out


# --- Unit: commit() writes a valid line via the API ---

def test_commit_writes_valid_line_with_derived_counts(tmp_path, monkeypatch):
    monkeypatch.setenv("RED_TEAM_STATE_DIR", str(tmp_path / "state"))
    # Re-import defaults by reading path through env-overridable root.
    run_dir = tmp_path / "runX"
    _write_critic({"findings": [{"severity": "BLOCK", "category": "x"}]}, run_dir)
    line = commit(run_dir=str(run_dir), session_id="s-x", verdict="REVISE",
                  state_root=tmp_path / "state")
    assert line["counts"]["BLOCK"] == 1
    assert line["verdict"] == "REVISE"
    written = recent(state_root=tmp_path / "state")
    assert len(written) == 1
    assert written[0]["run_id"] == "runX"


# --- Integration: CLI subprocess boundary ---

def test_cli_commit_writes_telemetry_jsonl(tmp_path, monkeypatch):
    monkeypatch.setenv("RED_TEAM_STATE_DIR", str(tmp_path / "state"))
    run_dir = tmp_path / "cli_run"
    _write_critic({"findings": [{"severity": "BLOCK", "category": "auth"}]}, run_dir)
    env = dict(os.environ, RED_TEAM_STATE_DIR=str(tmp_path / "state"))
    result = subprocess.run(
        [sys.executable, str(_LIB / "telemetry.py"), "commit",
         "--run-dir", str(run_dir), "--session-id", "cli-1", "--verdict", "BLOCK",
         "--dispatched", "security,logic", "--deferred", "performance",
         "--operator-outcome", "overridden"],
        capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    parsed = json.loads(result.stdout)
    assert parsed["verdict"] == "BLOCK"
    assert parsed["dispatched"] == ["security", "logic"]
    assert parsed["deferred"] == ["performance"]
    assert parsed["operator_outcome"] == "overridden"
    assert parsed["counts"]["BLOCK"] == 1

    tel_path = tmp_path / "state" / "red-team" / "telemetry.jsonl"
    assert tel_path.exists()
    lines = [json.loads(l) for l in tel_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0]["verdict"] == "BLOCK"
