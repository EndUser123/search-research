#!/usr/bin/env python3
"""
Hook Health Check Audit Script
===============================

Audits the hook configuration to ensure all hooks are properly wrapped
with hook_runner.py for error logging.

Usage:
    python P:/.claude/hooks/scripts/audit_hook_wrappers.py

Exit codes:
    0 - All hooks properly wrapped
    1 - Some hooks missing wrapper (needs attention)
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

SETTINGS_PATH = Path("P:/.claude/settings.json")
HOOK_RUNNER_PATTERN = re.compile(r"hook_runner\.py")

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def audit_hooks() -> tuple[list, list, list]:
    """
    Audit all hooks in settings.json.

    Returns:
        (wrapped, unwrapped, skipped) - Lists of hook info tuples
    """
    with open(SETTINGS_PATH, encoding="utf-8") as f:
        settings = json.load(f)

    hooks = settings.get("hooks", {})

    wrapped = []
    unwrapped = []
    skipped = []  # Non-python commands

    for event_type, matchers in hooks.items():
        if not isinstance(matchers, list):
            continue

        for matcher_group in matchers:
            matcher = matcher_group.get("matcher", ".*")
            hook_list = matcher_group.get("hooks", [])

            for hook in hook_list:
                if hook.get("type") != "command":
                    continue

                cmd = hook.get("command", "")
                timeout = hook.get("timeout", "N/A")

                # Skip non-python commands
                if not cmd.startswith("python "):
                    skipped.append((event_type, matcher, cmd, timeout))
                    continue

                info = (event_type, matcher, cmd, timeout)

                if HOOK_RUNNER_PATTERN.search(cmd):
                    wrapped.append(info)
                else:
                    unwrapped.append(info)

    return wrapped, unwrapped, skipped


def print_report(wrapped: list, unwrapped: list, skipped: list) -> None:
    """Print a formatted audit report."""
    print("=" * 80)
    print("HOOK WRAPPER AUDIT REPORT")
    print(f"Generated: {datetime.now(UTC).isoformat()}")
    print("=" * 80)
    print()

    # Summary
    total = len(wrapped) + len(unwrapped)
    pct = (len(wrapped) / total * 100) if total > 0 else 0

    if len(unwrapped) == 0:
        status_color = GREEN
        status = "✓ ALL HOOKS WRAPPED"
    else:
        status_color = RED
        status = "✗ MISSING WRAPPERS"

    print(f"Status: {status_color}{status}{RESET}")
    print(f"Wrapped:   {len(wrapped):3d} / {total} ({pct:.1f}%)")
    print(f"Unwrapped: {len(unwrapped):3d}")
    print(f"Skipped:   {len(skipped):3d} (non-Python)")
    print()

    # List unwrapped hooks
    if unwrapped:
        print(f"{RED}UNWRAPPED HOOKS (errors will NOT be logged):{RESET}")
        print("-" * 70)
        for event_type, matcher, cmd, timeout in unwrapped:
            print(f"  [{event_type}] {matcher}")
            print(f"    {YELLOW}{cmd}{RESET}")
            print()

    # List skipped (informational)
    if skipped:
        print(f"{YELLOW}SKIPPED (non-Python commands):{RESET}")
        for event_type, matcher, cmd, timeout in skipped:
            print(f"  [{event_type}] {cmd[:50]}...")
        print()

    print("=" * 80)


def main() -> int:
    """Run the audit and return exit code."""
    if not SETTINGS_PATH.exists():
        print(f"{RED}ERROR: settings.json not found at {SETTINGS_PATH}{RESET}")
        return 1

    wrapped, unwrapped, skipped = audit_hooks()
    print_report(wrapped, unwrapped, skipped)

    if unwrapped:
        print(
            f"\n{YELLOW}To fix: Run 'python P:/.claude/hooks/scripts/wrap_all_hooks.py'{RESET}"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
