#!/usr/bin/env python3
"""
Automated sys.path removal script for Python 2025 Standards Compliance.

This script removes sys.path.insert/append statements that add project paths,
since proper packaging with pyproject.toml makes these unnecessary.
"""

import ast
import os
import re
import sys


def find_python_files_with_sys_path(root_dir: str) -> list[str]:
    """Find all Python files containing sys.path.insert or sys.path.append."""
    python_files = []
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                "__pycache__",
                ".git",
                ".venv",
                "node_modules",
                ".mypy_cache",
                ".pytest_cache",
                ".claude",
                "logs",
                "temp",
                "temp_test_chs",
            }
        ]

        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        if re.search(r"sys\.path\.(insert|append)", content):
                            python_files.append(filepath)
                except Exception as e:
                    print(f"Warning: Could not read {filepath}: {e}")
                    continue

    return python_files


def analyze_sys_path_lines(content: str) -> list[tuple[int, str]]:
    """Analyze content and return line numbers and content of sys.path lines to remove."""
    lines = content.split("\n")
    lines_to_remove = []

    # Patterns that add project paths to sys.path
    project_path_patterns = [
        # Direct path additions
        r'sys\.path\.(insert|append)\s*\(\s*[\'"]([^\'"]*__csf\.nip[^\'"]*|src[^\'"]*|P:/[^\'"]*)[\'"]',
        # Path construction with Path
        r"sys\.path\.(insert|append)\s*\(\s*0?\s*,\s*str\s*\(\s*Path\s*\(",
        # Variable-based additions
        r"sys\.path\.(insert|append)\s*\(\s*0?\s*,\s*str\s*\(\s*[a-zA-Z_][a-zA-Z0-9_]*",
    ]

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()

        # Skip if line doesn't contain sys.path
        if "sys.path." not in line_stripped:
            continue

        # Check if it's a project path addition
        is_project_path = False

        for pattern in project_path_patterns:
            if re.search(pattern, line_stripped):
                is_project_path = True
                break

        # Additional heuristics for project paths
        if not is_project_path:
            # Check for common project path indicators
            indicators = [
                "csf_root",
                "project_root",
                "__csf",
                "/src",
                "src/",
                ".parent.parent",
            ]
            if any(indicator in line_stripped for indicator in indicators):
                # Look for path construction patterns
                if "str(" in line_stripped and (
                    "Path(" in line_stripped or "/" in line_stripped
                ):
                    is_project_path = True

        if is_project_path:
            lines_to_remove.append((i, line))

    return lines_to_remove


def remove_sys_path_lines(content: str, lines_to_remove: list[tuple[int, str]]) -> str:
    """Remove the specified lines from content."""
    lines = content.split("\n")
    # Sort by line number in reverse order to maintain indices
    lines_to_remove.sort(key=lambda x: x[0], reverse=True)

    for line_num, _ in lines_to_remove:
        # Convert to 0-based index
        idx = line_num - 1
        if 0 <= idx < len(lines):
            # Remove the line
            lines.pop(idx)

    return "\n".join(lines)


def validate_python_syntax(content: str) -> bool:
    """Validate that the content is valid Python syntax."""
    try:
        ast.parse(content)
        return True
    except SyntaxError:
        return False


def process_file(filepath: str, dry_run: bool = True) -> tuple[bool, int, str]:
    """Process a single file to remove sys.path lines."""
    try:
        with open(filepath, encoding="utf-8") as f:
            original_content = f.read()
    except Exception as e:
        return False, 0, f"Could not read file: {e}"

    # Analyze which lines to remove
    lines_to_remove = analyze_sys_path_lines(original_content)

    if not lines_to_remove:
        return True, 0, "No sys.path lines to remove"

    # Remove the lines
    modified_content = remove_sys_path_lines(original_content, lines_to_remove)

    # Validate syntax
    if not validate_python_syntax(modified_content):
        return False, 0, "Modified content has invalid Python syntax"

    # Write back if not dry run
    if not dry_run:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(modified_content)
        except Exception as e:
            return False, 0, f"Could not write file: {e}"

    return True, len(lines_to_remove), f"Removed {len(lines_to_remove)} sys.path lines"


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Remove sys.path manipulations for Python 2025 compliance"
    )
    parser.add_argument("--root", default="__csf", help="Root directory to scan")
    parser.add_argument(
        "--dry-run", action="store_true", default=True, help="Dry run mode (default)"
    )
    parser.add_argument("--execute", action="store_true", help="Actually modify files")
    parser.add_argument(
        "--max-files", type=int, default=100, help="Maximum files to process"
    )

    args = parser.parse_args()

    if args.execute:
        args.dry_run = False

    root_dir = args.root

    if not os.path.exists(root_dir):
        print(f"Error: Directory {root_dir} does not exist")
        return 1

    print(f"Scanning for Python files with sys.path manipulations in {root_dir}...")
    python_files = find_python_files_with_sys_path(root_dir)

    print(f"Found {len(python_files)} Python files with sys.path manipulations")

    if len(python_files) > args.max_files:
        print(f"Limiting to first {args.max_files} files")
        python_files = python_files[: args.max_files]

    total_processed = 0
    total_modified = 0
    total_lines_removed = 0
    failed_files = []

    for filepath in python_files:
        rel_path = os.path.relpath(filepath)
        success, lines_removed, message = process_file(filepath, args.dry_run)

        total_processed += 1

        if success and lines_removed > 0:
            total_modified += 1
            total_lines_removed += lines_removed
            status = "MODIFIED"
        elif success and lines_removed == 0:
            status = "SKIPPED"
        else:
            status = "FAILED"
            failed_files.append((filepath, message))

        print(f"{total_processed:2d}")

        if not success:
            print(f"  Error: {message}")

    print("\nSummary:")
    print(f"  Total files processed: {total_processed}")
    print(f"  Files modified: {total_modified}")
    print(f"  Total lines removed: {total_lines_removed}")
    print(f"  Failed files: {len(failed_files)}")

    if failed_files:
        print("\nFailed files:")
        for filepath, error in failed_files:
            print(f"  {filepath}: {error}")

    if args.dry_run:
        print("\nThis was a DRY RUN. Use --execute to actually modify files.")
    else:
        print("\nFiles have been modified.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
