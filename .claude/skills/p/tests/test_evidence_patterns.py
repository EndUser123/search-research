#!/usr/bin/env python3
"""
Tests for evidence_patterns.py module.

Tests the shared evidence detection patterns used by Stop hooks.
"""

import re
import sys
from pathlib import Path

import pytest

# Add lib directory to path
LIB_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from evidence_patterns import (
    EXECUTION_EVIDENCE_PATTERNS,
    FABRICATION_PATTERNS,
    MIN_BOX_DRAWING_CHARS,
    check_execution_evidence,
    get_fabrication_error_message,
    has_heavy_tables,
)


class TestCheckExecutionEvidence:
    """Test execution evidence detection."""

    def test_no_evidence_returns_false(self):
        """Text without execution evidence should return False."""
        text = "This is just plain text with no tool output"
        has_ev, patterns = check_execution_evidence(text)
        assert has_ev is False
        assert len(patterns) == 0

    def test_pytest_output_counts_as_evidence(self):
        """Pytest output should be detected as evidence."""
        text = "pytest collected 42 items\\n22 PASSED, 1 FAILED"
        has_ev, patterns = check_execution_evidence(text)
        assert has_ev is True
        assert len(patterns) >= 2

    def test_git_commands_count_as_evidence(self):
        """Git commands should be detected as evidence."""
        text = "git status\\ngit branch -a\\nexit code: 0\\npytest PASSED"
        has_ev, patterns = check_execution_evidence(text)
        assert has_ev is True
        assert len(patterns) >= 3

    def test_tool_call_references_count_as_evidence(self):
        """Tool call references should be detected as evidence."""
        text = "Called Read(file.txt) and Glob(**/*.py)\\nBash completed\\npytest PASSED 3 tests"
        has_ev, patterns = check_execution_evidence(text)
        assert has_ev is True
        assert len(patterns) >= 3

    def test_requires_three_distinct_patterns(self):
        """Need at least 2 distinct evidence indicators OR tool calls."""
        # Only 1 pattern, no tool calls - should fail
        text = "pytest output"
        has_ev, patterns = check_execution_evidence(text)
        assert has_ev is False
        # Only 1 pattern matched
        assert len(patterns) >= 1  # 'pytest'

        # 2+ patterns - should pass
        text = "pytest collected 10 items\\ngit status"
        has_ev, patterns = check_execution_evidence(text)
        assert has_ev is True
        assert len(patterns) >= 2


class TestHasHeavyTables:
    """Test heavy table formatting detection."""

    def test_no_tables_returns_false(self):
        """Text without box-drawing characters should return False."""
        text = "This is plain text without tables"
        assert has_heavy_tables(text) is False

    def test_few_box_drawing_returns_false(self):
        """Fewer than MIN_BOX_DRAWING_CHARS should return False."""
        # Only 5 characters
        text = "┌─┐└"
        assert has_heavy_tables(text) is False

    def test_heavy_tables_returns_true(self):
        """10+ box-drawing characters should return True."""
        text = "┌────────┬─────────┐"
        assert has_heavy_tables(text) is True

    def test_complex_table_returns_true(self):
        """Complex ASCII table should be detected."""
        text = """
┌──────────┬─────────┬──────────┐
│ Column 1 │ Column 2│ Column 3 │
├──────────┼─────────┼──────────┤
│ Data 1   │ Data 2  │ Data 3   │
└──────────┴─────────┴──────────┘
        """.strip()
        assert has_heavy_tables(text) is True


class TestFabricationErrorMessage:
    """Test fabrication error message generation."""

    def test_error_message_is_consistent(self):
        """Error message should be consistent across calls."""
        msg1 = get_fabrication_error_message()
        msg2 = get_fabrication_error_message()
        assert msg1 == msg2

    def test_error_message_contains_key_phrases(self):
        """Error message should mention required phrases."""
        msg = get_fabrication_error_message()
        assert "FABRICATION DETECTED" in msg
        assert "formatted tables" in msg
        assert "real tool execution" in msg
        assert "Task/Bash tools" in msg


