"""Show recent hook errors from diagnostic logs."""

import json
from pathlib import Path

LOG_FILE = Path("P:/.claude/hooks/logs/diagnostics/cc_errors.jsonl")

if not LOG_FILE.exists():
    print("No error log file found")
    exit(0)

with open(LOG_FILE) as f:
    lines = f.readlines()

print(f"Total error entries: {len(lines)}")
print("\nLast 20 errors:")
print("-" * 80)

for line in lines[-20:]:
    if not line.strip():
        continue
    try:
        e = json.loads(line)
        ts = e.get("timestamp", "?")[:19]
        etype = e.get("error_type", "?")[:35]
        msg = str(e.get("error_message", "?"))[:60].replace("\n", " ")
        print(f"{ts} | {etype:35} | {msg}")
    except Exception as ex:
        print(f"Parse error: {ex}")
