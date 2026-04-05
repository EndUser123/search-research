#!/usr/bin/env python3
"""
Stage 3 Output: High Confidence Findings Reporter

Writes filtered findings from Stage 3 adversarial review to TaskList as JSON.
Each finding becomes a task that /TDD can process.

Priority Level Mapping (from /refactor):
- P0: Bugs & Race Conditions → CRITICAL
- P1: Error Handling → HIGH
- P2: DRY Violations → MEDIUM
- P3: Conventions → LOW

Usage:
    python stage3_findings.py --target <target> --critical <count> --high <count> --raw <count> --ratio <float> --critical-findings '[...]' --high-findings '[...]'

Exit codes:
    0 - Always
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

# Add hooks directory for terminal detection
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

try:
    from terminal_detection import detect_terminal_id
except ImportError:
    # Fallback if terminal_detection not available
    def detect_terminal_id() -> str:
        return f"env_{os.getpid()}"


def validate_findings_json(input_data) -> bool:
    """Validates agent output is valid JSON with required fields.

    Args:
        input_data: Either a JSON string or a file path (str or Path)

    Returns:
        True if valid JSON with required fields, False otherwise

    Raises:
        ValueError: If JSON is malformed (for test consistency)
    """
    import json

    # Determine if input_data is a file path or JSON string
    json_str = None
    if isinstance(input_data, Path):
        # It's a Path object - read from file
        try:
            json_str = input_data.read_text(encoding='utf-8')
        except (IOError, OSError):
            return False
    elif isinstance(input_data, str):
        # Check if it's a file path or JSON string
        path = Path(input_data)
        if path.exists() and path.is_file():
            try:
                json_str = path.read_text(encoding='utf-8')
            except (IOError, OSError):
                return False
        else:
            # Treat as JSON string
            json_str = input_data
    else:
        return False

    # Parse JSON
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return False

    # Check if data is a list (array of findings)
    if isinstance(data, list):
        # List must contain findings with required fields
        for finding in data:
            if not isinstance(finding, dict):
                return False
            if not all(k in finding for k in ['id', 'title', 'severity']):
                return False
        return True

    # Check if data is a dict with required keys
    if not isinstance(data, dict):
        return False

    # Check required top-level keys
    if 'findings' not in data:
        return False

    findings = data['findings']
    if not isinstance(findings, list):
        return False

    # Validate changed_files is present and is an array
    if 'changed_files' not in data:
        return False

    changed_files = data['changed_files']
    if not isinstance(changed_files, list):
        return False

    # Validate each finding has required fields
    for finding in findings:
        if not isinstance(finding, dict):
            return False
        if not all(k in finding for k in ['id', 'title', 'severity']):
            return False

    return True


def get_adversarial_findings_path(agent: str, terminal_id: str = None) -> Path:
    """Generate terminal-scoped path for adversarial findings.

    Args:
        agent: Agent name (e.g., 'adversarial-security')
        terminal_id: Terminal ID for isolation (auto-detected if None)

    Returns:
        Path object in format: P:/.claude/state/p3_findings/{terminal_id}/adversarial-{agent}-{terminal_id}.json
    """
    if terminal_id is None:
        terminal_id = detect_terminal_id()

    findings_dir = Path(f'P:/.claude/state/p3_findings/{terminal_id}')
    findings_dir.mkdir(parents=True, exist_ok=True)

    return findings_dir / f'adversarial-{agent}-{terminal_id}.json'


def write_findings_atomic(findings: dict, agent: str, filepath: str) -> None:
    """Write findings atomically using temp file + rename pattern.

    Args:
        findings: Dictionary containing findings data to write
        agent: Agent name (for logging/context)
        filepath: Target filepath as string

    Pattern:
        1. Write to {path}.tmp
        2. Atomic rename to {path}

    This ensures readers never see partially-written files.
    """
    import json

    filepath_obj = Path(filepath)
    temp_file = filepath_obj.with_suffix('.tmp')

    # Write to temp file
    temp_file.write_text(json.dumps(findings, indent=2), encoding='utf-8')

    # Atomic rename
    temp_file.replace(filepath_obj)


# Priority level patterns from /refactor
PRIORITY_PATTERNS = {
    'P0': [
        'race condition', 'deadlock', 'concurrency', 'thread safety',
        'data race', 'atomic', 'mutex', 'lock', 'memory leak',
        'buffer overflow', 'null pointer', 'segmentation fault',
        'use after free', 'double free', 'infinite loop'
    ],
    'P1': [
        'error handling', 'exception', 'bare except', 'swallow',
        'silent error', 'unhandled exception', 'try.*except',
        'validation', 'input validation', 'sanitization'
    ],
    'P2': [
        'duplicate', 'duplication', 'copy.*paste', 'dry',
        'repeated code', 'extract', 'consolidate', 'merge'
    ],
    'P3': [
        'type hint', 'formatting', 'naming', 'convention',
        'style', 'docstring', 'comment', 'indentation'
    ]
}


def infer_priority_from_finding(finding: dict) -> str:
    """Infer priority level (P0-P3) from finding content.

    Returns:
        Priority level: 'P0', 'P1', 'P2', or 'P3'
    """
    # Extract text to analyze
    text = ' '.join([
        str(finding.get('title', '')),
        str(finding.get('description', '')),
        str(finding.get('category', ''))
    ]).lower()

    # Check P0 first (most critical)
    for pattern in PRIORITY_PATTERNS['P0']:
        if re.search(pattern, text):
            return 'P0'

    # Check P1
    for pattern in PRIORITY_PATTERNS['P1']:
        if re.search(pattern, text):
            return 'P1'

    # Check P2
    for pattern in PRIORITY_PATTERNS['P2']:
        if re.search(pattern, text):
            return 'P2'

    # Default to P3
    return 'P3'


def priority_to_severity(priority: str) -> str:
    """Map priority level to severity for p3 compatibility.

    P0 → CRITICAL
    P1 → HIGH
    P2 → MEDIUM
    P3 → LOW
    """
    mapping = {
        'P0': 'CRITICAL',
        'P1': 'HIGH',
        'P2': 'MEDIUM',
        'P3': 'LOW'
    }
    return mapping.get(priority, 'LOW')


def get_next_task_id(tasks_dir: Path) -> int:
    """Get the next task ID from .highwatermark file."""
    highwatermark = tasks_dir / ".highwatermark"
    if highwatermark.exists():
        try:
            return int(highwatermark.read_text().strip())
        except (ValueError, IOError):
            pass
    return 1  # Default to task ID 1


def increment_highwatermark(tasks_dir: Path, task_id: int):
    """Update the .highwatermark file after creating a task."""
    highwatermark = tasks_dir / ".highwatermark"
    highwatermark.write_text(str(task_id + 1))


def format_findings_description(findings: dict) -> str:
    """Format findings as a task description with priority levels."""
    lines = []

    # Add priority level legend
    lines.append("## Priority Level Legend (from /refactor)")
    lines.append("- P0 (CRITICAL): Bugs & Race Conditions - fix first")
    lines.append("- P1 (HIGH): Error Handling - bare except, swallowed errors")
    lines.append("- P2 (MEDIUM): DRY Violations - duplicate code")
    lines.append("- P3 (LOW): Conventions - type hints, formatting")
    lines.append("")

    if findings['critical_count'] > 0:
        lines.append(f"## CRITICAL Findings ({findings['critical_count']})")
        for finding in findings['critical_findings']:
            priority = finding.get('priority', 'P0')
            lines.append(f"- [{priority}] {finding.get('id', '?')}: {finding.get('title', 'No title')}")
            if 'file' in finding:
                lines.append(f"  File: {finding['file']}:{finding.get('line', '?')}")
            if 'description' in finding:
                lines.append(f"  {finding['description'][:100]}...")

    if findings['high_count'] > 0:
        if findings['critical_count'] > 0:
            lines.append("")  # Blank line between sections
        lines.append(f"## HIGH Findings ({findings['high_count']})")
        for finding in findings['high_findings']:
            priority = finding.get('priority', 'P1')
            lines.append(f"- [{priority}] {finding.get('id', '?')}: {finding.get('title', 'No title')}")
            if 'file' in finding:
                lines.append(f"  File: {finding['file']}:{finding.get('line', '?')}")
            if 'description' in finding:
                lines.append(f"  {finding['description'][:100]}...")

    lines.append("")
    lines.append(f"Signal-to-noise: {findings['signal_to_noise']:.2f} ({findings['total_filtered']} filtered from {findings['raw_findings_count']} raw findings)")
    lines.append(f"Halt: {'YES' if findings['halt'] else 'NO'}")

    return "\n".join(lines)


def create_task(tasks_dir: Path, task_id: int, findings: dict, terminal_id: str) -> Path:
    """Create a task file in the TaskList directory."""
    # Format findings for task description
    description = format_findings_description(findings)

    # Create task object
    task = {
        "id": str(task_id),
        "subject": f"Stage 3: Adversarial Review Findings - {findings['target']} [terminal:{terminal_id}]",
        "description": description,
        "activeForm": "Processing adversarial review findings",
        "status": "pending",
        "blocks": [],
        "blockedBy": []
    }

    # Write task file
    task_path = tasks_dir / f"{task_id}.json"
    task_path.write_text(json.dumps(task, indent=2))

    return task_path


def main():
    parser = argparse.ArgumentParser(description='Write Stage 3 findings to TaskList')
    parser.add_argument('--target', required=True, help='Validation target')
    parser.add_argument('--critical', type=int, default=0, help='Count of CRITICAL findings')
    parser.add_argument('--high', type=int, default=0, help='Count of HIGH findings')
    parser.add_argument('--raw', type=int, default=0, help='Raw findings count before filtering')
    parser.add_argument('--ratio', type=float, default=1.0, help='Signal-to-noise ratio')
    parser.add_argument('--critical-findings', type=str, default='[]', help='JSON array of critical findings')
    parser.add_argument('--high-findings', type=str, default='[]', help='JSON array of high findings')

    args = parser.parse_args()

    # Get terminal ID for isolation (prevents context bleed between terminals)
    terminal_id = detect_terminal_id()

    # TaskList directory - respects CLAUDE_CODE_TASK_LIST_ID from CLI
    task_list_id = os.environ.get('CLAUDE_CODE_TASK_LIST_ID', 'project-main-tasks')
    tasks_dir = Path.home() / '.claude' / 'tasks' / task_list_id
    tasks_dir.mkdir(parents=True, exist_ok=True)

    # Parse findings arrays and annotate with priority levels
    try:
        critical_findings = json.loads(args.critical_findings)
        # Annotate each finding with inferred priority
        for finding in critical_findings:
            if 'priority' not in finding:
                finding['priority'] = infer_priority_from_finding(finding)
    except json.JSONDecodeError:
        critical_findings = []

    try:
        high_findings = json.loads(args.high_findings)
        # Annotate each finding with inferred priority
        for finding in high_findings:
            if 'priority' not in finding:
                finding['priority'] = infer_priority_from_finding(finding)
    except json.JSONDecodeError:
        high_findings = []

    findings = {
        'target': args.target,
        'critical_findings': critical_findings,
        'high_findings': high_findings,
        'critical_count': args.critical,
        'high_count': args.high,
        'total_filtered': args.critical + args.high,
        'raw_findings_count': args.raw,
        'signal_to_noise': args.ratio,
        'halt': (args.critical > 0 or args.high > 0)
    }

    # Get next task ID and create task
    task_id = get_next_task_id(tasks_dir)
    task_path = create_task(tasks_dir, task_id, findings, terminal_id)

    # Update highwatermark
    increment_highwatermark(tasks_dir, task_id)

    print(f'✅ Task created: {task_path}')
    print(f'   Task ID: {task_id}')
    print(f'   Terminal: {terminal_id}')
    print(f'   CRITICAL: {args.critical}, HIGH: {args.high}')


if __name__ == "__main__":
    main()
