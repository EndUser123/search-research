#!/usr/bin/env python3
"""Test that hooks return 'diagnostic' field, not 'error' field."""

import re
from pathlib import Path


def check_file_for_error_field(file_path: Path) -> bool:
    """Check if file contains 'error' field in exception handlers (excluding 'diagnostic')."""
    content = file_path.read_text(encoding="utf-8")

    # Look for patterns like: return {"ok": False, "error": ...}
    # But exclude patterns with "diagnostic"
    error_pattern = re.compile(r'return\s*{[^}]*"error"\s*:', re.MULTILINE)

    # Check if there are any "error" fields
    error_matches = error_pattern.findall(content)

    # Now verify these are NOT followed by "diagnostic" in the same file
    # (i.e., make sure we haven't just renamed them to "diagnostic")
    for match in error_matches:
        # If there's an "error" field, it's a problem
        return True

    return False


def check_file_for_diagnostic_field(file_path: Path) -> bool:
    """Check if file contains 'diagnostic' field in exception handlers."""
    content = file_path.read_text(encoding="utf-8")

    # Look for patterns like: return {"ok": False, "diagnostic": ...}
    diagnostic_pattern = re.compile(r'return\s*{[^}]*"diagnostic"\s*:', re.MULTILINE)
    return bool(diagnostic_pattern.search(content))


def main():
    """Run all checks."""
    print("Checking hook files for error field fixes...")
    print()

    files_to_check = [
        "UserPromptSubmit.py",
        "Stop.py",
        "PreToolUse.py",
        "posttooluse/base.py"
    ]

    all_passed = True

    for file_name in files_to_check:
        file_path = Path(file_name)

        if not file_path.exists():
            print(f"⚠️  {file_name}: NOT FOUND")
            all_passed = False
            continue

        has_error = check_file_for_error_field(file_path)
        has_diagnostic = check_file_for_diagnostic_field(file_path)

        if has_error:
            print(f"❌ {file_name}: FAILED (still has 'error' field)")
            all_passed = False
        elif has_diagnostic:
            print(f"✅ {file_name}: PASSED (uses 'diagnostic' field)")
        else:
            print(f"⚠️  {file_name}: WARNING (neither 'error' nor 'diagnostic' found)")

    print()
    print("=" * 60)

    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("=" * 60)
        print()
        print("All hooks now return 'diagnostic' field instead of 'error' field.")
        print("This prevents false positive hook errors in Claude Code UI.")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("=" * 60)
        print()
        print("Some hooks still return 'error' field which will cause")
        print("false positive hook errors in Claude Code UI.")
        return 1


if __name__ == "__main__":
    exit(main())
