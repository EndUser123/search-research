#!/usr/bin/env python3
"""
Tests for cleanup verification system.

Tests the PostToolUse cleanup tracker and Stop cleanup verifier integration.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from posttooluse.cleanup_tracker_hook import CleanupTrackerHook
from Stop_cleanup_verifier import (
    _load_tool_history,
    check_cleanup_requirements,
    detect_work_type,
)


@pytest.fixture
def temp_state_dir():
    """Create a temporary state directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        yield state_dir


@pytest.fixture
def cleanup_tracker():
    """Create a CleanupTrackerHook instance."""
    return CleanupTrackerHook()


class TestCleanupTrackerHook:
    """Test CleanupTrackerHook functionality."""

    def test_track_tool_execution(self, cleanup_tracker, temp_state_dir):
        """Test that tool execution is tracked to history file."""
        session_id = "test-session-123"
        safe_session = "test-session-123"

        tool_input = {
            "file_path": "/test/path",
            "session_id": session_id,
        }

        with patch.dict(os.environ, {"CLEANUP_TRACKER_DIR": str(temp_state_dir)}):
            result = cleanup_tracker.process(
                tool_name="Edit",
                tool_input=tool_input,
                tool_response={"success": True},
            )

        assert result["passed"] is True

        # Verify history file was created
        history_file = temp_state_dir / f"cleanup_history_{safe_session}.json"
        assert history_file.exists()

        # Verify content
        history = json.loads(history_file.read_text(encoding="utf-8"))
        assert len(history["tools"]) == 1
        assert history["tools"][0]["name"] == "Edit"
        assert history["tools"][0]["input"] == tool_input

    def test_track_multiple_tools(self, cleanup_tracker, temp_state_dir):
        """Test that multiple tool executions accumulate."""
        session_id = "test-session-multi"
        safe_session = "test-session-multi"

        tools = ["Edit", "Read", "Grep"]

        with patch.dict(os.environ, {"CLEANUP_TRACKER_DIR": str(temp_state_dir)}):
            for tool_name in tools:
                cleanup_tracker.process(
                    tool_name=tool_name,
                    tool_input={"session_id": session_id},
                    tool_response={},
                )

        history_file = temp_state_dir / f"cleanup_history_{safe_session}.json"
        history = json.loads(history_file.read_text(encoding="utf-8"))

        assert len(history["tools"]) == 3
        assert [t["name"] for t in history["tools"]] == tools

    def test_skip_without_session_id(self, cleanup_tracker, temp_state_dir, monkeypatch):
        """Test that tracking is skipped when session_id is missing."""
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        result = cleanup_tracker.process(
            tool_name="Edit",
            tool_input={"file_path": "/test"},
            tool_response={},
        )

        assert result["passed"] is True
        assert result.get("skipped") is True

    def test_corrupted_file_recovery(self, cleanup_tracker, temp_state_dir):
        """Test that corrupted history files are recovered."""
        session_id = "test-corruption"
        safe_session = "test-corruption"
        history_file = temp_state_dir / f"cleanup_history_{safe_session}.json"

        # Create corrupted file
        history_file.write_text("invalid json", encoding="utf-8")

        with patch.dict(os.environ, {"CLEANUP_TRACKER_DIR": str(temp_state_dir)}):
            result = cleanup_tracker.process(
                tool_name="Edit",
                tool_input={"session_id": session_id},
                tool_response={},
            )

        # Should recover and create new file
        assert result["passed"] is True
        history = json.loads(history_file.read_text(encoding="utf-8"))
        assert len(history["tools"]) == 1


class TestLoadToolHistory:
    """Test _load_tool_history function."""

    def test_load_from_file(self, temp_state_dir):
        """Test loading tool history from file."""
        session_id = "test-load"
        safe_session = "test-load"
        history_file = temp_state_dir / f"cleanup_history_{safe_session}.json"

        # Create history file
        history_data = {
            "tools": [
                {
                    "name": "Edit",
                    "input": {"file_path": "/test"},
                    "timestamp": "2026-03-05T12:00:00",
                },
                {
                    "name": "Read",
                    "input": {"file_path": "/test"},
                    "timestamp": "2026-03-05T12:01:00",
                },
            ]
        }
        history_file.write_text(json.dumps(history_data), encoding="utf-8")

        data = {"session_id": session_id}
        with patch.dict(os.environ, {"CLEANUP_TRACKER_DIR": str(temp_state_dir)}):
            result = _load_tool_history(data)

        assert result is not None
        assert len(result) == 2
        assert result[0]["name"] == "Edit"

    def test_missing_file_returns_none(self, temp_state_dir):
        """Test that missing file returns None."""
        data = {"session_id": "nonexistent"}
        with patch.dict(os.environ, {"CLEANUP_TRACKER_DIR": str(temp_state_dir)}):
            result = _load_tool_history(data)

        assert result is None

    def test_missing_session_id_returns_none(self, monkeypatch):
        """Test that missing session_id returns None."""
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        data = {}
        result = _load_tool_history(data)
        assert result is None


