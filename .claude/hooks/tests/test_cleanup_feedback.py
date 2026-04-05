#!/usr/bin/env python3
"""Tests for cleanup.py feedback loop pattern analysis.

Tests analyze_feedback_patterns() via direct function import.
"""

import sys
from pathlib import Path

import pytest

# Path to the cleanup script under test
CLEANUP_PATH = Path(__file__).resolve().parents[2] / "skills" / "cleanup" / "scripts" / "cleanup.py"

# Import from cleanup module directly
sys.path.insert(0, str(CLEANUP_PATH.parent))
from cleanup import (
    _categorize_violation,
    _infer_purpose,
    _infer_suggested_location,
    analyze_feedback_patterns,
)


class TestCategorizeViolation:
    """Unit tests for _categorize_violation helper."""

    def test_dotfile_with_leading_dot(self):
        """DOTFILE_VIOLATION for .env returns dotfile category."""
        violation = {"type": "DOTFILE_VIOLATION", "path": "/root/.env"}
        category_key, _ = _categorize_violation(violation)
        assert category_key == "DOTFILE:.env"

    def test_dotfile_without_leading_dot(self):
        """DOTFILE_VIOLATION for vimrc returns dotfile category with glob."""
        violation = {"type": "DOTFILE_VIOLATION", "path": "/root/vimrc"}
        category_key, pattern = _categorize_violation(violation)
        assert category_key == "DOTFILE:vimrc"
        assert pattern == "*vimrc"

    def test_unknown_config_file(self):
        """UNKNOWN_CONFIG_FILE returns CONFIG: prefix."""
        violation = {"type": "UNKNOWN_CONFIG_FILE", "path": "/root/config.toml"}
        category_key, pattern = _categorize_violation(violation)
        assert category_key == "CONFIG:config.toml"
        assert pattern == "config.toml"

    def test_worktree_at_root(self):
        """WORKTREE_AT_ROOT returns proper category."""
        violation = {"type": "WORKTREE_AT_ROOT", "path": "/root/worktrees/feature-x"}
        category_key, pattern = _categorize_violation(violation)
        assert "WORKTREE" in category_key
        assert "*feature-x*" in pattern

    def test_ai_generated(self):
        """AI_GENERATED returns AI_GEN: prefix."""
        violation = {"type": "AI_GENERATED", "path": "/root/.claude/hooks/generated.py"}
        category_key, _ = _categorize_violation(violation)
        assert "AI_GEN" in category_key

    def test_backup_file(self):
        """BACKUP_FILE returns proper category."""
        violation = {"type": "BACKUP_FILE", "path": "/root/script.py.bak"}
        category_key, pattern = _categorize_violation(violation)
        assert "BACKUP" in category_key
        assert "*.bak" in pattern

    def test_empty_path_unknown_type(self):
        """UNKNOWN type with no path returns unknown category."""
        violation = {"type": "UNKNOWN", "path": ""}
        category_key, pattern = _categorize_violation(violation)
        assert "unknown" in category_key.lower()
        assert pattern == ""


class TestInferPurpose:
    """Unit tests for _infer_purpose helper."""

    def test_dotfile_purpose(self):
        """DOTFILE category returns purpose with 'Dotfile'."""
        purpose = _infer_purpose("DOTFILE:.env", ".env")
        assert "Dotfile" in purpose or "dotfile" in purpose.lower()

    def test_backup_purpose(self):
        """BACKUP category returns purpose with 'Backup'."""
        purpose = _infer_purpose("BACKUP:*.bak", "script.py.bak")
        assert "backup" in purpose.lower()


class TestInferSuggestedLocation:
    """Unit tests for _infer_suggested_location helper."""

    def test_dotfile_suggests_dotclaude(self):
        """DOTFILE suggests .claude/ directory."""
        location = _infer_suggested_location("DOTFILE:.env", ".env")
        assert ".claude" in location

    def test_backup_suggests_backups(self):
        """BACKUP_FILE suggests .claude/backups/ directory."""
        location = _infer_suggested_location("BACKUP:*.bak", "script.py.bak")
        assert "backup" in location.lower()


