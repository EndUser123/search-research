#!/usr/bin/env python3
"""
test_stop_epistemic_applicability.py
====================================
End-to-end integration tests for the two-layer epistemic applicability system:
- Layer 1: Turn-mode scoping (is_substantive_reasoning_turn)
- Layer 2: Simple-answer fast path (is_simple_epistemic_response, is_grounded_delivery_summary)

Covers:
- LAZY WORKAROUND gate: skips on non-substantive modes, delivery summaries
- Epistemic format gate: bypasses section-header requirement on simple responses
"""

from __future__ import annotations

import pytest

from __lib.epistemic_applicability import (
    is_substantive_reasoning_turn,
    is_simple_epistemic_response,
    is_grounded_delivery_summary,
    strip_for_gate_matching,
    classify_epistemic_response,
    EpistemicClassification,
    EpistemicApplicabilityDecision,
    determine_epistemic_applicability,
)
from __lib.turn_mode import TurnMode


# =============================================================================
# Layer 1: Turn-mode scoping — is_substantive_reasoning_turn
# =============================================================================

class TestIsSubstantiveReasoningTurn:
    """Unit tests for is_substantive_reasoning_turn()."""

    @pytest.mark.parametrize("mode", ["control", "exploration", "meta", "plan", "execution-report"])
    def test_non_substantive_modes_return_false(self, mode: TurnMode):
        assert is_substantive_reasoning_turn(mode) is False

    @pytest.mark.parametrize("mode", ["analysis", "final-answer"])
    def test_substantive_modes_return_true(self, mode: TurnMode):
        assert is_substantive_reasoning_turn(mode) is True


# =============================================================================
# Layer 2: Simple-answer fast path
# =============================================================================

class TestIsSimpleEpistemicResponse:
    """Unit tests for is_simple_epistemic_response()."""

    @pytest.mark.parametrize(
        "response",
        [
            "Yes, the fix is in.",
            "Tests are passing.",
            "103 passed, 2 failed.",
            "All tests pass. Done.",
            "I've fixed the import.",
            "LIMITATIONS:\n- No graceful degradation for missing config",
        ],
    )
    def test_simple_direct_answers_return_true(self, response: str):
        assert is_simple_epistemic_response(response) is True

    @pytest.mark.parametrize(
        "response",
        [
            "The root cause is that sys.path does not include the hooks directory.",
            "This is a lazy workaround because the real fix would require significant refactoring.",
            "The problem originates from the import chain — I traced it to line 42.",
            "Because the gate fires on every response, it creates a loop.",
            "Therefore, the fix requires adding a turn-mode check.",
        ],
    )
    def test_diagnosis_responses_return_false(self, response: str):
        assert is_simple_epistemic_response(response) is False

    def test_section_headers_return_false(self):
        response = "[FACT]\n- grep shows the import is missing\n[INFERENCE]\n- the fix is to add the import"
        assert is_simple_epistemic_response(response) is False


# =============================================================================
# Layer 2: Grounded delivery summary detection
# =============================================================================

class TestIsGroundedDeliverySummary:
    """Unit tests for is_grounded_delivery_summary()."""

    @pytest.mark.parametrize(
        "response",
        [
            "103 passed, 2 failed.",
            "All tests pass. Done.",
            "Implementation complete.",
        ],
    )
    def test_grounded_summaries_return_true(self, response: str):
        assert is_grounded_delivery_summary(response) is True

    def test_diagnosis_returns_false(self):
        assert is_grounded_delivery_summary("The root cause is X.") is False


# =============================================================================
# LAZY WORKAROUND gate integration
# =============================================================================

def _make_data(mode: TurnMode, response: str, tool_events=None) -> dict:
    """Build a minimal Stop hook data dict for testing."""
    return {
        "mode": mode,
        "terminal_id": "test_terminal",
        "session_id": "test_session",
        "response": response,
        "tool_events": tool_events or [],
    }


