#!/usr/bin/env python3
"""
Fix G004 logging f-string issues.

Transforms: logger.info(f"x: {y}") → logger.info("x: %s", y)
"""
import ast
import re
from pathlib import Path


def fix_logging_fstring(content: str) -> tuple[str, int]:
    """Fix logging f-strings in Python code.

    Returns (fixed_content, fixes_made)
    """
    fixes = 0

    # Pattern to match logging calls with f-strings
    # logger.info(f"..."), logger.debug(f"..."), etc.
    # Need to handle:
    # - logger.METHOD(f"...")
    # - Extract format string and variables
    # - Convert to %s, %d, %r format

    def replace_fstring(match):
        nonlocal fixes
        full_match = match.group(0)
        method = match.group(1)

        # Extract the f-string content
        fstring_content = match.group(2)

        # Parse the f-string to find placeholders
        # Format: {...} with optional format specs
        placeholders = re.findall(r'\{([^}:}]*?)(?::[^}]+)?\}', fstring_content)

        if not placeholders:
            return full_match  # No placeholders, weird but keep as-is

        # Build new format string and args
        format_parts = []
        args = []

        # Split by placeholders and rebuild
        last_end = 0
        for ph in placeholders:
            var_name = ph[0]  # The variable/expression inside {}
            placeholder_start = fstring_content.find('{' + ph[0])
            if placeholder_start > last_end:
                format_parts.append(fstring_content[last_end:placeholder_start])

            # Determine format specifier
            fmt_spec = ph[1] if len(ph) > 1 else ''
            if fmt_spec == 'r':
                format_parts.append('%r')
            elif fmt_spec == 'd':
                format_parts.append('%d')
            elif fmt_spec and 'f' in fmt_spec:
                format_parts.append('%f')
            else:
                format_parts.append('%s')

            args.append(var_name)
            last_end = fstring_content.find('}' + (ph[1] if len(ph) > 1 else '}')) + 1

        if last_end < len(fstring_content):
            format_parts.append(fstring_content[last_end:])

        format_str = ''.join(format_parts)
        format_str = format_str.replace('%', '%%')  # Escape % for Python

        # Build the replacement
        if len(args) == 1:
            new_call = f'logger.{method}("{format_str}", {args[0]})'
        else:
            new_call = f'logger.{method}("{format_str}", {", ".join(args)})'

        fixes += 1
        return new_call

    # Pattern: logger.METHOD(f"...")
    pattern = r'logger\.(info|debug|warning|error|exception|critical)\(f"([^"]*(?:\{[^}]*\}[^"]*)*)"\)'

    # Replace in code
    fixed_content = re.sub(pattern, replace_fstring, content)

    return fixed_content, fixes


def fix_file(file_path: Path) -> int:
    """Fix a single file, return number of fixes made."""
    try:
        content = file_path.read_text(encoding='utf-8')
        fixed, count = fix_logging_fstring(content)

        if count > 0:
            file_path.write_text(fixed, encoding='utf-8')
            print(f'  Fixed {count} issues in {file_path.relative_to(file_path.parents[-2])}')
        return count
    except Exception as e:
        print(f'  Error processing {file_path}: {e}')
        return 0


def main():
    import sys

    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
        if target.is_file():
            print(f'Fixing {target}...')
            fix_file(target)
        elif target.is_dir():
            py_files = list(target.rglob('*.py'))
            print(f'Scanning {len(py_files)} files...')
            total = 0
            for py_file in py_files:
                total += fix_file(py_file)
            print(f'\nTotal fixes: {total}')
    else:
        print('Usage: fix_g004.py <file_or_directory>')
        print('Example: python fix_g004.py src/yt_fts/services/')


if __name__ == '__main__':
    main()
