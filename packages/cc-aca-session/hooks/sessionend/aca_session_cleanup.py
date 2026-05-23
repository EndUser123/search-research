#!/usr/bin/env python3
"""
SessionEnd cleanup hook (minimal janitor).

Best-effort cleanup only; never blocks session end.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from shared_utils import resolve_session_id as _resolve_session_id_from_utils

# Plugin lib for shared state paths (works from source or cache)
_PLUGIN_LIB = Path(__file__).resolve().parent.parent.parent / "lib"
if str(_PLUGIN_LIB) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_LIB))

from state_paths import get_hooks_dir, safe_id as _safe_id_from_paths

HOOKS_DIR = get_hooks_dir()
sys.path.insert(0, str(HOOKS_DIR / "__lib"))


def _safe_id(value: str | None) -> str:
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _resolve_session_id(data: dict) -> str:
    """Delegates to shared_utils.resolve_session_id()."""
    return _resolve_session_id_from_utils(data)

def _resolve_terminal_id(data: dict) -> str:
    for key in ("terminal_id", "terminalId", "CLAUDE_TERMINAL_ID"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_TERMINAL_ID", "").strip() or "terminal_unknown"


def _delete_if_exists(path: Path) -> None:
    try:
        if path.exists():
            path.unlink(missing_ok=True)
    except Exception:
        pass


def _terminal_cleanup_keys(terminal_id: str) -> list[str]:
    """Return terminal-safe IDs that may exist for this session's state files."""
    keys: list[str] = []
    if terminal_id and terminal_id != "terminal_unknown":
        keys.append(_safe_id(terminal_id))
    else:
        keys.append("unknown")

    if "unknown" not in keys:
        keys.append("unknown")
    return keys


def main() -> None:
    raw = sys.stdin.read().strip()
    if not raw:
        print("{}")
        sys.exit(0)

    try:
        data = json.loads(raw.lstrip("\ufeff"))
    except json.JSONDecodeError:
        data = {}

    session_id = _resolve_session_id(data)
    terminal_id = _resolve_terminal_id(data)

    # 1) Clear terminal/session-scoped transient state created by active hooks.
    state_bases = [
        HOOKS_DIR / "state",
        Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state",
    ]
    safe_session = _safe_id(session_id)
    terminal_keys = _terminal_cleanup_keys(terminal_id)
    safe_terminal = terminal_keys[0]
    for base in state_bases:
        if session_id:
            for terminal_key in terminal_keys:
                _delete_if_exists(base / f"pending_command_intent_{terminal_key}.json")
                _delete_if_exists(base / f"pending_command_intent_{terminal_key}_{safe_session}.json")
                _delete_if_exists(base / f"pretool_degraded_{terminal_key}_{safe_session}.json")
            _delete_if_exists(base / f"pending_command_intent_{safe_session}.json")
            _delete_if_exists(base / f"pretool_degraded_{safe_session}.json")
            _delete_if_exists(base / f"grounded_artifact_{safe_session}.json")
            for terminal_key in terminal_keys:
                _delete_if_exists(base / f"grounded_artifact_{terminal_key}_{safe_session}.json")

    # 2) Clear scoped blocked-claim marker for this session/terminal.
    scoped_marker = (
        HOOKS_DIR / "session_data" / f"last_blocked_claim_{safe_session}_{safe_terminal}.json"
    )
    _delete_if_exists(scoped_marker)

    # 3) Remove edit-consent tokens for this session/terminal by using impossible task scope.
    try:
        import pre_tool_use_logic

        if session_id:
            pre_tool_use_logic.cleanup_session_edit_consent_tokens(
                session_id,
                terminal_id=terminal_id,
                major_task_id="__session_end_cleanup__",
            )
    except Exception:
        pass

    # 4) Cleanup terminal-specific state file (multi-terminal isolation)
    # Remove the terminal_{hex_handle}.json file written by SessionStart
    state_dir = HOOKS_DIR / "state"
    if terminal_id and terminal_id != "terminal_unknown":
        try:
            # Extract console handle from terminal_id if it's a console_ format
            # terminal_id format is "console_{hex_handle}" or similar
            if terminal_id.startswith("console_"):
                console_handle = terminal_id.split("_", 1)[1] if "_" in terminal_id else ""
                if console_handle:
                    terminal_state_file = state_dir / f"terminal_{console_handle}.json"
                    _delete_if_exists(terminal_state_file)
        except Exception:
            pass  # Terminal state cleanup failure is non-critical

    # 5) Cleanup discovery state file (ADR-00X discovery-first enforcement)
    # Session-scoped state file: ~/.claude/discovery_state_{session_id}.json
    if session_id:
        try:
            discovery_state_file = Path.home() / '.claude' / f'discovery_state_{safe_session}.json'
            _delete_if_exists(discovery_state_file)
        except PermissionError as e:
            # Log permission errors distinctly (observable for diagnostics)
            print(f"[SessionEnd Cleanup] Permission denied removing discovery state: {e}", file=sys.stderr)
        except Exception as e:
            # Log other OS errors (network filesystem issues, etc.)
            print(f"[SessionEnd Cleanup] OS error removing discovery state: {e}", file=sys.stderr)
        # If file doesn't exist, silently succeed (idempotent cleanup)

    print("{}")
    sys.exit(0)


if __name__ == "__main__":
    main()
