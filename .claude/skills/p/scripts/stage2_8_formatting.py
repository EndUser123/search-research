#!/usr/bin/env python3
"""
Stage 2.8: Formatting Check (ruff)

Checks code formatting with ruff format, providing clear UX
for "needs formatting" vs actual errors.

Exit codes:
- 0 = All files properly formatted
- 1 = Files would be reformatted (informational, not error)
- 2 = Actual error occurred
"""

import subprocess
import sys
from pathlib import Path


def check_formatting(target: str) -> int:
    """
    Check formatting with ruff.

    Returns:
        0 = PASS (formatted)
        1 = WARN (needs formatting)
        2 = FAIL (error)
    """
    # Prevent blue console flash on Windows
    creation_flags = 0x08000000 if sys.platform == 'win32' else 0
    result = subprocess.run(
        ['python', '-m', 'ruff', 'format', '--check', target],
        capture_output=True,
        text=True,
        creationflags=creation_flags
    )

    # ruff returns:
    # 0 = nothing to format
    # 1 = files would be reformatted
    # 2+ = actual error
    exit_code = result.returncode

    if exit_code == 0:
        print(f"✅ PASS: {target} is properly formatted")
        return 0

    elif exit_code == 1:
        # Parse output to show what needs formatting
        stdout = result.stdout.strip()
        if stdout:
            # Show the "would reformat" lines
            for line in stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
        print(f"⚠️  WARN: {target} needs formatting")
        print(f"   Run: ruff format {target}")
        return 1

    else:  # exit_code >= 2 = actual error
        stderr = result.stderr.strip()
        if stderr:
            print(f"❌ FAIL: ruff error (exit {exit_code})")
            for line in stderr.split('\n'):
                if line.strip():
                    print(f"  {line}")
        else:
            print(f"❌ FAIL: ruff error (exit {exit_code})")
        return 2


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: stage2_8_formatting.py <target>")
        sys.exit(2)

    target = sys.argv[1]
    sys.exit(check_formatting(target))
