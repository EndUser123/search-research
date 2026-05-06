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
import time
from datetime import UTC, datetime
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
# Each tuple is (compiled_regex, label_string) — label is used in reason_category
_IMPLEMENTATION_PATTERNS = [
    (re.compile(r"\bimplement\b", re.IGNORECASE), "implement"),
    (re.compile(r"\bbuild\b", re.IGNORECASE), "build"),
    (re.compile(r"\bcreate\b", re.IGNORECASE), "create"),
    (re.compile(r"\badd\b", re.IGNORECASE), "add"),
    (re.compile(r"\bdevelop\b", re.IGNORECASE), "develop"),
    (re.compile(r"\bfix\b", re.IGNORECASE), "fix"),
    (re.compile(r"\brefactor\b", re.IGNORECASE), "refactor"),
    (re.compile(r"\bupdate\b", re.IGNORECASE), "update"),
    (re.compile(r"\bmodify\b", re.IGNORECASE), "modify"),
    (re.compile(r"\bwrite\b", re.IGNORECASE), "write"),
    (re.compile(r"\bmake\b", re.IGNORECASE), "make"),
    (re.compile(r"\bgenerate\b", re.IGNORECASE), "generate"),
    (re.compile(r"\bsetup\b", re.IGNORECASE), "setup"),
    (re.compile(r"\bconfigure\b", re.IGNORECASE), "configure"),
    (re.compile(r"\binstall\b", re.IGNORECASE), "install"),
    (re.compile(r"\bdeploy\b", re.IGNORECASE), "deploy"),
]


def _get_trigger_label(prompt: str) -> str:
    """Return 'trigger:<label>' for the first matched trigger, else 'no_trigger_found'."""
    for pattern, label in _IMPLEMENTATION_PATTERNS:
        if pattern.search(prompt):
            return f"trigger:{label}"
    return "no_trigger_found"


def _has_implementation_intent(prompt: str) -> bool:
    """Check if prompt contains an explicit implementation trigger."""
    if not prompt:
        return False
    for pattern, _ in _IMPLEMENTATION_PATTERNS:
        if pattern.search(prompt):
            return True
    return False


def _get_state_path() -> Path | None:
    """Get path for session state file."""
    if load_state is None or save_state is None:
        return None
    state_dir = Path(os.environ.get("CSF_STATE_DIR", str(_HOOKS_DIR / "state")))
    return state_dir / "implementation_default_gate.json"


def _set_intent_allowed(terminal_id: str, session_id: str, allowed: bool, turn_number: int) -> None:
    """Store implementation intent state for this session+terminal+turn.

    Per-turn reset: if turn_number differs from stored turn_number, the per-turn
    implementation_allowed flag is cleared and re-evaluated for the current turn.
    This prevents a single trigger word from permanently disabling the
    gather-and-report default for the remainder of the session.
    """
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
    state[key]["turn_number"] = turn_number
    state[key]["updated_at"] = str(Path(__file__).stat().st_mtime)
    save_state(str(state_path), state)


def _is_intent_allowed(terminal_id: str, session_id: str, turn_number: int) -> bool | None:
    """Retrieve implementation intent state. Returns None if no state exists or turn_number mismatched.

    Per-turn reset: if stored turn_number differs from current turn_number,
    clears implementation_allowed and returns None so the current turn's
    trigger words are re-evaluated fresh.
    """
    if load_state is None:
        return None
    state_path = _get_state_path()
    if state_path is None or not state_path.exists():
        return None
    state = load_state(str(state_path))
    key = f"{session_id}:{terminal_id}"
    entry = state.get(key, {})

    # Per-turn reset: mismatched turn number means the stored per-turn flag is stale
    if entry.get("turn_number") != turn_number:
        return None

    return entry.get("implementation_allowed", None)


def _clear_intent_state(terminal_id: str, session_id: str, turn_number: int) -> None:
    """Clear implementation intent state for this session+terminal+turn."""
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

# Log sink for block telemetry — appended to pretooluse_blocks.jsonl
# so hook_observability_rollup.py can ingest it.
_BLOCK_LOG = _HOOKS_DIR / "logs" / "diagnostics" / "pretooluse_blocks.jsonl"


def _log_block_event(
    session_id: str,
    terminal_id: str,
    tool_name: str,
    reason_category: str,
    latency_ms: float,
) -> None:
    """Append a structured block event to pretooluse_blocks.jsonl."""
    import datetime

    entry = {
        "ts": datetime.datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "event_kind": "block:implementation_default_gate",
        "source_hook": "PreToolUse_implementation_default_gate.py",
        "blocking_hook": "PreToolUse_implementation_default_gate.py",
        "hook_phase": "PreToolUse",
        "session_id": session_id,
        "terminal_id": terminal_id,
        "tool_name": tool_name,
        "reason_category": reason_category,
        "latency_ms": round(latency_ms, 2),
        "decision": "block",
    }
    try:
        _BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_BLOCK_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # never fail the gate due to logging errors


def main() -> None:
    start_monotonic = time.monotonic()

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

    # Derive turn_number from message count in the hook input payload.
    # messages array grows by one per user turn; using its length as a
    # monotonic turn counter ensures per-turn state resets when the user
    # sends a new message.
    messages = input_data.get("messages", [])
    turn_number = len(messages)

    user_message = _get_last_user_message(input_data)

    # Check if implementation intent was already established this turn
    intent_allowed = _is_intent_allowed(terminal_id, session_id, turn_number)
    if intent_allowed is True:
        sys.exit(0)  # Already confirmed

    # Check for explicit implementation trigger words
    if _has_implementation_intent(user_message):
        _set_intent_allowed(terminal_id, session_id, True, turn_number)
        sys.exit(0)  # Allow - explicit trigger present

    # No explicit trigger found — block by default
    reason_category = _get_trigger_label(user_message)
    latency_ms = (time.monotonic() - start_monotonic) * 1000

    _log_block_event(session_id, terminal_id, tool_name, reason_category, latency_ms)

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

    print(json.dumps({"decision": "block", "reason": message, "reason_category": reason_category}))
    print(message, file=sys.stderr)
    sys.exit(2)  # Block


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# Implementation notes (self-check, not executed)
# ---------------------------------------------------------------------------
# Turn number derivation:
#   turn_number = len(input_data.get("messages", []))
#   Each user message appends one entry to the messages array, so the array
#   length is a monotonic per-session turn counter already available in the
#   hook input payload. A mismatched stored turn_number triggers per-turn reset.
#
# reason_category values:
#   "trigger:<label>" — first trigger word matched (implement, build, create, …)
#   "no_trigger_found" — no trigger word in user message
#   These values are written to pretooluse_blocks.jsonl and ingested by
#   hook_observability_rollup.py's ingest_pretooluse_blocks() as the
#   reason_category column, replacing the hard-coded "other" fallback.
#
# Latency logging:
#   time.monotonic() captured at main() entry; latency_ms computed before
#   any sys.exit(2). _log_block_event() appends a JSON line to
#   logs/diagnostics/pretooluse_blocks.jsonl (the canonical block stream),
#   matching the format expected by ingest_pretooluse_blocks().
#   hook_observability_rollup.py will pick up these events on next run.
#   latency_ms is also included in the JSON stdout payload for the block response.
#
# Per-turn reset:
#   _is_intent_allowed(key, turn_number) returns None when stored
#   turn_number differs from current turn_number, causing the gate to
#   re-evaluate trigger words for the current turn instead of using a
#   stale "session-wide" implementation_allowed flag.
#   _set_intent_allowed() stores turn_number alongside implementation_allowed.
# ---------------------------------------------------------------------------
