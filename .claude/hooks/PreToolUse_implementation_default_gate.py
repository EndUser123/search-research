#!/usr/bin/env python3
"""Implementation Default Gate (PreToolUse).

PURPOSE: Block Edit/Write by default unless explicit implementation intent is present.
PROBLEM ADDRESSED: LLM defaults to implementing even when user only asked for investigation,
documentation, or findings. The blanket rule is: "do not implement unless explicitly asked."

ENFORCEMENT MECHANISM:
- Scans user message for explicit implementation trigger words
- If triggers present -> allow Edit/Write
- If no triggers -> block with message asking for explicit confirmation
- State: session+terminal-scoped JSON in CSF_STATE_DIR

EXPLICIT IMPLEMENTATION TRIGGERS (must be present to allow mutation):
    implement, build, create, add, develop, fix, refactor, update, modify,
    write, make, generate, setup, configure, install, deploy

This is the FLIPPED default: gather-and-report is assumed unless an explicit
implementation trigger word appears. "Document the approach" -> no Edit/Write.
"Implement the fix" -> Edit/Write allowed.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Add hooks dir to path for shared utilities
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

# State management
try:
    from __lib.commitment_tracker import load_state, save_state
except Exception:
    load_state = None
    save_state = None

# === CONFIGURATION ===

_STATE_KEY = "implementation_default_gate"
_ALLOWED_TOOLS = {"Edit", "Write", "MultiEdit"}

# Explicit implementation trigger patterns
_IMPLEMENTATION_PATTERNS = [
    re.compile(r"\bimplement\b", re.IGNORECASE),
    re.compile(r"\bbuild\b", re.IGNORECASE),
    re.compile(r"\bcreate\b", re.IGNORECASE),
    re.compile(r"\badd\b", re.IGNORECASE),
    re.compile(r"\bdevelop\b", re.IGNORECASE),
    re.compile(r"\bfix\b", re.IGNORECASE),
    re.compile(r"\brefactor\b", re.IGNORECASE),
    re.compile(r"\bupdate\b", re.IGNORECASE),
    re.compile(r"\bmodify\b", re.IGNORECASE),
    re.compile(r"\bwrite\b", re.IGNORECASE),
    re.compile(r"\bmake\b", re.IGNORECASE),
    re.compile(r"\bgenerate\b", re.IGNORECASE),
    re.compile(r"\bsetup\b", re.IGNORECASE),
    re.compile(r"\bconfigure\b", re.IGNORECASE),
    re.compile(r"\binstall\b", re.IGNORECASE),
    re.compile(r"\bdeploy\b", re.IGNORECASE),
]


def _has_implementation_intent(prompt: str) -> bool:
    """Check if prompt contains an explicit implementation trigger."""
    if not prompt:
        return False
    for pattern in _IMPLEMENTATION_PATTERNS:
        if pattern.search(prompt):
            return True
    return False


def _get_state_path() -> Path | None:
    """Get path for session state file."""
    if load_state is None or save_state is None:
        return None
    state_dir = Path(os.environ.get("CSF_STATE_DIR", str(_HOOKS_DIR / "state")))
    return state_dir / "implementation_default_gate.json"


def _set_intent_allowed(terminal_id: str, session_id: str, allowed: bool) -> None:
    """Store implementation intent state for this session+terminal."""
    if load_state is None or save_state is None:
        return
    state_path = _get_state_path()
    if state_path is None:
        return
    state = load_state(str(state_path)) if state_path.exists() else {}
    key = f"{session_id}:{terminal_id}"
    if key not in state:
        state[key] = {}
    state[key]["implementation_allowed"] = allowed
    state[key]["updated_at"] = str(Path(__file__).stat().st_mtime)
    save_state(str(state_path), state)


def _is_intent_allowed(terminal_id: str, session_id: str) -> bool | None:
    """Retrieve implementation intent state. Returns None if no state exists."""
    if load_state is None:
        return None
    state_path = _get_state_path()
    if state_path is None or not state_path.exists():
        return None
    state = load_state(str(state_path))
    key = f"{session_id}:{terminal_id}"
    entry = state.get(key, {})
    return entry.get("implementation_allowed", None)


def _clear_intent_state(terminal_id: str, session_id: str) -> None:
    """Clear implementation intent state."""
    if load_state is None or save_state is None:
        return
    state_path = _get_state_path()
    if state_path is None or not state_path.exists():
        return
    state = load_state(str(state_path))
    key = f"{session_id}:{terminal_id}"
    state.pop(key, None)
    save_state(str(state_path), state)


def _get_last_user_message(input_data: dict[str, Any]) -> str:
    """Extract last user message from hook input data."""
    messages = input_data.get("messages", [])
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        return part.get("text", "")
            elif isinstance(content, str):
                return content
    return input_data.get("last_prompt", "")


# === MAIN ===

def main() -> None:
    stdin_content = sys.stdin.read()
    if not stdin_content.strip():
        print("implementation_default_gate: empty stdin, allowing", file=sys.stderr)
        sys.exit(0)

    try:
        input_data = json.loads(stdin_content)
    except json.JSONDecodeError:
        print("implementation_default_gate: invalid JSON, allowing", file=sys.stderr)
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    terminal_id = str(
        input_data.get("terminal_id")
        or input_data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()
    session_id = input_data.get("session_id", "default")

    # Only check mutation tools
    if tool_name not in _ALLOWED_TOOLS:
        sys.exit(0)

    user_message = _get_last_user_message(input_data)

    # Check if implementation intent was already established this turn
    intent_allowed = _is_intent_allowed(terminal_id, session_id)
    if intent_allowed is True:
        sys.exit(0)  # Already confirmed

    # Check for explicit implementation trigger words
    if _has_implementation_intent(user_message):
        _set_intent_allowed(terminal_id, session_id, True)
        sys.exit(0)  # Allow - explicit trigger present

    # No explicit trigger found - block by default
    message = (
        "\n\n⛔ IMPLEMENTATION BLOCKED: No explicit implementation intent detected.\n\n"
        "Your message does not contain an explicit implementation trigger.\n"
        "Allowed triggers: implement, build, create, add, develop, fix, refactor,\n"
        "update, modify, write, make, generate, setup, configure, install, deploy.\n\n"
        "If you want implementation, rephrase with an explicit trigger, e.g.:\n"
        '  • "implement the fix" → allows Edit/Write\n'
        '  • "build the script" → allows Edit/Write\n'
        '  • "create a handler for this" → allows Edit/Write\n\n'
        "This gate enforces: do not implement unless explicitly asked."
    )

    print(json.dumps({"decision": "block", "reason": message}))
    print(message, file=sys.stderr)
    sys.exit(2)  # Block


if __name__ == "__main__":
    main()
