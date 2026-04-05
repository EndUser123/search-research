#!/usr/bin/env python3
"""Test UserPromptSubmit with actual /code skill payload."""

import json
import subprocess
import sys

# Exact payload that /code would send
test_payload = {
    "prompt": "/code implement the plan",
    "command_name": "code",
    "command_arguments": "implement the plan",
    "session": {
        "id": "test-session-123"
    }
}

print("=" * 70)
print("TESTING UserPromptSubmit WITH /code PAYLOAD")
print("=" * 70)
print()
print("Payload:")
print(json.dumps(test_payload, indent=2))
print()

result = subprocess.run(
    [sys.executable, 'UserPromptSubmit.py'],
    input=json.dumps(test_payload).encode(),
    capture_output=True,
    timeout=10
)

print("=" * 70)
print("RESULTS")
print("=" * 70)
print()

print(f"Exit code: {result.returncode}")
print()

stderr_text = result.stderr.decode('utf-8', errors='replace')
stdout_text = result.stdout.decode('utf-8', errors='replace')

if stderr_text:
    print("STDERR:")
    print(stderr_text)
    print()

if stdout_text:
    print("STDOUT (first 1000 chars):")
    print(stdout_text[:1000])
    print()
    print(f"Total STDOUT length: {len(stdout_text)} chars")

print()
print("=" * 70)
print("ANALYSIS")
print("=" * 70)

has_error = False
error_details = []

if result.returncode != 0:
    has_error = True
    error_details.append(f"Exit code {result.returncode}")

if "Error" in stderr_text or "Exception" in stderr_text or "Traceback" in stderr_text:
    has_error = True
    error_details.append("Exception in stderr")

if "ImportError" in stderr_text or "ModuleNotFoundError" in stderr_text:
    has_error = True
    error_details.append("Import error")

if has_error:
    print(f"❌ ERRORS DETECTED: {', '.join(error_details)}")
    sys.exit(1)
else:
    print("✅ NO ERRORS - Hook executed successfully")
    sys.exit(0)
