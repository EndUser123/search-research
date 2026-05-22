#!/usr/bin/env python3
"""Tests for __lib/stop_gate_telemetry.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent  # P:/.claude/hooks — where __lib/ lives


def _run_script(script_body: str, tmp_path: Path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    """Write script to a temp .py file and run it. Avoids repr-path corruption on Windows."""
    work_dir = str(tmp_path.resolve())
    # Double-backslash for Python string literals
    escaped_dir = work_dir.replace("\\", "\\\\")
    script = script_body.replace("{TMP_DIR}", escaped_dir)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=work_dir, encoding="utf-8"
    ) as f:
        f.write(script)
        script_file = f.name
    try:
        env = {**os.environ}
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            [sys.executable, script_file],
            capture_output=True,
            text=True,
            cwd=work_dir,
            env=env,
        )
    finally:
        try:
            os.unlink(script_file)
        except OSError:
            pass


class TestStopGateTelemetry:
    """Verify telemetry logging, fail-silent behavior, and test utilities."""

    def test_telemetry_disabled_by_default_writes_nothing(self, tmp_path):
        """When STOP_TELEMETRY is unset/0, no file is written."""
        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
import os
from pathlib import Path
import __lib.stop_gate_telemetry as tel
tel._STATE_DIR = Path("{TMP_DIR}")
tel._LOG_FILE = Path("{TMP_DIR}") / "gate_telemetry.jsonl"
os.environ.pop("STOP_TELEMETRY", None)
tel.log_gate_event(gate_name="test_gate", classification="quality", profile=None, decision="allow")
print("file_exists:" + str(tel._LOG_FILE.exists()).lower())
""".replace("{HOOKS_DIR}", repr(str(HOOKS_DIR)))

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            env={**os.environ, "STOP_TELEMETRY": "0"},
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "file_exists:false" in result.stdout

    def test_telemetry_enabled_writes_jsonl(self, tmp_path):
        """When STOP_TELEMETRY=1, log_gate_event writes a JSON line."""
        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
import json
import os
from pathlib import Path
import __lib.stop_gate_telemetry as tel
tel._STATE_DIR = Path("{TMP_DIR}")
tel._LOG_FILE = Path("{TMP_DIR}") / "gate_telemetry.jsonl"
tel._TELEMETRY_ENABLED = True
tel.log_gate_event(
    gate_name="semantic_critic",
    classification="quality",
    profile="software_rca",
    decision="warn",
    session_id="sess-test-1",
    terminal_id="term-abc",
)
records = []
lf = tel._LOG_FILE
if lf.exists():
    with open(lf) as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
print("count:" + str(len(records)))
if records:
    r = records[0]
    print("gate:" + r.get("gate",""))
    print("profile:" + str(r.get("profile","")))
""".replace("{HOOKS_DIR}", repr(str(HOOKS_DIR)))

        result = _run_script(script, tmp_path, extra_env={"STOP_TELEMETRY": "1"})
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "count:1" in result.stdout, f"stdout: {result.stdout!r}"
        assert "gate:semantic_critic" in result.stdout
        assert "profile:software_rca" in result.stdout

    def test_telemetry_multiple_events_accumulate(self, tmp_path):
        """Multiple log_gate_event calls append to the same file."""
        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
import json
import os
from pathlib import Path
import __lib.stop_gate_telemetry as tel
tel._STATE_DIR = Path("{TMP_DIR}")
tel._LOG_FILE = Path("{TMP_DIR}") / "gate_telemetry.jsonl"
tel._TELEMETRY_ENABLED = True
tel.log_gate_event(gate_name="gate_a", classification="policy", profile=None, decision="allow")
tel.log_gate_event(gate_name="gate_b", classification="quality", profile="general_diagnostic", decision="warn")
tel.log_gate_event(gate_name="gate_c", classification="policy", profile=None, decision="block")
lf = tel._LOG_FILE
records = []
if lf.exists():
    with open(lf) as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
print("count:" + str(len(records)))
print("gate_a:" + str(records[0]["gate"]))
print("gate_b:" + str(records[1]["gate"]) + "|profile:" + str(records[1]["profile"]))
print("gate_c:" + str(records[2]["gate"]) + "|decision:" + str(records[2]["decision"]))
""".replace("{HOOKS_DIR}", repr(str(HOOKS_DIR)))

        result = _run_script(script, tmp_path, extra_env={"STOP_TELEMETRY": "1"})
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "count:3" in result.stdout
        assert "profile:general_diagnostic" in result.stdout
        assert "decision:block" in result.stdout

    def test_telemetry_extra_fields_written(self, tmp_path):
        """Extra dict fields are included in the record."""
        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
