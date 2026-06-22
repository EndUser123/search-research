#!/usr/bin/env python3
"""Tests for StopHook_perf_attribution_gate.py"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# Import the module under test
from StopHook_perf_attribution_gate import (
    PERF_CLAIM_PATTERNS,
    TIMING_CODE_MARKERS,
    HEDGE_PATTERNS,
    META_SIGNALS,
    _detect_perf_claims,
    _is_meta_analysis,
    _timing_code_was_read,
    run,
)

# ----------------------------------------------------------------------
# Test Data
# ----------------------------------------------------------------------

NO_PERF_CLAIMS = "The implementation looks good. Let me summarize what was done."

PERF_CLAIM_UNVERIFIED = (
    "The ~480s timing is dominated by yt-dlp fetching. "
    "The bottleneck is clearly yt-dlp which takes most of the total time."
)

PERF_CLAIM_VERIFIED = (
    "Reading experiment_add_acceptance.py shows elapsed_s measures nlm source add --wait. "
    "The ~480s timing is dominated by yt-dlp fetching."
)

PERF_CLAIM_LOOP_GUARD = (
    "The bottleneck is yt-dlp fetching taking ~480s."
)

HEDGED_CLAIM = (
    "yt-dlp might dominate the ~480s timing, but this is just an estimate."
)

STOP_HOOK_PAYLOAD_NO_PERF = {
    "session_id": "test-session-123",
    "terminal_id": "test-terminal-456",
    "last_assistant_message": NO_PERF_CLAIMS,
    "stop_hook_active": False,
}

STOP_HOOK_PAYLOAD_PERF_UNVERIFIED = {
    "session_id": "test-session-123",
    "terminal_id": "test-terminal-456",
    "last_assistant_message": PERF_CLAIM_UNVERIFIED,
    "stop_hook_active": False,
}

STOP_HOOK_PAYLOAD_PERF_VERIFIED = {
    "session_id": "test-session-123",
    "terminal_id": "test-terminal-456",
    "last_assistant_message": PERF_CLAIM_VERIFIED,
    "stop_hook_active": False,
}

STOP_HOOK_PAYLOAD_PERF_LOOP_GUARD = {
    "session_id": "test-session-123",
    "terminal_id": "test-terminal-456",
    "last_assistant_message": PERF_CLAIM_LOOP_GUARD,
    "stop_hook_active": True,
}

STOP_HOOK_PAYLOAD_HEDGED = {
    "session_id": "test-session-123",
    "terminal_id": "test-terminal-456",
    "last_assistant_message": HEDGED_CLAIM,
    "stop_hook_active": False,
}

# ----------------------------------------------------------------------
# Test Cases
# ----------------------------------------------------------------------

class TestDetectPerfClaims:
    """Test _detect_perf_claims function."""

    def test_no_perf_claims(self):
        """Response with no perf claims -> should not detect."""
        assert _detect_perf_claims(NO_PERF_CLAIMS) is False

    def test_dominant_factor_claim(self):
        """'dominant factor' should trigger detection."""
        text = "The dominant factor in the ~480s timing is yt-dlp fetching."
        assert _detect_perf_claims(text) is True

    def test_bottleneck_claim(self):
        """'bottleneck' should trigger detection."""
        text = "The bottleneck is clearly yt-dlp processing."
        assert _detect_perf_claims(text) is True

    def test_duration_pattern(self):
        """~480s pattern should trigger detection."""
        text = "The ~480s total is dominated by fetch operations."
        assert _detect_perf_claims(text) is True

    def test_hedged_claim(self):
        """'yt-dlp might dominate' should NOT trigger (hedged)."""
        text = "yt-dlp might dominate the ~480s timing"
        assert _detect_perf_claims(text) is False

    def test_hedged_claim_roughly(self):
        """'roughly ~480s' should NOT trigger (hedged)."""
        text = "yt-dlp roughly takes ~480s"
        assert _detect_perf_claims(text) is False

    def test_hedged_claim_around(self):
        """'around ~480s' should NOT trigger (hedged)."""
        text = "yt-dlp is around ~480s total"
        assert _detect_perf_claims(text) is False

    def test_hedged_claim_approximately(self):
        """'approximately ~480s' should NOT trigger (hedged)."""
        text = "The bottleneck is approximately ~480s"
        assert _detect_perf_claims(text) is False

    def test_hedged_claim_about(self):
        """'about ~480s' should NOT trigger (hedged)."""
        text = "The timing is about ~480s"
        assert _detect_perf_claims(text) is False

    def test_throughput_claim(self):
        """'throughput is' should trigger detection."""
        text = "The throughput is bottlenecked by yt-dlp"
        assert _detect_perf_claims(text) is True

    def test_latency_claim(self):
        """'latency is' (adjacent) should trigger detection."""
        text = "The latency is caused by download operations"
        assert _detect_perf_claims(text) is True

    def test_latency_clause_spanning_not_blocked(self):
        """FP regression: 'latency' + a distant 'is' in an unrelated clause should NOT trigger.

        The verb must be adjacent to the noun; greedy .* previously matched across clauses.
        """
        text = (
            "The panel costs real latency/tokens, so a heuristic that fires on "
            "everything is worse than none."
        )
        assert _detect_perf_claims(text) is False

    def test_throughput_clause_spanning_not_blocked(self):
        """FP regression: 'throughput' with a non-adjacent 'is' should NOT trigger."""
        text = "Throughput matters here, and the design is clean."
        assert _detect_perf_claims(text) is False

    def test_no_longer_dominates(self):
        """'no longer dominates' should NOT trigger (negated)."""
        text = "Confirm CDS no longer dominates with score-0.00 noise"
        assert _detect_perf_claims(text) is False

    def test_verify_does_not_dominate(self):
        """Verification goal with negation should NOT trigger."""
        text = "Verify that yt-dlp doesn't dominate total time after the fix"
        assert _detect_perf_claims(text) is False

    def test_confirm_no_bottleneck(self):
        """'confirm' context should NOT trigger."""
        text = "Confirm the bottleneck is resolved by re-running the experiment"
        assert _detect_perf_claims(text) is False

    def test_ensure_not_bottleneck(self):
        """'ensure' context should NOT trigger."""
        text = "Ensure this step is not the bottleneck before shipping"
        assert _detect_perf_claims(text) is False

    def test_small_timing_estimate_not_blocked(self):
        """'~10 seconds' as a prose estimate for a tool call should NOT trigger (< 3 digits)."""
        text = "That single test (one Bash call, ~10 seconds) falsifies or confirms my diagnosis."
        assert _detect_perf_claims(text) is False

    def test_large_timing_measurement_still_blocked(self):
        """'~480s' (3+ digits) should still trigger detection."""
        text = "The ~480s total is dominated by fetch operations."
        assert _detect_perf_claims(text) is True

    def test_medium_timing_not_blocked(self):
        """'~60s' (2 digits) should NOT trigger after the narrowing."""
        text = "The fetch step takes ~60s in most cases."
        assert _detect_perf_claims(text) is False


class TestMetaAnalysis:
    """Test _is_meta_analysis and its effect on run()."""

    def test_meta_signal_detected(self):
        """Text containing a META_SIGNAL string should return True."""
        text = "The PERF_CLAIM_PATTERNS list includes `\\bbottleneck\\b`."
        assert _is_meta_analysis(text) is True

    def test_plain_text_not_meta(self):
        """Ordinary text without implementation strings is not meta."""
        text = "The bottleneck is clearly yt-dlp."
        assert _is_meta_analysis(text) is False

    def test_meta_signals_list_nonempty(self):
        """META_SIGNALS must contain entries."""
        assert len(META_SIGNALS) > 0

    def test_run_allows_meta_analysis_response(self):
        """run() exempts responses that discuss the gate's own implementation vocabulary."""
        payload = {
            "session_id": "test-session-123",
            "terminal_id": "test-terminal-456",
            "last_assistant_message": (
                "The PERF_CLAIM_PATTERNS list includes `\\bbottleneck\\b` which fires "
                "on meta-analysis responses that discuss the gate's own trigger vocabulary. "
                "The _detect_perf_claims function checks ±50 chars of context."
            ),
            "stop_hook_active": False,
        }
        result = run(payload)
        assert result["continue"] is True


