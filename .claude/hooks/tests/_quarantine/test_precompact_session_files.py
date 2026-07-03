"""
Tests for on_precompact.py extract_modified_files() method.

Requirement: extract_modified_files() should return files tracked by the
session activity tracker, NOT from git status.

Test Strategy:
1. Mock the session activity tracker's get_session_files() to return specific files
2. Let git subprocess run (it will return actual git status)
3. Verify extract_modified_files() returns session files, NOT git status
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

# Setup path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CKS_MODULE_PATH = PROJECT_ROOT / "__csf" / "src" / "csf"
HOOKS_PATH = PROJECT_ROOT / ".claude" / "hooks"
SESSION_MODULE_PATH = PROJECT_ROOT / "__csf" / "src" / "modules" / "session_management"

import sys

sys.path.insert(0, str(CKS_MODULE_PATH))
sys.path.insert(0, str(HOOKS_PATH))
sys.path.insert(0, str(SESSION_MODULE_PATH))


class TestExtractModifiedFilesUsesSessionTracker:
    """
    Test that extract_modified_files() returns session-tracked files,
    NOT git status results.
    """

    @patch("on_precompact.PROJECT_ROOT", Path("P:/"))
    @patch("on_precompact.TaskIdentityManager")
    @patch("on_precompact.CKSHyperGraphClient")
    @patch("on_precompact._get_session_id_from_env", return_value="test_session")
    @patch("on_precompact.get_session_files")
    def test_returns_session_files_not_git_status(
        self, mock_get_session_files, mock_session_id, mock_cks_client, mock_task_manager
    ):
        """
        Test that extract_modified_files() returns session-tracked files,
        NOT the files from git status.

        Given:
            - Session activity tracker's get_session_files() returns specific files
            - Git status returns different files (actual repo state)
        When:
            - extract_modified_files() is called
        Then:
            - Returns the session-tracked files
            - Does NOT return the git status files
        """
        # Import here to apply patches
        from on_precompact import PreCompactCheckpointCKS

        # Arrange: Create instance
        instance = PreCompactCheckpointCKS()

        # Mock session files (what we expect to be returned)
        session_files = [
            "P:/src/module/service.py",
            "P:/src/module/models.py",
            "P:/src/utils/helpers.py",
        ]
        mock_get_session_files.return_value = session_files

        # Act
        result = instance.extract_modified_files()

        # Assert: Result should be session files, NOT git files
        assert result == session_files, (
            f"Expected session files {session_files}, "
            f"but got {result}. "
        )

    @patch("on_precompact.PROJECT_ROOT", Path("P:/"))
    @patch("on_precompact.TaskIdentityManager")
    @patch("on_precompact.CKSHyperGraphClient")
    @patch("on_precompact._get_session_id_from_env", return_value="test_session")
    @patch("on_precompact.get_session_files")
    def test_returns_empty_list_when_no_session_files(
        self, mock_get_session_files, mock_session_id, mock_cks_client, mock_task_manager
    ):
        """
        Test that extract_modified_files() returns empty list
        when session has no tracked files.

        Given:
            - Session activity tracker's get_session_files() returns empty list
            - Git status returns modified files (actual repo state)
        When:
            - extract_modified_files() is called
        Then:
            - Returns empty list (session files take priority)
        """
        # Import here to apply patches
        from on_precompact import PreCompactCheckpointCKS

        # Arrange
        instance = PreCompactCheckpointCKS()

        # Session returns empty
        session_files: list[str] = []
        mock_get_session_files.return_value = session_files

        # Act
        result = instance.extract_modified_files()

        # Assert: Empty list because no session files
        assert result == [], (
            f"Expected empty list when no session files, "
            f"but got {result}. "
        )

    @patch("on_precompact.PROJECT_ROOT", Path("P:/"))
    @patch("on_precompact.TaskIdentityManager")
    @patch("on_precompact.CKSHyperGraphClient")
    @patch("on_precompact._get_session_id_from_env", return_value="test_session")
    @patch("on_precompact.get_session_files")
    def test_limits_to_ten_files_max(
        self, mock_get_session_files, mock_session_id, mock_cks_client, mock_task_manager
    ):
        """
        Test that extract_modified_files() limits results to 10 files maximum.

        Given:
            - Session activity tracker returns 15 files
        When:
            - extract_modified_files() is called
        Then:
            - Returns only first 10 files
        """
        # Import here to apply patches
        from on_precompact import PreCompactCheckpointCKS

        # Arrange
        instance = PreCompactCheckpointCKS()

        # Create 15 session files
        session_files = [f"P:/src/file{i}.py" for i in range(15)]
        mock_get_session_files.return_value = session_files

        # Act
        result = instance.extract_modified_files()

        # Assert: Only 10 files returned
        assert len(result) == 10, (
            f"Expected max 10 files, but got {len(result)}. "
        )
        assert result == session_files[:10], (
            f"Expected first 10 session files, but got {result}"
        )

    @patch("on_precompact.PROJECT_ROOT", Path("P:/"))
    @patch("on_precompact.TaskIdentityManager")
    @patch("on_precompact.CKSHyperGraphClient")
    @patch("on_precompact._get_session_id_from_env", return_value="test_session")
    @patch("on_precompact.get_session_files")
    def test_session_files_preserve_order(
        self, mock_get_session_files, mock_session_id, mock_cks_client, mock_task_manager
    ):
        """
        Test that extract_modified_files() preserves the order from session tracker.

        Given:
            - Session activity tracker returns files in specific order (most recent first)
        When:
            - extract_modified_files() is called
        Then:
            - Returns files in the same order as session tracker
        """
        # Import here to apply patches
        from on_precompact import PreCompactCheckpointCKS

        # Arrange
        instance = PreCompactCheckpointCKS()

        # Session files in specific order (most recent first)
        session_files = [
            "P:/src/latest_change.py",
            "P:/src/middle_change.py",
            "P:/src/earliest_change.py",
        ]
        mock_get_session_files.return_value = session_files

        # Act
        result = instance.extract_modified_files()

        # Assert: Order preserved
        assert result == session_files, (
            f"Expected order {session_files}, but got {result}. "
        )

    @patch("on_precompact.PROJECT_ROOT", Path("P:/"))
    @patch("on_precompact.TaskIdentityManager")
    @patch("on_precompact.CKSHyperGraphClient")
    @patch("on_precompact._get_session_id_from_env", return_value=None)
    def test_returns_empty_list_when_no_session_id(
        self, mock_session_id, mock_cks_client, mock_task_manager
    ):
        """
        Test that extract_modified_files() returns empty list when no session ID available.

        Given:
            - _get_session_id_from_env() returns None (no WT_SESSION)
        When:
            - extract_modified_files() is called
        Then:
            - Returns empty list
        """
        # Import here to apply patches
        from on_precompact import PreCompactCheckpointCKS

        # Arrange
        instance = PreCompactCheckpointCKS()

        # Act
        result = instance.extract_modified_files()

        # Assert: Empty list because no session ID
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
