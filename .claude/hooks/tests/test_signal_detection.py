#!/usr/bin/env python3
"""Test signal detection for competence_injector conditional injection."""

import json
import re
import sys
import time
from pathlib import Path

# Fix intent patterns (copied from competence_injector)
FIX_INTENT_PATTERNS = re.compile(
    r"\b(fix|debug|error|broken|crash(?:ed|es|ing)?|fail(?:ed|s|ing)?|"
    r"bug|issue|wrong|not working|"
    r"doesn't work|doesn't work|won't|can't|cannot|exception|traceback|"
    r"stacktrace|stack trace|segfault|panic|abort)\b",
    re.IGNORECASE,
)


def test_fix_intent_detection():
    """Test that fix/debug intent is correctly detected from prompts."""
    test_cases = [
        ("fix the broken hook", True),
        ("debug this error", True),
        ("the test is failing", True),
        ("please add a new feature", False),
        ("list all files", False),
        ("there is a bug in the code", True),
        ("this exception needs handling", True),
        ("refactor the module", False),
        ("it crashed on startup", True),
        ("can't import the module", True),
        ("implement dark mode", False),
    ]

    all_pass = True
    for prompt, expected in test_cases:
        result = bool(FIX_INTENT_PATTERNS.search(prompt))
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_pass = False
        print(f"  {status}: \"{prompt}\" -> {result} (expected {expected})")

    return all_pass


def test_signal_file_roundtrip():
    """Test signal file creation and reading."""
    signal_dir = Path("P:/.claude/state/signals")
    signal_dir.mkdir(parents=True, exist_ok=True)
    signal_file = signal_dir / "last_tool_error.json"

    # Write
    signal_file.write_text(
        json.dumps({
            "timestamp": time.time(),
            "tool_name": "Bash",
            "command": "python test.py",
        }),
        encoding="utf-8",
    )

    # Read
    data = json.loads(signal_file.read_text(encoding="utf-8"))
    age = time.time() - data["timestamp"]
    print(f"  Signal file age: {age:.2f}s, tool: {data['tool_name']}")

    # Clean up
    signal_file.unlink(missing_ok=True)

    return age < 5


def test_stop_advisory_shortcut_patterns():
    """Test that Stop_advisory detects lazy shortcut language."""
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from Stop_advisory import check_advisories

    shortcut_responses = [
        "This is just a cosmetic error, you can safely ignore it.",
        "As a workaround, you can restart the service.",
        "You can ignore this warning, it's harmless.",
        "The cosmetic issue in the output doesn't affect functionality.",
    ]

    clean_responses = [
        "I fixed the root cause by updating the import path.",
        "The test passes after correcting the schema.",
        "Here is the implementation of the new feature.",
    ]

    all_pass = True
    for resp in shortcut_responses:
        suggestions = check_advisories(resp)
        has_shortcut = any("root cause" in s.lower() or "dismissing" in s.lower() or "workaround" in s.lower() for s in suggestions)
        status = "PASS" if has_shortcut else "FAIL"
        if not has_shortcut:
            all_pass = False
        print(f"  {status}: shortcut detected in: \"{resp[:50]}...\" -> {suggestions}")

    for resp in clean_responses:
        suggestions = check_advisories(resp)
        has_shortcut = any("root cause" in s.lower() or "dismissing" in s.lower() or "workaround" in s.lower() for s in suggestions)
        status = "PASS" if not has_shortcut else "FAIL"
        if has_shortcut:
            all_pass = False
        print(f"  {status}: no shortcut in: \"{resp[:50]}...\" -> {suggestions}")

    return all_pass


if __name__ == "__main__":
    print("=== Test: Fix Intent Detection ===")
    r1 = test_fix_intent_detection()

    print("\n=== Test: Signal File Roundtrip ===")
    r2 = test_signal_file_roundtrip()

    print("\n=== Test: Stop Advisory Shortcut Patterns ===")
    r3 = test_stop_advisory_shortcut_patterns()

    print("\n" + "=" * 40)
    if r1 and r2 and r3:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
