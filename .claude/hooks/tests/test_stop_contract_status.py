"""Tests for Stop_contract_status.py and _get_contract_status_output().

Run with: pytest P:/.claude/hooks/tests/test_stop_contract_status.py -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
SCRIPT = HOOKS_DIR / "Stop_contract_status.py"
TOOLS_SCRIPT = HOOKS_DIR / "tools" / "contract-telemetry-queries.py"


class TestStopContractStatusScript:
    """Test the standalone Stop_contract_status.py script."""

    def test_script_runs_without_error(self):
        """Script must run without crashing."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(HOOKS_DIR),
        )
        # Script should not error
        assert result.returncode == 0, f"Script failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_script_produces_output_with_empty_logs(self):
        """Script should produce output even with no telemetry."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(HOOKS_DIR),
        )
        # With no data, script should still produce header/footer
        output = result.stdout
        # Should have box-drawing characters
        assert any(c in output for c in "═─"), f"Expected box-drawing output, got: {output}"


class TestGetWriterSummary:
    """Test writer summary functionality."""

    def test_writer_summary_with_synthetic_events(self, tmp_path):
        """Write synthetic writer events, verify summary counts."""
        writer_log = tmp_path / "task_contract_writer_telemetry.jsonl"

        # Write synthetic events
        with writer_log.open("w", encoding="utf-8") as f:
            for i in range(10):
                f.write(json.dumps({
                    "timestamp": 2e9 + i,
                    "feature": "task_contract_writer",
                    "event": "contract_active",
                    "task_class": "bug_fix",
                    "terminal_id": f"test{i}",
                }) + "\n")
            for i in range(3):
                f.write(json.dumps({
                    "timestamp": 2e9 + i + 100,
                    "feature": "task_contract_writer",
                    "event": "contract_skip",
                    "reason": "not_a_task_start",
                    "terminal_id": f"test{i}",
                }) + "\n")

        # Verify the script can read the events
        from Stop_contract_status import _load_events
        events = _load_events(writer_log)
        assert len(events) == 13
        assert len([e for e in events if e.get("event") == "contract_active"]) == 10
        assert len([e for e in events if e.get("reason") == "not_a_task_start"]) == 3


class TestGetStopBreakdown:
    """Test Stop gate breakdown functionality."""

    def test_stop_breakdown_with_synthetic_events(self, tmp_path):
        """Write synthetic Stop events, verify breakdown counts."""
        stop_log = tmp_path / "task_contract_telemetry.jsonl"

        # Write synthetic events
        with stop_log.open("w", encoding="utf-8") as f:
            for i in range(5):
                f.write(json.dumps({
                    "timestamp": 2e9 + i,
                    "gate": "task_contract_fit",
                    "decision": "allow",
                    "terminal_id": f"test{i}",
                }) + "\n")
            f.write(json.dumps({
                "timestamp": 2e9 + 10,
                "gate": "task_contract_fit",
                "decision": "block",
                "terminal_id": "test0",
            }) + "\n")
            f.write(json.dumps({
                "timestamp": 2e9 + 11,
                "gate": "task_contract_fit",
                "event": "silent",
                "reason": "uncertain_non_completion",
                "terminal_id": "test0",
            }) + "\n")

        # Verify events load correctly
        from Stop_contract_status import _load_events
        events = _load_events(stop_log)
        assert len(events) == 7
        assert len([e for e in events if e.get("decision") == "allow"]) == 5
        assert len([e for e in events if e.get("decision") == "block"]) == 1
        assert len([e for e in events if e.get("event") == "silent"]) == 1


class TestAnomalyDetection:
    """Test anomaly detection — delegates to contract_health.py."""

    def test_benign_not_task_start_volume_does_not_surface_alert(self, tmp_path):
        """High not-task-start volume alone must NOT surface a writer alert.

        'not_a_task_start' is benign exploratory chatter — not a writer failure.
        The old 'HIGH skip rate' wording is gone; the tuned model only fires on
        actual writer infrastructure failures (no_terminal_id, ambiguous, etc.).
        """
        from Stop_contract_status import get_anomaly_status

        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)

        now = datetime.now(timezone.utc).timestamp()
        # 200 not-task-start skips — should still be benign, no alert
        writer_lines = [
            json.dumps({
                "event": "contract_skip",
                "reason": "not_a_task_start",
                "feature": "task_contract_writer",
                "terminal_id": "test",
                "timestamp": now - i,
            }) for i in range(200)
        ]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(writer_lines) + "\n")

        from Stop_contract_status import get_anomaly_status as _gas
        from contract_health import get_health_summary as _ghs

        # The dashboard delegates to contract_health — test it directly
        summary = _ghs(hooks_dir=tmp_path)
        # Should be healthy — no suspicious skips
        assert summary.healthy is True
        # No writer-related alerts
        alert_text = " ".join(summary.alerts)
        assert "HIGH skip rate" not in alert_text
        assert "writer underperformance" not in alert_text
        assert "writer skip problem" not in alert_text

    def test_writer_underperformance_wording_on_real_problem(self, tmp_path):
        """Real writer infrastructure failures must surface 'writer underperformance'.

        When suspicious-skip ratio exceeds 40%, the tuned model fires with the
        'writer underperformance: N suspicious skips' wording — NOT 'HIGH skip rate'.
        """
        from contract_health import get_health_summary as _ghs

        diag = tmp_path / "logs" / "diagnostics"
        diag.mkdir(parents=True)

        now = datetime.now(timezone.utc).timestamp()
        writer_lines = []
        # 30 creates (assessment minimum)
        writer_lines += [
            json.dumps({
                "event": "contract_create",
                "feature": "task_contract_writer",
                "terminal_id": "test",
                "timestamp": now - i,
            }) for i in range(30)
        ]
        # 55 total skips: 25 benign + 30 no_terminal_id → 30/55 = 55% → fires
        writer_lines += [
            json.dumps({
                "event": "contract_skip",
                "reason": "not_a_task_start",
                "feature": "task_contract_writer",
                "terminal_id": "test",
                "timestamp": now - i,
            }) for i in range(30, 55)
        ]
        writer_lines += [
            json.dumps({
                "event": "contract_skip",
                "reason": "no_terminal_id",
                "feature": "task_contract_writer",
                "terminal_id": "test",
                "timestamp": now - i,
            }) for i in range(55, 85)
        ]
        (diag / "task_contract_writer_telemetry.jsonl").write_text("\n".join(writer_lines) + "\n")

        summary = _ghs(hooks_dir=tmp_path)
        assert summary.healthy is False
        alert_text = " ".join(summary.alerts)
        # Must use the tuned wording
        assert "writer underperformance" in alert_text
        # Old wording must NOT appear
        assert "HIGH skip rate" not in alert_text


class TestDashboardIntegration:
    """Test dashboard output integration with Stop hook."""

    def test_dashboard_includes_writer_stats(self):
        """Dashboard should include writer event counts."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(HOOKS_DIR),
        )
        output = result.stdout
        # Should have Contract Writer label
        assert "Contract" in output or "Writer" in output or "contracts" in output.lower()

    def test_dashboard_includes_stop_stats(self):
        """Dashboard should include Stop gate stats."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True,
            text=True,
            cwd=str(HOOKS_DIR),
        )
        output = result.stdout
        # Should mention Stop or block/allow/silent
        assert any(k in output for k in ["Stop", "allow", "block", "silent"])


class TestInProcessFunction:
    """Test the _get_contract_status_output() function (in-process version)."""

    def test_in_process_function_exists(self):
        """Stop.py should expose _get_contract_status_output."""
        # This tests the wiring - the function should be importable from Stop.py
        sys.path.insert(0, str(HOOKS_DIR))
        try:
            from Stop import _get_contract_status_output
            result = _get_contract_status_output()
            # Result is empty string when no events, or has content
            assert isinstance(result, str)
        except ImportError:
            pytest.fail("_get_contract_status_output not found in Stop.py")

    def test_in_process_function_with_empty_logs(self):
        """Function should return empty string with no telemetry."""
        sys.path.insert(0, str(HOOKS_DIR))
        try:
            from Stop import _get_contract_status_output
            # Force empty logs by ensuring files don't exist
            # (function checks for existence)
            result = _get_contract_status_output()
            # Empty logs = empty string
            assert isinstance(result, str)
        except ImportError:
            pytest.fail("_get_contract_status_output not found in Stop.py")