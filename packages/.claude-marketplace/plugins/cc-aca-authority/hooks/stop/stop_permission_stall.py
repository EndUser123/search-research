#!/usr/bin/env python3
"""
Permission-seeking stall detector for Stop hook.

Detects when the LLM asks "Want me to...?" / "Shall I proceed?" after the user
has already given explicit authorization (via /command or skill invocation).
The permission-seeking phrase should not appear after 3 turns of explicit auth.

Detection:
  - "Want me to..." / "Should I..." / "Shall I proceed?" in response
  - No Bash tool used
  - Authorization signal detected (slash command in prompt OR active_skill set)
  - Grace period: 3 turns after authorization before blocking

State: Per-terminal, stored in state/stop_permission_stall/{terminal_id}.json

Author: Stop System Team
Created: 2026-05-12
"""

# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

_Hook_Dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(_Hook_Dir))

_STATE_SUBDIR = "stop_permission_stall"
_GRACE_TURNS = 3
_TTL_SECONDS = 60 * 60  # 1 hour


# Permission-seeking patterns — phrases that seek re-authorization
# after the user has already authorized via /command or skill invocation.
_PERMISSION_SEEKING_PATTERNS = [
    r"\bwant\s+me\s+to\s+(?:do|implement|fix|try|run|execute)\b",
    r"\bshould\s+I\s+(?:implement|do|fix|run|execute)\b",
    r"\bshall\s+I\s+(?:proceed|implement|fix)\b",
    r"\bdo\s+you\s+want\s+me\s+to\s+(?:implement|do|fix|run)\b",
    r"\bwould\s+you\s+like\s+me\s+to\s+(?:implement|do|fix|run)\b",
    r"\bcan\s+I\s+(?:just|simply|go\s+ahead\s+and)\s+(?:implement|do|fix|add)\b",
    r"\bmay\s+I\s+(?:proceed|implement|fix)\b",
]


def _get_state_dir() -> Path:
    base = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
    return base / _STATE_SUBDIR


def _state_path(terminal_id: str) -> Path:
    return _get_state_dir() / f"{terminal_id}.json"


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"grace_remaining": 0, "authorization_ts": 0, "updated_at": 0}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"grace_remaining": 0, "authorization_ts": 0, "updated_at": 0}


def _save_state(path: Path, state: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=True), encoding="utf-8")
    except OSError:
        pass


def _has_permission_seeking(text: str) -> bool:
    """Return True if text contains permission-seeking phrases."""
    for pattern in _PERMISSION_SEEKING_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _has_authorization_signal(user_prompt: str) -> bool:
    """Return True if user prompt contains an authorization signal."""
    # Slash command
    if re.search(r"^/\S", user_prompt.strip()):
        return True
    # Explicit authorization phrases
    auth_phrases = [
        "do it", "go ahead", "proceed", "yes, do", "go for it",
        "yes please", "please do", "authorized",
        "you're cleared", "you can go ahead",
    ]
    prompt_lower = user_prompt.lower()
    if any(phrase in prompt_lower for phrase in auth_phrases):
        return True
    return False


def _has_bash_evidence(tool_events: list[dict]) -> bool:
    """Return True if any Bash tool was used this turn."""
    for event in tool_events:
        if event.get("name") == "Bash":
            return True
    return False


