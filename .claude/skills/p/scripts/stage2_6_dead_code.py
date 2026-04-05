#!/usr/bin/env python3
"""
Stage 2.6: Dead Code Detection (vulture)

Detects unused Python code (functions, classes, variables) using vulture.
Early detection prevents dead code from accumulating.

Usage:
    python stage2_6_dead_code.py <target>

Exit codes:
- 0 = No dead code found
- 1 = Dead code found (informational, not blocking)
- 2 = Error occurred
"""

import subprocess
import sys
from pathlib import Path


def check_dead_code(target: str) -> int:
    """
    Check for dead code using vulture.

    Returns:
        0 = PASS (no dead code)
        1 = WARN (dead code found)
        2 = FAIL (error)
    """
    # Check if vulture is installed
    # Prevent blue console flash on Windows
    creation_flags = 0x08000000 if sys.platform == 'win32' else 0
    check_result = subprocess.run(
        ['python', '-m', 'vulture', '--version'],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    if check_result.returncode != 0:
        print("❌ FAIL: vulture not installed")
        print("   Install: pip install vulture")
        return 2

    # Run vulture with min-confidence 80
    result = subprocess.run(
        ['python', '-m', 'vulture', target, '--min-confidence', '80'],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    exit_code = result.returncode

    if exit_code == 0:
        # No dead code found
        print(f"✅ PASS: No dead code found in {target}")
        return 0

    # Vulture found dead code or had issues
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    # Check if this is actual dead code findings
    if stdout and ('unused' in stdout.lower() or 'dead' in stdout.lower() or '%' in stdout):
        # Parse and display findings
        lines = stdout.split('\n')
        print(f"⚠️  WARN: Dead code detected in {target}")

        # Show summary if available
        for line in lines:
            if '%' in line or 'unused' in line.lower():
                print(f"  {line}")

        # Show first few dead code items
        dead_items = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('%') and ':' in line:
                dead_items.append(line)
                if len(dead_items) >= 5:
                    break

        if dead_items:
            print("\n  Sample dead code:")
            for item in dead_items:
                print(f"    {item}")

        print(f"\n  Total: {len([l for l in lines if ':' in l])} items found")
        print("  Review with: vulture <target> --min-confidence 80")
        return 1

    # Error condition
    if stderr:
        print(f"❌ FAIL: vulture error")
        for line in stderr.split('\n'):
            if line.strip():
                print(f"  {line}")
    else:
        print(f"❌ FAIL: vulture exited with code {exit_code}")

    return 2


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: stage2_6_dead_code.py <target>")
        sys.exit(2)

    target = sys.argv[1]
    sys.exit(check_dead_code(target))