class TestTimingCodeWasRead:
    """Test _timing_code_was_read function."""

    def test_no_timing_code_read(self):
        """Events without timing markers should return False."""
        events = [
            {"name": "Read", "command": "P:/some/file.py"},
            {"name": "Grep", "command": "import re"},
        ]
        assert _timing_code_was_read(events) is False

    def test_timing_code_was_read(self):
        """Events with timing markers should return True."""
        events = [
            {"name": "Read", "command": "P:/experiment_add_acceptance.py"},
            {"name": "Grep", "command": "elapsed_s"},
        ]
        assert _timing_code_was_read(events) is True

    def test_only_read_grep_counts(self):
        """Only Read and Grep events should be checked."""
        events = [
            {"name": "Bash", "command": "pytest experiment_add_acceptance.py"},
            {"name": "Write", "command": "P:/output.txt"},
        ]
        assert _timing_code_was_read(events) is False

    def test_elapsed_s_marker(self):
        """'elapsed_s' in command should return True."""
        events = [
            {"name": "Read", "command": "elapsed_s measurement"},
        ]
        assert _timing_code_was_read(events) is True


class TestRunFunction:
    """Test run() function with mocked evidence_scope."""

    def test_no_perf_claims_allows(self):
        """Response with no perf claims -> allow."""
        result = run(STOP_HOOK_PAYLOAD_NO_PERF)
        assert result["continue"] is True

    @patch("evidence_scope.load_scoped_tool_events")
    def test_perf_claim_unverified_blocks(
        self, mock_load_scoped_tool_events
    ):
        """Perf claim + NO timing code + stop_hook_active=false -> block."""
        mock_load_scoped_tool_events.return_value = [
            {"name": "Read", "command": "P:/some/file.py"},  # not timing code
        ]

        result = run(STOP_HOOK_PAYLOAD_PERF_UNVERIFIED)
        assert result["continue"] is False
        assert "stopReason" in result
        assert "UNVERIFIED PERFORMANCE ATTRIBUTION" in result["stopReason"]

    @patch("evidence_scope.load_scoped_tool_events")
    def test_perf_claim_verified_allows(
        self, mock_load_scoped_tool_events
    ):
        """Perf claim + timing code WAS read -> allow."""
        mock_load_scoped_tool_events.return_value = [
            {"name": "Read", "command": "experiment_add_acceptance.py"},
        ]

        result = run(STOP_HOOK_PAYLOAD_PERF_VERIFIED)
        assert result["continue"] is True

    @patch("evidence_scope.load_scoped_tool_events")
    def test_loop_guard_allows(
        self, mock_load_scoped_tool_events
    ):
        """Perf claim + NO timing code + stop_hook_active=true -> allow (loop guard)."""
        mock_load_scoped_tool_events.return_value = [
            {"name": "Read", "command": "P:/some/file.py"},  # not timing code
        ]

        result = run(STOP_HOOK_PAYLOAD_PERF_LOOP_GUARD)
        assert result["continue"] is True

    @patch("evidence_scope.load_scoped_tool_events")
    def test_hedged_claim_allows(
        self, mock_load_scoped_tool_events
    ):
        """Hedged claim -> allow (not confident)."""
        mock_load_scoped_tool_events.return_value = []

        result = run(STOP_HOOK_PAYLOAD_HEDGED)
        assert result["continue"] is True

    @patch("evidence_scope.load_scoped_tool_events")
    def test_evidence_scope_unavailable_fails_open(
        self, mock_load_scoped_tool_events
    ):
        """evidence_scope import fails -> allow (fail open)."""
        mock_load_scoped_tool_events.side_effect = ImportError("module not found")

        result = run(STOP_HOOK_PAYLOAD_PERF_UNVERIFIED)
        assert result["continue"] is True


