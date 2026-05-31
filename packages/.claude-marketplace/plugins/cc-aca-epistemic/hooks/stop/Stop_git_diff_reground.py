#!/usr/bin/env python3
"""
Stop Hook: Git-Diff Re-grounding

Injects a warning when files touched during investigation have changed from git HEAD.
This prevents reasoning on stale assumptions after the codebase changes underneath.

Addresses: "does not always re-ground after the codebase changes underneath it"
GLM/MiniMax failure mode #3.

Practical improvements (v2):
- Excludes self-edits (files the session itself wrote/edited)
- Warns once per file per session (dedup via state file)
- Time-bounds checks (only warns if file changed AFTER last Read)

Configuration:
- GIT_DIFF_REGROUND_ENABLED (default: true)
- GIT_DIFF_REGROUND_MIN_FILES (default: 3) — minimum touched files to check
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data






import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HOOKS_DIR = _hooks_dir  # from bootstrap
# Repo root is where git runs — one level above .claude/
REPO_ROOT = HOOKS_DIR.parent.parent

sys_path_hook = str(HOOKS_DIR)
if sys_path_hook not in sys.path:
    sys.path.insert(0, sys_path_hook)

try:
    from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
except ImportError:
    SCOPE_SESSION_FRESH = ""
    load_scoped_tool_events = None  # type: ignore

GIT_DIFF_REGROUND_ENABLED = os.environ.get("GIT_DIFF_REGROUND_ENABLED", "true").lower() == "true"
GIT_DIFF_REGROUND_MIN_FILES = int(os.environ.get("GIT_DIFF_REGROUND_MIN_FILES", "3"))

STATE_DIR = HOOKS_DIR / "state"


def _state_path(session_id: str) -> Path:
    return STATE_DIR / f"git_reground_warned_{session_id}.json"


def _load_warned(session_id: str) -> set[str]:
    path = _state_path(session_id)
    if not path.exists():
        return set()
    try:
        return set(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return set()


def _save_warned(session_id: str, files: set[str]) -> None:
    path = _state_path(session_id)
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(sorted(files)), encoding="utf-8")
    except Exception:
        pass


def _make_relative(file_path: str) -> str:
    """Normalize an absolute or relative path to repo-root-relative posix."""
    p = Path(file_path)
    try:
        rel = p.relative_to(REPO_ROOT)
        return rel.as_posix()
    except (ValueError, TypeError):
        pass
    # Already relative or on different drive — normalize separators
    return p.as_posix()


def _parse_ts(ts: Any) -> float:
    """Parse timestamp from event data."""
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, str):
        try:
            return float(ts)
        except (ValueError, TypeError):
            pass
    return 0.0


def load_tool_events(session_id: str, limit: int = 50) -> list[dict[str, Any]]:
    """Compatibility wrapper for recent session evidence."""
    if load_scoped_tool_events is None:
        raise ImportError("evidence_scope unavailable")
    return load_scoped_tool_events(
        session_id=session_id,
        scope=SCOPE_SESSION_FRESH,
        limit=limit,
    )


def _get_git_diff_names() -> set[str]:
    """Get files that differ from HEAD in current working tree."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return set()
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except Exception:
        return set()


