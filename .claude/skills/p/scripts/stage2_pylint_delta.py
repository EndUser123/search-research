#!/usr/bin/env python3
"""
Stage 2 pylint delta filter.

Runs pylint on target, then filters output to only show violations on lines
that have been modified according to git diff. Pre-existing violations on
unchanged lines are suppressed to reduce noise.

If git is unavailable or the file is untracked, all violations are shown.

Usage:
    python stage2_pylint_delta.py <target> [--all]

    --all    Show all violations (disable delta filtering)

Exit codes:
    0  - Score >= 7.0 (or no new violations)
    1  - Score < 7.0 on changed lines
    2  - Pylint not available
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def get_changed_lines(target: Path) -> dict[str, set[int]] | None:
    """Get changed line numbers per file from git diff.

    Returns {filepath: {line_numbers}} or None if git unavailable/untracked.
    """
    try:
        # Prevent blue console flash on Windows
        creation_flags = 0x08000000 if sys.platform == 'win32' else 0
        # Get unified diff for the target
        result = subprocess.run(
            ["git", "diff", "--unified=0", "HEAD", "--", str(target)],
            capture_output=True, text=True, timeout=10,
            creationflags=creation_flags
        )
        if result.returncode != 0:
            # Try against staging area too
            result = subprocess.run(
                ["git", "diff", "--unified=0", "--", str(target)],
                capture_output=True, text=True, timeout=10,
                creationflags=creation_flags
            )
        if not result.stdout.strip():
            # No diff — file is unchanged or untracked
            # Check if untracked
            status = subprocess.run(
                ["git", "status", "--porcelain", "--", str(target)],
                capture_output=True, text=True, timeout=10,
                creationflags=creation_flags
            )
            if status.stdout.strip().startswith("??"):
                return None  # Untracked — show all
            return {}  # Tracked but unchanged — no changed lines

        changed: dict[str, set[int]] = {}
        current_file = str(target.resolve())
        for line in result.stdout.splitlines():
            # Parse @@ -old,count +new,count @@ hunk headers
            match = re.match(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', line)
            if match:
                start = int(match.group(1))
                count = int(match.group(2)) if match.group(2) else 1
                lines = set(range(start, start + count))
                changed.setdefault(current_file, set()).update(lines)

        return changed
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None  # Git not available


def run_pylint(target: Path) -> tuple[str, float]:
    """Run pylint and return (output, score)."""
    try:
        # Prevent blue console flash on Windows
        creation_flags = 0x08000000 if sys.platform == 'win32' else 0
        result = subprocess.run(
            [sys.executable, "-m", "pylint",
             str(target),
             "--output-format=text",
             "--max-line-length=120",
             "--score=y"],
            capture_output=True, text=True, timeout=120,
            creationflags=creation_flags
        )
        output = result.stdout + result.stderr

        # Extract score
        score_match = re.search(r'rated at (-?[\d.]+)/10', output)
        score = float(score_match.group(1)) if score_match else 0.0

        return output, score
    except FileNotFoundError:
        print("pylint not installed. Install with: pip install pylint", file=sys.stderr)
        sys.exit(2)
    except subprocess.TimeoutExpired:
        print("pylint timed out after 120 seconds", file=sys.stderr)
        sys.exit(2)


def filter_pylint_output(output: str, changed_lines: dict[str, set[int]], target: Path) -> tuple[str, int]:
    """Filter pylint output to only show violations on changed lines.

    Returns (filtered_output, count_of_new_violations).
    """
    # Pylint output format: filename:line:col: CODE message
    violation_pattern = re.compile(r'^(.+?):(\d+):\d+: ([A-Z]\d{4}): (.+)$')

    filtered_lines = []
    new_count = 0
    suppressed_count = 0
    target_resolved = str(target.resolve())

    for line in output.splitlines():
        match = violation_pattern.match(line)
        if match:
            filepath = match.group(1)
            lineno = int(match.group(2))

            # Resolve the filepath for comparison
            try:
                resolved = str(Path(filepath).resolve())
            except (OSError, ValueError):
                resolved = filepath

            file_changes = changed_lines.get(resolved, changed_lines.get(target_resolved, set()))
            if file_changes and lineno in file_changes:
                filtered_lines.append(f"[NEW] {line}")
                new_count += 1
            else:
                suppressed_count += 1
        elif re.match(r'^Your code has been rated', line):
            filtered_lines.append(line)
        elif re.match(r'^\*+', line):
            # Module header line
            filtered_lines.append(line)

    if suppressed_count > 0:
        filtered_lines.insert(0, f"({suppressed_count} pre-existing violations hidden, {new_count} new)")

    return "\n".join(filtered_lines), new_count


def main():
    parser = argparse.ArgumentParser(description="Pylint with delta filtering")
    parser.add_argument("target", help="File or directory to lint")
    parser.add_argument("--all", action="store_true", help="Show all violations")
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"Target not found: {target}", file=sys.stderr)
        sys.exit(1)

    output, score = run_pylint(target)

    if args.all:
        # No filtering
        print(output)
        print(f"\nScore: {score}/10")
        sys.exit(0 if score >= 7.0 else 1)

    changed_lines = get_changed_lines(target)

    if changed_lines is None:
        # Git unavailable or untracked — show everything
        print("(git delta unavailable — showing all violations)")
        print(output)
        sys.exit(0 if score >= 7.0 else 1)

    if not changed_lines:
        # No changes — just show score
        print(f"No changed lines detected. Overall score: {score}/10")
        sys.exit(0)

    filtered, new_count = filter_pylint_output(output, changed_lines, target)
    print(filtered)
    print(f"\nOverall score: {score}/10 | New violations on changed lines: {new_count}")

    # Pass if overall score >= 7.0 (pre-existing issues don't block)
    sys.exit(0 if score >= 7.0 else 1)


if __name__ == "__main__":
    main()
