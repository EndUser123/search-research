#!/usr/bin/env python3
"""
Script to replace all direct sqlite3.connect() calls with the centralized factory.
This is part of Phase 1.2 - Database Connection Centralization.
"""

import re
from pathlib import Path

def replace_in_file(file_path: Path) -> int:
    """Replace sqlite3.connect calls in a single file.

    Returns:
        Number of replacements made.
    """
    if not file_path.exists():
        return 0

    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # Check if factory import already exists
    has_factory_import = 'from yt_fts.db.factory import' in content or \
                         'from ...db.factory import' in content or \
                         'from ..db.factory import' in content

    replacements = 0

    # Pattern 1: Simple sqlite3.connect(get_db_path()) -> get_connection()
    # This is used with context managers
    pattern1 = r'with sqlite3\.connect\(get_db_path\(\)\) as (\w+):'
    if re.search(pattern1, content):
        content = re.sub(pattern1, r'with get_connection() as \1:', content)
        replacements += re.subn(pattern1, r'with get_connection() as \1:', original_content)[1]
        original_content = content  # Update for next pattern

    # Pattern 2: conn = sqlite3.connect(get_db_path()) -> with get_connection() as conn:
    # For standalone connections (not in context manager)
    # Find lines that assign sqlite3.connect to a variable
    pattern2 = r'(\w+)\s*=\s*sqlite3\.connect\(get_db_path\(\)\)'
    matches = list(re.finditer(pattern2, content))

    for match in reversed(matches):  # Reverse to maintain positions
        var_name = match.group(1)
        # Check if next line is NOT a context manager
        start_pos = match.end()
        # Get remaining text after this assignment
        remaining = content[start_pos:]

        # Look ahead to see if this is followed by cursor usage
        # We need to wrap with context manager
        # Find the next conn.close() or end of function/block

        # For now, replace with open_connection and manual close
        # (simpler pattern that preserves existing control flow)
        content = content[:match.start()] + f'{var_name} = open_connection()' + content[match.end():]
        replacements += 1

    # Pattern 3: sqlite3.connect(db_path) where db_path is a variable
    pattern3 = r'with sqlite3\.connect\((\w+)\) as (\w+):'
    matches3 = list(re.finditer(pattern3, content))
    for match in reversed(matches3):
        db_var = match.group(1)
        conn_var = match.group(2)
        # Replace: with sqlite3.connect(db_path) as conn: -> with get_connection(db_path) as conn:
        content = content[:match.start()] + f'with get_connection({db_var}) as {conn_var}:' + content[match.end():]
        replacements += 1

    # Pattern 4: conn = sqlite3.connect(db_path, timeout=X, isolation_level=Y)
    pattern4 = r'(\w+)\s*=\s*sqlite3\.connect\(([^)]+)\)'
    matches4 = list(re.finditer(pattern4, content))
    for match in reversed(matches4):
        var_name = match.group(1)
        args = match.group(2)
        # Check if this already uses open_connection (skip)
        if 'open_connection' in args:
            continue
        # Replace with open_connection, preserving arguments
        content = content[:match.start()] + f'{var_name} = open_connection({args})' + content[match.end():]
        replacements += 1

    # Pattern 5: sqlite3.connect(str(db_path), timeout=X) -> get_connection(db_path, timeout=X)
    pattern5 = r'with sqlite3\.connect\(str\((\w+)\),\s*timeout=(\d+\.?\d*)\) as (\w+):'
    matches5 = list(re.finditer(pattern5, content))
    for match in reversed(matches5):
        db_var = match.group(1)
        timeout = match.group(2)
        conn_var = match.group(3)
        content = content[:match.start()] + f'with get_connection({db_var}, timeout={timeout}) as {conn_var}:' + content[match.end():]
        replacements += 1

    # Pattern 6: sqlite3.connect(db_path, timeout=X, isolation_level=Y) -> open_connection(...)
    # This is for non-context-manager usage
    pattern6 = r'(\w+)\s*=\s*sqlite3\.connect\((\w+),\s*timeout=(\d+\.?\d*)(?:,\s*isolation_level="(\w+)")?\)'
    matches6 = list(re.finditer(pattern6, content))
    for match in reversed(matches6):
        var_name = match.group(1)
        db_var = match.group(2)
        timeout = match.group(3)
        iso_level = match.group(4) if match.group(4) else 'None'

        if iso_level != 'None':
            replacement = f'{var_name} = open_connection({db_var}, timeout={timeout}, isolation_level="{iso_level}")'
        else:
            replacement = f'{var_name} = open_connection({db_var}, timeout={timeout})'
        content = content[:match.start()] + replacement + content[match.end():]
        replacements += 1

    # Pattern 7: with sqlite3.connect(db_path) as conn: (simple case)
    pattern7 = r'with sqlite3\.connect\((\w+)\) as (\w+):'
    # This overlaps with pattern3, so we need to be careful
    # Let's skip if already handled by pattern3

    # Add factory import if needed and replacements were made
    if replacements > 0 and not has_factory_import:
        # Find the last import line
        lines = content.split('\n')
        import_idx = -1
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                import_idx = i

        if import_idx >= 0:
            # Determine correct import path based on file location
            rel_path = file_path.relative_to(Path(__file__).parent / 'src' / 'yt_fts')
            depth = len(rel_path.parts) - 1

            if depth == 0:  # In yt_fts/ directory
                import_line = 'from yt_fts.db.factory import get_connection, open_connection'
            elif depth == 1:  # In yt_fts/subdir/
                import_line = 'from ..db.factory import get_connection, open_connection'
            else:  # In yt_fts/subdir/subdir/
                dots = '.' * (depth + 1)
                import_line = f'from {dots}db.factory import get_connection, open_connection'

            lines.insert(import_idx + 1, import_line)
            content = '\n'.join(lines)

    # Write back if changed
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')

    return replacements


def main():
    """Main entry point."""
    src_dir = Path(__file__).parent / 'src' / 'yt_fts'

    # Find all Python files
    py_files = list(src_dir.rglob('*.py'))

    total_replacements = 0
    files_modified = []

    for py_file in py_files:
        # Skip the factory itself and test files
        if 'db/factory.py' in str(py_file) or 'test_' in py_file.name:
            continue

        replacements = replace_in_file(py_file)
        if replacements > 0:
            total_replacements += replacements
            files_modified.append((str(py_file.relative_to(src_dir)), replacements))

    # Print summary
    print(f"\n=== Database Connection Factory Migration ===\n")
    print(f"Total files modified: {len(files_modified)}")
    print(f"Total replacements: {total_replacements}\n")

    if files_modified:
        print("Files modified:")
        for file_path, count in sorted(files_modified):
            print(f"  {file_path}: {count} replacement(s)")
        print()

    print("Next steps:")
    print("  1. Review the changes with: git diff")
    print("  2. Run tests to verify: pytest tests/")
    print("  3. Commit if all tests pass")


if __name__ == '__main__':
    main()
