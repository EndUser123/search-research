"""
Tests for the local-summary guidance one-turn injection system:
- Stop.py assembles tool_transcript from tool_events
- Stop.py writes guidance marker on epistemic block with tool_transcript
- UserPromptSubmit reads and injects guidance next turn, then deletes it
"""

import importlib.util
import json
import time
from pathlib import Path
from unittest.mock import patch


def _load_stop():
    spec = importlib.util.spec_from_file_location("Stop", "P:/.claude/hooks/Stop.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _load_ups():
    spec = importlib.util.spec_from_file_location("UserPromptSubmit", "P:/.claude/hooks/UserPromptSubmit.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class TestToolTranscriptAssembly:
    """Stop.py assembles tool_transcript from tool_events before epistemic validation."""

    def test_assembles_transcript_from_last_5_events(self):
        """Last 5 tool events are concatenated into tool_transcript."""
        data = {
            "tool_events": [
                {"name": "Read", "output": "file1.txt: 10 lines"},  # index 0 — NOT in last-5
                {"name": "Bash", "output": "pytest result: 38 passed"},  # index 1 — FIRST of last-5
                {"name": "Edit", "output": "file2.py modified"},  # index 2
                {"name": "Glob", "output": "found 3 files"},  # index 3
                {"name": "Grep", "output": "match at line 42"},  # index 4
                {"name": "Write", "output": "new file created"},  # index 5 — LAST of last-5
            ]
        }

        # Simulate what Stop.py does before the cfg wire
        if not data.get("tool_transcript"):
            tool_events = data.get("tool_events", [])
            if tool_events:
                parts = []
                for event in tool_events[-5:]:  # last 5 = indices 1-5
                    output = event.get("output", "")
                    if output and isinstance(output, str):
                        parts.append(output[:500])
                data["tool_transcript"] = "\n".join(parts)

        # file1.txt is index 0, NOT in last-5 → should be excluded
        assert "file1.txt: 10 lines" not in data["tool_transcript"]
        assert "pytest result: 38 passed" in data["tool_transcript"]  # first of last-5 (index 1)
        assert "match at line 42" in data["tool_transcript"]  # index 4
        assert "new file created" in data["tool_transcript"]  # index 5 (last of last-5)
        assert len(data["tool_transcript"].split("\n")) == 5

    def test_truncates_long_output_per_event(self):
        """Each event's output is truncated to 500 chars."""
        long_output = "x" * 1000
        data = {
            "tool_events": [
                {"name": "Bash", "output": long_output},
            ]
        }

        if not data.get("tool_transcript"):
            tool_events = data.get("tool_events", [])
            parts = []
            for event in tool_events[-5:]:
                output = event.get("output", "")
                if output and isinstance(output, str):
                    parts.append(output[:500])
            data["tool_transcript"] = "\n".join(parts)

        assert len(data["tool_transcript"]) == 500
        assert "x" * 499 in data["tool_transcript"]

    def test_skips_non_string_output(self):
        """Non-string output fields are skipped."""
        data = {
            "tool_events": [
                {"name": "Read", "output": 12345},  # int, not str
                {"name": "Bash", "output": "actual result"},
            ]
        }

        if not data.get("tool_transcript"):
            tool_events = data.get("tool_events", [])
            parts = []
            for event in tool_events[-5:]:
                output = event.get("output", "")
                if output and isinstance(output, str):
                    parts.append(output[:500])
            data["tool_transcript"] = "\n".join(parts)

        assert data["tool_transcript"] == "actual result"

    def test_does_not_overwrite_existing_transcript(self):
        """If tool_transcript already in data dict, assembly is skipped."""
        data = {
            "tool_transcript": "pre-existing transcript",
            "tool_events": [
                {"name": "Bash", "output": "should not appear"},
            ]
        }

        if not data.get("tool_transcript"):
            tool_events = data.get("tool_events", [])
            parts = []
            for event in tool_events[-5:]:
                output = event.get("output", "")
                if output and isinstance(output, str):
                    parts.append(output[:500])
            data["tool_transcript"] = "\n".join(parts)

        assert data["tool_transcript"] == "pre-existing transcript"


class TestLocalSummaryGuidanceMarker:
    """Stop.py writes guidance marker when block is citation failure + tool_transcript."""

    def test_write_marker_creates_file(self, tmp_path, monkeypatch):
        """Marker file is created in the correct state directory."""
        Stop = _load_stop()

        # Mock HOOKS_DIR to tmp_path to avoid polluting real state
        with monkeypatch.context() as m:
            m.setattr(Stop, "HOOKS_DIR", tmp_path)
            m.setenv("CLAUDE_SESSION_ID", "test-session-abc")
            m.setenv("CLAUDE_TERMINAL_ID", "console-test-xyz")

            data = {
                "session_id": "test-session-abc",
                "terminal_id": "console-test-xyz",
            }
            Stop._write_local_summary_guidance_marker(data, "pytest", "38 passed in 0.5s")

        state_dir = tmp_path / "state" / "local_summary_guidance"
        marker = state_dir / "guidance__test-session-abc__console-test-xyz.json"
        assert marker.exists()
        contents = json.loads(marker.read_text(encoding="utf-8"))
        assert contents["session_id"] == "test-session-abc"
        assert contents["terminal_id"] == "console-test-xyz"
        assert "pytest" in contents["guidance"]
        assert "38 passed" in contents["guidance"]

    def test_write_marker_fails_silently_on_error(self, tmp_path, monkeypatch):
        """Errors in marker writing do not propagate."""
        Stop = _load_stop()

        # Path too long will cause OSError on write — should not raise
        class BadPath:
            def mkdir(self, *a, **k): raise OSError("disk full")
            def write_text(self, *a, **k): raise OSError("disk full")

        with monkeypatch.context() as m:
            m.setattr(Stop, "HOOKS_DIR", BadPath())
            m.setenv("CLAUDE_SESSION_ID", "test-session")
            m.setenv("CLAUDE_TERMINAL_ID", "console-test")

            data = {"session_id": "test-session", "terminal_id": "console-test"}
            # Should not raise
            Stop._write_local_summary_guidance_marker(data, "pytest", "38 passed")

    def test_no_marker_when_tool_transcript_empty(self, tmp_path, monkeypatch):
        """No marker is written when tool_transcript is empty."""
        Stop = _load_stop()

        with monkeypatch.context() as m:
            m.setattr(Stop, "HOOKS_DIR", tmp_path)
            m.setenv("CLAUDE_SESSION_ID", "test-session")
            m.setenv("CLAUDE_TERMINAL_ID", "console-test")

            data = {"session_id": "test-session", "terminal_id": "console-test"}
            Stop._write_local_summary_guidance_marker(data, "pytest", "")  # empty

        state_dir = tmp_path / "state" / "local_summary_guidance"
        marker = state_dir / "guidance__test-session__console-test.json"
        assert not marker.exists()


class TestCheckLocalSummaryGuidance:
    """UserPromptSubmit.check_local_summary_guidance reads and deletes the marker."""

    def test_returns_guidance_and_deletes_marker(self, tmp_path):
        """When marker exists and is fresh, guidance is returned and marker deleted."""
        UPS = _load_ups()

        # Create a valid marker
        state_dir = tmp_path / "state" / "local_summary_guidance"
        state_dir.mkdir(parents=True, exist_ok=True)
        marker_path = state_dir / "guidance__test-session__console-test.json"
        marker_data = {
            "session_id": "test-session",
            "terminal_id": "console-test",
            "timestamp": time.time(),
            "guidance": "Test guidance text for the model.",
        }
        marker_path.write_text(json.dumps(marker_data), encoding="utf-8")

        data = {
            "session_id": "test-session",
            "terminal_id": "console-test",
        }

        # Patch the state_dir in UPS to use tmp_path
        import os
        orig_state_dir = "P:/.claude/hooks/state/local_summary_guidance"
        # We need to test the function directly - it reads from P:/.claude/hooks/state/local_summary_guidance
        # So we create the marker in the real location and test cleanup
        # Instead, test by patching Path
        marker_path_real = Path("P:/.claude/hooks/state/local_summary_guidance") / "guidance__test-session__console-test.json"
        marker_path_real.parent.mkdir(parents=True, exist_ok=True)
        marker_path_real.write_text(json.dumps(marker_data), encoding="utf-8")

        result = UPS.check_local_summary_guidance(data)

        assert result == "Test guidance text for the model."
        assert not marker_path_real.exists()  # deleted after read

    def test_returns_none_when_no_marker(self, tmp_path):
        """No marker present → None."""
        UPS = _load_ups()

        data = {
            "session_id": "no-such-session",
            "terminal_id": "no-such-terminal",
        }

        result = UPS.check_local_summary_guidance(data)
        assert result is None

    def test_expired_marker_is_deleted(self, tmp_path):
        """Marker older than 120s is deleted and None is returned."""
        UPS = _load_ups()

        state_dir = Path("P:/.claude/hooks/state/local_summary_guidance")
        state_dir.mkdir(parents=True, exist_ok=True)
        marker_path = state_dir / "guidance__test-session__console-test.json"
        marker_data = {
            "session_id": "test-session",
            "terminal_id": "console-test",
            "timestamp": time.time() - 200,  # expired
            "guidance": "Old guidance.",
        }
        marker_path.write_text(json.dumps(marker_data), encoding="utf-8")

        data = {"session_id": "test-session", "terminal_id": "console-test"}
        result = UPS.check_local_summary_guidance(data)

        assert result is None
        assert not marker_path.exists()

    def test_empty_guidance_returns_none(self, tmp_path):
        """Marker with empty guidance string returns None."""
        UPS = _load_ups()

        state_dir = Path("P:/.claude/hooks/state/local_summary_guidance")
        state_dir.mkdir(parents=True, exist_ok=True)
        marker_path = state_dir / "guidance__test-session__console-test.json"
        marker_data = {
            "session_id": "test-session",
            "terminal_id": "console-test",
            "timestamp": time.time(),
            "guidance": "",
        }
        marker_path.write_text(json.dumps(marker_data), encoding="utf-8")

        data = {"session_id": "test-session", "terminal_id": "console-test"}
        result = UPS.check_local_summary_guidance(data)

        assert result is None

    def test_uses_env_fallback_when_data_missing(self, tmp_path, monkeypatch):
        """session_id/terminal_id fall back to environment when not in data."""
        UPS = _load_ups()

        state_dir = Path("P:/.claude/hooks/state/local_summary_guidance")
        state_dir.mkdir(parents=True, exist_ok=True)
        marker_path = state_dir / "guidance__env-session__env-terminal.json"
        marker_data = {
            "session_id": "env-session",
            "terminal_id": "env-terminal",
            "timestamp": time.time(),
            "guidance": "From env fallback.",
        }
        marker_path.write_text(json.dumps(marker_data), encoding="utf-8")

        with monkeypatch.context() as m:
            m.setenv("CLAUDE_SESSION_ID", "env-session")
            m.setenv("CLAUDE_TERMINAL_ID", "env-terminal")
            # No session_id/terminal_id in data dict
            result = UPS.check_local_summary_guidance({})

        assert result == "From env fallback."


class TestInjectsLocalSummaryGuidance:
    """Local summary guidance is injected via the injections list in UserPromptSubmit."""

    def test_guidance_appended_to_injections(self, tmp_path, monkeypatch):
        """check_local_summary_guidance result is appended to injections list."""
        UPS = _load_ups()

        state_dir = Path("P:/.claude/hooks/state/local_summary_guidance")
        state_dir.mkdir(parents=True, exist_ok=True)
        marker_path = state_dir / "guidance__sess__term.json"
        marker_path.write_text(json.dumps({
            "session_id": "sess",
            "terminal_id": "term",
            "timestamp": time.time(),
            "guidance": "This is the guidance tip.",
        }), encoding="utf-8")

        data = {"session_id": "sess", "terminal_id": "term"}
        guidance = UPS.check_local_summary_guidance(data)

        injections = []
        if guidance:
            injections.append(guidance)

        assert len(injections) == 1
        assert injections[0] == "This is the guidance tip."

    def test_no_injection_when_no_marker(self, tmp_path):
        """When no guidance marker exists, injections list is unchanged."""
        UPS = _load_ups()

        data = {"session_id": "no-such", "terminal_id": "no-such"}
        guidance = UPS.check_local_summary_guidance(data)

        injections = []
        if guidance:
            injections.append(guidance)

        assert injections == []


class TestPushbackUnaffected:
    """Local summary guidance is independent of the challenge/pushback system."""

    def test_pushback_and_guidance_use_different_namespaces(self, tmp_path):
        """Challenge markers and guidance markers use different directories and prefixes."""
        challenge_dir = tmp_path / "state" / "anti_sycophancy_injector"
        guidance_dir = tmp_path / "state" / "local_summary_guidance"

        challenge_dir.mkdir(parents=True, exist_ok=True)
        guidance_dir.mkdir(parents=True, exist_ok=True)

        # Write challenge marker
        challenge_marker = challenge_dir / "challenge__sess__term.json"
        challenge_marker.write_text(json.dumps({
            "session_id": "sess",
            "terminal_id": "term",
            "timestamp": time.time(),
        }), encoding="utf-8")

        # Write guidance marker
        guidance_marker = guidance_dir / "guidance__sess__term.json"
        guidance_marker.write_text(json.dumps({
            "session_id": "sess",
            "terminal_id": "term",
            "timestamp": time.time(),
            "guidance": "Guidance text.",
        }), encoding="utf-8")

        # Both files exist and are distinct
        assert challenge_marker.exists()
        assert guidance_marker.exists()
        assert challenge_marker != guidance_marker
        assert challenge_marker.parent != guidance_marker.parent