import json
from pathlib import Path
import __lib.stop_gate_telemetry as tel
tel._STATE_DIR = Path("{TMP_DIR}")
tel._LOG_FILE = Path("{TMP_DIR}") / "gate_telemetry.jsonl"
tel._TELEMETRY_ENABLED = True
extra_arg = dict(skill="gto", missing_step="evidence")
tel.log_gate_event(
    gate_name="phase0_depends_on_skills",
    classification="quality",
    profile=None,
    decision="block",
    extra=extra_arg,
)
lf = tel._LOG_FILE
records = []
if lf.exists():
    with open(lf) as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
empty_dict = dict()
print("count:" + str(len(records)))
print("skill:" + str(records[0].get("extra", empty_dict).get("skill", "")))
""".replace("{HOOKS_DIR}", repr(str(HOOKS_DIR)))

        result = _run_script(script, tmp_path, extra_env={"STOP_TELEMETRY": "1"})
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "count:1" in result.stdout
        assert "skill:gto" in result.stdout

    def test_telemetry_fails_silent_on_file_error(self, tmp_path):
        """If the log file is unreadable, log_gate_event does not raise."""
        log_file = tmp_path / "gate_telemetry.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text("")
        log_file.chmod(0o000)

        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
import os
from pathlib import Path
import __lib.stop_gate_telemetry as tel
tel._STATE_DIR = Path("{TMP_DIR}")
tel._LOG_FILE = Path("{TMP_DIR}") / "gate_telemetry.jsonl"
tel._TELEMETRY_ENABLED = True
try:
    tel.log_gate_event(gate_name="test_gate", classification="quality", profile=None, decision="allow")
    print("ok")
except Exception as e:
    print("error:" + str(e))
""".replace("{HOOKS_DIR}", repr(str(HOOKS_DIR)))

        result = _run_script(script, tmp_path, extra_env={"STOP_TELEMETRY": "1"})
        log_file.chmod(0o644)  # restore
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "ok" in result.stdout, f"Should not raise: {result.stdout}"

    def test_clear_test_telemetry_removes_file(self, tmp_path):
        """clear_test_telemetry deletes the log file."""
        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
import os
from pathlib import Path
import __lib.stop_gate_telemetry as tel
tel._STATE_DIR = Path("{TMP_DIR}")
tel._LOG_FILE = Path("{TMP_DIR}") / "gate_telemetry.jsonl"
tel._TELEMETRY_ENABLED = True
tel.log_gate_event(gate_name="test_gate", classification="quality", profile=None, decision="allow")
lf = tel._LOG_FILE
print("exists:" + str(lf.exists()).lower())
tel.clear_test_telemetry()
print("cleared:" + str(lf.exists()).lower())
""".replace("{HOOKS_DIR}", repr(str(HOOKS_DIR)))

        result = _run_script(script, tmp_path, extra_env={"STOP_TELEMETRY": "1"})
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "exists:true" in result.stdout
        assert "cleared:false" in result.stdout

    def test_telemetry_visible_field_populated(self, tmp_path):
        """visible field is written for all gate outcomes (block/warn/allow)."""
        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
import json
from pathlib import Path
import __lib.stop_gate_telemetry as tel
tel._STATE_DIR = Path("{TMP_DIR}")
tel._LOG_FILE = Path("{TMP_DIR}") / "gate_telemetry.jsonl"
tel._TELEMETRY_ENABLED = True

# Block → visible=True
tel.log_gate_event(gate_name="gate_block", classification="quality", profile=None,
    decision="block", visible=True)
# Warn → visible=True (has systemMessage)
tel.log_gate_event(gate_name="gate_warn", classification="quality", profile=None,
    decision="warn", visible=True)
# Skip/suppressed → visible=False
tel.log_gate_event(gate_name="gate_skip", classification="quality", profile=None,
    decision="allow", visible=False, skip_reason="not_applicable")

lf = tel._LOG_FILE
records = []
if lf.exists():
    with open(lf) as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))

print("count:" + str(len(records)))
for r in records:
    print("gate:" + r.get("gate") + "|visible:" + str(r.get("visible")))
""".replace("{HOOKS_DIR}", repr(str(HOOKS_DIR)))

        result = _run_script(script, tmp_path, extra_env={"STOP_TELEMETRY": "1"})
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "count:3" in result.stdout
        assert "gate:gate_block|visible:True" in result.stdout
        assert "gate:gate_warn|visible:True" in result.stdout
        assert "gate:gate_skip|visible:False" in result.stdout


