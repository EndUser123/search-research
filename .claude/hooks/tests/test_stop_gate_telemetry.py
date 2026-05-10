#!/usr/bin/env python3
"""Tests for __lib/stop_gate_telemetry.py."""

from __future__ import annotations

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
os.environ.pop("STOP_TELEMETRY", None)
from __lib.stop_gate_telemetry import log_gate_event, _LOG_FILE
log_gate_event(gate_name="test_gate", classification="quality", profile=None, decision="allow")
print("file_exists:" + str(_LOG_FILE.exists()).lower())
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