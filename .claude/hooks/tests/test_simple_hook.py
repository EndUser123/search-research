"""Simple hook test to debug hanging issue."""
import json
import subprocess
import sys

# Hook path
HOOK_PATH = "P:/.claude/hooks/PreToolUse/PreToolUse_skill_pattern_gate.py"

# Test 1: Regular message (should allow)
print("Test 1: Regular message without slash command...")
data = {
    "tool_name": "Bash",
    "input": {"command": "echo test"},
    "user_message": "help me"
}

result = subprocess.run(
    [sys.executable, HOOK_PATH],
    input=json.dumps(data),
    capture_output=True,
    text=True,
    timeout=5,
)

print(f"stdout: {result.stdout}")
print(f"stderr: {result.stderr}")
print(f"returncode: {result.returncode}")
print()

# Test 2: Slash command with Skill tool (should allow)
print("Test 2: Slash command with Skill tool...")
data = {
    "tool_name": "Skill",
    "input": {"skill": "code"},
    "user_message": "/code test"
}

result = subprocess.run(
    [sys.executable, HOOK_PATH],
    input=json.dumps(data),
    capture_output=True,
    text=True,
    timeout=5,
)

print(f"stdout: {result.stdout}")
print(f"stderr: {result.stderr}")
print(f"returncode: {result.returncode}")
print()

print("All tests completed!")
