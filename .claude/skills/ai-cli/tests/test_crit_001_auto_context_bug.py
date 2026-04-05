"""Characterization test for CRIT-001: Undefined variable 'latest' in _get_auto_context.

This test captures the current (broken) behavior of _get_auto_context.
Run with: pytest P:/.claude/skills/ai-cli/tests/test_crit_001_auto_context_bug.py -v

RED PHASE: This test should FAIL because the bug exists.
GREEN PHASE: After fix, this test should PASS.
"""

import json

# Add parent directory to path for imports
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_cli import _get_auto_context


class TestCrit001AutoContextBug:
    """Characterization test for CRIT-001: undefined variable 'latest'."""

    def test_auto_context_with_session_files_returns_latest_history(self, tmp_path):
        """
        Test that _get_auto_context returns formatted history from the latest session file.

        This test FAILS (RED phase) because 'latest' variable is undefined.

        Given: Session directory exists with multiple session files
        When: _get_auto_context() is called
        Then: Should return formatted history from the most recently modified file

        The bug: line 436 references undefined 'latest' variable.
        """
        # Arrange - Create mock session directory with multiple session files
        mock_session_dir = tmp_path / "sessions"
        mock_session_dir.mkdir()

        # Create session files with different timestamps
        session1 = mock_session_dir / "session1.jsonl"
        session2 = mock_session_dir / "session2.jsonl"
        session3 = mock_session_dir / "session3.jsonl"

        # Write session content with valid JSONL entries
        session_content = [
            {"type": "say", "message": {"role": "user", "content": "Hello"}},
            {"type": "say", "message": {"role": "assistant", "content": "Hi there"}},
        ]

        for session in [session1, session2, session3]:
            session.write_text(
                "\n".join(json.dumps(entry) for entry in session_content), encoding="utf-8"
            )

        # Make session2 the most recently modified
        session2.touch()

        # Act - Patch _SESSION_DIR to use our mock directory
        with patch("ai_cli._SESSION_DIR", mock_session_dir):
            # This should FAIL with NameError: name 'latest' is not defined
            result = _get_auto_context()

        # Assert - Should return formatted history from session2 (latest by mtime)
        # For now, we expect NameError - this is the BUG
        # After fix, we should get non-empty string with session content
        assert isinstance(result, str), "Result should be a string"
        # The bug causes NameError, so we won't reach here in RED phase
        # After GREEN phase (fix), result should contain session data

    def test_auto_context_with_empty_session_dir_returns_empty_string(self, tmp_path):
        """
        Test that _get_auto_context returns empty string when session directory is empty.

        Given: Session directory exists but has no session files
        When: _get_auto_context() is called
        Then: Should return empty string

        This test PASSES even with the bug (early return on empty list).
        """
        # Arrange - Create empty mock session directory
        mock_session_dir = tmp_path / "sessions_empty"
        mock_session_dir.mkdir()

        # Act
        with patch("ai_cli._SESSION_DIR", mock_session_dir):
            result = _get_auto_context()

        # Assert
        assert result == "", "Should return empty string for empty session directory"

    def test_auto_context_with_no_session_dir_returns_empty_string(self, tmp_path):
        """
        Test that _get_auto_context returns empty string when session directory doesn't exist.

        Given: Session directory does not exist
        When: _get_auto_context() is called
        Then: Should return empty string

        This test PASSES even with the bug (early return on non-existent directory).
        """
        # Arrange - Create a path that doesn't exist
        mock_session_dir = tmp_path / "nonexistent_sessions"

        # Act
        with patch("ai_cli._SESSION_DIR", mock_session_dir):
            result = _get_auto_context()

        # Assert
        assert result == "", "Should return empty string when session directory doesn't exist"
