#!/usr/bin/env python3
"""why_blocked.py -- show recent Stop/PreToolUse hook blocks with their reasons.

Claude Code's UI shows a bare "Blocked by hook" for an exit-2 block, but the full
reason is ALWAYS captured in diagnostics.db (hooks table, action='block', reason
column). This surfaces it instead of hand-querying SQLite.

Each block is shown with its AGE. This matters because not every "Blocked by hook"
writes a fresh row (some exit paths / gates don't log here). When that happens the
newest row in the table is a STALE prior block, and reading it as "this turn's
block" sends you investigating the wrong thing. Rows older than STALE_THRESHOLD_SEC
are flagged ⚠️ STALE, and a banner fires if the newest block itself is stale.

Usage:
    python why_blocked.py            # last 10 blocks (any event)
    python why_blocked.py 25         # last 25 blocks
    python why_blocked.py --stop     # only Stop-event blocks
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_DB = Path(__file__).resolve().parent.parent / "logs" / "diagnostics" / "diagnostics.db"
# Canonical Stop-block log (flat file, written by __lib/stop_block_log.py from ALL Stop
# block sources, incl. the cc-aca-authority router). diagnostics.db only captures blocks
# logged by the main Stop.py path, so reading the DB alone MISSES authority-router Stop
# blocks (e.g. Stop_lazy_workaround_gate) -> the bare "Blocked by hook" with no findable
# reason. Merge both sinks. See hooks/CLAUDE.md "Observability Storage Policy".
_JSONL = _DB.parent / "stop_blocks.jsonl"

# A block logged for the CURRENT turn is seconds old. Anything older than this is
# from a prior turn and almost certainly NOT the "Blocked by hook" you just saw.
# 120s is a generous ceiling for one interaction (model turn + hook latency).
STALE_THRESHOLD_SEC = 120


def _age(ts: str, now: datetime) -> tuple[float, str]:
    """Return (age_seconds, human_str) for an ISO-8601 timestamp.

    Returns (inf, "unknown age") if the timestamp can't be parsed, so an
    unparseable row is treated as stale rather than masquerading as fresh.
    """
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return float("inf"), "unknown age"
    secs = (now - dt).total_seconds()
    if secs < 0:
        return 0.0, "just now"
    if secs < 90:
        return secs, f"{int(secs)}s ago"
    mins = secs / 60
    if mins < 90:
        return secs, f"{int(mins)}m ago"
    hrs = int(mins // 60)
    rem = int(mins % 60)
    return secs, f"{hrs}h{rem:02d}m ago"


def _read_db_blocks(stop_only: bool) -> list[tuple]:
    """Block rows from diagnostics.db (main Stop.py path + PreToolUse blocks)."""
    if not _DB.exists():
        return []
    where = "action='block'"
    if stop_only:
        where += " AND event_type='Stop'"
    try:
        conn = sqlite3.connect(str(_DB))
        try:
            return [
                (ts, ev, hk, rs)
                for ts, ev, hk, rs in conn.execute(
                    f"""SELECT timestamp, event_type, hook_name, reason
                        FROM hooks WHERE {where}
                        ORDER BY id DESC LIMIT 500"""
                ).fetchall()
            ]
        finally:
            conn.close()
    except sqlite3.Error:
        return []


def _read_jsonl_blocks() -> list[tuple]:
    """Block rows from stop_blocks.jsonl (canonical Stop-block log, all sources)."""
    if not _JSONL.exists():
        return []
    out: list[tuple] = []
    try:
        for line in _JSONL.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            out.append(
                (
                    str(r.get("timestamp", "")),
                    str(r.get("event", "Stop") or "Stop"),
                    str(r.get("gate_name", "") or "(unknown gate)"),
                    str(r.get("reason", "") or ""),
                )
            )
    except OSError:
        return []
    return out


def _load_blocks(stop_only: bool, limit: int) -> list[tuple]:
    """Merge both block sinks, dedup, sort newest-first, apply limit."""
    merged = _read_db_blocks(stop_only) + _read_jsonl_blocks()
    seen: set = set()
    deduped: list[tuple] = []
    for ts, ev, hk, rs in merged:
        # A block can be logged to both sinks; key on time + hook + reason head.
        key = (ts, hk, (rs or "")[:80])
        if key in seen:
            continue
        seen.add(key)
        deduped.append((ts, ev, hk, rs))
    # ISO-8601 UTC timestamps sort lexicographically by time.
    deduped.sort(key=lambda r: r[0], reverse=True)
    return deduped[:limit]


def main() -> int:
    args = list(sys.argv[1:])
    stop_only = "--stop" in args
    limit = next((int(a) for a in args if a.isdigit()), 10)

    if not _DB.exists() and not _JSONL.exists():
        print(f"No block logs found ({_DB} / {_JSONL})", file=sys.stderr)
        return 1

    rows = _load_blocks(stop_only, limit)
    if not rows:
        print("No block events found.")
        return 0

    now = datetime.now(timezone.utc)

    # Banner: if the most-recent block is itself stale, the current "Blocked by
    # hook" (if any) likely wrote no row here -- don't chase this old reason.
    newest_age, newest_human = _age(rows[0][0], now)
    if newest_age > STALE_THRESHOLD_SEC:
        print(
            f"⚠️  Newest block is STALE ({newest_human}). If you just saw "
            f"'Blocked by hook', it likely wrote NO row here (different gate or "
            f"exit path) -- the entries below are from prior turns.\n"
        )

    for ts, event, hook, reason in rows:
        lines = (reason or "(no reason recorded)").strip().splitlines()
        first = lines[0] if lines else "(empty)"
        age_secs, age_human = _age(ts, now)
        stale = " ⚠️ STALE" if age_secs > STALE_THRESHOLD_SEC else ""
        print(f"[{ts}] ({age_human}){stale} {event} :: {hook}")
        print(f"    {first}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
