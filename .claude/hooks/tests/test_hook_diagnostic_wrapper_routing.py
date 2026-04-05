#!/usr/bin/env python3
"""Tests for hook_diagnostic_wrapper.py routing functionality - TDD RED Phase.

These tests verify the smart routing functionality for stderr output based on hook type.
All tests should FAIL initially (RED phase) until implementation is complete.

Run with: pytest P:/.claude/hooks/tests/test_hook_diagnostic_wrapper_routing.py -v

Features tested:
1. Hook type detection from command args
2. Stderr routing decisions (blocking vs advisory hooks)
3. Log file creation and content for advisory hooks
4. Fallback behavior for unknown hook types

Hook Categories:
- Blocking hooks (stderr passes through): PreToolUse, Stop
- Advisory hooks (stderr routes to log): PostToolUse, UserPromptSubmit
"""

import sys
from pathlib import Path

# Add __lib directory to path for imports
hooks_lib_dir = Path(__file__).resolve().parent.parent / "__lib"
sys.path.insert(0, str(hooks_lib_dir))


class TestExtractHookTypeFromCmdArgs:
    """Test hook type extraction from command arguments."""

    def test_extract_pretooluse_hook_type(self):
        """
        Test extracting PreToolUse hook type from command args.

        Given: Command args for PreToolUse_file_existence_guard.py
        When: extract_hook_type_from_cmd_args is called
        Then: Should return "PreToolUse"
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/__lib/hook_runner.py",
            "P:/.claude/hooks/PreToolUse_file_existence_guard.py",
            "--timeout",
            "5.0"
        ]

        # Act
        # Note: This function doesn't exist yet, will fail with ImportError
        from hook_diagnostic_wrapper import extract_hook_type_from_cmd_args
        hook_type = extract_hook_type_from_cmd_args(real_cmd)

        # Assert
        assert hook_type == "PreToolUse", f"Expected 'PreToolUse', got '{hook_type}'"

    def test_extract_posttooluse_hook_type(self):
        """
        Test extracting PostToolUse hook type from command args.

        Given: Command args for PostToolUse_artifact_validator.py
        When: extract_hook_type_from_cmd_args is called
        Then: Should return "PostToolUse"
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/__lib/hook_runner.py",
            "P:/.claude/hooks/PostToolUse_artifact_validator.py"
        ]

        # Act
        from hook_diagnostic_wrapper import extract_hook_type_from_cmd_args
        hook_type = extract_hook_type_from_cmd_args(real_cmd)

        # Assert
        assert hook_type == "PostToolUse", f"Expected 'PostToolUse', got '{hook_type}'"

    def test_extract_stop_hook_type(self):
        """
        Test extracting Stop hook type from command args.

        Given: Command args for StopHook_reality_check.py
        When: extract_hook_type_from_cmd_args is called
        Then: Should return "Stop"
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/StopHook_reality_check.py"
        ]

        # Act
        from hook_diagnostic_wrapper import extract_hook_type_from_cmd_args
        hook_type = extract_hook_type_from_cmd_args(real_cmd)

        # Assert
        assert hook_type == "Stop", f"Expected 'Stop', got '{hook_type}'"

    def test_extract_userpromptsubmit_hook_type(self):
        """
        Test extracting UserPromptSubmit hook type from command args.

        Given: Command args for UserPromptSubmit_router.py
        When: extract_hook_type_from_cmd_args is called
        Then: Should return "UserPromptSubmit"
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/UserPromptSubmit_router.py"
        ]

        # Act
        from hook_diagnostic_wrapper import extract_hook_type_from_cmd_args
        hook_type = extract_hook_type_from_cmd_args(real_cmd)

        # Assert
        assert hook_type == "UserPromptSubmit", f"Expected 'UserPromptSubmit', got '{hook_type}'"

    def test_extract_hook_type_from_nested_path(self):
        """
        Test extracting hook type from nested directory path.

        Given: Command args for hook in posttooluse/ subdirectory
        When: extract_hook_type_from_cmd_args is called
        Then: Should return "PostToolUse"
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/posttooluse/integration_verifier.py"
        ]

        # Act
        from hook_diagnostic_wrapper import extract_hook_type_from_cmd_args
        hook_type = extract_hook_type_from_cmd_args(real_cmd)

        # Assert
        assert hook_type == "PostToolUse", f"Expected 'PostToolUse' from nested path, got '{hook_type}'"

    def test_extract_hook_type_unknown_format(self):
        """
        Test extracting hook type with unknown filename format.

        Given: Command args for hook without standard prefix
        When: extract_hook_type_from_cmd_args is called
        Then: Should return None or empty string
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/unknown_hook.py"
        ]

        # Act
        from hook_diagnostic_wrapper import extract_hook_type_from_cmd_args
        hook_type = extract_hook_type_from_cmd_args(real_cmd)

        # Assert - Unknown format should return None or empty
        assert hook_type in (None, ""), f"Expected None or empty string for unknown format, got '{hook_type}'"


