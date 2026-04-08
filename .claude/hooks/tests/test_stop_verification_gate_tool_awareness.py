#!/usr/bin/env python3
"""
Test turn-scoped tool event awareness in Stop_verification_gate.py

Tests the fix for BEHAV-002-A infinite loop:
- With no verification tools: BEHAV-002-A should still fire
- With verification tools this turn: BEHAV-002-A should NOT fire
"""

import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import stop.Stop_verification_gate as gate_module

check_response_violations = gate_module.check_response_violations


def test_behav_002a_fires_without_verification_tools():
    """BEHAV-002-A should fire when implementation claim exists but no verification tools used."""
    response = "This feature is NOT implemented yet. We need to add it."

    result = check_response_violations(
        response,
        hypothesis_details=[],
        single_root_cause=False,
        session_id="test_session",
        terminal_id="test_terminal",
    )

    # Should have BEHAV-002-A violation
    assert "BEHAV-002-A" in str(result["violations"]), \
        f"Expected BEHAV-002-A violation, got: {result['violations']}"
    print("✓ BEHAV-002-A fires without verification tools")


def test_behav_002a_suppressed_with_read_tool():
    """BEHAV-002-A should NOT fire when Read tool was used this turn."""
    original_loader = gate_module.load_turn_scoped_events

    def mock_load_events(*, session_id, terminal_id, limit):
        assert session_id == "test_session"
        assert terminal_id == "test_terminal"
        assert limit == 200
        return [{"id": 101, "name": "Read", "command": "Read file.py"}]

    gate_module.load_turn_scoped_events = mock_load_events

    try:
        response = "Code analysis shows feature X is NOT implemented in the current codebase."

        result = check_response_violations(
            response,
            hypothesis_details=[],
            single_root_cause=False,
            session_id="test_session",
            terminal_id="test_terminal",
        )

        assert "BEHAV-002-A" not in str(result["violations"]), \
            f"BEHAV-002-A should not fire when Read was used, got: {result['violations']}"
        print("✓ BEHAV-002-A suppressed when Read tool used")

    finally:
        gate_module.load_turn_scoped_events = original_loader


def test_behav_002a_suppressed_with_grep_tool():
    """BEHAV-002-A should NOT fire when Grep tool was used this turn."""
    original_loader = gate_module.load_turn_scoped_events

    def mock_load_events(*, session_id, terminal_id, limit):
        assert session_id == "test_session"
        assert terminal_id == "test_terminal"
        assert limit == 200
        return [{"id": 101, "name": "Grep", "command": "grep pattern"}]

    gate_module.load_turn_scoped_events = mock_load_events

    try:
        response = "Search results indicate this is fully implemented."

        result = check_response_violations(
            response,
            hypothesis_details=[],
            single_root_cause=False,
            session_id="test_session",
            terminal_id="test_terminal",
        )

        assert "BEHAV-002-A" not in str(result["violations"]), \
            f"BEHAV-002-A should not fire when Grep was used, got: {result['violations']}"
        print("✓ BEHAV-002-A suppressed when Grep tool used")

    finally:
        gate_module.load_turn_scoped_events = original_loader


def test_behav_002a_fires_with_non_verification_tools():
    """BEHAV-002-A should fire when only non-verification tools were used."""
    original_loader = gate_module.load_turn_scoped_events

    def mock_load_events(*, session_id, terminal_id, limit):
        assert session_id == "test_session"
        assert terminal_id == "test_terminal"
        assert limit == 200
        return [{"id": 101, "name": "Write", "command": "Write file.py"}]

    gate_module.load_turn_scoped_events = mock_load_events

    try:
        response = "This is NOT implemented."

        result = check_response_violations(
            response,
            hypothesis_details=[],
            single_root_cause=False,
            session_id="test_session",
            terminal_id="test_terminal",
        )

        assert "BEHAV-002-A" in str(result["violations"]), \
            f"BEHAV-002-A should fire with non-verification tools, got: {result['violations']}"
        print("✓ BEHAV-002-A fires with non-verification tools only")

    finally:
        gate_module.load_turn_scoped_events = original_loader


def test_other_violations_unaffected():
    """Other BEHAV violations should not be affected by tool awareness."""
    response = "I think the problem is X. Let's fix it."

    result = check_response_violations(
        response,
        hypothesis_details=[],
        single_root_cause=False,
        session_id="",
        terminal_id="",
    )

    # Should have BEHAV-001 or BEHAV-003 for premature solution jump
    violations_str = str(result["violations"])
    has_expected_violation = any(v in violations_str for v in ["BEHAV-001", "BEHAV-003"])
    assert has_expected_violation, f"Expected other violations to still work, got: {result['violations']}"
    print("✓ Other violations unaffected by tool awareness")


def test_no_implementation_claim_no_violation():
    """No BEHAV-002-A violation when no implementation claim exists."""
    response = "Here is some analysis without any implementation status claims."

    result = check_response_violations(
        response,
        hypothesis_details=[],
        single_root_cause=False,
        session_id="test_session",
        terminal_id="test_terminal",
    )

    assert "BEHAV-002-A" not in str(result["violations"]), \
        f"BEHAV-002-A should not fire without implementation claim, got: {result['violations']}"
    print("✓ No violation without implementation claim")


if __name__ == "__main__":
    print("Running BEHAV-002-A tool awareness tests...\n")

    test_behav_002a_fires_without_verification_tools()
    test_behav_002a_suppressed_with_read_tool()
    test_behav_002a_suppressed_with_grep_tool()
    test_behav_002a_fires_with_non_verification_tools()
    test_other_violations_unaffected()
    test_no_implementation_claim_no_violation()

    print("\n✅ All tests passed!")