class TestLazyWorkaroundGateApplicability:
    """Integration tests: LAZY WORKAROUND gate respects turn-mode scoping + delivery bypass."""

    def test_block_on_analysis_mode_with_actual_workaround(self):
        """analysis mode + real lazy workaround → SHOULD block."""
        # Analysis mode is substantive, so gate should fire
        assert is_substantive_reasoning_turn("analysis") is True
        # Delivery summary should NOT bypass in this case (no delivery pattern)
        assert is_grounded_delivery_summary(
            "That's a cosmetic bug — let's just suppress the error."
        ) is False

    def test_skip_on_control_mode_with_workaround_pattern(self):
        """control mode + pattern match → should skip (non-substantive)."""
        # Non-substantive mode: should skip even with workaround pattern
        assert is_substantive_reasoning_turn("control") is False

    def test_skip_on_plan_mode_with_workaround_pattern(self):
        """plan mode + pattern match → should skip."""
        # Non-substantive mode: should skip even with workaround pattern
        assert is_substantive_reasoning_turn("plan") is False

    def test_skip_on_execution_report_with_workaround_pattern(self):
        """execution-report mode + pattern match → should skip."""
        # Non-substantive mode: should skip even with workaround pattern
        assert is_substantive_reasoning_turn("execution-report") is False

    def test_skip_on_meta_mode_with_workaround_pattern(self):
        """meta mode + pattern match → should skip."""
        # Non-substantive mode: should skip even with workaround pattern
        assert is_substantive_reasoning_turn("meta") is False

    def test_skip_on_delivery_summary_with_workaround_words(self):
        """analysis mode + delivery summary with 'minor issue' → bypass delivery."""
        # Delivery summary bypasses lazy workaround check
        assert is_grounded_delivery_summary(
            "LIMITATIONS:\n- Minor issue: no graceful degradation for missing config"
        ) is True

    def test_skip_on_exploration_mode_with_workaround_pattern(self):
        """exploration mode + pattern match → should skip (non-substantive)."""
        # Non-substantive mode: should skip even with workaround pattern
        assert is_substantive_reasoning_turn("exploration") is False


# =============================================================================
# Epistemic format gate integration
# =============================================================================

class TestEpistemicContractApplicability:
    """Integration tests: epistemic format gate respects simple-answer fast path."""

    def test_skip_simple_answer_on_analysis_mode(self):
        """analysis mode + simple answer → skip section-header requirement."""
        # Simple answer: bypass should skip epistemic contract check
        assert is_simple_epistemic_response("103 passed, 2 failed.") is True

    def test_skip_simple_answer_on_final_answer_mode(self):
        """final-answer mode + simple answer → skip section-header requirement."""
        # Simple answer: bypass should skip epistemic contract check
        assert is_simple_epistemic_response("Yes, the fix is in.") is True

    def test_delivery_summary_on_analysis_mode_bypasses(self):
        """analysis mode + delivery summary → bypasses."""
        # Delivery summary: is_grounded_delivery_summary returns True
        assert is_grounded_delivery_summary("Implementation complete. 4 files created.") is True

    def test_diagnosis_on_analysis_mode_should_be_blocked_or_warned(self):
        """analysis mode + diagnosis → section headers required."""
        # Diagnosis on analysis mode should NOT be skipped
        assert is_simple_epistemic_response(
            "The root cause is that sys.path does not include the hooks directory."
        ) is False


# =============================================================================
# strip_for_gate_matching
# =============================================================================

class TestStripForGateMatching:
    """Tests for strip_for_gate_matching() — prevents self-trigger on prior output."""

    def test_strips_blockquote(self):
        text = "> The root cause is X\n> more context\nActual response text."
        result = strip_for_gate_matching(text)
        assert "> The root cause" not in result

    def test_strips_stop_hook_feedback_artifacts(self):
        text = "LAZY WORKAROUND detected\nReal response here."
        result = strip_for_gate_matching(text)
        assert "LAZY WORKAROUND" not in result


# =============================================================================
# classify_epistemic_response — unified classifier
# =============================================================================

