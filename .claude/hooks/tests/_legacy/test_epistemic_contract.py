#!/usr/bin/env python3
"""DEPRECATED — Tests for the legacy StopHook_epistemic_contract.py.

Superseded by: tests/test_epistemic_validator.py (80 tests).
This file tests a module that is no longer in the dispatch chain.
Kept for reference only — do not add new tests here.

Tests for StopHook_epistemic_contract.py — Phase 1 epistemic contract validator."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from StopHook_epistemic_contract import (
    validate_epistemic_answer,
    _strip_bullet,
    _is_code_related,
    SECTION_ORDER,
)


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

def fact(text: str) -> str:
    return f"[FACT]\n- {text}"


def inf(text: str) -> str:
    return f"[INFERENCE]\n- {text}"


def unk(text: str) -> str:
    return f"[UNKNOWN]\n- {text}"


def rec(text: str) -> str:
    return f"[RECOMMENDATION]\n- {text}"


def good_response(extra_fact: str = "", extra_inf: str = "", extra_unk: str = "", extra_rec: str = "") -> str:
    parts = [
        "[FACT]",
        f"- {extra_fact or 'Stop.py line 236 sets response (source: Stop.py:236)'}",
        "[INFERENCE]",
        f"- {extra_inf or 'Based on line 240, it appears that evaluate_claims is called after response extraction.'}",
        "[UNKNOWN]",
        f"- {extra_unk or 'I do not know whether there are existing tests for causal claim detection.'}",
        "[RECOMMENDATION]",
        f"- {extra_rec or 'Given the current implementation, I recommend writing a unit test because it validates the design.'}",
    ]
    return "\n".join(parts)


# --------------------------------------------------------------------
# Structure tests
# --------------------------------------------------------------------

def test_valid_minimal_response() -> None:
    """A properly structured response with all four sections passes."""
    text = good_response()
    result = validate_epistemic_answer(text)
    assert result.ok, f"Expected pass, got: {result.to_reason()}"


def test_empty_response_allowed() -> None:
    """Empty response returns ok=True (let other gates handle it)."""
    result = validate_epistemic_answer("")
    assert result.ok
    assert result.issues == []


def test_missing_fact_section() -> None:
    """Missing [FACT] section fails."""
    text = "\n".join([
        "[INFERENCE]",
        "- This may indicate a bug.",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- Given the evidence, I recommend a fix.",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("Missing section heading [FACT]" in i.message for i in result.issues)


def test_missing_inference_section() -> None:
    """Missing [INFERENCE] fails."""
    text = "\n".join([
        "[FACT]",
        "- Stop.py line 236 sets response = data.get('response', '').",
        "[UNKNOWN]",
        "- I do not know.",
        "[RECOMMENDATION]",
        "- Given the facts, I recommend a test.",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok


def test_missing_unknown_section() -> None:
    """Missing [UNKNOWN] fails."""
    text = "\n".join([
        "[FACT]",
        "- Stop.py line 236 sets response = data.get('response', '').",
        "[INFERENCE]",
        "- This may indicate a bug.",
        "[RECOMMENDATION]",
        "- Given the facts, I recommend a test.",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok


def test_missing_recommendation_section() -> None:
    """Missing [RECOMMENDATION] fails."""
    text = "\n".join([
        "[FACT]",
        "- Stop.py line 236 sets response = data.get('response', '').",
        "[INFERENCE]",
        "- This may indicate a bug.",
        "[UNKNOWN]",
        "- I do not know.",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok


def test_wrong_section_order() -> None:
    """Sections out of order fail."""
    text = "\n".join([
        "[INFERENCE]",
        "- This may indicate a bug.",
        "[FACT]",
        "- Stop.py line 236 sets response = data.get('response', '').",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("must appear in order" in i.message for i in result.issues)


def test_text_outside_sections_fails() -> None:
    """Free-floating text outside sections is a global error."""
    text = "This is a free-floating sentence.\n\n[FACT]\n- Stop.py line 236.\n[INFERENCE]\n- (none)\n[UNKNOWN]\n- (none)\n[RECOMMENDATION]\n- (none)"
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("outside any" in i.message for i in result.issues)


def test_empty_section_needs_none_bullet() -> None:
    """Empty section (no bullets) fails unless it has '- (none)'."""
    text = "\n".join([
        "[FACT]",
        "- Stop.py line 236.",
        "[INFERENCE]",
        "",  # empty section with no bullet
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok


def test_section_with_none_bullet_passes() -> None:
    """A section with '- (none)' is valid even if empty."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


