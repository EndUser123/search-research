#!/usr/bin/env python3
"""Find UserPromptSubmit errors."""
import json

with open("P:/.claude/hooks/logs/diagnostics/cc_errors.jsonl") as f:
    for i, line in enumerate(f, 1):
        if "UserPromptSubmit" in line:
            e = json.loads(line.strip())
            ts = e.get("timestamp", "")
            err_type = e.get("error_type", "")
            msg = e.get("error_message", "")[:80]
            print(f"Line {i}: {ts}")
            print(f"  Type: {err_type}")
            print(f"  Msg: {msg}")
            print()
