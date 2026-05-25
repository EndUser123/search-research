#!/usr/bin/env python3
"""
Hook state manager for repetition prevention and escalation tracking.

Centralized state management for all repetition/escalation hooks.
State is terminal-scoped and session-aware, stored in:
  ~/.claude/.artifacts/{terminal_id}/hook_state/

All state files expire after 24 hours (fresh session = fresh slate).
Multi-terminal isolated via terminal_id scoping.
Compact-resilient via durable file storage (not memory).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import logging as _li
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _home() -> Path:
    return Path.home()

def get_state_dir(terminal_id: str) -> Path:
    """Return terminal-scoped hook state directory, creating it if needed."""
    artifacts = _home() / ".claude" / ".artifacts" / terminal_id / "hook_state"
    artifacts.mkdir(parents=True, exist_ok=True)
    return artifacts

# ---------------------------------------------------------------------------
# Core I/O
# ---------------------------------------------------------------------------

def _safe_id(value: str | None) -> str:
    """Convert session/terminal id to filesystem-safe fragment."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)

def _is_stale(ts: str, hours: int = 24) -> bool:
    """Return True if ISO timestamp is older than `hours`."""
    try:
        ts_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return datetime.now() - ts_dt > timedelta(hours=hours)
    except Exception:
        return True  # Treat parse errors as stale

def read_state(terminal_id: str, filename: str) -> dict[str, Any]:
    """Read state file, returning empty dict if missing, stale, or corrupt."""
    if not terminal_id:
        return {}
    state_file = get_state_dir(terminal_id) / filename
    if not state_file.exists():
        return {}

    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        if _is_stale(data.get("ts", "")):
            return {}
        return data
    except Exception:
        return {}

def write_state(terminal_id: str, filename: str, data: dict[str, Any]) -> None:
    """Write state file atomically via temp-file replace."""
    if not terminal_id:
        return
    data["ts"] = datetime.now().isoformat()
    state_file = get_state_dir(terminal_id) / filename
    temp = state_file.with_suffix(".tmp")
    try:
        temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        temp.replace(state_file)
    except OSError:
        pass  # Fail open — state loss is not catastrophic

def clear_state(terminal_id: str, filename: str) -> None:
    """Delete a state file if it exists."""
    if not terminal_id:
        return
    state_file = get_state_dir(terminal_id) / filename
    try:
        state_file.unlink(missing_ok=True)
    except OSError:
        pass

# ---------------------------------------------------------------------------
# Violation counters
# ---------------------------------------------------------------------------

def increment_violation_count(
    terminal_id: str, session_id: str, violation_type: str
) -> int:
    """Increment and return violation count for this session.

    State file: {violation_type}_count.json
    Resets when session_id changes (new session = fresh count).
    """
    if not terminal_id:
        return 1

    filename = f"{violation_type}_count.json"
    state = read_state(terminal_id, filename)

    if state.get("session_id") != session_id:
        state = {"session_id": session_id, "count": 0}

    state["count"] = state.get("count", 0) + 1
    write_state(terminal_id, filename, state)
    return state["count"]

def get_violation_count(
    terminal_id: str, session_id: str, violation_type: str
) -> int:
    """Return current violation count for this session, or 0."""
    if not terminal_id:
        return 0

    filename = f"{violation_type}_count.json"
    state = read_state(terminal_id, filename)

    if state.get("session_id") != session_id:
        return 0
    return state.get("count", 0)

# ---------------------------------------------------------------------------
# Violation history (for repetition detection)
# ---------------------------------------------------------------------------

def get_last_violations(terminal_id: str, session_id: str) -> dict[str, Any]:
    """Read last-violations state.

    Returns:
        {
            "session_id": str,
            "turn_number": int,
            "violations": list[str],
            "user_corrected": bool,
            "acknowledged": bool,
            "ts": str
        }
    """
    return read_state(terminal_id, "last_violations.json")

def set_last_violations(
    terminal_id: str,
    session_id: str,
    turn_number: int,
    violations: list[str],
    user_corrected: bool = False,
    acknowledged: bool = False,
) -> None:
    """Write current turn's violations for next-turn comparison."""
    write_state(terminal_id, "last_violations.json", {
        "session_id": session_id,
        "turn_number": turn_number,
        "violations": violations,
        "user_corrected": user_corrected,
        "acknowledged": acknowledged,
    })