# --------------------------------------------------------------------
# [FACT] semantic tests
# --------------------------------------------------------------------

def test_fact_with_uncertainty_fails() -> None:
    """FACT bullets with uncertainty words fail."""
    text = good_response(
        extra_fact="Stop.py line 236 probably handles the response extraction."
    )
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any(
        "[FACT]" in i.section and "uncertainty language" in i.message
        for i in result.issues
    )


def test_fact_coding_related_needs_source_suffix() -> None:
    """FACT without structured source suffix fails."""
    text = good_response(
        extra_fact="The behavior_audit gate calls evaluate_claims."
    )
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any(
        "[FACT]" in i.section and "source suffix" in i.message
        for i in result.issues
    )


def test_fact_with_source_suffix_passes() -> None:
    """FACT with (source: filename:line) suffix passes."""
    text = good_response(
        extra_fact="Stop.py line 236 sets the response field (source: Stop.py:236)"
    )
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_fact_user_attribution_passes() -> None:
    """FACT attributed to user passes without code source hint."""
    text = "\n".join([
        "[FACT]",
        "- According to the user's description, the current gate uses regex-based claim detection.",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_fact_none_placeholder_passes() -> None:
    """FACT '- (none)' passes without source check."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok


# --------------------------------------------------------------------
# [INFERENCE] semantic tests
# --------------------------------------------------------------------

def test_inference_without_uncertainty_fails() -> None:
    """INFERENCE bullet without uncertainty markers fails when it reads as hard assertion."""
    text = good_response(
        extra_inf="The cause is that the regex does not match causal patterns."
    )
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any(
        "[INFERENCE]" in i.section and "hard assertion" in i.message
        for i in result.issues
    )


def test_inference_with_uncertainty_passes() -> None:
    """INFERENCE with explicit uncertainty markers passes."""
    text = good_response(
        extra_inf="Based on the evidence, I infer that causal claims may not be detected."
    )
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


# --------------------------------------------------------------------
# [UNKNOWN] semantic tests
# --------------------------------------------------------------------

def test_unknown_with_recommendation_fails() -> None:
    """UNKNOWN bullet that smuggles in a recommendation fails."""
    text = good_response(
        extra_unk="I do not know which option is best, so you should choose Option A."
    )
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any(
        "[UNKNOWN]" in i.section and "recommendation" in i.message
        for i in result.issues
    )


def test_unknown_clean_passes() -> None:
    """Pure UNKNOWN without recommendation language passes."""
    text = good_response(
        extra_unk="I do not know whether there are existing tests for this behavior."
    )
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


# --------------------------------------------------------------------
# [RECOMMENDATION] semantic tests
# --------------------------------------------------------------------

def test_recommendation_without_rationale_or_assumption_fails() -> None:
    """RECOMMENDATION without goal/assumption or rationale fails."""
    text = good_response(
        extra_rec="Use Option A to fix this."
    )
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any(
        "[RECOMMENDATION]" in i.section and "lacks goal/assumption or rationale" in i.message
        for i in result.issues
    )


def test_recommendation_with_because_passes() -> None:
    """RECOMMENDATION with 'because' passes."""
    text = good_response(
        extra_rec="Given your goal of minimal changes, I recommend Option A because it keeps changes localized."
    )
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_recommendation_with_given_passes() -> None:
    """RECOMMENDATION with 'given' assumption phrase passes."""
    text = good_response(
        extra_rec="Assuming you want minimal code churn, I recommend extending the existing gate."
    )
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_recommendation_with_so_that_passes() -> None:
    """RECOMMENDATION with 'so that' rationale passes."""
    text = good_response(
        extra_rec="I recommend adding a pre-filter so that the change stays localized."
    )
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


# --------------------------------------------------------------------
# Bullet format tests
# --------------------------------------------------------------------

def test_bullet_without_dash_fails() -> None:
    """Bullet not starting with '- ' fails."""
    text = "\n".join([
        "[FACT]",
        "Stop.py line 236 sets response.",  # missing dash
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("must start with '- '" in i.message for i in result.issues)


# --------------------------------------------------------------------
# Helper function tests
# --------------------------------------------------------------------

def test_strip_bullet() -> None:
    assert _strip_bullet("- Hello world") == "Hello world"
    assert _strip_bullet("  -   trimmed  ") == "trimmed"
    assert _strip_bullet("no dash") == "no dash"


def test_is_code_related() -> None:
    assert _is_code_related("Stop.py line 236 handles this.")
    assert _is_code_related("The function returns None.")
    assert _is_code_related("import sys")
    assert not _is_code_related("This is a general question.")
    assert not _is_code_related("I do not know.")


# --------------------------------------------------------------------
# Phase 2: Causal claim detector tests
# --------------------------------------------------------------------

def test_unknown_causal_language_blocked() -> None:
    """UNKNOWN with causal phrase blocked."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- The issue is because the regex doesn't match.",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[UNKNOWN]" in i.section and "causal language" in i.message for i in result.issues)


def test_fact_causal_without_quote_blocked() -> None:
    """FACT with causal phrase but no quote/observed evidence blocked."""
    text = "\n".join([
        "[FACT]",
        "- The crash occurs because the null check is missing (source: bug.py:42)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[FACT]" in i.section and "directly observed" in i.message for i in result.issues)


def test_fact_causal_with_quote_allowed() -> None:
    """FACT with causal phrase and 'according to' passes."""
    text = "\n".join([
        "[FACT]",
        "- According to the crash trace, the null reference is caused by missing validation (source: trace.txt:10)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_inference_causal_without_uncertainty_blocked() -> None:
    """INFERENCE with causal phrase but no uncertainty blocked."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- The crash is caused by the null check being missing.",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[INFERENCE]" in i.section and "uncertainty" in i.message for i in result.issues)


def test_inference_causal_with_uncertainty_allowed() -> None:
    """INFERENCE with causal phrase and uncertainty marker passes."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- The crash may be caused by missing null check logic.",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_recommendation_causal_with_guarantee_blocked() -> None:
    """RECOMMENDATION with causal phrase + hard assertion verb blocked."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- Adding the null check is caused by fixing the crash.",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[RECOMMENDATION]" in i.section and "guarantee" in i.message for i in result.issues)


def test_recommendation_causal_probabilistic_allowed() -> None:
    """RECOMMENDATION with causal phrase in probabilistic form passes."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- Given the crash data, adding a null check is likely to reduce the crash rate.",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


# --------------------------------------------------------------------
# Mode and run() function tests
# --------------------------------------------------------------------

def test_run_warn_mode_returns_warn_not_block() -> None:
    """run() with EPISTEMIC_CONTRACT_MODE=warn returns warn decision."""
    import os
    from StopHook_epistemic_contract import run

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "warn"
    os.environ["EPISTEMIC_CAUSAL_MODE"] = "off"
    try:
        data = {"response": "No sections at all"}
        result = run(data)
        assert result is not None
        assert result["decision"] == "warn"
        assert "outside any" in result["reason"]
    finally:
        os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
        os.environ["EPISTEMIC_CAUSAL_MODE"] = "warn"


def test_run_strict_mode_returns_block() -> None:
    """run() with EPISTEMIC_CONTRACT_MODE=strict returns block decision."""
    import os
    from StopHook_epistemic_contract import run

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
    os.environ["EPISTEMIC_CAUSAL_MODE"] = "off"
    try:
        data = {"response": "No sections at all"}
        result = run(data)
        assert result is not None
        assert result["decision"] == "block"
        assert "outside any" in result["reason"]
    finally:
        os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
        os.environ["EPISTEMIC_CAUSAL_MODE"] = "warn"


def test_run_empty_response_allowed() -> None:
    """run() with empty response returns None (allow)."""
    import os
    from StopHook_epistemic_contract import run

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
    try:
        result = run({"response": ""})
        assert result is None
    finally:
        os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"


# --------------------------------------------------------------------
# Phase 3: Comparative judgment detector tests
# --------------------------------------------------------------------

def test_unknown_comparative_language_blocked() -> None:
    """UNKNOWN with comparative phrase blocked."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- The other approach is better.",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[UNKNOWN]" in i.section and "comparative" in i.message for i in result.issues)


def test_fact_comparative_without_attribution_blocked() -> None:
    """FACT with comparative but no external attribution blocked."""
    text = "\n".join([
        "[FACT]",
        "- Option A is the best approach (source: test.py:1)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[FACT]" in i.section and "comparative" in i.message for i in result.issues)


def test_fact_comparative_with_attribution_allowed() -> None:
    """FACT with comparative and external attribution passes."""
    text = "\n".join([
        "[FACT]",
        "- According to the benchmarks, algorithm A has the best throughput (source: benchmark.txt:5)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_inference_superlative_without_uncertainty_blocked() -> None:
    """INFERENCE with superlative but no uncertainty blocked."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- Option A is the optimal solution.",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[INFERENCE]" in i.section and "uncertainty" in i.message for i in result.issues)


def test_inference_superlative_with_uncertainty_allowed() -> None:
    """INFERENCE with superlative and uncertainty marker passes."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- Option A is likely the optimal solution given the constraints.",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- (none)",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_recommendation_superlative_without_assumption_blocked() -> None:
    """RECOMMENDATION with superlative but no assumption/goal blocked."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- Use Option A — it is the best choice.",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[RECOMMENDATION]" in i.section and "assumptions" in i.message or "goal" in i.message for i in result.issues)


def test_recommendation_comparative_with_assumption_allowed() -> None:
    """RECOMMENDATION with comparative and explicit assumption passes."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- Assuming minimal code churn is the priority, Option A may be preferable since it avoids large refactors.",
    ])
    result = validate_epistemic_answer(text)
    assert result.ok, result.to_reason()


def test_recommendation_weaker_comparative_without_rationale_blocked() -> None:
    """RECOMMENDATION with 'better' but no assumption/rationale blocked."""
    text = "\n".join([
        "[FACT]",
        "- (none)",
        "[INFERENCE]",
        "- (none)",
        "[UNKNOWN]",
        "- (none)",
        "[RECOMMENDATION]",
        "- Option A is better than Option B.",
    ])
    result = validate_epistemic_answer(text)
    assert not result.ok
    assert any("[RECOMMENDATION]" in i.section and ("goal" in i.message or "rationale" in i.message or "assumption" in i.message) for i in result.issues)


# --------------------------------------------------------------------
# Golden exemplar tests — passes Phase 1 + Phase 2 + Phase 3 (strict)
# --------------------------------------------------------------------

def test_golden_exemplar_code_analysis_with_recommendation() -> None:
    """Golden exemplar 1: Code analysis with causal + comparative language — passes all phases in strict mode.

    This response passes:
    - Phase 1: FACT has source suffix, INFERENCE has uncertainty markers, REC has rationale
    - Phase 2: UNKNOWN has no causal language, FACT causal has attribution, REC causal uses Phase 2 uncertainty ("may reduce")
    - Phase 3: UNKNOWN has no comparative, REC comparative has explicit goal/assumption + rationale
    """
    text = """[FACT]
- The hook returns {"decision": "block"} when sections are missing (source: StopHook_epistemic_contract.py:230)
- validate_epistemic_answer() runs in under 50ms for typical inputs (source: test_file:12)

[INFERENCE]
- The gate likely blocks responses without [FACT] sections to enforce evidence-grounded output.
- It appears the regex-based section detection is vulnerable to whitespace variations between the bracket and section name.

[UNKNOWN]
- I do not know whether the gate has been tested with non-ASCII section headers.
- I have not verified whether the gate handles nested bullet structures.

[RECOMMENDATION]
- Given the current implementation, adding a PreToolUse normalization step to strip leading/trailing whitespace from section headers may reduce false positives.
- Assuming input validation is a goal, Option A (strip whitespace in the section regex) is preferable to Option B (whitelist allowed section names) since it avoids maintaining an allowlist.
"""
    # Force strict mode for this test
    import os
    os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
    os.environ["EPISTEMIC_CAUSAL_MODE"] = "strict"
    os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "strict"
    try:
        result = validate_epistemic_answer(text)
        assert result.ok, f"Golden exemplar 1 should pass strict mode but got: {result.to_reason()}"
    finally:
        os.environ["EPISTEMIC_CONTRACT_MODE"] = "warn"
        os.environ["EPISTEMIC_CAUSAL_MODE"] = "warn"
        os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "warn"


def test_golden_exemplar_option_comparison_with_justification() -> None:
    """Golden exemplar 2: Option comparison with causal reasoning — passes all phases in strict mode.

    This response passes:
    - Phase 1: FACT has source suffix, INFERENCE has uncertainty markers, REC has explicit goal/assumption + rationale
    - Phase 2: UNKNOWN forbids causal, REC causal uses "may" (not guarantee), REC rationale uses "since" (not causal guarantee)
    - Phase 3: REC comparative has explicit goal ("Assuming minimal code churn is the priority") + rationale ("since it avoids large refactors")
    """
    text = """[FACT]
- Stop.py currently invokes _run_epistemic_contract before behavior_audit (source: Stop.py:236)
- The IN_PROCESS_GATES list contains 7 registered gates (source: Stop.py:51)

[INFERENCE]
- The ordering suggests epistemic contract validation runs as a first-pass gate before stylistic analysis.
- The hook may be checking for structured output format before evaluating content quality.

[UNKNOWN]
- I do not know whether there are existing benchmarks comparing gate ordering effects on response quality.
- I have not found documentation on the intended degradation path when gates fail.

[RECOMMENDATION]
- Assuming minimal code churn is the priority, moving the epistemic contract gate after behavior_audit may reduce ordering-related side effects since downstream gates would already have a chance to normalize the response.
- If response latency is a concern, keeping the current ordering may be preferable since epistemic validation is regex-based and adds negligible overhead compared to LLM-powered gates.
- Given that we need to balance latency and correctness, Option A (maintain current ordering) might be the safer choice since it has been stable for several releases and the risk of introducing ordering bugs outweighs the potential optimization gains.
"""
    import os
    os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
    os.environ["EPISTEMIC_CAUSAL_MODE"] = "strict"
    os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "strict"
    try:
        result = validate_epistemic_answer(text)
        assert result.ok, f"Golden exemplar 2 should pass strict mode but got: {result.to_reason()}"
    finally:
        os.environ["EPISTEMIC_CONTRACT_MODE"] = "warn"
        os.environ["EPISTEMIC_CAUSAL_MODE"] = "warn"
        os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "warn"


# --------------------------------------------------------------------
# Failure example tests — ensure bad answers are caught by each phase
# --------------------------------------------------------------------

def test_phase1_no_structure_blocked() -> None:
    """Phase 1 failure: response with no 4-section structure is blocked."""
    import os

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
    os.environ["EPISTEMIC_CAUSAL_MODE"] = "off"
    os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "off"
    try:
        text = (
            "The Stop hook is blocking your responses because it thinks some of your claims are unverified.\n\n"
            "You should add more tests and update the claim verifier so it trusts your statements more."
        )
        result = validate_epistemic_answer(text)
        assert not result.ok
        # Must flag text outside sections
        assert any(
            i.section == "__GLOBAL__" and "outside any" in i.message
            for i in result.issues
        ), f"Expected global 'outside any' issue: {result.issues}"
        # Must flag all 4 missing sections
        sections_found = {i.message.split("[")[1].split("]")[0] for i in result.issues if "Missing section heading" in i.message}
        assert sections_found == {"FACT", "INFERENCE", "UNKNOWN", "RECOMMENDATION"}, f"Missing: {sections_found}"
    finally:
        os.environ["EPISTEMIC_CONTRACT_MODE"] = "warn"
        os.environ["EPISTEMIC_CAUSAL_MODE"] = "warn"
        os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "warn"


def test_phase2_causal_wrong_sections_blocked() -> None:
    """Phase 2 failure: causal language in wrong sections without uncertainty is blocked."""
    import os

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
    os.environ["EPISTEMIC_CAUSAL_MODE"] = "strict"
    os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "off"
    try:
        text = "\n".join([
            "[FACT]",
            "- The Stop hook blocks your responses because it detects unverified claims in your messages. (source: Stop.py:240)",
            "[INFERENCE]",
            "- The cause is that your messages are too long and the regexes fail to match correctly. (source: StopHook_epistemic_contract.py)",
            "[UNKNOWN]",
            "- I do not know the exact reason, but it is caused by the way the Stop hook is configured. (source: user-description)",
            "[RECOMMENDATION]",
            "- I recommend rewriting the Stop hook; this will fix all blocking issues. (source: StopHook_epistemic_contract.py)",
        ])
        result = validate_epistemic_answer(text)
        assert not result.ok

        # FACT: causal without attribution
        assert any(
            i.section == "[FACT]" and "causal language" in i.message
            for i in result.issues
        ), f"FACT should have causal-language issue: {result.issues}"

        # INFERENCE: causal without uncertainty
        assert any(
            i.section == "[INFERENCE]" and "causal language" in i.message and "uncertainty" in i.message
            for i in result.issues
        ), f"INFERENCE should have causal-language + uncertainty issue: {result.issues}"

        # UNKNOWN: causal forbidden
        assert any(
            i.section == "[UNKNOWN]" and "causal language" in i.message
            for i in result.issues
        ), f"UNKNOWN should have causal-language issue: {result.issues}"
    finally:
        os.environ["EPISTEMIC_CONTRACT_MODE"] = "warn"
        os.environ["EPISTEMIC_CAUSAL_MODE"] = "warn"
        os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "warn"


def test_phase3_comparative_wrong_sections_blocked() -> None:
    """Phase 3 failure: comparative language in wrong sections without assumptions is blocked."""
    import os

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "strict"
    os.environ["EPISTEMIC_CAUSAL_MODE"] = "off"
    os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "strict"
    try:
        text = "\n".join([
            "[FACT]",
            "- Extending unified_claim_verifier is the best solution for your Stop hook issues. (source: StopHook_epistemic_contract.py)",
            "[INFERENCE]",
            "- Based on what I see, extending unified_claim_verifier is the optimal approach. (source: StopHook_epistemic_contract.py)",
            "[UNKNOWN]",
            "- I do not know which option is better for you, but creating a new gate might be the safest choice. (source: user-description)",
            "[RECOMMENDATION]",
            "- I recommend extending unified_claim_verifier; it is the best and lowest risk option. (source: StopHook_epistemic_contract.py)",
        ])
        result = validate_epistemic_answer(text)
        assert not result.ok

        # FACT: comparative without attribution
        assert any(
            i.section == "[FACT]" and "comparative language" in i.message
            for i in result.issues
        ), f"FACT should have comparative-language issue: {result.issues}"

        # INFERENCE: strong comparative without uncertainty
        assert any(
            i.section == "[INFERENCE]" and "strong comparative" in i.message and "uncertainty" in i.message
            for i in result.issues
        ), f"INFERENCE should have strong-comparative + uncertainty issue: {result.issues}"

        # UNKNOWN: comparative forbidden
        assert any(
            i.section == "[UNKNOWN]" and "comparative language" in i.message
            for i in result.issues
        ), f"UNKNOWN should have comparative-language issue: {result.issues}"

        # RECOMMENDATION: strong comparative without assumption/goal
        assert any(
            i.section == "[RECOMMENDATION]" and "strong comparative language" in i.message and "assumptions" in i.message
            for i in result.issues
        ), f"RECOMMENDATION should have strong-comparative + assumptions issue: {result.issues}"
    finally:
        os.environ["EPISTEMIC_CONTRACT_MODE"] = "warn"
        os.environ["EPISTEMIC_CAUSAL_MODE"] = "warn"
        os.environ["EPISTEMIC_COMPARATIVE_MODE"] = "warn"
