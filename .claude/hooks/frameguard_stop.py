#!/usr/bin/env python3
"""FrameGuard Stop Hook Validator.

Validates that responses addressed the systemic frame when required.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

from evidence_store import load_frameguard_state, mark_frameguard_handled

# Configuration
FRAMEGUARD_ENABLED = os.environ.get("FRAMEGUARD_ENABLED", "true").lower() == "true"
FRAMEGUARD_MODE = os.environ.get("FRAMEGUARD_MODE", "warn").lower()

# Metrics tracking
try:
    from csftracker import frameguard_blocked_inc, frameguard_unhandled_inc
except ImportError:

    def frameguard_blocked_inc() -> None:
        pass  # No-op if csftracker not available

    def frameguard_unhandled_inc() -> None:
        pass  # No-op if csftracker not available


# Systemic handling patterns (indicates frame was addressed)
SYSTEMIC_HANDLING_PATTERNS = [
    r"(?i)\bbroader (question|issue|structure|context|frame)\b",
    r"(?i)\bcoverage\b",
    r"(?i)\brelationship\b",
    r"(?i)\b(other|related) (agents?|hooks?|services?|components?|elements?)\b",
    r"(?i)\bI am not addressing the broader\b",
    r"(?i)\bsystemic (context|frame|question)\b",
    r"(?i)\barchitectural (context|implication)\b",
]


def evaluate_frameguard(data: dict[str, Any]) -> tuple[bool, str]:
    """
    Evaluate response for systemic frame handling.

    Args:
        data: Hook input data with response, session_id, terminal_id, turn_id

    Returns:
        (allow, reason) - allow=True means response can stop
    """
    if not FRAMEGUARD_ENABLED:
        return True, "FrameGuard disabled"

    response = str(data.get("response") or data.get("assistant_response") or "")
    session_id = data.get("session_id") or data.get("sessionId") or ""
    terminal_id = data.get("terminal_id") or data.get("terminalId") or ""
    turn_id = data.get("turn_id") or ""

    # Validate inputs
    if not session_id or not turn_id:
        return True, "No session/turn context"

    # Load FrameGuard state
    state = load_frameguard_state(session_id, terminal_id, turn_id)
    if not state or not state.get("needs_systemic_frame"):
        return True, "No systemic frame required"

    # Check if already handled
    if state.get("handled"):
        return True, "Systemic frame already marked as handled"

    # Check for systemic handling patterns in response
    handled = any(re.search(p, response) for p in SYSTEMIC_HANDLING_PATTERNS)

    if handled:
        # Mark as handled
        mark_frameguard_handled(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            handled=True,
            handled_reason="Systemic frame mentioned in response",
        )
        return True, "Systemic frame handled"

    # Not handled - determine action based on mode
    mark_frameguard_handled(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        handled=False,
        handled_reason="Systemic frame missing from response",
    )

    if FRAMEGUARD_MODE == "block":
        # Track metrics
        frameguard_blocked_inc()
        return False, (
            "FRAMEGUARD: Narrow-frame response to a systemic query. "
            "You must explicitly address the broader structural question(s) or "
            "state why you are not."
        )
    else:
        # Track metrics
        frameguard_unhandled_inc()
        # Warn mode - allow but annotate
        return True, (
            "FRAMEGUARD advisory: Systemic frame was required but not explicitly handled."
        )


def main() -> None:
    """Main entry point."""
    try:
        data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        data = {}

    allow, reason = evaluate_frameguard(data)

    result = {"allow": allow, "reason": reason}

    print(json.dumps(result))
    sys.exit(0 if allow else 2)


if __name__ == "__main__":
    main()