class TestModuleConstants:
    """Test module-level constants."""

    def test_min_box_drawing_chars_value(self):
        """MIN_BOX_DRAWING_CHARS should be 10."""
        assert MIN_BOX_DRAWING_CHARS == 10

    def test_execution_evidence_patterns_not_empty(self):
        """EXECUTION_EVIDENCE_PATTERNS should not be empty."""
        assert len(EXECUTION_EVIDENCE_PATTERNS) > 0

    def test_fabrication_patterns_not_empty(self):
        """FABRICATION_PATTERNS should not be empty."""
        assert len(FABRICATION_PATTERNS) > 0

    def test_fabrication_pattern_uses_constant(self):
        """FABRICATION_PATTERNS should use MIN_BOX_DRAWING_CHARS."""
        # The pattern should reference MIN_BOX_DRAWING_CHARS
        pattern = FABRICATION_PATTERNS[0]
        # Handle both string and pre-compiled Pattern objects
        pattern_str = pattern.pattern if hasattr(pattern, 'pattern') else str(pattern)
        assert str(MIN_BOX_DRAWING_CHARS) in pattern_str


class TestRegexPrecompilation:
    """Test P1-001: Regex injection risk - patterns should be pre-compiled."""

    def test_fabrication_pattern_is_precompiled(self):
        """FABRICATION_PATTERNS[0] should be a compiled regex Pattern object.

        This test prevents regex injection risks by ensuring the pattern is
        compiled at module load time rather than built on each call via f-string.

        Given: The module has been imported
        When: We check the type of FABRICATION_PATTERNS[0]
        Then: It should be a compiled re.Pattern object, not a string
        """
        # This will FAIL until the pattern is pre-compiled
        assert isinstance(FABRICATION_PATTERNS[0], re.Pattern), (
            "FABRICATION_PATTERNS[0] should be pre-compiled as re.Pattern "
            "to prevent regex injection and improve performance"
        )

    def test_fabrication_pattern_works_correctly(self):
        """Pre-compiled pattern should still detect heavy tables correctly.

        Given: A pre-compiled regex pattern
        When: Used to search for box-drawing characters
        Then: It should correctly identify heavy table formatting
        """
        # Test with valid box-drawing input
        heavy_table_text = "┌────────┬─────────┐"
        assert FABRICATION_PATTERNS[0].search(heavy_table_text) is not None

        # Test with insufficient box-drawing characters
        light_table_text = "┌─┐"
        assert FABRICATION_PATTERNS[0].search(light_table_text) is None

    def test_has_heavy_tables_uses_precompiled_pattern(self):
        """has_heavy_tables() should use the pre-compiled pattern efficiently.

        Given: The has_heavy_tables() function
        When: Called multiple times
        Then: It should use the pre-compiled pattern (not rebuild on each call)

        Note: This is a behavioral test - the function should work correctly
        regardless of implementation, but performance testing could verify
        no recompilation occurs.
        """
        # Test basic functionality
        assert has_heavy_tables("┌────────────────┬───────────┐") is True
        assert has_heavy_tables("plain text") is False

        # Test edge case: exactly at threshold
        threshold_text = "┌─────────┐"  # Exactly MIN_BOX_DRAWING_CHARS
        assert has_heavy_tables(threshold_text) is True

    def test_precompiled_pattern_catches_injection_attempts(self):
        """Pre-compiled pattern should be safe from regex injection.

        Given: A pre-compiled regex pattern
        When: Malicious input contains regex metacharacters
        Then: They should be treated as literals, not regex commands

        This test documents the security benefit of pre-compilation.
        """
        # Input that might be dangerous if pattern were built with f-string
        dangerous_input = ".*.*.*.*.*.*.*.*.*.*"  # 10+ dots (like regex wildcard)
        # Safe: dots are treated as literal dots, not "any character"
        result = FABRICATION_PATTERNS[0].search(dangerous_input)
        assert result is None  # Should NOT match - dots aren't box-drawing chars


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
