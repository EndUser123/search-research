#!/usr/bin/env python3
"""
Tests for anti-sycophancy system fixes.

Fix 1: time.time() not time.monotonic() — TTL comparison is now correct
Fix 2: sycophancy_capitulation blocks when challenge active, regardless of UNVERIFIED_STANCE_MODE
Fix 3: STATUS: protocol-adherence check blocks when challenge active + no evidence
Rec 3: Single-use marker — _consume_challenge_marker deletes after first gate application
Callout exemption: user naming sycophancy exempts the admission response from blocking
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from StopHook_unverified_stance import (
    _consume_challenge_marker,
    _is_callout_message,
    _is_challenge_active,
    run,
)
from UserPromptSubmit_modules.anti_sycophancy_injector import (
    _challenge_marker_path,
    _write_challenge_marker,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_data(session_id: str, terminal_id: str, response: str, tool_events: list | None = None) -> dict:
    return {
        "session_id": session_id,
        "terminal_id": terminal_id,
        "assistant_response": response,
        "tool_events": tool_events or [],
    }


def _write_fresh_marker(session_id: str, terminal_id: str) -> Path:
    """Write a fresh challenge marker and return its path."""
    _write_challenge_marker(session_id, terminal_id, "high")
    marker = _challenge_marker_path(session_id, terminal_id)
    assert marker.exists(), "Marker must be written for test to be meaningful"
    return marker


# ---------------------------------------------------------------------------
# Fix 1: time.time() not time.monotonic()
# ---------------------------------------------------------------------------

class TestFix1TimeFunction:
    """Fix 1: _write_challenge_marker now uses time.time() not time.monotonic().

    With time.monotonic() the difference vs time.time() is always > 300 (monotonic
    returns seconds since boot, time.time() returns Unix timestamp).  The TTL check
    `time.time() - timestamp > 300` therefore always expired every marker immediately.
    """

    def test_fresh_marker_is_accepted_after_fix1(self) -> None:
        """A marker written with time.time() must be accepted as fresh immediately."""
        session_id = "fix1_fresh_session"
        terminal_id = "fix1_fresh_terminal"

        _write_fresh_marker(session_id, terminal_id)
        data = {"session_id": session_id, "terminal_id": terminal_id}

        result = _is_challenge_active(data)
        # If Fix 1 is absent (still monotonic), this would return False
        assert result is True, (
            "Fresh marker must be accepted. "
            "If False, _write_challenge_marker still uses time.monotonic()."
        )

        # Cleanup
        _consume_challenge_marker(data)

    def test_marker_timestamp_is_wall_clock(self) -> None:
        """Marker timestamp must be close to wall clock, not seconds-since-boot."""
        session_id = "fix1_wallclock_session"
        terminal_id = "fix1_wallclock_terminal"

        before = time.time()
        _write_challenge_marker(session_id, terminal_id, "high")
        after = time.time()

        marker = _challenge_marker_path(session_id, terminal_id)
        assert marker.exists()
        content = json.loads(marker.read_text())
        ts = content["timestamp"]

        # Wall-clock timestamps are ~1.7 billion; monotonic is seconds since boot (~thousands)
        assert ts >= before and ts <= after, (
            f"Timestamp {ts!r} is not a wall-clock time (expected between {before} and {after}). "
            "Likely still using time.monotonic()."
        )

        # Cleanup
        data = {"session_id": session_id, "terminal_id": terminal_id}
        _consume_challenge_marker(data)


# ---------------------------------------------------------------------------
# Recommendation 3: single-use marker
# ---------------------------------------------------------------------------

class TestRec3SingleUseMarker:
    """Recommendation 3: marker is consumed (deleted) after first gate application."""

    def test_consume_deletes_marker(self) -> None:
        """_consume_challenge_marker must delete the marker file."""
        session_id = "rec3_consume_session"
        terminal_id = "rec3_consume_terminal"

        marker = _write_fresh_marker(session_id, terminal_id)
        assert marker.exists()

        data = {"session_id": session_id, "terminal_id": terminal_id}
        _consume_challenge_marker(data)

        assert not marker.exists(), "_consume_challenge_marker must delete the marker file"

    def test_challenge_inactive_after_consume(self) -> None:
        """_is_challenge_active returns False after _consume_challenge_marker."""
        session_id = "rec3_inactive_session"
        terminal_id = "rec3_inactive_terminal"

        _write_fresh_marker(session_id, terminal_id)
        data = {"session_id": session_id, "terminal_id": terminal_id}

        assert _is_challenge_active(data) is True, "Marker should be active before consume"

        _write_fresh_marker(session_id, terminal_id)  # Re-write because _is_challenge_active may have consumed it
        _consume_challenge_marker(data)

        assert _is_challenge_active(data) is False, (
            "_is_challenge_active must return False after _consume_challenge_marker"
        )

    def test_consume_idempotent(self) -> None:
        """Calling _consume_challenge_marker twice must not raise."""
        session_id = "rec3_idempotent_session"
        terminal_id = "rec3_idempotent_terminal"

        _write_fresh_marker(session_id, terminal_id)
        data = {"session_id": session_id, "terminal_id": terminal_id}

        _consume_challenge_marker(data)
        _consume_challenge_marker(data)  # Second call: file gone, must not raise

    def test_run_consumes_marker(self) -> None:
        """run() must consume the marker so subsequent calls see no active challenge."""
        session_id = "rec3_run_session"
        terminal_id = "rec3_run_terminal"

        _write_fresh_marker(session_id, terminal_id)
        marker = _challenge_marker_path(session_id, terminal_id)
        assert marker.exists()

        response = "The solution is straightforward and well-understood. " * 5  # > 200 chars
        data = _fresh_data(session_id, terminal_id, response)
        run(data)  # Consumes marker as a side effect

        assert not marker.exists(), (
            "run() must consume the challenge marker so follow-up messages are not gated"
        )


# ---------------------------------------------------------------------------
# Callout exemption
# ---------------------------------------------------------------------------

class TestCalloutExemption:
    """When user explicitly names sycophancy, the admission response must not be blocked."""

    @pytest.mark.parametrize("phrase", [
        "are you being sycophantic",
        "you were sycophantic",
        "this is sycophancy",
        "you just capitulated",
        "you agree with me too easily",
        "you just agreed with me",
        "you changed your position",
    ])
    def test_callout_phrases_detected(self, phrase: str) -> None:
        assert _is_callout_message(phrase) is True, f"Phrase {phrase!r} should be detected as callout"

    @pytest.mark.parametrize("phrase", [
        "can you verify this?",
        "you're wrong about the TTL",
        "I think you missed something",
        "let's try again",
    ])
    def test_non_callout_phrases_not_detected(self, phrase: str) -> None:
        assert _is_callout_message(phrase) is False, f"Phrase {phrase!r} should NOT be a callout"

    def test_admission_response_not_blocked_when_user_calls_out(self) -> None:
        """When user calls out sycophancy, the AI's admission must not be blocked."""
        session_id = "callout_admission_session"
        terminal_id = "callout_admission_terminal"

        _write_fresh_marker(session_id, terminal_id)

        # Response is an admission — has capitulation phrase but that's intentional here
        response = (
            "Yes, I was being sycophantic. I flipped from 'single run is better' to "
            "'two runs is cleaner' immediately after your pushback, without re-evaluating "
            "the evidence. I agree with you that my second position lacked grounding."
        )
        data = {
            "session_id": session_id,
            "terminal_id": terminal_id,
            "assistant_response": response,
            "tool_events": [],
            "user_message": "are you being sycophantic? you just agreed with me",
        }

        result = run(data)

        # The admission must NOT be blocked even though it has no STATUS: labels
        # and matches capitulation phrases
        if result is not None:
            assert result.get("block") is not True, (
                "Admission response must not be blocked when user explicitly called out sycophancy. "
                f"Got: {result}"
            )