class TestLogNonCriticalAdvisoryStrategyFields:
    """Verify _log_non_critical_advisory emits retry-causality fields when strategy is passed."""

    def test_strategy_fields_emitted_when_strategy_provided(self, tmp_path, monkeypatch):
        """When strategy object is passed, entry includes strategy/reason_code/triggering_codes/repeat_key."""
        import Stop

        # _log_non_critical_advisory writes to HOOKS_DIR / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        # so the actual log file is nested one level deeper than tmp_path itself
        monkeypatch.setattr(Stop, "HOOKS_DIR", tmp_path)

        from epistemic_validator import EpistemicIssue, RetryStrategy

        issues = [
            EpistemicIssue(section="[FACT]", bullet_index=0, type="unsupported_fact", message="no citation"),
            EpistemicIssue(section="__GLOBAL__", bullet_index=-1, type="format", message="missing section"),
        ]

        strategy = RetryStrategy(
            strategy="retry_with_guidance",
            reason_code="UNSUPPORTED_FACT_LOCAL_SUMMARY",
            summary="summary",
            max_retries=3,
            escalate_external_judge=False,
            repeat_key="analytical:mode1",
            triggering_codes=("unsupported_fact",),
        )

        data = {
            "session_id": "sess-abc",
            "terminal_id": "term-xyz",
            "response": "x" * 200,
        }

        Stop._log_non_critical_advisory(
            data, "unsupported_fact_retry", issues,
            strategy=strategy, retry_count=2,
        )

        # Correct path: HOOKS_DIR / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        log_file = tmp_path / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        assert log_file.exists(), "log file was not written"
        records = []
        with open(log_file) as fh:
            for line in fh:
                if line.strip():
                    records.append(json.loads(line))

        assert len(records) == 1
        r = records[0]
        assert r["advisory_type"] == "unsupported_fact_retry"
        assert r["strategy"] == "retry_with_guidance"
        assert r["reason_code"] == "UNSUPPORTED_FACT_LOCAL_SUMMARY"
        assert r["triggering_codes"] in (("unsupported_fact",), ["unsupported_fact"])
        assert r["repeat_key"] == "analytical:mode1"
        assert r["retry_count"] == 2

    def test_no_strategy_fields_when_strategy_not_provided(self, tmp_path, monkeypatch):
        """When strategy is None, no strategy-related fields are written."""
        import Stop
        # Correct path: HOOKS_DIR / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        monkeypatch.setattr(Stop, "HOOKS_DIR", tmp_path)

        from epistemic_validator import EpistemicIssue

        issues = [
            EpistemicIssue(section="[FACT]", bullet_index=0, type="unsupported_fact", message="no citation"),
        ]

        data = {
            "session_id": "sess-abc",
            "terminal_id": "term-xyz",
            "response": "x" * 200,
        }

        Stop._log_non_critical_advisory(data, "unsupported_fact_retry", issues)

        log_file = tmp_path / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        assert log_file.exists()
        records = []
        with open(log_file) as fh:
            for line in fh:
                if line.strip():
                    records.append(json.loads(line))

        assert len(records) == 1
        r = records[0]
        assert "strategy" not in r
        assert "reason_code" not in r
        assert "triggering_codes" not in r
        assert "retry_count" not in r

    def test_retry_count_emitted_without_strategy(self, tmp_path, monkeypatch):
        """retry_count is written even when strategy is None (passed separately)."""
        import Stop
        # Correct path: HOOKS_DIR / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        monkeypatch.setattr(Stop, "HOOKS_DIR", tmp_path)

        from epistemic_validator import EpistemicIssue

        issues = [
            EpistemicIssue(section="[FACT]", bullet_index=0, type="unsupported_fact", message="no citation"),
        ]

        data = {
            "session_id": "sess-abc",
            "terminal_id": "term-xyz",
            "response": "x" * 200,
        }

        Stop._log_non_critical_advisory(data, "unsupported_fact_retry", issues, retry_count=1)

        log_file = tmp_path / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        assert log_file.exists()
        records = []
        with open(log_file) as fh:
            for line in fh:
                if line.strip():
                    records.append(json.loads(line))

        assert len(records) == 1
        r = records[0]
        assert r["retry_count"] == 1
