#!/usr/bin/env python3
import json
import sys

# Read actual PostToolUse input
data = json.load(sys.stdin)

# Write to a file we can read
with open(r"P:\.claude\logs\real_post_input.json", "w") as f:
    json.dump(data, f, indent=2)

# Return empty
print(json.dumps({"ok": True}))
