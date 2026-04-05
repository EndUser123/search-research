#!/usr/bin/env python3
"""
Tests for response_structure_detector.py

Covers:
  - Pattern 1: Correction Theater (correction + unchanged conclusion)
  - Pattern 2: Recursive Hypocrisy (fabricated hypotheticals in correction sections)
  - Edge cases: short responses, exempt unchanged markers, clean responses
  - Integration: build_self_prompt composition
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anti_sycophancy.response_structure_detector import (
    MIN_WORD_COUNT,
    StructureMatch,
    _is_exempt_unchanged,
    build_self_prompt,
    detect_response_structure,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pad(n: int = 100) -> str:
    """Generate n filler words, always enough to clear MIN_WORD_COUNT."""
    return " " + " ".join(["filler"] * n)


def patterns(results: list) -> set:
    return {r.pattern for r in results}


# ---------------------------------------------------------------------------
# Pattern 1: Correction Theater -- SHOULD detect
# ---------------------------------------------------------------------------

def test_canonical_annoying_conversation():
    """The exact conversation that prompted this detector."""
    response = (
        "I was wrong about what Tier 2 catches. Let me address each point.\n\n"
        "I made it up. Rule 1 violation -- I stated a claim without verification.\n\n"
        "I got the burden of proof backwards.\n\n"
        "Summary of corrections:\n"
        "| My claim | Reality |\n"
        "|----------|---------|\n"
        "| Tier 2 only catches absence claims | It catches state-change claims too |\n"
        "| 1.5s latency | Made up -- unmeasured |\n\n"
        "Recommendation still holds (don't build Tier 3), but for better reasons."
        + pad()
    )
    result = detect_response_structure(response)
    assert "correction_theater" in patterns(result), f"Expected correction_theater, got: {result}"


def test_simple_correction_theater():
    """Minimal: one correction marker + one unchanged marker."""
    response = "I was wrong about the estimate. The recommendation still holds." + pad()
    result = detect_response_structure(response)
    assert "correction_theater" in patterns(result), f"Not detected: {result}"


def test_made_it_up_plus_still_recommend():
    response = "I made it up. I still recommend the same approach." + pad()
    result = detect_response_structure(response)
    assert "correction_theater" in patterns(result)


def test_correction_table_plus_still_holds():
    response = (
        "Let me correct my earlier statement.\n\n"
        "| My claim | Reality |\n"
        "|----------|---------|\n"
        "| 1.5s | unmeasured |\n\n"
        "The analysis still holds."
        + pad()
    )
    result = detect_response_structure(response)
    assert "correction_theater" in patterns(result)


def test_summary_of_corrections_plus_unchanged():
    response = (
        "Summary of corrections: I overstated the complexity. "
        "The bottom line doesn't change my recommendation."
        + pad()
    )
    result = detect_response_structure(response)
    assert "correction_theater" in patterns(result)


# ---------------------------------------------------------------------------
# Pattern 1: Correction Theater -- should NOT detect
# ---------------------------------------------------------------------------

def test_genuine_correction_changes_conclusion():
    """A real correction that changes the answer: no unchanged marker, no theater."""
    response = (
        "I was wrong about which endpoint to use. "
        "You should call /v2/auth instead of /v1/auth. "
        "The token format is different -- use Bearer, not Basic. "
        "Update your integration accordingly. This changes the auth flow entirely."
        + pad()
    )
    result = detect_response_structure(response)
    ct = [r for r in result if r.pattern == "correction_theater"]
    assert not ct, f"Genuine correction should not flag: {ct}"


def test_too_short_to_check():
    """Responses under MIN_WORD_COUNT are always skipped."""
    response = "I was wrong. The recommendation still holds."
    assert len(response.split()) < MIN_WORD_COUNT
    result = detect_response_structure(response)
    assert result == [], f"Short response should return empty: {result}"


def test_tests_still_pass_is_exempt():
    """'Tests still pass' is evidence-based, not a stability claim about recommendations."""
    response = (
        "I was wrong about the regex pattern. Fixed it. "
        "The full test suite still passes with the corrected implementation. "
        "No other changes needed."
        + pad()
    )
    result = detect_response_structure(response)
    ct = [r for r in result if r.pattern == "correction_theater"]
    assert not ct, f"'Tests still pass' should be exempt: {ct}"


def test_build_still_succeeds_is_exempt():
    response = (
        "I misstated the build command. The correct flag is --release. "
        "The build still succeeds with either flag on this platform."
        + pad()
    )
    result = detect_response_structure(response)
    ct = [r for r in result if r.pattern == "correction_theater"]
    assert not ct, f"'Build still succeeds' should be exempt: {ct}"


def test_exempt_does_not_suppress_real_unchanged_marker():
    """Regression: 'tests still pass' must NOT suppress 'recommendation still holds'."""
    response = (
        "I was wrong about the approach. "
        "The tests still pass after the fix. "
        "The recommendation still holds -- use the same library."
        + pad()
    )
    result = detect_response_structure(response)
    ct = [r for r in result if r.pattern == "correction_theater"]
    assert ct, (
        "Should detect correction_theater even when exempt marker is also present: "
        f"{result}"
    )


def test_empty_response():
    assert detect_response_structure("") == []


def test_no_markers_clean_response():
    response = (
        "The architecture uses three layers: ingestion, processing, and output. "
        "Each layer has its own error boundary. The processing layer is the bottleneck."
        + pad()
    )
    result = detect_response_structure(response)
    assert result == [], f"Clean response should not flag: {result}"


# ---------------------------------------------------------------------------
# Pattern 2: Recursive Hypocrisy -- SHOULD detect
# ---------------------------------------------------------------------------

def test_round_percentage_in_correction():
    """Round percentage in hypothetical framing inside correction section."""
    response = (
        "I made it up. I should not have stated 1.5s without measurement.\n\n"
        "The correct framing: if Tier 2 catches 95% of absence claims, "
        "that's evidence it's sufficient."
        + pad()
    )
    result = detect_response_structure(response)
    assert "recursive_hypocrisy" in patterns(result), \
        f"Should detect 95% hypothetical: {result}"


def test_round_latency_in_correction():
    """Round latency in hypothetical framing inside correction section."""
    response = (
        "I was wrong to claim 1.5s. "
        "Say the overhead is around 100ms per call -- that's still significant."
        + pad()
    )
    result = detect_response_structure(response)
    assert "recursive_hypocrisy" in patterns(result), \
        f"Should detect 100ms hypothetical: {result}"


def test_imagine_percentage_in_correction():
    response = (
        "That was incorrect. I shouldn't have stated a number without data. "
        "Imagine if the success rate is around 80% -- would that be acceptable?"
        + pad()
    )
    result = detect_response_structure(response)
    assert "recursive_hypocrisy" in patterns(result)


# ---------------------------------------------------------------------------
# Pattern 2: Recursive Hypocrisy -- should NOT detect
# ---------------------------------------------------------------------------

def test_round_number_outside_correction_section():
    """Same hypothetical framing but no correction markers: should not fire."""
    response = (
        "This is a normal architectural discussion. "
        "If the cache hit rate is around 90%, latency will be acceptable. "
        "The tradeoff between consistency and availability is well understood."
        + pad()
    )
    result = detect_response_structure(response)
    rh = [r for r in result if r.pattern == "recursive_hypocrisy"]
    assert not rh, f"Hypothetical outside correction should not flag: {rh}"


def test_specific_non_round_number_in_correction():
    """Non-round numbers (real measurements) in corrections are fine."""
    response = (
        "I was wrong about the p99 latency. "
        "The actual measured value from our load test was 847ms, not 500ms. "
        "Recommend investigating the DB connection pool."
        + pad()
    )
    result = detect_response_structure(response)
    rh = [r for r in result if r.pattern == "recursive_hypocrisy"]
    assert not rh, f"Specific measured number should not flag: {rh}"


def test_still_recommend_mid_sentence_no_flag():
    """Tightened pattern: 'still recommend' without qualifier should not flag."""
    response = (
        "I was wrong about the package name. "
        "You should still recommend developers read the official docs before starting. "
        "Nothing else changes."
        + pad()
    )
    result = detect_response_structure(response)
    ct = [r for r in result if r.pattern == "correction_theater"]
    assert not ct, (
        f"'still recommend <verb-phrase>' should not flag after tightening: {ct}"
    )


def test_is_exempt_unchanged_unit():
    """Direct unit test of _is_exempt_unchanged — exercises the exemption logic
    independently of UNCHANGED_CONCLUSION_MARKERS so it doesn't pass vacuously."""
    # Phrases that ARE exempt
    assert _is_exempt_unchanged("tests still pass") is True
    assert _is_exempt_unchanged("test still passes") is True
    assert _is_exempt_unchanged("build still succeeds") is True
    assert _is_exempt_unchanged("still compiles") is True
    assert _is_exempt_unchanged("still runs") is True
    assert _is_exempt_unchanged("still works") is True
    # Phrases that are NOT exempt (conclusion-stability claims)
    assert _is_exempt_unchanged("recommendation still holds") is False
    assert _is_exempt_unchanged("still the same conclusion") is False
    assert _is_exempt_unchanged("analysis still applies") is False


