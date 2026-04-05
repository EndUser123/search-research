#!/usr/bin/env python3
"""Minimal test - direct function calls"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("P:/.claude/hooks")))

from test_assumption_audit import is_safe_response

test_cases = [
    ("Found them! 13 tasks already have [yt-fts] in their title.", False, "Enumeration claim"),
    ("The daemon handles this by polling every 5 seconds.", False, "Code behavior claim"),
    ("A mutex is a synchronization primitive.", True, "General knowledge"),
    ("Okay, I'll check that now.", True, "Acknowledgment"),
]

print("Testing is_safe_response()")
print("=" * 60)

for text, expected_safe, description in test_cases:
    result = is_safe_response(text)
    status = "✓" if result == expected_safe else "✗"

    print(f"{status} {description}")
    print(f"  Text: {text}")
    print(f"  Length: {len(text)} chars")
    print(f"  Expected: {'SAFE' if expected_safe else 'VERIFY'}")
    print(f"  Got: {'SAFE' if result else 'VERIFY'}")

    if result != expected_safe:
        print("  ❌ MISMATCH")
    print()
