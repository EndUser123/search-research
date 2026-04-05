#!/usr/bin/env python3
# TEST - This should be blocked by investigation gate
"""Test hook to verify PreToolUse is called for Read operations."""

import json
import sys
from pathlib import Path

LOG_FILE = Path("P:/.claude/state/read_pretooluse_test.log")

try:
    # Read input
    raw_input = sys.stdin.read()
    data = json.loads(raw_input) if raw_input.strip() else {}

    # Log invocation
    with open(LOG_FILE, "a") as f:
        f.write(f"TOOL_NAME: {data.get('tool_name', 'UNKNOWN')}\n")
        f.write(f"INPUT_KEYS: {list(data.keys())}\n")
        f.write(f"TOOL_INPUT_KEYS: {list(data.get('tool_input', {}).keys())}\n")
        f.write(f"FULL_INPUT: {json.dumps(data, indent=2)}\n")
        f.write("-" * 50 + "\n")

    # Approve everything
    print(json.dumps({"decision": "approve", "reason": "test hook"}))
    sys.exit(0)

except Exception as e:
    print(json.dumps({"decision": "approve", "reason": f"error: {e}"}))
    sys.exit(0)