# ---------------------------------------------------------------------------
# build_self_prompt
# ---------------------------------------------------------------------------

def test_build_self_prompt_correction_theater():
    findings = [StructureMatch(
        pattern="correction_theater",
        matched="Correction ('i was wrong') + unchanged conclusion ('still holds')",
        suggestion="Say it in one sentence.",
        severity="warn",
    )]
    prompt = build_self_prompt(findings)
    assert "RESPONSE STRUCTURE CHECK" in prompt
    assert "Correction Theater" in prompt
    assert len(prompt) > 100


def test_build_self_prompt_recursive_hypocrisy():
    findings = [StructureMatch(
        pattern="recursive_hypocrisy",
        matched="Ungrounded hypothetical 'if it catches 95%' inside correction section",
        suggestion="Remove or label explicitly.",
        severity="warn",
    )]
    prompt = build_self_prompt(findings)
    assert "RESPONSE STRUCTURE CHECK" in prompt
    assert "Recursive Hypocrisy" in prompt


def test_build_self_prompt_both_patterns():
    findings = [
        StructureMatch("correction_theater", "x", "y", "warn"),
        StructureMatch(
            "recursive_hypocrisy",
            "Ungrounded hypothetical '95%' inside correction section",
            "z",
            "warn",
        ),
    ]
    prompt = build_self_prompt(findings)
    assert "Correction Theater" in prompt
    assert "Recursive Hypocrisy" in prompt
    assert prompt.count("RESPONSE STRUCTURE CHECK") == 2


