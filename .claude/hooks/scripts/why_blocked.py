#!/usr/bin/env python3
"""why_blocked.py -- show recent Stop/PreToolUse hook blocks with their reasons.

Claude Code's UI shows a bare "Blocked by hook" for an exit-2 block, but the full
reason is ALWAYS captured in diagnostics.db (hooks table, action='block', reason
column). This surfaces it instead of hand-querying SQLite.

Usage:
    python why_blocked.py            # last 10 blocks (any event)
    python why_blocked.py 25         # last 25 blocks
    python why_blocked.py --stop     # only Stop-event blocks
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

_DB = Path(__file__).resolve().parent.parent / "logs" / "diagnostics" / "diagnostics.db"


def main() -> int:
    args = list(sys.argv[1:])
    stop_only = "--stop" in args
    limit = next((int(a) for a in args if a.isdigit()), 10)

    if not _DB.exists():
        print(f"diagnostics.db not found at {_DB}", file=sys.stderr)
        return 1

    where = "action='block'"
    if stop_only:
        where += " AND event_type='Stop'"

    conn = sqlite3.connect(str(_DB))
    rows = conn.execute(
        f"""SELECT timestamp, event_type, hook_name, reason
            FROM hooks WHERE {where}
            ORDER BY id DESC LIMIT ?""",
        (limit,),
    ).fetchall()

    if not rows:
        print("No block events found.")
        return 0

    for ts, event, hook, reason in rows:
        lines = (reason or "(no reason recorded)").strip().splitlines()
        first = lines[0] if lines else "(empty)"
        print(f"[{ts}] {event} :: {hook}")
        print(f"    {first}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
