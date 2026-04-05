#!/usr/bin/env python3
"""Test if PreCompact_handoff_capture works via subprocess."""
import subprocess
import sys

result = subprocess.run(
    [sys.executable, "P:/.claude/hooks/PreCompact_handoff_capture.py"],
    input=b"{}",
    capture_output=True,
    timeout=5,
)


print(f"Exit code: {result.returncode}")
print(f"Stdout:\n{result.stdout.decode()}")
print(f"Stderr:\n{result.stderr.decode()}")
