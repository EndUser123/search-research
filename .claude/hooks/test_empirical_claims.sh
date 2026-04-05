#!/usr/bin/env python3
"""Comprehensive test suite for empirical_claims_gate.py

Tests the hook's exit codes and blocking behavior for various scenarios.
"""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")
HOOK_FILE = HOOKS_DIR / "empirical_claims_gate.py"


def run_hook(messages: list, tools_used: list = None) -> tuple[int, str, str]:
    """Run hook with given messages, return (exit_code, stdout, stderr)."""
    import os
    input_data = {
        "type": "transcript",
        "messages": messages,
        "tools_used": tools_used or []
    }

    # Set environment variable
    env = os.environ.copy()
    env["EMPIRICAL_CLAIMS_GATE_ENABLED"] = "true"

    result = subprocess.run(
        [sys.executable, str(HOOK_FILE)],
        input=json.dumps(input_data).encode(),
        capture_output=True,
        timeout=5,
        env=env
    )

    return (
        result.returncode,
        result.stdout.decode(),
        result.stderr.decode()
    )


def test_unverified_enumeration():
    """Test 1: Enumeration claim without tools should BLOCK (exit 2)."""
    print("Test 1: Unverified enumeration (should block with exit 2)...")

    messages = [
        {"role": "user", "content": "How many tasks have the tag?"},
        {"role": "assistant", "content": "Found 13 tasks with the tag already."}
    ]

    exit_code, stdout, stderr = run_hook(messages, tools_used=[])

    if exit_code == 2:
        print("  ✓ PASS: Blocked with exit code 2")
        if stderr:
            print(f"    stderr: {stderr[:100]}")
        return True
    else:
        print(f"  ✗ FAIL: Expected exit 2, got {exit_code}")
        print(f"    stdout: {stdout[:200]}")
        print(f"    stderr: {stderr[:200]}")
        return False


def test_verified_enumeration():
    """Test 2: Enumeration claim WITH tools should ALLOW (exit 0)."""
    print("Test 2: Verified enumeration with tools (should allow with exit 0)...")

    messages = [
        {"role": "user", "content": "How many tasks have the tag?"},
        {"role": "assistant", "content": "Found 13 tasks with the tag."}
    ]

    exit_code, stdout, stderr = run_hook(messages, tools_used=[{"name": "Grep"}])

    if exit_code == 0:
        print("  ✓ PASS: Allowed with exit code 0")
        return True
    else:
        print(f"  ✗ FAIL: Expected exit 0, got {exit_code}")
        print(f"    stdout: {stdout[:200]}")
        return False


def test_general_knowledge():
    """Test 3: General knowledge without tools should ALLOW (exit 0)."""
    print("Test 3: General knowledge (should allow with exit 0)...")

    messages = [
        {"role": "user", "content": "What is Git?"},
        {"role": "assistant", "content": "Git is a distributed version control system designed for tracking changes in source code during software development."}
    ]

    exit_code, stdout, stderr = run_hook(messages, tools_used=[])

    if exit_code == 0:
        print("  ✓ PASS: Allowed with exit code 0")
        return True
    else:
        print(f"  ✗ FAIL: Expected exit 0, got {exit_code}")
        return False


def test_success_claim_without_execution():
    """Test 4: Success claim without execution should BLOCK (exit 2)."""
    print("Test 4: Success claim without execution (should block with exit 2)...")

    messages = [
        {"role": "user", "content": "Fix the bug"},
        {"role": "assistant", "content": "The bug is now fixed and working correctly."}
    ]

    exit_code, stdout, stderr = run_hook(messages, tools_used=[])

    if exit_code == 2:
        print("  ✓ PASS: Blocked with exit code 2")
        return True
    else:
        print(f"  ✗ FAIL: Expected exit 2, got {exit_code}")
        print(f"    stdout: {stdout[:200]}")
        return False


def test_code_behavior_claim_without_reading():
    """Test 5: Code behavior claim without reading should BLOCK (exit 2)."""
    print("Test 5: Code behavior claim without reading (should block with exit 2)...")

    messages = [
        {"role": "user", "content": "How does this function work?"},
        {"role": "assistant", "content": "The function handles user authentication by validating tokens and checking permissions."}
    ]

    exit_code, stdout, stderr = run_hook(messages, tools_used=[])

    if exit_code == 2:
        print("  ✓ PASS: Blocked with exit code 2")
        return True
    else:
        print(f"  ✗ FAIL: Expected exit 2, got {exit_code}")
        return False


def main():
    print("=" * 60)
    print("Testing empirical_claims_gate.py")
    print("=" * 60)
    print()

    tests = [
        test_unverified_enumeration,
        test_verified_enumeration,
        test_general_knowledge,
        test_success_claim_without_execution,
        test_code_behavior_claim_without_reading,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            results.append(False)
        print()

    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} passed")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
