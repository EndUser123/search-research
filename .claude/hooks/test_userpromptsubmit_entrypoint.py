#!/usr/bin/env python3
"""Test UserPromptSubmit.py entrypoint"""
import json
import subprocess
import sys

test_data = {
    "prompt": "what the fuck? stop being stupid."
}

result = subprocess.run(
    [sys.executable, "P:/.claude/hooks/UserPromptSubmit.py"],
    input=json.dumps(test_data),
    capture_output=True,
    text=True,
    timeout=5
)

print(f"Exit code: {result.returncode}")
print(f"Stdout length: {len(result.stdout)}")
if result.stdout:
    print(f"Stdout preview:\n{result.stdout[:300]}")
print(f"Stderr: {result.stderr[:200] if result.stderr else 'None'}")

# Check for concern detection
if "CONCERN" in result.stdout or "frustration" in result.stdout:
    print("\n✅ SUCCESS - Concern detection fired")
else:
    print("\n❌ FAIL - No concern detection in output")
