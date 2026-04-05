#!/usr/bin/env python3
"""Tests for SessionStart_verification_cleanup.py plan file cleanup.

Tests the cleanup_old_plan_files() function to ensure:
- Files younger than threshold are NOT deleted
- Files older than threshold ARE deleted
- Subdirectories are NOT cleaned (only root *.md files)
- Windows path handling works correctly
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path for imports
HOOK_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOK_DIR))

from SessionStart_verification_cleanup import cleanup_old_plan_files


@pytest.fixture
def temp_plan_dir():
    """Create a temporary plan directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        plan_dir = Path(tmpdir) / "plans"
        plan_dir.mkdir()
        yield plan_dir


@pytest.fixture
def set_plan_dir(temp_plan_dir):
    """Fixture to patch PLAN_DIR with temp directory."""
    with patch("SessionStart_verification_cleanup.PLAN_DIR", temp_plan_dir):
        yield temp_plan_dir


class TestPlanFileCleanup:
    """Test suite for plan file cleanup functionality."""

    def test_young_files_not_deleted(self, set_plan_dir):
        """Files younger than threshold should NOT be deleted."""
        plan_dir = set_plan_dir

        # Create a young plan file (1 second old)
        young_file = plan_dir / "young-plan.md"
        young_file.write_text("# Young Plan")

        # Run cleanup with 7-day threshold
        removed = cleanup_old_plan_files(max_age_days=7)

        # File should still exist
        assert young_file.exists(), "Young file (< 7 days) should not be deleted"
        assert removed == 0, "No files should be removed"

    def test_old_files_deleted(self, set_plan_dir):
        """Files older than threshold SHOULD be deleted."""
        plan_dir = set_plan_dir

        # Create an old plan file (mock as 10 days old)
        old_file = plan_dir / "old-plan.md"
        old_file.write_text("# Old Plan")

        # Mock mtime to be 10 days ago
        old_time = time.time() - (10 * 86400)
        os.utime(old_file, (old_time, old_time))

        # Run cleanup with 7-day threshold
        removed = cleanup_old_plan_files(max_age_days=7)

        # File should be deleted
        assert not old_file.exists(), "Old file (≥ 7 days) should be deleted"
        assert removed == 1, "One file should be removed"

    def test_mixed_age_files(self, set_plan_dir):
        """Mixed age files - only old ones deleted."""
        plan_dir = set_plan_dir

        # Create young file
        young_file = plan_dir / "young-plan.md"
        young_file.write_text("# Young Plan")

        # Create old file
        old_file = plan_dir / "old-plan.md"
        old_file.write_text("# Old Plan")
        old_time = time.time() - (10 * 86400)
        os.utime(old_file, (old_time, old_time))

        # Create another young file
        young_file2 = plan_dir / "another-young.md"
        young_file2.write_text("# Another Young")

        # Run cleanup
        removed = cleanup_old_plan_files(max_age_days=7)

        # Verify: only old file deleted
        assert young_file.exists(), "Young file 1 should not be deleted"
        assert young_file2.exists(), "Young file 2 should not be deleted"
        assert not old_file.exists(), "Old file should be deleted"
        assert removed == 1, "Only one file should be removed"

    def test_subdirectories_not_cleaned(self, set_plan_dir):
        """Subdirectories should NOT be cleaned (only root *.md files)."""
        plan_dir = set_plan_dir

        # Create subdirectory with old file
        subdir = plan_dir / "abandoned"
        subdir.mkdir()
        old_subdir_file = subdir / "old-abandoned.md"
        old_subdir_file.write_text("# Old Abandoned")
        old_time = time.time() - (10 * 86400)
        os.utime(old_subdir_file, (old_time, old_time))

        # Create root old file
        old_root_file = plan_dir / "old-root.md"
        old_root_file.write_text("# Old Root")
        os.utime(old_root_file, (old_time, old_time))

        # Run cleanup
        removed = cleanup_old_plan_files(max_age_days=7)

        # Subdirectory file should still exist
        assert old_subdir_file.exists(), "Subdirectory files should not be cleaned"
        # Root file should be deleted
        assert not old_root_file.exists(), "Root old file should be deleted"
        assert removed == 1, "Only root file should be removed"

    def test_only_md_files_cleaned(self, set_plan_dir):
        """Only *.md files should be cleaned, other files ignored."""
        plan_dir = set_plan_dir

        # Create old .md file
        old_md = plan_dir / "old-plan.md"
        old_md.write_text("# Old Plan")
        old_time = time.time() - (10 * 86400)
        os.utime(old_md, (old_time, old_time))

        # Create old .json file (should be ignored)
        old_json = plan_dir / "old-plan.json"
        old_json.write_text('{"old": true}')
        os.utime(old_json, (old_time, old_time))

        # Create old .bak file (should be ignored)
        old_bak = plan_dir / "old-plan.md.bak"
        old_bak.write_text("# Backup")
        os.utime(old_bak, (old_time, old_time))

        # Run cleanup
        removed = cleanup_old_plan_files(max_age_days=7)

        # Only .md file should be deleted
        assert not old_md.exists(), "Old .md file should be deleted"
        assert old_json.exists(), ".json file should not be cleaned"
        assert old_bak.exists(), ".bak file should not be cleaned"
        assert removed == 1, "Only .md file should be removed"

    def test_empty_directory(self, set_plan_dir):
        """Empty plan directory should return 0 removed."""
        plan_dir = set_plan_dir

        # Run cleanup on empty directory
        removed = cleanup_old_plan_files(max_age_days=7)

        assert removed == 0, "Empty directory should return 0"

    def test_nonexistent_directory(self, caplog):
        """Nonexistent plan directory should return 0 removed."""
        with patch("SessionStart_verification_cleanup.PLAN_DIR", Path("/nonexistent/plans")):
            with caplog.at_level(logging.INFO):
                removed = cleanup_old_plan_files(max_age_days=7)

        assert removed == 0, "Nonexistent directory should return 0"

    def test_exactly_threshold_age(self, set_plan_dir):
        """File exactly at threshold age should be deleted."""
        plan_dir = set_plan_dir

        # Create file exactly 7 days old
        exact_file = plan_dir / "exact-threshold.md"
        exact_file.write_text("# Exact Threshold")
        # Use 7 days + 1 second to ensure it's over threshold
        exact_time = time.time() - (7 * 86400) - 1
        os.utime(exact_file, (exact_time, exact_time))

        # Run cleanup
        removed = cleanup_old_plan_files(max_age_days=7)

        # File at exact threshold should be deleted
        assert not exact_file.exists(), "File at threshold age should be deleted"
        assert removed == 1, "One file should be removed"

    def test_windows_path_handling(self, caplog):
        """Windows path handling should work correctly."""
        # Test with Windows-style path
        with patch(
            "SessionStart_verification_cleanup.PLAN_DIR", Path("C:/Users/test/.claude/plans")
        ):
            # Nonexistent Windows path should not crash
            removed = cleanup_old_plan_files(max_age_days=7)
            assert removed == 0, "Nonexistent Windows path should return 0"

    def test_logging_on_removal(self, set_plan_dir, caplog):
        """Verify logging occurs when files are removed."""
        plan_dir = set_plan_dir

        # Create old file
        old_file = plan_dir / "old-plan.md"
        old_file.write_text("# Old Plan")
        old_time = time.time() - (10 * 86400)
        os.utime(old_file, (old_time, old_time))

        # Run cleanup with logging
        with caplog.at_level(logging.INFO):
            removed = cleanup_old_plan_files(max_age_days=7)

        # Verify log entry
        assert removed == 1
        assert "old-plan.md" in caplog.text
        assert "Removed stale plan file" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
