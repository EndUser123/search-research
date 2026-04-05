#!/usr/bin/env python3
"""Find UserPromptSubmit errors in cc_errors.jsonl."""
import json

with open("P:/.claude/hooks/logs/diagnostics/cc_errors.jsonl") as f:
    for line in f:
        try:
            e = json.loads(line.strip())
            if "UserPromptSubmit" in e.get("error_type", ""):
                print(f"{e['timestamp']}: {e['error_type']}")
        except:
            pass
