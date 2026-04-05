#!/usr/bin/env python3
"""Session/terminal-scoped prompt state for hook coordination.

Design goals:
- Multi-terminal safe: state file is scoped by session_id + terminal_id.
- No TTL: state remains valid until replaced by a newer user prompt.
- Stale-data immune: every user prompt overwrites prior state for the scope.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path

CLAUDE_ROOT = Path("P:/.claude")
HOOKS_ROOT = CLAUDE_ROOT / "hooks"
STATE_DIR_PRIMARY = CLAUDE_ROOT / "state" / "prompt_session"
STATE_DIR_FALLBACK = HOOKS_ROOT / "state" / "prompt_session"
STATE_DIR_TEMP = Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state" / "prompt_session"


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value or "")


def resolve_session_id(data: dict | None = None) -> str:
    payload = data or {}
    session_obj = payload.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("session_id", "sessionId", "CLAUDE_SESSION_ID"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_SESSION_ID", "").strip()


def resolve_terminal_id(data: dict | None = None) -> str:
    payload = data or {}
    for key in ("terminal_id", "terminalId", "CLAUDE_TERMINAL_ID"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_TERMINAL_ID", "").strip()


def _iter_state_dirs() -> list[Path]:
    return [STATE_DIR_PRIMARY, STATE_DIR_FALLBACK, STATE_DIR_TEMP]


def _state_name(session_id: str, terminal_id: str) -> str:
    term = _safe_id(terminal_id) if terminal_id else "terminal_unknown"
    return f"latest_prompt_{_safe_id(session_id)}_{term}.json"


def _state_paths(session_id: str, terminal_id: str) -> list[Path]:
    filename = _state_name(session_id, terminal_id)
    return [base / filename for base in _iter_state_dirs()]


def write_latest_prompt(data: dict | None, prompt: str) -> tuple[bool, str]:
    """Write latest prompt for current session+terminal scope."""
    session_id = resolve_session_id(data)
    terminal_id = resolve_terminal_id(data)
    if not session_id:
        return False, "missing_session_id"
    if not terminal_id:
        terminal_id = "terminal_unknown"

    payload = {
        "session_id": session_id,
        "terminal_id": terminal_id,
        "prompt": (prompt or "").strip(),
        "updated_at": int(time.time()),
    }

    for path in _state_paths(session_id, terminal_id):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd, temp_path = tempfile.mkstemp(suffix=".tmp", dir=str(path.parent))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(payload, f, ensure_ascii=True)
                os.replace(temp_path, path)
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            return True, "written"
        except Exception:
            continue
    return False, "write_failed"


def read_latest_prompt(data: dict | None) -> tuple[str, str]:
    """Read latest prompt for current session+terminal scope."""
    session_id = resolve_session_id(data)
    terminal_id = resolve_terminal_id(data)
    if not session_id:
        return "", "missing_session_id"
    if not terminal_id:
        terminal_id = "terminal_unknown"

    for path in _state_paths(session_id, terminal_id):
        if not path.exists():
            continue
        try:
            with path.open(encoding="utf-8") as f:
                payload = json.load(f)
            if str(payload.get("session_id", "")).strip() != session_id:
                continue
            if str(payload.get("terminal_id", "")).strip() != terminal_id:
                continue
            return str(payload.get("prompt", "")).strip(), "ok"
        except Exception:
            continue
    return "", "not_found"


def read_latest_prompt_record(data: dict | None) -> tuple[dict, str]:
    """Read latest prompt record for current session+terminal scope."""
    session_id = resolve_session_id(data)
    terminal_id = resolve_terminal_id(data)
    if not session_id:
        return {}, "missing_session_id"
    if not terminal_id:
        terminal_id = "terminal_unknown"

    for path in _state_paths(session_id, terminal_id):
        if not path.exists():
            continue
        try:
            with path.open(encoding="utf-8") as f:
                payload = json.load(f)
            if str(payload.get("session_id", "")).strip() != session_id:
                continue
            if str(payload.get("terminal_id", "")).strip() != terminal_id:
                continue
            return payload, "ok"
        except Exception:
            continue
    return {}, "not_found"


def clear_latest_prompt(data: dict | None, expected_updated_at: int | None = None) -> tuple[bool, str]:
    """Clear latest prompt for current session+terminal scope."""
    session_id = resolve_session_id(data)
    terminal_id = resolve_terminal_id(data)
    if not session_id:
        return False, "missing_session_id"
    if not terminal_id:
        terminal_id = "terminal_unknown"

    removed_any = False
    for path in _state_paths(session_id, terminal_id):
        try:
            if not path.exists():
                continue
            if expected_updated_at is not None:
                with path.open(encoding="utf-8") as f:
                    payload = json.load(f)
                current_updated_at = int(payload.get("updated_at", 0))
                if current_updated_at != int(expected_updated_at):
                    return False, "stale_mismatch"
            path.unlink()
            removed_any = True
        except Exception:
            continue
    return (True, "cleared") if removed_any else (True, "already_absent")
