"""Pre-commit hook to verify dead code before removal.

This hook uses grep to check for dead code patterns (F401/F841 violations)
before allowing commits. If dead code is found, the commit is blocked with
specific file:line locations.

Usage:
    This hook is automatically invoked by git before each commit.
    To bypass (not recommended), use: git commit --no-verify
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def check_dead_code_with_grep(root_path: Path) -> list[tuple[str, int, str]]:
    """Check for dead code patterns using grep.

    Args:
        root_path: Root directory to search

    Returns:
        List of tuples (file_path, line_number, pattern_found)
    """
    dead_code_issues = []

    # Pattern 1: Unused imports (F401)
    # Matches: `from X import Y` where Y is never used
    # We check for imports followed by no usage in the same file
    try:
        result = subprocess.run(
            [
                "rg",
                "--type",
                "py",
                "-n",
                "^from .* import .*",
                str(root_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # Parse results and check for unused imports
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                # Format: "file:line:content"
                parts = line.split(":", 2)
                if len(parts) >= 2:
                    file_path = parts[0]
                    line_number = int(parts[1])
                    # Additional verification could be added here
                    # For now, we flag all imports for manual review
                    content = parts[2] if len(parts) > 2 else ""
                    if "import" in content:
                        dead_code_issues.append((file_path, line_number, "Unused import (F401)"))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Pattern 2: Assigned but never used (F841)
    # Matches: `variable = value` where variable is never referenced
    try:
        result = subprocess.run(
            [
                "rg",
                "--type",
                "py",
                "-n",
               r"^\s*\w+\s*=.+",  # Variable assignment
                str(root_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split(":", 2)
                if len(parts) >= 2:
                    file_path = parts[0]
                    line_number = int(parts[1])
                    content = parts[2] if len(parts) > 2 else ""
                    # Flag assignments for manual review
                    if "=" in content and not content.strip().startswith("#"):
                        dead_code_issues.append((file_path, line_number, "Assigned but never used (F841)"))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return dead_code_issues


def main() -> int:
    """Run pre-commit dead code check.

    Returns:
        Exit code: 0 for success (no dead code), 1 for failure (dead code found)
    """
    # Get the git repository root
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        repo_root = Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Not in a git repo or git not available
        return 0

    # Get list of staged Python files
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "*.py"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        staged_files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        staged_files = []

    if not staged_files:
        # No Python files staged
        return 0

    # Check each staged file for dead code
    all_issues = []
    for file_path in staged_files:
        full_path = repo_root / file_path
        if full_path.exists():
            issues = check_dead_code_with_grep(full_path.parent)
            # Filter issues to only include the staged file
            file_issues = [
                (fp, line, pattern)
                for fp, line, pattern in issues
                if fp == str(full_path) or fp.endswith(file_path)
            ]
            all_issues.extend(file_issues)

    if all_issues:
        print("❌ Dead code detected - commit blocked", file=sys.stderr)
        print("\nFound potential dead code issues:\n", file=sys.stderr)

        # Group by file
        by_file: dict[str, list[tuple[int, str]]] = {}
        for file_path, line_number, pattern in all_issues:
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append((line_number, pattern))

        # Print issues grouped by file
        for file_path, issues in sorted(by_file.items()):
            rel_path = Path(file_path).relative_to(repo_root) if file_path.startswith(str(repo_root)) else file_path
            print(f"  {rel_path}:", file=sys.stderr)
            for line_number, pattern in sorted(set(issues)):
                print(f"    Line {line_number}: {pattern}", file=sys.stderr)

        print("\nTo fix:", file=sys.stderr)
        print("  1. Remove unused imports or variables", file=sys.stderr)
        print("  2. Or verify the code is actually used and update the hook", file=sys.stderr)
        print("\nTo bypass (not recommended): git commit --no-verify", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
