#!/usr/bin/env python3
"""
Stage 3 Layer 3: Behavioral Assertion Validator

Checks test quality before reporting findings.

Usage:
    python stage3_layer3_assertions.py <findings.json> --test-files file1.py,file2.py

Output:
    Writes to P:/.claude/state/layer3-{terminal}-{timestamp}.json
    Prints output file path to stdout for chaining
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

STATE_DIR = Path("P:/.claude/state")


def get_terminal_id() -> str:
    """Get terminal identifier for multi-terminal isolation."""
    for env_var in ['CLAUDE_TERMINAL_ID', 'WINDOWID', 'TERM_SESSION_ID', 'WT_SESSION']:
        value = os.environ.get(env_var)
        if value:
            return value[-8:] if len(value) > 8 else value
    return str(os.getppid())


def write_state_file(layer: int, result: dict) -> Path:
    """Write result to state file with terminal isolation."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    terminal_id = get_terminal_id()
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('findings', help='Path to findings JSON file (output from layer 2)')
    parser.add_argument('--test-files', default='', help='Comma-separated test file paths')
    args = parser.parse_args()

    # Load findings
    findings_path = Path(args.findings)
    if not findings_path.exists():
        print(json.dumps({'error': 'Findings file not found', 'filtered': []}))
        sys.exit(1)

    data = json.loads(findings_path.read_text())
    findings = data.get('filtered', data.get('findings', []))

    # Parse test files
    test_files = [f.strip() for f in args.test_files.split(',') if f.strip()]

    # Try to import CSF module
    try:
        sys.path.insert(0, 'P:/__csf/src')
        from validation.behavioral_assertion_validator import BehavioralAssertionAuditor

        auditor = BehavioralAssertionAuditor()
        report = auditor.audit_test_suite(test_files)

        result = {
            'layer': 3,
            'name': 'behavioral_assertion_validator',
            'input_count': len(findings),
            'output_count': len(findings),  # This layer doesn't filter, just adds metrics
            'test_confidence': report.confidence_multiplier,
            'meaningful_tests': report.meaningful_tests,
            'total_tests': report.total_tests,
            'filtered': findings
        }

    except ImportError:
        # CSF not available - pass through with default metrics
        result = {
            'layer': 3,
            'name': 'behavioral_assertion_validator',
            'input_count': len(findings),
            'output_count': len(findings),
            'test_confidence': 1.0,
            'filtered': findings,
            'warning': 'CSF module not available, using default confidence'
        }
    except AttributeError:
        result = {
            'layer': 3,
            'name': 'behavioral_assertion_validator',
            'input_count': len(findings),
            'output_count': len(findings),
            'test_confidence': 1.0,
            'filtered': findings,
            'warning': 'CSF interface mismatch, using default confidence'
        }

    # Write to state file and print path for chaining
    output_path = write_state_file(3, result)
    print(str(output_path))


if __name__ == '__main__':
    main()
