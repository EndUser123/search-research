#!/usr/bin/env python3
"""
Fast pattern scanner - focused scan of high-priority directories only.
"""
import re
from pathlib import Path

# High-priority directories to scan (where bugs are most likely)
TARGET_DIRS = [
    "P:/packages",           # Hook packages
    "P:/__csf/.claude/hooks", # Core hooks
    "P:/__csf/src",          # Main source
]

# Patterns to scan for
PATTERNS = [
    {
        "name": "stale_task_metadata",
        "severity": "CRITICAL",
        "pattern": r'active_task.*\.get\([\"\' ]metadata[\"\' ]\)',
        "description": "Extracting session/terminal IDs from stale task metadata"
    },
    {
        "name": "hardcoded_session_json",
        "severity": "MEDIUM",
        "pattern": r'[\"\']P:/\.claude/current_session\.json[\"\']',
        "description": "Hardcoded path to current_session.json"
    },
    {
        "name": "missing_error_handling",
        "severity": "MEDIUM",
        "pattern": r'json\.load\([^)]+\)(?!\s*except)',
        "description": "JSON load without error handling"
    },
    {
        "name": "mutable_default_args",
        "severity": "LOW",
        "pattern": r'def\s+\w+\s*\([^)]*=\s*(?:\[\]|\{\})',
        "description": "Mutable default arguments"
    },
]

def scan_file(file_path, pattern_data):
    """Scan a single file for a pattern."""
    matches = []
    try:
        with open(file_path, encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if re.search(pattern_data["pattern"], line):
                    matches.append({
                        "file": str(file_path),
                        "line": line_num,
                        "content": line.strip(),
                        "pattern": pattern_data["name"],
                        "pattern_name": pattern_data["name"],
                        "description": pattern_data["description"],
                        "severity": pattern_data["severity"]
                    })
    except (OSError, UnicodeDecodeError):
        pass
    return matches

def main():
    print("=" * 70)
    print("FAST PATTERN SCAN (High-Priority Directories Only)")
    print("=" * 70)
    print()

    all_matches = []

    for target_dir in TARGET_DIRS:
        root = Path(target_dir)
        if not root.exists():
            continue

        print(f"Scanning: {target_dir}")
        file_count = 0

        for py_file in root.rglob("*.py"):
            # Skip common exclusion directories
            if any(skip in str(py_file) for skip in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']):
                continue

            file_count += 1
            if file_count % 50 == 0:
                print(f"  Scanned {file_count} files...")

            for pattern_data in PATTERNS:
                matches = scan_file(py_file, pattern_data)
                all_matches.extend(matches)

        print(f"  Scanned {file_count} Python files")
        print()

    # Group results by severity
    by_severity = {"CRITICAL": [], "HIGH": [], "MEDIUM": [], "LOW": []}
    for match in all_matches:
        severity = match["severity"]
        by_severity[severity].append(match)

    print("=" * 70)
    print("SCAN RESULTS")
    print("=" * 70)
    print(f"Total matches found: {len(all_matches)}")
    print()

    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        matches = by_severity[severity]
        if matches:
            print(f"{severity} SEVERITY: {len(matches)} matches")
            for match in matches[:10]:  # Show first 10
                print(f"  - {match['file']}:{match['line']}")
                print(f"    {match['pattern']}: {match['description']}")
            if len(matches) > 10:
                print(f"  ... and {len(matches) - 10} more")
            print()

    return all_matches

if __name__ == "__main__":
    main()
