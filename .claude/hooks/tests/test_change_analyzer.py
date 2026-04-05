#!/usr/bin/env python3
"""Tests for change_analyzer module."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from change_analyzer import (
    analyze_changes,
    changelog_already_changed,
    get_cached_changes,
    is_in_merge,
    update_changelog,
)


def test_is_in_merge_no_repo() -> None:
    """Test is_in_merge with non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = is_in_merge(Path(tmpdir))
        assert result is False, "Should return False for non-git directory"


def test_get_cached_changes_no_repo() -> None:
    """Test get_cached_changes with non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = get_cached_changes(Path(tmpdir))
        assert result == [], "Should return empty list for non-git directory"


def test_analyze_changes_no_repo() -> None:
    """Test analyze_changes with non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = analyze_changes(Path(tmpdir))
        # Should return default dict when no changes
        assert result.get("notable") is False


def test_changelog_already_changed_no_repo() -> None:
    """Test changelog_already_changed with non-git directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = changelog_already_changed(Path(tmpdir))
        assert result is False


def test_update_changelog_empty_entry() -> None:
    """Test update_changelog with empty entry."""
    with tempfile.TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        result = update_changelog(Path(tmpdir), {"Added": [], "Changed": [], "Removed": [], "Fixed": []}, changelog_path)
        assert result is False, "Should return False for empty entry"


def test_update_changelog_creates_file() -> None:
    """Test update_changelog creates new file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        entry = {
            "Added": ["test.py: new file"],
            "Changed": [],
            "Removed": [],
            "Fixed": []
        }
        result = update_changelog(Path(tmpdir), entry, changelog_path)
        assert result is True
        assert changelog_path.exists()
        content = changelog_path.read_text()
        assert "test.py: new file" in content
        assert "### Added" in content  # Has category header


def test_update_changelog_preserves_frontmatter() -> None:
    """Test update_changelog preserves YAML frontmatter."""
    with tempfile.TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        # Create file with frontmatter
        changelog_path.write_text("---\ndoc_type: changelog\n---\n\n# Existing content\n")
        entry = {
            "Added": ["new feature"],
            "Changed": [],
            "Removed": [],
            "Fixed": []
        }
        result = update_changelog(Path(tmpdir), entry, changelog_path)
        assert result is True
        content = changelog_path.read_text()
        assert content.startswith("---\ndoc_type: changelog\n---")
        assert "new feature" in content


def test_update_changelog_append_to_unreleased() -> None:
    """Test update_changelog appends to [Unreleased] section."""
    with tempfile.TemporaryDirectory() as tmpdir:
        changelog_path = Path(tmpdir) / "CHANGELOG.md"
        changelog_path.write_text("## [Unreleased]\n\nExisting content\n")
        entry = {
            "Added": ["new feature"],
            "Changed": [],
            "Removed": [],
            "Fixed": []
        }
        result = update_changelog(Path(tmpdir), entry, changelog_path)
        assert result is True
        content = changelog_path.read_text()
        assert "## [Unreleased]" in content
        assert "new feature" in content


if __name__ == "__main__":
    print("Running change_analyzer tests...")
    test_is_in_merge_no_repo()
    print("✓ test_is_in_merge_no_repo")
    test_get_cached_changes_no_repo()
    print("✓ test_get_cached_changes_no_repo")
    test_analyze_changes_no_repo()
    print("✓ test_analyze_changes_no_repo")
    test_changelog_already_changed_no_repo()
    print("✓ test_changelog_already_changed_no_repo")
    test_update_changelog_empty_entry()
    print("✓ test_update_changelog_empty_entry")
    test_update_changelog_creates_file()
    print("✓ test_update_changelog_creates_file")
    test_update_changelog_preserves_frontmatter()
    print("✓ test_update_changelog_preserves_frontmatter")
    test_update_changelog_append_to_unreleased()
    print("✓ test_update_changelog_append_to_unreleased")
    print("\nAll tests passed!")
