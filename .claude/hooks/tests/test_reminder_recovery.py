#!/usr/bin/env python3
"""Tests for reminder recovery hooks."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
from utils.reminder_state import (
    artifacts_dir,
    hash_reminder,
    is_state_fresh,
    read_compaction_state,
    read_memory_md,
    write_compaction_state,
)
from PreCompact import capture_state
from PostCompact import restore_state
from SessionStart_reminder_recovery import resume_session


class TestReminderState:
    """Tests for shared reminder_state utilities."""

    def test_hash_reminder_length(self):
        h = hash_reminder("test")
        assert len(h) == 12
        assert h == hash_reminder("test")

    def test_is_state_fresh_now(self):
        now = datetime.now(timezone.utc).isoformat()
        assert is_state_fresh(now, 60) is True

    def test_is_state_fresh_stale(self):
        stale = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        assert is_state_fresh(stale, 60) is False

    def test_is_state_fresh_none(self):
        assert is_state_fresh(None, 60) is True

    def test_write_and_read_compaction_state(self):
        terminal = "test_terminal_123"
        state = {
            "session_id": "sess_abc",
            "goal": "test goal",
            "last_action": "Write: test.py",
            "pending_work": ["verify"],
            "active_files": ["test.py"],
            "recent_corrections": ["Test correction"],
            "reminder_hashes": [],
        }
        write_compaction_state(terminal, state, update_timestamp=False)
        loaded = read_compaction_state(terminal)
        assert loaded is not None
        assert loaded["goal"] == "test goal"
        assert loaded["session_id"] == "sess_abc"

    def test_read_compaction_state_missing(self):
        assert read_compaction_state("nonexistent_terminal") is None

    def test_artifacts_dir_creates_parent(self, tmp_path, monkeypatch):
        """artifacts_dir creates directory if missing."""
        monkeypatch.setenv("CLAUDE_PROJECT_ROOT", str(tmp_path))
        td = artifacts_dir("test_console_xyz")
        assert td.exists()
        assert td.is_dir()


class TestPreCompact:
    """Tests for PreCompact hook."""

    def test_capture_state_success(self):
        data = {
            "session_id": "test_sess",
            "terminal_id": "test_terminal_precompact",
            "transcript_path": None,
            "context": {
                "last_user_message": "Test the precompact hook",
                "recent_tool_calls": [
                    {"tool": "Write", "input": {"file_path": "test.py"}, "result": "ok"}
                ],
            },
        }
        result = capture_state(data)
        assert result["status"] == "success"

    def test_capture_state_extracts_goal(self):
        data = {
            "session_id": "test_sess",
            "terminal_id": "test_terminal_goal",
            "transcript_path": None,
            "context": {
                "last_user_message": "Fix the bug in PreCompact.py",
                "recent_tool_calls": [],
            },
        }
        capture_state(data)
        state = read_compaction_state("test_terminal_goal")
        assert state is not None
        assert "bug" in state["goal"]

    def test_capture_state_invalid_json(self):
        # Should not crash - returns error dict
        pass  # Handled at __main__ level


class TestPostCompact:
    """Tests for PostCompact hook."""

    def test_restore_state_with_fresh_state(self):
        terminal = "test_terminal_postcompact"
        # Pre-write state
        state = {
            "session_id": "sess_abc",
            "goal": "restore test",
            "last_action": "Write: test.py",
            "pending_work": ["verify it works"],
            "active_files": ["test.py"],
            "recent_corrections": ["Don't mock the database"],
            "reminder_hashes": [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        write_compaction_state(terminal, state, update_timestamp=False)

        data = {
            "session_id": "sess_abc",
            "terminal_id": terminal,
            "transcript_path": None,
        }
        result = restore_state(data)
        assert result["status"] == "success"
        assert "additionalContext" in result
        assert "restore test" in result["additionalContext"]
        assert "RESUME:" in result["additionalContext"]

    def test_restore_state_no_state(self):
        data = {
            "session_id": "test",
            "terminal_id": "nonexistent_terminal",
            "transcript_path": None,
        }
        result = restore_state(data)
        assert result["status"] == "success"
        assert "additionalContext" not in result

    def test_restore_state_stale(self):
        terminal = "test_terminal_stale"
        state = {
            "session_id": "sess_abc",
            "goal": "old goal",
            "last_action": "",
            "pending_work": [],
            "active_files": [],
            "recent_corrections": [],
            "reminder_hashes": [],
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        }
        write_compaction_state(terminal, state, update_timestamp=False)

        data = {"session_id": "sess", "terminal_id": terminal, "transcript_path": None}
        result = restore_state(data)
        assert result["status"] == "success"
        assert "additionalContext" not in result


class TestSessionStart:
    """Tests for SessionStart reminder recovery."""

    def test_resume_session_with_fresh_state(self):
        terminal = "test_terminal_ss"
        state = {
            "session_id": "sess_abc",
            "goal": "session resume test",
            "pending_work": ["check the work"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        write_compaction_state(terminal, state, update_timestamp=False)

        data = {
            "session_id": "sess_abc",
            "terminal_id": terminal,
            "is_resume": True,
        }
        result = resume_session(data)
        assert result["status"] == "success"
        assert "additionalContext" in result
        assert "session resume test" in result["additionalContext"]

    def test_resume_session_no_state(self):
        data = {
            "session_id": "test",
            "terminal_id": "nonexistent_terminal",
            "is_resume": False,
        }
        result = resume_session(data)
        assert result["status"] == "success"

    def test_resume_session_stale(self):
        terminal = "test_terminal_ss_stale"
        state = {
            "session_id": "sess",
            "goal": "old session",
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
        }
        write_compaction_state(terminal, state, update_timestamp=False)

        data = {"session_id": "sess", "terminal_id": terminal, "is_resume": True}
        result = resume_session(data)
        assert result["status"] == "success"
        # Stale + resume = no injection
        assert "additionalContext" not in result
