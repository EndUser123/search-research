#!/usr/bin/env python3
"""Test actual hook execution"""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")

# Create test transcript
transcript = []
transcript.append(json.dumps({
    "type": "user",
    "message": {"content": "test query"}
}))

content = [{
    "type": "text",
    "text": "Found them! 13 tasks already have [yt-fts] in their title."
}]

transcript.append(json.dumps({
    "type": "assistant",
    "message": {"content": content}
}))

temp_file = HOOKS_DIR / "temp_test_exec.jsonl"
temp_file.write_text("\n".join(transcript))

# Run hook
input_data = {
    "transcript_path": str(temp_file),
    "conversation": [],
    "stop_hook_active": False
}

print("Running hook...")
result = subprocess.run(
    [sys.executable, str(HOOKS_DIR / "test_assumption_audit.py")],
    input=json.dumps(input_data).encode(),
    capture_output=True,
    timeout=5
)

print(f"Exit code: {result.returncode}")
print(f"Stdout: {result.stdout.decode()}")
print(f"Stderr: {result.stderr.decode()}")

print("\nExpected: Exit code 2 (BLOCK)")
print(f"Got: Exit code {result.returncode}")

if result.returncode == 2:
    print("✓ BLOCKED correctly")
else:
    print("✗ ALLOWED incorrectly")

# Cleanup
temp_file.unlink()
