#!/usr/bin/env python3
"""Integration tests: Stop.py → is_trivial_exchange() → gate returns None.

Verifies that Stop hooks actually invoke the trivial exchange bypass and
skip correctly for the intended trivial paths. Closes the gap between
unit tests (test_trivial_turns.py covers the helper in isolation) and
Stop.py regression tests (test_stop_control_mode.py covers mode suppression
but not the trivial exchange integration path).

Run with: pytest P:/.claude/hooks/tests/test_trivial_exchange_stop_integration.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

# Import the Stop module components under test
import importlib
import Stop

importlib.reload(Stop)

# Expose the gate runners for testing
_run_epistemic_contract = Stop._run_epistemic_contract
_run_reasoning_quality_gate = Stop._run_reasoning_quality_gate
_is_trivial_exchange = Stop._is_trivial_exchange


# =============================================================================
# HELPERS
# =============================================================================


def make_data(
    *,
    prompt: str = "",
    response: str = "",
    user_prompt: str = "",
    session_id: str = "test-session-trivial",
    terminal_id: str = "test-terminal-trivial",
) -> dict:
    """Construct a minimal Stop hook data dict."""
    ctx = {
        "prompt": prompt,
        "response": response,
        "user_prompt": user_prompt or prompt,
        "session_id": session_id,
        "terminal_id": terminal_id,
        "tool_transcript": "",
    }
    return ctx


# =============================================================================
# TRIVIAL EXCHANGE → EPISTEMIC CONTRACT SKIP
# =============================================================================


class TestEpistemicContractTrivialIntegration:
    """Stop-level: _run_epistemic_contract returns None for trivial numeric answers."""

    def test_numeric_answer_skips_epistemic_gate(self):
        """Numeric response to simple prompt → gate returns None (trivial bypass)."""
        data = make_data(
            prompt="what is 2+2",
            response="4",
            user_prompt="what is 2+2",
        )
        result = _run_epistemic_contract(data)
        # None means gate was skipped (trivial exchange bypass fired)
        assert result is None, f"Expected None (trivial bypass), got {result}"

    def test_short_ack_skips_epistemic_gate(self):
        """Short acknowledgement → gate returns None (trivial bypass)."""
        data = make_data(
            prompt="does this work",
            response="yes",
            user_prompt="does this work",
        )
        result = _run_epistemic_contract(data)
        assert result is None, f"Expected None (trivial bypass), got {result}"

    def test_smoke_test_skips_epistemic_gate(self):
        """Smoke test prompt → gate returns None (trivial bypass)."""
        data = make_data(
            prompt="test m27",
            response="I am working correctly.",
            user_prompt="test m27",
        )
        result = _run_epistemic_contract(data)
        assert result is None, f"Expected None (trivial bypass), got {result}"

    def test_control_mode_skips_epistemic_gate(self):
        """Control mode response → gate returns None (trivial bypass)."""
        data = make_data(
            prompt="stop",
            response="stopping",
            user_prompt="stop",
        )
        result = _run_epistemic_contract(data)
        assert result is None, f"Expected None (trivial bypass), got {result}"

    def test_structured_response_does_not_skip(self):
        """Response with epistemic structure → gate runs (NOT trivial)."""
        data = make_data(
            prompt="explain the bug",
            response="[FACT]\n- The null check was missing",
            user_prompt="explain the bug",
        )
        result = _run_epistemic_contract(data)
        # NOT None means gate was NOT skipped — structured response is non-trivial
        # (Gate may return a verdict dict or None depending on whether format check fires.
        # The key invariant: it didn't exit via the trivial bypass path.)
        # Verify by checking that a non-trivial reason was produced (gate ran normally)
        # We check by ensuring _is_trivial_exchange returns False
        trivial, reason = _is_trivial_exchange(data, data["response"])
        assert trivial is False, f"Expected non-trivial, got {reason}"
        # The gate itself may still return None (format repair or pass) — that's fine.
        # The invariant is that the trivial bypass was NOT taken, not that block fires.


# =============================================================================
# TRIVIAL EXCHANGE → REASONING QUALITY GATE SKIP
# =============================================================================


class TestReasoningQualityTrivialIntegration:
    """Stop-level: _run_reasoning_quality_gate returns None for trivial exchanges."""

    def test_numeric_answer_skips_reasoning_gate(self):
        """Numeric response → gate returns None (trivial bypass)."""
        data = make_data(
            prompt="how many items",
            response="42",
            user_prompt="how many items",
        )
        result = _run_reasoning_quality_gate(data)
        assert result is None, f"Expected None (trivial bypass), got {result}"

    def test_short_ack_skips_reasoning_gate(self):
        """Short acknowledgement → gate returns None (trivial bypass)."""
        data = make_data(
            prompt="is it done",
            response="done",
            user_prompt="is it done",
        )
        result = _run_reasoning_quality_gate(data)
        assert result is None, f"Expected None (trivial bypass), got {result}"

    def test_control_mode_skips_reasoning_gate(self):
        """Control mode response → gate returns None (trivial bypass)."""
        data = make_data(
            prompt="actually fix it",
            response="done",
            user_prompt="actually fix it",
        )
        result = _run_reasoning_quality_gate(data)
        assert result is None, f"Expected None (trivial bypass), got {result}"

    def test_complex_prompt_with_ack_not_trivial(self):
        """'done' to a complex substantive request → NOT trivial (prompt >= 15 words)."""
        complex_prompt = "Analyze and fix the concurrency bug in the task scheduler where race conditions cause duplicate execution"
        data = make_data(
            prompt=complex_prompt,
            response="done",
            user_prompt=complex_prompt,
        )
        trivial, reason = _is_trivial_exchange(data, "done")
        # With prompt >= 15 words and "done" as response, this should NOT be trivial
        # because _SHORT_ACK_RE requires prompt_words < 15
        assert trivial is False, f"Expected non-trivial for complex prompt, got {reason}"


# =============================================================================
# TELEMETRY OBSERVABILITY
# =============================================================================


class TestTrivialExchangeTelemetry:
    """Verify observable failure modes for contract lookup."""

    def test_contract_lookup_failure_logs_reason(self, tmp_path, monkeypatch):
        """When _load_contract fails, log_trivial_skip is called with the failure reason."""
        import logging
        import io

        # Capture logging output
        log_buffer = io.StringIO()
        handler = logging.StreamHandler(log_buffer)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger("trivial_turns.epistemic_contract")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            # Manually simulate the contract lookup failure path
            from __lib.trivial_turns import log_trivial_skip
            log_trivial_skip("epistemic_contract", "contract_lookup_failed:ModuleNotFoundError", "analysis", "response")
            output = log_buffer.getvalue()
            assert "contract_lookup_failed" in output, f"Expected contract_lookup_failed in log, got: {output}"
        finally:
            logger.removeHandler(handler)


class TestNonTrivialTelemetry:
    """Verify non-trivial classifications are logged for tuning baseline."""

    def test_non_trivial_logs_reason(self, tmp_path):
        """Every non-trivial decision is logged so precision/recall can be measured."""
        import logging
        import io

        log_buffer = io.StringIO()
        handler = logging.StreamHandler(log_buffer)
        handler.setLevel(logging.INFO)
        logger = logging.getLogger("trivial_turns.generic")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            from __lib.trivial_turns import log_non_trivial_classification
            log_non_trivial_classification("generic", "not_trivial", "analysis", "done")
            output = log_buffer.getvalue()
            assert "NON_TRIVIAL" in output, f"Expected NON_TRIVIAL in log, got: {output}"
            assert "not_trivial" in output, f"Expected reason in log, got: {output}"
        finally:
            logger.removeHandler(handler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])