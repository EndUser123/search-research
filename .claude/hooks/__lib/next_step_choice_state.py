#!/usr/bin/env python3
"""Next Step Choice State Manager.

Persists the *most recent* Stop-time "Next Step Options" menu for a given
(session_id, terminal_id) scope, so the user can respond with a single number
(e.g. "0") and have UserPromptSubmit rewrite their prompt to the chosen command.

Design goals:
- Multi-terminal friendly: state is scoped by session_id + terminal_id when available.
- Stale immune WITHOUT TTL: state is one-turn only (cleared on any non-choice input).
- No background processes.

This intentionally does *not* use TTL timeouts; staleness is handled by:
- overwriting state on each new menu
- clearing state when the user sends any non-choice message

Files:
- State dir: P:/.claude/state/next_step_choice/
- State file name: derived from session_id + terminal_id (sanitized)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from __lib.file_lock import FileLock

STATE_DIR = Path("P:/.claude/state/next_step_choice")


_SAFE_RE = re.compile(r"[^a-zA-Z0-9_.-]+")


def _safe_fragment(value: str) -> str:
    value = (value or "").strip()
    value = value.replace("..", "_")
    value = value.replace("/", "_").replace("\\", "_").replace(":", "_")
    value = _SAFE_RE.sub("_", value)
    return value or "unknown"


def _extract_session_id(data: dict[str, Any]) -> str:
    return str(
        data.get("session_id")
        or data.get("sessionId")
        or data.get("conversation_id")
        or data.get("conversationId")
        or ""
    ).strip()


def _extract_terminal_id(data: dict[str, Any]) -> str:
    # Prefer explicit fields; otherwise use terminal_detection's deterministic resolution.
    tid = str(data.get("terminal_id") or data.get("terminalId") or "").strip()
    if tid:
        return tid

    try:
        from __lib.terminal_detection import resolve_terminal_key

        resolved = resolve_terminal_key(data)
        return "" if resolved == "unknown" else str(resolved)
    except Exception:
        return ""


def _state_key(data: dict[str, Any]) -> str | None:
    """Return a stable scope key for the state file.

    Preference:
    1) session + terminal (best)
    2) session only
    3) terminal only
    4) None (feature disabled)
    """

    sid = _extract_session_id(data)
    tid = _extract_terminal_id(data)

    if sid and tid:
        return f"session_{_safe_fragment(sid)}__terminal_{_safe_fragment(tid)}"
    if sid:
        return f"session_{_safe_fragment(sid)}"
    if tid:
        return f"terminal_{_safe_fragment(tid)}"
    return None


def _state_file(data: dict[str, Any]) -> Path | None:
    key = _state_key(data)
    if not key:
        return None
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR / f"{key}.json"


@dataclass(frozen=True)
class NextStepOption:
    label: str
    command: str
    display: str


def _parse_options(options: list[str]) -> list[NextStepOption]:
    parsed: list[NextStepOption] = []
    for idx, opt in enumerate(options):
        if not isinstance(opt, str):
            continue
        s = opt.strip()
        if not s:
            continue

        # /p-style numbering: 0, 1, 2, ...
        label = str(idx)

        token = s.split()[0].strip()
        if not token.startswith("/"):
            token = "/" + token.lstrip("/")

        parsed.append(NextStepOption(label=label, command=token, display=s))
    return parsed


def save_next_step_menu(data: dict[str, Any], options: list[str], response_text: str = "") -> None:
    """Persist a new menu (overwrites any previous menu for this scope)."""
    state_path = _state_file(data)
    if state_path is None:
        return

    parsed = _parse_options(options)
    if not parsed:
        clear_next_step_menu(data)
        return

    resp_hash = hashlib.sha256((response_text or "").encode("utf-8", errors="ignore")).hexdigest()[:16]

    payload = {
        "pending": True,
        "response_hash": resp_hash,
        "options": [
            {"label": o.label, "command": o.command, "display": o.display}
            for o in parsed
        ],
    }

    lock_path = state_path.with_suffix(".lock")
    tmp_path = state_path.with_suffix(f".{hashlib.md5(os.urandom(16)).hexdigest()[:8]}.tmp")

    try:
        with FileLock(lock_path, timeout=2.0):
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp_path.replace(state_path)
    except Exception:
        # Fail open: never break Stop hook.
        try:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def clear_next_step_menu(data: dict[str, Any]) -> None:
    state_path = _state_file(data)
    if state_path is None:
        return

    lock_path = state_path.with_suffix(".lock")
    try:
        with FileLock(lock_path, timeout=1.0):
            state_path.unlink(missing_ok=True)
    except Exception:
        pass


def get_pending_next_step_menu(data: dict[str, Any]) -> dict[str, Any] | None:
    state_path = _state_file(data)
    if state_path is None or not state_path.exists():
        return None

    lock_path = state_path.with_suffix(".lock")
    try:
        with FileLock(lock_path, timeout=1.0):
            obj = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(obj, dict) or not obj.get("pending"):
            return None
        if not isinstance(obj.get("options"), list) or not obj["options"]:
            return None
        return obj
    except Exception:
        return None


def detect_number_choice(message: str) -> str | None:
    """Detect a numeric choice token.

    Stale-immune by design: only accept a *single* number token (e.g. "0").
    We intentionally do not accept "0 - ..." or other variants.
    """
    msg = (message or "").strip()
    if re.fullmatch(r"\d+", msg):
        return msg
    return None


# Backward-compatibility: older code/tests referred to "letter choice".
# Keep this name, but make it numeric.
def detect_letter_choice(message: str) -> str | None:
    return detect_number_choice(message)


def resolve_choice_to_command(state: dict[str, Any], choice: str) -> tuple[str, str] | None:
    """Return (command, display) for a given numeric choice token (e.g. "0")."""
    if not state or not isinstance(state.get("options"), list):
        return None

    for opt in state["options"]:
        if not isinstance(opt, dict):
            continue
        if str(opt.get("label", "")).strip() == str(choice).strip():
            cmd = str(opt.get("command", "")).strip()
            disp = str(opt.get("display", "")).strip()
            if cmd:
                return cmd, disp
    return None
