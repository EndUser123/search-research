#!/usr/bin/env python3
"""Find recent errors in the last 30 minutes."""
import json
from datetime import UTC, datetime, timedelta

cutoff = datetime.now(UTC) - timedelta(minutes=30)

with open("P:/.claude/hooks/logs/diagnostics/cc_errors.jsonl") as f:
    for line in f:
        try:
            e = json.loads(line.strip())
            ts_str = e.get("timestamp", "")
            # Parse ISO timestamp
            if "+" in ts_str:
                ts = datetime.fromisoformat(ts_str)
            elif "Z" in ts_str:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            else:
                continue

            if ts > cutoff:
                print("=" * 60)
                print(f"Time: {ts_str}")
                print(f"Type: {e.get('error_type')}")
                print(f"Msg: {e.get('error_message')}")
                hook = e.get("context", {}).get("hook", "unknown")
                print(f"Hook: {hook}")
                if e.get("stack_trace"):
                    trace = e.get("stack_trace", "")[:400]
                    print(f"Stack: {trace}")
                print()
        except Exception:
            pass