class TestShouldLogToFileStderr:
    """Test stderr routing logic based on hook type."""

    def test_pretooluse_should_not_log_to_file(self):
        """
        Test that PreToolUse hooks should NOT log stderr to file.

        Given: Hook type is "PreToolUse" (blocking hook)
        When: should_log_to_file_stderr is called
        Then: Should return False (stderr should pass through)
        """
        # Arrange
        hook_type = "PreToolUse"
        stderr_content = "Some error message"

        # Act
        from hook_diagnostic_wrapper import should_log_to_file_stderr
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Assert
        assert should_log is False, "PreToolUse is a blocking hook, stderr should pass through, not log to file"

    def test_stop_should_not_log_to_file(self):
        """
        Test that Stop hooks should NOT log stderr to file.

        Given: Hook type is "Stop" (blocking hook)
        When: should_log_to_file_stderr is called
        Then: Should return False (stderr should pass through)
        """
        # Arrange
        hook_type = "Stop"
        stderr_content = "Verification failed"

        # Act
        from hook_diagnostic_wrapper import should_log_to_file_stderr
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Assert
        assert should_log is False, "Stop is a blocking hook, stderr should pass through, not log to file"

    def test_posttooluse_should_log_to_file(self):
        """
        Test that PostToolUse hooks SHOULD log stderr to file.

        Given: Hook type is "PostToolUse" (advisory hook)
        When: should_log_to_file_stderr is called
        Then: Should return True (stderr should route to log file)
        """
        # Arrange
        hook_type = "PostToolUse"
        stderr_content = "Warning message"

        # Act
        from hook_diagnostic_wrapper import should_log_to_file_stderr
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Assert
        assert should_log is True, "PostToolUse is an advisory hook, stderr should log to file"

    def test_userpromptsubmit_should_log_to_file(self):
        """
        Test that UserPromptSubmit hooks SHOULD log stderr to file.

        Given: Hook type is "UserPromptSubmit" (advisory hook)
        When: should_log_to_file_stderr is called
        Then: Should return True (stderr should route to log file)
        """
        # Arrange
        hook_type = "UserPromptSubmit"
        stderr_content = "Debug info"

        # Act
        from hook_diagnostic_wrapper import should_log_to_file_stderr
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Assert
        assert should_log is True, "UserPromptSubmit is an advisory hook, stderr should log to file"

    def test_unknown_hook_type_should_not_log_to_file(self):
        """
        Test that unknown hook types default to pass-through (not log to file).

        Given: Hook type is "UnknownType" (not recognized)
        When: should_log_to_file_stderr is called
        Then: Should return False (fallback to pass-through behavior)
        """
        # Arrange
        hook_type = "UnknownType"
        stderr_content = "Some message"

        # Act
        from hook_diagnostic_wrapper import should_log_to_file_stderr
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Assert
        assert should_log is False, "Unknown hook types should default to pass-through (not log to file)"

    def test_empty_hook_type_should_not_log_to_file(self):
        """
        Test that empty hook type defaults to pass-through.

        Given: Hook type is None or empty string
        When: should_log_to_file_stderr is called
        Then: Should return False (fallback to pass-through behavior)
        """
        # Arrange
        hook_type = None
        stderr_content = "Some message"

        # Act
        from hook_diagnostic_wrapper import should_log_to_file_stderr
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Assert
        assert should_log is False, "Empty hook type should default to pass-through (not log to file)"


