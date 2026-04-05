"""Tests for error_attribution_tracker.py Data Source Filtering (Change A).

These tests verify that EXCLUDED_PATTERNS prevents false positives from
historical session data files like session_ledger.json.

Feature: Add EXCLUDED_PATTERNS list to skip pattern matching on historical
session data files. This prevents the error attribution tracker from incorrectly
attributing errors to hook code when the error actually comes from reading
historical session data files.

Requirements verified:
1. EXCLUDED_PATTERNS = ["session_ledger.json", "/data/session_", "/logs/", "/.claude/data/"]
2. In process() method, check tool_input["file_path"] against EXCLUDED_PATTERNS
3. If file_path matches any excluded pattern, return {"passed": True, "skipped": True, "reason": "historical_data"}
4. This prevents false positives from session_ledger.json

Run with:
    pytest P:/.claude/hooks/repositories/tests/test_error_attribution_data_source_filter.py -v

TDD RED Phase: Tests are expected to FAIL because the EXCLUDED_PATTERNS
feature does not exist yet in error_attribution_tracker.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add repositories directory to path for imports
_repo_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_repo_path))

# Also add posttooluse directory to path for importing the hook
_posttooluse_path = Path(__file__).resolve().parent.parent.parent / "posttooluse"
sys.path.insert(0, str(_posttooluse_path))


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def _import_error_attribution_tracker():
    """Import error_attribution_tracker module, raising ImportError if not found.

    Returns:
        ErrorAttributionTracker class

    Raises:
        ImportError: If error_attribution_tracker module doesn't exist yet
    """
    try:
        from error_attribution_tracker import ErrorAttributionTracker

        return ErrorAttributionTracker
    except ImportError as e:
        raise ImportError(
            f"error_attribution_tracker module not found: {e}"
            "\nThis is expected in RED phase - feature will be added in GREEN phase."
        )


# ============================================================================
# TEST CLASS: Excluded Pattern - session_ledger.json
# ============================================================================


class TestExcludedSessionLedgerJson:
    """Tests for excluding session_ledger.json files from error attribution."""

    def test_excluded_session_ledger_json_returns_skipped(self) -> None:
        """Verify file_path containing 'session_ledger.json' returns skipped result.

        Given: A file_path that contains 'session_ledger.json'
        When: The process() method is called with this file_path
        Then:
            - Result contains "skipped": True
            - Result contains "reason": "historical_data"
            - Result contains "passed": True
            - No error attribution is performed

        This prevents false positives when reading historical session ledger
        files that may contain error-like patterns from previous sessions.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        tool_input = {"file_path": "P:/.claude/data/session_ledger.json"}
        tool_response = {"output": "Some content with error-like patterns"}

        # Act
        result = tracker.process(
            tool_name="Read", tool_input=tool_input, tool_response=tool_response
        )

        # Assert - Should return skipped result
        assert (
            result.get("skipped") is True
        ), "Result should contain 'skipped': True for session_ledger.json files"
        assert (
            result.get("reason") == "historical_data"
        ), "Result should contain 'reason': 'historical_data'"
        assert (
            result.get("passed") is True
        ), "Result should contain 'passed': True (allowing operation to proceed)"
        assert "injection" not in result, "Result should NOT contain 'injection' for excluded files"

    def test_excluded_session_ledger_json_nested_path(self) -> None:
        """Verify session_ledger.json in nested paths is also excluded.

        Given: A file_path with 'session_ledger.json' in a nested directory
        When: The process() method is called
        Then: Returns skipped result regardless of path depth

        This ensures exclusion works for session_ledger.json at any
        directory level (e.g., backups/session_ledger.json, data/old/session_ledger.json).
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        nested_paths = [
            "P:/.claude/data/backups/session_ledger.json",
            "P:/.claude/data/archive/old/session_ledger.json",
            "P:/backups/session_ledger.json",
        ]

        for file_path in nested_paths:
            tool_input = {"file_path": file_path}
            tool_response = {"output": "Content"}

            # Act
            result = tracker.process(
                tool_name="Read", tool_input=tool_input, tool_response=tool_response
            )

            # Assert
            assert result.get("skipped") is True, f"Nested path {file_path} should be excluded"
            assert result.get("reason") == "historical_data"


# ============================================================================
# TEST CLASS: Excluded Pattern - /data/session_
# ============================================================================


class TestExcludedDataSession:
    """Tests for excluding /data/session_ pattern files."""

    def test_excluded_data_session_pattern(self) -> None:
        """Verify file_path containing '/data/session_' returns skipped result.

        Given: A file_path that contains '/data/session_' pattern
        When: The process() method is called
        Then: Returns skipped result with reason "historical_data"

        This prevents false positives from historical session data files
        that may be stored in session-specific files (e.g., session_abc123.json).
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        test_paths = [
            "P:/.claude/data/session_abc123.json",
            "P:/.claude/data/session_xyz789/data.json",
            "P:/data/session_backup/data.json",
        ]

        for file_path in test_paths:
            tool_input = {"file_path": file_path}
            tool_response = {"output": "Session data content"}

            # Act
            result = tracker.process(
                tool_name="Read", tool_input=tool_input, tool_response=tool_response
            )

            # Assert
            assert (
                result.get("skipped") is True
            ), f"File {file_path} with /data/session_ pattern should be excluded"
            assert result.get("reason") == "historical_data"

    def test_session_pattern_variations(self) -> None:
        """Verify various session_ file patterns are excluded.

        Given: Different variations of session_ pattern in paths
        When: The process() method is called
        Then: All variations return skipped result

        Test cases include different extensions and path structures.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        session_paths = [
            "P:/.claude/data/session_20250101.json",
            "P:/.claude/data/session_active/data.txt",
            "P:/.claude/data/session_error.log",
        ]

        for file_path in session_paths:
            tool_input = {"file_path": file_path}
            tool_response = {"output": "Content"}

            # Act
            result = tracker.process(
                tool_name="Read", tool_input=tool_input, tool_response=tool_response
            )

            # Assert
            assert result.get("skipped") is True, f"Session file {file_path} should be excluded"


# ============================================================================
# TEST CLASS: Excluded Pattern - /logs/
# ============================================================================


class TestExcludedLogs:
    """Tests for excluding /logs/ directory pattern."""

    def test_excluded_logs_pattern(self) -> None:
        """Verify file_path containing '/logs/' returns skipped result.

        Given: A file_path that contains '/logs/' directory pattern
        When: The process() method is called
        Then: Returns skipped result with reason "historical_data"

        This prevents false positives from log files that may contain
        historical error messages or stack traces from previous sessions.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        log_paths = [
            "P:/.claude/logs/error.log",
            "P:/.claude/logs/hook_activity.jsonl",
            "P:/logs/application.log",
            "P:/projects/xyz/logs/debug.log",
        ]

        for file_path in log_paths:
            tool_input = {"file_path": file_path}
            tool_response = {"output": "Log content with errors"}

            # Act
            result = tracker.process(
                tool_name="Read", tool_input=tool_input, tool_response=tool_response
            )

            # Assert
            assert result.get("skipped") is True, f"Log file {file_path} should be excluded"
            assert result.get("reason") == "historical_data"


