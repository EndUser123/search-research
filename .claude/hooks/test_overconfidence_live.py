#!/usr/bin/env python3
"""Test if overconfidence detector actually fires"""
import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# Test response with overconfidence patterns
test_response = """
This explains why the test failed - the system is broken.
The root cause is the configuration file.
"""

test_input = {
    "response": test_response
}

hook_path = HOOKS_DIR / "StopHook_overconfidence_detector.py"

result = subprocess.run(
    [sys.executable, str(hook_path)],
    input=json.dumps(test_input),
    capture_output=True,
    text=True,
    timeout=5
)

print(f"Exit code: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")

# Check if it detected anything
try:
    output = json.loads(result.stdout)
    if "hookSpecificOutput" in output:
        context = output["hookSpecificOutput"].get("additionalContext", "")
        if "OVERCONFIDENCE CHECK" in context:
            print("\n✅ Hook is WORKING - detected overconfidence")
        else:
            print("\n❌ Hook returned output but no overconfidence detection")
    elif output == {}:
        print("\n❌ Hook returned empty - did NOT detect overconfidence")
    else:
        print(f"\n❓ Unexpected output: {output}")
except json.JSONDecodeError:
    print("\n❌ Hook did not return valid JSON")
