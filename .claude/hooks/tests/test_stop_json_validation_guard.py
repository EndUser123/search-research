"""Tests for the Stop JSON validation failure guard in Stop.py.

Tests the guard logic directly by calling the output-assembly path with
synthetic stderr log fixtures. No real hooks run.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

# We test the guard logic by importing the module and calling its main()
# in a controlled environment. The guard reads hook_runner_stderr.jsonl
# from HOOKS_DIR/logs/diagnostics/. We patch that path via monkeypatch.


def _make_stderr_entry(session_id: str, stderr: str, ts: str) -> dict:
    """Create a synthetic hook_runner_stderr.jsonl entry."""
    return {
        "session_id": session_id,
        "stderr": stderr,
        "ts": ts,
        "hook": "Stop",
        "exit_code": 0,
    }


def _write_stderr_log(path: Path, entries: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(e) for e in entries) + "\n",
        encoding="utf-8",
    )


class TestStopJsonValidationGuard:
    """Test the JSON validation failure guard in Stop.py output assembly."""

    def test_recent_current_session_adds_warning(self, monkeypatch, tmp_path):
        """Case 1: recent current-session JSON validation failure adds warning."""
        # Create a stderr log with a recent JSON validation failure
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        now = datetime.now(timezone.utc)
        entry = _make_stderr_entry(
            "test-session-123",
            "JSON validation failed",
            now.isoformat(),
        )
        _write_stderr_log(diag_dir / "hook_runner_stderr.jsonl", [entry])

        # Import and test the guard logic directly
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop import _apply_json_validation_guard

        output = {"systemMessage": "test output"}
        data = {"session_id": "test-session-123"}
        _apply_json_validation_guard(output, data, tmp_path)

        assert "JSON validation failure detected" in output["systemMessage"]
        assert "test output" in output["systemMessage"]

    def test_clean_log_adds_no_warning(self, monkeypatch, tmp_path):
        """Case 2: clean log adds no warning."""
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        entry = _make_stderr_entry(
            "test-session-123",
            "semantic_critic mistral_error: timeout",
            datetime.now(timezone.utc).isoformat(),
        )
        _write_stderr_log(diag_dir / "hook_runner_stderr.jsonl", [entry])

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop import _apply_json_validation_guard

        output = {"systemMessage": "test output"}
        data = {"session_id": "test-session-123"}
        _apply_json_validation_guard(output, data, tmp_path)

        assert output["systemMessage"] == "test output"

    def test_stale_entry_adds_no_warning(self, monkeypatch, tmp_path):
        """Case 3: stale entry (>5 minutes) adds no warning."""
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        stale_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        entry = _make_stderr_entry(
            "test-session-123",
            "JSON validation failed",
            stale_time.isoformat(),
        )
        _write_stderr_log(diag_dir / "hook_runner_stderr.jsonl", [entry])

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop import _apply_json_validation_guard

        output = {"systemMessage": "test output"}
        data = {"session_id": "test-session-123"}
        _apply_json_validation_guard(output, data, tmp_path)

        assert output["systemMessage"] == "test output"

    def test_different_session_adds_no_warning(self, monkeypatch, tmp_path):
        """Case 4: different session's failure adds no warning."""
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        entry = _make_stderr_entry(
            "other-session-456",
            "JSON validation failed",
            datetime.now(timezone.utc).isoformat(),
        )
        _write_stderr_log(diag_dir / "hook_runner_stderr.jsonl", [entry])

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop import _apply_json_validation_guard

        output = {"systemMessage": "test output"}
        data = {"session_id": "test-session-123"}
        _apply_json_validation_guard(output, data, tmp_path)

        assert output["systemMessage"] == "test output"

    def test_output_remains_valid_stop_schema(self, monkeypatch, tmp_path):
        """Case 5: final output remains valid Stop schema."""
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        entry = _make_stderr_entry(
            "test-session-123",
            "JSON validation failed",
            datetime.now(timezone.utc).isoformat(),
        )
        _write_stderr_log(diag_dir / "hook_runner_stderr.jsonl", [entry])

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop import _apply_json_validation_guard

        # Start with a valid Stop output (advisory path)
        output = {"systemMessage": "original message", "continue": True}
        data = {"session_id": "test-session-123"}
        _apply_json_validation_guard(output, data, tmp_path)

        # Must still be valid Stop schema
        assert "continue" in output
        assert output["continue"] is True
        assert "systemMessage" in output
        # Must be JSON-serializable
        serialized = json.dumps(output)
        parsed = json.loads(serialized)
        assert parsed["continue"] is True
        assert "JSON validation failure detected" in parsed["systemMessage"]

    def test_no_system_message_creates_one(self, monkeypatch, tmp_path):
        """Guard creates systemMessage if none existed."""
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        entry = _make_stderr_entry(
            "test-session-123",
            "JSON validation failed",
            datetime.now(timezone.utc).isoformat(),
        )
        _write_stderr_log(diag_dir / "hook_runner_stderr.jsonl", [entry])

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop import _apply_json_validation_guard

        output = {"continue": True}
        data = {"session_id": "test-session-123"}
        _apply_json_validation_guard(output, data, tmp_path)

        assert "systemMessage" in output
        assert "JSON validation failure detected" in output["systemMessage"]

    def test_missing_session_id_no_crash(self, monkeypatch, tmp_path):
        """Guard handles missing session_id gracefully."""
        diag_dir = tmp_path / "logs" / "diagnostics"
        diag_dir.mkdir(parents=True)
        _write_stderr_log(diag_dir / "hook_runner_stderr.jsonl", [])

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop import _apply_json_validation_guard

        output = {"continue": True}
        data = {}
        _apply_json_validation_guard(output, data, tmp_path)
        # No crash, no warning added
        assert "systemMessage" not in output

    def test_missing_log_file_no_crash(self, monkeypatch, tmp_path):
        """Guard handles missing stderr log file gracefully."""
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from Stop import _apply_json_validation_guard

        output = {"continue": True}
        data = {"session_id": "test-session-123"}
        _apply_json_validation_guard(output, data, tmp_path)
        # No crash, no warning added
        assert "systemMessage" not in output
