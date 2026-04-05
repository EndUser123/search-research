"""Tests for git status checking functionality.

These tests verify the check_uncommitted_changes() function which checks
git status for session-scoped files only.
"""

import subprocess
from pathlib import Path

import pytest


def check_uncommitted_changes(session_files: list[str]) -> list[dict[str, str]]:
    """
    Check git status for only the provided session files.

    Args:
        session_files: List of file paths to check (session-scoped)

    Returns:
        List of uncommitted changes with keys: file_path, status, action
    """
    changes = []

    for file_path in session_files:
        # Skip non-existent files
        if not Path(file_path).exists():
            continue

        # Check if file has uncommitted changes using git diff --quiet
        # Exit code 1 = file has changes, Exit code 0 = no changes
        try:
            # Use git -C to run from the file's directory
            file_dir = str(Path(file_path).parent)
            result = subprocess.run(
                ["git", "-C", file_dir, "diff", "--quiet", "--", file_path],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 1:
                # File has uncommitted changes
                changes.append({
                    "file_path": file_path,
                    "status": "modified",
                    "action": "commit or stash"
                })
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Handle git timeout or git not found gracefully
            continue

    return changes


class TestCheckUncommittedChanges:
    """Test suite for check_uncommitted_changes() function."""

    def test_check_uncommitted_changes_detects_modified(self, tmp_path, git_repo):
        """
        Test that check_uncommitted_changes detects modified files.

        Given: A git repository with a modified file
        When: check_uncommitted_changes is called with the file path
        Then: Returns list containing the modified file with status info
        """
        # Arrange: Create a file and commit it
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        subprocess.run(["git", "add", "test.txt"], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )

        # Modify the file (uncommitted change)
        test_file.write_text("modified content")

        # Act: Check for uncommitted changes
        changes = check_uncommitted_changes([str(test_file)])

        # Assert: Changes detected
        assert len(changes) == 1
        assert changes[0]["file_path"] == str(test_file)
        assert changes[0]["status"] == "modified"
        assert changes[0]["action"] == "commit or stash"

    def test_check_uncommitted_changes_handles_clean(self, tmp_path, git_repo):
        """
        Test that check_uncommitted_changes returns empty list when no changes.

        Given: A git repository with clean (committed) files
        When: check_uncommitted_changes is called with file paths
        Then: Returns empty list (no uncommitted changes)
        """
        # Arrange: Create and commit a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        subprocess.run(["git", "add", "test.txt"], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )

        # Act: Check for uncommitted changes (file is clean)
        changes = check_uncommitted_changes([str(test_file)])

        # Assert: No changes detected
        assert len(changes) == 0
        assert changes == []

    def test_check_uncommitted_changes_handles_nonexistent(self, tmp_path, git_repo):
        """
        Test that check_uncommitted_changes skips non-existent files without error.

        Given: A list containing non-existent file paths
        When: check_uncommitted_changes is called
        Then: Skips non-existent files and returns changes for valid files only
        """
        # Arrange: Mix of existing and non-existent files
        existing_file = tmp_path / "exists.txt"
        existing_file.write_text("content")
        subprocess.run(["git", "add", "exists.txt"], cwd=tmp_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Add file"],
            cwd=tmp_path,
            check=True,
            capture_output=True
        )

        # Modify the existing file
        existing_file.write_text("modified")

        nonexistent_file = tmp_path / "does_not_exist.txt"

        # Act: Check for uncommitted changes
        changes = check_uncommitted_changes([
            str(existing_file),
            str(nonexistent_file)
        ])

        # Assert: Only existing file checked, non-existent skipped
        assert len(changes) == 1
        assert changes[0]["file_path"] == str(existing_file)
        assert changes[0]["status"] == "modified"


@pytest.fixture
def git_repo(tmp_path):
    """
    Fixture that creates a git repository in tmp_path.

    Initializes git repo with default config.
    """
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)

    # Configure git user
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True
    )

    yield tmp_path
