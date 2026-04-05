#!/usr/bin/env python3
"""
Tests for Git operations library (lib/git.py).

Tests cover:
- Getting current commit SHA
- Detecting file changes since a base commit
- Error handling for non-git repositories
- Invalid commit references
- Working directory parameter

Test File: tests/test_git.py
Run with: pytest tests/test_git.py -v
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add lib directory to path
LIB_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from git import (
    detect_git_changes,
    get_git_commit_sha,
)


class TestGetGitCommitSha:
    """Tests for get_git_commit_sha function."""

    def test_returns_sha_for_valid_git_repo(self):
        """
        Test that get_git_commit_sha returns valid SHA in git repo.

        Given: A valid git repository with commits
        When: get_git_commit_sha is called
        Then: Should return 40-character hexadecimal SHA
        """
        # Mock subprocess.run to return a valid SHA
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            sha = get_git_commit_sha()

            assert sha == "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
            assert len(sha) == 40
            assert all(c in "0123456789abcdef" for c in sha.lower())

    def test_returns_none_for_invalid_sha_format(self):
        """
        Test that get_git_commit_sha returns None for invalid SHA format.

        Given: git rev-parse returns invalid output (not 40 hex chars)
        When: get_git_commit_sha is called
        Then: Should return None
        """
        # Mock subprocess.run to return invalid SHA
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "not-a-valid-sha\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            sha = get_git_commit_sha()

            assert sha is None

    def test_returns_none_when_not_in_git_repo(self):
        """
        Test that get_git_commit_sha returns None when not in git repo.

        Given: Directory is not a git repository
        When: get_git_commit_sha is called
        Then: Should return None
        """
        # Mock subprocess.run to raise CalledProcessError
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            sha = get_git_commit_sha()

            assert sha is None

    def test_returns_none_when_git_not_found(self):
        """
        Test that get_git_commit_sha returns None when git is not installed.

        Given: git command is not available
        When: get_git_commit_sha is called
        Then: Should return None
        """
        # Mock subprocess.run to raise FileNotFoundError
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            sha = get_git_commit_sha()

            assert sha is None

    def test_respects_cwd_parameter(self):
        """
        Test that get_git_commit_sha uses cwd parameter.

        Given: A specific working directory is provided
        When: get_git_commit_sha is called with cwd parameter
        Then: Should pass cwd to subprocess.run
        """
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "abc123def4567890123456789012345678901234\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            sha = get_git_commit_sha(cwd="/path/to/repo")

            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs['cwd'] == "/path/to/repo"
            assert sha == "abc123def4567890123456789012345678901234"


class TestDetectGitChanges:
    """Tests for detect_git_changes function."""

    def test_returns_list_of_changed_files(self):
        """
        Test that detect_git_changes returns list of changed files.

        Given: Files have changed since base commit
        When: detect_git_changes is called
        Then: Should return list of file paths
        """
        # Mock subprocess.run to return changed files
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "src/main.py\ntests/test_main.py\nREADME.md\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            changed = detect_git_changes("HEAD~5")

            assert len(changed) == 3
            assert "src/main.py" in changed
            assert "tests/test_main.py" in changed
            assert "README.md" in changed

    def test_returns_empty_list_when_no_changes(self):
        """
        Test that detect_git_changes returns empty list when no changes.

        Given: No files have changed since base commit
        When: detect_git_changes is called
        Then: Should return empty list
        """
        # Mock subprocess.run to return empty output
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            changed = detect_git_changes("HEAD~5")

            assert changed == []

    def test_returns_empty_list_for_invalid_commit(self):
        """
        Test that detect_git_changes returns empty list for invalid commit.

        Given: Base commit reference is invalid
        When: detect_git_changes is called
        Then: Should return empty list
        """
        # Mock subprocess.run to raise CalledProcessError
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            changed = detect_git_changes("nonexistent-commit-12345")

            assert changed == []

    def test_returns_empty_list_when_git_not_found(self):
        """
        Test that detect_git_changes returns empty list when git not installed.

        Given: git command is not available
        When: detect_git_changes is called
        Then: Should return empty list
        """
        # Mock subprocess.run to raise FileNotFoundError
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()

            changed = detect_git_changes("HEAD~5")

            assert changed == []

    def test_filters_empty_lines_from_output(self):
        """
        Test that detect_git_changes filters empty lines.

        Given: git diff output contains blank lines
        When: detect_git_changes is called
        Then: Should filter out empty lines
        """
        # Mock subprocess.run to return output with blank lines
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "src/main.py\n\n\ntests/test_main.py\n\nREADME.md\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            changed = detect_git_changes("HEAD~5")

            assert len(changed) == 3
            assert "" not in changed

    def test_strips_whitespace_from_paths(self):
        """
        Test that detect_git_changes strips whitespace from paths.

        Given: git diff output has leading/trailing whitespace
        When: detect_git_changes is called
        Then: Should strip whitespace from file paths
        """
        # Mock subprocess.run to return output with whitespace
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "  src/main.py  \n\ttests/test_main.py\t\n   README.md   \n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            changed = detect_git_changes("HEAD~5")

            assert "src/main.py" in changed
            assert "tests/test_main.py" in changed
            assert "README.md" in changed
            assert not any(path.startswith(" ") or path.endswith(" ") for path in changed)

    def test_respects_cwd_parameter(self):
        """
        Test that detect_git_changes uses cwd parameter.

        Given: A specific working directory is provided
        When: detect_git_changes is called with cwd parameter
        Then: Should pass cwd to subprocess.run
        """
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = "src/main.py\n"
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            changed = detect_git_changes("HEAD~5", cwd="/path/to/repo")

            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs['cwd'] == "/path/to/repo"

    def test_passes_base_commit_to_git_command(self):
        """
        Test that detect_git_changes passes base commit to git command.

        Given: A base commit reference is provided
        When: detect_git_changes is called
        Then: Should pass base_commit to git diff command
        """
        with patch('subprocess.run') as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = ""
            mock_result.returncode = 0
            mock_run.return_value = mock_result

            detect_git_changes("HEAD~10")

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "HEAD~10" in call_args
            assert call_args == ["git", "diff", "--name-only", "HEAD~10"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
