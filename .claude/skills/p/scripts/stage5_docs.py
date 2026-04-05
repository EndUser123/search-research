#!/usr/bin/env python3
"""
Stage 5: Documentation Check

Verifies docstrings exist for functions, classes, and modules.

Usage:
    python stage5_docs.py file.py

Exit codes:
    0 - Always (non-blocking stage)
"""

import ast
import sys
from pathlib import Path


def check_docstrings(target: Path) -> tuple[int, int]:
    """
    Check for docstrings in a Python file.
    
    Returns (found_count, missing_count)
    """
    if not target.exists():
        print(f'⚠️ File not found: {target}')
        return 0, 0

    if target.suffix != '.py':
        print(f'⊘ Not a Python file, skipping docstring check')
        return 0, 0

    try:
        code = target.read_text()
        tree = ast.parse(code)
    except SyntaxError as e:
        print(f'⚠️ Cannot parse file: {e}')
        return 0, 0
    except Exception as e:
        print(f'⚠️ Error reading file: {e}')
        return 0, 0

    found = 0
    missing = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            doc = ast.get_docstring(node)
            if doc:
                print(f'✓ {name}')
                found += 1
            else:
                print(f'✗ {name}')
                missing += 1
        elif isinstance(node, ast.Module):
            doc = ast.get_docstring(node)
            if doc:
                print(f'✓ module')
                found += 1
            else:
                print(f'✗ module')
                missing += 1

    return found, missing


def main():
    if len(sys.argv) < 2:
        print("Usage: python stage5_docs.py <target>")
        sys.exit(0)

    # Handle comma-separated input
    targets = []
    for arg in sys.argv[1:]:
        targets.extend(arg.split(','))
    targets = [t.strip() for t in targets if t.strip()]

    total_found = 0
    total_missing = 0

    for target in targets:
        print(f'\n📄 Checking docstrings: {target}')
        found, missing = check_docstrings(Path(target))
        total_found += found
        total_missing += missing

    # Summary
    print(f'\n{"─" * 40}')
    if total_missing == 0:
        print(f'✅ Stage 5 PASS: {total_found} docstrings found')
    else:
        print(f'⚠️ Stage 5 WARN: {total_found} found, {total_missing} missing')

    # Always exit 0 - non-blocking stage
    sys.exit(0)


if __name__ == "__main__":
    main()
