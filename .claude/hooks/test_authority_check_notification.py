#!/usr/bin/env python3
from __future__ import annotations

"""
Notification Integration Tests for authority-check.py

Tests that planning mode adds notifications and authorization clears them.
"""

import json
import subprocess
import sys
from pathlib import Path

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"


def print_test_result(name: str, passed: bool, details: str | None = None) -> None:
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  [{status}] {name}")
    if details:
        print(f"       {details}")


def check_notification_exists(notification_type: str = "planning_mode") -> bool:
    """Check if a notification of the given type exists."""
    try:
        notif_file = Path.home() / ".claude" / "notifications.json"
        if not notif_file.exists():
            return False
        notifications = json.loads(notif_file.read_text())
        return any(n.get("type") == notification_type for n in notifications)
    except Exception:
        return False


def clear_test_notifications() -> None:
    """Clear test notifications before running tests."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from notification_queue import clear_by_type
        clear_by_type("planning_mode", source="authority_check")
    except Exception:
        pass


def run_notification_test(name: str, prompt_input: str, should_have_notification: bool = False) -> bool:
    """Test that planning mode notifications are added/cleared correctly."""
    hook_path = Path(__file__).resolve().parent / "authority-check.py"
    try:
        # Clear any existing notifications first
        clear_test_notifications()

        # Run the hook
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps({"prompt": prompt_input}),
            capture_output=True,
            text=True,
            timeout=5
        )

        # Check if notification was added
        has_notification = check_notification_exists("planning_mode")
        passed = has_notification == should_have_notification

        if not passed:
            details = f"Expected notification: {should_have_notification}, Got: {has_notification}"
            print_test_result(name, passed, details)
        else:
            print_test_result(name, passed)

        # Cleanup
        clear_test_notifications()
        return passed
    except Exception as e:
        print_test_result(name, False, f"ERROR: {e}")
        clear_test_notifications()
        return False


def main() -> int:
    print("=" * 60)
    print("Authority Check Notification Integration Tests")
    print("=" * 60)

    results = []

    print(f"\n{YELLOW}SECTION: Notification Integration{RESET}")

    # Test 1: Planning question adds notification
    results.append(run_notification_test(
        "Test 1: Planning question adds notification",
        "How should I design this component?",
        should_have_notification=True
    ))

    # Test 2: Authorization clears notification (no notification after impl)
    results.append(run_notification_test(
        "Test 2: 'implement' clears planning notification",
        "implement the feature",
        should_have_notification=False
    ))

    # Test 3: Statement (not a question) doesn't add notification
    results.append(run_notification_test(
        "Test 3: Non-question statement doesn't add notification",
        "Create a new file",
        should_have_notification=False
    ))

    # Test 4: What question adds notification
    results.append(run_notification_test(
        "Test 4: 'What' question adds notification",
        "What approach works best?",
        should_have_notification=True
    ))

    # Test 5: Code explanation doesn't add notification
    results.append(run_notification_test(
        "Test 5: Code explanation doesn't add notification",
        "Explain how this regex works",
        should_have_notification=False
    ))

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    pct = (passed / total) * 100
    if passed == total:
        print(f"{GREEN}ALL {total}/{total} TESTS PASSED ({pct:.0f}%){RESET}")
    else:
        print(f"{RED}TESTS FAILED: {passed}/{total} passed ({pct:.0f}%){RESET}")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
