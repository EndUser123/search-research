#!/usr/bin/env python3
"""Scan all hooks for stderr writes.

Usage:
    python hook_scan.py
    python hook_scan.py --help

Exit codes:
    0: No stderr writes found
    1: Stderr writes detected
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    """Scan all hooks for stderr writes."""
    hooks_dir = Path("P:/.claude/hooks")
    pattern = r'print\(.*file=sys\.stderr\)'

    violations = []

    # Scan all hook files
    for hook_file in hooks_dir.glob("*ToolUse*.py"):
        try:
            content = hook_file.read_text(encoding="utf-8")
            lines = content.splitlines()

            for i, line in enumerate(lines, start=1):
                # Skip commented lines
                if line.strip().startswith('#'):
                    continue
                if re.search(pattern, line):
                    violations.append((hook_file.name, i, line.strip()))
        except Exception:
            # Fail gracefully - report errors but continue scanning
            print(f"Warning: Could not read {hook_file}", file=sys.stdout)

    # Report results
    if violations:
        print("⛔ STDERR WRITES FOUND:")
        for filename, line_no, line_text in violations:
            print(f"  {filename}:{line_no}: {line_text}")
        print(f"\nTotal: {len(violations)} violation(s)")
        print("\nFix: Replace with logging module using NullHandler")
        print("See: P:/.claude/hooks/docs/development_guide.md")
        return 1
    else:
        print("✅ No stderr writes found in hooks")
        return 0


if __name__ == "__main__":
    sys.exit(main())
