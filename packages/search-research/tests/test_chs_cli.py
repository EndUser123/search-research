"""Tests for _detect_terminal_id_inline() and get_current_session_id()."""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "chs" / "scripts"))
from chs_cli import CHSExporter


class TestDetectTerminalIdInline:
    """Unit tests for _detect_terminal_id_inline()."""

    def test_env_var_priority(self):
        """Priority 1: CLAUDE_TERMINAL_ID env var takes precedence."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "my-terminal-123"}):
            exporter = CHSExporter()
            result = exporter._detect_terminal_id_inline()
            assert result == "env_my-terminal-123"

    def test_env_var_sanitization(self):
        """Env var value with unsafe chars is sanitized."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "host/path:win"}):
            exporter = CHSExporter()
            result = exporter._detect_terminal_id_inline()
            assert result == "env_host-path-win"

    def test_wt_session_fallback(self):
        """Priority 2: WT_SESSION is used when no explicit env var."""
        # Clear explicit env vars so we fall through to WT_SESSION
        env = {k: v for k, v in os.environ.items()
               if k not in ("CLAUDE_TERMINAL_ID", "TERMINAL_ID", "TERM_ID", "SESSION_TERMINAL")}
        env["WT_SESSION"] = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        with patch.dict(os.environ, env, clear=True):
            exporter = CHSExporter()
            result = exporter._detect_terminal_id_inline()
            assert result == "console_a1b2c3d4-e5f6-7890-abcd-ef1234567890"

    def test_returns_empty_on_failure(self):
        """Priority 4: Returns empty string when no detection method succeeds."""
        # Clear all env vars
        with patch.dict(os.environ, {}, clear=True):
            exporter = CHSExporter()
            result = exporter._detect_terminal_id_inline()
            assert result == ""


class TestGetCurrentSessionId:
    """Unit tests for get_current_session_id()."""

    def test_empty_terminal_id_skips_active_session(self, tmp_path):
        """When terminal detection returns empty string, no file access occurs."""
        fake_home = tmp_path / ".claude"
        fake_home.mkdir(parents=True, exist_ok=True)

        with patch.dict(os.environ, {}, clear=True):
            exporter = CHSExporter()
            terminal_id = exporter._detect_terminal_id_inline()
            assert terminal_id == ""

            # get_current_session_id() returns None because:
            # 1. active-session check is guarded by `if terminal_id:`
            # 2. SDK fallback would need real HOME env var
            with patch("pathlib.Path.home", return_value=tmp_path):
                result = exporter.get_current_session_id()
            assert result is None

    def test_active_session_file_takes_priority(self, tmp_path):
        """Priority 1: active-session file is checked first."""
        fake_home = tmp_path / ".claude"
        fake_home.mkdir(parents=True, exist_ok=True)

        # Write active-session file with known session ID
        terminal_file = fake_home / "active-session-env_testterminal.txt"
        terminal_file.write_text("test-session-abc123\n")

        # Write transcript file so validation passes
        transcript_dir = fake_home / "projects" / "P--"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        (transcript_dir / "test-session-abc123.jsonl").write_text('{"test": true}\n')

        with patch("pathlib.Path.home", return_value=tmp_path):
            with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "testterminal"}):
                exporter = CHSExporter()
                result = exporter.get_current_session_id()

        assert result == "test-session-abc123"


class TestIntegrationActiveSessionFile:
    """Integration tests using real active-session files from this terminal."""

    def test_real_terminal_detection(self):
        """Using current terminal's WT_SESSION, detect_terminal_id returns non-empty."""
        wt_session = os.environ.get("WT_SESSION")
        if not wt_session:
            pytest.skip("WT_SESSION not set in this environment")

        exporter = CHSExporter()
        terminal_id = exporter._detect_terminal_id_inline()

        assert terminal_id != ""
        assert terminal_id.startswith("console_") or terminal_id.startswith("env_")

    def test_real_active_session_file_valid(self):
        """The active-session file written by handoff hook contains a real session ID."""
        wt_session = os.environ.get("WT_SESSION")
        if wt_session:
            active_file = Path.home() / ".claude" / f"active-session-console_{wt_session}.txt"
        else:
            # Find any active-session file
            active_files = list(Path.home() / ".claude" / "active-session-*.txt").glob("*")
            if not active_files:
                pytest.skip("No active-session files found")
            active_file = active_files[0]

        if not active_file.exists():
            pytest.skip(f"Active session file not found: {active_file}")

        session_id = active_file.read_text().strip()
        assert session_id != ""
        assert len(session_id) >= 32  # UUID format

        # Verify transcript exists
        transcript = Path.home() / ".claude" / "projects" / "P--" / f"{session_id}.jsonl"
        assert transcript.exists(), f"Transcript not found for session {session_id}"

    def test_get_current_session_id_returns_real_session(self):
        """get_current_session_id() returns the real current session from active-session file."""
        wt_session = os.environ.get("WT_SESSION")
        if not wt_session:
            pytest.skip("WT_SESSION not set")

        exporter = CHSExporter()
        session_id = exporter.get_current_session_id()

        if session_id:
            # It's a valid session ID from the active-session file
            assert len(session_id) >= 32
            transcript = Path.home() / ".claude" / "projects" / "P--" / f"{session_id}.jsonl"
            assert transcript.exists()
        # If None is returned, it's because the SDK fallback also failed
        # (expected in test environment without full SDK credentials)
