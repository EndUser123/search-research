#!/usr/bin/env python3
"""Test suite for block_protocol.py

Tests the standardized Stop hook protocol:
- Exit code 2 = BLOCK (with stderr message)
- Exit code 0 = ALLOW
- block_response() / allow_response() functions
- Audit logging to block_enforcement.jsonl
"""

import json
import sys
import tempfile
from pathlib import Path

# Add hooks to path
hooks_dir = Path("P:/.claude/hooks")
sys.path.insert(0, str(hooks_dir))

from block_protocol import (
    BLOCK_LOG,
    allow_response,
    block_response,
    conditional_block,
    is_block_result,
    make_allow_result,
    make_block_result,
)

# Override BLOCK_LOG for testing
_test_log = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.jsonl')
import block_protocol

original_block_log = BLOCK_LOG
block_protocol.BLOCK_LOG = Path(_test_log.name)


def cleanup():
    try:
        Path(_test_log.name).unlink(missing_ok=True)
    except:
        pass


def test_block_response_exits_2():
    """Test: block_response exits with code 2"""
    print("\nTest: block_response exits with code 2")
    try:
        block_response(reason="test violation", hook="test_hook")
        print("  ✗ FAIL: Should have exited")
        return False
    except SystemExit as e:
        if e.code == 2:
            print(f"  ✓ PASS: Exited with code {e.code}")
            return True
        else:
            print(f"  ✗ FAIL: Exited with code {e.code}, expected 2")
            return False


def test_allow_response_exits_0():
    """Test: allow_response exits with code 0"""
    print("\nTest: allow_response exits with code 0")
    try:
        allow_response()
        print("  ✗ FAIL: Should have exited")
        return False
    except SystemExit as e:
        if e.code == 0:
            print(f"  ✓ PASS: Exited with code {e.code}")
            return True
        else:
            print(f"  ✗ FAIL: Exited with code {e.code}, expected 0")
            return False


def test_conditional_block():
    """Test: conditional_block blocks when True, allows when False"""
    print("\nTest: conditional_block")

    # Test condition=True (should block)
    try:
        conditional_block(condition=True, reason="blocked", hook="test")
        print("  ✗ FAIL: Should have exited (condition=True)")
        result1 = False
    except SystemExit as e:
        result1 = (e.code == 2)
        print(f"  condition=True: exit code {e.code} {'✓' if result1 else '✗'}")

    # Clear test log
    Path(_test_log.name).write_text("")

    # Test condition=False (should allow)
    try:
        conditional_block(condition=False, reason="blocked", hook="test")
        print("  ✗ FAIL: Should have exited (condition=False)")
        result2 = False
    except SystemExit as e:
        result2 = (e.code == 0)
        print(f"  condition=False: exit code {e.code} {'✓' if result2 else '✗'}")

    if result1 and result2:
        print("  ✓ PASS")
        return True
    return False


def test_block_audit_log():
    """Test: block_response logs to audit file"""
    print("\nTest: block_response logs audit entry")

    # Clear log
    Path(_test_log.name).write_text("")

    try:
        block_response(reason="test reason", hook="test_hook")
    except SystemExit:
        pass

    # Read log
    log_content = Path(_test_log.name).read_text()
    if log_content:
        entry = json.loads(log_content.strip())
        if entry.get("hook") == "test_hook" and entry.get("action") == "block":
            print(f"  ✓ PASS: Log entry found - hook={entry.get('hook')}, action={entry.get('action')}")
            return True
        else:
            print(f"  ✗ FAIL: Wrong log entry: {entry}")
            return False
    else:
        print("  ✗ FAIL: No log entry written")
        return False


def test_make_block_result_no_exit():
    """Test: make_block_result returns dict without exiting"""
    print("\nTest: make_block_result returns dict without exiting")
    result = make_block_result(reason="test", hook="h")

    expected = {"decision": "block", "reason": "test", "_hook": "h"}
    if result == expected:
        print(f"  ✓ PASS: {result}")
        return True
    else:
        print(f"  ✗ FAIL: Expected {expected}, got {result}")
        return False


def test_make_allow_result():
    """Test: make_allow_result returns correct dict"""
    print("\nTest: make_allow_result")

    result1 = make_allow_result()
    if result1 != {}:
        print(f"  ✗ FAIL (empty): Expected {{}}, got {result1}")
        return False

    result2 = make_allow_result(message="info")
    expected = {"systemMessage": "info"}
    if result2 == expected:
        print(f"  ✓ PASS: empty={result1}, with message={result2}")
        return True
    else:
        print(f"  ✗ FAIL: Expected {expected}, got {result2}")
        return False


def test_is_block_result():
    """Test: is_block_result checks decision field"""
    print("\nTest: is_block_result")

    tests = [
        ({"decision": "block"}, True),
        ({}, False),
        ({"decision": "allow"}, False),
        ({"other": "value"}, False),
    ]

    all_pass = True
    for input_data, expected in tests:
        result = is_block_result(input_data)
        if result == expected:
            print(f"  ✓ {input_data} -> {result}")
        else:
            print(f"  ✗ {input_data} -> {result}, expected {expected}")
            all_pass = False

    if all_pass:
        print("  ✓ PASS")
    return all_pass


# Run tests
print("=" * 60)
print("Testing block_protocol.py")
print("=" * 60)

try:
    tests = [
        test_block_response_exits_2,
        test_allow_response_exits_0,
        test_conditional_block,
        test_block_audit_log,
        test_make_block_result_no_exit,
        test_make_allow_result,
        test_is_block_result,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

finally:
    cleanup()

# Summary
print("\n" + "=" * 60)
passed = sum(results)
total = len(results)
print(f"Results: {passed}/{total} passed")

if passed == total:
    print("✓ All tests passed!")
    sys.exit(0)
else:
    print("✗ Some tests failed")
    sys.exit(1)
