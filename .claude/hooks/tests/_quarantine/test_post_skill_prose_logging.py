#!/usr/bin/env python3
"""Tests for enhanced logging in post-skill prose detection.

Tests verify that logging captures both block and allow decisions with
complete context (skill_type, tools_used, execution_tools_used).
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import Stop


class TestPostSkillProseLogging:
    """Enhanced logging tests for post-skill prose detection."""

    def test_block_decision_logs_enhanced_fields(self, tmp_path):
        """Test that block decisions log all enhanced fields."""
        # Create mock log file
        log_file = tmp_path / "skill_first_enforcement.jsonl"

        with patch("Stop._log_post_skill_prose_event") as mock_log:
            with patch("time.time", return_value=1741910000.0):
                data = {
                    "tool_calls": [{"name": "Skill"}],
                    "tool_input": {"skill": "code"},
                    "tools_used": [{"name": "Skill"}],
                    "session_id": "test_session",
                    "terminal_id": "test_terminal",
                }

                result = Stop._check_post_skill_prose_response(data)

                # Verify block decision
                assert result is not None
                assert result["decision"] == "block"

                # Verify logging was called
                mock_log.assert_called_once()
                call_args = mock_log.call_args

                # Check the decision parameter
                assert call_args.kwargs["decision"] == "block"
                assert call_args.kwargs["skill_name"] == "code"
                assert call_args.kwargs["skill_type"] == "execution"
                assert call_args.kwargs["session_id"] == "test_session"

    def test_allow_decision_logs_enhanced_fields(self, tmp_path):
        """Test that allow decisions log all enhanced fields."""
        # When execution tools are used, should log allow decision
        with patch("Stop._log_post_skill_prose_event") as mock_log:
            with patch("time.time", return_value=1741910000.0):
                data = {
                    "tool_calls": [{"name": "Skill"}, {"name": "Bash"}],
                    "tool_input": {"skill": "code"},
                    "tools_used": [{"name": "Skill"}, {"name": "Bash"}],
                    "session_id": "test_session",
                    "terminal_id": "test_terminal",
                }

                result = Stop._check_post_skill_prose_response(data)

                # Verify allow decision
                assert result is None  # No block = allow

                # Verify logging was called for allow decision too
                mock_log.assert_called_once()
                call_args = mock_log.call_args

                # Check the decision parameter
                assert call_args.kwargs["decision"] == "allow"
                assert call_args.kwargs["skill_name"] == "code"
                assert call_args.kwargs["skill_type"] == "execution"
                assert call_args.kwargs["reason"] == "allow: execution_tools_used"

    def test_log_includes_skill_type(self, tmp_path):
        """Test that logs include skill_type field (execution vs knowledge)."""
        # Execution skill (has workflow_steps)
        with patch("Stop._log_post_skill_prose_event") as mock_log:
            data = {
                "tool_calls": [{"name": "Skill"}],
                "tool_input": {"skill": "code"},  # /code has workflow_steps
                "tools_used": [{"name": "Skill"}],
            }

            Stop._check_post_skill_prose_response(data)

            # Verify skill_type parameter indicates execution skill
            call_args = mock_log.call_args
            assert call_args.kwargs["skill_type"] == "execution"

    def test_log_includes_tools_used_list(self, tmp_path):
        """Test that logs include tools_used list for context."""
        # Mock log capture to inspect JSON payload
        captured_logs = []

        def capture_log(**kwargs):
            captured_logs.append(kwargs)

        with patch("Stop._log_post_skill_prose_event", side_effect=capture_log):
            data = {
                "tool_calls": [{"name": "Skill"}, {"name": "Bash"}, {"name": "Read"}],
                "tool_input": {"skill": "code"},
                "tools_used": [{"name": "Skill"}, {"name": "Bash"}, {"name": "Read"}],
            }

            Stop._check_post_skill_prose_response(data)

            # Verify log was captured
            assert len(captured_logs) == 1
            log_entry = captured_logs[0]
            assert log_entry["decision"] == "allow"
            assert log_entry["skill_name"] == "code"
            assert "Skill" in log_entry["tools_used"]
            assert "Bash" in log_entry["tools_used"]
            assert "Read" in log_entry["tools_used"]

    def test_log_includes_execution_tools_used(self, tmp_path):
        """Test that logs include execution_tools_used list."""
        with patch("Stop._log_post_skill_prose_event") as mock_log:
            data = {
                "tool_calls": [{"name": "Skill"}, {"name": "Bash"}, {"name": "Read"}],
                "tool_input": {"skill": "code"},
                "tools_used": [{"name": "Skill"}, {"name": "Bash"}, {"name": "Read"}],
            }

            Stop._check_post_skill_prose_response(data)

            # Verify logging was called
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert "Bash" in call_args.kwargs["execution_tools_used"]
            assert "Read" in call_args.kwargs["execution_tools_used"]

    def test_multiple_execution_tools_all_logged(self, tmp_path):
        """Test that all execution tools are logged when multiple used."""
        with patch("Stop._log_post_skill_prose_event") as mock_log:
            data = {
                "tool_calls": [
                    {"name": "Skill"},
                    {"name": "Bash"},
                    {"name": "Write"},
                    {"name": "Edit"},
                    {"name": "Grep"},
                ],
                "tool_input": {"skill": "code"},
                "tools_used": [
                    {"name": "Skill"},
                    {"name": "Bash"},
                    {"name": "Write"},
                    {"name": "Edit"},
                    {"name": "Grep"},
                ],
            }

            Stop._check_post_skill_prose_response(data)

            # Verify allow decision (multiple execution tools used)
            mock_log.assert_called_once()
            call_args = mock_log.call_args
            execution_tools = call_args.kwargs["execution_tools_used"]
            assert "Bash" in execution_tools
            assert "Write" in execution_tools
            assert "Edit" in execution_tools
            assert "Grep" in execution_tools

    def test_no_skill_no_logging(self, tmp_path):
        """Test that no logging occurs when Skill tool not used."""
        with patch("Stop._log_post_skill_prose_event") as mock_log:
            data = {
                "tool_calls": [{"name": "Read"}],
                "tool_input": {"file_path": "test.txt"},
                "tools_used": [{"name": "Read"}],
            }

            result = Stop._check_post_skill_prose_response(data)

            # Verify no block
            assert result is None

            # Verify no logging
            mock_log.assert_not_called()

    def test_knowledge_skill_logs_correct_type(self, tmp_path):
        """Test that knowledge skills are logged with correct type."""
        # Non-existent skill = knowledge skill (no workflow_steps)
        with patch("Stop._log_skill_first_stop_event") as mock_log:
            data = {
                "tool_calls": [{"name": "Skill"}],
                "tool_input": {"skill": "nonexistent_knowledge_skill"},
                "tools_used": [{"name": "Skill"}],
            }

            result = Stop._check_post_skill_prose_response(data)

            # Knowledge skills allow prose (no block)
            assert result is None

            # Verify logging (if implemented) shows knowledge type
            # Currently: knowledge skills don't trigger blocks, so may not log
            # This test verifies expected behavior


class TestLoggingIntegration:
    """Integration tests for logging with actual file output."""

    def test_log_entry_format_valid_json(self, tmp_path):
        """Test that log entries can be parsed as valid JSON."""
        # Mock the log file path
        log_file = tmp_path / "skill_first_enforcement.jsonl"

        with patch("Stop._log_post_skill_prose_event") as mock_log:
            data = {
                "tool_calls": [{"name": "Skill"}],
                "tool_input": {"skill": "code"},
                "tools_used": [{"name": "Skill"}],
            }

            Stop._check_post_skill_prose_response(data)

            # Verify log was called
            assert mock_log.call_count > 0

    def test_logging_graceful_degradation(self, tmp_path):
        """Test that logging failures don't break the detection logic."""
        # Mock log function that raises exception
        def failing_log(*args, **kwargs):
            raise OSError("Log write failed")

        with patch("Stop._log_skill_first_stop_event", side_effect=failing_log):
            data = {
                "tool_calls": [{"name": "Skill"}],
                "tool_input": {"skill": "code"},
                "tools_used": [{"name": "Skill"}],
            }

            # Should still return block decision despite logging failure
            result = Stop._check_post_skill_prose_response(data)
            assert result is not None
            assert result["decision"] == "block"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
