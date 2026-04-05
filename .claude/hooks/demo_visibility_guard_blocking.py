#!/usr/bin/env python3
"""
Demonstration: Repository Visibility Guard blocking through PreToolUse router

This shows what happens when you try to run a dangerous command through
the actual PreToolUse hook system (the way it works in real usage).
"""

import json
import subprocess

print("="*70)
print("DEMONSTRATION: Repository Visibility Guard in Action")
print("="*70)

print("\nScenario: Attempting to make P:\\ drive repository public")
print("-" * 70)

# Create a test input that simulates what Claude Code sends
test_input = {
    "tool_name": "Bash",
    "tool_input": {
        "command": "gh repo edit EndUser123/P --visibility public"
    }
}

print(f"Command: {test_input['tool_input']['command']}")
print("Current directory: P:\\")
print("\nSending to PreToolUse router...")

# Run through the actual PreToolUse router
result = subprocess.run(
    ["python", "P:/.claude/hooks/PreToolUse.py"],
    input=json.dumps(test_input),
    capture_output=True,
    text=True,
    timeout=15,
    cwd="P:\\"
)

print(f"\nExit code: {result.returncode}")
print(f"Stdout: {result.stdout if result.stdout else '(empty)'}")

if result.returncode == 2:
    try:
        output = json.loads(result.stdout)
        print("\n" + "="*70)
        print("RESULT: COMMAND BLOCKED ✓")
        print("="*70)
        print("\nThe hook successfully prevented the repository from being made public!")
        print("\nBlocking reason:")
        print(output.get("reason", "No reason provided"))
        print("\n" + "="*70)
        print(r"PROTECTION ACTIVE: Your P:\ drive repos are safe!")
        print("="*70)
    except json.JSONDecodeError:
        print("\nBlocked (non-JSON output)")
else:
    print("\n⚠️ Command was allowed (this shouldn't happen for P:\\ drive)")
    if result.stderr:
        print(f"Stderr: {result.stderr}")
