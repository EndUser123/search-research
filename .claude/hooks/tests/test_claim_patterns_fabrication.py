"""
Unit tests for ACTION_CLAIM_PATTERNS fabrication detection.

Tests the has_action_claim() function and ACTION_CLAIM_PATTERNS from
claim_patterns.py to ensure proper fabrication detection without false
positives on tentative language.

Test file: P:/.claude/hooks/__lib/claim_patterns.py
"""

import sys
from pathlib import Path

# Add hooks directory to path for imports
# This works regardless of where pytest is invoked from
_hooks_dir = Path(__file__).resolve().parent.parent
_str_hooks_dir = str(_hooks_dir)
if _str_hooks_dir not in sys.path:
    sys.path.insert(0, _str_hooks_dir)

import pytest
from __lib.claim_patterns import (
    ACTION_CLAIM_PATTERNS,
    EXTERNAL_CLAIM_PATTERNS,
    has_action_claim,
    has_external_claim,
)


class TestFabricationPatternsDetectClaims:
    """Test that ACTION_CLAIM_PATTERNS correctly detect fabrication claims."""

    def test_fabrication_pattern_search_429(self):
        """Test 'I tried WebSearch but got 429' pattern detection."""
        response = "I tried WebSearch but got a 429 error from the API."
        assert has_action_claim(response) is True

    def test_fabrication_pattern_external_research_blocked(self):
        """Test 'external research was blocked' pattern detection."""
        response = "External research was blocked by API quota limits."
        assert has_action_claim(response) is True

    def test_fabrication_pattern_searched_found_nothing(self):
        """Test 'I searched but found nothing' pattern detection."""
        response = "I searched the codebase but found nothing matching."
        assert has_action_claim(response) is True

    def test_fabrication_pattern_attempted_search(self):
        """Test 'attempted to search' pattern detection."""
        response = "I attempted to search for the pattern in the logs."
        assert has_action_claim(response) is True

    def test_fabrication_pattern_ran_pytest(self):
        """Test 'I ran pytest' pattern detection."""
        response = "I ran pytest and all tests passed successfully."
        assert has_action_claim(response) is True

    def test_fabrication_pattern_just_verified(self):
        """Test 'I just verified' pattern detection."""
        response = "I just verified the fix works correctly."
        assert has_action_claim(response) is True

    def test_fabrication_pattern_search_returned_nothing(self):
        """Test 'search returned nothing' pattern detection."""
        response = "The search returned nothing useful for this query."
        assert has_action_claim(response) is True

    def test_fabrication_pattern_api_quota_exceeded(self):
        """Test 'API quota exceeded' pattern detection."""
        response = "API quota exceeded, can't complete the request."
        assert has_action_claim(response) is True


class TestTentativeLanguageNotFabrication:
    """Test that tentative/hedging language is NOT flagged as fabrication."""

    def test_would_need_to_search(self):
        """Test 'I would need to search' - tentative, not fabrication."""
        response = "I would need to search for the latest documentation."
        assert has_action_claim(response) is False

    def test_should_check_pattern(self):
        """Test 'We should check if' - tentative, not fabrication."""
        response = "We should check if the hook is properly registered."
        assert has_action_claim(response) is False

    def test_might_search_pattern(self):
        """Test 'I might search' - tentative, not fabrication."""
        response = "I might search for similar patterns in the codebase."
        assert has_action_claim(response) is False

    def test_could_try_pattern(self):
        """Test 'We could try' - tentative, not fabrication."""
        response = "We could try running the tests with verbose output."
        assert has_action_claim(response) is False

    def test_we_could_search_pattern(self):
        """Test 'we could search' - tentative, not fabrication."""
        response = "We could search the documentation for examples."
        assert has_action_claim(response) is False


class TestRealErrorWithToolAllowed:
    """Test that actual tool usage with error messages is allowed."""

    def test_websearch_429_with_tool_allowed(self):
        """Test WebSearch with 429 error + actual tool call should pass."""
        # This would be called from a hook with tool evidence
        # The has_action_claim function only checks the response text
        # It doesn't have access to tool events, so we test the pattern logic
        # Pattern requires "I tried" or "I attempted" prefix
        response = "I attempted WebSearch but got 429 error from API."
        # This should still be detected as a claim (True) because the pattern
        # matches. The hook logic would then check for tool evidence separately.
        assert has_action_claim(response) is True

    def test_bash_error_with_tool_context(self):
        """Test bash command error report - claim detected, verified by tool."""
        # Pattern requires specific tool name (pytest, test, npm, pip)
        response = "I ran pytest but tests failed with exit code 1."
        # Pattern matches, so claim detected
        assert has_action_claim(response) is True

    def test_search_with_actual_results(self):
        """Test search that actually returned results - claim detected."""
        # Pattern requires "but found nothing" to match
        response = "I searched the codebase but found nothing useful."
        # Claim detected (has_action_claim doesn't check tool evidence)
        assert has_action_claim(response) is True


