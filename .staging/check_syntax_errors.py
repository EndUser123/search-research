#!/usr/bin/env python3
"""Check for syntax errors in all modified .py files."""

import ast
import subprocess
import sys
from pathlib import Path

# Get modified .py files from git
result = subprocess.run(
    ["git", "status", "--porcelain"], capture_output=True, text=True, cwd="P:/"
)

changed_files = []
for line in result.stdout.strip().split("\n"):
    if not line:
        continue
    parts = line.split()
    if len(parts) >= 2:
        filename = " ".join(parts[1:])
        if filename.endswith(".py"):
            changed_files.append(filename)

# Check each file for syntax errors
errors = []
for file_path in changed_files:
    full_path = Path("P:/") / file_path
    if not full_path.exists():
        continue

    try:
        with open(full_path, encoding="utf-8") as f:
            content = f.read()
        ast.parse(content)
        print(f"✓ {file_path}: OK")
    except SyntaxError as e:
        error_msg = f"{file_path}:{e.lineno} - {e.msg}"
        print(f"✗ {error_msg}")
        if e.text:
            print(f"  → {e.text.strip()}")
        errors.append(error_msg)

if errors:
    print(f"\n{len(errors)} syntax error(s) found", file=sys.stderr)
    sys.exit(1)
else:
    print(f"\nAll {len(changed_files)} files are valid")
    sys.exit(0)
