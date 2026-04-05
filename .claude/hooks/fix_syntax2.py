#!/usr/bin/env python3
"""Fix syntax errors in test files - missing closing parentheses after function calls."""
import re
from pathlib import Path

hooks_dir = Path("P:/.claude/hooks")

# Find all test files and tdd_core.py with syntax errors
broken_files = []
for f in hooks_dir.glob("test_*.py"):
    try:
        compile(f.read_text(), str(f), 'exec')
    except SyntaxError:
        broken_files.append(f)

# Also check tdd_core.py
tdd_core = hooks_dir / "tdd_core.py"
if tdd_core.exists():
    try:
        compile(tdd_core.read_text(), str(tdd_core), 'exec')
    except SyntaxError:
        broken_files.append(tdd_core)

# Also check baseline_hooks.py and test-damage-control.py
for name in ["baseline_hooks.py", "test-damage-control.py"]:
    f = hooks_dir / name
    if f.exists():
        try:
            compile(f.read_text(), str(f), 'exec')
        except SyntaxError:
            broken_files.append(f)

print(f"Found {len(broken_files)} files with syntax errors")

fixed = 0
for filepath in broken_files:
    content = filepath.read_text()
    original = content

    # Pattern: str(THING)] -> str(THING))]
    # This catches cases where a function call is missing a closing paren before ]
    content = re.sub(r'str\(([^)]+)\]', r'str(\1)]', content)

    # Pattern: Path.cwd(, -> Path.cwd(),
    content = re.sub(r'Path\.cwd\(\,', r'Path.cwd(),', content)

    # Pattern: ["python", str(HOOK], -> ["python", str(HOOK)],
    content = re.sub(r'\["python", str\(HOOK\],', r'["python", str(HOOK)],', content)

    # Pattern: [sys.executable, str(hook_path], -> [sys.executable, str(hook_path)],
    content = re.sub(r'\[sys\.executable, str\(hook_path\],', r'[sys.executable, str(hook_path)],', content)

    # Pattern: str(arg1), arg2] -> str(arg1)), arg2]
    content = re.sub(r'str\(([^)]+)\), ([^]]+)\]', r'str(\1)), \2]', content)

    if content != original:
        filepath.write_text(content)
        fixed += 1
        print(f"Fixed: {filepath.name}")
    else:
        print(f"Skipped (no changes): {filepath.name}")

print(f"\nFixed: {fixed}/{len(broken_files)}")