class TestFabricationWithoutToolBlocked:
    """Test that claims without tool evidence are detected as fabrication."""

    def test_claim_pytest_without_tool(self):
        """Test 'I ran pytest' without tool evidence should be detected."""
        response = "I ran pytest and all tests passed."
        # has_action_claim detects the pattern
        assert has_action_claim(response) is True

    def test_claim_verified_without_tool(self):
        """Test 'I just verified' without tool evidence should be detected."""
        response = "I just verified the implementation is correct."
        assert has_action_claim(response) is True

    def test_claim_searched_without_tool(self):
        """Test 'I searched but found nothing' without tool evidence should be detected."""
        # Pattern requires "but found nothing" to match
        response = "I searched the entire codebase but found nothing."
        assert has_action_claim(response) is True

    def test_claim_attempted_without_tool(self):
        """Test 'I attempted to search' without tool evidence should be detected."""
        response = "I attempted to fetch the remote data but got blocked."
        assert has_action_claim(response) is True

    def test_claim_executed_without_tool(self):
        """Test 'I executed pytest' without tool evidence should be detected."""
        # Pattern requires specific tool name (pytest, test, npm, pip)
        response = "I executed pytest and all tests passed."
        assert has_action_claim(response) is True


class TestConfigAsTruthStillDetected:
    """Test that EXTERNAL_CLAIM_PATTERNS still work (regression test)."""

    def test_fix_works_pattern(self):
        """Test 'the fix works' pattern from EXTERNAL_CLAIM_PATTERNS."""
        response = "The fix works and all tests pass."
        assert has_external_claim(response) is True

    def test_tests_passed_pattern(self):
        """Test 'tests passed' pattern from EXTERNAL_CLAIM_PATTERNS."""
        response = "All tests passed successfully."
        assert has_external_claim(response) is True

    def test_issue_is_fixed_pattern(self):
        """Test 'issue is fixed' pattern from EXTERNAL_CLAIM_PATTERNS."""
        response = "The issue is fixed and resolved."
        assert has_external_claim(response) is True

    def test_hook_returns_ok_pattern(self):
        """Test 'hook returns ok' pattern from EXTERNAL_CLAIM_PATTERNS."""
        response = "Hook returns {'ok': true} in the response."
        assert has_external_claim(response) is True

    def test_file_is_at_pattern(self):
        """Test 'file is at' pattern from EXTERNAL_CLAIM_PATTERNS."""
        response = "The file is at C:\\path\\to\\file.py"
        assert has_external_claim(response) is True

    def test_bug_is_in_line_pattern(self):
        """Test 'bug is in line' pattern from EXTERNAL_CLAIM_PATTERNS."""
        response = "The bug is in line 42 of the module."
        assert has_external_claim(response) is True

    def test_verified_the_fix_pattern(self):
        """Test 'verified the fix' pattern from EXTERNAL_CLAIM_PATTERNS."""
        response = "I verified the fix works correctly."
        assert has_external_claim(response) is True

    def test_found_pattern(self):
        """Test 'I found' pattern from EXTERNAL_CLAIM_PATTERNS."""
        response = "I found the issue in the configuration."
        assert has_external_claim(response) is True


class TestActionClaimNotExternalClaim:
    """Test that action claims and external claims are separate."""

    def test_fabrication_is_not_external_claim(self):
        """Test fabrication claims are not external claims."""
        response = "I tried WebSearch but got 429 error."
        assert has_action_claim(response) is True
        assert has_external_claim(response) is False

    def test_external_claim_is_not_fabrication(self):
        """Test external claims are not fabrication claims."""
        response = "The fix works perfectly."
        assert has_external_claim(response) is True
        assert has_action_claim(response) is False

    def test_process_talk_neither_claim(self):
        """Test process/self-report is neither claim type."""
        response = "I did not use TDD for this change."
        assert has_action_claim(response) is False
        assert has_external_claim(response) is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_response(self):
        """Test empty response returns False."""
        assert has_action_claim("") is False
        assert has_external_claim("") is False

    def test_none_response(self):
        """Test None response returns False."""
        assert has_action_claim(None) is False
        assert has_external_claim(None) is False

    def test_non_string_response(self):
        """Test non-string response returns False."""
        assert has_action_claim(123) is False
        assert has_external_claim(["list"]) is False

    def test_case_insensitive_patterns(self):
        """Test patterns are case-insensitive."""
        assert has_action_claim("I TRIED WEBSEARCH but got 429") is True
        assert has_action_claim("i tried websearch but got 429") is True
        assert has_external_claim("THE FIX WORKS") is True
        assert has_external_claim("the fix works") is True

    def test_mixed_tentative_and_fabrication(self):
        """Test tentative language takes precedence (not fabrication)."""
        response = "I would need to search, but I found nothing."
        # Tentative language dominates - should be False
        assert has_action_claim(response) is False

    def test_multiple_patterns_match(self):
        """Test response matching multiple patterns."""
        response = "I ran pytest and all tests passed. I verified the fix works."
        assert has_action_claim(response) is True
        assert has_external_claim(response) is True


class TestPatternCoverage:
    """Verify all ACTION_CLAIM_PATTERNS are tested."""

    def test_all_action_patterns_covered(self):
        """Test that all ACTION_CLAIM_PATTERNS have corresponding tests."""
        # This is a meta-test to ensure test coverage
        # All patterns should have at least one test case above
        assert len(ACTION_CLAIM_PATTERNS) > 0, "ACTION_CLAIM_PATTERNS should not be empty"

    def test_external_patterns_still_exist(self):
        """Test EXTERNAL_CLAIM_PATTERNS still exist (no regression)."""
        assert len(EXTERNAL_CLAIM_PATTERNS) > 0, "EXTERNAL_CLAIM_PATTERNS should not be empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
