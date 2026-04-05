#!/usr/bin/env python3
"""Test the investigation read fix for contract enforcer."""

import sys
from pathlib import Path

# Add hooks to path
hooks_dir = Path("P:/.claude/hooks")
sys.path.insert(0, str(hooks_dir))

# Import the functions we want to test
from PreToolUse.contract_enforcer import (
    _is_investigation_intent,
    _is_read_only_bash_command,
)


def test_read_only_command_detection():
    """Test that read-only commands are correctly identified."""
    print("Testing read-only command detection...")

    # Should be True (read-only)
    assert _is_read_only_bash_command("ls -la"), "ls should be read-only"
    assert _is_read_only_bash_command("cat file.py"), "cat should be read-only"
    assert _is_read_only_bash_command("grep pattern file.txt"), "grep should be read-only"
    assert _is_read_only_bash_command("head -20 file.py"), "head should be read-only"
    assert _is_read_only_bash_command("find /path -type f -name '*.py'"), "find without -delete should be read-only"

    # Should be False (substantive)
    assert not _is_read_only_bash_command("rm file.txt"), "rm should NOT be read-only"
    assert not _is_read_only_bash_command("mv a.txt b.txt"), "mv should NOT be read-only"
    assert not _is_read_only_bash_command("python script.py"), "python should NOT be read-only"
    assert not _is_read_only_bash_command("find /path -delete"), "find -delete should NOT be read-only"

    print("✅ Read-only command detection: PASSED")

def test_investigation_intent_detection():
    """Test that investigation intent is correctly identified."""
    print("\nTesting investigation intent detection...")

    # Should be True (investigation intent)
    assert _is_investigation_intent("investigate the code structure"), "investigate keyword"
    assert _is_investigation_intent("understand how X works"), "understand keyword"
    assert _is_investigation_intent("analyze the architecture"), "analyze keyword"
    assert _is_investigation_intent("review the implementation"), "review keyword"
    assert _is_investigation_intent("show me the code"), "show code pattern"
    assert _is_investigation_intent("check how this is implemented"), "check pattern"

    # Should be False (non-investigation)
    assert not _is_investigation_intent("run the tests"), "run is not investigation"
    assert not _is_investigation_intent("deploy to production"), "deploy is not investigation"
    assert not _is_investigation_intent("delete the file"), "delete is not investigation"
    assert not _is_investigation_intent(""), "empty string"

    print("✅ Investigation intent detection: PASSED")

def test_combined_logic():
    """Test the combined logic of command + intent."""
    print("\nTesting combined logic (command + intent)...")

    # Scenario 1: Investigation with read-only command
    command = "ls -la P:/.claude/hooks/"
    user_message = "investigate the hooks directory structure"

    is_safe_command = _is_read_only_bash_command(command)
    has_investigative_intent = _is_investigation_intent(user_message)

    assert is_safe_command, "ls should be detected as read-only"
    assert has_investigative_intent, "message should be detected as investigation"
    print(f"  ✓ {command} + '{user_message}' = ALLOWED")

    # Scenario 2: Substantive command (not read-only)
    command2 = "rm file.txt"
    user_message2 = "investigate by deleting files"

    is_safe_command2 = _is_read_only_bash_command(command2)
    has_investigative_intent2 = _is_investigation_intent(user_message2)

    assert not is_safe_command2, "rm should NOT be detected as read-only"
    assert has_investigative_intent2, "message should still be detected as investigation"
    print(f"  ✓ {command2} + '{user_message2}' = BLOCKED (command not read-only)")

    # Scenario 3: Read-only command without investigation intent
    command3 = "cat file.py"
    user_message3 = "run the script"

    is_safe_command3 = _is_read_only_bash_command(command3)
    has_investigative_intent3 = _is_investigation_intent(user_message3)

    assert is_safe_command3, "cat should be detected as read-only"
    assert not has_investigative_intent3, "'run the script' should NOT be investigation"
    print(f"  ✓ {command3} + '{user_message3}' = BLOCKED (no investigation intent)")

    print("\n✅ Combined logic: PASSED")

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Investigation Read Fix")
    print("=" * 60)

    try:
        test_read_only_command_detection()
        test_investigation_intent_detection()
        test_combined_logic()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✅")
        print("=" * 60)
        print("\nSummary:")
        print("- Read-only command detection works correctly")
        print("- Investigation intent detection works correctly")
        print("- Combined logic (command + intent) works correctly")
        print("\nThe fix allows:")
        print("  ✓ ls, cat, grep, head, etc. for investigation")
        print("  ✗ rm, mv, python, etc. still require contract")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