def check_violation_repeated(
    terminal_id: str,
    session_id: str,
    violation_type: str,
) -> tuple[bool, bool]:
    """Check if a violation has repeated from the previous turn.

    Args:
        terminal_id: Terminal scope
        session_id: Session scope
        violation_type: e.g. "lazy_fix", "confidence_without_evidence"

    Returns:
        (is_repeated, was_acknowledged)
        - is_repeated: violation appeared in both previous and current turn
        - was_acknowledged: previous turn contained acknowledgment of this violation
    """
    last = get_last_violations(terminal_id, session_id)

    if not last or last.get("session_id") != session_id:
        return False, False

    prev_violations = last.get("violations", [])
    if violation_type not in prev_violations:
        return False, False

    # Same violation in previous turn
    acknowledged = last.get("acknowledged", False)
    return True, acknowledged

# ---------------------------------------------------------------------------
# Acknowledgment detection
# ---------------------------------------------------------------------------

_ACK_PHRASES = [
    "you're right",
    "you're correct",
    "acknowledged",
    "i apologize",
    "that was wrong",
    "i was mistaken",
    "you caught",
    "the hook is correct",
    "i understand now",
    "fair point",
    "good catch",
]

def check_acknowledgment(output_text: str) -> bool:
    """Return True if output acknowledges a previous correction."""
    if not output_text:
        return False
    lower = output_text.lower()
    return any(phrase in lower for phrase in _ACK_PHRASES)

# ---------------------------------------------------------------------------
# Escalation helpers
# ---------------------------------------------------------------------------

def escalation_level(
    terminal_id: str,
    session_id: str,
    violation_type: str,
    thresholds: tuple[int, int, int] = (1, 2, 3),
) -> str:
    """Return escalation level: "advisory", "warning", "block".

    Args:
        thresholds: (advisory_up_to, warning_up_to, block_at_or_above)
        Default (1, 2, 3): 1st=advisory, 2nd=warning, 3rd+=block
    """
    count = get_violation_count(terminal_id, session_id, violation_type)
    advisory, warning, block = thresholds
    if count >= block:
        return "block"
    elif count >= warning:
        return "warning"
    return "advisory"

# ---------------------------------------------------------------------------
# Confidence violations tracking
# ---------------------------------------------------------------------------

def track_confidence_claim(
    terminal_id: str,
    session_id: str,
    claim: str,
    max_claims: int = 10,
) -> list[str]:
    """Track unverified confidence claims for escalation.

    Returns list of all stored claims (up to max_claims).
    """
    filename = "confidence_violations.json"
    state = read_state(terminal_id, filename)

    if state.get("session_id") != session_id:
        state = {"session_id": session_id, "claims": []}

    claims = state.get("claims", [])
    if claim not in claims:
        claims.append(claim)
        claims[:] = claims[-max_claims:]  # Keep last N

    state["claims"] = claims
    write_state(terminal_id, filename, state)
    return claims

# ---------------------------------------------------------------------------
# Circular reasoning detection
# ---------------------------------------------------------------------------

def get_explanation_history(
    terminal_id: str, session_id: str
) -> dict[str, Any]:
    """Read explanation history for circular reasoning detection."""
    return read_state(terminal_id, "explanation_history.json")

def push_explanation(
    terminal_id: str,
    session_id: str,
    explanation_hash: str,
    max_history: int = 5,
) -> list[str]:
    """Add explanation hash to history, return recent hashes."""
    filename = "explanation_history.json"
    state = read_state(terminal_id, filename)

    if state.get("session_id") != session_id:
        state = {"session_id": session_id, "history": []}

    history = state.get("history", [])
    history.append(explanation_hash)
    history[:] = history[-max_history:]

    state["history"] = history
    write_state(terminal_id, filename, state)
    return history

def is_circular_explanation(
    terminal_id: str,
    session_id: str,
    explanation_hash: str,
    similarity_threshold: int = 3,
) -> bool:
    """Check if explanation is repeating (hash appears >= threshold times).

    Uses content hash for exact duplicate detection.
    """
    history = get_explanation_history(terminal_id, session_id)
    if history.get("session_id") != session_id:
        return False

    count = 0
    for h in history.get("history", []):
        if h == explanation_hash:
            count += 1
            if count >= similarity_threshold:
                return True
    return False

