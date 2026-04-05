#!/usr/bin/env python3
"""
Enforcement Rate Limiter

Session-scoped rate limiting for advisory warnings to prevent warning fatigue.

Purpose: Limit advisory warnings to max 1 per skill per session, preventing
the "advisory warnings are ignored 80%+ of the time" failure mode.

State file: .claude/state/enforcement_warnings_{session_id}.json
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Thread-safe state
_state_lock = Lock()
_state_cache: dict[str, Any] | None = None
_session_id: str | None = None


def _get_session_id() -> str:
    """Get current session ID from environment."""
    global _session_id
    if _session_id is not None:
        return _session_id

    _session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    return _session_id


def _get_state_path() -> Path:
    """Get path to session-scoped state file."""
    base = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
    base.mkdir(parents=True, exist_ok=True)
    session_id = _get_session_id()
    return base / f"enforcement_warnings_{session_id}.json"


def _load_state() -> dict[str, Any]:
    """Load warning state from file."""
    global _state_cache

    with _state_lock:
        if _state_cache is not None:
            return _state_cache

        state_path = _get_state_path()
        state: dict[str, Any]
        try:
            if state_path.exists():
                state = json.loads(state_path.read_text(encoding="utf-8"))
            else:
                state = {"warnings": {}, "created": datetime.now(timezone.utc).isoformat()}
        except (json.JSONDecodeError, OSError):
            logger.exception("Failed to load warning state")
            state = {"warnings": {}, "created": datetime.now(timezone.utc).isoformat()}

        _state_cache = state
        return state


def _save_state(state: dict[str, Any]) -> None:
    """Save warning state to file."""
    state_path = _get_state_path()
    with _state_lock:
        try:
            state["updated"] = datetime.now(timezone.utc).isoformat()
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        except OSError:
            logger.exception("Failed to save warning state")


def should_show_warning(skill_name: str, terminal_id: str | None = None) -> bool:
    """
    Check if an advisory warning should be shown (rate limited).

    Args:
        skill_name: Name of the skill generating the warning
        terminal_id: Optional terminal identifier for multi-terminal tracking

    Returns:
        True if warning should be shown (first time for this skill this session)
        False if warning was already shown (rate limited)
    """
    state = _load_state()
    key = f"{terminal_id}:{skill_name}" if terminal_id else skill_name

    if key in state.get("warnings", {}):
        # Warning already shown for this skill in this session
        return False

    return True


def record_warning_shown(
    skill_name: str,
    terminal_id: str | None = None,
    warning_content: str | None = None,
) -> None:
    """
    Record that an advisory warning was shown.

    Args:
        skill_name: Name of the skill generating the warning
        terminal_id: Optional terminal identifier
        warning_content: Optional warning text for debugging
    """
    state = _load_state()
    key = f"{terminal_id}:{skill_name}" if terminal_id else skill_name

    state.setdefault("warnings", {})[key] = {
        "shown_at": datetime.now(timezone.utc).isoformat(),
        "warning": warning_content[:200] if warning_content else None,
    }

    _save_state(state)


def get_warning_history() -> dict[str, Any]:
    """
    Get history of warnings shown this session.

    Returns:
        Dict with 'warnings' key containing skill_name -> metadata mapping
    """
    state = _load_state()
    return state.get("warnings", {})


def clear_warning_history() -> int:
    """
    Clear all warning history for this session.

    Returns:
        Number of warnings cleared
    """
    global _state_cache

    state = _load_state()
    count = len(state.get("warnings", {}))

    state["warnings"] = {}
    _save_state(state)
    _state_cache = None  # Force reload on next access

    return count


def get_session_stats() -> dict[str, Any]:
    """
    Get statistics about warning rate limiting for this session.

    Returns:
        Dict with total_warnings, unique_skills, session_created
    """
    state = _load_state()
    warnings = state.get("warnings", {})

    return {
        "total_warnings": len(warnings),
        "unique_skills": len({k.split(":")[-1] for k in warnings.keys()}),
        "session_created": state.get("created"),
        "last_updated": state.get("updated"),
    }


# Self-test
if __name__ == "__main__":
    print("=== Enforcement Rate Limiter Self-Test ===\n")

    # Test 1: First warning should be shown
    should_show = should_show_warning("test_skill")
    print(f"1. First warning should show: {'PASS' if should_show else 'FAIL'}")

    # Test 2: Record warning
    record_warning_shown("test_skill", warning_content="Test warning")
    print("2. Record warning: PASS")

    # Test 3: Second warning should be rate limited
    should_show_again = should_show_warning("test_skill")
    print(f"3. Second warning rate limited: {'PASS' if not should_show_again else 'FAIL'}")

    # Test 4: Different skill should still show
    should_show_other = should_show_warning("other_skill")
    print(f"4. Different skill shows: {'PASS' if should_show_other else 'FAIL'}")

    # Test 5: Terminal-scoped warning
    should_show_terminal = should_show_warning("test_skill", terminal_id="terminal_123")
    print(f"5. Terminal-scoped warning shows: {'PASS' if should_show_terminal else 'FAIL'}")

    # Test 6: Stats
    stats = get_session_stats()
    print(
        f"6. Session stats: {stats['total_warnings']} warnings, {stats['unique_skills']} unique skills"
    )

    # Test 7: Clear history
    cleared = clear_warning_history()
    print(f"7. Clear history: {cleared} warnings cleared")

    # Test 8: Warning shows again after clear
    should_show_after_clear = should_show_warning("test_skill")
    print(f"8. Warning shows after clear: {'PASS' if should_show_after_clear else 'FAIL'}")

    print("\n=== All tests complete ===")
