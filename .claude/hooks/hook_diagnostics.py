#!/usr/bin/env python3
"""
Hook Diagnostics Tool

Quick validation checks for Claude Code hooks.
Run: python .claude/hooks/hook_diagnostics.py
"""

import subprocess
import sys
from pathlib import Path


def check_hook_stderr_violations() -> bool:
    """Check hooks don't write to stderr (Claude Code treats stderr as error)."""
    hooks_dir = Path(__file__).resolve().parent / "posttooluse"

    print("Checking for stderr violations in hooks...")

    result = subprocess.run(
        ["grep", "-rn", "file=sys.stderr", str(hooks_dir)],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        violations = []
        for line in result.stdout.strip().split('\n'):
            # Skip archived/unused hooks
            if 'verification_tracker.py' in line:
                continue
            # Skip __pycache__ directories
            if '__pycache__' in line:
                continue
            violations.append(line)

        if violations:
            print("\n❌ STDERR VIOLATIONS FOUND:")
            for v in violations:
                print(f"  {v}")
            print("\nHook policy: Hooks MUST NOT write to stderr.")
            print("Claude Code treats stderr as error.")
            print("\nFix: Replace with logger.error() or silent pass")
            return False
        else:
            print("✅ No stderr violations in active hooks")
            return True
    else:
        print("✅ No stderr violations found")
        return True

def main():
    """Run all diagnostic checks."""
    checks_passed = True

    print("=" * 60)
    print("Hook Diagnostics")
    print("=" * 60)

    checks_passed &= check_hook_stderr_violations()

    print("=" * 60)
    if checks_passed:
        print("✅ All checks passed")
        sys.exit(0)
    else:
        print("❌ Some checks failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
