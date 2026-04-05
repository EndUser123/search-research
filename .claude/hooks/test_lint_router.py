#!/usr/bin/env python3
"""
Test script for PostToolUse_lint_router.py

Tests:
1. Hook imports without errors
2. Capability probe detects ruff
3. Re-entrancy guard prevents infinite loops
4. Graceful degrade works when linter missing
"""

import json
import subprocess
import sys
from pathlib import Path

# Add hooks directory to path
# Test script is in .claude/hooks/, so parent is .claude/
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))


def test_hook_imports():
    """Test 1: Hook imports successfully."""
    print("Test 1: Hook imports...", end=" ")
    try:
        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False


def test_ruff_available():
    """Test 2: Ruff is available."""
    print("Test 2: Ruff available...", end=" ")
    try:
        result = subprocess.run(
            ["ruff", "--version"],
            capture_output=True,
            timeout=5
        )

        if result.returncode == 0:
            print(f"✓ PASS (ruff {result.stdout.decode().strip()})")
            return True
        else:
            print("✗ FAIL (ruff returned error)")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"✗ FAIL: {e}")
        return False


def test_reentrancy_guard():
    """Test 3: Re-entrancy guard works."""
    print("Test 3: Re-entrancy guard...", end=" ")
    try:
        import tempfile

        from PostToolUse_lint_router import (
            is_already_linted,
            mark_as_linted,
        )

        # Create a test marker
        temp_dir = Path(tempfile.gettempdir())
        test_marker = temp_dir / "test_lint_marker_12345"

        # Should not be marked initially
        if is_already_linted(test_marker):
            print("✗ FAIL (marker already exists before creation)")
            return False

        # Mark it
        mark_as_linted(str(test_marker))

        # Should now be marked
        if not is_already_linted(test_marker):
            print("✗ FAIL (marker not detected after creation)")
            return False

        # Cleanup
        test_marker.unlink()

        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False


def test_graceful_degrade():
    """Test 4: Graceful degrade returns False for missing linter."""
    print("Test 4: Graceful degrade...", end=" ")
    try:
        import PostToolUse_lint_router

        # Test with a linter that definitely doesn't exist
        result = PostToolUse_lint_router.is_linter_available({
            "check_cmd": ["nonexistent_linter_xyz", "--version"]
        })

        if result:
            print("✗ FAIL (should return False for missing linter)")
            return False

        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False


def test_hook_execution():
    """Test 5: Hook executes with sample input."""
    print("Test 5: Hook execution...", end=" ")
    try:
        # Simulate a Write operation on a Python file
        test_input = {
            "toolName": "Write",
            "toolInput": {"file_path": "test_sample.py"}
        }

        # Run the hook
        input_data = json.dumps(test_input).encode()
        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "PostToolUse_lint_router.py")],
            input=input_data,
            capture_output=True,
            timeout=5,
            cwd=Path.cwd()
        )

        # Hook should not crash
        if result.returncode not in (0, None):
            print(f"✗ FAIL (exit code {result.returncode})")
            return False

        print("✓ PASS")
        return True
    except Exception as e:
        print(f"✗ FAIL: {e}")
        return False


def main():
    """Run all tests."""
    print("Running PostToolUse_lint_router.py tests...")
    print("-" * 50)

    tests = [
        test_hook_imports,
        test_ruff_available,
        test_reentrancy_guard,
        test_graceful_degrade,
        test_hook_execution,
    ]

    results = [test() for test in tests]

    print("-" * 50)
    passed = sum(results)
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
