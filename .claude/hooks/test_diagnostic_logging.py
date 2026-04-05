#!/usr/bin/env python3
"""
Test Stop_router diagnostic logging by simulating CC's input.

This verifies the diagnostic patch works before waiting for CC to execute.
"""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent


def test_missing_response_field():
    """Test when response field is completely absent."""
    print("\n=== Test 1: Missing response field ===")

    input_data = {
        "transcript_path": "/fake/path",
        "conversation": []
        # Note: no "response" field
    }

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "Stop_router.py")],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd=str(HOOKS_DIR)
    )

    print(f"Exit code: {result.returncode}")
    print("\nStderr output:")
    print(result.stderr)
    print("\nStdout output:")
    print(result.stdout)

    # Check for diagnostic message
    if "DIAGNOSTIC" in result.stderr:
        print("\n✅ Diagnostic logging detected!")
        if "response_field_present: False" in result.stderr:
            print("✅ Correctly identified missing field")
    else:
        print("\n❌ No diagnostic message found")

    return result


def test_empty_response_field():
    """Test when response field exists but is empty."""
    print("\n=== Test 2: Empty response field ===")

    input_data = {
        "transcript_path": "/fake/path",
        "conversation": [],
        "response": ""  # Field present but empty
    }

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "Stop_router.py")],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd=str(HOOKS_DIR)
    )

    print(f"Exit code: {result.returncode}")
    print("\nStderr output:")
    print(result.stderr)

    # Check for both diagnostics
    if "DIAGNOSTIC" in result.stderr:
        print("\n✅ Diagnostic logging detected!")
        if "response_field_present: True" in result.stderr:
            print("✅ Correctly identified empty string")

    if "WARNING" in result.stderr and "Pattern-detection hooks" in result.stderr:
        print("✅ Pattern hook warning detected!")

    return result


def test_with_response():
    """Test when response field has content."""
    print("\n=== Test 3: Valid response field ===")

    input_data = {
        "transcript_path": "/fake/path",
        "conversation": [],
        "response": "You're absolutely right! Great question."
    }

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "Stop_router.py")],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd=str(HOOKS_DIR)
    )

    print(f"Exit code: {result.returncode}")

    # Should NOT see diagnostics
    if "DIAGNOSTIC" not in result.stderr:
        print("✅ No diagnostic message (correct)")
    else:
        print("❌ Unexpected diagnostic message")

    if "WARNING" not in result.stderr:
        print("✅ No warning message (correct)")
    else:
        print("❌ Unexpected warning message")

    return result


if __name__ == "__main__":
    print("Testing Stop_router diagnostic logging...")
    print("=" * 80)

    test_missing_response_field()
    test_empty_response_field()
    test_with_response()

    print("\n" + "=" * 80)
    print("Test complete. Check output above for diagnostic messages.")
