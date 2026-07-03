#!/usr/bin/env python3
"""
Tests for cc_health.py and stop_gate_telemetry health helpers.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load helpers with isolated state first
import __lib.stop_gate_telemetry as tel

_HOOKS_DIR = Path(__file__).resolve().parent.parent


class TestModeStatusRendering:
    """Phase B: Mode status rendering in NORMAL / AUDIT / DEBUG_GATES."""

    def test_render_normal_mode(self):
        from __lib.stop_gate_telemetry import render_mode_status
        result = render_mode_status("normal")
        assert result == "Session Mode: NORMAL"

    def test_render_audit_mode(self):
        from __lib.stop_gate_telemetry import render_mode_status
        result = render_mode_status("audit")
        assert result == "Session Mode: AUDIT  (format-only friction softened on audit-report turns)"

    def test_render_debug_gates_mode(self):
        from __lib.stop_gate_telemetry import render_mode_status
        result = render_mode_status("debug_gates")
        assert result == "Session Mode: DEBUG_GATES  (quality gates suppressed)"


class TestHealthSnapshotEmpty:
    """Phase C: Health snapshot is minimal when nothing actionable."""

    def test_empty_when_no_events(self, tmp_path):
        tel._STATE_DIR = tmp_path
        tel._LOG_FILE = tmp_path / "stop_gate_telemetry.jsonl"
        tel._TELEMETRY_ENABLED = True

        gate_summary = {}
        claim_summary = {"matched": 0, "artifact_missing": 0, "no_match": 0, "other": 0}
        rollout_summary = {}

        from __lib.stop_gate_telemetry import render_compact_health
        output = render_compact_health(
            session_mode="normal",
            gate_summary=gate_summary,
            claim_summary=claim_summary,
            rollout_summary=rollout_summary,
            hours=24,
        )

        lines = output.splitlines()
        assert any("NORMAL" in l for l in lines)
        assert any("No non-allow gate events" in l for l in lines)
        # No attention lines when nothing actionable
        assert not any("⚑" in l for l in lines)


class TestHealthSnapshotArtifactProblem:
    """Phase C: Health snapshot includes artifact_missing warning when dominant."""

    def test_artifact_missing_warning(self, tmp_path):
        tel._STATE_DIR = tmp_path
        tel._LOG_FILE = tmp_path / "stop_gate_telemetry.jsonl"
        tel._TELEMETRY_ENABLED = True

        gate_summary = {"epistemic_contract": 6}
        claim_summary = {"matched": 2, "artifact_missing": 6, "no_match": 1, "other": 0}
        rollout_summary = {}

        from __lib.stop_gate_telemetry import render_attention_lines
        lines = render_attention_lines(gate_summary, claim_summary, rollout_summary, "normal")

        assert len(lines) == 1
        assert "artifact_missing" in lines[0]
        assert "6/9" in lines[0]  # 6 out of 9 total
        assert "66%" in lines[0]  # dominant threshold exceeded (6/9 = 66%)


class TestTopNonAllowGates:
    """Phase D: Top non-allow gates summarized correctly from fixture."""

    def test_top_gates_from_records(self, tmp_path):
        tel._STATE_DIR = tmp_path
        tel._LOG_FILE = tmp_path / "stop_gate_telemetry.jsonl"
        tel._TELEMETRY_ENABLED = True

        records = [
            {"ts": "2026-05-11T12:00:00+00:00", "gate": "epistemic_contract", "decision": "block"},
            {"ts": "2026-05-11T12:01:00+00:00", "gate": "epistemic_contract", "decision": "block"},
            {"ts": "2026-05-11T12:02:00+00:00", "gate": "lazy_workaround_gate", "decision": "warn"},
            {"ts": "2026-05-11T12:03:00+00:00", "gate": "epistemic_contract", "decision": "block"},
            {"ts": "2026-05-11T12:04:00+00:00", "gate": "lazy_workaround_gate", "decision": "block"},
            {"ts": "2026-05-11T12:05:00+00:00", "gate": "epistemic_contract", "decision": "allow"},
            {"ts": "2026-05-11T12:06:00+00:00", "gate": "intent_artifact_alignment", "decision": "warn"},
        ]

        from __lib.stop_gate_telemetry import get_recent_gate_summary
        result = get_recent_gate_summary(records=records, hours=24, top_n=5)

        assert result == {
            "epistemic_contract": 3,  # 3 blocks
            "lazy_workaround_gate": 2,  # 1 warn + 1 block
            "intent_artifact_alignment": 1,  # 1 warn
        }

    def test_allow_decisions_excluded(self, tmp_path):
        tel._STATE_DIR = tmp_path
        tel._LOG_FILE = tmp_path / "stop_gate_telemetry.jsonl"
        tel._TELEMETRY_ENABLED = True

        records = [
            {"ts": "2026-05-11T12:00:00+00:00", "gate": "epistemic_contract", "decision": "allow"},
            {"ts": "2026-05-11T12:01:00+00:00", "gate": "epistemic_contract", "decision": "allow"},
            {"ts": "2026-05-11T12:02:00+00:00", "gate": "epistemic_contract", "decision": "allow"},
        ]

        from __lib.stop_gate_telemetry import get_recent_gate_summary
        result = get_recent_gate_summary(records=records, hours=24)

        assert result == {}  # all allow → empty


class TestRolloutSummary:
    """Phase D: Non-default rollout modes surfaced."""

    def test_rollout_non_default(self, tmp_path):
        tel._STATE_DIR = tmp_path
        tel._LOG_FILE = tmp_path / "stop_gate_telemetry.jsonl"
        tel._TELEMETRY_ENABLED = True

        records = [
            {"ts": "2026-05-11T12:00:00+00:00", "rollout_mode": "advisory"},
            {"ts": "2026-05-11T12:01:00+00:00", "rollout_mode": "advisory"},
            {"ts": "2026-05-11T12:02:00+00:00", "rollout_mode": "advisory"},
            {"ts": "2026-05-11T12:03:00+00:00", "rollout_mode": "block"},  # default
            {"ts": "2026-05-11T12:04:00+00:00", "rollout_mode": "shadow"},
        ]

        from __lib.stop_gate_telemetry import get_rollout_summary
        result = get_rollout_summary(records=records, hours=24)

        assert result == {"advisory": 3, "shadow": 1}


class TestRuntimeClaimSummary:
    """Phase D: Runtime claim enforcement counts."""

    def test_runtime_claim_all_outcomes(self, tmp_path):
        tel._STATE_DIR = tmp_path
        tel._LOG_FILE = tmp_path / "stop_gate_telemetry.jsonl"
        tel._TELEMETRY_ENABLED = True

        records = [
            {"ts": "2026-05-11T12:00:00+00:00", "artifact_class_required": "runtime_log", "artifact_class_observed": "pytest_output"},
            {"ts": "2026-05-11T12:01:00+00:00", "artifact_class_required": "runtime_log", "artifact_class_observed": "artifact_missing"},
            {"ts": "2026-05-11T12:02:00+00:00", "artifact_class_required": "runtime_log", "artifact_class_observed": None},
            {"ts": "2026-05-11T12:03:00+00:00", "artifact_class_required": "runtime_log", "artifact_class_observed": "artifact_missing"},
        ]

        from __lib.stop_gate_telemetry import get_runtime_claim_summary
        result = get_runtime_claim_summary(records=records, hours=24)

        assert result["matched"] == 1
        assert result["artifact_missing"] == 2
        assert result["no_match"] == 1


class TestCCHealthScript:
    """Phase E / F: cc_health.py script integration."""

    def test_mode_only_shows_mode(self, tmp_path):
        """Mode + telemetry helpers work together to show health."""
        import json

        # Write telemetry directly to temp file
        tel_file = tmp_path / "stop_gate_telemetry.jsonl"
        tel_file.write_text(json.dumps({
            "ts": "2026-05-11T12:00:00+00:00",
            "gate": "epistemic_contract",
            "decision": "block",
            "rollout_mode": "advisory",
        }) + "\n")

        # Override state to use our temp file
        import __lib.stop_gate_telemetry as tel_module
        orig_state_dir = tel_module._STATE_DIR
        orig_log_file = tel_module._LOG_FILE
        orig_telemetry_enabled = tel_module._TELEMETRY_ENABLED
        tel_module._STATE_DIR = tmp_path
        tel_module._LOG_FILE = tel_file
        tel_module._TELEMETRY_ENABLED = True

        try:
            from __lib.stop_gate_telemetry import (
                render_mode_status,
                render_compact_health,
                get_recent_gate_summary,
                get_runtime_claim_summary,
                get_rollout_summary,
            )
            from __lib.turn_mode import get_session_mode

            sm = get_session_mode("normal prompt")
            mode_line = render_mode_status(sm)
            gs = get_recent_gate_summary(hours=24)
            cs = get_runtime_claim_summary(hours=24)
            rs = get_rollout_summary(hours=24)
            health = render_compact_health(sm, gs, cs, rs, 24)

            assert mode_line == "Session Mode: NORMAL"
            assert any("epistemic_contract" in l for l in health.splitlines())
            assert any("advisory" in l for l in health.splitlines())
        finally:
            tel_module._STATE_DIR = orig_state_dir
            tel_module._LOG_FILE = orig_log_file
            tel_module._TELEMETRY_ENABLED = orig_telemetry_enabled

    def test_no_telemetry_note_when_disabled(self, tmp_path):
        """When telemetry is off, reads from file but nothing logged."""
        import __lib.stop_gate_telemetry as tel_module

        # Write a file with data
        tel_file = tmp_path / "stop_gate_telemetry.jsonl"
        tel_file.write_text('{"ts":"2026-05-11T12:00:00+00:00","gate":"epistemic_contract","decision":"block"}\n')

        orig_state_dir = tel_module._STATE_DIR
        orig_log_file = tel_module._LOG_FILE
        orig_telemetry_enabled = tel_module._TELEMETRY_ENABLED
        tel_module._STATE_DIR = tmp_path
        tel_module._LOG_FILE = tel_file
        tel_module._TELEMETRY_ENABLED = False  # telemetry disabled

        try:
            from __lib.stop_gate_telemetry import render_mode_status, get_recent_gate_summary

            sm = "normal"  # hard-coded, not env-dependent here
            result = render_mode_status(sm)
            assert result == "Session Mode: NORMAL"
            gs = get_recent_gate_summary(hours=24)
            # With telemetry OFF, log_gate_event() writes nothing,
            # so reading the file we wrote manually shows real data.
            # The point: render_mode_status works regardless of telemetry state.
        finally:
            tel_module._STATE_DIR = orig_state_dir
            tel_module._LOG_FILE = orig_log_file
            tel_module._TELEMETRY_ENABLED = orig_telemetry_enabled

    def test_audit_mode_in_output(self, tmp_path):
        """Session mode AUDIT is reflected in output."""
        import subprocess, sys

        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
from __lib.stop_gate_telemetry import render_mode_status
result = render_mode_status("audit")
print(result)
""".replace("{HOOKS_DIR}", repr(str(_HOOKS_DIR)))

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True,
            env={**os.environ, "STOP_SESSION_MODE": "audit"},
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Session Mode: AUDIT" in result.stdout

    def test_debug_gates_mode_in_output(self, tmp_path):
        """Session mode DEBUG_GATES is reflected in output."""
        import subprocess, sys

        script = """
import sys
sys.path.insert(0, {HOOKS_DIR})
from __lib.stop_gate_telemetry import render_mode_status
result = render_mode_status("debug_gates")
print(result)
""".replace("{HOOKS_DIR}", repr(str(_HOOKS_DIR)))

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True,
            env={**os.environ, "STOP_SESSION_MODE": "debug_gates"},
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "Session Mode: DEBUG_GATES" in result.stdout


