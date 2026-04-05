#!/usr/bin/env python3
"""
Convert UserPromptSubmit_modules from relative to absolute imports.

This script refactors all relative imports (from .base, from .registry)
to absolute imports (from UserPromptSubmit_modules.base, etc.) to enable
dynamic module loading via importlib.util.
"""

from __future__ import annotations

import re
from pathlib import Path


def convert_relative_imports(file_path: Path) -> tuple[bool, int]:
    """Convert relative imports to absolute imports in a Python file.

    Returns:
        (success, number_of_imports_converted)
    """

    content = file_path.read_text()
    original_content = content

    # Pattern 1: from .base import X
    pattern1 = re.compile(r'from \.base import')
    content = pattern1.sub('from UserPromptSubmit_modules.base import', content)

    # Pattern 2: from .registry import X
    pattern2 = re.compile(r'from \.registry import')
    content = pattern2.sub('from UserPromptSubmit_modules.registry import', content)

    # Count changes
    changes = content.count('from UserPromptSubmit_modules.')
    changes_original = original_content.count('from UserPromptSubmit_modules.')

    # Only write if changes were made
    if content != original_content:
        file_path.write_text(content)
        return True, changes

    return False, 0


def main():
    """Convert all relative imports in UserPromptSubmit_modules package."""

    modules_dir = Path(__file__).resolve().parent

    print(f"\n{'='*60}")
    print("Converting UserPromptSubmit_modules to Absolute Imports")
    print(f"{'='*60}\n")

    # Find all Python files in the package
    py_files = [
        f for f in modules_dir.glob("*.py")
        if f.name != "__init__.py" and not f.name.startswith("convert_")
    ]

    print(f"Found {len(py_files)} Python files to process\n")

    total_converted = 0
    converted_files = []

    for file_path in sorted(py_files):
        success, count = convert_relative_imports(file_path)

        if success:
            total_converted += count
            converted_files.append(file_path.name)
            print(f"✅ {file_path.name}: {count} import(s) converted")
        else:
            print(f"⏭️  {file_path.name}: No relative imports found")

    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    print(f"Files converted: {len(converted_files)}")
    print(f"Total imports converted: {total_converted}")

    if converted_files:
        print("\nConverted files:")
        for filename in converted_files:
            print(f"  • {filename}")

    print("\n✅ Refactoring complete!")
    print("\nNext steps:")
    print("1. Test UserPromptSubmit with HookImporter")
    print("2. Run in-process hook execution tests")
    print("3. Update settings.json to use in-process for UserPromptSubmit")


if __name__ == "__main__":
    main()
