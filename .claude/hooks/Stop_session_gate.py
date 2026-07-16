#!/usr/bin/env python3
"""
Stop hook: cross-session contamination gate (ADVISORY + migration — reports, never blocks).

Migration: terminal_id-only state files are read, their content is appended to
session-qualified files ({terminal}_{session}.jsonl), and the old file is renamed
with a .deprecated suffix so new writes never hit it. Future sessions read only
from session-qualified files.

Detection: after migration, scans still find contamination (unlikely) and report.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
DIAG_DIR = HOOKS_DIR / "logs" / "diagnostics"
STATE_GLOBS = [
    HOOKS_DIR / ".state" / "*.jsonl",
    HOOKS_DIR / "logs" / "diagnostics" / "*.jsonl",
]


def _get_current_ids() -> tuple[str, str]:
    """Get session_id and terminal_id from environment."""
    sid = os.environ.get("CLAUDE_SESSION_ID") or "nosession"
    tid = os.environ.get("WT_SESSION") or os.environ.get("CLAUDE_TERMINAL_ID") or "shared"
    return sid, tid


def _safe(name: str, maxlen: int = 48) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", name)[:maxlen]


def _count_lines(path: Path) -> int:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f if _.strip())
    except Exception:
        return 0


def _extract_session_from_line(line: str) -> str | None:
    """Extract session_id or writer_session from a JSONL line."""
    try:
        rec = json.loads(line)
        if isinstance(rec, dict):
            return str(rec.get("session_id") or rec.get("writer_session") or "")
    except Exception:
        pass
    return None


def _migrate_state_files(session_id: str, terminal_id: str) -> list[dict]:
    """Migrate all state files from old format ({terminal}.jsonl) to new
    format ({terminal}_{session}.jsonl).

    Strategy: for each old-format file that matches the current terminal_id:
      1. Read all lines.
      2. For lines that contain a session_id field, route to
         {terminal}_{extracted_sid}.jsonl. For lines that DON'T have a
         session_id (pre-migration data), attach the current session_id.
      3. Rename old file to .deprecated so no new writer touches it.
      4. Append data to the correct new-format file(s).

    Never deletes data. Never fails on permissions.
    Returns list of migration actions taken.
    """
    actions = []
    safe_tid = _safe(terminal_id)

    for pattern in STATE_GLOBS:
        pat = Path(pattern)
        for fpath in sorted(pat.parent.glob(pat.name)):
            # Skip files that already have a session suffix (_<something> after tid)
            stem = fpath.stem  # e.g. "negation_hits_d54ddaf8-c012"
            if "_" + safe_tid != "_" + stem and safe_tid in stem:
                # Check if already in new format (has _<session> after tid)
                # Old format: negation_hits_{tid}.jsonl  → one suffix after tid
                # New format: negation_hits_{tid}_{sid}.jsonl → two suffixes
                parts = stem.split(safe_tid)
                if len(parts) >= 2 and parts[1].startswith("_"):
                    remain = parts[1][1:]  # after tid_
                    if remain and remain != "shared":
                        continue  # already in new format

            if safe_tid not in fpath.name:
                continue
            if not fpath.is_file() or fpath.stat().st_size == 0:
                continue
            if fpath.suffix == ".deprecated" or ".deprecated" in fpath.name:
                continue

            # Read all content, grouping by session
            sessions_data: dict[str, list[str]] = {}
            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line_s = line.strip()
                        if not line_s:
                            continue
                        sid = _extract_session_from_line(line_s) or session_id
                        sessions_data.setdefault(sid, []).append(line_s)
            except (OSError, PermissionError):
                continue

            # Write to new session-qualified files
            total_lines = 0
            for sid, lines in sessions_data.items():
                safe_sid = _safe(sid)
                new_name = fpath.parent / f"{stem}_{safe_sid}.jsonl"
                try:
                    with open(new_name, "a", encoding="utf-8") as f:
                        for ln in lines:
                            f.write(ln + "\n")
                        total_lines += len(lines)
                except (OSError, PermissionError):
                    continue

            # Rename old file to .deprecated
            deprecated = fpath.with_name(fpath.name + ".deprecated")
            try:
                fpath.rename(deprecated)
            except (OSError, PermissionError):
                pass  # Best effort; file will be migrated again next time

            actions.append({
                "old_file": str(fpath),
                "deprecated_to": str(deprecated),
                "lines_migrated": total_lines,
                "session_targets": list(sessions_data.keys()),
            })

    return actions


def _scan_for_contamination(terminal_id: str) -> list[dict]:
    """Scan for remaining non-migrated old-format files (should be rare
    after migration runs)."""
    findings = []
    if not terminal_id:
        return findings
    safe_tid = _safe(terminal_id)

    for pattern in STATE_GLOBS:
        pat = Path(pattern)
        for fpath in sorted(pat.parent.glob(pat.name)):
            if safe_tid not in fpath.name:
                continue
            if ".deprecated" in fpath.name:
                continue
            if not fpath.is_file() or fpath.stat().st_size == 0:
                continue

            sessions_seen: set[str] = set()
            try:
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line_s = line.strip()
                        if not line_s:
                            continue
                        sid = _extract_session_from_line(line_s)
                        if sid:
                            sessions_seen.add(sid)

                if len(sessions_seen) >= 2:
                    findings.append({
                        "file": str(fpath),
                        "session_count": len(sessions_seen),
                        "sessions_found": sorted(sessions_seen),
                        "line_count": _count_lines(fpath),
                    })
            except (OSError, PermissionError):
                pass

    return findings


def _log_migration(actions: list[dict]) -> None:
    if not actions:
        return
    try:
        DIAG_DIR.mkdir(parents=True, exist_ok=True)
        log_path = DIAG_DIR / "session_migration.jsonl"
        for a in actions:
            record = {
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "hook": "Stop_session_gate",
                "event": "state_file_migrated",
                "old_file": a["old_file"],
                "new_target": a["deprecated_to"],
                "lines_migrated": a["lines_migrated"],
            }
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main() -> int:
    """Entry point: migrate old-format files, detect remainder, never block."""
    session_id, terminal_id = _get_current_ids()

    # Step 1: Migrate old-format state files to session-qualified format
    actions = _migrate_state_files(session_id, terminal_id)
    if actions:
        _log_migration(actions)

    # Step 2: Scan for remaining contamination (should be rare post-migration)
    findings = _scan_for_contamination(terminal_id)

    if not findings:
        return 0  # Clean — silence = allow

    # Contamination still present — log and emit advisory
    sessions: set[str] = set()
    for f in findings:
        sessions.update(f.get("sessions_found", []))
    session_list = sorted(sessions)[:5]
    files_str = "; ".join(f["file"] for f in findings[:3])

    advisory = {
        "decision": "approve",  # advisory — never blocks
        "reason": (
            f"ADVISORY: cross-session contamination persists after migration "
            f"in sessions {session_list}. Files: {files_str}. "
            f"These files contain data from 2+ sessions on the same WT_SESSION "
            f"and need manual review to split."
        ),
    }
    print(json.dumps(advisory, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