# ---------------------------------------------------------------------------
# Meta-analysis trap detection
# ---------------------------------------------------------------------------

_META_PHRASES = [
    "root cause is i",
    "what i should have",
    "the actual fix should",
    "i diagnosed but didn't",
    "why i put",
    "i should have rendered",
    "the reason i used",
    "i'm analyzing why",
]

def check_meta_analysis_trap(output_text: str) -> bool:
    """Return True if output analyzes WHY instead of fixing."""
    if not output_text:
        return False
    lower = output_text.lower()
    return any(phrase in lower for phrase in _META_PHRASES)

# ---------------------------------------------------------------------------
# Tool hallucination detection
# ---------------------------------------------------------------------------

def check_tool_hallucination(output_text: str, raw_data: str | None = None) -> bool:
    """Return True if output claims tool was run but no output present."""
    if not output_text:
        return False

    tool_claim_patterns = [
        r"\bran\s+(?:the\s+)?test",
        r"\bexecuted\s+(?:the\s+)?(?:script|command)",
        r"\bverified\s+(?:with|by)",
        r"\bchecked\s+(?:the\s+)?(?:file|output)",
        r"\bran\s+(?:the\s+)?(?:build|test|lint)",
        r"\bjust\s+ran\s+",
    ]

    claims_tool = any(
        re.search(p, output_text, re.I) for p in tool_claim_patterns
    )
    if not claims_tool:
        return False

    # Check for actual tool output in raw_data
    if raw_data and ("<tool_output>" in raw_data or '"output"' in raw_data):
        return False  # Tool output present

    return True

# ---------------------------------------------------------------------------
# Fake done detection
# ---------------------------------------------------------------------------

def check_fake_done(output_text: str) -> bool:
    """Return True if output claims completion without evidence."""
    if not output_text:
        return False

    done_phrases = [
        "implementation complete",
        "done.",
        "fixed.",
        "complete.",
        "all files pass",
        "tests passed",
        "verified working",
    ]

    lower = output_text.lower()
    has_claim = any(phrase in lower for phrase in done_phrases)
    if not has_claim:
        return False

    # Check for evidence markers
    evidence_markers = [
        "```",       # Code block
        "file:",      # File reference
        "line ",      # Line reference
        "test",       # Test mention
        "diff",       # Diff output
        "git",        # Git command
        "pytest",     # Test runner
        "pass",       # Test pass
    ]

    has_evidence = any(marker in output_text for marker in evidence_markers)
    return has_claim and not has_evidence

# ---------------------------------------------------------------------------
# Workaround escalation tracking
# ---------------------------------------------------------------------------

def track_workaround(
    terminal_id: str, session_id: str
) -> int:
    """Increment workaround count for session. Returns new count."""
    return increment_violation_count(terminal_id, session_id, "workaround")

# ---------------------------------------------------------------------------
# Module self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Smoke test — run with: python hook_state_manager.py
    import sys

    tid = "test_terminal_123"
    sid = "test_session_456"

    write_state(tid, "test.json", {"value": 42})
    data = read_state(tid, "test.json")
    assert data.get("value") == 42, f"Expected 42, got {data}"

    clear_state(tid, "test.json")
    data = read_state(tid, "test.json")
    assert data == {}, f"Expected empty, got {data}"

    # Violation count test
    for _ in range(3):
        c = increment_violation_count(tid, sid, "lazy_fix")
    assert c == 3, f"Expected count 3, got {c}"

    c2 = get_violation_count(tid, sid, "lazy_fix")
    assert c2 == 3, f"Expected get count 3, got {c2}"

    c3 = get_violation_count(tid, "other_session", "lazy_fix")
    assert c3 == 0, f"Expected 0 for new session, got {c3}"

    # Acknowledgment test
    assert check_acknowledgment("You're right, I apologize")
    assert not check_acknowledgment("Let me check the file")

    # Meta trap test
    assert check_meta_analysis_trap("The root cause is I misunderstood")
    assert not check_meta_analysis_trap("I fixed the issue by adding a check")

    # Fake done test
    assert check_fake_done("Implementation complete. Done.")
    assert not check_fake_done("Implementation complete. Here's the diff:\n```")

    # Escalation level test
    assert escalation_level(tid, sid, "lazy_fix", (1, 2, 3)) == "block"
    clear_state(tid, "lazy_fix_count.json")

    _logger.info("All hook_state_manager.py self-tests passed.")