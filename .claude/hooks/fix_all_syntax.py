#!/usr/bin/env python3
"""Comprehensive syntax fix for all broken test files."""
import re
from pathlib import Path

hooks_dir = Path("P:/.claude/hooks")

# Files that need specific fixes
remaining = [
    "test_router_concern.py",
    "test_subprocess.py",
    "test_userpromptsubmit_entrypoint.py",
    "tdd_core.py",
]

for filename in remaining:
    filepath = hooks_dir / filename
    if not filepath.exists():
        continue

    content = filepath.read_text()
    original = content

    # Fix missing closing ) for subprocess.run
    # Pattern: subprocess.run(\n        [...args],\n        capture_output=True,\n        timeout=5,\n    \n    print
    content = re.sub(
        r'subprocess\.run\(\s*\n\s*\[([^\]]+)\],\s*\n\s*capture_output=True,\s*\n\s*timeout=\d+,?\s*\n\s*\)\s*\n\s*print',
        r'subprocess.run(\n        [\1],\n        capture_output=True,\n        timeout=5,\n    )\n    print',
        content,
        flags=re.MULTILINE
    )

    # Fix missing ) after json.dumps call
    content = re.sub(
        r'input=json\.dumps\(([^)]+),\s*\n\s*capture_output',
        r'input=json.dumps(\1),\n        capture_output',
        content
    )

    # Fix unmatched ) - remove stray ) at line start
    content = re.sub(r'^\s*\)\s*$', '', content, flags=re.MULTILINE)

    # Fix cwd=Path.cwd(, -> cwd=Path.cwd()),
    content = re.sub(r'cwd=Path\.cwd\(\,', r'cwd=Path.cwd(),', content)

    if content != original:
        filepath.write_text(content)
        print(f"Fixed: {filename}")

print("Done fixing remaining files")