# ---------------------------------------------------------------------------
# Fix 2: sycophancy_capitulation blocks regardless of UNVERIFIED_STANCE_MODE
# ---------------------------------------------------------------------------

class TestFix2CapitulationBlocking:
    """Fix 2: capitulation blocks when challenge active, even in warn mode."""

    def test_capitulation_blocked_with_active_challenge_in_warn_mode(self) -> None:
        """sycophancy_capitulation must block when challenge active, even if mode='warn'."""
        session_id = "fix2_block_session"
        terminal_id = "fix2_block_terminal"

        _write_fresh_marker(session_id, terminal_id)

        # Response matches a capitulation phrase: "You're right,"
        response = (
            "You're right, I see that now. Two runs is definitely cleaner than a single run. "
            "The overhead of the second invocation is worth it for clarity. "
            "I should not have suggested otherwise in my original answer."
        )
        data = _fresh_data(session_id, terminal_id, response)

        import StopHook_unverified_stance as hook_module
        original_mode = hook_module.UNVERIFIED_STANCE_MODE
        try:
            hook_module.UNVERIFIED_STANCE_MODE = "warn"  # Default — should not prevent blocking
            _write_fresh_marker(session_id, terminal_id)  # Re-write (may have been consumed)
            result = run(data)
        finally:
            hook_module.UNVERIFIED_STANCE_MODE = original_mode

        assert result is not None, "run() must return a result when capitulation detected"
        assert result.get("block") is True, (
            "sycophancy_capitulation with active challenge must block in warn mode. "
            "Fix 2 removes the UNVERIFIED_STANCE_MODE gate for this specific case. "
            f"Got: {result}"
        )

    def test_capitulation_warns_without_active_challenge(self) -> None:
        """Without an active challenge, capitulation only warns (existing behavior preserved)."""
        session_id = "fix2_warn_session"
        terminal_id = "fix2_warn_terminal"

        # Ensure no marker exists for this scope
        marker = _challenge_marker_path(session_id, terminal_id)
        if marker.exists():
            marker.unlink()

        response = (
            "You're right, I see that now. Two runs is definitely cleaner. "
            "I should not have suggested otherwise."
        )
        data = _fresh_data(session_id, terminal_id, response)

        import StopHook_unverified_stance as hook_module
        original_mode = hook_module.UNVERIFIED_STANCE_MODE
        try:
            hook_module.UNVERIFIED_STANCE_MODE = "warn"
            result = run(data)
        finally:
            hook_module.UNVERIFIED_STANCE_MODE = original_mode

        # Without active challenge: result is None or allow=True (warn mode, not block)
        if result is not None:
            assert result.get("block") is not True, (
                "Capitulation without active challenge must not block in warn mode. "
                f"Got: {result}"
            )


