#!/usr/bin/env python3
"""PreToolUse Delegation Gate - Block non-Task tools when delegation is expected.

Wired to delegation_prospector state: when delegation_prospector detects a
delegation opportunity and writes state, this gate blocks any tool other
than Task until the delegation occurs.

State location: .claude/.artifacts/{terminal_id}/hook_state/delegation_expected.json
Terminal-scoped for multi-terminal isolation.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
# Three levels up: hooks/ -> .claude/ -> P:/
# State goes in .artifacts/{terminal_id}/hook_state/
DELEGATION_TTL_SECONDS = 300  # 5 minutes


def _get_artifacts_dir() -> Path:
    """Get .artifacts directory for this terminal."""
    claude_root = HOOKS_DIR.parent.parent  # P:/.claude
    terminal_id = _detect_terminal_id()
    return claude_root / ".artifacts" / terminal_id / "hook_state"


def _detect_terminal_id() -> str:
    """Detect terminal ID for state isolation.

    Uses WT_SESSION env var (set in Windows Terminal).
    Normalized to console_{uuid} format.
    """
    raw = os.environ.get("WT_SESSION", "")
    if raw:
        return f"console_{raw}"
    return "unknown"


def _is_expired(timestamp: float, now: float | None = None) -> bool:
    """Check if state has expired."""
    if now is None:
        now = time.time()
    return (now - timestamp) >= DELEGATION_TTL_SECONDS


def _load_delegation_state() -> dict | None:
    """Load delegation state from terminal-scoped state file."""
    state_dir = _get_artifacts_dir()
    state_file = state_dir / "delegation_expected.json"
    if not state_file.exists():
        return None
    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = json.load(f)
        # Check TTL
        detected_at = state.get("detected_at", 0)
        if _is_expired(detected_at):
            state_file.unlink(missing_ok=True)
            return None
        return state
    except (json.JSONDecodeError, OSError):
        return None


def _clear_delegation_state() -> None:
    """Clear delegation state."""
    state_dir = _get_artifacts_dir()
    state_file = state_dir / "delegation_expected.json"
    try:
        state_file.unlink(missing_ok=True)
    except OSError:
        pass


def _log_gate_event(event_type: str, tool_name: str, detail: str = "") -> None:
    """Log gate events to telemetry."""
    try:
        log_dir = HOOKS_DIR / "logs" / "diagnostics"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "delegation_gate.jsonl"
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "event": event_type,
            "terminal_id": _detect_terminal_id(),
            "tool_name": tool_name,
            "detail": detail,
        }
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def _is_bypass_flagged(prompt: str) -> bool:
    """Check if user message contains bypass flag."""
    if not prompt:
        return False
    # Only exact --allow-inline flag (not similar text)
    return bool(re.search(r"--allow-inline\b", prompt, re.IGNORECASE))


def _build_block_message(tool_name: str, state: dict) -> str:
    """Build descriptive block message."""
    matched = state.get("matched_pattern", "unknown pattern")
    snippet = state.get("prompt_snippet", "")[:100]
    return f"""⛔ DELEGATION REQUIRED

A delegation opportunity was detected: {matched}

Snippet: {snippet}...

You MUST use the Agent/Task tool to delegate this work.

To bypass this gate: Add --allow-inline to your message.
"""


def main() -> int:
    """Run the delegation gate."""
    data = _load_data()
    if not data:
        return 0  # Allow on parse error (fail-open)

    tool_name = data.get("tool_name", "")
    prompt = data.get("prompt", "") or data.get("user_input", "")

    # Check for bypass flag
    if _is_bypass_flagged(prompt):
        _log_gate_event("bypass_used", tool_name)
        return 0  # Allow

    # Load delegation state (terminal-scoped)
    state = _load_delegation_state()
    if not state:
        return 0  # No delegation expected, allow

    # Task or Agent tool clears state (delegation occurred)
    if tool_name in ("Task", "Agent"):
        _clear_delegation_state()
        _log_gate_event("delegation_occurred_state_cleared", tool_name)
        return 0  # Allow

    # Block all other tools
    block_msg = _build_block_message(tool_name, state)
    print(block_msg, file=sys.stderr)
    _log_gate_event("blocked", tool_name, state.get("matched_pattern", ""))
    return 2  # Block


def _load_data() -> dict | None:
    """Load PreToolUse input data from stdin."""
    try:
        raw = sys.stdin.read()
        if not raw:
            return None
        return json.loads(raw)
    except (json.JSONDecodeError, OSError):
        return None


if __name__ == "__main__":
    sys.exit(main())