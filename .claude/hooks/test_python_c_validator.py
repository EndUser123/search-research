"""Test script for PreToolUse_python_c_validator.py"""
import json
import subprocess
import sys

# Test valid Python code
test_valid = {"tool_name": "Bash", "tool_input": {"command": 'python -c "print(1 + 1)"'}}

# Test invalid Python code (f-string error)
test_invalid = {"tool_name": "Bash", "tool_input": {"command": 'python -c "print({=*60})"'}}

print("=" * 60)
print("Testing VALID Python code...")
print("=" * 60)
result = subprocess.run(
    [sys.executable, "PreToolUse_python_c_validator.py"],
    input=json.dumps(test_valid),
    capture_output=True,
    text=True,
    cwd="P:/.claude/hooks"
)

print(f"Exit: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")

print("\n" + "=" * 60)
print("Testing INVALID Python code...")
print("=" * 60)
result = subprocess.run(
    [sys.executable, "PreToolUse_python_c_validator.py"],
    input=json.dumps(test_invalid),
    capture_output=True,
    text=True,
    cwd="P:/.claude/hooks"
)

print(f"Exit: {result.returncode}")
print(f"Stdout: {result.stdout}")
print(f"Stderr: {result.stderr}")
