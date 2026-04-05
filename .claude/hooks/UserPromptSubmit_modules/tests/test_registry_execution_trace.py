"""Failing tests for execution trace logging in registry.py.

This test file verifies the _log_execution_trace() function that creates
JSON-structured log entries for hook execution tracking.

Tests verify:
1. _log_execution_trace() creates correct JSON structure
2. Log entry includes: ts, session_id, terminal_id, hook_name, result summary
3. Log file is created if it doesn't exist
4. Log file is appended to if it exists

Run with: pytest P:/.claude/hooks/UserPromptSubmit_modules/tests/test_registry_execution_trace.py -v

Test Phase: RED - Tests must FAIL before implementation
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class TestLogExecutionTraceCreatesCorrectJSONStructure:
    """Tests for _log_execution_trace() JSON structure validation."""

    def test_log_entry_has_required_fields(self, tmp_path):
        """
        RED TEST: Verify _log_execution_trace() creates JSON entry with required fields.

        Given: A hook execution with context and result
        When: _log_execution_trace() is called
        Then: Log entry should contain: ts, session_id, terminal_id, hook_name, result

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"
        test_session_id = "test_session_12345"
        test_terminal_id = "test_terminal_67890"
        test_hook_name = "test_hook"
        test_prompt = "Test prompt for execution trace"

        context = HookContext(
            prompt=test_prompt,
            data={"test": "data"},
            session_id=test_session_id,
            terminal_id=test_terminal_id,
        )

        result = HookResult(
            context={"test": "result"},
            tokens_added=10,
        )

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name=test_hook_name,
            context=context,
            result=result,
        )

        # Assert - Verify log file was created
        assert test_log_file.exists(), f"Log file {test_log_file} should be created"

        # Verify log file has content
        content = test_log_file.read_text()
        assert len(content) > 0, "Log file should have content"

        # Parse and verify JSON structure
        log_entry = json.loads(content.strip())

        # Verify required fields exist
        assert "ts" in log_entry, "Log entry should have 'ts' (timestamp) field"
        assert "session_id" in log_entry, "Log entry should have 'session_id' field"
        assert "terminal_id" in log_entry, "Log entry should have 'terminal_id' field"
        assert "hook_name" in log_entry, "Log entry should have 'hook_name' field"
        assert "result" in log_entry, "Log entry should have 'result' field"

    def test_timestamp_field_format(self, tmp_path):
        """
        RED TEST: Verify 'ts' field uses ISO 8601 format (YYYY-MM-DDTHH:MM:SS).

        Given: A hook execution occurs
        When: _log_execution_trace() logs the entry
        Then: 'ts' field should be in ISO 8601 format

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"
        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id="terminal_1",
        )

        result = HookResult.empty()

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert - Verify timestamp format
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())

        ts_format = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$"
        import re
        assert re.match(ts_format, log_entry["ts"]), (
            f"Timestamp should be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS), "
            f"got '{log_entry['ts']}'"
        )

    def test_session_id_from_context(self, tmp_path):
        """
        RED TEST: Verify session_id is extracted from HookContext.

        Given: HookContext with session_id="test_session_123"
        When: _log_execution_trace() is called
        Then: Log entry should have session_id="test_session_123"

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"
        test_session_id = "test_session_abc123"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id=test_session_id,
            terminal_id="terminal_1",
        )

        result = HookResult.empty()

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())

        assert log_entry["session_id"] == test_session_id, (
            f"Expected session_id '{test_session_id}', got '{log_entry['session_id']}'"
        )

    def test_terminal_id_from_context(self, tmp_path):
        """
        RED TEST: Verify terminal_id is extracted from HookContext.

        Given: HookContext with terminal_id="test_terminal_xyz"
        When: _log_execution_trace() is called
        Then: Log entry should have terminal_id="test_terminal_xyz"

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"
        test_terminal_id = "test_terminal_xyz789"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id=test_terminal_id,
        )

        result = HookResult.empty()

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())

        assert log_entry["terminal_id"] == test_terminal_id, (
            f"Expected terminal_id '{test_terminal_id}', got '{log_entry['terminal_id']}'"
        )

    def test_hook_name_parameter(self, tmp_path):
        """
        RED TEST: Verify hook_name is passed as parameter and logged.

        Given: hook_name="my_custom_hook"
        When: _log_execution_trace() is called
        Then: Log entry should have hook_name="my_custom_hook"

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"
        test_hook_name = "my_custom_hook"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id="terminal_1",
        )

        result = HookResult.empty()

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name=test_hook_name,
            context=context,
            result=result,
        )

        # Assert
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())

        assert log_entry["hook_name"] == test_hook_name, (
            f"Expected hook_name '{test_hook_name}', got '{log_entry['hook_name']}'"
        )

    def test_result_summary_includes_tokens_added(self, tmp_path):
        """
        RED TEST: Verify result summary includes tokens_added from HookResult.

        Given: HookResult with tokens_added=42
        When: _log_execution_trace() is called
        Then: Log entry result should include tokens_added=42

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"
        test_tokens = 42

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id="terminal_1",
        )

        result = HookResult(
            context={"test": "data"},
            tokens_added=test_tokens,
        )

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())

        assert "result" in log_entry, "Log entry should have 'result' field"
        assert "tokens_added" in log_entry["result"], "Result should include 'tokens_added'"
        assert log_entry["result"]["tokens_added"] == test_tokens, (
            f"Expected tokens_added={test_tokens}, got {log_entry['result']['tokens_added']}"
        )


class TestLogExecutionTraceFileCreation:
    """Tests for log file creation behavior."""

    def test_log_file_created_if_not_exists(self, tmp_path):
        """
        RED TEST: Verify log file is created if it doesn't exist.

        Given: Log file path doesn't exist
        When: _log_execution_trace() is called
        Then: Log file should be created with parent directories

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        # Create log file path in nested directory that doesn't exist
        test_log_file = tmp_path / "nested" / "dir" / "execution_trace.jsonl"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id="terminal_1",
        )

        result = HookResult.empty()

        # Verify file doesn't exist before
        assert not test_log_file.exists(), "Log file should not exist before test"

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert - File should be created
        assert test_log_file.exists(), f"Log file {test_log_file} should be created"

        # Parent directory should also be created
        assert test_log_file.parent.exists(), "Parent directory should be created"

    def test_log_file_appended_if_exists(self, tmp_path):
        """
        RED TEST: Verify log file is appended to if it exists.

        Given: Log file already exists with one entry
        When: _log_execution_trace() is called twice
        Then: Log file should contain two entries (one per line)

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id="terminal_1",
        )

        result1 = HookResult(context={"run": 1}, tokens_added=10)
        result2 = HookResult(context={"run": 2}, tokens_added=20)

        # Act - First call
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="hook_1",
            context=context,
            result=result1,
        )

        # Act - Second call
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="hook_2",
            context=context,
            result=result2,
        )

        # Assert - File should have 2 lines (2 entries)
        content = test_log_file.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 2, f"Expected 2 log entries, got {len(lines)}"

        # Parse and verify each entry
        entry1 = json.loads(lines[0])
        entry2 = json.loads(lines[1])

        assert entry1["hook_name"] == "hook_1"
        assert entry2["hook_name"] == "hook_2"

    def test_multiple_entries_separated_by_newlines(self, tmp_path):
        """
        RED TEST: Verify multiple log entries are newline-separated (JSONL format).

        Given: Three hook executions are logged
        When: All three are written to the same log file
        Then: Each entry should be on its own line (JSONL format)

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id="terminal_1",
        )

        # Act - Log three entries
        for i in range(3):
            result = HookResult(context={"index": i}, tokens_added=i * 10)
            _log_execution_trace(
                log_file=test_log_file,
                hook_name=f"hook_{i}",
                context=context,
                result=result,
            )

        # Assert - Verify JSONL format (one JSON object per line)
        content = test_log_file.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"

        # Each line should be valid JSON
        for i, line in enumerate(lines):
            entry = json.loads(line)
            assert entry["hook_name"] == f"hook_{i}"
            assert entry["result"]["tokens_added"] == i * 10


class TestLogExecutionTraceEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_result_context(self, tmp_path):
        """
        RED TEST: Verify logging works when HookResult has empty context.

        Given: HookResult with empty context dict
        When: _log_execution_trace() is called
        Then: Log entry should be created successfully

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id="terminal_1",
        )

        result = HookResult(context={}, tokens_added=0)

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())

        assert "result" in log_entry
        assert log_entry["result"]["tokens_added"] == 0

    def test_none_session_id(self, tmp_path):
        """
        RED TEST: Verify logging works when session_id is None.

        Given: HookContext with session_id=None
        When: _log_execution_trace() is called
        Then: Log entry should handle None gracefully

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id=None,  # None session_id
            terminal_id="terminal_1",
        )

        result = HookResult.empty()

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert - Should log successfully with null or empty session_id
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())

        # session_id should be present (either None or empty string)
        assert "session_id" in log_entry

    def test_none_terminal_id(self, tmp_path):
        """
        RED TEST: Verify logging works when terminal_id is None.

        Given: HookContext with terminal_id=None
        When: _log_execution_trace() is called
        Then: Log entry should handle None gracefully

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id=None,  # None terminal_id
        )

        result = HookResult.empty()

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert - Should log successfully with null or empty terminal_id
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())

        # terminal_id should be present (either None or empty string)
        assert "terminal_id" in log_entry

    def test_special_characters_in_context(self, tmp_path):
        """
        RED TEST: Verify logging works with special characters in context.

        Given: HookResult context with special characters (quotes, newlines, unicode)
        When: _log_execution_trace() is called
        Then: JSON should be properly escaped and valid

        This test FAILS because _log_execution_trace() function doesn't exist yet.
        """
        # Arrange
        from UserPromptSubmit_modules.base import HookContext, HookResult
        from UserPromptSubmit_modules.registry import _log_execution_trace

        test_log_file = tmp_path / "execution_trace.jsonl"

        context = HookContext(
            prompt="Test prompt",
            data={},
            session_id="session_1",
            terminal_id="terminal_1",
        )

        # Context with special characters
        special_context = {
            "quote": 'Text with "quotes"',
            "newline": "Line 1\nLine 2",
            "unicode": "Unicode: 🚀 🎯 ✨",
            "backslash": "Path\\to\\file",
        }

        result = HookResult(context=special_context, tokens_added=10)

        # Act
        _log_execution_trace(
            log_file=test_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
        )

        # Assert - JSON should be valid and properly escaped
        content = test_log_file.read_text()
        log_entry = json.loads(content.strip())  # Should not raise JSONDecodeError

        assert log_entry["result"]["context"]["quote"] == 'Text with "quotes"'
        assert log_entry["result"]["context"]["newline"] == "Line 1\nLine 2"
        assert log_entry["result"]["context"]["unicode"] == "Unicode: 🚀 🎯 ✨"
        assert log_entry["result"]["context"]["backslash"] == "Path\\to\\file"