class TestAnalyzeFeedbackPatterns:
    """Integration tests for analyze_feedback_patterns main function."""

    def test_no_violations_returns_empty(self):
        """Empty violation list returns empty suggestions."""
        result = analyze_feedback_patterns([])
        assert result == []

    def test_single_violation_below_threshold(self):
        """Single violation below threshold returns no suggestion."""
        violations = [{"type": "DOTFILE_VIOLATION", "path": "/root/.env"}]
        result = analyze_feedback_patterns(violations, threshold=3)
        assert result == []

    def test_same_dotfile_three_times_generates_suggestion(self):
        """Same dotfile appearing 3 times generates a suggestion."""
        violations = [
            {"type": "DOTFILE_VIOLATION", "path": "/root/.env"},
            {"type": "DOTFILE_VIOLATION", "path": "/home/user/.env"},
            {"type": "DOTFILE_VIOLATION", "path": "/project/.env"},
        ]
        result = analyze_feedback_patterns(violations, threshold=3)
        assert len(result) == 1
        # Check suggestion has expected fields (pattern, purpose, max_age_days, auto_cleanup, suggested_location)
        suggestion = result[0]
        assert suggestion["pattern"] == ".env"
        assert "purpose" in suggestion
        assert "max_age_days" in suggestion
        assert suggestion["auto_cleanup"] is True

    def test_different_dotfiles_no_aggregation(self):
        """Different dotfiles don't aggregate into a single suggestion."""
        violations = [
            {"type": "DOTFILE_VIOLATION", "path": "/root/.env"},
            {"type": "DOTFILE_VIOLATION", "path": "/root/.gitconfig"},
            {"type": "DOTFILE_VIOLATION", "path": "/root/.npmrc"},
        ]
        result = analyze_feedback_patterns(violations, threshold=3)
        # Each dotfile is a different category, none meet threshold
        assert result == []

    def test_suggestion_has_required_fields(self):
        """Suggestion contains all required fields."""
        violations = [
            {"type": "DOTFILE_VIOLATION", "path": "/root/.env"},
            {"type": "DOTFILE_VIOLATION", "path": "/home/user/.env"},
            {"type": "DOTFILE_VIOLATION", "path": "/project/.env"},
        ]
        result = analyze_feedback_patterns(violations, threshold=3)
        suggestion = result[0]
        assert "pattern" in suggestion
        assert "purpose" in suggestion
        assert "max_age_days" in suggestion
        assert "auto_cleanup" in suggestion
        assert "suggested_location" in suggestion

    def test_max_age_days_for_dotfile(self):
        """Dotfile suggestion has max_age_days of 7."""
        violations = [
            {"type": "DOTFILE_VIOLATION", "path": "/root/.env"},
            {"type": "DOTFILE_VIOLATION", "path": "/home/user/.env"},
            {"type": "DOTFILE_VIOLATION", "path": "/project/.env"},
        ]
        result = analyze_feedback_patterns(violations, threshold=3)
        assert result[0]["max_age_days"] == 7

    def test_empty_patterns_skipped(self):
        """Patterns that resolve to empty strings are skipped."""
        violations = [
            {"type": "UNKNOWN", "path": ""},
            {"type": "UNKNOWN", "path": ""},
            {"type": "UNKNOWN", "path": ""},
        ]
        result = analyze_feedback_patterns(violations, threshold=3)
        assert result == []

    def test_custom_threshold_2(self):
        """Custom threshold of 2 generates suggestion with 2 occurrences."""
        violations = [
            {"type": "DOTFILE_VIOLATION", "path": "/root/.env"},
            {"type": "DOTFILE_VIOLATION", "path": "/home/user/.env"},
        ]
        result = analyze_feedback_patterns(violations, threshold=2)
        assert len(result) == 1
        assert result[0]["pattern"] == ".env"

    def test_backup_file_pattern(self):
        """BACKUP_FILE violation type generates proper category."""
        violations = [
            {"type": "BACKUP_FILE", "path": "/root/script.py.bak"},
            {"type": "BACKUP_FILE", "path": "/root/old.py.bak"},
            {"type": "BACKUP_FILE", "path": "/root/test.py.bak"},
        ]
        result = analyze_feedback_patterns(violations, threshold=3)
        # All .bak files share the same suffix category
        assert len(result) >= 1

    def test_session_debris_with_matched_pattern(self):
        """session-*.json with matched_pattern detected and assigned short max_age."""
        violations = [
            {
                "type": "AI_GENERATED",
                "matched_pattern": "session-*.json",
                "path": "P:/session-abc.json",
            },
            {
                "type": "AI_GENERATED",
                "matched_pattern": "session-*.json",
                "path": "P:/session-xyz.json",
            },
            {
                "type": "AI_GENERATED",
                "matched_pattern": "session-*.json",
                "path": "P:/session-123.json",
            },
        ]
        result = analyze_feedback_patterns(violations, threshold=3)
        assert len(result) >= 1
        # Session debris should have short max_age_days (1)
        suggestion = result[0]
        assert suggestion.get("max_age_days", 0) <= 1


class TestAnalyzeFeedbackPatternsIntegration:
    """Integration tests matching real-world usage patterns."""

    def test_dotfile_accumulation_scenario(self):
        """User repeatedly creates .env files that get flagged."""
        violations = [
            {"type": "DOTFILE_VIOLATION", "path": "P:/.coverage"},
            {"type": "DOTFILE_VIOLATION", "path": "P:/old_coverage"},
            {"type": "DOTFILE_VIOLATION", "path": "P:/temp/.coverage"},
        ]
        # These are different filenames so won't aggregate
        result = analyze_feedback_patterns(violations, threshold=3)
        assert isinstance(result, list)

    def test_real_world_session_debris(self):
        """Session debris files with same matched_pattern should be detected."""
        violations = [
            {
                "type": "AI_GENERATED",
                "matched_pattern": "session-*.json",
                "path": "P:/session-abc.json",
            },
            {
                "type": "AI_GENERATED",
                "matched_pattern": "session-*.json",
                "path": "P:/session-xyz.json",
            },
            {
                "type": "AI_GENERATED",
                "matched_pattern": "session-*.json",
                "path": "P:/session-123.json",
            },
        ]
        result = analyze_feedback_patterns(violations, threshold=3)
        assert len(result) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
