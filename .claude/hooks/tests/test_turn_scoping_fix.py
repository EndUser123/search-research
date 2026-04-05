#!/usr/bin/env python3
"""Test TASK-013 turn scoping fix."""

import json
import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

def test_turn_marker_writer():
    """Test that start_turn writes turn marker with actual event_id."""
    print("Testing turn marker writer...")

    try:
        from __lib.hook_ledger import _safe_scope_key, start_turn

        # Create a test turn
        session_id = "test-session-123"
        terminal_id = "test-terminal-456"

        # Clean up any existing marker
        STATE_DIR = Path("P:/.claude/state")
        STATE_DIR_TURN_MARKERS = STATE_DIR / "turn_markers"
        STATE_DIR_TURN_MARKERS.mkdir(parents=True, exist_ok=True)

        scope_key = _safe_scope_key(session_id, terminal_id)
        marker_path = STATE_DIR_TURN_MARKERS / f"turn_start_{scope_key}.json"

        # Remove old marker if exists
        if marker_path.exists():
            marker_path.unlink()

        # Start a turn
        turn_id = start_turn(
            terminal_id=terminal_id,
            prompt="Test prompt",
            session_id=session_id
        )

        # Check that turn marker file was created
        if not marker_path.exists():
            print("  ✗ Turn marker file not created")
            return False

        # Read and verify marker file
        with open(marker_path, encoding="utf-8") as f:
            marker_data = json.load(f)

        event_id = marker_data.get("turn_start_event_id")

        if event_id is None:
            print("  ✗ turn_start_event_id is None")
            return False

        if event_id == 0:
            print("  ✗ turn_start_event_id is 0 (not fixed)")
            return False

        if event_id > 0:
            print(f"  ✓ Turn marker created with event_id={event_id}")
            return True

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def test_turn_scoping_filter():
    """Test that load_tool_events_for_context filters by turn marker."""
    print("\nTesting turn scoping filter...")

    try:
        from evidence_store import load_tool_events_for_context

        session_id = "test-session-789"
        terminal_id = "test-terminal-012"

        # Test 1: Without turn scoping (should return all events)
        print("  Test 1: Without turn scoping")
        events_all = load_tool_events_for_context(
            session_id=session_id,
            terminal_id=terminal_id,
            use_turn_scoping=False
        )
        print(f"    Events (no scoping): {len(events_all)}")

        # Test 2: With turn scoping enabled (should filter to current turn)
        print("  Test 2: With turn scoping enabled")
        events_turn = load_tool_events_for_context(
            session_id=session_id,
            terminal_id=terminal_id,
            use_turn_scoping=True
        )
        print(f"    Events (turn scoping): {len(events_turn)}")

        # Verify that turn-scoped results are subset of all results
        all_ids = {e["id"] for e in events_all}
        turn_ids = {e["id"] for e in events_turn}

        if turn_ids.issubset(all_ids):
            print("  ✓ Turn-scoped events are subset of all events")
        else:
            print("  ✗ Turn-scoped events contain IDs not in all events")
            return False

        # If turn marker exists and has valid event_id, verify filtering
        STATE_DIR = Path("P:/.claude/state")
        STATE_DIR_TURN_MARKERS = STATE_DIR / "turn_markers"

        import re
        def _safe(s: str) -> str:
            return re.sub(r"[^a-zA-Z0-9_.-]", "_", (s or "unknown").strip())
        scope_key = f"{_safe(session_id)}__{_safe(terminal_id)}"
        marker_path = STATE_DIR_TURN_MARKERS / f"turn_start_{scope_key}.json"

        if marker_path.exists():
            with open(marker_path, encoding="utf-8") as f:
                marker_data = json.load(f)
            turn_start_event_id = marker_data.get("turn_start_event_id", 0)

            if turn_start_event_id > 0:
                # All returned events should have id > turn_start_event_id
                for event in events_turn:
                    if event["id"] <= turn_start_event_id:
                        print(f"  ✗ Event {event['id']} <= turn_start_event_id ({turn_start_event_id})")
                        return False

                print(f"  ✓ All events filtered correctly (id > {turn_start_event_id})")

        print("  ✓ Turn scoping filter works")
        return True

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("TASK-013 Turn Scoping Fix Tests")
    print("=" * 60)

    all_passed = True

    all_passed &= test_turn_marker_writer()
    all_passed &= test_turn_scoping_filter()

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL TESTS PASSED - TASK-013 complete")
    else:
        print("✗ SOME TESTS FAILED - review errors above")
    print("=" * 60)

    sys.exit(0 if all_passed else 1)