# ============================================================================
# TEST CLASS: Excluded Pattern - /.claude/data/
# ============================================================================


class TestExcludedClaudeData:
    """Tests for excluding /.claude/data/ directory pattern."""

    def test_excluded_claude_data_pattern(self) -> None:
        """Verify file_path containing '/.claude/data/' returns skipped result.

        Given: A file_path that contains '/.claude/data/' directory pattern
        When: The process() method is called
        Then: Returns skipped result with reason "historical_data"

        This prevents false positives from Claude's internal data directory
        which stores historical session information, state files, and other
        non-error-source data that may contain error-like patterns.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        claude_data_paths = [
            "P:/.claude/data/state.json",
            "P:/.claude/data/cache/results.json",
            "P:/.claude/data/historical/session_info.json",
        ]

        for file_path in claude_data_paths:
            tool_input = {"file_path": file_path}
            tool_response = {"output": "Data content"}

            # Act
            result = tracker.process(
                tool_name="Read", tool_input=tool_input, tool_response=tool_response
            )

            # Assert
            assert result.get("skipped") is True, f"Claude data file {file_path} should be excluded"
            assert result.get("reason") == "historical_data"


# ============================================================================
# TEST CLASS: Normal Files Not Excluded
# ============================================================================


class TestNormalFileNotExcluded:
    """Tests for normal files that should be processed normally."""

    def test_normal_error_file_processed(self) -> None:
        """Verify normal files with error content are processed normally.

        Given: A normal file_path (not matching any excluded pattern)
        And: Tool response contains error indicators
        When: The process() method is called
        Then:
            - Result does NOT contain "skipped"
            - Error attribution is performed
            - Injection is included in result

        This ensures normal error handling continues to work for
        actual errors from tool execution.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        tool_input = {
            "file_path": "P:/projects/myapp/src/main.py"  # Normal file path
        }
        tool_response = {
            "output": "[python .claude/hooks/skill_enforcement_gate.py] Error: Skill not found"
        }

        # Act
        result = tracker.process(
            tool_name="Bash", tool_input=tool_input, tool_response=tool_response
        )

        # Assert - Should process normally, not skip
        assert (
            "skipped" not in result or result.get("skipped") is False
        ), "Normal files should NOT be skipped"
        assert result.get("passed") is True, "Result should have 'passed': True"
        assert "injection" in result, "Normal error files should have error attribution injection"
        assert "metadata" in result, "Normal error files should have metadata"

    def test_normal_hook_error_processed(self) -> None:
        """Verify hook error files are processed normally.

        Given: A file_path pointing to a hook file
        And: Tool response contains hook error message
        When: The process() method is called
        Then: Error attribution is performed (not skipped)

        This ensures actual hook errors are still attributed correctly.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        tool_input = {"file_path": "P:/.claude/hooks/pretooluse_tdd_gate.py"}
        tool_response = {"output": "PreToolUse:Bash hook error - TDD compliance required"}

        # Act
        result = tracker.process(
            tool_name="Bash", tool_input=tool_input, tool_response=tool_response
        )

        # Assert - Should process, not skip
        assert (
            "skipped" not in result or result.get("skipped") is False
        ), "Hook files should NOT be skipped (different from data files)"
        assert "injection" in result, "Hook errors should have attribution injection"

    def test_normal_paths_not_excluded(self) -> None:
        """Verify various normal project paths are not excluded.

        Given: Normal project file paths
        When: The process() method is called
        Then: None return skipped result

        This test verifies that exclusion patterns don't accidentally
        exclude legitimate project files.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        normal_paths = [
            "P:/projects/myapp/src/main.py",
            "P:/work/requirements.txt",
            "P:/tests/test_module.py",
            "P:/.claude/hooks/my_hook.py",
            "P:/.claude/docs/README.md",
            "P:/config/settings.json",
        ]

        for file_path in normal_paths:
            tool_input = {"file_path": file_path}
            tool_response = {"output": "Some output"}

            # Act
            result = tracker.process(
                tool_name="Read", tool_input=tool_input, tool_response=tool_response
            )

            # Assert - Normal files should not be skipped
            # (unless there's an error pattern, in which case they should be processed)
            assert (
                result.get("skipped") is not True
            ), f"Normal file {file_path} should NOT be skipped"


