#!/usr/bin/env python3
"""
Stage 2.9: Duplicate Code Detection (pylint similarities)

Checks code duplication with pylint similarity checker.

FAIL FAST: If pylint is not installed, pipeline HALTS with install instructions.
Non-blocking: Duplicates found is WARN, not FAIL.

Exit codes:
- 0 = No duplicates → PASS
- 1 = Duplicates found → WARN (non-blocking)
- 2 = pylint not installed → FAIL (blocking, fail fast)
- 3 = Error occurred → FAIL (blocking)
"""

import subprocess
import sys
import re
from pathlib import Path


def check_pylint_installed() -> bool:
    """Check if pylint is installed and accessible."""
    try:
        # Prevent blue console flash on Windows
        creation_flags = 0x08000000 if sys.platform == 'win32' else 0
        result = subprocess.run(
            [sys.executable, '-m', 'pylint', '--version'],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=creation_flags
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def parse_pylint_similarities(output: str) -> list[dict]:
    """Parse pylint similarity output into structured findings."""
    findings = []

    # pylint similarities output format:
    # SIMILARITIES:
    # --------------------
    # path/to/file1:10: Top level
    # path/to/file2:15: Top level
    #   Similar code in [file1, file2]:
    #     <duplicate lines>
    #
    # Or: "Similarity: X lines (Y%)"

    lines = output.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Look for similarity reports
        if 'SIMILARITIES' in line or 'Similarities' in line:
            i += 2  # Skip the separator line
            continue

        if 'similar' in line.lower() or 'duplicate' in line.lower():
            # Capture the finding
            finding = {'lines': [], 'files': [], 'percentage': None}

            # Look for percentage
            pct_match = re.search(r'(\d+)%', line)
            if pct_match:
                finding['percentage'] = int(pct_match.group(1))
                finding['summary'] = line.strip()
                findings.append(finding)
                i += 1
                continue

        i += 1

    return findings


def check_duplication(target: str) -> int:
    """
    Check code duplication with pylint similarity checker.

    Returns:
        0 = PASS (no duplicates)
        1 = WARN (duplicates found, non-blocking)
        2 = FAIL (pylint not installed, blocking)
        3 = FAIL (error occurred, blocking)
    """
    # Fail fast: check if pylint is installed
    if not check_pylint_installed():
        print("❌ FAIL: pylint is not installed")
        print()
        print("Required for Stage 2.9: Duplicate Code Detection")
        print()
        print("Install with:")
        print("  pip install pylint")
        print()
        print("pylint includes similarity detection for Python code.")
        return 2

    # Convert target to path
    target_path = Path(target)

    # Build pylint command
    cmd = [
        sys.executable, '-m', 'pylint',
        '--disable=all',
        '--enable=similarities',
        '--min-similarity-lines=5',
        str(target_path)
    ]

    # Run pylint
    # Prevent blue console flash on Windows
    creation_flags = 0x08000000 if sys.platform == 'win32' else 0
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,  # 2 minute timeout for large codebases
        creationflags=creation_flags
    )

    # pylint returns:
    # 0 = no issues (including no similarities)
    # non-zero = issues found (including similarities)
    # We need to parse output to distinguish similarities from errors

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    # Check for actual pylint errors (ignore JSON parsing from other scripts)
    has_errors = False
    error_lines = []

    # Pylint-specific error patterns (not generic "error" text)
    pylint_error_patterns = [
        'F0001',  # Fatal error
        'E0001',  # Syntax error
        'fatal error',
        'syntax error',
        'import error',
        'no module named',
    ]

    for line in stdout.split('\n'):
        line_lower = line.lower()
        # Check for pylint-specific errors only
        if any(pattern in line_lower for pattern in pylint_error_patterns):
            # Filter out similarity section
            if 'similar' not in line_lower and 'similarities' not in line_lower:
                has_errors = True
                error_lines.append(line.strip())

    # Check stderr only for pylint-related messages
    if stderr and not any(word in stderr.lower() for word in ['similar', 'similarity', 'duplicat']):
        # Stderr contains non-similarity error
        if 'usage:' in stderr.lower() or 'argument' in stderr.lower():
            # Pylint invocation error (not code error)
            has_errors = True
            error_lines.append('pylint invocation error')
            if stderr:
                error_lines.append(stderr[:200])

    if has_errors:
        print(f"❌ FAIL: pylint error occurred")
        for line in error_lines[:5]:
            print(f"  {line}")
        return 3

    # Check for similarities in output
    has_similarities = False
    similarity_count = 0

    # Look for similarity reports
    # Format: "More than X lines of code are similar across Y files"
    # Or: "Similarity between file1:line and file2:line"

    similarity_lines = []
    in_similarity_section = False

    for line in stdout.split('\n'):
        if 'SIMILARITIES' in line.upper() or 'Similarities' in line:
            in_similarity_section = True
            continue

        if in_similarity_section:
            if line.strip().startswith('---') or line.strip().startswith('==='):
                continue

            if line.strip() and not line.startswith(' ') and 'Your code' not in line:
                # This is a similarity report
                similarity_lines.append(line.strip())
                similarity_count += 1

    # Also check stderr for similarities (pylint sometimes puts them there)
    for line in stderr.split('\n'):
        if 'similar' in line.lower() and 'SIMILARITIES' not in line.upper():
            similarity_lines.append(line.strip())
            similarity_count += 1

    has_similarities = similarity_count > 0

    if not has_similarities:
        print(f"✅ PASS: No code duplication found in {target}")
        return 0

    # Duplicates found - show summary
    print(f"⚠️  WARN: Code duplication detected in {target}")
    print()

    # Show similarity summary
    for line in similarity_lines[:10]:  # Show first 10 similarity lines
        print(f"  {line}")

    if similarity_count > 10:
        print(f"  ... ({similarity_count - 10} more similarities found)")

    print()
    print("Recommendation:")
    print("  Consider refactoring duplicated code to improve maintainability.")
    print(f"  Run: pylint --disable=all --enable=similarities {target}")
    print()
    print("⚠️  WARN: Pipeline continues (non-blocking)")

    return 1


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: stage2_9_duplication.py <target>")
        sys.exit(3)

    target = sys.argv[1]
    sys.exit(check_duplication(target))
