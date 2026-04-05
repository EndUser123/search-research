#!/usr/bin/env python3
"""
Tests for Stop hook validators (P1-002: Race Condition in Fabrication Detection).

These tests verify that the validation logic properly handles responses with both
tables AND execution evidence, ensuring the order of checks doesn't create race
conditions.

Test File: tests/test_stop_hook_validators.py
Run with: pytest tests/test_stop_hook_validators.py -v
"""

import sys
from pathlib import Path

import pytest

# Add lib directory to path
LIB_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from evidence_patterns import (
    validate_p_response,
)


class TestP1_002_RaceConditionInFabricationDetection:
    """
    Tests for P1-002: Race Condition in Fabrication Detection.

    The validation logic should use proper AND logic to avoid race conditions
    where a response might have tables AND evidence but be checked in wrong order.
    """

    def test_tables_without_evidence_should_be_blocked(self):
        """
        Test that responses with heavy tables but no execution evidence are blocked.

        Given: A response has formatted tables (10+ box-drawing chars)
        And: The response has NO execution evidence (no pytest, git, bash output)
        When: validate_p_response is called
        Then: The response should be blocked with fabrication error
        """
        response = """
## Pipeline Status: COMPLETE

**Summary:** All tests passed

┌──────────┬─────────┬──────────┐
│ Column 1 │ Column 2│ Column 3 │
├──────────┼─────────┼──────────┤
│ Data 1   │ Data 2  │ Data 3   │
└──────────┴─────────┴──────────┘

**Next Steps:** Deploy to production
        """.strip()

        allow, reason = validate_p_response(response, check_for_completion=True)

        assert allow is False, f"Expected False but got True. Reason: {reason}"
        assert "FABRICATION DETECTED" in reason
        assert "formatted tables" in reason
        assert "no evidence" in reason

    def test_evidence_without_tables_should_be_allowed(self):
        """
        Test that responses with execution evidence but no tables are allowed.

        Given: A response has execution evidence (pytest, git, etc.)
        And: The response has NO formatted tables
        When: validate_p_response is called
        Then: The response should be allowed
        """
        response = """
## Pipeline Status: COMPLETE

**Summary:** All tests passed

pytest collected 42 items
22 PASSED, 1 FAILED
git status shows clean repo
Bash exit code: 0

**Next Steps:** Fix failing test
        """.strip()

        allow, reason = validate_p_response(response, check_for_completion=True)

        assert allow is True, f"Expected True but got False. Reason: {reason}"
        assert "FABRICATION DETECTED" not in reason

    def test_both_tables_and_evidence_should_be_allowed(self):
        """
        Test CRITICAL case: responses with BOTH tables AND evidence should be allowed.

        This is the race condition test. The order of checks should not matter
        when both conditions are met - tables alone don't indicate fabrication
        if there's also evidence of real tool execution.

        Given: A response has formatted tables (10+ box-drawing chars)
        And: The response HAS execution evidence (pytest, git, bash output)
        When: validate_p_response is called
        Then: The response should be ALLOWED (evidence trumps table check)

        This test FAILS under the buggy implementation where the check order
        creates a race condition that incorrectly blocks valid responses.
        """
        response = """
## Pipeline Status: COMPLETE

**Summary:** All tests passed

pytest collected 42 items
22 PASSED, 1 FAILED
git status shows clean repo

┌──────────┬─────────┬──────────┐
│ Test     │ Status  │ Time     │
├──────────┼─────────┼──────────┤
│ test_1   │ PASSED  │ 0.5s     │
│ test_2   │ PASSED  │ 0.3s     │
│ test_3   │ FAILED  │ 0.7s     │
└──────────┴─────────┴──────────┘

**Next Steps:** Fix failing test
        """.strip()

        allow, reason = validate_p_response(response, check_for_completion=True)

        # CRITICAL ASSERTION: This SHOULD pass but may fail due to race condition
        assert allow is True, (
            f"Race condition detected! Response with BOTH tables AND evidence "
            f"was incorrectly blocked. Reason: {reason}\n\n"
            f"This indicates the check order creates a race condition where "
            f"the table check fires before evidence is properly considered."
        )
        assert "FABRICATION DETECTED" not in reason

    def test_neither_tables_nor_evidence_should_be_allowed(self):
        """
        Test that responses with neither tables nor evidence are allowed.

        Given: A response has NO formatted tables
        And: The response has NO execution evidence
        When: validate_p_response is called
        Then: The response should be allowed (fabrication check doesn't apply)

        Note: This might still fail other validation checks, but the fabrication
        detection specifically should not block it.
        """
        response = """
## Pipeline Status: COMPLETE

**Summary:** Work completed

**Next Steps:** Continue with next phase
        """.strip()

        allow, reason = validate_p_response(response, check_for_completion=True)

        # Should not be blocked for fabrication (no tables detected)
        assert "FABRICATION DETECTED" not in reason

    def test_table_detection_threshold(self):
        """
        Test that table detection requires minimum box-drawing characters.

        Given: A response has fewer than 10 box-drawing characters
        And: The response has execution evidence
        When: validate_p_response is called
        Then: The response should be allowed (threshold not met)
        """
        response = """
## Pipeline Status: COMPLETE

**Summary:** Tests passed

pytest PASSED
git status

┌─┐└┘  # Only 5 chars - below threshold

**Next Steps:** Deploy
        """.strip()

        allow, reason = validate_p_response(response, check_for_completion=True)

        assert allow is True, f"Expected True but got False. Reason: {reason}"
        assert "FABRICATION DETECTED" not in reason

    def test_evidence_pattern_variations(self):
        """
        Test various execution evidence patterns are properly detected.

        This test reveals BUG: Current code requires 3 DISTINCT pattern types.
        Multiple tool calls (Read, Glob, Bash) should count as multiple evidence
        indicators even though they match the same pattern regex.

        EXPECTED: Responses with multiple tool calls should be allowed
        ACTUAL: Currently blocked because all tool calls match one pattern
        """
        # Test with multiple tool call references - this SHOULD be enough evidence
        response_with_tools = """
## Pipeline Status: COMPLETE

**Summary:** Done

Read(file.py)
Glob(**/*.txt)
Bash(ls -la)
Bash(pwd)
Task(readme_check)

┌──────────────┬─────────┐
│ File         │ Size    │
├──────────────┼─────────┤
│ file.py      │ 1024    │
└──────────────┴─────────┘

**Next Steps:** Continue
        """.strip()

        allow, reason = validate_p_response(response_with_tools, check_for_completion=True)

        # CRITICAL: This SHOULD pass (multiple tool executions = clear evidence)
        # but currently FAILS due to pattern counting bug
        assert allow is True, (
            f"BUG DETECTED: Multiple distinct tool calls (Read, Glob, Bash, Task) "
            f"provide clear evidence of real execution but are incorrectly blocked. "
            f"Reason: {reason}\n\n"
            f"The evidence detection counts pattern REGEXES matched, not actual "
            f"evidence instances. 5 tool calls should count as 5 evidence indicators, "
            f"not 1 pattern type."
        )

    def test_check_order_independence(self):
        """
        Test that validation result is independent of check implementation order.

        This test verifies that the logical AND operation is properly implemented
        such that the order of checking (tables first vs evidence first) doesn't
        change the result when both conditions are present.

        Given: Multiple responses with various combinations
        When: validate_p_response is called
        Then: Results should be consistent regardless of implementation details

        This is a characterization test - it documents current behavior and
        ensures fixes don't break valid cases.
        """
        test_cases = [
            # (response, expected_allow, description)
            (
                "pytest PASSED\ngit status\n┌──────────┬─────────┐",
                True,
                "Both evidence and tables - should allow"
            ),
            (
                "┌──────────┬─────────┐\n│ Table   │ Data    │",
                False,
                "Only tables - should block"
            ),
            (
                "pytest PASSED\ngit status",
                True,
                "Only evidence - should allow"
            ),
            (
                "Plain text response",
                True,
                "Neither - should allow (fabrication check doesn't apply)"
            ),
        ]

        for response_text, expected_allow, description in test_cases:
            # Add completion indicator to make it valid
            full_response = f"## Pipeline Status: COMPLETE\n\n{response_text}"

            allow, reason = validate_p_response(full_response, check_for_completion=True)

            # For blocked responses, verify fabrication error
            if not expected_allow:
                assert allow is False, f"{description}: Expected False but got True"
                assert "FABRICATION DETECTED" in reason, f"{description}: Wrong error type"
            else:
                assert allow is True, f"{description}: Expected True but got False. Reason: {reason}"


    def test_tool_call_path_returns_early(self):
        """
        TEST-009: Verify tool call code path returns early with True.

        This tests the FIRST code path in check_execution_evidence():
        - Lines 75-77: If has_tool_calls is True, return True immediately
        - Tool calls are strong evidence - 1 is enough

        Given: A response contains tool call references (Read, Glob, Bash, Task)
        When: check_execution_evidence() is called
        Then: Should return (True, found) immediately without checking distinct patterns
        """
        from evidence_patterns import check_execution_evidence

        response_with_tool_calls = """
        Read(file.py)
        Glob(**/*.txt)
        Bash(ls -la)
        """

        has_evidence, found_patterns = check_execution_evidence(response_with_tool_calls)

        # Tool call path should return True immediately
        assert has_evidence is True, "Tool calls should be sufficient evidence"
        assert len(found_patterns) >= 3, "Should find all tool call matches"

    def test_no_tool_call_requires_two_patterns(self):
        """
        TEST-009: Verify no-tool-call code path requires 2 distinct pattern matches.

        This tests the SECOND code path in check_execution_evidence():
        - Lines 79-84: If no tool calls, need 2 distinct pattern matches
        - Must count DISTINCT pattern matches, not total string matches

        Given: A response has NO tool calls but has execution evidence patterns
        When: check_execution_evidence() is called
        Then:
            - With < 2 distinct patterns: should return (False, found)
            - With >= 2 distinct patterns: should return (True, found)

        This test verifies that the threshold is 2 patterns, not 3.
        """
        from evidence_patterns import check_execution_evidence

        # Test with only 1 pattern match (should fail)
        response_one_pattern = """
        pytest output
        """

        has_evidence, found = check_execution_evidence(response_one_pattern)

        # Should return False - only 1 pattern matched (pytest)
        assert has_evidence is False, "1 pattern should not be enough (need 2)"

        # Test with 2 pattern matches (should pass)
        response_two_patterns = """
        pytest PASSED
        git status
        """

        has_evidence, found = check_execution_evidence(response_two_patterns)

        # Should return True - 2 patterns matched (pytest, PASSED/FAILED, git)
        assert has_evidence is True, "2 distinct patterns should be sufficient"


class TestValidatePResponseIntegration:
    """
    Integration tests for validate_p_response function.
    """

    def test_non_p_response_bypasses_all_checks(self):
        """Non-/p responses should bypass fabrication checks entirely."""
        response = "This is just a regular conversation response"

        allow, reason = validate_p_response(response, check_for_completion=True)

        assert allow is True
        assert "Not a /p response" in reason

    def test_completion_indicator_required(self):
        """Test that completion format is properly detected."""
        response = """
pytest PASSED
git status
        """.strip()

        allow, reason = validate_p_response(response, check_for_completion=True)

        # Should bypass because no completion indicator
        assert allow is True
        assert "Not a completion message" in reason or "Not a /p response" in reason

    def test_halt_indicator_allows_evidence_without_completion(self):
        """Test that halt responses are validated differently."""
        response = """
## Pipeline Status: HALTED

pytest PASSED
git status

┌──────────┬─────────┐
│ Test     │ Result  │
└──────────┴─────────┘
        """.strip()

        allow, reason = validate_p_response(response, check_for_completion=False)

        # Should allow - halt format, has evidence, tables don't matter with evidence
        assert allow is True, f"Halt response with evidence blocked. Reason: {reason}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
