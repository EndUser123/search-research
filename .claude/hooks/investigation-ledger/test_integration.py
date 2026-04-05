#!/usr/bin/env python3
"""
Test: Investigation Ledger Integration

Verifies that the investigation-ledger system blocks claims without investigation.
"""

import sys
from pathlib import Path

# Setup paths
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "investigation-ledger"))

from ledger import get_investigation_stats, record_file_read, reset_ledger
from validate_claims import validate_claims


def test_blocks_claims_without_investigation():
    """Claims about system behavior should be blocked when no files were read."""
    # Reset ledger to ensure clean state
    reset_ledger()

    # Response with claims but no investigation (must be > 100 chars)
    response = """The hook system architecture works by intercepting tool calls at multiple lifecycle points. 
    The PreToolUse hooks validate actions before execution, while PostToolUse hooks analyze results. 
    The Stop hooks validate the final response for quality and compliance with constitutional rules."""

    result = validate_claims(response)

    assert not result["valid"], f"Expected invalid, got: {result}"
    assert "CLAIM WITHOUT INVESTIGATION" in result["message"] or "UNSUBSTANTIATED" in result["message"]
    print("✓ test_blocks_claims_without_investigation passed")


def test_allows_claims_after_investigation():
    """Claims should be allowed after relevant files have been read."""
    # Reset and record file read
    reset_ledger()
    record_file_read("P:/.claude/hooks/Stop_router.py")

    stats = get_investigation_stats()
    assert stats["files_read"] >= 1, f"File read not recorded: {stats}"

    # Response with claims about investigated topic
    response = "The hook system works by intercepting tool calls and validating them."

    result = validate_claims(response)

    # Should be valid now (either because topics match or evidence markers)
    assert result["valid"], f"Expected valid after investigation, got: {result}"
    print("✓ test_allows_claims_after_investigation passed")


def test_allows_short_responses():
    """Short responses (< 100 chars) should be allowed without investigation."""
    reset_ledger()

    response = "Yes, I can help with that."
    result = validate_claims(response)

    assert result["valid"], f"Expected valid for short response, got: {result}"
    print("✓ test_allows_short_responses passed")


def test_allows_questions():
    """Questions should be allowed without investigation."""
    reset_ledger()

    response = "Can you provide more details about what you're trying to accomplish?"
    result = validate_claims(response)

    assert result["valid"], f"Expected valid for question, got: {result}"
    print("✓ test_allows_questions passed")


if __name__ == "__main__":
    print("Running investigation ledger integration tests...")
    print()

    test_blocks_claims_without_investigation()
    test_allows_claims_after_investigation()
    test_allows_short_responses()
    test_allows_questions()

    print()
    print("All tests passed! ✓")
