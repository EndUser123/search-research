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


def _get_artifacts_dir(terminal_id_override: str | None = None) -> Path:
    """Get .artifacts directory for this terminal.

    Args:
        terminal_id_override: Optional terminal ID from input data (preferred)
                               to match prospector's context-derived approach.
    """
    claude_root = HOOKS_DIR.parent.parent  # P:/.claude
    # Use override if provided (from input data), otherwise detect
    terminal_id = terminal_id_override or _detect_terminal_id()
    return claude_root / ".artifacts" / terminal_id / "hook_state"


def _detect_terminal_id() -> str:
    """Detect terminal ID for state isolation.

    Uses WT_SESSION env var (set in Windows Terminal).
    Falls back to CLAUDE_TERMINAL_ID, then to hash(PID+cwd).
    Normalized to console_{uuid} format.
    """
    raw = os.environ.get("WT_SESSION", "")
    if raw:
        return f"console_{raw}"

    # Fallback: CLAUDE_TERMINAL_ID env var
    fallback = os.environ.get("CLAUDE_TERMINAL_ID", "")
    if fallback:
        return f"console_{fallback}"

    # Fallback: hash of PID + cwd for process isolation
    import hashlib
    pid = os.getpid()
    cwd = os.getcwd()
    hash_input = f"{pid}:{cwd}"
    terminal_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
    return f"unknown_{terminal_hash}"


def _is_expired(timestamp: float, now: float | None = None) -> bool:
    """Check if state has expired."""
    if now is None:
        now = time.time()
    return (now - timestamp) >= DELEGATION_TTL_SECONDS


def _load_delegation_state(terminal_id: str | None = None) -> dict | None:
    """Load delegation state from terminal-scoped state file.

    Args:
        terminal_id: Optional terminal ID from input data to match prospector's
                     context-derived approach and validate state freshness.
    """
    state_dir = _get_artifacts_dir(terminal_id)
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
        # Validate terminal_id matches current detection (cross-terminal bleed check)
        if terminal_id:
            stored_terminal_id = state.get("terminal_id", "")
            current_terminal_id = _detect_terminal_id()
            # If stored differs from current AND stored differs from provided,
            # treat as stale (cross-terminal bleed)
            if stored_terminal_id and stored_terminal_id != terminal_id:
                state_file.unlink(missing_ok=True)
                return None
        return state
    except (json.JSONDecodeError, OSError):
        return None


def _clear_delegation_state(terminal_id: str | None = None) -> None:
    """Clear delegation state.

    Args:
        terminal_id: Optional terminal ID from input data.
    """
    state_dir = _get_artifacts_dir(terminal_id)
    state_file = state_dir / "delegation_expected.json"
    try:
        state_file.unlink(missing_ok=True)
    except OSError:
        pass


def _log_gate_event(event_type: str, tool_name: str, detail: str = "") -> None:
    """Log gate events to telemetry."""
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "event": event_type,
        "terminal_id": _detect_terminal_id(),
        "tool_name": tool_name,
        "detail": detail,
    }
    try:
        log_dir = HOOKS_DIR / "logs" / "diagnostics"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "delegation_gate.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        # Fallback to stderr when file logging fails
        import warnings
        warnings.warn(f"delegation_gate: failed to log event to file: {entry}", RuntimeWarning)


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

    # Extract terminal_id from input data if available (matches prospector's approach)
    terminal_id = _detect_terminal_id_from_data(data)

    # Check for bypass flag
    if _is_bypass_flagged(prompt):
        _log_gate_event("bypass_used", tool_name)
        return 0  # Allow

    # Load delegation state (terminal-scoped, with input-data terminal_id for validation)
    state = _load_delegation_state(terminal_id)
    if not state:
        return 0  # No delegation expected, allow

    # Task or Agent tool clears state (delegation occurred)
    if tool_name in ("Task", "Agent"):
        _clear_delegation_state(terminal_id)
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


def _detect_terminal_id_from_data(data: dict) -> str | None:
    """Extract terminal_id from input data if available.

    Prioritizes context-derived terminal_id over env detection
    to match prospector's approach and prevent path mismatch.
    """
    # Try various keys that Claude Code might use
    for key in ("terminal_id", "terminalId", "CLAUDE_TERMINAL_ID", "terminal"):
        if key in data and data[key]:
            return str(data[key])
    return None


if __name__ == "__main__":
    sys.exit(main())