class TestClassifyEpistemicResponse:
    """Unit tests for classify_epistemic_response() — unified epistemic classification."""

    # Simple direct answers
    def test_classify_short_assessment_as_simple(self):
        result = classify_epistemic_response("Yes, the fix is in.")
        assert result.is_simple_response is True
        assert result.is_delivery_response is False
        assert result.is_deep_analysis_candidate is False
        assert "short_response" in result.matched_signals or "direct_answer_pattern" in result.matched_signals

    def test_classify_yes_no_answer(self):
        result = classify_epistemic_response("No, that's not correct.")
        assert result.is_simple_response is True
        assert result.is_deep_analysis_candidate is False

    # Delivery responses
    def test_classify_delivery_tests_passing(self):
        result = classify_epistemic_response("Tests are passing.")
        assert result.is_simple_response is True
        assert result.is_delivery_response is True
        assert result.is_deep_analysis_candidate is False
        assert "delivery_pattern" in result.matched_signals or "grounded_short" in result.matched_signals

    def test_classify_delivery_ive_fixed(self):
        result = classify_epistemic_response("I've fixed the import.")
        assert result.is_simple_response is True
        assert result.is_delivery_response is True
        assert result.is_deep_analysis_candidate is False

    def test_classify_delivery_heres_what_i_changed(self):
        # "Here's what I changed" is long (>80 chars) and doesn't match delivery pattern
        # So it's simple (no deep analysis) but NOT delivery-specific
        result = classify_epistemic_response("Here's what I changed:\n- Stop.py\n- test_stop.py")
        assert result.is_simple_response is True
        assert result.is_deep_analysis_candidate is False
        # Not flagged as delivery because it starts with "Here's", not a delivery trigger

    def test_classify_delivery_verification_passed(self):
        result = classify_epistemic_response("All tests passed.")
        assert result.is_simple_response is True
        assert result.is_delivery_response is True

    def test_classify_delivery_digit_prefixed(self):
        result = classify_epistemic_response("103 passed, 2 failed.")
        assert result.is_simple_response is True
        assert result.is_delivery_response is True
        assert result.is_deep_analysis_candidate is False

    def test_classify_delivery_implemented(self):
        result = classify_epistemic_response("Implementation complete. 4 files created.")
        assert result.is_simple_response is True
        assert result.is_delivery_response is True

    # Deep analysis candidates
    def test_classify_deep_root_cause_analysis(self):
        result = classify_epistemic_response(
            "The root cause is that sys.path does not include the hooks directory."
        )
        assert result.is_simple_response is False
        assert result.is_delivery_response is False
        assert result.is_deep_analysis_candidate is True
        assert "diagnosis_markers" in result.matched_signals

    def test_classify_deep_because_clause(self):
        result = classify_epistemic_response(
            "Because the gate fires on every response, it creates a loop."
        )
        assert result.is_simple_response is False
        assert result.is_deep_analysis_candidate is True

    def test_classify_deep_therefore_clause(self):
        result = classify_epistemic_response(
            "Therefore, the fix requires adding a turn-mode check."
        )
        assert result.is_simple_response is False
        assert result.is_deep_analysis_candidate is True

    def test_classify_deep_architecture_tradeoff(self):
        result = classify_epistemic_response(
            "Weighing the tradeoffs: Option A gives faster performance but higher memory usage. "
            "Option B uses less memory but introduces latency. Given our constraints, Option B is better."
        )
        assert result.is_simple_response is False
        assert result.is_deep_analysis_candidate is True

    def test_classify_deep_section_headers(self):
        result = classify_epistemic_response(
            "[FACT]\n- grep shows the import is missing\n[INFERENCE]\n- the fix is to add the import"
        )
        assert result.is_simple_response is False
        assert result.is_deep_analysis_candidate is True
        assert "section_headers" in result.matched_signals

    # Conservative defaults
    def test_classify_short_response_uncertain_defaults_conservative(self):
        # Medium-length response without clear signals → conservative
        result = classify_epistemic_response("This looks like a potential issue.")
        # Without strong markers, short response should be simple
        assert result.is_simple_response is True
        assert result.is_deep_analysis_candidate is False

    def test_classify_medium_without_markers_is_simple(self):
        # Medium length without diagnosis markers → simple
        result = classify_epistemic_response("The tests are now passing after the fix.")
        assert result.is_simple_response is True

    # Cross-check with existing functions
    def test_classify_agrees_with_is_simple(self):
        cases = [
            "Yes, the fix is in.",
            "Tests are passing.",
            "The root cause is X.",
            "[FACT]\n- evidence here",
        ]
        for resp in cases:
            classify_result = classify_epistemic_response(resp)
            simple_result = is_simple_epistemic_response(resp)
            assert classify_result.is_simple_response == simple_result, \
                f"Mismatch for {resp!r}: classify={classify_result.is_simple_response}, is_simple={simple_result}"

    def test_classify_agrees_with_is_delivery(self):
        cases = [
            "Tests are passing.",
            "I've fixed the import.",
            "The root cause is X.",
        ]
        for resp in cases:
            classify_result = classify_epistemic_response(resp)
            delivery_result = is_grounded_delivery_summary(resp)
            assert classify_result.is_delivery_response == delivery_result, \
                f"Mismatch for {resp!r}: classify={classify_result.is_delivery_response}, is_delivery={delivery_result}"


