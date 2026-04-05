#!/usr/bin/env python3
"""Test path extraction and matching for mkdir commands."""

import fnmatch
import re

_PATTERN_MKDIR_WIN = re.compile(
    r'mkdir\s+(?:-p\s+)?["\']?([A-Za-z]:[\\/][^\s"\';&|]+)', re.IGNORECASE
)

command = 'mkdir -p "C:/Users/brsth/.claude/plans" && mkdir -p "C:/Users/brsth/.claude/state/planning/terminals"'

matches = _PATTERN_MKDIR_WIN.findall(command)
print("Matches:", matches)

# Test is_allowed_external_path logic
patterns = [
    "*/.claude/plans",
    "*/.claude/plans/*",
    "c:/users/*/.claude/plans",
    "c:/users/*/.claude/plans/*",
    "c:/users/*/.claude/state/*",
]

for path in matches:
    normalized = path.replace("\\", "/").lower()
    print(f"Path: {path}")
    print(f"Normalized: {normalized}")
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern.lower()):
            print(f"  MATCHES pattern: {pattern}")
            break
    else:
        print("  NO MATCH")
