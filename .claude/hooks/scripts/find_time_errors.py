#!/usr/bin/env python3
"""Find all errors around specific time."""
import json
import sys

target_time = sys.argv[1] if len(sys.argv) > 1 else "05:20"

with open("P:/.claude/hooks/logs/diagnostics/cc_errors.jsonl") as f:
    for line in f:
        try:
            e = json.loads(line.strip())
            ts = e.get("timestamp", "")
            if target_time in ts:
                err_type = e.get("error_type", "unknown")
                print(f"{ts[-15:-6]}: {err_type}")
        except:
            pass
