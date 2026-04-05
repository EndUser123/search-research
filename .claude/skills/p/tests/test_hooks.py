#!/usr/bin/env python3
"""
Tests for /p skill hooks.

Tests cover:
- StopHook_p_completion_validator.py - Completion format validation
- StopHook_p_halt_format_validator.py - Halt format validation
- validate_p_phase_order.py - Phase order enforcement

Test File: tests/test_hooks.py
Run with: pytest tests/test_hooks.py -v
"""

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).parent.parent / "hooks"
LIB_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(LIB_DIR))


class TestStopHookPCompletionValidator:
    """Tests for StopHook_p_completion_validator.py."""

    def setup_method(self):
        """Import the module for each test to ensure clean state."""
        # We need to import the module to get the main function
        # but we'll mock the validate_p_response function
        import importlib
        self.module = importlib.import_module("StopHook_p_completion_validator")

    @patch('StopHook_p_completion_validator.validate_p_response')
    def test_allows_non_p_response(self, mock_validate):
        """
        Test that non-/p responses are allowed.

        Given: A response that is not a /p response
        When: The completion validator runs
        Then: Should allow the response
        """
        mock_validate.return_value = (True, "Not a /p response")

        # Simulate stdin input
        with patch('sys.stdin', StringIO("This is a regular response")):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                # Should exit with code 0 (allow)
                assert exc_info.value.code == 0

                # Check output
                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is True

    @patch('StopHook_p_completion_validator.validate_p_response')
    def test_allows_non_completion_message(self, mock_validate):
        """
        Test that non-completion /p responses are allowed.

        Given: A /p response that is not a completion message
        When: The completion validator runs
        Then: Should allow the response
        """
        mock_validate.return_value = (True, "Not a completion message")

        with patch('sys.stdin', StringIO("/p response without completion")):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is True

    @patch('StopHook_p_completion_validator.validate_p_response')
    def test_blocks_completion_without_summary(self, mock_validate):
        """
        Test that completion without Summary section is blocked.

        Given: A completion message missing **Summary:** section
        When: The completion validator runs
        Then: Should block the response
        """
        mock_validate.return_value = (True, "Completion detected")

        completion = """
## Pipeline Status: COMPLETE

**Status:** ✅ ALL PHASES PASSED

## Next Steps
1. Continue development
        """.strip()

        with patch('sys.stdin', StringIO(completion)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 1

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is False
                assert "Summary" in output["reason"]

    @patch('StopHook_p_completion_validator.validate_p_response')
    def test_blocks_completion_without_next_steps(self, mock_validate):
        """
        Test that completion without Next Steps section is blocked.

        Given: A completion message missing ## Next Steps section
        When: The completion validator runs
        Then: Should block the response
        """
        mock_validate.return_value = (True, "Completion detected")

        completion = """
## Pipeline Status: COMPLETE

**Summary:** Code is production-ready

✅ Phase 1: Build - PASS
        """.strip()

        with patch('sys.stdin', StringIO(completion)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 1

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is False
                assert "Next Steps" in output["reason"]

    @patch('StopHook_p_completion_validator.validate_p_response')
    def test_blocks_completion_without_phase_results(self, mock_validate):
        """
        Test that completion without phase results table is blocked.

        Given: A completion message missing phase results (✅ Phase N: PASS)
        When: The completion validator runs
        Then: Should block the response
        """
        mock_validate.return_value = (True, "Completion detected")

        completion = """
## Pipeline Status: COMPLETE

**Summary:** Code is production-ready

## Next Steps
1. Continue development
        """.strip()

        with patch('sys.stdin', StringIO(completion)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 1

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is False
                assert "phase results" in output["reason"]

    @patch('StopHook_p_completion_validator.validate_p_response')
    def test_allows_valid_completion_format(self, mock_validate):
        """
        Test that valid completion format is allowed.

        Given: A completion message with all required sections
        When: The completion validator runs
        Then: Should allow the response
        """
        mock_validate.return_value = (True, "Completion detected")

        completion = """
## Pipeline Status: COMPLETE

**Summary:** Code is production-ready

✅ Phase 1: Build - PASS
✅ Phase 2: Review - PASS
✅ Phase 3: Validate - PASS

## Next Steps
1. Continue development
        """.strip()

        with patch('sys.stdin', StringIO(completion)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is True


class TestStopHookPHaltFormatValidator:
    """Tests for StopHook_p_halt_format_validator.py."""

    def setup_method(self):
        """Import the module for each test to ensure clean state."""
        import importlib
        self.module = importlib.import_module("StopHook_p_halt_format_validator")

    @patch('StopHook_p_halt_format_validator.validate_p_response')
    def test_allows_non_p_response(self, mock_validate):
        """
        Test that non-/p responses are allowed.

        Given: A response that is not a /p response
        When: The halt validator runs
        Then: Should allow the response
        """
        mock_validate.return_value = (True, "Not a /p response")

        with patch('sys.stdin', StringIO("This is a regular response")):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is True

    @patch('StopHook_p_halt_format_validator.validate_p_response')
    def test_allows_non_halt_message(self, mock_validate):
        """
        Test that non-halt /p responses are allowed.

        Given: A /p response that is not a halt message
        When: The halt validator runs
        Then: Should allow the response
        """
        mock_validate.return_value = (True, "No halt detected")

        with patch('sys.stdin', StringIO("/p response without halt")):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is True

    @patch('StopHook_p_halt_format_validator.validate_p_response')
    def test_blocks_halt_without_reason(self, mock_validate):
        """
        Test that halt without Reason section is blocked.

        Given: A halt message missing **Reason:** section
        When: The halt validator runs
        Then: Should block the response
        """
        mock_validate.return_value = (True, "Halt detected")

        halt = """
## Pipeline Status: HALTED

**Status:** 🛑 HALTED at Phase 2

## Next Steps
1. Fix findings
        """.strip()

        with patch('sys.stdin', StringIO(halt)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 1

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is False
                assert "Reason" in output["reason"]

    @patch('StopHook_p_halt_format_validator.validate_p_response')
    def test_blocks_halt_without_next_steps(self, mock_validate):
        """
        Test that halt without Next Steps section is blocked.

        Given: A halt message missing ## Next Steps section
        When: The halt validator runs
        Then: Should block the response
        """
        mock_validate.return_value = (True, "Halt detected")

        halt = """
## Pipeline Status: HALTED

**Reason:** Tests failing
        """.strip()

        with patch('sys.stdin', StringIO(halt)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 1

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is False
                assert "Next Steps" in output["reason"]

    @patch('StopHook_p_halt_format_validator.validate_p_response')
    def test_blocks_halt_without_numbered_format(self, mock_validate):
        """
        Test that halt without numbered format is blocked.

        Given: A halt message missing "1 - /tdd Fix" format
        When: The halt validator runs
        Then: Should block the response
        """
        mock_validate.return_value = (True, "Halt detected")

        halt = """
## Pipeline Status: HALTED

**Reason:** Tests failing

## Next Steps
- Fix tests
- Run again
        """.strip()

        with patch('sys.stdin', StringIO(halt)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 1

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is False
                assert "numbered format" in output["reason"]

    @patch('StopHook_p_halt_format_validator.validate_p_response')
    def test_allows_valid_halt_format(self, mock_validate):
        """
        Test that valid halt format is allowed.

        Given: A halt message with all required sections and proper format
        When: The halt validator runs
        Then: Should allow the response
        """
        mock_validate.return_value = (True, "Halt detected")

        halt = """
## Pipeline Status: HALTED

**Reason:** Tests failing

**Phase Results:**
- ✅ Phase 1: Build - PASS
- 🛑 Phase 2: Review - HALTED

## Next Steps
1 - /tdd Fix tests
2 - /tdd Fix CRITICAL
3 - /tdd Fix HIGH
4 - /tdd Fix all findings

x - Fix all verified findings: 5
Then re-run: /p
        """.strip()

        with patch('sys.stdin', StringIO(halt)):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["allow"] is True


class TestValidatePPHaseOrder:
    """Tests for validate_p_phase_order.py."""

    def setup_method(self):
        """Import the module for each test to ensure clean state."""
        import importlib
        self.module = importlib.import_module("validate_p_phase_order")

    def test_allows_non_skill_tool(self):
        """
        Test that non-Skill tools are allowed.

        Given: A tool that is not Skill
        When: Phase order validation runs
        Then: Should allow the request
        """
        input_data = {
            "tool_name": "Read",
            "tool_input": {}
        }

        with patch('sys.stdin', StringIO(json.dumps(input_data))):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_allows_non_p_skill(self):
        """
        Test that non-/p skills are allowed.

        Given: A Skill call that is not /p
        When: Phase order validation runs
        Then: Should allow the request
        """
        input_data = {
            "tool_name": "Skill",
            "tool_input": {
                "name": "test"
            }
        }

        with patch('sys.stdin', StringIO(json.dumps(input_data))):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    @patch('validate_p_phase_order.marker_exists')
    def test_denies_p2_without_p1_marker(self, mock_marker):
        """
        Test that P2 is denied without P1 marker.

        Given: Attempting to run P2 (Review) without P1 completion marker
        When: Phase order validation runs
        Then: Should deny the request
        """
        mock_marker.return_value = False

        input_data = {
            "tool_name": "Skill",
            "tool_input": {
                "name": "p",
                "args": ["--phase=2"]
            }
        }

        with patch('sys.stdin', StringIO(json.dumps(input_data))):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
                assert "P1" in output["hookSpecificOutput"]["permissionDecisionReason"]

    @patch('validate_p_phase_order.marker_exists')
    def test_denies_p3_without_p2_marker(self, mock_marker):
        """
        Test that P3 is denied without P2 marker.

        Given: Attempting to run P3 (Validate) without P2 completion marker
        When: Phase order validation runs
        Then: Should deny the request
        """
        mock_marker.return_value = False

        input_data = {
            "tool_name": "Skill",
            "tool_input": {
                "name": "p",
                "args": ["--phase=3"]
            }
        }

        with patch('sys.stdin', StringIO(json.dumps(input_data))):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["hookSpecificOutput"]["permissionDecision"] == "deny"
                assert "P2" in output["hookSpecificOutput"]["permissionDecisionReason"]

    @patch('validate_p_phase_order.marker_exists')
    def test_allows_p2_with_p1_marker(self, mock_marker):
        """
        Test that P2 is allowed with P1 marker.

        Given: P1 completion marker exists
        When: Running P2 (Review)
        Then: Should allow the request
        """
        mock_marker.return_value = True

        input_data = {
            "tool_name": "Skill",
            "tool_input": {
                "name": "p",
                "args": ["--phase=2"]
            }
        }

        with patch('sys.stdin', StringIO(json.dumps(input_data))):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    self.module.main()

                assert exc_info.value.code == 0

                output = json.loads(mock_stdout.getvalue())
                assert output["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_marker_exists_returns_true_for_valid_marker(self):
        """
        Test that marker_exists returns True for valid marker file.

        Given: Marker file exists with valid content
        When: marker_exists is called
        Then: Should return True
        """
        from validate_p_phase_order import marker_exists

        # Mock Path.read_text to return valid content
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.return_value = "Phase 1 completed at 2026-03-09T12:00:00\n"

            result = marker_exists(Path("/fake/path"), expected_phase=1)

            assert result is True

    def test_marker_exists_returns_false_for_missing_file(self):
        """
        Test that marker_exists returns False for missing marker file.

        Given: Marker file does not exist
        When: marker_exists is called
        Then: Should return False
        """
        from validate_p_phase_order import marker_exists

        # Mock Path.read_text to raise FileNotFoundError
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.side_effect = FileNotFoundError()

            result = marker_exists(Path("/fake/path"), expected_phase=1)

            assert result is False

    def test_marker_exists_returns_false_for_empty_content(self):
        """
        Test that marker_exists returns False for empty marker file.

        Given: Marker file exists but is empty
        When: marker_exists is called
        Then: Should return False
        """
        from validate_p_phase_order import marker_exists

        # Mock Path.read_text to return empty string
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.return_value = ""

            result = marker_exists(Path("/fake/path"), expected_phase=1)

            assert result is False

    def test_marker_exists_returns_false_for_wrong_phase(self):
        """
        Test that marker_exists returns False for wrong phase content.

        Given: Marker file exists but contains wrong phase number
        When: marker_exists is called
        Then: Should return False
        """
        from validate_p_phase_order import marker_exists

        # Mock Path.read_text to return wrong phase
        with patch('pathlib.Path.read_text') as mock_read:
            mock_read.return_value = "Phase 2 completed at 2026-03-09T12:00:00\n"

            result = marker_exists(Path("/fake/path"), expected_phase=1)

            assert result is False

    def test_safe_json_loads_accepts_valid_json(self):
        """
        Test that safe_json_loads accepts valid JSON.

        Given: Valid JSON string within size limits
        When: safe_json_loads is called
        Then: Should return parsed JSON object
        """
        from validate_p_phase_order import safe_json_loads

        json_string = '{"key": "value", "number": 42}'

        result = safe_json_loads(json_string)

        assert result == {"key": "value", "number": 42}

    def test_safe_json_loads_rejects_oversized_json(self):
        """
        Test that safe_json_loads rejects oversized JSON.

        Given: JSON string exceeding 10MB limit
        When: safe_json_loads is called
        Then: Should raise ValueError
        """
        from validate_p_phase_order import safe_json_loads

        # Create JSON that exceeds 10MB limit
        large_json = '{"data": "' + ("x" * 11 * 1024 * 1024) + '"}'

        with pytest.raises(ValueError) as exc_info:
            safe_json_loads(large_json)

        assert "exceeds maximum size" in str(exc_info.value)

    def test_safe_json_loads_rejects_deeply_nested_json(self):
        """
        Test that safe_json_loads rejects deeply nested JSON.

        Given: JSON string exceeding 100 levels of nesting
        When: safe_json_loads is called
        Then: Should raise ValueError
        """
        from validate_p_phase_order import safe_json_loads

        # Create deeply nested JSON (101 levels)
        deep_json = " ".join([f'{{"level{n}":' for n in range(101)]) + "1" + "}" * 101

        with pytest.raises(ValueError) as exc_info:
            safe_json_loads(deep_json)

        assert "nesting depth exceeds maximum" in str(exc_info.value)

    def test_safe_json_loads_rejects_malformed_json(self):
        """
        Test that safe_json_loads rejects malformed JSON.

        Given: Invalid JSON string
        When: safe_json_loads is called
        Then: Should raise ValueError
        """
        from validate_p_phase_order import safe_json_loads

        malformed_json = '{invalid json}'

        with pytest.raises(ValueError) as exc_info:
            safe_json_loads(malformed_json)

        assert "Invalid JSON" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