# =============================================================================
# Layer 4: Authoritative applicability decision
# =============================================================================

class TestDetermineEpistemicApplicability:
    """Unit tests for determine_epistemic_applicability() — authoritative layered decision."""

    # --- Turn-mode suppression (Layer 1 overrides text heuristics) ---

    def test_control_mode_returns_none_enforcement(self):
        result = determine_epistemic_applicability(
            "The root cause is X.",
            turn_mode="control",
        )
        assert result.applicable is False
        assert result.enforcement_level == "none"
        assert "non-substantive" in result.reason

    def test_plan_mode_returns_none_enforcement(self):
        result = determine_epistemic_applicability(
            "Therefore, we need to fix this.",
            turn_mode="plan",
        )
        assert result.applicable is False
        assert result.enforcement_level == "none"

    def test_meta_mode_returns_none_enforcement(self):
        result = determine_epistemic_applicability(
            "I should verify this claim.",
            turn_mode="meta",
        )
        assert result.applicable is False
        assert result.enforcement_level == "none"

    def test_execution_report_mode_returns_none_enforcement(self):
        result = determine_epistemic_applicability(
            "Implementation complete.",
            turn_mode="execution-report",
        )
        assert result.applicable is False
        assert result.enforcement_level == "none"

    def test_exploration_mode_returns_none_enforcement(self):
        result = determine_epistemic_applicability(
            "Testing reveals the issue.",
            turn_mode="exploration",
        )
        assert result.applicable is False
        assert result.enforcement_level == "none"

    # --- Substantive modes go to Layer 2 ---

    def test_analysis_mode_simple_response_gets_simple_enforcement(self):
        result = determine_epistemic_applicability(
            "103 passed, 2 failed.",
            turn_mode="analysis",
        )
        assert result.applicable is True
        assert result.enforcement_level == "simple"
        assert result.turn_mode == "analysis"

    def test_final_answer_mode_simple_response_gets_simple_enforcement(self):
        result = determine_epistemic_applicability(
            "Yes, the fix is in.",
            turn_mode="final-answer",
        )
        assert result.applicable is True
        assert result.enforcement_level == "simple"

    def test_analysis_mode_deep_analysis_gets_full_enforcement(self):
        result = determine_epistemic_applicability(
            "The root cause is that sys.path does not include the hooks directory.",
            turn_mode="analysis",
        )
        assert result.applicable is True
        assert result.enforcement_level == "full"
        assert result.is_deep_analysis_candidate is True

    def test_final_answer_mode_deep_analysis_gets_full_enforcement(self):
        result = determine_epistemic_applicability(
            "[FACT]\n- grep shows the import is missing\n[INFERENCE]\n- the fix is to add the import",
            turn_mode="final-answer",
        )
        assert result.applicable is True
        assert result.enforcement_level == "full"
        assert result.is_simple_response is False

    # --- Unknown mode: conservative fallback (Layer 2 text heuristics) ---

    def test_unknown_mode_delivery_bypasses_to_simple(self):
        result = determine_epistemic_applicability(
            "I've fixed the import.",
            turn_mode=None,  # unknown mode
        )
        assert result.applicable is True
        assert result.enforcement_level == "simple"
        assert result.is_delivery_response is True

    def test_unknown_mode_deep_analysis_enforces_full(self):
        result = determine_epistemic_applicability(
            "Because the gate fires on every response, it creates a loop.",
            turn_mode=None,
        )
        assert result.applicable is True
        assert result.enforcement_level == "full"

    def test_unknown_mode_no_signals_defaults_full(self):
        # Medium-length response without diagnosis markers → simple (not deep)
        # Conservative default only applies when response is NOT already classified
        result = determine_epistemic_applicability(
            "This looks like a potential issue.",
            turn_mode=None,
        )
        assert result.applicable is True
        assert result.enforcement_level == "simple"  # Not "full" — classify() already sorted it

    # --- Signal tracking ---

    def test_signals_include_turn_mode_and_classification_markers(self):
        result = determine_epistemic_applicability(
            "The root cause is that sys.path does not include the hooks directory.",
            turn_mode="analysis",
        )
        assert any("mode=analysis" in s for s in result.matched_signals)
        assert any("diagnosis_markers" in s for s in result.matched_signals)

    def test_none_turn_mode_included_in_signals(self):
        result = determine_epistemic_applicability(
            "Tests are passing.",
            turn_mode=None,
        )
        assert any("turn_mode_suppression" not in s for s in result.matched_signals)

    # --- Quote/loop resistance ---

    def test_quoted_hook_output_suppressed(self):
        # Quoted diagnostic content is stripped before classification
        # "I've fixed the issue." is delivery → simple enforcement
        result = determine_epistemic_applicability(
            "> The root cause is X\n> more context\nI've fixed the issue.",
            turn_mode="analysis",
        )
        assert result.applicable is True
        assert result.is_simple_response is True  # Delivery pattern triggers simple
        assert result.enforcement_level == "simple"

    def test_fenced_diagnostic_block_classified_correctly(self):
        # Fenced diagnostic block with "root cause" → diagnosis → full enforcement
        # strip_for_gate_matching removes fence markers but leaves the content inside,
        # which contains "root cause" → deep analysis classification
        result = determine_epistemic_applicability(
            "```\nThe root cause is X.\n```\n\nI've fixed the issue.",
            turn_mode="analysis",
        )
        assert result.applicable is True
        # The diagnosis marker "root cause" dominates even with delivery phrase present
        assert result.is_deep_analysis_candidate is True
        assert result.enforcement_level == "full"

    # --- Backward compatibility: existing helpers agree ---

    def test_agreement_with_is_simple_on_substantive_mode(self):
        cases = [
            ("Yes, the fix is in.", "analysis"),
            ("The root cause is X.", "analysis"),
            ("[FACT]\nevidence", "final-answer"),
        ]
        for resp, mode in cases:
            decision = determine_epistemic_applicability(resp, turn_mode=mode)
            simple = is_simple_epistemic_response(resp)
            assert decision.is_simple_response == simple, \
                f"Mismatch for {resp!r} in {mode}: decision={decision.is_simple_response}, is_simple={simple}"

    def test_non_substantive_mode_skips_even_deep_content(self):
        result = determine_epistemic_applicability(
            "[FACT]\n- grep shows the import is missing\n[INFERENCE]\n- the fix is to add the import",
            turn_mode="plan",  # non-substantive
        )
        # Even though content has section headers, turn mode suppresses
        assert result.applicable is False
        assert result.enforcement_level == "none"

    # --- Enumeration of all non-substantive modes ---

    @pytest.mark.parametrize("mode", ["control", "exploration", "meta", "plan", "execution-report"])
    def test_all_non_substantive_modes_return_none_enforcement(self, mode: str):
        result = determine_epistemic_applicability("Deep analysis content here.", turn_mode=mode)
        assert result.applicable is False
        assert result.enforcement_level == "none"

    @pytest.mark.parametrize("mode", ["analysis", "final-answer"])
    def test_all_substantive_modes_respect_simple_delivery(self, mode: str):
        result = determine_epistemic_applicability("Tests are passing.", turn_mode=mode)
        assert result.applicable is True
        assert result.enforcement_level == "simple"


