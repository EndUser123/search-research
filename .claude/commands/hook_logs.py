#!/usr/bin/env python3
"""View recent hook_errors.jsonl entries.

Usage:
    python hook_logs.py
    python hook_logs.py --limit 20
    python hook_logs.py --help

Arguments:
    --limit N: Show last N entries (default: 10)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(limit: int = 10) -> None:
    """View recent hook error log entries."""
    log_file = Path("P:/.claude/hooks/logs/hook_errors.jsonl")

    if not log_file.exists():
        print("No error logs found")
        print(f"Expected location: {log_file}")
        return

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if not lines:
            print("Log file is empty (no errors recorded)")
            return

        # Show last N entries
        recent_lines = lines[-limit:] if len(lines) > limit else lines

        print(f"Recent {len(recent_lines)} entries (of {len(lines)} total):\n")

        for i, line in enumerate(recent_lines, start=1):
            try:
                record = json.loads(line)
                timestamp = record.get('timestamp', 'N/A')
                hook = record.get('hook', 'N/A')
                message = record.get('message', record.get('error', 'N/A'))

                # Format timestamp if it's a number
                try:
                    from datetime import datetime
                    ts = float(timestamp)
                    dt = datetime.fromtimestamp(ts)
                    timestamp_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    timestamp_str = str(timestamp)

                print(f"[{i}] {timestamp_str}")
                print(f"    Hook: {hook}")
                print(f"    Message: {message}")
                print()
            except json.JSONDecodeError:
                # Skip malformed lines
                print(f"[{i}] Malformed log entry (skipped)")
                print()

    except FileNotFoundError:
        print("No error logs found")
        print(f"Expected location: {log_file}")
    except Exception as e:
        print(f"Error reading log file: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="View recent hook error logs"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of recent entries to show (default: 10)"
    )
    args = parser.parse_args()
    main(args.limit)
