#!/usr/bin/env python3
"""
P6 Security Scanning - Bandit static analysis

Migrated from /v Stage 2.7: Security scanning using Bandit.
Detects security issues like SQL injection, hardcoded passwords, etc.

Usage:
    python security.py <target>

Exit codes:
- 0 = No security issues (PASS)
- 1 = Medium/Low severity issues found (WARN)
- 2 = High/Critical severity found (FAIL/HALT)
- 3 = Error occurred (tool not installed)
"""

import json
import subprocess
import sys
from pathlib import Path


def validate_target_path(target: str) -> None:
    """
    Validate and sanitize target path before passing to subprocess.

    Prevents:
    - Command injection via shell metacharacters
    - Path traversal attacks (../../etc/passwd)
    - Access to sensitive system directories

    Args:
        target: User-provided target path from command line

    Raises:
        ValueError: If path is invalid or unsafe
    """
    # Check for shell metacharacters that could enable command injection
    shell_metachars = [';', '&', '|', '$', '`', '(', ')', '<', '>', '\n', '\r']
    if any(char in target for char in shell_metachars):
        raise ValueError(f"Path contains invalid characters: {shell_metachars}")

    # Resolve to absolute path and check existence
    target_path = Path(target).resolve()

    if not target_path.exists():
        raise ValueError(f"Target path does not exist: {target}")

    if not target_path.is_dir():
        raise ValueError(f"Target must be a directory: {target}")

    # Prevent access to sensitive system directories
    sensitive_paths = [
        Path('/etc'),
        Path('/sys'),
        Path('/proc'),
        Path('/root'),
        Path.home() / '.ssh' if Path.home() else Path('.ssh'),
    ]

    for sensitive in sensitive_paths:
        try:
            if sensitive.exists() and target_path.resolve().is_relative_to(sensitive):
                raise ValueError(f"Access to sensitive directory blocked: {sensitive}")
        except (OSError, RuntimeError):
            # Path doesn't exist or can't be resolved - skip
            continue


def check_security_bandit(target: str) -> int:
    """
    Check for security issues using Bandit.

    Returns:
        0 = PASS (no issues)
        1 = WARN (medium/low severity)
        2 = FAIL (high/critical severity - HALT)
        3 = ERROR (bandit not installed or other error)
    """
    # Validate target path before any operations
    try:
        validate_target_path(target)
    except ValueError as e:
        print(f"❌ INVALID TARGET: {e}")
        return 3

    # Prevent blue console flash on Windows
    creation_flags = 0x08000000 if sys.platform == 'win32' else 0

    # Check if bandit is installed
    check_result = subprocess.run(
        ['bandit', '--version'],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    if check_result.returncode != 0:
        print("❌ BANDIT NOT INSTALLED")
        print("   Install: pip install bandit")
        return 3

    # Run bandit with JSON output for parsing
    result = subprocess.run(
        ['bandit', '-r', target, '-f', 'json'],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    exit_code = result.returncode

    if exit_code == 0:
        print(f"✅ BANDIT: No security issues found in {target}")
        return 0

    # Parse JSON output for severity classification
    try:
        bandit_output = json.loads(result.stdout)
        results = bandit_output.get('results', [])
        errors = bandit_output.get('errors', [])

        if errors:
            print("❌ BANDIT ERROR:")
            for error in errors:
                print(f"  {error}")
            return 3

        if not results:
            print(f"✅ BANDIT: No security issues found in {target}")
            return 0

        # Classify by severity
        high_critical = [r for r in results if r.get('issue_severity', 'MEDIUM') in ('HIGH', 'CRITICAL')]
        medium_low = [r for r in results if r.get('issue_severity', 'MEDIUM') in ('MEDIUM', 'LOW')]

        if high_critical:
            print(f"❌ BANDIT: High/Critical security issues found in {target}")
            print(f"   {len(high_critical)} high/critical severity issues detected")

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
            print(f"⚠️  BANDIT: Medium/Low security issues found in {target}")
            print(f"   {len(medium_low)} issues detected (non-blocking)")

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
            print("❌ BANDIT ERROR:")
            for line in stderr.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            if 'high' in stdout.lower() or 'critical' in stdout.lower():
                print("❌ BANDIT: High severity issues detected")
                print(f"  Run: bandit -r {target} -ll")
                return 2
            else:
                print("⚠️  BANDIT: Security issues detected")
                print(f"  Run: bandit -r {target} -ll")
                return 1

    return 3


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: security.py <target>")
        sys.exit(3)

    target = sys.argv[1]
    sys.exit(check_security_bandit(target))