# =============================================================================
# Direct gate migration behavior — _run_epistemic_contract
# =============================================================================

class TestEpistemicContractGateMigration:
    """Verify _run_epistemic_contract behavior via determine_epistemic_applicability()."""

    def test_epistemic_contract_skips_when_applicability_none(self):
        # Non-substantive mode (control) → applicable=False → gate should skip
        decision = determine_epistemic_applicability(
            "Yes, the fix is in.",
            turn_mode="control",
        )
        assert decision.applicable is False
        assert decision.enforcement_level == "none"

    def test_epistemic_contract_skips_when_enforcement_level_simple(self):
        # Simple response on analysis mode → level=simple → gate should skip
        decision = determine_epistemic_applicability(
            "Yes, the fix is in.",
            turn_mode="analysis",
        )
        assert decision.applicable is True
        assert decision.enforcement_level == "simple"
        # Gate skips format check for simple responses

    def test_epistemic_contract_runs_when_enforcement_level_full(self):
        # Diagnosis response on analysis mode → level=full → gate should run validator
        decision = determine_epistemic_applicability(
            "The root cause is that sys.path does not include the hooks directory.",
            turn_mode="analysis",
        )
        assert decision.applicable is True
        assert decision.enforcement_level == "full"
        # Gate runs epistemic validator with section-header requirement


