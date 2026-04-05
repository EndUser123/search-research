#!/usr/bin/env python3
"""Test if UserPromptSubmit_router is being called"""
import sys
from pathlib import Path

# Add hooks to path
sys.path.insert(0, str(Path("P:/.claude/hooks")))

# Import the router

# Simulate stdin that Claude Code would send
test_data = {
    "prompt": "what the fuck? stop being stupid.",
    "sessionId": "test-session-123"
}

import json
import subprocess

# Call the router as Claude Code would
result = subprocess.run(
    [sys.executable, "P:/.claude/hooks/UserPromptSubmit_router.py"],
    input=json.dumps(test_data),
    capture_output=True,
    text=True,
    timeout=5
)

print(f"Exit code: {result.returncode}")
print(f"Stdout length: {len(result.stdout)}")
print(f"Stdout preview: {result.stdout[:500]}")
print(f"Stderr: {result.stderr}")

# Check if concern detection fired
if "CONCERN DETECTED" in result.stdout or "frustration" in result.stdout:
    print("\n✅ Concern detection FIRED in router")
else:
    print("\n❌ Concern detection did NOT fire in router")
