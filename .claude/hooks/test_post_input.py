#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# Capture input to a file
data = json.load(sys.stdin)
log_file = Path("P:/__csf/data/post_tool_use_input_debug.jsonl")
log_file.parent.mkdir(parents=True, exist_ok=True)

with open(log_file, "a", encoding="utf-8") as f:
    f.write(json.dumps({
        "tool_name": data.get("tool_name"),
        "tool_input": data.get("tool_input"),
        "tool_response": data.get("tool_response"),
        "all_keys": list(data.keys())
    }, indent=2) + "\n")

# Return empty to not interfere
print(json.dumps({"ok": True}))
