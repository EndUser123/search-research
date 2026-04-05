#!/usr/bin/env python3
"""
Stage 2.7: Security Scanning (Bandit)

Static security analysis for common Python vulnerabilities using Bandit.
Detects security issues like SQL injection, hardcoded passwords, etc.

Usage:
    python stage2_7_security.py <target>

Exit codes:
- 0 = No security issues
- 1 = Medium/Low severity issues found (informational)
- 2 = High/Critical severity found (blocking)
- 3 = Error occurred
"""

import json
import subprocess
import sys
from pathlib import Path


def check_security(target: str) -> int:
    """
    Check for security issues using Bandit.

    Returns:
        0 = PASS (no issues)
        1 = WARN (medium/low severity)
        2 = FAIL (high/critical severity - HALT)
        3 = ERROR (bandit not installed or other error)
    """
    # Check if bandit is installed
    # Prevent blue console flash on Windows
    creation_flags = 0x08000000 if sys.platform == 'win32' else 0
    check_result = subprocess.run(
        ['python', '-m', 'bandit', '--version'],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    if check_result.returncode != 0:
        print("❌ ERROR: bandit not installed")
        print("   Install: pip install bandit")
        return 3

    # Run bandit with JSON output for parsing
    result = subprocess.run(
        ['python', '-m', 'bandit', '-r', target, '-f', 'json'],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    exit_code = result.returncode

    # Bandit returns:
    # 0 = no issues
    # 1 = issues found
    # 2+ = error

    if exit_code == 0:
        print(f"✅ PASS: No security issues found in {target}")
        return 0

    # Parse JSON output for severity classification
    try:
        bandit_output = json.loads(result.stdout)
        results = bandit_output.get('results', [])
        errors = bandit_output.get('errors', [])

        if errors:
            print(f"❌ ERROR: Bandit encountered errors:")
            for error in errors:
                print(f"  {error}")
            return 3

        if not results:
            print(f"✅ PASS: No security issues found in {target}")
            return 0

        # Classify by severity
        high_critical = [r for r in results if r.get('issue_severity', 'MEDIUM') in ('HIGH', 'CRITICAL')]
        medium_low = [r for r in results if r.get('issue_severity', 'MEDIUM') in ('MEDIUM', 'LOW')]

        if high_critical:
            print(f"❌ FAIL: High/Critical security issues found in {target}")
            print(f"   {len(high_critical)} high/critical severity issues detected")

            # Show high/critical findings
            for issue in high_critical[:5]:
                filename = issue.get('filename', 'unknown')
                line = issue.get('line_number', '?')
                severity = issue.get('issue_severity', 'UNKNOWN')
                test_id = issue.get('test_id', '???')
                text = issue.get('issue_text', 'No description')

                print(f"\n  [{severity}] {test_id}")
                print(f"    File: {filename}:{line}")
                print(f"    {text[:100]}{'...' if len(text) > 100 else ''}")

            if len(high_critical) > 5:
                print(f"\n  ... and {len(high_critical) - 5} more")

            return 2

        elif medium_low:
            print(f"⚠️  WARN: Medium/Low security issues found in {target}")
            print(f"   {len(medium_low)} issues detected (non-blocking)")

            # Show medium/low findings (sample)
            for issue in medium_low[:3]:
                filename = issue.get('filename', 'unknown')
                line = issue.get('line_number', '?')
                severity = issue.get('issue_severity', 'MEDIUM')
                test_id = issue.get('test_id', '???')
                text = issue.get('issue_text', 'No description')

                print(f"\n  [{severity}] {test_id}")
                print(f"    File: {filename}:{line}")
                print(f"    {text[:80]}{'...' if len(text) > 80 else ''}")

            if len(medium_low) > 3:
                print(f"\n  ... and {len(medium_low) - 3} more")
                print(f"  Review with: bandit -r {target} -ll")

            return 1

    except json.JSONDecodeError:
        # Fallback to plain text parsing
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()

        if stderr:
            print(f"❌ ERROR: Bandit error")
            for line in stderr.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            # Try to extract severity from stdout
            if 'high' in stdout.lower() or 'critical' in stdout.lower():
                print(f"❌ FAIL: High severity issues detected")
                print(f"  Run: bandit -r {target} -ll")
                return 2
            else:
                print(f"⚠️  WARN: Security issues detected")
                print(f"  Run: bandit -r {target} -ll")
                return 1

    return 3


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: stage2_7_security.py <target>")
        sys.exit(3)

    target = sys.argv[1]
    sys.exit(check_security(target))