# ============================================================================
# TEST CLASS: EXCLUDED_PATTERNS Constant
# ============================================================================


class TestExcludedPatternsConstant:
    """Tests for EXCLUDED_PATTERNS constant existence and values."""

    def test_excluded_patterns_exists(self) -> None:
        """Verify EXCLUDED_PATTERNS constant exists in module.

        Given: The error_attribution_tracker module
        When: Checking for EXCLUDED_PATTERNS constant
        Then: Constant exists and is a list

        This verifies the feature is properly implemented.
        """
        # Import module directly to check constant
        import error_attribution_tracker

        # Assert - EXCLUDED_PATTERNS should exist
        assert hasattr(
            error_attribution_tracker, "EXCLUDED_PATTERNS"
        ), "Module should define EXCLUDED_PATTERNS constant"
        assert isinstance(
            error_attribution_tracker.EXCLUDED_PATTERNS, list
        ), "EXCLUDED_PATTERNS should be a list"

    def test_excluded_patterns_contains_required_values(self) -> None:
        """Verify EXCLUDED_PATTERNS contains all required patterns.

        Given: The EXCLUDED_PATTERNS constant
        When: Checking its contents
        Then: Contains all required patterns:
            - "session_ledger.json"
            - "/data/session_"
            - "/logs/"
            - "/.claude/data/"

        This ensures all historical data sources are properly excluded.
        """
        import error_attribution_tracker

        required_patterns = ["session_ledger.json", "/data/session_", "/logs/", "/.claude/data/"]

        for pattern in required_patterns:
            assert (
                pattern in error_attribution_tracker.EXCLUDED_PATTERNS
            ), f"EXCLUDED_PATTERNS should contain '{pattern}'"


