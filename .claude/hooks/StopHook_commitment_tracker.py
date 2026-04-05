"""
StopHook_commitment_tracker.py - Persist uncompleted commitments at session end.

At session end (any stop):
1. Reads transcript from session state
2. Calls CommitmentTracker.scan_transcript()
3. Calls CommitmentTracker.check_completion() for each
4. Persists uncompleted commitments via save_state()

Feature-gated by PROACTIVE_COMMITMENT_TRACKER_ENABLED.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add __lib to path for commitment_tracker import
_HOOKS_DIR = Path(__file__).resolve().parent
_HOOKS_LIB_DIR = _HOOKS_DIR / "__lib"
if str(_HOOKS_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_LIB_DIR))

from commitment_tracker import CommitmentTracker

# Feature flag check
_ENABLED = os.environ.get("PROACTIVE_COMMITMENT_TRACKER_ENABLED", "").lower() in (
    "1",
    "true",
    "yes",
)


def run(data: dict) -> dict:
    """Main entry point for Stop router.

    Args:
        data: Stop hook payload with transcript and session info.

    Returns:
        dict with 'allow' (bool) and 'reason' (str).
    """
    if not _ENABLED:
        return {"allow": True, "reason": "Commitment tracker disabled"}

    try:
        terminal_id = _extract_terminal_id(data)
        if not terminal_id:
            return {"allow": True, "reason": "No terminal_id available"}

        transcript = _extract_transcript(data)
        if not transcript:
            return {"allow": True, "reason": "No transcript available"}

        session_id = _extract_session_id(data)

        tracker = CommitmentTracker()
        commitments = tracker.scan_transcript(transcript, session_id=session_id)

        # Check completion status for each commitment
        uncompleted = []
        for commitment in commitments:
            updated = tracker.check_completion(commitment, transcript)
            if not updated.completed:
                uncompleted.append(updated)

        if uncompleted:
            tracker.save_state(uncompleted, terminal_id)

        return {"allow": True, "reason": f"Tracked {len(uncompleted)} uncompleted commitments"}

    except Exception as exc:
        # Fail open - don't block stop for commitment tracking errors
        return {"allow": True, "reason": f"Commitment tracker error: {exc}"}


def _extract_terminal_id(data: dict) -> str:
    """Extract terminal_id from hook data."""
    # Try direct field first
    terminal = data.get("terminal_id", "")
    if terminal:
        return str(terminal)

    # Try nested session object
    session = data.get("session", {})
    if isinstance(session, dict):
        terminal = session.get("terminal_id", "")
        if terminal:
            return str(terminal)

    # Try environment fallback (for subprocess mode)
    terminal = os.environ.get("CLAUDE_TERMINAL_ID", "")
    if terminal:
        return terminal

    return ""


def _extract_session_id(data: dict) -> str:
    """Extract session_id from hook data."""
    session = data.get("session_id", "")
    if session:
        return str(session)

    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            val = session_obj.get(key)
            if val:
                return str(val)

    return ""


def _extract_transcript(data: dict) -> list[dict]:
    """Extract transcript from hook data."""
    transcript = data.get("transcript", [])
    if isinstance(transcript, list):
        return transcript

    # Try to get from handoff_envelope or other sources
    handoff = data.get("handoff_envelope", {})
    if isinstance(handoff, dict):
        transcript = handoff.get("transcript", [])
        if isinstance(transcript, list):
            return transcript

    return []
