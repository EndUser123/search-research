#!/usr/bin/env python3
"""
Stage 3 Layer 1: Change Delta Gate

Filters findings to only those affecting changed files.

Usage:
    python stage3_layer1_delta.py <findings.json> [findings2.json ...] [--base HEAD~1] [--head HEAD]

Output:
    Writes to P:/.claude/state/layer1-{terminal}-{timestamp}.json
    Prints output file path to stdout for chaining
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Import shared terminal detection module
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "hooks"))
from terminal_detection import detect_terminal_id

STATE_DIR = Path("P:/.claude/state")


def write_state_file(layer: int, result: dict) -> Path:
    """Write result to state file with terminal isolation."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    terminal_id = detect_terminal_id()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"layer{layer}-{terminal_id}-{timestamp}.json"
    output_path = STATE_DIR / filename
    result['_meta'] = {
        'terminal_id': terminal_id,
        'timestamp': timestamp,
        'output_file': str(output_path)
    }
    output_path.write_text(json.dumps(result, indent=2))
    return output_path


def load_findings(findings_path: Path) -> tuple:
    """
    Load findings and changed_files from a single JSON file with safe parsing.

    Returns:
        tuple: (findings_list, changed_files_set)
    """
    if not findings_path.exists():
        return [], set()

    try:
        content = findings_path.read_text(encoding="utf-8")
        data = json.loads(content)
        findings = data.get('findings', [])
        changed_files = set(data.get('changed_files', []))
        return findings, changed_files
    except json.JSONDecodeError as e:
        # Log error and return empty tuple (fail open for single file)
        error_log = STATE_DIR / "json_parse_errors.log"
        with open(error_log, "a") as f:
            f.write(f"{datetime.now().isoformat()} - {findings_path}: {e}\n")
            f.write(f"  Content preview: {content[:500]}...\n")
        print(f"⚠️  Warning: Invalid JSON in {findings_path.name}, skipping", file=sys.stderr)
        return [], set()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('findings', nargs='+', help='Path(s) to findings JSON file(s)')
    parser.add_argument('--base', default='HEAD~1', help='Base commit (IGNORED in multi-terminal env)')
    parser.add_argument('--head', default='HEAD', help='Head commit (IGNORED in multi-terminal env)')
    parser.add_argument('--no-git', action='store_true', help='Skip git-based delta filtering (use changed_files from findings JSON)')
    args = parser.parse_args()

    # Load and merge findings from all input files
    all_findings = []
    all_changed_files = set()
    for findings_file in args.findings:
        findings_path = Path(findings_file)
        findings, changed_files = load_findings(findings_path)
        all_findings.extend(findings)
        all_changed_files.update(changed_files)

    if not all_findings:
        print(json.dumps({'error': 'No findings loaded from input files', 'filtered': []}))
        sys.exit(1)

    # Create merged findings structure for processing
    findings = {'findings': all_findings}

    # IMPORTANT: Skip git-based filtering in multi-terminal environments
    # Git state cannot be trusted across concurrent terminals - use explicit changed_files instead
    if args.no_git or all_changed_files:
        # Use changed_files from findings JSON (provided by caller)
        changed_files = all_changed_files if all_changed_files else {f.get('evidence', {}).get('file_path', '') for f in all_findings}

        # Filter findings to changed files only
        filtered = []
        for finding in findings.get('findings', []):
            file_path = finding.get('evidence', {}).get('file_path', '')
            if any(cf in file_path or file_path in cf for cf in changed_files):
                filtered.append(finding)

        result = {
            'layer': 1,
            'name': 'change_delta_gate',
            'input_count': len(findings.get('findings', [])),
            'output_count': len(filtered),
            'changed_files': list(changed_files),
            'filtered': filtered,
            'warning': 'Using explicit changed_files (git skipped for multi-terminal safety)'
        }

    # Try to import CSF module only if --no-git not specified and no explicit changed_files
    else:
        try:
            sys.path.insert(0, 'P:/__csf/src')
            from orchestration.change_delta_gate import ChangeDeltaGate

            gate = ChangeDeltaGate('P:/')
            context = gate.prepare_subagent_context(args.base, args.head)
            changed_files = set(context.changed_files)

            # Filter findings to changed files only
            filtered = []
            for finding in findings.get('findings', []):
                file_path = finding.get('evidence', {}).get('file_path', '')
                if any(cf in file_path or file_path in cf for cf in changed_files):
                    filtered.append(finding)

            result = {
                'layer': 1,
                'name': 'change_delta_gate',
                'input_count': len(findings.get('findings', [])),
                'output_count': len(filtered),
                'changed_files': list(changed_files),
                'filtered': filtered
            }

        except ImportError:
            # CSF not available - pass through all findings
            result = {
                'layer': 1,
                'name': 'change_delta_gate',
                'input_count': len(findings.get('findings', [])),
                'output_count': len(findings.get('findings', [])),
                'filtered': findings.get('findings', []),
                'warning': 'CSF module not available, passing through all findings'
            }

    # Write to state file and print path for chaining
    output_path = write_state_file(1, result)
    print(str(output_path))


if __name__ == '__main__':
    main()
