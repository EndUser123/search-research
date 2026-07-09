#!/usr/bin/env python3
"""
Bulk-update task statuses in the task tracker state files.

Zero tool calls: edits the *_tasks.json files directly. Changes persist
on next TaskList/TaskUpdate call because the PostToolUse tracker reads
the same files.

Usage:
    python batch_update_tasks.py '{"task_ids":["1072","1073"], "status":"pending"}'
    python batch_update_tasks.py @P:/tmp/flip_uncertain.json
    python batch_update_tasks.py --list-completed   # print completed task IDs

Writes go through a file lock to prevent corruption across terminals.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TASK_STATE_DIR = Path("P:/.claude/state/task_tracker")


def load_tasks_file(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def list_completed() -> list[str]:
    """Return all completed task IDs across all terminal state files."""
    ids = []
    for f in TASK_STATE_DIR.glob("*_tasks.json"):
        state = load_tasks_file(f)
        for tid, t in state.get("tasks", {}).items():
            if t.get("status") == "completed":
                ids.append(tid)
    return sorted(ids, key=lambda x: int(x))


def batch_update(task_ids: list[str], status: str) -> dict[str, dict]:
    """Update matching task IDs to `status` across all state files."""
    try:
        from filelock import FileLock
    except ImportError:
        FileLock = None

    id_set = set(task_ids)
    changes: dict[str, dict] = {}
    TASK_STATE_DIR.mkdir(parents=True, exist_ok=True)

    for state_file in TASK_STATE_DIR.glob("*_tasks.json"):
        lock_path = state_file.with_suffix(".lock")

        lock = FileLock(lock_path, timeout=5.0) if FileLock else None
        if lock:
            lock.acquire()
        try:
            state = load_tasks_file(state_file)
            tasks = state.get("tasks", {})
            affected = {tid: tasks[tid].get("status", "?") for tid in id_set if tid in tasks}
            if not affected:
                continue
            terminal = state.get("terminal_id", state_file.stem)
            changes[str(state_file.name)] = dict(affected)
            for tid in affected:
                tasks[tid]["status"] = status
            state["tasks"] = tasks
            state_file.write_text(json.dumps(state, indent=2, default=str), encoding="utf-8")
        finally:
            if lock:
                lock.release()

    return changes


def main():
    if len(sys.argv) < 2:
        print("Usage: batch_update_tasks.py '<json>' | @file | --list-completed", file=sys.stderr)
        sys.exit(2)

    arg = sys.argv[1]

    if arg == "--list-completed":
        ids = list_completed()
        print(json.dumps(ids))
        print(f"\n{len(ids)} completed tasks", file=sys.stderr)
        return

    if arg.startswith("@"):
        input_path = Path(arg[1:])
        payload = json.loads(input_path.read_text(encoding="utf-8"))
    else:
        payload = json.loads(arg)

    task_ids = payload.get("task_ids", [])
    status = payload.get("status", "pending")

    if not task_ids:
        print("Error: task_ids is empty", file=sys.stderr)
        sys.exit(1)

    changes = batch_update(task_ids, status)
    total = sum(len(v) for v in changes.values())
    print(json.dumps({"updated": total, "by_file": changes}, indent=2, default=str))
    print(f"\n{total} tasks updated to '{status}' across {len(changes)} state files", file=sys.stderr)


if __name__ == "__main__":
    main()
