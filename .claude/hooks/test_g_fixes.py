#!/usr/bin/env python3
"""Test if empirical_claims_gate now blocks with exit code 2"""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")

# Create test case: Claim without tools
test_input = {
    "response": "The system has 150 active users right now.",
    "tools_used": [],  # No verification tools
    "transcript_path": "fake.jsonl"
}

print("Testing empirical_claims_gate.py...")
print("Input: Claim without tools\n")

result = subprocess.run(
    [sys.executable, str(HOOKS_DIR / "empirical_claims_gate.py")],
    input=json.dumps(test_input).encode(),
    capture_output=True,
    timeout=5
)

print(f"Exit code: {result.returncode}")
print(f"Stderr: {result.stderr.decode()[:200]}")
print()

if result.returncode == 2:
    print("✓ SUCCESS: Hook blocks with exit code 2")
elif result.returncode == 0:
    stdout = result.stdout.decode()
    if "block" in stdout.lower():
        print("✗ BROKEN: Exit code 0 but JSON says block (router will miss this)")
    else:
        print("? UNEXPECTED: Exit code 0 and no block in output")
else:
    print(f"? UNEXPECTED: Exit code {result.returncode}")
