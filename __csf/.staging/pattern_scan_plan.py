#!/usr/bin/env python3
"""
Comprehensive Pattern Scanning for Bug Detection

Scans codebase for known anti-patterns that could cause bugs similar to
the session-binding issue we just fixed.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from re import Pattern


@dataclass
class PatternMatch:
    """Represents a single pattern match found in code."""
    pattern_name: str
    file_path: str
    line_number: int
    line_content: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str


@dataclass
class ScanPattern:
    """Defines a bug pattern to search for."""
    name: str
    description: str
    severity: str
    file_patterns: list[str]  # e.g., ["*.py", "hooks/*.py"]
    regex: Pattern[str]
    fix_recommendation: str


# Bug patterns to scan for
PATTERNS = [
    ScanPattern(
        name="stale_task_metadata",
        description="Extracting session/terminal IDs from stale task metadata instead of authoritative source",
        severity="CRITICAL",
        file_patterns=["*.py"],
        regex=re.compile(
            r'(?:active_task|task_tracker|task_data)\.get\(["\']metadata["\']\)\.get\(["\'](?:session|terminal|transcript)_path["\']',
            re.IGNORECASE
        ),
        fix_recommendation="Read from current_session.json or terminal_detection.py instead of task metadata"
    ),

    ScanPattern(
        name="hardcoded_session_json_path",
        description="Hardcoded path to current_session.json instead of using portable detection",
        severity="MEDIUM",
        file_patterns=["*.py"],
        regex=re.compile(
            r'["\']P:/\.claude/current_session\.json["\']',
            re.IGNORECASE
        ),
        fix_recommendation="Use portable path resolution via project root detection"
    ),

    ScanPattern(
        name="race_condition_file_read",
        description="Reading file without existence check (TOCTOU race condition)",
        severity="MEDIUM",
        file_patterns=["*.py"],
        regex=re.compile(
            r'open\((?!\s*.*\.exists\(\s*\))',
            re.IGNORECASE
        ),
        fix_recommendation="Add .exists() check before open() or use atomic operations"
    ),

    ScanPattern(
        name="missing_error_handling",
        description="File/network operations without proper error handling",
        severity="MEDIUM",
        file_patterns=["*.py"],
        regex=re.compile(
            r'(?:json\.load|open\(|Path\.read_text)\([^)]*\)(?!\s*(?:except|try:|with\s))',
            re.MULTILINE
        ),
        fix_recommendation="Wrap in try-except or use 'with' statement for proper cleanup"
    ),

    ScanPattern(
        name="implicit_session_assumption",
        description="Assuming session/terminal ID without verification",
        severity="HIGH",
        file_patterns=["*.py"],
        regex=re.compile(
            r'(?:session_id|terminal_id)\s*(?:=|==)\s*(?!("|"|extract|get|detect))',
            re.IGNORECASE
        ),
        fix_recommendation="Always verify session IDs via authoritative source or terminal_detection.py"
    ),

    ScanPattern(
        name="deprecated_path_separator",
        description="Using Windows path separator in portable code",
        severity="LOW",
        file_patterns=["*.py"],
        regex=re.compile(
            r'["\'][A-Z]:[/\\](?![a-zA-Z])',
        ),
        fix_recommendation="Use pathlib.Path for cross-platform compatibility"
    ),

    ScanPattern(
        name="mutable_default_args",
        description="Using mutable default arguments (list/dict)",
        severity="LOW",
        file_patterns=["*.py"],
        regex=re.compile(
            r'def\s+\w+\s*\([^)]*=\s*(?:\[\]|\{)',
        ),
        fix_recommendation="Use None and initialize inside function body"
    ),

    ScanPattern(
        name="global_state_mutation",
        description="Mutating global state without thread safety",
        severity="HIGH",
        file_patterns=["*.py"],
        regex=re.compile(
            r'^\s*(?:\w+\s*=\s*[^=\n]+(?:(?!\n)))+(?=^def\s|\nclass\s)',
            re.MULTILINE | re.IGNORECASE
        ),
        fix_recommendation="Use thread-safe primitives or avoid global state"
    ),

    ScanPattern(
        name="unchecked_subprocess_call",
        description="Subprocess call without shell=False (command injection risk)",
        severity="HIGH",
        file_patterns=["*.py"],
        regex=re.compile(
            r'subprocess\.(?:run|call|Popen)\([^)]*\)(?!\s*shell\s*=\s*False)',
        ),
        fix_recommendation="Always use shell=False for security unless shell is explicitly needed"
    ),
]


def scan_file(file_path: Path, pattern: ScanPattern) -> list[PatternMatch]:
    """Scan a single file for a pattern."""
    matches = []
    try:
        with open(file_path, encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if pattern.regex.search(line):
                    matches.append(PatternMatch(
                        pattern_name=pattern.name,
                        file_path=str(file_path),
                        line_number=line_num,
                        line_content=line.strip(),
                        severity=pattern.severity,
                        description=pattern.description
                    ))
    except (OSError, UnicodeDecodeError):
        pass

    return matches


def scan_directory(root_dir: Path, patterns: list[ScanPattern] = None) -> dict[str, list[PatternMatch]]:
    """Scan directory for all patterns."""
    if patterns is None:
        patterns = PATTERNS

    results = defaultdict(list)

    for pattern in patterns:
        # Find files matching pattern
        for file_pattern in pattern.file_patterns:
            for file_path in root_dir.rglob(file_pattern):
                # Skip certain directories
                if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'node_modules', '.venv']):
                    continue

                matches = scan_file(file_path, pattern)
                if matches:
                    results[pattern.name].extend(matches)

    return results


def print_summary(results: dict[str, list[PatternMatch]]):
    """Print scan summary."""
    total_matches = sum(len(matches) for matches in results.values())

    print("=" * 70)
    print("PATTERN SCANNING SUMMARY")
    print("=" * 70)
    print()
    print(f"Total patterns scanned: {len(PATTERNS)}")
    print(f"Total matches found: {total_matches}")
    print()

    # Group by severity
    by_severity = defaultdict(list)
    for pattern_name, matches in results.items():
        for match in matches:
            by_severity[match.severity].append(match)

    for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
        if severity in by_severity:
            print(f"{severity} SEVERITY: {len(by_severity[severity])} matches")
            for match in by_severity[severity][:5]:  # Show first 5
                print(f"  - {match.file_path}:{match.line_number}")
                print(f"    {match.pattern_name}: {match.description[:80]}...")
            if len(by_severity[severity]) > 5:
                print(f"  ... and {len(by_severity[severity]) - 5} more")
            print()


if __name__ == "__main__":
    # Scan from CSF root
    root = Path("P:/__csf")
    results = scan_directory(root)
    print_summary(results)