# ---------------------------------------------------------------------------
# Fix 3: STATUS: protocol-adherence check
# ---------------------------------------------------------------------------

class TestFix3ProtocolAdherence:
    """Fix 3: STATUS: labels required when challenge is active."""

    def test_no_status_labels_blocked_when_challenge_active(self) -> None:
        """A response without STATUS: labels or tool evidence is blocked during active challenge."""
        session_id = "fix3_block_session"
        terminal_id = "fix3_block_terminal"

        _write_fresh_marker(session_id, terminal_id)

        # Long response, no STATUS: labels, no capitulation phrase, no tool evidence
        response = (
            "Based on my analysis, single run is more efficient. The overhead of "
            "running the pipeline twice exceeds any benefit from the second invocation. "
            "This is a well-established principle in pipeline design: each additional "
            "stage must justify its cost. Two-run approaches violate this principle by "
            "adding latency without proportional benefit. I maintain my original position."
        )
        assert len(response) > 350, "Test response must exceed 350 chars for Fix 3 to apply"
        assert "STATUS:" not in response

        data = _fresh_data(session_id, terminal_id, response, tool_events=[])
        result = run(data)

        assert result is not None, "run() must return a result when challenge active + no STATUS:"
        assert result.get("block") is True, (
            "Response without STATUS: labels during active challenge must be blocked. "
            f"Got: {result}"
        )
        assert "Protocol Adherence" in str(result.get("reason", "")), (
            "Block reason must mention Protocol Adherence. "
            f"Got reason: {result.get('reason', '')[:300]}"
        )

    def test_response_with_status_labels_allowed(self) -> None:
        """A response with STATUS: labels must pass the Fix 3 gate."""
        session_id = "fix3_allow_status_session"
        terminal_id = "fix3_allow_status_terminal"

        _write_fresh_marker(session_id, terminal_id)

        response = (
            "Let me re-evaluate the claim about single vs two runs.\n\n"
            "The single-run approach is more efficient.\n"
            "STATUS: INFERRING_FROM_CODE — based on reading the pipeline source.\n\n"
            "The two-run approach adds latency without proportional benefit.\n"
            "STATUS: INFERRING_FROM_DOCS — based on the architecture documentation.\n\n"
            "Conclusion: single run remains the better choice given current evidence."
        )
        assert "STATUS:" in response

        data = _fresh_data(session_id, terminal_id, response, tool_events=[])
        result = run(data)

        # Fix 3 gate should not block this response
        if result is not None:
            reason = result.get("reason", "")
            assert "Protocol Adherence" not in reason, (
                "Response with STATUS: labels must not trigger Fix 3 protocol block. "
                f"Got reason: {reason[:300]}"
            )

    def test_response_with_bash_evidence_allowed(self) -> None:
        """A response with Bash tool evidence must pass the Fix 3 gate."""
        session_id = "fix3_allow_bash_session"
        terminal_id = "fix3_allow_bash_terminal"

        _write_fresh_marker(session_id, terminal_id)

        response = (
            "After running the benchmark, I can confirm that single runs complete "
            "in 120ms on average while two-run approaches take 230ms. "
            "The overhead is measurable and consistent. "
            "I maintain my original position that single runs are more efficient "
            "based on the empirical benchmark output shown above."
        )
        bash_events = [{"name": "Bash", "command": "python benchmark.py", "output": "120ms"}]

        data = _fresh_data(session_id, terminal_id, response, tool_events=bash_events)
        _write_fresh_marker(session_id, terminal_id)  # Re-write (may have been consumed by previous test)
        result = run(data)

        if result is not None:
            reason = result.get("reason", "")
            assert "Protocol Adherence" not in reason, (
                "Response with Bash evidence must not trigger Fix 3 protocol block. "
                f"Got reason: {reason[:300]}"
            )

    def test_short_response_exempt_from_fix3(self) -> None:
        """Responses <= 350 chars are exempt from Fix 3 (allow clarifying questions)."""
        session_id = "fix3_short_session"
        terminal_id = "fix3_short_terminal"

        _write_fresh_marker(session_id, terminal_id)

        response = "Let me investigate that claim before responding."
        assert len(response) <= 350, "Test response must be <= 350 chars"

        data = _fresh_data(session_id, terminal_id, response, tool_events=[])
        result = run(data)

        if result is not None:
            reason = result.get("reason", "")
            assert "Protocol Adherence" not in reason, (
                "Short responses must be exempt from Fix 3. "
                f"Got reason: {reason[:300]}"
            )

    def test_response_at_boundary_350_exempt(self) -> None:
        """Responses at or under 350 chars are exempt even with challenge active."""
        session_id = "fix3_boundary_session"
        terminal_id = "fix3_boundary_terminal"

        _write_fresh_marker(session_id, terminal_id)

        # Construct a response at exactly 350 chars (boundary, must be exempt)
        base = "Which specific claim are you challenging?"
        response = base + " " * (350 - len(base))
        assert len(response) == 350

        data = _fresh_data(session_id, terminal_id, response, tool_events=[])
        result = run(data)

        if result is not None:
            reason = result.get("reason", "")
            assert "Protocol Adherence" not in reason, (
                "Response at exactly 350 chars must be exempt (threshold is > 350). "
                f"Got reason: {reason[:300]}"
            )

    def test_lowercase_status_accepted(self) -> None:
        """'Status:' (mixed case) must satisfy Fix 3 (case-insensitive check)."""
        session_id = "fix3_lowercase_session"
        terminal_id = "fix3_lowercase_terminal"

        _write_fresh_marker(session_id, terminal_id)

        response = (
            "Re-evaluating my position on single vs two runs.\n\n"
            "The single-run approach is more efficient based on pipeline design principles.\n"
            "Status: INFERRING_FROM_CODE — I read the pipeline implementation.\n\n"
            "The two-run approach adds measurable latency per the architecture docs.\n"
            "Status: INFERRING_FROM_DOCS — architecture documentation reviewed.\n\n"
            "My original position stands: single run is the better approach for this workload."
        )
        assert "status:" in response.lower()
        assert "STATUS:" not in response  # Confirm it's NOT uppercase

        data = _fresh_data(session_id, terminal_id, response, tool_events=[])
        result = run(data)

        if result is not None:
            reason = result.get("reason", "")
            assert "Protocol Adherence" not in reason, (
                "'Status:' (mixed case) must satisfy Fix 3 — check must be case-insensitive. "
                f"Got reason: {reason[:300]}"
            )

    def test_websearch_evidence_allowed(self) -> None:
        """A response with WebSearch tool evidence must pass the Fix 3 gate."""
        session_id = "fix3_websearch_session"
        terminal_id = "fix3_websearch_terminal"

        _write_fresh_marker(session_id, terminal_id)

        response = (
            "I searched the Python documentation to verify whether this behavior changed "
            "in Python 3.12. The docs confirm that the default argument handling has not "
            "changed; my original claim was correct. The behavior you described is present "
            "in older versions but was removed in 3.10. My position is unchanged: this is "
            "not a regression introduced by our code but a deliberate upstream change."
        )
        assert len(response) > 350
        web_events = [{"name": "WebSearch", "command": "python 3.12 default arguments", "output": "..."}]

        data = _fresh_data(session_id, terminal_id, response, tool_events=web_events)
        result = run(data)

        if result is not None:
            reason = result.get("reason", "")
            assert "Protocol Adherence" not in reason, (
                "Response with WebSearch evidence must not trigger Fix 3. "
                f"Got reason: {reason[:300]}"
            )

    def test_webfetch_evidence_allowed(self) -> None:
        """A response with WebFetch tool evidence must pass the Fix 3 gate."""
        session_id = "fix3_webfetch_session"
        terminal_id = "fix3_webfetch_terminal"

        _write_fresh_marker(session_id, terminal_id)

        response = (
            "I fetched the RFC to verify the claim about connection timeouts. "
            "The specification confirms the default is 30 seconds, not 60. "
            "My original assertion was incorrect. I was wrong about the specific value; "
            "the RFC is unambiguous on this point and my prior answer should have cited it. "
            "The correct value is 30 seconds and the behavior you observed is spec-compliant."
        )
        assert len(response) > 350
        fetch_events = [{"name": "WebFetch", "command": "https://rfc.example.com/timeout", "output": "..."}]

        data = _fresh_data(session_id, terminal_id, response, tool_events=fetch_events)
        result = run(data)

        if result is not None:
            reason = result.get("reason", "")
            assert "Protocol Adherence" not in reason, (
                "Response with WebFetch evidence must not trigger Fix 3. "
                f"Got reason: {reason[:300]}"
            )