class TestLogToHookStderrFile:
    """Test log file creation and writing for advisory hooks."""

    def test_log_to_hook_stderr_file_creates_directory(self, tmp_path):
        """
        Test that log file creation creates parent directories if needed.

        Given: A hook type and stderr content
        When: log_to_hook_stderr_file is called with non-existent directory
        Then: Should create the directory and log file
        """
        # Arrange
        hook_type = "PostToolUse"
        stderr_content = "Test warning message"
        log_dir = tmp_path / "logs" / "diagnostics"

        # Act
        from hook_diagnostic_wrapper import log_to_hook_stderr_file
        log_file = log_to_hook_stderr_file(hook_type, stderr_content, log_dir=log_dir)

        # Assert
        assert log_dir.exists(), "Log directory should be created"
        assert log_file.exists(), "Log file should be created"
        assert log_file.name == "hook_stderr.log", f"Log file should be named 'hook_stderr.log', got '{log_file.name}'"

    def test_log_to_hook_stderr_file_writes_content(self, tmp_path):
        """
        Test that log file contains the stderr content with metadata.

        Given: A hook type and stderr content
        When: log_to_hook_stderr_file is called
        Then: Log file should contain timestamp, hook type, and stderr content
        """
        # Arrange
        hook_type = "PostToolUse"
        stderr_content = "Test warning message"
        log_dir = tmp_path / "logs" / "diagnostics"

        # Act
        from hook_diagnostic_wrapper import log_to_hook_stderr_file
        log_file = log_to_hook_stderr_file(hook_type, stderr_content, log_dir=log_dir)

        # Assert - Read log file and verify content
        log_content = log_file.read_text(encoding='utf-8')

        # Should contain hook type
        assert hook_type in log_content, f"Log should contain hook type '{hook_type}'"

        # Should contain stderr content
        assert stderr_content in log_content, f"Log should contain stderr content '{stderr_content}'"

        # Should contain timestamp (ISO format has 'T' and colons)
        assert 'T' in log_content or ':' in log_content, "Log should contain timestamp"

    def test_log_to_hook_stderr_file_appends_multiple_entries(self, tmp_path):
        """
        Test that multiple log entries are appended to the same file.

        Given: A log file already exists
        When: log_to_hook_stderr_file is called multiple times
        Then: All entries should be in the log file
        """
        # Arrange
        hook_type = "PostToolUse"
        log_dir = tmp_path / "logs" / "diagnostics"

        # Act - Log multiple messages
        from hook_diagnostic_wrapper import log_to_hook_stderr_file

        log_to_hook_stderr_file(hook_type, "First message", log_dir=log_dir)
        log_to_hook_stderr_file(hook_type, "Second message", log_dir=log_dir)
        log_to_hook_stderr_file(hook_type, "Third message", log_dir=log_dir)

        # Assert
        log_file = log_dir / "hook_stderr.log"
        log_content = log_file.read_text(encoding='utf-8')

        assert "First message" in log_content, "First message should be in log"
        assert "Second message" in log_content, "Second message should be in log"
        assert "Third message" in log_content, "Third message should be in log"

        # Should have 3 entries (count by hook_type occurrences)
        hook_type_count = log_content.count(hook_type)
        assert hook_type_count >= 3, f"Should have at least 3 entries in log, found {hook_type_count}"

    def test_log_to_hook_stderr_file_handles_multiline_content(self, tmp_path):
        """
        Test that multiline stderr content is logged correctly.

        Given: Stderr content with multiple lines
        When: log_to_hook_stderr_file is called
        Then: All lines should be preserved in log file
        """
        # Arrange
        hook_type = "UserPromptSubmit"
        stderr_content = """Line 1: Warning
Line 2: Debug info
Line 3: Additional context"""
        log_dir = tmp_path / "logs" / "diagnostics"

        # Act
        from hook_diagnostic_wrapper import log_to_hook_stderr_file
        log_file = log_to_hook_stderr_file(hook_type, stderr_content, log_dir=log_dir)

        # Assert
        log_content = log_file.read_text(encoding='utf-8')

        assert "Line 1: Warning" in log_content, "First line should be in log"
        assert "Line 2: Debug info" in log_content, "Second line should be in log"
        assert "Line 3: Additional context" in log_content, "Third line should be in log"

    def test_log_to_hook_stderr_file_handles_empty_content(self, tmp_path):
        """
        Test that empty stderr content is handled gracefully.

        Given: Empty stderr content
        When: log_to_hook_stderr_file is called
        Then: Should still create log entry or handle gracefully
        """
        # Arrange
        hook_type = "PostToolUse"
        stderr_content = ""
        log_dir = tmp_path / "logs" / "diagnostics"

        # Act
        from hook_diagnostic_wrapper import log_to_hook_stderr_file
        log_file = log_to_hook_stderr_file(hook_type, stderr_content, log_dir=log_dir)

        # Assert - Should create log file even with empty content
        assert log_file.exists(), "Log file should be created even with empty content"

    def test_log_to_hook_stderr_file_uses_default_directory(self, tmp_path):
        """
        Test that log_to_hook_stderr_file uses default directory when none specified.

        Given: Hook type and stderr content, no log_dir specified
        When: log_to_hook_stderr_file is called
        Then: Should use default log directory
        """
        # Arrange
        hook_type = "PostToolUse"
        stderr_content = "Test message"

        # Act - Use default log directory (should be P:/.claude/hooks/logs/diagnostics)
        from hook_diagnostic_wrapper import log_to_hook_stderr_file
        log_file = log_to_hook_stderr_file(hook_type, stderr_content)

        # Assert - Should create file in default location
        assert log_file.exists(), "Log file should be created in default location"
        assert "hook_stderr.log" in str(log_file), "Log file should be named hook_stderr.log"

        # Clean up - remove the created log file
        if log_file.exists():
            log_file.unlink()


