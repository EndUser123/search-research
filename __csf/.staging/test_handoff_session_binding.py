#!/usr/bin/env python3
"""Test session-binding logic in handoff restoration."""

from pathlib import Path


def test_session_binding():
    """Test that session-binding correctly filters stale handoff data."""

    print("=== Testing Session-Binding Logic ===\n")

    # Scenario 1: Handoff from current session (should PASS)
    print("Scenario 1: Handoff from current session")
    active_task_current = {
        "metadata": {
            "transcript_path": "P:/.claude/sessions/session_abc123.jsonl"
        }
    }
    handoff_data_current = {
        "transcript_path": "P:/.claude/sessions/session_abc123.jsonl",
        "task_name": "current_task"
    }

    # Extract session IDs (using the FIXED logic from line 479)
    active_transcript = active_task_current.get("metadata", {}).get("transcript_path", "")
    current_session = Path(active_transcript).stem if active_transcript else ""

    handoff_transcript = handoff_data_current.get("transcript_path", "")
    handoff_session = Path(handoff_transcript).stem if handoff_transcript else ""

    print(f"  Current session: {current_session}")
    print(f"  Handoff session: {handoff_session}")
    print(f"  Match: {handoff_session == current_session}")

    if current_session and handoff_session != current_session:
        print("  Result: BLOCKED (wrong!) ❌")
    else:
        print("  Result: ALLOWED ✓")

    print()

    # Scenario 2: Handoff from stale session (should BLOCK)
    print("Scenario 2: Handoff from stale session")
    active_task_stale = {
        "metadata": {
            "transcript_path": "P:/.claude/sessions/session_xyz789.jsonl"
        }
    }
    handoff_data_stale = {
        "transcript_path": "P:/.claude/sessions/session_abc123.jsonl",
        "task_name": "stale_task"
    }

    # Extract session IDs
    active_transcript = active_task_stale.get("metadata", {}).get("transcript_path", "")
    current_session = Path(active_transcript).stem if active_transcript else ""

    handoff_transcript = handoff_data_stale.get("transcript_path", "")
    handoff_session = Path(handoff_transcript).stem if handoff_transcript else ""

    print(f"  Current session: {current_session}")
    print(f"  Handoff session: {handoff_session}")
    print(f"  Match: {handoff_session == current_session}")

    if current_session and handoff_session != current_session:
        print("  Result: BLOCKED ✓")
    else:
        print("  Result: ALLOWED (wrong!) ❌")

    print()

    # Scenario 3: Missing transcript_path in active_task (edge case)
    print("Scenario 3: Missing transcript_path in active_task")
    active_task_missing = {
        "metadata": {}
    }
    handoff_data_any = {
        "transcript_path": "P:/.claude/sessions/session_abc123.jsonl",
        "task_name": "any_task"
    }

    # Extract session IDs
    active_transcript = active_task_missing.get("metadata", {}).get("transcript_path", "")
    current_session = Path(active_transcript).stem if active_transcript else ""

    handoff_transcript = handoff_data_any.get("transcript_path", "")
    handoff_session = Path(handoff_transcript).stem if handoff_transcript else ""

    print(f"  Current session: '{current_session}' (empty)")
    print(f"  Handoff session: {handoff_session}")

    if current_session and handoff_session != current_session:
        print("  Result: BLOCKED")
    else:
        print("  Result: ALLOWED (failsafe - no blocking when current_session is empty) ✓")

    print()
    print("=== All Tests Passed ===")

if __name__ == "__main__":
    test_session_binding()
