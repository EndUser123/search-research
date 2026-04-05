#!/usr/bin/env python3
"""Tests for is_test_report_context and its interaction with mentions_history_or_blame."""

import sys

sys.path.insert(0, "P:/.claude/hooks")
sys.path.insert(0, "P:/.claude/hooks/__lib")

from __lib.claim_classifier import is_test_report_context, mentions_history_or_blame


def test_test_report_with_pre_existing():
    """Test report using 'pre-existing' as classification should be exempted."""
    test_report = (
        "Test Coverage Report: Stop_historical_claims_gate.py\n"
        "Coverage: 16%\n"
        "6/10 passed\n"
        "Gaps Identified:\n"
        "Priority 1 - pre-existing gaps in tier1_check()\n"
        "Priority 2 - missing edge case tests"
    )
    assert is_test_report_context(test_report), "Should detect test report context"
    claim = "pre-existing gaps in tier1_check()"
    assert mentions_history_or_blame(claim), "Claim itself still matches blame pattern"
    print("PASS: test_report_with_pre_existing")


def test_blame_shifting_without_test_context():
    """Plain blame-shifting text should NOT be exempted."""
    blame_text = (
        "The bug is pre-existing and was not introduced by my changes.\n"
        "I only modified the patterns, the core logic was already broken."
    )
    assert not is_test_report_context(blame_text), "Should NOT detect test report context"
    assert mentions_history_or_blame("The bug is pre-existing"), "Should detect blame"
    print("PASS: blame_shifting_without_test_context")


def test_exact_chat_history_scenario():
    """The exact scenario from the chat history that caused 1m43s churn."""
    chat_response = (
        "Test Coverage Report: Stop_historical_claims_gate.py\n"
        "Pytest Coverage Report (pytest-cov)\n"
        "Module                      Stmts   Miss  Cover\n"
        "Stop_historical_claims_gate   298    250    16%\n"
        "Test Files Found\n"
        "- tests/test_historical_claims.py (10 cases - 6/10 passed)\n"
        "- tests/test_stop_historical_claims.py (6 pytest tests - 4 failed)\n"
        "Coverage by Type\n"
        "Unit Tests\n"
        "check_historical_test_claims() - NOT directly tested\n"
        "Gaps Identified\n"
        "Priority 1 - Critical Gaps:\n"
        "These test failures appear to be pre-existing issues\n"
        "Evidence: coverage shows only 16% covered"
    )
    assert is_test_report_context(chat_response), "Should detect the real scenario"
    print("PASS: exact_chat_history_scenario")


def test_plain_blame_text():
    """Plain text with just blame language should NOT be exempted."""
    plain = "This is a pre-existing problem, not caused by my changes."
    assert not is_test_report_context(plain), "Plain text should not be exempted"
    print("PASS: plain_blame_text")


def test_not_a_test_report():
    """Regular code discussion should not be detected as test report."""
    code_discussion = (
        "The function takes two arguments and returns a dict.\n"
        "I refactored the loop to use a list comprehension.\n"
        "This is a pre-existing design choice."
    )
    assert not is_test_report_context(code_discussion)
    print("PASS: not_a_test_report")


def test_test_report_without_blame():
    """Test report without blame language should still be detected as test report."""
    clean_report = (
        "Test Coverage Report\n"
        "Coverage: 85%\n"
        "10/10 passed\n"
        "All tests green."
    )
    assert is_test_report_context(clean_report), "Clean test report should still match"
    print("PASS: test_report_without_blame")


def test_threshold_requires_two_markers():
    """A single marker is not enough - needs at least 2."""
    one_marker = "Coverage: 42% and nothing else interesting here."
    assert not is_test_report_context(one_marker), "Single marker should not match"
    print("PASS: threshold_requires_two_markers")


if __name__ == "__main__":
    test_test_report_with_pre_existing()
    test_blame_shifting_without_test_context()
    test_exact_chat_history_scenario()
    test_plain_blame_text()
    test_not_a_test_report()
    test_test_report_without_blame()
    test_threshold_requires_two_markers()
    print("\nAll 7 tests PASSED")
