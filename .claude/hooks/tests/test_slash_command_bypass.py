#!/usr/bin/env python3
"""Test that slash commands bypass UserPromptSubmit early-exit filter."""

import json
import subprocess
import sys


def test_slash_command_bypass():
    """Test that slash commands like /gto are not filtered out by early-exit."""
    print("Testing slash command early-exit bypass...")
    print()

    # Test cases: (prompt, expected_to_run, description)
    test_cases = [
        ("/gto", True, "4-char slash command"),
        ("/ask", True, "4-char slash command"),
        ("/arch", True, "5-char slash command"),
        ("/research", True, "9-char slash command"),
        ("hi", False, "2-char non-slash (too short)"),
        ("test", False, "4-char non-slash (exactly 4 chars, should be filtered)"),
        ("hello", True, "5-char non-slash (exactly 5 chars, should pass)"),
    ]

    passed = 0
    failed = 0

    for prompt, expected_to_run, description in test_cases:
        # Prepare input
        input_data = json.dumps({"prompt": prompt, "message": prompt, "session_id": "test"})

        # Run UserPromptSubmit.py
        result = subprocess.run(
            [sys.executable, "P:/.claude/hooks/UserPromptSubmit.py"],
            input=input_data,
            capture_output=True,
            text=True,
            cwd="P:/.claude/hooks"
        )

        # Check if hooks ran (output has hookSpecificOutput with additionalContext)
        try:
            output = json.loads(result.stdout.strip())
            has_content = (
                isinstance(output, dict) and
                "hookSpecificOutput" in output and
                isinstance(output["hookSpecificOutput"], dict) and
                output["hookSpecificOutput"].get("additionalContext") and
                len(output["hookSpecificOutput"].get("additionalContext", "")) > 0
            )
        except json.JSONDecodeError:
            has_content = False

        # Verify expectation
        success = (has_content == expected_to_run)

        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")
        print(f"  Prompt: '{prompt}' (len={len(prompt)})")
        print(f"  Expected hooks to run: {expected_to_run}")
        print(f"  Hooks ran: {has_content}")
        print()

        if success:
            passed += 1
        else:
            failed += 1

    # Summary
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0

if __name__ == "__main__":
    success = test_slash_command_bypass()
    sys.exit(0 if success else 1)
