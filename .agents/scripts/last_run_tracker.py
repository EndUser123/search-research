#!/usr/bin/env python3
"""Time-interval check for scheduled-via-filesystem tasks.

Replaces Grok scheduled tasks (which auto-expire after 7 days) with
filesystem-based last-run tracking. SessionStart hooks and /maintain
check this before running their scripts.

State file: P:/.artifacts/.last-runs.json
{
    "daily_rotation": "2026-08-13T17:00:00+00:00",
    "dream": "2026-08-10T10:00:00+00:00",
    "scanner_audit": "2026-07-15T10:00:00+00:00"
}

Usage:
    # Check if a task should run (returns JSON with should_run: true/false)
    python last_run_tracker.py check --task daily_rotation --interval-hours 24

    # Mark a task as run now
    python last_run_tracker.py mark --task daily_rotation

    # Get all last-run timestamps
    python last_run_tracker.py list
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

STATE_PATH = Path("P:/.artifacts/.last-runs.json")


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _parse_ts(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def should_run(task: str, interval_hours: float) -> dict:
    """Check if a task should run based on elapsed time since last run."""
    state = _load_state()
    last_run_str = state.get(task)
    last_run = _parse_ts(last_run_str) if last_run_str else None

    now = datetime.now(timezone.utc)

    if last_run is None:
        return {
            "task": task,
            "should_run": True,
            "reason": "never_run",
            "last_run": None,
            "hours_since": None,
            "interval_hours": interval_hours,
        }

    elapsed = (now - last_run).total_seconds() / 3600
    return {
        "task": task,
        "should_run": elapsed >= interval_hours,
        "reason": "interval_elapsed" if elapsed >= interval_hours else "too_recent",
        "last_run": last_run.isoformat(),
        "hours_since": round(elapsed, 1),
        "interval_hours": interval_hours,
    }


def mark_run(task: str) -> dict:
    """Mark a task as having run now."""
    state = _load_state()
    now_iso = datetime.now(timezone.utc).isoformat()
    state[task] = now_iso
    _save_state(state)
    return {"task": task, "marked_at": now_iso}


def list_runs() -> dict:
    """List all last-run timestamps."""
    return _load_state()


def main() -> None:
    parser = argparse.ArgumentParser(description="Time-interval check for filesystem-scheduled tasks")
    sub = parser.add_subparsers(dest="command")

    p_check = sub.add_parser("check", help="Check if a task should run")
    p_check.add_argument("--task", required=True)
    p_check.add_argument("--interval-hours", type=float, required=True)

    p_mark = sub.add_parser("mark", help="Mark a task as run now")
    p_mark.add_argument("--task", required=True)

    sub.add_parser("list", help="List all last-run timestamps")

    args = parser.parse_args()

    if args.command == "check":
        result = should_run(args.task, args.interval_hours)
        print(json.dumps(result, indent=2))
    elif args.command == "mark":
        result = mark_run(args.task)
        print(json.dumps(result, indent=2))
    elif args.command == "list":
        result = list_runs()
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