# =============================================================================
# Direct gate migration behavior — _run_lazy_workaround_gate
# =============================================================================

class TestLazyWorkaroundGateMigration:
    """Verify _run_lazy_workaround_gate behavior via determine_epistemic_applicability()."""

    def test_lazy_workaround_gate_skips_when_applicability_none(self):
        # Non-substantive mode (exploration) → applicable=False → gate should skip
        decision = determine_epistemic_applicability(
            "Let me check the logs.",
            turn_mode="exploration",
        )
        assert decision.applicable is False
        assert decision.enforcement_level == "none"

    def test_lazy_workaround_gate_skips_when_enforcement_level_simple(self):
        # Delivery summary on analysis mode → level=simple → gate should skip
        decision = determine_epistemic_applicability(
            "Tests are passing.",
            turn_mode="analysis",
        )
        assert decision.applicable is True
        assert decision.enforcement_level == "simple"
        # Lazy check is for detecting genuine lazy responses, not delivery summaries

    def test_lazy_workaround_gate_runs_when_enforcement_level_full(self):
        # Deep analysis content on analysis mode → level=full → gate should run
        decision = determine_epistemic_applicability(
            "Because the gate fires on every response, it creates a loop. "
            "The issue stems from the loop detection logic incrementing a counter "
            "even when the same hook is involved, which makes it appear as if "
            "multiple unique hooks are participating.",
            turn_mode="analysis",
        )
        assert decision.applicable is True
        assert decision.enforcement_level == "full"
        # Gate runs check_lazy_workarounds() to detect accept-bug-as-feature patterns


# =============================================================================
# Wrapper delegation and signal tracking (compatibility)
# =============================================================================

class TestWrapperDelegation:
    """Verify wrappers delegate to authoritative layer and signals track both layers."""

    def test_wrappers_delegate_to_authoritative_layer(self):
        # Each wrapper should produce results consistent with determine_epistemic_applicability
        response = "Yes, the fix is in."
        mode = "analysis"

        decision = determine_epistemic_applicability(response, turn_mode=mode)

        # is_simple_epistemic_response should match decision.is_simple_response
        wrapper_result = is_simple_epistemic_response(response)
        assert wrapper_result == decision.is_simple_response, \
            f"is_simple_epistemic_response={wrapper_result} != decision.is_simple_response={decision.is_simple_response}"

        # is_grounded_delivery_summary should match decision.is_delivery_response
        wrapper_result = is_grounded_delivery_summary(response)
        assert wrapper_result == decision.is_delivery_response, \
            f"is_grounded_delivery_summary={wrapper_result} != decision.is_delivery_response={decision.is_delivery_response}"

    def test_decision_signals_track_both_layers(self):
        # matched_signals should include signals from both Layer 1 and Layer 2
        decision = determine_epistemic_applicability(
            "The root cause is X.",
            turn_mode="analysis",
        )
        # Layer 1 signal (turn mode)
        assert any("mode=analysis" in s for s in decision.matched_signals)
        # Layer 2 signal (classification)
        assert any(
            "diagnosis_markers" in s or "simple_response" in s
            for s in decision.matched_signals
        )


class TestEpistemicClassification:
    """Unit tests for EpistemicClassification dataclass."""

    def test_classification_has_is_simple_shorthand(self):
        result = determine_epistemic_applicability("Yes, the fix is in.", turn_mode="analysis")
        assert result.classification.is_simple_response == result.is_simple_response

    def test_classification_has_is_delivery_shorthand(self):
        result = determine_epistemic_applicability("I've fixed the import.", turn_mode="analysis")
        assert result.classification.is_delivery_response == result.is_delivery_response

    def test_classification_has_is_deep_shorthand(self):
        result = determine_epistemic_applicability(
            "The root cause is X.", turn_mode="analysis"
        )
        assert result.classification.is_deep_analysis_candidate == result.is_deep_analysis_candidate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
