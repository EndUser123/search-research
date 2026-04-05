#!/usr/bin/env python3
"""
Session validation improvement for PreCompact_handoff_capture.py

This script adds session ownership validation to PreCompact, preventing
unnecessary I/O when creating handoffs that don't belong to the current session.

Current behavior:
  - PreCompact creates handoff for ANY active task
  - Stores in task metadata
  - SessionStart validates and blocks if session mismatch
  - Result: Wasted I/O creating handoff that will be rejected

Improved behavior:
  - PreCompact reads current_session.json (authoritative source)
  - Extracts session ID from transcript_path
  - Only creates handoff if sessions match
  - Result: No wasted I/O, cleaner architecture
"""

import json
from pathlib import Path


def check_session_ownership(
    transcript_path: str,
    current_session_file: Path = Path("P:/.claude/current_session.json")
) -> tuple[bool, str, str]:
    """Check if a handoff belongs to the current session.

    Args:
        transcript_path: Path to the session transcript (e.g., "P:/.claude/sessions/session_abc123.jsonl")
        current_session_file: Path to current_session.json (authoritative source)

    Returns:
        Tuple of (is_owned, handoff_session, current_session)
        - is_owned: True if handoff belongs to current session
        - handoff_session: Session ID extracted from transcript_path
        - current_session: Session ID from current_session.json
    """
    # Extract session ID from transcript path
    # Path format: "P:/.claude/sessions/session_abc123.jsonl"
    # Session ID is the filename without extension
    handoff_session = Path(transcript_path).stem

    # Read current session from authoritative source
    current_session = ""
    if current_session_file.exists():
        try:
            with open(current_session_file, encoding="utf-8") as f:
                current_session_data = json.load(f)
            current_session = current_session_data.get("session_id", "")
        except (json.JSONDecodeError, OSError):
            current_session = ""

    # Check if sessions match
    is_owned = current_session and handoff_session == current_session

    return is_owned, handoff_session, current_session


def format_session_message(
    is_owned: bool,
    handoff_session: str,
    current_session: str,
    task_name: str
) -> str:
    """Format a human-readable session validation message.

    Args:
        is_owned: Whether handoff belongs to current session
        handoff_session: Session ID from handoff transcript
        current_session: Current session ID
        task_name: Name of the task

    Returns:
        Formatted message string
    """
    if is_owned:
        return (
            f"[PreCompact] ✓ Session validation passed: '{task_name}' belongs to current session\n"
            f"  Handoff session: {handoff_session}\n"
            f"  Current session: {current_session}"
        )
    elif not current_session:
        return (
            f"[PreCompact] ⚠️  No current session detected: '{task_name}' will be created without session validation\n"
            f"  Handoff session: {handoff_session}\n"
            f"  Reason: current_session.json not found or empty"
        )
    else:
        return (
            f"[PreCompact] ⊘ Session validation skipped: '{task_name}' from different session\n"
            f"  Handoff session: {handoff_session}\n"
            f"  Current session: {current_session}\n"
            f"  Action: Handoff will not be created (prevents wasted I/O)"
        )


if __name__ == "__main__":
    # Test scenarios
    print("=" * 70)
    print("SESSION VALIDATION TEST SCENARIOS")
    print("=" * 70)
    print()

    # Scenario 1: Matching sessions (should create handoff)
    print("Scenario 1: Matching sessions")
    transcript_1 = "P:/.claude/sessions/session_current_789.jsonl"
    is_owned, handoff, current = check_session_ownership(transcript_1)
    print(format_session_message(is_owned, handoff, current, "test_task"))
    print()

    # Scenario 2: Mismatched sessions (should skip handoff creation)
    print("Scenario 2: Mismatched sessions (stale handoff)")
    transcript_2 = "P:/.claude/sessions/session_stale_123.jsonl"
    is_owned, handoff, current = check_session_ownership(transcript_2)
    print(format_session_message(is_owned, handoff, current, "test_task"))
    print()

    # Scenario 3: No current session (should create handoff - edge case)
    print("Scenario 3: No current session (edge case)")
    # Create a temporary empty current_session.json for testing
    test_file = Path("/tmp/test_current_session.json")
    test_file.write_text("{}")
    is_owned, handoff, current = check_session_ownership(
        "P:/.claude/sessions/session_abc.jsonl",
        current_session_file=test_file
    )
    print(format_session_message(is_owned, handoff, current, "test_task"))
    test_file.unlink()
    print()

    print("=" * 70)
    print("Test complete")
    print("=" * 70)
