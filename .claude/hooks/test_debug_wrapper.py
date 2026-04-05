#!/usr/bin/env python3
"""Debug wrapper to trace what PreToolUse_python_c_validator.py receives."""

import json
import sys

# Capture stdin
stdin_raw = sys.stdin.read()
print(f"[DEBUG] Raw stdin length: {len(stdin_raw)}", file=sys.stderr)
print(f"[DEBUG] Raw stdin content: {repr(stdin_raw)}", file=sys.stderr)

# Try to parse JSON
try:
    data = json.loads(stdin_raw)
    print("[DEBUG] JSON parsed successfully", file=sys.stderr)
    print(f"[DEBUG] tool_name: {data.get('tool_name')}", file=sys.stderr)
    print(f"[DEBUG] command: {data.get('tool_input', {}).get('command')}", file=sys.stderr)
except json.JSONDecodeError as e:
    print(f"[DEBUG] JSON decode error: {e}", file=sys.stderr)
    print(f"[DEBUG] Error at position {e.pos}", file=sys.stderr)
    print(f"[DEBUG] Context: {repr(stdin_raw[max(0, e.pos-20):e.pos+20])}", file=sys.stderr)
    sys.exit(1)

# Now call the actual hook
import PreToolUse_python_c_validator as validator

validator.main()
