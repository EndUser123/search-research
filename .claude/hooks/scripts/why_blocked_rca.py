#!/usr/bin/env python3
"""why_blocked_rca.py -- multi-source RCA for Stop/PreToolUse hook blocks.

Joins three diagnostic sources for a given session or set of sessions:
  1. stop_blocks.jsonl (canonical Stop-block flat file)
  2. diagnostics.db (hooks + importer_diagnostics tables)
  3. hook_runner_stderr.jsonl (stderr capture)

Usage:
    python why_blocked_rca.py                     # last 5 sessions
    python why_blocked_rca.py --last N             # N most recent transcript sessions
    python why_blocked_rca.py --session <uuid>     # single session
"""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_HOOKS = Path(__file__).resolve().parent.parent
_DIAG = _HOOKS / "logs" / "diagnostics"
_STOP_BLOCKS = _DIAG / "stop_blocks.jsonl"
_DB_PATH = _DIAG / "diagnostics.db"
_HOOK_STDERR = _DIAG / "hook_runner_stderr.jsonl"
_PROJECT_DIR = Path("C:/Users/brsth/.claude/projects/P--/")


def _utc(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (assume UTC if naive)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _parse_ts(ts: str) -> datetime | None:
    """Parse an ISO-8601 timestamp string to UTC-aware datetime."""
    try:
        return _utc(datetime.fromisoformat(ts))
    except (ValueError, TypeError):
        return None


# ── Source readers ──────────────────────────────────────────────


def read_stop_blocks(session_ids: set[str] | None = None) -> list[dict]:
    """Read stop_blocks.jsonl, optionally filtered by session_id."""
    if not _STOP_BLOCKS.exists():
        raise FileNotFoundError(f"stop_blocks.jsonl not found at {_STOP_BLOCKS}")
    rows: list[dict] = []
    for line in _STOP_BLOCKS.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = str(r.get("session_id", ""))
        if session_ids is not None and sid not in session_ids:
            continue
        rows.append({
            "source": "stop_blocks.jsonl",
            "timestamp": _parse_ts(str(r.get("timestamp", ""))),
            "ts_raw": str(r.get("timestamp", "")),
            "gate_name": str(r.get("gate_name", "")),
            "reason": str(r.get("reason", "")),
            "session_id": sid,
            "terminal_id": str(r.get("terminal_id", "")),
        })
    return rows


def read_db_blocks(session_ids: set[str] | None = None) -> list[dict]:
    """Read block rows from diagnostics.db hooks table (all actions, not just blocks)."""
    if not _DB_PATH.exists():
        raise FileNotFoundError(f"diagnostics.db not found at {_DB_PATH}")
    conn = sqlite3.connect(f"file:{_DB_PATH}?mode=ro", uri=True)
    try:
        rows: list[dict] = []
        cur = conn.cursor()
        query = (
            "SELECT timestamp, event, hook_name, reason, action, session_id, terminal_id "
            "FROM hooks"
        )
        params: list[str] = []
        if session_ids is not None:
            placeholders = ",".join("?" for _ in session_ids)
            query += f" WHERE session_id IN ({placeholders})"
            params = list(session_ids)
        query += " ORDER BY id DESC"
        for ts, ev, hk, reason, action, sid, tid in cur.execute(query, params).fetchall():
            rows.append({
                "source": "diagnostics.db (hooks)",
                "timestamp": _parse_ts(str(ts)) if ts else None,
                "ts_raw": str(ts) if ts else "",
                "gate_name": str(hk) if hk else "",
                "reason": str(reason) if reason else "",
                "action": str(action) if action else "",
                "session_id": str(sid) if sid else "",
                "terminal_id": str(tid) if tid else "",
                "event": str(ev) if ev else "",
            })
        return rows
    finally:
        conn.close()


def read_db_importer(session_ids: set[str] | None = None) -> list[dict]:
    """Read importer_diagnostics rows from diagnostics.db."""
    conn = sqlite3.connect(f"file:{_DB_PATH}?mode=ro", uri=True)
    try:
        rows: list[dict] = []
        cur = conn.cursor()
        query = (
            "SELECT timestamp, hook_name, phase, session_id, terminal_id, "
            "       tool_name, error_text "
            "FROM importer_diagnostics"
        )
        params: list[str] = []
        if session_ids is not None:
            placeholders = ",".join("?" for _ in session_ids)
            query += f" WHERE session_id IN ({placeholders})"
            params = list(session_ids)
        query += " ORDER BY id DESC"
        for ts, hk, phase, sid, tid, tool, err in cur.execute(query, params).fetchall():
            rows.append({
                "source": "diagnostics.db (importer_diagnostics)",
                "timestamp": _parse_ts(str(ts)) if ts else None,
                "ts_raw": str(ts) if ts else "",
                "gate_name": str(hk) if hk else "",
                "phase": str(phase) if phase else "",
                "reason": str(err) if err else "",
                "session_id": str(sid) if sid else "",
                "terminal_id": str(tid) if tid else "",
                "tool_name": str(tool) if tool else "",
            })
        return rows
    finally:
        conn.close()


def read_stderr(session_ids: set[str] | None = None) -> list[dict]:
    """Read hook_runner_stderr.jsonl, optionally filtered by session_id."""
    if not _HOOK_STDERR.exists():
        raise FileNotFoundError(f"hook_runner_stderr.jsonl not found at {_HOOK_STDERR}")
    rows: list[dict] = []
    for line in _HOOK_STDERR.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = str(r.get("session_id", ""))
        if session_ids is not None and sid not in session_ids:
            continue
        stderr_text = str(r.get("stderr", ""))
        rows.append({
            "source": "hook_runner_stderr.jsonl",
            "timestamp": _parse_ts(str(r.get("ts", ""))),
            "ts_raw": str(r.get("ts", "")),
            "gate_name": str(r.get("hook", "")),
            "reason": stderr_text,
            "session_id": sid,
            "terminal_id": str(r.get("terminal_id", "")),
            "tool_name": str(r.get("tool_name", "")),
            "stderr_len": r.get("stderr_len", 0),
            "exit_code": r.get("exit_code", ""),
        })
    return rows


# ── Session ID resolution ───────────────────────────────────────


def resolve_session_ids(last_n: int) -> list[str]:
    """Return the session_id stems of the N most recently modified transcript .jsonl files."""
    if not _PROJECT_DIR.is_dir():
        raise FileNotFoundError(f"Transcript directory not found: {_PROJECT_DIR}")
    files = sorted(
        _PROJECT_DIR.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    return [f.stem for f in files[:last_n]]


# ── Report ──────────────────────────────────────────────────────


def _fmt(val: object, default: str = "-") -> str:
    if val is None or (isinstance(val, str) and not val.strip()):
        return default
    return str(val)


def _read_with_errors(
    label: str,
    reader_fn,
    errors: list[str],
    session_ids: set[str] | None = None,
) -> list[dict]:
    """Try to read a source; report UNAVAILABLE on failure."""
    try:
        return reader_fn(session_ids)
    except Exception as e:
        errors.append(f"SOURCE UNAVAILABLE: {label}: {e}")
        return []


def main() -> int:
    args = list(sys.argv[1:])

    session_ids_override: set[str] | None = None
    sid_label = ""

    if "--session" in args:
        idx = args.index("--session")
        if idx + 1 < len(args) and args[idx + 1]:
            session_ids_override = {args[idx + 1]}
            sid_label = f"session={args[idx + 1]}"
    elif "--last" in args:
        idx = args.index("--last")
        last_n = 5
        if idx + 1 < len(args) and args[idx + 1].isdigit():
            last_n = int(args[idx + 1])
        try:
            session_ids = resolve_session_ids(last_n)
            session_ids_override = set(session_ids)
            sid_label = f"last {last_n} sessions"
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1
    else:
        # Default: last 5 sessions
        try:
            session_ids = resolve_session_ids(5)
            session_ids_override = set(session_ids)
            sid_label = "last 5 sessions"
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 1

    errors: list[str] = []

    rows: list[dict] = []
    rows.extend(
        _read_with_errors("stop_blocks.jsonl", read_stop_blocks, errors, session_ids_override)
    )
    rows.extend(
        _read_with_errors("diagnostics.db (hooks)", read_db_blocks, errors, session_ids_override)
    )
    rows.extend(
        _read_with_errors(
            "diagnostics.db (importer_diagnostics)", read_db_importer, errors, session_ids_override
        )
    )
    rows.extend(
        _read_with_errors("hook_runner_stderr.jsonl", read_stderr, errors, session_ids_override)
    )

    for e in errors:
        print(e)
    if errors:
        print()

    if not rows:
        print("No block events found for the given session(s).")
        return 0

    # Sort by timestamp descending (None timestamps at end)
    rows.sort(
        key=lambda r: (r["timestamp"] or datetime.min.replace(tzinfo=timezone.utc)),
        reverse=True,
    )

    print(f"=== Stop Block RCA Report ({sid_label}) ===\n")

    for row in rows:
        ts = _fmt(row.get("ts_raw", ""))
        source = row.get("source", "?")
        gate = row.get("gate_name", "")

        print(f"[{ts}] ({source})")
        print(f"  Gate:     {gate}")

        if row.get("action"):
            print(f"  Action:   {row['action']}")
        if row.get("phase"):
            print(f"  Phase:    {row['phase']}")
        if row.get("event"):
            print(f"  Event:    {row['event']}")
        if row.get("tool_name"):
            print(f"  Tool:     {row['tool_name']}")
        if "stderr_len" in row:
            print(f"  Stderr:   {row['stderr_len']} bytes")
        if row.get("exit_code", "") != "":
            print(f"  Exit:     {row['exit_code']}")

        print(f"  Session:  {_fmt(row.get('session_id', ''))}")
        print(f"  Terminal: {_fmt(row.get('terminal_id', ''))}")

        reason = row.get("reason", "")
        if reason:
            rlines = reason.strip().splitlines()
            if len(rlines) > 3:
                reason_display = "\n".join(rlines[:3]) + f"\n    ... ({len(rlines) - 3} more lines)"
            else:
                reason_display = "\n".join(rlines) if rlines else "-"
            print(f"  Reason:\n    {reason_display}")
        else:
            print("  Reason:   -")
        print()

    print(f"Total entries: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
