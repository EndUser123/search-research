#!/usr/bin/env python3
"""Functional test for repository visibility guard hook - bypasses PreToolUse router."""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOK_PATH = HOOKS_DIR / "PreToolUse_repo_visibility_guard.py"


def test_hook_blocks_p_drive_public():
    r"""Test that hook blocks P:\ drive repos from being made public."""
    # Simulate being in P:\ drive repo
    test_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "gh repo edit owner/repo --visibility public"
        }
    }

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5,
        cwd="P:\\"  # Ensure we're in P:\ drive
    )

    # Should block (exit code 2)
    assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"

    # Should output valid JSON
    output = json.loads(result.stdout)
    assert output["decision"] == "block"
    assert "visibility change blocked" in output["reason"].lower()

    print(r"✓ Test 1 PASSED: Hook blocks P:\ drive public visibility change")


def test_hook_allows_private_visibility():
    """Test that hook allows repos to be made private."""
    test_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "gh repo edit owner/repo --visibility private"
        }
    }

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5,
        cwd="P:\\"
    )

    # Should allow (exit code 0)
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
    print("✓ Test 2 PASSED: Hook allows private visibility change")


def test_hook_allows_safe_commands():
    """Test that hook allows safe git commands."""
    test_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "git status"
        }
    }

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Should allow (exit code 0)
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
    print("✓ Test 3 PASSED: Hook allows safe git commands")


def test_hook_bypass_flag():
    """Test that bypass flag works."""
    test_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "gh repo edit owner/repo --visibility public --allow-visibility-change"
        }
    }

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5,
        cwd="P:\\"
    )

    # Should allow due to bypass flag (exit code 0)
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"
    print("✓ Test 4 PASSED: Bypass flag works correctly")


def test_hook_error_message_quality():
    """Test that error messages are helpful."""
    test_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "gh repo edit owner/repo --visibility public"
        }
    }

    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5,
        cwd="P:\\"
    )

    output = json.loads(result.stdout)

    # Check error message contains helpful information
    reason = output["reason"].lower()
    assert "p: drive" in reason
    assert "protected" in reason
    assert "packages/" in reason
    assert "--allow-visibility-change" in reason

    print("✓ Test 5 PASSED: Error messages are helpful and informative")


if __name__ == "__main__":
    print("Running functional tests for repository visibility guard...\n")

    try:
        test_hook_blocks_p_drive_public()
        test_hook_allows_private_visibility()
        test_hook_allows_safe_commands()
        test_hook_bypass_flag()
        test_hook_error_message_quality()

        print("\n" + "="*60)
        print("ALL FUNCTIONAL TESTS PASSED ✓")
        print("="*60)
        print("\nThe repository visibility guard hook is working correctly!")
        print(r"It protects P:\ drive repos from accidental public exposure.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