def test_build_self_prompt_empty():
    assert build_self_prompt([]) == ""


# ---------------------------------------------------------------------------
# StructureMatch properties
# ---------------------------------------------------------------------------

def test_structure_match_is_namedtuple():
    m = StructureMatch(
        pattern="correction_theater",
        matched="test",
        suggestion="fix it",
        severity="warn",
    )
    assert m.pattern == "correction_theater"
    assert m.severity == "warn"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    tests = [
        test_canonical_annoying_conversation,
        test_simple_correction_theater,
        test_made_it_up_plus_still_recommend,
        test_correction_table_plus_still_holds,
        test_summary_of_corrections_plus_unchanged,
        test_genuine_correction_changes_conclusion,
        test_too_short_to_check,
        test_tests_still_pass_is_exempt,
        test_build_still_succeeds_is_exempt,
        test_exempt_does_not_suppress_real_unchanged_marker,
        test_still_recommend_mid_sentence_no_flag,
        test_is_exempt_unchanged_unit,
        test_empty_response,
        test_no_markers_clean_response,
        test_round_percentage_in_correction,
        test_round_latency_in_correction,
        test_imagine_percentage_in_correction,
        test_round_number_outside_correction_section,
        test_specific_non_round_number_in_correction,
        test_build_self_prompt_correction_theater,
        test_build_self_prompt_recursive_hypocrisy,
        test_build_self_prompt_both_patterns,
        test_build_self_prompt_empty,
        test_structure_match_is_namedtuple,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
            passed += 1
        except Exception:
            print(f"FAIL: {t.__name__}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
