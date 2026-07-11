#!/usr/bin/env python3
"""
SessionStart hook: pre-migrate state files from terminal_id-only to
{terminal}_{session} naming. Runs BEFORE any Stop evaluator, so the
evaluator never sees old-format contamination files.

Strategy: for each JSONL state file with a single terminal_id segment
(pre-migration naming), rewrite into {terminal}_{session} and deprecate
the original. This is idempotent — files already in new format are skipped.

Zero output on success. Never blocks.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOKS_DIR / ".state"
DIAG_DIR = HOOKS_DIR / "logs" / "diagnostics"


def _safe(name: str, maxlen: int = 48) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", name)[:maxlen]


def _extract_session(line: str) -> str | None:
    try:
        rec = json.loads(line)
        if isinstance(rec, dict):
            return str(rec.get("session_id") or rec.get("writer_session") or "")
    except Exception:
        return None
    return None


def _migrate_file(path: Path) -> bool:
    """Migrate one state file. Returns True if migrations happened."""
    if not path.is_file() or path.stat().st_size == 0:
        return False
    if ".deprecated" in path.name:
        return False

    stem = path.stem

    # Check if already in new format (contains _<something>_<something> after prefix)
    # Old format: prefix_{tid}.jsonl (single segment after prefix)
    # New format: prefix_{tid}_{sid}.jsonl (double segment)
    # Detect by counting segments after prefix: if the name has pattern
    # prefix_X_Y.jsonl where both X and Y exist, it's new format.
    parts = stem.split("_")
    if len(parts) >= 3:
        # Could be prefix_tid_sid format or something else
        # Check: if the last segment is not "shared" and the file content
        # has session_ids, assume it's new format
        pass  # Don't skip — check content too

    # Group lines by session
    sessions: dict[str, list[str]] = {}
    session_count = 0
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                ls = line.strip()
                if not ls:
                    continue
                sid = _extract_session(ls) or "nosession"
                sessions.setdefault(sid, []).append(ls)
                session_count += 1
    except (OSError, PermissionError):
        return False

    if not sessions:
        return False

    # If 0 or 1 sessions found with session_id field, no contamination
    sid_found = sum(1 for s in sessions if s != "nosession")
    if sid_found <= 1 and session_count <= 1:
        return False

    # If already has session_id on all lines with a consistent single value,
    # this is a new-format file that was written by migrated code
    if sid_found == 1 and len(sessions) == 1:
        # Single-session file with session_id — already migrated, skip
        # But rename if it matches old format pattern
        only_sid = next(iter(sessions.keys()))
        if only_sid != "nosession":
            return False  # Already in new format — leave it

    # Migrate: write each session group to {stem}_{sid}.jsonl
    total_lines = 0
    for sid, lines in sessions.items():
        safe_sid = _safe(sid)
        new_path = path.parent / f"{stem}_{safe_sid}.jsonl"
        try:
            with open(new_path, "a", encoding="utf-8") as f:
                for ln in lines:
                    f.write(ln + "\n")
                    total_lines += 1
        except (OSError, PermissionError):
            pass

    # Rename original to .deprecated
    try:
        path.rename(path.with_name(path.name + ".deprecated"))
    except (OSError, PermissionError):
        pass

    # Log migration
    try:
        DIAG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = DIAG_DIR / "state_migration.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "event": "start_migrated",
                "file": str(path),
                "lines": total_lines,
                "sessions": list(sessions.keys()),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return True


def main() -> int:
    """Migrate all state files before Stop evaluator fires."""
    # Glob all JSONL files in .state (direct children only)
    for fpath in sorted(STATE_DIR.glob("*.jsonl")):
        try:
            _migrate_file(fpath)
        except Exception:
            continue

    # Also check logs/diagnostics
    for fpath in sorted(DIAG_DIR.glob("*.jsonl")):
        try:
            _migrate_file(fpath)
        except Exception:
            continue

    return 0  # Never block


if __name__ == "__main__":
    sys.exit(main())
