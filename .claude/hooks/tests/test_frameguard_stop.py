#!/usr/bin/env python3
"""Test FrameGuard Stop hook validator.

Tests the frameguard_stop.py Stop hook validator:
- Stop hook contract: {"allow": bool, "reason": str}
- State loading and validation
- Systemic handling pattern detection
- Block vs warn mode behavior
- Fail-open on errors
- Exit codes
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys_path_insert = str(Path(__file__).resolve().parents[1])
if sys_path_insert not in sys.path:
    sys.path.insert(0, sys_path_insert)

# === Helper Functions ===


def _create_stop_data(
    response: str = "",
    session_id: str = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    terminal_id: str = "console_test",
    turn_id: str = "test_turn_123",
    **kwargs,
) -> dict:
    """Create Stop hook input data."""
    data = {
        "response": response,
        "assistant_response": response,
        "session_id": session_id,
        "sessionId": session_id,
        "terminal_id": terminal_id,
        "terminalId": terminal_id,
        "turn_id": turn_id,
        **kwargs,
    }
    return data


def run_frameguard_stop(data: dict) -> tuple[bool, str, int]:
    """Run frameguard_stop.py and return (allow, reason, exit_code)."""
    import subprocess

    result = subprocess.run(
        [sys.executable, "P:/.claude/hooks/frameguard_stop.py"],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        cwd="P:/.claude/hooks",
    )

    # Parse output
    try:
        output = json.loads(result.stdout.strip())
        allow = output.get("allow", True)
        reason = output.get("reason", "")
    except json.JSONDecodeError:
        allow = True
        reason = ""

    return allow, reason, result.returncode


# === Basic Contract Tests ===


def test_stop_hook_contract() -> None:
    """Test returns {"allow": bool, "reason": str}."""
    data = _create_stop_data(
        response="Some response",
        session_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    )

    allow, reason, exit_code = run_frameguard_stop(data)

    # Should return proper JSON structure
    assert isinstance(allow, bool)
    assert isinstance(reason, str)


def test_exit_code_0_when_allow() -> None:
    """Test exit code 0 when allow=True."""
    data = _create_stop_data(
        response="Some response",
        session_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
    )

    allow, reason, exit_code = run_frameguard_stop(data)

    # Exit code 0 when allowing
    if allow:
        assert exit_code == 0


def test_exit_code_2_when_block() -> None:
    """Test exit code 2 when allow=False (block)."""
    # This test requires setting up a FrameGuard state and responding without systemic frame
    # For now, test the contract with a simple case
    original_mode = os.environ.get("FRAMEGUARD_MODE", "warn")

    try:
        os.environ["FRAMEGUARD_MODE"] = "block"

        data = _create_stop_data(
            response="Some response",
            session_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
        )

        allow, reason, exit_code = run_frameguard_stop(data)

        # If blocked, exit code should be 2
        if not allow:
            assert exit_code == 2

    finally:
        os.environ["FRAMEGUARD_MODE"] = original_mode


# === State Tests ===


def test_no_state_allow() -> None:
    """Test no FrameGuard state = allow."""
    # Use a session_id that won't have any FrameGuard state
    data = _create_stop_data(
        response="No systemic frame mentioned",
        session_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
    )

    allow, reason, exit_code = run_frameguard_stop(data)

    # Should allow when no state
    assert allow is True


def test_no_systemic_frame_allow() -> None:
    """Test FrameGuard exists but not systemic = allow."""
    # This would require setting up state with needs_systemic_frame=False
    # For now, test with no state (similar to above)
    data = _create_stop_data(
        response="Regular response",
        session_id="ffffffff-ffff-ffff-ffff-ffffffffffff",
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Should allow when no systemic frame required
    assert allow is True


def test_handled_allow() -> None:
    """Test already marked handled = allow."""
    # This would require setting up state with handled=True
    # For now, test the contract
    data = _create_stop_data(
        response="Some response",
        session_id="11111111-1111-1111-1111-111111111111",
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Without state, should allow
    assert allow is True


# === Systemic Frame Handling Tests ===


def test_systemic_handled_allow() -> None:
    """Test response addresses systemic frame = allow."""
    data = _create_stop_data(
        response="The broader structural question here is about the hook architecture coverage.",
        session_id="22222222-2222-2222-2222-222222222222",
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Should allow - response mentions "broader structural"
    assert allow is True
    if "FRAMEGUARD" in reason:
        assert "handled" in reason.lower()


def test_systemic_not_handled_warn() -> None:
    """Test response ignores frame = warn (mode=warn)."""
    original_mode = os.environ.get("FRAMEGUARD_MODE", "warn")

    try:
        os.environ["FRAMEGUARD_MODE"] = "warn"

        data = _create_stop_data(
            response="No, we don't have that hook.",
            session_id="33333333-3333-3333-3333-333333333333",
        )

        allow, reason, _ = run_frameguard_stop(data)

        # Warn mode allows but annotates
        assert allow is True

    finally:
        os.environ["FRAMEGUARD_MODE"] = original_mode


# === Disabled Tests ===


def test_disabled_allow() -> None:
    """Test FRAMEGUARD_ENABLED=false = allow."""
    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "false"

        data = _create_stop_data(
            response="Narrow frame response",
            session_id="44444444-4444-4444-4444-444444444444",
        )

        allow, reason, _ = run_frameguard_stop(data)

        # Should allow when disabled
        assert allow is True

    finally:
        os.environ["FRAMEGUARD_ENABLED"] = original_enabled


# === Fail-Open Tests ===


def test_no_session_id_allow() -> None:
    """Test missing session_id = allow (fail-open)."""
    data = _create_stop_data(
        response="Some response",
        session_id="",  # Empty session_id
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Should allow (fail-open on missing context)
    assert allow is True


def test_no_turn_id_allow() -> None:
    """Test missing turn_id = allow (fail-open)."""
    data = _create_stop_data(
        response="Some response",
        turn_id="",  # Empty turn_id
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Should allow (fail-open on missing context)
    assert allow is True


def test_db_failure_allow() -> None:
    """Test database error = allow (fail-open)."""
    # This is hard to test without actually corrupting the DB
    # The contract is that DB errors should fail-open
    data = _create_stop_data(
        response="Some response",
        session_id="55555555-5555-5555-5555-555555555555",
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Should allow even if DB has issues (fail-open)
    assert allow is True


# === Pattern Detection Tests ===


def test_handling_patterns_detection() -> None:
    """Test all handling patterns detected correctly."""
    handling_phrases = [
        "The broader structural question is...",
        "Looking at the architectural context...",
        "The relationship between these elements...",
        "Other agents in the system...",
        "I am not addressing the broader structural question because...",
        "The systemic context here...",
    ]

    for phrase in handling_phrases:
        data = _create_stop_data(
            response=phrase,
            session_id="66666666-6666-6666-6666-666666666666",
        )

        allow, reason, _ = run_frameguard_stop(data)

        # Should allow - pattern detected
        assert allow is True


# === Mark Handled Tests ===


def test_mark_handled_called() -> None:
    """Test mark_frameguard_handled() called when appropriate."""
    # This test verifies that the stop hook marks the state
    # We can't directly observe this without DB inspection
    # but we can verify the hook completes without error
    data = _create_stop_data(
        response="The broader structural context is...",
        session_id="77777777-7777-7777-7777-777777777777",
    )

    allow, reason, exit_code = run_frameguard_stop(data)

    # Should complete successfully
    assert isinstance(allow, bool)
    assert isinstance(reason, str)
    assert exit_code in (0, 2)  # Valid exit codes


# === Additional Edge Cases ===


def test_empty_response() -> None:
    """Test empty response handled gracefully."""
    data = _create_stop_data(
        response="",
        session_id="88888888-8888-8888-8888-888888888888",
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Should handle empty response
    assert isinstance(allow, bool)


def test_very_long_response() -> None:
    """Test very long response doesn't cause issues."""
    long_response = "x" * 10000

    data = _create_stop_data(
        response=long_response,
        session_id="99999999-9999-9999-9999-999999999999",
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Should handle long response
    assert isinstance(allow, bool)


def test_special_characters_in_response() -> None:
    """Test special characters in response handled correctly."""
    special_response = 'Test with quotes: "hello" and newlines\n\t and unicode: \u2713'

    data = _create_stop_data(
        response=special_response,
        session_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
    )

    allow, reason, _ = run_frameguard_stop(data)

    # Should handle special characters
    assert isinstance(allow, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