class TestDetectWorkType:
    """Test work type detection from tool history."""

    def test_detect_bug_fix(self):
        """Test bug_fix detection: Edit + investigation tools."""
        tool_history = [
            {"name": "Read", "input": {"file_path": "/test"}},
            {"name": "Grep", "input": {"pattern": "bug"}},
            {"name": "Edit", "input": {"file_path": "/test"}},
        ]

        result = detect_work_type(tool_history)
        assert result == "bug_fix"

    def test_detect_hook_dev(self):
        """Test hook_dev detection: Edit + hook files."""
        tool_history = [
            {"name": "Read", "input": {"file_path": "hook_test.py"}},
            {"name": "Edit", "input": {"file_path": ".claude/hooks/test.py"}},
        ]

        result = detect_work_type(tool_history)
        assert result == "hook_dev"

    def test_detect_feature_dev(self):
        """Test feature_dev detection: Edit without investigation."""
        tool_history = [
            {"name": "Edit", "input": {"file_path": "/src/feature.py"}},
            {"name": "Write", "input": {"file_path": "/src/new.py"}},
        ]

        result = detect_work_type(tool_history)
        assert result == "feature_dev"

    def test_detect_testing(self):
        """Test testing detection: Bash with pytest."""
        tool_history = [
            {"name": "Bash", "input": {"command": "pytest tests/test_foo.py"}},
            {"name": "Bash", "input": {"command": "python -m pytest"}},
        ]

        result = detect_work_type(tool_history)
        assert result == "testing"

    def test_detect_architecture(self):
        """Test architecture detection: Skill with arch."""
        tool_history = [
            {"name": "Skill", "input": {"skill": "/arch review design"}},
        ]

        result = detect_work_type(tool_history)
        assert result == "architecture"

    def test_detect_documentation(self):
        """Test documentation detection: Edit with doc patterns."""
        tool_history = [
            {"name": "Edit", "input": {"file_path": "README.md"}},
            {"name": "Write", "input": {"file_path": "CLAUDE.md"}},
        ]

        result = detect_work_type(tool_history)
        assert result == "documentation"

    def test_empty_history_returns_none(self):
        """Test that empty history returns None."""
        result = detect_work_type([])
        assert result is None


class TestCheckCleanupRequirements:
    """Test cleanup requirement checks."""

    def test_bug_fix_missing_documentation(self, tmp_path):
        """Test bug fix cleanup check - missing documentation."""
        tool_history = [
            {"name": "Edit", "input": {"file_path": "/test/fix.py"}},
            {"name": "Bash", "input": {"command": "pytest"}},  # No git commit
        ]

        # Create bugfixes.md without recent entry
        bugfixes_path = tmp_path / ".serena" / "memories" / "bugfixes.md"
        bugfixes_path.parent.mkdir(parents=True, exist_ok=True)
        bugfixes_path.write_text("# Old entry from 2025-01-01\n", encoding="utf-8")

        data = {
            "project_root": str(tmp_path),
            "response": "Fixed the bug",
        }

        issues = check_cleanup_requirements("bug_fix", tool_history, "Fixed the bug", data)

        assert len(issues) > 0
        assert any("bugfixes.md" in issue for issue in issues)
        assert any("git commit" in issue for issue in issues)

    def test_hook_dev_missing_test_and_docs(self):
        """Test hook dev cleanup check - missing test and docs."""
        tool_history = [
            {"name": "Edit", "input": {"file_path": ".claude/hooks/test.py"}},
        ]

        data = {
            "project_root": "P:/",
            "response": "Hook updated",
        }

        issues = check_cleanup_requirements("hook_dev", tool_history, "Hook updated", data)

        assert len(issues) > 0
        assert any("Test hook" in issue for issue in issues)
        assert any("CLAUDE.md" in issue for issue in issues)

    def test_architecture_missing_adr(self, tmp_path):
        """Test architecture cleanup check - missing ADR."""
        tool_history = [{"name": "Skill", "input": {"skill": "/arch new system"}}]

        arch_decisions_dir = tmp_path / "docs" / "adrs"
        arch_decisions_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "project_root": str(tmp_path),
            "response": "Architecture designed",
        }

        issues = check_cleanup_requirements(
            "architecture", tool_history, "Architecture designed", data
        )

        assert len(issues) > 0
        assert any("ADR" in issue for issue in issues)

    def test_feature_dev_missing_claude_md(self, tmp_path):
        """Test feature dev cleanup check - missing CLAUDE.md update."""
        (tmp_path / "CLAUDE.md").write_text("project guidance", encoding="utf-8")
        tool_history = [
            {"name": "Edit", "input": {"file_path": "/src/feature.py"}},
            {"name": "Write", "input": {"file_path": "/src/new.py"}},
        ]

        data = {
            "project_root": str(tmp_path),
            "response": "Feature implemented",
        }

        issues = check_cleanup_requirements(
            "feature_dev", tool_history, "Feature implemented", data
        )

        assert len(issues) > 0
        assert any("CLAUDE.md" in issue for issue in issues)

    def test_testing_missing_tests(self):
        """Test testing cleanup check - missing test additions."""
        tool_history = [{"name": "Bash", "input": {"command": "ls"}}]

        data = {
            "project_root": "P:/",
            "response": "Tests reviewed",
        }

        issues = check_cleanup_requirements("testing", tool_history, "Tests reviewed", data)

        assert len(issues) > 0
        assert any("test suite" in issue for issue in issues)
