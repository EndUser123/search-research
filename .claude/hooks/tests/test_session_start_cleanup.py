#!/usr/bin/env python3
"""
Tests for SessionStart state cleanup functionality.

Feature: SessionStart hook should clean stale state files older than 2 hours.

These tests VERIFY the requested behavior:
1. Old state files (>2 hours) are deleted
2. New state files (<2 hours) are NOT deleted
3. Cleanup function handles errors gracefully
"""

from __future__ import annotations

import json

# Add hooks dir to path
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestSessionStartStateCleanup:
    """Tests for SessionStart state cleanup of stale files."""

    @pytest.fixture
    def state_dir(self):
        """Temporary directory for state files."""
        with tempfile.TemporaryDirectory() as tmp:
            yield Path(tmp)

    @pytest.fixture
    def cleanup_func(self):
        """
        Import the cleanup function from SessionStart_checkpoint_restore.

        NOTE: cleanup_stale_state_files exists in SessionStart_checkpoint_restore.py
        which is imported from hooks directory, not handoff package.
        """
        from SessionStart_checkpoint_restore import cleanup_stale_state_files
        return cleanup_stale_state_files

    def test_old_state_file_is_deleted(self, state_dir, cleanup_func):
        """
        Test that state files older than 2 hours are deleted.

        Given: A state file older than 2 hours exists
        When: cleanup_stale_state_files is called
        Then: The old state file is deleted
        """
        # Arrange - create a state file older than 2 hours
        old_file = state_dir / "old_state.json"
        old_data = {"test": "old data", "timestamp": "2025-01-01T00:00:00Z"}
        old_file.write_text(json.dumps(old_data))

        # Set file modification time to 3 hours ago
        old_time = datetime.now(UTC) - timedelta(hours=3)
        import os
        os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))

        # Verify file exists before cleanup
        assert old_file.exists()

        # Act - run cleanup
        deleted_count = cleanup_func(state_dir, max_age_hours=2)

        # Assert - file should be deleted
        assert not old_file.exists(), "Old state file should be deleted"
        assert deleted_count >= 1, "Should report at least 1 deletion"

    def test_new_state_file_is_not_deleted(self, state_dir, cleanup_func):
        """
        Test that state files newer than 2 hours are NOT deleted.

        Given: A state file newer than 2 hours exists
        When: cleanup_stale_state_files is called
        Then: The new state file is NOT deleted
        """
        # Arrange - create a state file newer than 2 hours
        new_file = state_dir / "new_state.json"
        new_data = {"test": "new data", "timestamp": datetime.now(UTC).isoformat()}
        new_file.write_text(json.dumps(new_data))

        # File is already new (current time), no need to modify mtime

        # Verify file exists before cleanup
        assert new_file.exists()

        # Act - run cleanup
        deleted_count = cleanup_func(state_dir, max_age_hours=2)

        # Assert - file should NOT be deleted
        assert new_file.exists(), "New state file should NOT be deleted"
        # The count might be 0 or more depending on other files
        assert deleted_count >= 0

    def test_mixed_old_and_new_files(self, state_dir, cleanup_func):
        """
        Test cleanup with both old and new state files.

        Given: Multiple state files with varying ages (>2h and <2h)
        When: cleanup_stale_state_files is called
        Then: Only old files are deleted, new files preserved
        """
        # Arrange - create multiple state files with different ages
        files = {}

        # Old files (should be deleted)
        for i in range(3):
            old_file = state_dir / f"old_state_{i}.json"
            old_file.write_text(json.dumps({"index": i, "type": "old"}))
            old_time = datetime.now(UTC) - timedelta(hours=3 + i)
            import os
            os.utime(old_file, (old_time.timestamp(), old_time.timestamp()))
            files[f"old_{i}"] = old_file

        # New files (should be preserved)
        for i in range(2):
            new_file = state_dir / f"new_state_{i}.json"
            new_file.write_text(json.dumps({"index": i, "type": "new"}))
            files[f"new_{i}"] = new_file

        # Verify all files exist before cleanup
        for name, path in files.items():
            assert path.exists(), f"File {name} should exist before cleanup"

        # Act - run cleanup
        deleted_count = cleanup_func(state_dir, max_age_hours=2)

        # Assert - only old files deleted
        for i in range(3):
            old_file = files[f"old_{i}"]
            assert not old_file.exists(), f"Old file old_{i} should be deleted"

        for i in range(2):
            new_file = files[f"new_{i}"]
            assert new_file.exists(), f"New file new_{i} should be preserved"

        assert deleted_count == 3, "Should report exactly 3 deletions"

    def test_cleanup_handles_nonexistent_directory(self, cleanup_func):
        """
        Test that cleanup handles nonexistent directory gracefully.

        Given: A directory path that doesn't exist
        When: cleanup_stale_state_files is called
        Then: Function returns 0 (no errors, no deletions)
        """
        # Arrange - path to nonexistent directory
        nonexistent = Path("/tmp/this_does_not_exist_12345")

        # Act - run cleanup
        deleted_count = cleanup_func(nonexistent, max_age_hours=2)

        # Assert - should not raise error
        assert deleted_count == 0, "Should report 0 deletions for nonexistent directory"

    def test_cleanup_with_boundary_age_file(self, state_dir, cleanup_func):
        """
        Test cleanup behavior with file exactly at 2 hour boundary.

        Given: A state file exactly 2 hours old
        When: cleanup_stale_state_files is called with max_age_hours=2
        Then: File behavior is defined (deleted or preserved consistently)
        """
        # Arrange - create file exactly 2 hours old
        boundary_file = state_dir / "boundary_state.json"
        boundary_file.write_text(json.dumps({"test": "boundary"}))

        boundary_time = datetime.now(UTC) - timedelta(hours=2)
        import os
        os.utime(boundary_file, (boundary_time.timestamp(), boundary_time.timestamp()))

        # Act - run cleanup
        deleted_count = cleanup_func(state_dir, max_age_hours=2)

        # Assert - verify consistent behavior
        # Either the file is deleted (older than threshold) OR preserved (at threshold)
        # Either is acceptable as long as it's consistent
        assert deleted_count in [0, 1], "Should report 0 or 1 deletion"

    def test_cleanup_default_max_age(self, state_dir, cleanup_func):
        """
        Test cleanup with default max age (2 hours).

        Given: State files of various ages
        When: cleanup_stale_state_files is called without max_age_hours
        Then: Uses default of 2 hours
        """
        # Arrange - create files at different ages
        very_old = state_dir / "very_old.json"
        very_old.write_text(json.dumps({"age": "5 hours"}))
        very_old_time = datetime.now(UTC) - timedelta(hours=5)
        import os
        os.utime(very_old, (very_old_time.timestamp(), very_old_time.timestamp()))

        # Act - run cleanup with default max_age
        deleted_count = cleanup_func(state_dir)  # No max_age_hours specified

        # Assert - 5 hour old file should be deleted
        assert not very_old.exists(), "5 hour old file should be deleted with default max_age"
        assert deleted_count >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