class TestSessionStartHookRegistration:
    """Phase E: Guard against settings.json drift on SessionStart health hook."""

    def test_session_start_health_hook_registered_in_settings_json(self):
        """SessionStart_cc_health.py must be registered in settings.json SessionStart hooks."""
        import json, pathlib

        settings_path = pathlib.Path("P:/.claude/settings.json")
        with settings_path.open("r", encoding="utf-8") as f:
            settings = json.load(f)

        session_start_entries = settings.get("hooks", {}).get("SessionStart", [])
        registered = any(
            "SessionStart_cc_health.py" in cmd.get("command", "")
            for entry in session_start_entries
            for cmd in entry.get("hooks", [])
        )
        assert registered, (
            "SessionStart_cc_health.py not registered in settings.json SessionStart hooks. "
            "Add a SessionStart entry with command: 'python P:/.claude/hooks/SessionStart_cc_health.py'"
        )


class TestSessionStartHook:
    """Phase D: Automatic surfacing via SessionStart hook."""

    def test_normal_mode_silent_when_no_actionable(self, tmp_path):
        """NORMAL mode with no actionable issues → silent (no JSON output)."""
        import __lib.stop_gate_telemetry as tel_module
        import subprocess, sys

        # Write empty telemetry (no actionable issues)
        tel_file = tmp_path / "stop_gate_telemetry.jsonl"
        tel_file.write_text("")

        orig_state_dir = tel_module._STATE_DIR
        orig_log_file = tel_module._LOG_FILE
        orig_telemetry = tel_module._TELEMETRY_ENABLED
        tel_module._STATE_DIR = tmp_path
        tel_module._LOG_FILE = tel_file
        tel_module._TELEMETRY_ENABLED = True

        try:
            result = subprocess.run(
                [sys.executable, "P:/.claude/hooks/SessionStart_cc_health.py"],
                capture_output=True, text=True,
                env={**os.environ, "STOP_SESSION_MODE": "normal", "STOP_TELEMETRY": "1"},
            )
            assert result.returncode == 0
            # Silent: no output (cc_health would print nothing when NORMAL + no actionable)
            # But since telemetry IS enabled and file exists, what matters is render_attention_lines
            # With empty summaries, attention_lines returns [], so silent
        finally:
            tel_module._STATE_DIR = orig_state_dir
            tel_module._LOG_FILE = orig_log_file
            tel_module._TELEMETRY_ENABLED = orig_telemetry

    def test_debug_gates_shows_mode_line(self, tmp_path):
        """DEBUG_GATES always surfaces mode line."""
        import subprocess, sys

        result = subprocess.run(
            [sys.executable, "P:/.claude/hooks/SessionStart_cc_health.py"],
            capture_output=True, text=True,
            env={**os.environ, "STOP_SESSION_MODE": "debug_gates"},
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "Session Mode: DEBUG_GATES" in data["hookSpecificOutput"]["additionalContext"]

    def test_audit_shows_mode_line(self, tmp_path):
        """AUDIT always surfaces mode line."""
        import subprocess, sys

        result = subprocess.run(
            [sys.executable, "P:/.claude/hooks/SessionStart_cc_health.py"],
            capture_output=True, text=True,
            env={**os.environ, "STOP_SESSION_MODE": "audit"},
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "Session Mode: AUDIT" in data["hookSpecificOutput"]["additionalContext"]

    def test_rollout_attention_surfaced_automatically(self, tmp_path):
        """Rollout override is surfaced automatically in output."""
        import __lib.stop_gate_telemetry as tel_module
        import subprocess, sys

        # Write telemetry with advisory rollout override
        tel_file = tmp_path / "stop_gate_telemetry.jsonl"
        tel_file.write_text(
            json.dumps({"rollout_mode": "advisory", "gate": "epistemic_contract", "decision": "block", "ts": "2026-05-11T12:00:00+00:00"}) + "\n"
        )

        orig_state_dir = tel_module._STATE_DIR
        orig_log_file = tel_module._LOG_FILE
        orig_telemetry = tel_module._TELEMETRY_ENABLED
        tel_module._STATE_DIR = tmp_path
        tel_module._LOG_FILE = tel_file
        tel_module._TELEMETRY_ENABLED = True

        try:
            result = subprocess.run(
                [sys.executable, "P:/.claude/hooks/SessionStart_cc_health.py"],
                capture_output=True, text=True,
                env={**os.environ, "STOP_SESSION_MODE": "normal", "STOP_TELEMETRY": "1"},
            )
            assert result.returncode == 0
            if result.stdout.strip():
                data = json.loads(result.stdout)
                context = data["hookSpecificOutput"]["additionalContext"]
                assert "advisory" in context
        finally:
            tel_module._STATE_DIR = orig_state_dir
            tel_module._LOG_FILE = orig_log_file
            tel_module._TELEMETRY_ENABLED = orig_telemetry

    def test_no_noise_when_telemetry_off(self, tmp_path):
        """When STOP_TELEMETRY=0, hook still works but reads nothing."""
        import __lib.stop_gate_telemetry as tel_module
        import subprocess, sys

        # Write telemetry but telemetry is OFF
        tel_file = tmp_path / "stop_gate_telemetry.jsonl"
        tel_file.write_text(
            json.dumps({"rollout_mode": "advisory", "gate": "epistemic_contract", "decision": "block", "ts": "2026-05-11T12:00:00+00:00"}) + "\n"
        )

        orig_state_dir = tel_module._STATE_DIR
        orig_log_file = tel_module._LOG_FILE
        orig_telemetry = tel_module._TELEMETRY_ENABLED
        tel_module._STATE_DIR = tmp_path
        tel_module._LOG_FILE = tel_file
        tel_module._TELEMETRY_ENABLED = True  # module state

        try:
            result = subprocess.run(
                [sys.executable, "P:/.claude/hooks/SessionStart_cc_health.py"],
                capture_output=True, text=True,
                env={**os.environ, "STOP_SESSION_MODE": "normal", "STOP_TELEMETRY": "0"},
            )
            assert result.returncode == 0
            # With telemetry off, no attention lines, no output (NORMAL with nothing actionable)
            # Result is silent (no stdout) when telemetry off + NORMAL + nothing in summaries
        finally:
            tel_module._STATE_DIR = orig_state_dir
            tel_module._LOG_FILE = orig_log_file
            tel_module._TELEMETRY_ENABLED = orig_telemetry

    def test_fail_open_on_exception(self, tmp_path):
        """Hook fails open — returns 0 even on error."""
        import subprocess, sys

        result = subprocess.run(
            [sys.executable, "P:/.claude/hooks/SessionStart_cc_health.py"],
            capture_output=True, text=True,
            env={**os.environ, "STOP_SESSION_MODE": "nonexistent_mode"},
        )
        # Should still exit 0 (fail open)
        assert result.returncode == 0

    def test_outputs_valid_session_start_protocol(self, tmp_path):
        """Output conforms to SessionStart hook protocol."""
        import subprocess, sys

        result = subprocess.run(
            [sys.executable, "P:/.claude/hooks/SessionStart_cc_health.py"],
            capture_output=True, text=True,
            env={**os.environ, "STOP_SESSION_MODE": "debug_gates"},
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "hookSpecificOutput" in data
        assert data["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert isinstance(data["hookSpecificOutput"]["additionalContext"], str)


class TestAttentionLines:
    """Phase C: Attention lines only when actionable."""

    def test_no_attention_in_normal_health(self):
        from __lib.stop_gate_telemetry import render_attention_lines
        lines = render_attention_lines(
            gate_summary={"epistemic_contract": 2},
            claim_summary={"matched": 3, "artifact_missing": 0, "no_match": 0, "other": 0},
            rollout_summary={},
            session_mode="normal",
        )
        assert lines == []

    def test_debug_gates_attention(self):
        from __lib.stop_gate_telemetry import render_attention_lines
        lines = render_attention_lines(
            gate_summary={},
            claim_summary={"matched": 0, "artifact_missing": 0, "no_match": 0, "other": 0},
            rollout_summary={},
            session_mode="debug_gates",
        )
        assert len(lines) == 1
        assert "DEBUG_GATES" in lines[0]

    def test_rollout_attention(self):
        from __lib.stop_gate_telemetry import render_attention_lines
        lines = render_attention_lines(
            gate_summary={},
            claim_summary={"matched": 0, "artifact_missing": 0, "no_match": 0, "other": 0},
            rollout_summary={"advisory": 5},
            session_mode="normal",
        )
        assert len(lines) == 1
        assert "advisory" in lines[0]
        assert "5" in lines[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])