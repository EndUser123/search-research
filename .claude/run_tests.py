#!/usr/bin/env python
"""Run pytest and save output to file."""

import os
import subprocess
import sys

os.chdir(r"P:\packages\intelligence-stream")

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "--timeout=60", "-v"],
    capture_output=True,
    text=True,
    timeout=300,
)

with open(r"P:\.claude\test_results.txt", "w", encoding="utf-8") as f:
    f.write(result.stdout)
    f.write("\n=== STDERR ===\n")
    f.write(result.stderr)

print(f"Exit code: {result.returncode}", flush=True)
print("Results written to P:\\.claude\\test_results.txt", flush=True)