class TestPatternConstants:
    """Test that pattern constants are properly defined."""

    def test_perf_claim_patterns_is_list(self):
        """PERF_CLAIM_PATTERNS should be a list."""
        assert isinstance(PERF_CLAIM_PATTERNS, list)
        assert len(PERF_CLAIM_PATTERNS) > 0

    def test_perf_claim_patterns_are_compiled(self):
        """All PERF_CLAIM_PATTERNS should be compiled regex."""
        for p in PERF_CLAIM_PATTERNS:
            assert isinstance(p, re.Pattern)

    def test_timing_code_markers_is_list(self):
        """TIMING_CODE_MARKERS should be a list."""
        assert isinstance(TIMING_CODE_MARKERS, list)
        assert len(TIMING_CODE_MARKERS) > 0

    def test_hedge_patterns_is_list(self):
        """HEDGE_PATTERNS should be a list."""
        assert isinstance(HEDGE_PATTERNS, list)
        assert len(HEDGE_PATTERNS) > 0

    def test_meta_signals_is_list(self):
        """META_SIGNALS should be a list."""
        assert isinstance(META_SIGNALS, list)
        assert len(META_SIGNALS) > 0

    def test_contains_expected_markers(self):
        """TIMING_CODE_MARKERS should contain expected values."""
        assert "experiment_add_acceptance" in TIMING_CODE_MARKERS
        assert "elapsed_s" in TIMING_CODE_MARKERS
        assert "time.time" in TIMING_CODE_MARKERS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])