def _detect_permission_stall(data: dict) -> dict | None:
    """Detect permission-seeking stall after authorization.

    Returns None (pass) or a dict with systemMessage/advisory.
    """
    terminal_id = data.get("terminal_id") or os.environ.get("CLAUDE_TERMINAL_ID", "")
    if not terminal_id:
        return None

    response_text = data.get("output_text", "")
    user_prompt = data.get("user_prompt", "")
    tool_events = data.get("tool_events", [])
    if isinstance(tool_events, dict):
        tool_events = tool_events.get("events", [])

    # Only check if response has permission-seeking pattern
    if not _has_permission_seeking(response_text):
        return None

    # Only check if no Bash tools used (wants to seek permission instead of doing)
    if _has_bash_evidence(tool_events):
        return None

    # Load state
    path = _state_path(terminal_id)
    state = _load_state(path)
    now = int(time.time())

    # Reset stale state
    if now - state.get("updated_at", 0) > _TTL_SECONDS:
        state = {"grace_remaining": 0, "authorization_ts": 0, "updated_at": 0}

    # Check for new authorization signal in user prompt
    if _has_authorization_signal(user_prompt):
        state["grace_remaining"] = _GRACE_TURNS
        state["authorization_ts"] = now
        state["updated_at"] = now
        _save_state(path, state)
        return None  # Grace period just granted — don't block

    # Check grace period
    if state.get("grace_remaining", 0) > 0:
        state["grace_remaining"] -= 1
        state["updated_at"] = now
        _save_state(path, state)
        return None  # Still in grace period

    # Grace expired — block
    return {
        "decision": "block",
        "systemMessage": (
            "PERMISSION-SEEKING STALL: You asked 'Want me to...?' or 'Shall I proceed?' "
            "but you already have authorization (a /command was invoked or the user "
            "gave explicit permission).\n\n"
            "Rule: After a /command or explicit authorization, proceed directly with "
            "tool use — do not ask for permission again.\n\n"
            "Take action now: Edit, Write, or Bash. Do not seek re-authorization."
        ),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Simple functional tests - no file state needed for detection logic
    from stop_permission_stall import (
        _has_permission_seeking,
        _has_authorization_signal,
        _has_bash_evidence,
    )

    # Test 1: No permission seeking → False
    assert _has_permission_seeking("Here's the analysis.") is False
    assert _has_permission_seeking("The gap was identified.") is False

    # Test 2: Permission seeking patterns
    assert _has_permission_seeking("Want me to implement this?") is True
    assert _has_permission_seeking("Should I fix the issue?") is True
    assert _has_permission_seeking("Shall I proceed?") is True
    assert _has_permission_seeking("Can I just add it?") is True

    # Test 3: Non-seeking phrases (should NOT match)
    assert _has_permission_seeking("I want to implement this") is False  # not "want me to"
    assert _has_permission_seeking("You should implement this") is False  # not "should I"

    # Test 4: Authorization signal detection
    assert _has_authorization_signal("/design implement the gap") is True
    assert _has_authorization_signal("/cc-skills-sdlc:design test") is True
    assert _has_authorization_signal("do it") is True
    assert _has_authorization_signal("go ahead") is True
    assert _has_authorization_signal("proceed") is True
    assert _has_authorization_signal("yes, do it") is True

    # Test 5: Non-auth signals
    assert _has_authorization_signal("Can you look at this?") is False
    assert _has_authorization_signal("what do you think") is False

    # Test 6: Bash evidence detection
    assert _has_bash_evidence([{"name": "Bash"}]) is True
    assert _has_bash_evidence([{"name": "Read"}]) is False
    assert _has_bash_evidence([{"name": "Bash"}, {"name": "Edit"}]) is True
    assert _has_bash_evidence([]) is False

    # Test 7: Permission stall detection (unit-level, no state file)
    from stop_permission_stall import _detect_permission_stall

    # No permission seeking → pass
    result = _detect_permission_stall({
        "terminal_id": "test",
        "output_text": "Here's my analysis.",
        "user_prompt": "/design what to do",
        "tool_events": [],
    })
    assert result is None, f"Non-seeking text should pass, got {result}"

    # Permission seeking + no auth → block
    result = _detect_permission_stall({
        "terminal_id": "test",
        "output_text": "Want me to implement this?",
        "user_prompt": "Can you look at this?",
        "tool_events": [],
    })
    assert result is not None and result["decision"] == "block"

    # Permission seeking + auth signal → pass (grace granted)
    result = _detect_permission_stall({
        "terminal_id": "test2",
        "output_text": "Want me to proceed?",
        "user_prompt": "/design implement the gap",
        "tool_events": [],
    })
    assert result is None, f"Auth signal should grant grace, got {result}"

    # Permission seeking + Bash used → pass (authorization via execution)
    result = _detect_permission_stall({
        "terminal_id": "test3",
        "output_text": "Want me to proceed?",
        "user_prompt": "/design",
        "tool_events": [{"name": "Bash"}],
    })
    assert result is None, f"Bash used = auth via execution, got {result}"

    print("All stop_permission_stall.py self-tests passed.", file=sys.stderr)