class TestIntegrationScenarios:
    """Integration tests combining routing logic."""

    def test_pretooluse_stderr_routing_decision(self):
        """
        Test complete routing flow for PreToolUse hook.

        Given: PreToolUse hook with stderr content
        When: Extract hook type and check routing decision
        Then: Should determine to pass through (not log to file)
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/PreToolUse_file_existence_guard.py",
            "--timeout",
            "5.0"
        ]
        stderr_content = "File does not exist error"

        # Act
        from hook_diagnostic_wrapper import (
            extract_hook_type_from_cmd_args,
            should_log_to_file_stderr,
        )

        hook_type = extract_hook_type_from_cmd_args(real_cmd)
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Assert
        assert hook_type == "PreToolUse", "Should extract PreToolUse hook type"
        assert should_log is False, "PreToolUse should pass through stderr, not log to file"

    def test_posttooluse_stderr_routing_decision(self, tmp_path):
        """
        Test complete routing flow for PostToolUse hook.

        Given: PostToolUse hook with stderr content
        When: Extract hook type, check routing decision, and log to file
        Then: Should determine to log to file and create log entry
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/PostToolUse_artifact_validator.py"
        ]
        stderr_content = "Artifact validation warning"
        log_dir = tmp_path / "logs" / "diagnostics"

        # Act
        from hook_diagnostic_wrapper import (
            extract_hook_type_from_cmd_args,
            log_to_hook_stderr_file,
            should_log_to_file_stderr,
        )

        hook_type = extract_hook_type_from_cmd_args(real_cmd)
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Only log if routing decision is True
        if should_log:
            log_file = log_to_hook_stderr_file(hook_type, stderr_content, log_dir=log_dir)
        else:
            log_file = None

        # Assert
        assert hook_type == "PostToolUse", "Should extract PostToolUse hook type"
        assert should_log is True, "PostToolUse should log stderr to file"
        assert log_file is not None, "Log file should be created"
        assert log_file.exists(), "Log file should exist"

        # Verify log content
        log_content = log_file.read_text(encoding='utf-8')
        assert stderr_content in log_content, "Stderr content should be in log file"

    def test_stop_hook_stderr_routing_decision(self):
        """
        Test complete routing flow for Stop hook.

        Given: Stop hook with stderr content
        When: Extract hook type and check routing decision
        Then: Should determine to pass through (not log to file)
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/StopHook_reality_check.py"
        ]
        stderr_content = "Verification failed error"

        # Act
        from hook_diagnostic_wrapper import (
            extract_hook_type_from_cmd_args,
            should_log_to_file_stderr,
        )

        hook_type = extract_hook_type_from_cmd_args(real_cmd)
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Assert
        assert hook_type == "Stop", "Should extract Stop hook type"
        assert should_log is False, "Stop should pass through stderr, not log to file"

    def test_userpromptsubmit_stderr_routing_decision(self, tmp_path):
        """
        Test complete routing flow for UserPromptSubmit hook.

        Given: UserPromptSubmit hook with stderr content
        When: Extract hook type, check routing decision, and log to file
        Then: Should determine to log to file and create log entry
        """
        # Arrange
        real_cmd = [
            "python",
            "P:/.claude/hooks/UserPromptSubmit_router.py"
        ]
        stderr_content = "Prompt processing debug info"
        log_dir = tmp_path / "logs" / "diagnostics"

        # Act
        from hook_diagnostic_wrapper import (
            extract_hook_type_from_cmd_args,
            log_to_hook_stderr_file,
            should_log_to_file_stderr,
        )

        hook_type = extract_hook_type_from_cmd_args(real_cmd)
        should_log = should_log_to_file_stderr(hook_type, stderr_content)

        # Only log if routing decision is True
        if should_log:
            log_file = log_to_hook_stderr_file(hook_type, stderr_content, log_dir=log_dir)
        else:
            log_file = None

        # Assert
        assert hook_type == "UserPromptSubmit", "Should extract UserPromptSubmit hook type"
        assert should_log is True, "UserPromptSubmit should log stderr to file"
        assert log_file is not None, "Log file should be created"
        assert log_file.exists(), "Log file should exist"