def _get_session_file_touches(
    data: dict,
    session_id: str,
    limit: int = 50,
) -> tuple[dict[str, float], set[str]]:
    """Get file paths from tool events, split into reads and edits.

    Uses two data sources:
    1. data["tool_events"] — Stop hook stdin has full tool input with file_path
    2. evidence_store — fallback for events not in stdin

    Returns:
        (read_files, edited_files) where read_files maps {path: timestamp}
        and edited_files is a set of paths the session itself wrote/edited.
    """
    read_files: dict[str, float] = {}
    edited_files: set[str] = set()

    # Source 1: Stop hook stdin tool_events (has input.file_path)
    stdin_events = data.get("tool_events") or []
    for event in stdin_events:
        tool_name = event.get("name", "")
        tool_input = event.get("input") or {}
        ts = _parse_ts(event.get("timestamp") or event.get("ts"))
        path = tool_input.get("file_path") or tool_input.get("path", "")
        if not path:
            continue

        normalized = _make_relative(path)

        if tool_name == "Read":
            if ts > read_files.get(normalized, 0.0):
                read_files[normalized] = ts
        elif tool_name in ("Edit", "Write"):
            edited_files.add(normalized)

    # Source 2: evidence_store (for Bash commands that may reference files)
    try:
        ev_events = load_tool_events(session_id=session_id, limit=limit)
    except Exception:
        ev_events = []

    for event in ev_events:
        tool_name = event.get("name", "")
        command = event.get("command", "")
        ts = _parse_ts(event.get("timestamp") or event.get("ts"))

        # Bash commands: extract file paths from common patterns
        if tool_name == "Bash" and command:
            for match in re.finditer(r"(?:cat|head|tail|type)\s+[\"']?([^\s\"']+)[\"']?", command):
                path = match.group(1)
                normalized = _make_relative(path)
                if ts > read_files.get(normalized, 0.0):
                    read_files[normalized] = ts

    return read_files, edited_files


def _file_changed_after(file_path: str, after_timestamp: float) -> bool:
    """Check if a file was modified after the given timestamp."""
    try:
        abs_path = REPO_ROOT / file_path
        if abs_path.exists():
            mtime = abs_path.stat().st_mtime
            return mtime > after_timestamp
    except Exception:
        pass
    # If we can't check, assume it changed (conservative)
    return True


def check_git_diff_reground(data: dict) -> dict | None:
    """Check if investigation files have changed from git HEAD.

    Three practicality filters:
    1. Exclude files the session itself edited (self-edit exclusion)
    2. Only warn if file changed after the last Read (time-bound)
    3. Only warn once per file per session (dedup)

    Returns:
        dict with systemMessage if re-grounding needed, None otherwise
    """
    if not GIT_DIFF_REGROUND_ENABLED:
        return None

    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or os.environ.get("CLAUDE_SESSION_ID", "")
    )
    if not session_id:
        return None

    # Get files touched during investigation, split into reads vs edits
    read_files, edited_files = _get_session_file_touches(data, session_id, limit=50)

    # Need minimum files to warrant checking
    if len(read_files) < GIT_DIFF_REGROUND_MIN_FILES:
        return None

    # Get files that differ from HEAD
    changed_files = _get_git_diff_names()
    if not changed_files:
        return None

    # Normalize changed files for comparison
    changed_normalized = {str(Path(f).as_posix()) for f in changed_files}

    # Filter 1: Exclude self-edits — files this session wrote/edited
    candidate_files = read_files.keys() - edited_files

    # Find intersection: read-only files that have changed from HEAD
    intersection = candidate_files & changed_normalized

    if not intersection:
        return None

    # Filter 2: Time-bound — only warn if file changed AFTER last Read
    time_relevant = set()
    for f in intersection:
        last_read_ts = read_files.get(f, 0.0)
        if last_read_ts == 0.0:
            # No timestamp available — assume relevant (conservative)
            time_relevant.add(f)
        elif _file_changed_after(f, last_read_ts):
            time_relevant.add(f)

    if not time_relevant:
        return None

    # Filter 3: Dedup — only warn about files not already warned this session
    already_warned = _load_warned(session_id)
    new_files = time_relevant - already_warned

    if not new_files:
        return None

    # Update dedup state
    _save_warned(session_id, already_warned | new_files)

    # Build warning message
    changed_list = sorted(new_files)[:10]
    changed_str = ", ".join(f"`{f}`" for f in changed_list)
    if len(new_files) > 10:
        changed_str += f" ... and {len(new_files) - 10} more"

    message = (
        f"**Git-diff re-grounding**: The following files you investigated have changed since your last read: {changed_str}.\n"
        "Your current hypothesis may be stale. Verify the change doesn't invalidate your analysis."
    )

    return {"systemMessage": message}


def main() -> int:
    """Main hook entry point."""
    input_data = sys.stdin.read()
    if not input_data:
        print("{}")
        return 0

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        print("{}")
        return 0

    result = check_git_diff_reground(data)
    if result:
        print(json.dumps(_normalize_stdout(result)))
    else:
        print("{}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
