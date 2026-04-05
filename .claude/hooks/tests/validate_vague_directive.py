#!/usr/bin/env python3
"""
Test script for vague_directive_gate hook.

Run with: python test_vague_directive_gate.py
"""

import sys

sys.path.insert(0, "P:/.claude/hooks")

from PreToolUse_vague_directive_gate import check_directive


def test_case(description: str, directive: str, expected_allowed: bool):
    """Run a single test case."""
    allowed, message = check_directive(directive)

    status = "✓" if allowed == expected_allowed else "✗"
    result = "ALLOW" if allowed else "BLOCK"
    expected = "ALLOW" if expected_allowed else "BLOCK"

    print(f"{status} {description}")
    print(f"  Input: \"{directive[:60]}{'...' if len(directive) > 60 else ''}\"")
    print(f"  Result: {result} (expected: {expected})")

    if allowed != expected_allowed:
        print("  *** FAILED ***")
        if message:
            print(f"  Message: {message[:100]}")
    print()

    return allowed == expected_allowed


def main():
    print("=" * 60)
    print("Vague Directive Gate - Test Suite")
    print("=" * 60)
    print()

    tests = [
        # Should ALLOW (specific enough)
        ("Specific file + line", "Fix line 47 in cache.py", True),
        ("Specific file + function", "Add error handling to auth.get_user()", True),
        ("Specific file + action", "Add step 2A to debug.md", True),
        ("Question", "Does /debug add logging?", True),
        ("Authorization phrase", "Proceed with the changes", True),
        ("Explicit 'do it'", "Do it", True),
        ("File target + vague action", "Improve error handling in auth.py", True),

        # Should BLOCK (vague)
        ("Vague action, no target", "Make the debug workflow better", False),
        ("Vague 'improve', no target", "Improve error handling", False),
        ("Abstract scope, no target", "Refactor everything", False),
        ("Abstract 'system'", "Make the system more robust", False),
        ("Vague 'as good as'", "Make debug as good as it can be", False),
        ("Vague 'optimize'", "Optimize the codebase", False),
        ("Vague 'clean up'", "Clean up the code", False),

        # Edge cases
        ("Empty string", "", True),  # Fail open
        ("Just whitespace", "   ", True),  # Fail open
    ]

    passed = 0
    failed = 0

    for description, directive, expected in tests:
        if test_case(description, directive, expected):
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
