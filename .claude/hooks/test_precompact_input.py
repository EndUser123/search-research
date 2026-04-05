#!/usr/bin/env python3
"""
Diagnostic script to see what PreCompact hook actually receives.
Writes output to a log file for later inspection.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "projects" / "P--" / "precompact_diagnostic.log"

# Read stdin (same as PreCompact handoff capture hook)
raw_input = sys.stdin.read().strip()
if not raw_input:
    sys.exit(0)

try:
    # Remove BOM if present
    raw_input = raw_input.lstrip('\ufeff')
    data = json.loads(raw_input)
except json.JSONDecodeError:
    sys.exit(0)

# Build diagnostic output
output_lines = [
    "=" * 60,
    f"PreCompact Hook Input Diagnostic - {datetime.now().isoformat()}",
    "=" * 60,
    json.dumps(data, indent=2),
    "=" * 60,
]

# Check for session-related keys
session_keys = [
    "session.id",
    "session.session_id",
    "session.sessionId",
    "session_id",
    "sessionId",
]

output_lines.append("\nSession-related fields found:")
for key in session_keys:
    if "." in key:
        parts = key.split(".")
        obj = data
        found = True
        for part in parts:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                found = False
                break
        if found:
            output_lines.append(f"  ✓ {key} = {obj}")
    else:
        if key in data:
            output_lines.append(f"  ✓ {key} = {data[key]}")

# Write to log file
with open(LOG_FILE, "a", encoding="utf-8") as f:
    f.write("\n".join(output_lines) + "\n\n")

sys.exit(0)