# ============================================================================
# TEST CLASS: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Tests for edge cases in data source filtering."""

    def test_no_file_path_input(self) -> None:
        """Verify behavior when tool_input has no file_path key.

        Given: tool_input dict without 'file_path' key
        When: The process() method is called
        Then: Processed normally (not skipped)

        Edge case: Some tools may not provide file_path.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        tool_input = {"command": "ls"}  # No file_path
        tool_response = {"output": "file listing"}

        # Act
        result = tracker.process(
            tool_name="Bash", tool_input=tool_input, tool_response=tool_response
        )

        # Assert - Should not skip (no file_path to check against patterns)
        assert result.get("skipped") is not True, "Should not skip when file_path is not provided"

    def test_empty_file_path(self) -> None:
        """Verify behavior when file_path is empty string.

        Given: tool_input with empty file_path
        When: The process() method is called
        Then: Processed normally (not skipped)

        Edge case: Empty string should not match any excluded pattern.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        tool_input = {"file_path": ""}
        tool_response = {"output": "output"}

        # Act
        result = tracker.process(
            tool_name="Read", tool_input=tool_input, tool_response=tool_response
        )

        # Assert
        assert result.get("skipped") is not True, "Should not skip for empty file_path"

    def test_case_sensitivity(self) -> None:
        """Verify pattern matching is case-sensitive for paths.

        Given: file_path with different case than excluded patterns
        When: The process() method is called
        Then: Directory-pattern matches remain case-sensitive, while exact
        filename exclusions still apply when the filename case matches.

        This ensures exclusion patterns are precise and don't
        accidentally match similar but different paths.
        """
        ErrorAttributionTracker = _import_error_attribution_tracker()

        # Arrange
        tracker = ErrorAttributionTracker()
        # Exact filename exclusion still applies even if parent directory case differs.
        filename_match = tracker.process(
            tool_name="Read",
            tool_input={"file_path": "P:/.claude/Data/session_ledger.json"},
            tool_response={"output": "content"},
        )
        assert (
            filename_match.get("skipped") is True
        ), "session_ledger.json should still be excluded by exact filename match"

        # This should NOT be excluded because its directory case differs from the
        # configured pattern in EXCLUDED_PATTERNS.
        different_case_paths = [
            "P:/.claude/LOGS/error.log",  # Capital LOGS
        ]

        for file_path in different_case_paths:
            tool_input = {"file_path": file_path}
            tool_response = {"output": "content"}

            result = tracker.process(
                tool_name="Read",
                tool_input=tool_input,
                tool_response=tool_response,
            )

            assert (
                result.get("skipped") is not True
            ), f"Path with different case should not be skipped: {file_path}"


# ============================================================================
# MAIN TEST SUITE ENTRY
# ============================================================================

if __name__ == "__main__":
    # Run tests with pytest when executed directly
    pytest.main([__file__, "-v"])
