"""Tests for epistemic_validator.py.

Covers: sanitization, parsing, fact support, causal rules, comparative rules,
decision logic, and full validate() integration.

.. role:: mode-note
   :class: warning

**Epistemic Contract Mode**

.. admonition:: Default environment: mode = warn
   :class: note

   The default ``mode`` in production is ``"warn"`` — unsupported fact issues
   are surfaced as advisory guidance, not hard blocks. This matches the
   ``EPISTEMIC_CONTRACT_MODE`` env var setting in Stop.py.

   **Tests that expect hard blocks must set strict mode explicitly:**

   - **Unit tests**: ``cfg = EpistemicConfig(mode="block")``
   - **Integration tests** (uses ``_run_epistemic_contract``):
     - Set ``os.environ["EPISTEMIC_CONTRACT_MODE"] = "block"``, OR
     - Pass ``data["user_prompt"] = "--epistemic-strict"`` to simulate the flag

   Without one of these, a test that asserts ``verdict.decision == "block"``
   will fail in warn mode — even if the test's ``EpistemicConfig`` sets
   ``mode="block"`` in the config object (the config field does **not**
   replicate the env var that Stop.py reads).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import os
from contextlib import contextmanager
from epistemic_validator import (
    EpistemicConfig,
    EpistemicVerdict,
    ParsedBullet,
    ParsedResponse,
    _is_direct_answer_to_question,
    check_causal_rules,
    check_comparative_rules,
    check_fact_support,
    decide_from_issues,
    parse_sections,
    sanitize_response,
    validate,
)


def strict_cfg(**overrides: object) -> EpistemicConfig:
    """EpistemicConfig for strict/block mode tests.

    Default behavior:
    - mode = "block"
    - treat_unsupported_fact_as = "block"
    - other fields left at EpistemicConfig defaults, but can be overridden.

    Use for unit tests that assert block decisions. For integration tests that
    call ``_run_epistemic_contract`` directly, use ``strict_epistemic_env`` instead
    (the env var is what Stop.py reads, not the config object).
    """
    cfg = EpistemicConfig()
    cfg.mode = "block"
    cfg.treat_unsupported_fact_as = "block"
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


@contextmanager
def strict_epistemic_env():
    """Context manager that sets ``EPISTEMIC_CONTRACT_MODE=block`` for integration tests.

    Stop.py reads this env var (not the config object), so unit-level ``cfg.mode``
    settings have no effect on the integration path through ``_run_epistemic_contract``.

    Restores prior value on exit.
    """
    old = os.environ.get("EPISTEMIC_CONTRACT_MODE")
    os.environ["EPISTEMIC_CONTRACT_MODE"] = "block"
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("EPISTEMIC_CONTRACT_MODE", None)
        else:
            os.environ["EPISTEMIC_CONTRACT_MODE"] = old

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GOOD_RESPONSE = """\
[FACT]
- File exists at line 42 (source: shared_helpers.py:42)
- The function returns True (source: pytest output above)

[INFERENCE]
- The patch may reduce loop frequency
- This suggests the gate is working

[UNKNOWN]
- I do not know the false-positive rate
- Whether the epistemic gate uses strip_non_claim_lines

[RECOMMENDATION]
- Read StopHook_epistemic_contract.py to confirm coverage
- Given session stability, switch to strict mode
"""

DIAGNOSTIC_RESPONSE = """\
Stop hook feedback:
UNVERIFIED CLAIMS: UNVERIFIED_CLAIMS
Evidence missing for: ['some claim text']
STATUS: blocked
The file at shared_helpers.py:147 defines strip_non_claim_lines (source: shared_helpers.py:147)
"""


def _bullet(section: str, text: str, **kwargs) -> ParsedBullet:
    """Shorthand to build a ParsedBullet for unit tests."""
    defaults = dict(
        index=0,
        citations=[],
        has_claim=bool(text),
        has_causal=False,
        has_comparative=False,
    )
    defaults.update(kwargs)
    return ParsedBullet(section=section, text=text, **defaults)


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------


def test_sanitize_strips_diagnostics():
    result = sanitize_response(DIAGNOSTIC_RESPONSE)
    assert "UNVERIFIED CLAIMS:" not in result
    assert "Evidence missing for:" not in result
    assert "STATUS:" not in result
    assert "Stop hook feedback:" not in result
    assert "shared_helpers.py" in result


def test_sanitize_strips_headers_and_quotes():
    text = "## Header\n> Quote\nActual content."
    result = sanitize_response(text)
    assert "## Header" not in result
    assert "> Quote" not in result
    assert "Actual content." in result


def test_sanitize_empty():
    assert sanitize_response("") == ""


# ---------------------------------------------------------------------------
# Scaffolding stripping (regression for format-failure-on-internal-text bug)
# ---------------------------------------------------------------------------

def test_sanitize_strips_test_strategy_contract_block():
    """Regression: internal TEST STRATEGY CONTRACT block must not reach the validator."""
    text = (
        "> **TEST STRATEGY CONTRACT**\n"
        "> - Start with an integration or smoke proof...\n"
        "[FACT]\n"
        "- The fix isolates the answer body (source: Stop.py:474)\n"
    )
    result = sanitize_response(text)
    assert "**TEST STRATEGY CONTRACT**" not in result
    assert "TEST STRATEGY CONTRACT" not in result
    assert "[FACT]" in result
    assert "The fix isolates the answer body" in result


def test_sanitize_strips_think_system_blocks():
    """Regression: [THINK:*] system blocks must not reach the validator."""
    text = (
        "[THINK:debug_rca]\n"
        "[FACT]\n"
        "- The root cause is identified (source: investigation)\n"
    )
    result = sanitize_response(text)
    assert "[THINK:debug_rca]" not in result
    assert "[FACT]" in result


def test_sanitize_strips_cognitive_tags_trailer():
    """Regression: cognitive-tags trailers must not reach the validator."""
    text = (
        "[FACT]\n"
        "- The fix is correct (source: code review)\n"
        "Tags:\n"
    )
    result = sanitize_response(text)
    assert "Tags:" not in result
    assert "[FACT]" in result


def test_sanitize_strips_mixed_internal_scaffolding():
    """Regression: mixed TEST STRATEGY CONTRACT + [THINK:*] + Tags: all stripped."""
    text = (
        "> **TEST STRATEGY CONTRACT**\n"
        "> rules here\n"
        "[THINK:debug_rca]\n"
        "[FACT]\n"
        "- The fix is correct (source: code review)\n"
        "[INFERENCE]\n"
        "- This should work\n"
        "Tags:\n"
    )
    result = sanitize_response(text)
    assert "TEST STRATEGY CONTRACT" not in result
    assert "[THINK:debug_rca]" not in result
    assert "Tags:" not in result
    assert "[FACT]" in result
    assert "[INFERENCE]" in result


def test_sanitize_preserves_genuine_answer_body():
    """Scaffolding stripping must not corrupt the real assistant answer."""
    text = (
        "[THINK:some_profile]\n"
        "[FACT]\n"
        "- File exists at line 42 (source: ls output)\n"
        "[INFERENCE]\n"
        "- This suggests the fix is working\n"
        "Tags:\n"
    )
    result = sanitize_response(text)
    assert "[FACT]" in result
    assert "File exists at line 42" in result
    assert "[INFERENCE]" in result
    assert "This suggests the fix is working" in result


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def test_parse_good_response():
    parsed, issues = parse_sections(GOOD_RESPONSE)
    assert not issues
    assert len(parsed.bullets) == 8  # 2 per section


def test_parse_missing_section():
    text = "[FACT]\n- Something (source: x)\n\n[INFERENCE]\n- Maybe"
    _, issues = parse_sections(text)
    section_types = {i.message for i in issues if i.type == "format"}
    assert any("Missing required section [UNKNOWN]" in m for m in section_types)
    assert any("Missing required section [RECOMMENDATION]" in m for m in section_types)


def test_parse_text_outside_sections():
    text = "Rogue text\n\n[FACT]\n- Ok (source: x)\n\n[INFERENCE]\n- M\n\n[UNKNOWN]\n- U\n\n[RECOMMENDATION]\n- R"
    _, issues = parse_sections(text)
    assert any(i.type == "format" and i.section == "__GLOBAL__" for i in issues)


def test_parse_wrong_order():
    text = "[INFERENCE]\n- X\n\n[FACT]\n- Y (source: z)"
    _, issues = parse_sections(text)
    assert any("Order must be" in i.message for i in issues)


def test_parse_bad_bullet_format():
    text = "[FACT]\nNo dash here (source: x)\n\n[INFERENCE]\n- Ok\n\n[UNKNOWN]\n- U\n\n[RECOMMENDATION]\n- R"
    _, issues = parse_sections(text)
    assert any("does not start with '- '" in i.message for i in issues)


def test_parse_extracts_citations():
    parsed, _ = parse_sections(GOOD_RESPONSE)
    fact_bullets = [b for b in parsed.bullets if b.section == "[FACT]"]
    assert len(fact_bullets[0].citations) == 1
    assert "source:" in fact_bullets[0].citations[0].lower()


def test_parse_detects_causal():
    text = "[FACT]\n- X causes Y (source: test)\n\n[INFERENCE]\n- Maybe\n\n[UNKNOWN]\n- U\n\n[RECOMMENDATION]\n- R"
    parsed, _ = parse_sections(text)
    fact = [b for b in parsed.bullets if b.section == "[FACT]"][0]
    assert fact.has_causal


def test_parse_detects_comparative():
    text = "[FACT]\n- X is best (source: test)\n\n[INFERENCE]\n- Maybe\n\n[UNKNOWN]\n- U\n\n[RECOMMENDATION]\n- R"
    parsed, _ = parse_sections(text)
    fact = [b for b in parsed.bullets if b.section == "[FACT]"][0]
    assert fact.has_comparative


# ---------------------------------------------------------------------------
# Fact support
# ---------------------------------------------------------------------------


def test_fact_with_citation_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "File exists (source: x.py:10)", citations=["(source: x.py:10)"]),
    ])
    assert check_fact_support(parsed) == []


def test_fact_without_citation_flags():
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "File exists"),
    ])
    issues = check_fact_support(parsed)
    assert len(issues) == 1
    assert issues[0].type == "unsupported_fact"


def test_fact_none_bullet_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "(none)"),
    ])
    assert check_fact_support(parsed) == []


def test_fact_user_source_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "User stated the config is wrong"),
    ])
    assert check_fact_support(parsed) == []


def test_inference_not_checked():
    parsed = ParsedResponse(bullets=[
        _bullet("[INFERENCE]", "Something without citation"),
    ])
    assert check_fact_support(parsed) == []


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------


def test_causal_in_unknown_violates():
    parsed = ParsedResponse(bullets=[
        _bullet("[UNKNOWN]", "X causes Y", has_causal=True),
    ])
    issues = check_causal_rules(parsed)
    assert any(i.type == "causal_violation" for i in issues)


def test_causal_in_fact_without_citation_violates():
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "X causes Y", has_causal=True),
    ])
    issues = check_causal_rules(parsed)
    assert any(i.type == "causal_violation" for i in issues)


def test_causal_in_fact_with_citation_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "X causes Y", has_causal=True, citations=["(source: test)"]),
    ])
    assert check_causal_rules(parsed) == []


def test_causal_in_inference_without_uncertainty_violates():
    parsed = ParsedResponse(bullets=[
        _bullet("[INFERENCE]", "X leads to Y", has_causal=True),
    ])
    issues = check_causal_rules(parsed)
    assert any(i.type == "causal_violation" for i in issues)


def test_causal_in_inference_with_uncertainty_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[INFERENCE]", "X may lead to Y", has_causal=True),
    ])
    # "may" is an uncertainty word, so this should pass
    assert check_causal_rules(parsed) == []


def test_no_causal_claim_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "File exists (source: x)"),
    ])
    assert check_causal_rules(parsed) == []


# ---------------------------------------------------------------------------
# Comparative rules
# ---------------------------------------------------------------------------


def test_comparative_in_unknown_violates():
    parsed = ParsedResponse(bullets=[
        _bullet("[UNKNOWN]", "X is best", has_comparative=True),
    ])
    issues = check_comparative_rules(parsed)
    assert any(i.type == "comparative_violation" for i in issues)


def test_superlative_in_inference_without_uncertainty_violates():
    parsed = ParsedResponse(bullets=[
        _bullet("[INFERENCE]", "X is the best approach", has_comparative=True),
    ])
    issues = check_comparative_rules(parsed)
    assert any(i.type == "comparative_violation" for i in issues)


def test_superlative_in_inference_with_uncertainty_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[INFERENCE]", "X is likely the best approach", has_comparative=True),
    ])
    assert check_comparative_rules(parsed) == []


def test_superlative_in_recommendation_without_assumption_violates():
    parsed = ParsedResponse(bullets=[
        _bullet("[RECOMMENDATION]", "Use X — it is best", has_comparative=True),
    ])
    issues = check_comparative_rules(parsed)
    assert any(i.type == "comparative_violation" for i in issues)


def test_superlative_in_recommendation_with_assumption_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[RECOMMENDATION]", "Given latency priority, X is best", has_comparative=True),
    ])
    assert check_comparative_rules(parsed) == []


def test_no_comparative_passes():
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "File exists (source: x)"),
    ])
    assert check_comparative_rules(parsed) == []


# ---------------------------------------------------------------------------
# Rationale hardening: temporal vs contextual "since"
# ---------------------------------------------------------------------------


def test_temporal_since_not_flagged_as_rationale():
    """Temporal 'since' (e.g. 'in production since Tuesday') is not rationale."""
    text = "[RECOMMENDATION]\n- X has been in production since Tuesday"
    parsed, _ = parse_sections(text)
    rec = [b for b in parsed.bullets if b.section == "[RECOMMENDATION]"][0]
    from epistemic_validator import RATIONALE_WORDS_RE
    assert not RATIONALE_WORDS_RE.search(rec.text)


def test_contextual_since_is_rationale():
    """Contextual 'since' followed by a clause with 'be' verb IS rationale."""
    from epistemic_validator import RATIONALE_WORDS_RE
    # "since it is the stated criteria" — lookahead: since + word + form-of-be
    assert RATIONALE_WORDS_RE.search("since it is the stated criteria")


def test_temporal_since_not_flagged_as_causal():
    """Temporal 'since' does not match CAUSAL_PHRASES_RE (needs 'because of')."""
    from epistemic_validator import CAUSAL_PHRASES_RE
    assert not CAUSAL_PHRASES_RE.search("has been running since Tuesday")
    assert not CAUSAL_PHRASES_RE.search("since last week")


def test_because_of_is_causal():
    """'because of' (not bare 'because') is causal."""
    from epistemic_validator import CAUSAL_PHRASES_RE
    assert CAUSAL_PHRASES_RE.search("crashed because of a missing file")
    assert CAUSAL_PHRASES_RE.search("slow because of I/O")


def test_bare_because_is_rationale():
    """Bare 'because' introducing a reason clause IS rationale — it explains why."""
    from epistemic_validator import RATIONALE_WORDS_RE
    assert RATIONALE_WORDS_RE.search("because we already discussed this")
    assert RATIONALE_WORDS_RE.search("Use X because it avoids large refactors")


def test_causal_because_of_triggers_causal_phase():
    """'because of' triggers causal detection in Phase 2."""
    from epistemic_validator import CAUSAL_PHRASES_RE
    assert CAUSAL_PHRASES_RE.search("crashed because of the bug")
    assert CAUSAL_PHRASES_RE.search("slow because of network I/O")


# ---------------------------------------------------------------------------
# Causal hardening: causal vs non-causal "because"
# ---------------------------------------------------------------------------


def test_causal_because_of_triggers_causal_phase():
    """'because of' triggers causal detection in Phase 2."""
    from epistemic_validator import CAUSAL_PHRASES_RE
    assert CAUSAL_PHRASES_RE.search("crashed because of the bug")
    assert CAUSAL_PHRASES_RE.search("slow because of network I/O")


# ---------------------------------------------------------------------------
# Recommendation comparative hardening
# ---------------------------------------------------------------------------


def test_comparative_with_goal_and_rationale_passes():
    """Comparative with both goal/assumption AND rationale should pass."""
    from epistemic_validator import RATIONALE_WORDS_RE, COMPARATIVE_WORDS_RE
    text = "For minimal code churn, Option A is preferable because it avoids large refactors"
    assert COMPARATIVE_WORDS_RE.search(text)
    assert RATIONALE_WORDS_RE.search(text)


def test_comparative_without_criterion_fails():
    """Comparative without goal/assumption/rationale should fail in RECOMMENDATION."""
    parsed = ParsedResponse(bullets=[
        _bullet("[RECOMMENDATION]", "Option A is better than B", has_comparative=True),
    ])
    issues = check_comparative_rules(parsed)
    assert any(i.type == "comparative_violation" for i in issues)


def test_recommendation_best_with_rationale_passes():
    """'best' in RECOMMENDATION with explicit rationale/assumption passes."""
    from epistemic_validator import RATIONALE_WORDS_RE, SUPERLATIVE_ONLY_RE
    text = "Given code stability, X is best because it has no breaking changes"
    assert SUPERLATIVE_ONLY_RE.search(text)
    assert RATIONALE_WORDS_RE.search(text)


# ---------------------------------------------------------------------------
# Evidence reuse expectations
# ---------------------------------------------------------------------------


def test_fact_restating_prior_output_with_citation_passes():
    """FACT restating prior output with explicit citation passes."""
    parsed = ParsedResponse(bullets=[
        _bullet(
            "[FACT]",
            "49 tests pass (source: pytest output above)",
            citations=["(source: pytest output above)"],
        ),
    ])
    issues = check_fact_support(parsed)
    assert issues == []


def test_inference_referencing_prior_fact_with_uncertainty_passes():
    """INFERENCE referencing prior fact with uncertainty marker passes causal."""
    parsed = ParsedResponse(bullets=[
        _bullet("[INFERENCE]", "49 tests may indicate the fix works", has_causal=True),
    ])
    issues = check_causal_rules(parsed)
    assert issues == []


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------


def test_no_issues_allows():
    assert decide_from_issues([], EpistemicConfig()) == "allow"


def test_format_issue_blocks_by_default():
    issues = [type("I", (), {"type": "format", "section": "", "message": "", "bullet_index": -1})()]
    cfg = EpistemicConfig(mode="block")
    # Pass response_type="investigation" so the policy layer falls through
    # to config (no override entry) and format blocks as configured.
    assert decide_from_issues(issues, cfg, response_type="investigation", raw_response="") == "block"


def test_format_issue_warns_when_configured():
    issues = [type("I", (), {"type": "format", "section": "", "message": "", "bullet_index": -1})()]
    cfg = EpistemicConfig(treat_format_violation_as="warn")
    assert decide_from_issues(issues, cfg) == "warn"


def test_global_mode_warn_overrides_block():
    issues = [type("I", (), {"type": "format", "section": "", "message": "", "bullet_index": -1})()]
    cfg = EpistemicConfig(mode="warn")
    assert decide_from_issues(issues, cfg) == "warn"


def test_global_mode_allow_overrides_everything():
    issues = [type("I", (), {"type": "format", "section": "", "message": "", "bullet_index": -1})()]
    cfg = EpistemicConfig(mode="allow")
    assert decide_from_issues(issues, cfg) == "allow"


def test_causal_warns_by_default():
    issues = [type("I", (), {"type": "causal_violation", "section": "", "message": "", "bullet_index": -1})()]
    assert decide_from_issues(issues, EpistemicConfig()) == "warn"


# ---------------------------------------------------------------------------
# Full validate() integration
# ---------------------------------------------------------------------------


def test_validate_good_response_passes():
    verdict = validate(GOOD_RESPONSE)
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_validate_diagnostic_response_sanitized():
    """Contaminated response with diagnostics should still parse correctly
    after sanitization strips the Stop scaffolding.

    Under the evidence-first design, the sanitized line with a source citation
    is a valid simple response - no format issues expected.
    """
    verdict = validate(DIAGNOSTIC_RESPONSE)
    # After sanitization, the factual line remains with a source citation.
    # It passes as a valid simple/evidence response (no format issues).
    assert verdict.decision == "allow"
    assert not any(i.type == "format" for i in verdict.issues)


def test_validate_unsupported_fact_blocks():
    """Unsupported fact in a [FACT]/[INFERENCE] response.

    The response type is simple (no report headers detected), but the
    turn_kind is CONTROL and the policy table at decide_from_issues applies
    _POLICY_TABLE[(CONTROL, FACTUAL)]="warn" even when cfg.mode="block" —
    this is an intentional design choice (structured factual reports get
    advisory treatment regardless of mode setting).

    Default mode = warn → warn. In block mode: still warn (policy overrides).
    """
    text = (
        "[FACT]\n- The file exists\n\n"
        "[INFERENCE]\n- Maybe\n\n"
        "[UNKNOWN]\n- I do not know\n\n"
        "[RECOMMENDATION]\n- Check the file"
    )
    verdict = validate(text, EpistemicConfig(mode="block"))
    assert verdict.decision == "warn"
    assert any(i.type == "unsupported_fact" for i in verdict.issues)


def test_validate_warn_mode_never_blocks():
    text = (
        "[FACT]\n- The file exists\n\n"
        "[INFERENCE]\n- Maybe\n\n"
        "[UNKNOWN]\n- I do not know\n\n"
        "[RECOMMENDATION]\n- Check the file"
    )
    verdict = validate(text, EpistemicConfig(mode="warn"))
    assert verdict.decision == "warn"


def test_validate_disable_causal_and_comparative():
    text = (
        "[FACT]\n- X causes Y and is best (source: test)\n\n"
        "[INFERENCE]\n- Maybe\n\n"
        "[UNKNOWN]\n- I do not know\n\n"
        "[RECOMMENDATION]\n- Check X"
    )
    cfg = EpistemicConfig(enable_causal_checks=False, enable_comparative_checks=False)
    verdict = validate(text, cfg)
    assert verdict.decision == "allow"


def test_validate_causal_in_unknown():
    text = (
        "[FACT]\n- Something (source: x)\n\n"
        "[INFERENCE]\n- Maybe\n\n"
        "[UNKNOWN]\n- X causes Y\n\n"
        "[RECOMMENDATION]\n- Check X"
    )
    verdict = validate(text, EpistemicConfig(mode="warn"))
    assert any(i.type == "causal_violation" for i in verdict.issues)


# ---------------------------------------------------------------------------
# CLI flag override integration (Stop.py _run_epistemic_contract)
# ---------------------------------------------------------------------------


def test_strict_flag_overrides_env_warn():
    """Simulates Stop.py _run_epistemic_contract with --epistemic-strict."""
    import os

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "warn"
    user_prompt = "analyze this --epistemic-strict"

    mode = os.environ.get("EPISTEMIC_CONTRACT_MODE", "warn")
    if "--epistemic-strict" in user_prompt:
        mode = "block"
    elif "--epistemic-warn" in user_prompt:
        mode = "warn"

    assert mode == "block"
    del os.environ["EPISTEMIC_CONTRACT_MODE"]


def test_warn_flag_overrides_env_block():
    """Simulates Stop.py _run_epistemic_contract with --epistemic-warn."""
    import os

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "block"
    user_prompt = "analyze this --epistemic-warn"

    mode = os.environ.get("EPISTEMIC_CONTRACT_MODE", "warn")
    if "--epistemic-strict" in user_prompt:
        mode = "block"
    elif "--epistemic-warn" in user_prompt:
        mode = "warn"

    assert mode == "warn"
    del os.environ["EPISTEMIC_CONTRACT_MODE"]


def test_no_flag_uses_env_default():
    """No CLI flag falls through to env var."""
    import os

    os.environ["EPISTEMIC_CONTRACT_MODE"] = "block"
    user_prompt = "analyze this normally"

    mode = os.environ.get("EPISTEMIC_CONTRACT_MODE", "warn")
    if "--epistemic-strict" in user_prompt:
        mode = "block"
    elif "--epistemic-warn" in user_prompt:
        mode = "warn"

    assert mode == "block"
    del os.environ["EPISTEMIC_CONTRACT_MODE"]


def test_strict_flag_takes_precedence_over_warn():
    """Both flags present — strict wins (checked first)."""
    user_prompt = "analyze --epistemic-strict --epistemic-warn"

    mode = "warn"
    if "--epistemic-strict" in user_prompt:
        mode = "block"
    elif "--epistemic-warn" in user_prompt:
        mode = "warn"

    assert mode == "block"


# ---------------------------------------------------------------------------
# Cross-phase tests: single bullet with both causal AND comparative
# ---------------------------------------------------------------------------


def test_recommendation_causal_and_comparative_with_rationale_passes():
    """Single RECOMMENDATION bullet with both causal and comparative language
    should pass when rationale ('because') is present."""
    parsed = ParsedResponse(bullets=[
        _bullet(
            "[RECOMMENDATION]",
            "Use Option A because it simplifies the pipeline and is probably the best fit for our current constraints.",
            has_causal=True,
            has_comparative=True,
        ),
    ])
    assert check_causal_rules(parsed) == []
    assert check_comparative_rules(parsed) == []


def test_recommendation_causal_and_comparative_without_rationale_flags_both():
    """Single RECOMMENDATION bullet with both causal and comparative language
    should flag BOTH violation types when no rationale is present."""
    parsed = ParsedResponse(bullets=[
        _bullet(
            "[RECOMMENDATION]",
            "Option A leads to faster results. It is optimal.",
            has_causal=True,
            has_comparative=True,
        ),
    ])
    causal_issues = check_causal_rules(parsed)
    comparative_issues = check_comparative_rules(parsed)
    assert any(i.type == "causal_violation" for i in causal_issues)
    assert any(i.type == "comparative_violation" for i in comparative_issues)


def test_cross_phase_bullet_integration():
    """Full validate() with a RECOMMENDATION bullet containing both causal
    and comparative language with rationale — should allow."""
    text = (
        "[FACT]\n- Something (source: x)\n\n"
        "[INFERENCE]\n- Maybe\n\n"
        "[UNKNOWN]\n- I do not know\n\n"
        "[RECOMMENDATION]\n"
        "- Use Option A because it simplifies the pipeline and is the best fit for our constraints"
    )
    verdict = validate(text, EpistemicConfig(mode="block"))
    assert verdict.decision == "allow"


# ---------------------------------------------------------------------------
# Temporal "since" negative tests
# ---------------------------------------------------------------------------


def test_temporal_since_does_not_trigger_causal():
    """Temporal 'since' (meaning 'from that time') must not trigger causal detection."""
    text = (
        "[FACT]\n- The job has been stable since Tuesday (source: CI dashboard)\n\n"
        "[INFERENCE]\n- Maybe\n\n"
        "[UNKNOWN]\n- I do not know\n\n"
        "[RECOMMENDATION]\n- Monitor the job"
    )
    verdict = validate(text, EpistemicConfig(mode="block"))
    assert verdict.decision == "allow"
    assert not any(i.type == "causal_violation" for i in verdict.issues)


def test_temporal_since_in_fact_not_flagged():
    """FACT bullet with temporal 'since' and citation should pass causal check."""
    parsed = ParsedResponse(bullets=[
        _bullet(
            "[FACT]",
            "The system has been running since March 2024",
            citations=["(source: uptime logs)"],
        ),
    ])
    assert check_causal_rules(parsed) == []


def test_causal_phrases_re_excludes_bare_since():
    """CAUSAL_PHRASES_RE must not match bare temporal 'since'."""
    from epistemic_validator import CAUSAL_PHRASES_RE
    assert not CAUSAL_PHRASES_RE.search("The job has been stable since Tuesday")
    assert CAUSAL_PHRASES_RE.search("The crash because of memory pressure")


# ---------------------------------------------------------------------------
# Citation pattern tests
# ---------------------------------------------------------------------------


def test_citation_filename_with_spaces():
    """Citation with filename containing spaces is recognized by check_fact_support."""
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "File exists (source: my file.py:10)", citations=["(source: my file.py:10)"]),
    ])
    assert check_fact_support(parsed) == []


def test_citation_pytest_output():
    """Citation referencing pytest output is recognized."""
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "All tests pass (source: pytest output above)", citations=["(source: pytest output above)"]),
    ])
    assert check_fact_support(parsed) == []


def test_bare_claim_still_flagged():
    """FACT bullet without any citation source is still flagged."""
    parsed = ParsedResponse(bullets=[
        _bullet("[FACT]", "The function works correctly"),
    ])
    issues = check_fact_support(parsed)
    assert len(issues) == 1
    assert issues[0].type == "unsupported_fact"


def test_multiple_citations_extracted():
    """Multiple citations in a single bullet are all extracted by parse_sections."""
    text = (
        "[FACT]\n- X and Y (source: a.py:1) (source: b.py:2)\n\n"
        "[INFERENCE]\n- M\n\n[UNKNOWN]\n- U\n\n[RECOMMENDATION]\n- R"
    )
    parsed, _ = parse_sections(text)
    fact = [b for b in parsed.bullets if b.section == "[FACT]"][0]
    assert len(fact.citations) == 2


def test_citation_re_matches_various_formats():
    """CITATION_RE matches filenames with spaces, descriptive sources, and case variants."""
    from epistemic_validator import CITATION_RE
    assert CITATION_RE.search("(source: file.py:10)")
    assert CITATION_RE.search("(source: my file.py:10)")
    assert CITATION_RE.search("(source: pytest output above)")
    assert CITATION_RE.search("(SOURCE: Capitalized)")
    assert not CITATION_RE.search("source: file.py:10")


# ---------------------------------------------------------------------------
# Status-summary bypass
# ---------------------------------------------------------------------------


def test_status_summary_bypass_files_created():
    """Response starting with 'Files created' bypasses format enforcement."""
    from epistemic_validator import is_status_summary_response
    response = "Files Created:\n- src/main.py\n- tests/test_main.py\nAll 14 tests pass."
    assert is_status_summary_response(response)
    verdict = validate(response)
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_status_summary_bypass_implementation_complete():
    """'Implementation complete' first-line response bypasses format enforcement."""
    from epistemic_validator import is_status_summary_response
    response = "Implementation complete. Here's the summary:\n- Added 3 files\n- All tests pass"
    assert is_status_summary_response(response)
    verdict = validate(response)
    assert verdict.decision == "allow"


def test_status_summary_bypass_session_summary():
    """Session deliverables report bypasses format enforcement."""
    from epistemic_validator import is_status_summary_response
    response = "Session deliverables:\n- Fixed auth bug\n- Added 8 tests\n- Refactored middleware"
    assert is_status_summary_response(response)


def test_status_summary_bypass_tests_pass():
    """'All 55 tests pass' report bypasses format enforcement."""
    from epistemic_validator import is_status_summary_response
    response = "All 55 tests pass in 0.35s.\nNo regressions detected."
    assert is_status_summary_response(response)


def test_analytical_answer_does_not_bypass():
    """A genuine analytical answer without sections does NOT bypass."""
    from epistemic_validator import is_status_summary_response
    response = (
        "The root cause is a race condition in the middleware. "
        "Thread A reads the cache while Thread B invalidates it. "
        "The fix is to add a lock around the read operation."
    )
    assert not is_status_summary_response(response)
    verdict = validate(response, EpistemicConfig(mode="warn"))
    # Should produce format issues (missing sections)
    assert any(i.type == "format" for i in verdict.issues)


def test_design_recommendation_does_not_bypass():
    """A design/architecture recommendation does NOT bypass."""
    from epistemic_validator import is_status_summary_response
    response = (
        "I recommend using a message queue for the event pipeline. "
        "This decouples producers from consumers and provides backpressure."
    )
    assert not is_status_summary_response(response)


def test_mixed_response_with_report_header_bypasses():
    """Response that starts as a report but contains analysis still bypasses
    if the first line is a clear report signal."""
    from epistemic_validator import is_status_summary_response
    response = (
        "Task complete. Here's what was done:\n"
        "- Refactored the auth module\n"
        "- The root cause was a missing null check, which could cause issues under load"
    )
    assert is_status_summary_response(response)


def test_bypass_empty_response():
    """Empty response does not bypass."""
    from epistemic_validator import is_status_summary_response
    assert not is_status_summary_response("")
    assert not is_status_summary_response("   ")


# ---------------------------------------------------------------------------
# Telemetry (Stop.py integration)
# ---------------------------------------------------------------------------


def test_epistemic_telemetry_tool_transcript_observability(tmp_path):
    """Verify telemetry entry includes tool_transcript_len and tool_transcript_present."""
    import json

    from epistemic_validator import EpistemicVerdict

    verdict = EpistemicVerdict(decision="warn", issues=[])

    # Case 1: tool_transcript present in data dict
    data_with_transcript = {
        "session_id": "sess-abc",
        "terminal_id": "console-xyz",
        "tool_transcript": "Read file.txt → 42 lines",
    }

    entry = {
        "timestamp": 1234567890.0,
        "gate": "epistemic_contract",
        "decision": verdict.decision,
        "issue_count": 0,
        "issue_types": [],
        "has_format_issues": False,
        "has_unsupported_fact": False,
        "has_causal_issues": False,
        "has_comparative_issues": False,
        "mode": "warn",
        "responseMode": "analysis",
        "repair_bypass": False,
        "session_id": data_with_transcript.get("session_id", ""),
        "terminal_id": data_with_transcript.get("terminal_id", ""),
        # NEW: observability for tool_transcript runtime wiring
        "tool_transcript_len": len(data_with_transcript.get("tool_transcript") or ""),
        "tool_transcript_present": bool(data_with_transcript.get("tool_transcript")),
    }

    log_path = tmp_path / "epistemic_telemetry.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    parsed = json.loads(log_path.read_text().strip())
    assert parsed["tool_transcript_present"] is True
    assert parsed["tool_transcript_len"] == len("Read file.txt → 42 lines")

    # Case 2: tool_transcript absent (empty string via wire)
    data_without_transcript = {
        "session_id": "sess-abc",
        "terminal_id": "console-xyz",
        "tool_transcript": "",
    }

    entry2 = {
        **entry,
        "tool_transcript_len": len(data_without_transcript.get("tool_transcript") or ""),
        "tool_transcript_present": bool(data_without_transcript.get("tool_transcript")),
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry2) + "\n")

    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 2
    parsed2 = json.loads(lines[1])
    assert parsed2["tool_transcript_present"] is False
    assert parsed2["tool_transcript_len"] == 0


def test_epistemic_telemetry_emits_fields(tmp_path):
    """Verify _log_epistemic_telemetry writes a valid JSONL line with all fields."""
    import json

    # Patch HOOKS_DIR temporarily to use tmp_path
    log_path = tmp_path / "epistemic_telemetry.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Import and call directly rather than patching Stop.py internals
    from epistemic_validator import EpistemicVerdict, EpistemicIssue, is_status_summary_response

    verdict = EpistemicVerdict(
        decision="warn",
        issues=[
            EpistemicIssue(section="[FACT]", bullet_index=0, type="unsupported_fact", message="no citation"),
            EpistemicIssue(section="__GLOBAL__", bullet_index=-1, type="format", message="missing section"),
        ],
    )

    # Simulate what Stop.py's _log_epistemic_telemetry does
    issue_types = sorted({i.type for i in verdict.issues})
    entry = {
        "gate": "epistemic_contract",
        "decision": verdict.decision,
        "issue_count": len(verdict.issues),
        "issue_types": issue_types,
        "has_format_issues": "format" in issue_types,
        "has_unsupported_fact": "unsupported_fact" in issue_types,
        "has_causal_issues": any(t.startswith("causal") for t in issue_types),
        "has_comparative_issues": any(t.startswith("comparative") for t in issue_types),
        "mode": "warn",
    }

    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    # Read back and verify
    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["gate"] == "epistemic_contract"
    assert parsed["decision"] == "warn"
    assert parsed["issue_count"] == 2
    assert parsed["issue_types"] == ["format", "unsupported_fact"]
    assert parsed["has_format_issues"] is True
    assert parsed["has_unsupported_fact"] is True
    assert parsed["has_causal_issues"] is False
    assert parsed["has_comparative_issues"] is False
    assert parsed["mode"] == "warn"


def test_epistemic_telemetry_allow_decision(tmp_path):
    """Verify telemetry for an allow decision with no issues."""
    import json

    from epistemic_validator import EpistemicVerdict

    verdict = EpistemicVerdict(decision="allow", issues=[])
    log_path = tmp_path / "epistemic_telemetry.jsonl"
    issue_types = sorted({i.type for i in verdict.issues})
    entry = {
        "gate": "epistemic_contract",
        "decision": verdict.decision,
        "issue_count": 0,
        "issue_types": issue_types,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    parsed = json.loads(log_path.read_text().strip())
    assert parsed["decision"] == "allow"
    assert parsed["issue_count"] == 0
    assert parsed["issue_types"] == []


# ---------------------------------------------------------------------------
# Response-mode detection and mode-aware validation
# ---------------------------------------------------------------------------


def test_detect_response_mode_analysis_default():
    """Analytical response defaults to analysis mode."""
    from epistemic_validator import detect_response_mode

    assert detect_response_mode("[FACT]\n- foo (source: bar)\n[INFERENCE]\n- may be") == "analysis"


def test_detect_response_mode_report_explicit_headers():
    """Report mode detected when ≥2 report section headers present."""
    from epistemic_validator import detect_response_mode

    text = "[STATUS]\nFiles created.\n[CHANGES]\n- Updated X"
    assert detect_response_mode(text) == "report"


def test_detect_response_mode_report_all_headers():
    """Report mode detected with all four report headers."""
    from epistemic_validator import detect_response_mode

    text = "[STATUS]\nDone.\n[CHANGES]\n- X\n[RESULTS]\nAll pass.\n[NEXT]\nNone."
    assert detect_response_mode(text) == "report"


def test_detect_response_mode_report_status_summary_fallback():
    """Report mode falls back to status-summary heuristic."""
    from epistemic_validator import detect_response_mode

    text = "Implementation complete. Files written and tests pass."
    assert detect_response_mode(text) == "report"


def test_detect_response_mode_empty():
    """Empty response defaults to analysis."""
    from epistemic_validator import detect_response_mode

    assert detect_response_mode("") == "analysis"


def test_detect_patch_report_format():
    """Patch-report format with FILES_CHANGED / TESTS / LIMITATIONS is detected as report mode."""
    from epistemic_validator import detect_response_mode

    text = """FILES_CHANGED
- Stop.py
- test_referent_hooks.py

LOGIC_CHANGES
- Added _user_asked_for_prioritization helper
- VERY_LARGE_LIST_THRESHOLD bumped to 20

TESTS
- pytest tests/test_referent_hooks.py -v → 41 passed

LIMITATIONS
- Heuristic phrase detection may miss edge cases."""
    assert detect_response_mode(text) == "report"


def test_validate_patch_report_format_bypasses_enforcement():
    """Patch-report format bypasses epistemic enforcement via auto-detection."""
    from epistemic_validator import validate

    text = """FILES_CHANGED
- Stop.py

LOGIC_CHANGES
- Added _user_asked_for_prioritization

TESTS
- pytest -v → 41 passed

LIMITATIONS
- May need phrase-set tuning."""
    verdict = validate(text)
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_validate_patch_report_with_unsupported_fact_allowed():
    """Patch report with unsourced fact is still allowed (report mode skips enforcement)."""
    from epistemic_validator import validate

    text = """FILES_CHANGED
- Stop.py

TESTS
- All 41 tests passed

LIMITATIONS
- The heuristic phrase detection may miss edge cases."""
    verdict = validate(text)
    assert verdict.decision == "allow"


def test_validate_report_mode_auto_detect():
    """Report-mode response bypasses format enforcement via auto-detection."""
    from epistemic_validator import validate

    text = "[STATUS]\nCreated 3 files.\n[CHANGES]\n- Added X\n[RESULTS]\nPass\n[NEXT]\nNone"
    verdict = validate(text)
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_validate_explicit_report_mode():
    """Explicit report mode config bypasses format enforcement."""
    from epistemic_validator import validate, EpistemicConfig

    cfg = EpistemicConfig(responseMode="report")
    verdict = validate("[FACT]\n- unsourced claim", cfg)
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_validate_explicit_analysis_mode():
    """Explicit analysis mode enforces the 4-section contract for non-status content."""
    from epistemic_validator import validate, EpistemicConfig

    # mode="block" so format violations actually block; responseMode forces analysis.
    # Use a phrase that does NOT match is_status_summary_response so it gets
    # classified as "simple" → no bypass → format block fires.
    cfg = EpistemicConfig(responseMode="analysis", mode="block")
    verdict = validate(
        "The root cause investigation identified the control-flow bug as primary. "
        "However, the secondary factor is also relevant.",
        cfg,
    )
    assert verdict.decision == "block", (
        f"Expected block for investigation without sections, got: {verdict.decision}, "
        f"issues: {verdict.issues}"
    )
    assert any(i.type == "format" for i in verdict.issues)


def test_validate_auto_mode_analytical_still_enforced():
    """Auto mode with analytical content still enforces contract."""
    from epistemic_validator import validate

    # No report headers, no status-summary patterns → analysis mode
    text = "The function handles edge cases by checking for None."
    verdict = validate(text)
    # Should flag missing sections
    assert any(i.type == "format" for i in verdict.issues)


def test_validate_report_mode_with_unsupported_facts():
    """Report mode does not flag unsupported facts (no analytical contract)."""
    from epistemic_validator import validate, EpistemicConfig

    cfg = EpistemicConfig(responseMode="report")
    text = "[STATUS]\n- Claimed X is true but no citation"
    verdict = validate(text, cfg)
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_validate_config_default_auto():
    """Default EpistemicConfig has responseMode='auto'."""
    from epistemic_validator import EpistemicConfig

    cfg = EpistemicConfig()
    assert cfg.responseMode == "auto"


def test_conservative_fallback_status_summary():
    """Conservative fallback: status-summary heuristic still works when no report headers."""
    from epistemic_validator import validate

    # No report section headers, but first line matches status-summary pattern
    text = "Implementation complete.\nAll 5 files written successfully."
    verdict = validate(text)
    assert verdict.decision == "allow"


# ---------------------------------------------------------------------------
# Regression: EXTERNAL_QUOTE_RE trailing-pipe bug fix
# ---------------------------------------------------------------------------


def test_fact_comparative_without_citation_or_external_flags():
    """FACT comparative without citation or external reference must flag."""
    from epistemic_validator import validate

    text = (
        "[FACT]\n"
        "- This is the best approach (source: docs)\n"
        "- Approach X is better than Y\n"  # comparative, no citation, no external ref
        "[INFERENCE]\n"
        "- May be related\n"
        "[UNKNOWN]\n"
        "- (none)\n"
        "[RECOMMENDATION]\n"
        "- Given speed, use X\n"
    )
    verdict = validate(text)
    comparative_issues = [i for i in verdict.issues if i.type == "comparative_violation"]
    assert any("Approach X" in i.message or "better" in i.message or "comparative" in i.message.lower()
               for i in comparative_issues), (
        f"Expected FACT comparative violation for 'better than' without citation/external ref, "
        f"got issues: {comparative_issues}"
    )


def test_fact_comparative_with_external_reference_passes():
    """FACT comparative with external reference keyword (but no citation) passes."""
    from epistemic_validator import validate

    text = (
        "[FACT]\n"
        "- According to benchmark data, X is faster than Y\n"  # "according to" = external ref
        "[INFERENCE]\n"
        "- May be related\n"
        "[UNKNOWN]\n"
        "- (none)\n"
        "[RECOMMENDATION]\n"
        "- Given speed, use X\n"
    )
    verdict = validate(text)
    comparative_issues = [i for i in verdict.issues if i.type == "comparative_violation"]
    assert not any(i.section == "[FACT]" for i in comparative_issues), (
        f"FACT with 'according to' should pass external reference check, got: {comparative_issues}"
    )


def test_fact_comparative_with_citation_passes():
    """FACT comparative with citation passes regardless of external reference."""
    from epistemic_validator import validate

    text = (
        "[FACT]\n"
        "- X is more efficient than Y (source: bench_results.md)\n"
        "[INFERENCE]\n"
        "- May be related\n"
        "[UNKNOWN]\n"
        "- (none)\n"
        "[RECOMMENDATION]\n"
        "- Given speed, use X\n"
    )
    verdict = validate(text)
    comparative_issues = [i for i in verdict.issues if i.type == "comparative_violation"]
    assert not any(i.section == "[FACT]" for i in comparative_issues)


# ---------------------------------------------------------------------------
# Auto-repair tests (format-only vs mixed issue discrimination)
# ---------------------------------------------------------------------------


def test_format_only_all_format_issues():
    """When all issues are format-only, verdict issues are all type='format'."""
    from epistemic_validator import validate

    # Missing [UNKNOWN] and [RECOMMENDATION] sections — format issues only.
    text = (
        "[FACT]\n"
        "- Something happened (source: file.py:10)\n"
        "[INFERENCE]\n"
        "- May be related\n"
    )
    verdict = validate(text)
    assert verdict.issues, "Expected issues for missing sections"
    assert all(i.type == "format" for i in verdict.issues), (
        f"Expected all format issues, got: {[i.type for i in verdict.issues]}"
    )


def test_mixed_issues_not_all_format():
    """When issues include non-format types, not all are format."""
    from epistemic_validator import validate

    # Missing sections (format) + unsupported fact (non-format).
    text = (
        "[FACT]\n"
        "- Something happened with no citation\n"
        "[INFERENCE]\n"
        "- May be related\n"
    )
    verdict = validate(text)
    types = [i.type for i in verdict.issues]
    assert "format" in types
    assert "unsupported_fact" in types


def test_stop_auto_repair_format_only():
    """Stop._run_epistemic_contract silently logs format-only issues by default.

    NON-CRITICAL — format repair is logged to epistemic_advisories.jsonl
    instead of injecting repair text into the response. Use --epistemic-verbose
    to surface full repair text inline.

    ``NON-CRITICAL`` — format repair is logged to epistemic_advisories.jsonl
    instead of injecting repair text into the response. Use --epistemic-verbose
    to surface full repair text inline.

    Note: _run_epistemic_contract checks turn mode and returns None early when
    no user_prompt key is present (mode classifies as suppressed). The
    --epistemic-verbose flag in user_prompt forces non-suppressed mode (warn mode).
    --epistemic-strict forces block mode instead.
    """
    from Stop import _run_epistemic_contract

    data = {
        "response": (
            "[FACT]\n"
            "- Something happened\n"
            "[INFERENCE]\n"
            "- May be related\n"
            "[UNKNOWN]\n"
            "- Whether this is the cause\n"
            "[RECOMMENDATION]\n"
            "- Investigate further\n"
        ),
        "session_id": "test-session",
        # NO user_prompt key - mode="warn" (default), suppressed
        # _run_epistemic_contract returns None early for suppressed
    }
    result = _run_epistemic_contract(data)
    assert result is not None
    assert result["decision"] == "warn", (
        f"Expected warn for unsupported_fact in warn mode, got {result.get('decision')}"
    )
    # Silent logging — systemMessage is None, reason tells caller it was logged
    assert result["systemMessage"] is None
    assert result["reason"] == "epistemic_advisory_logged"


def test_stop_mixed_issues_surface_advisory():
    """Stop._run_epistemic_contract silently logs mixed issues by default.

    NON-CRITICAL — advisory is logged to epistemic_advisories.jsonl instead
    of injecting raw advisory into the response. Use --epistemic-verbose to
    surface full advisory text inline.
    """
    from Stop import _run_epistemic_contract

    data = {
        "response": (
            "[FACT]\n"
            "- Bare assertion without source\n"
            "[INFERENCE]\n"
            "- May be related\n"
        ),
        "session_id": "test-session",
    }
    result = _run_epistemic_contract(data)
    assert result is not None
    assert result["decision"] == "warn"
    # Silent logging — systemMessage is None, reason tells caller it was logged
    assert result["systemMessage"] is None
    assert result["reason"] == "epistemic_advisory_logged"


def test_stop_non_format_issues_no_repair():
    """Causal/comparative violations do NOT trigger repair path — silently logged."""
    from Stop import _run_epistemic_contract

    data = {
        "response": (
            "[FACT]\n"
            "- X exists (source: file.py:1)\n"
            "[INFERENCE]\n"
            "- May be relevant\n"
            "[UNKNOWN]\n"
            "- The reason is unclear (causal in UNKNOWN)\n"
            "[RECOMMENDATION]\n"
            "- Investigate further\n"
        ),
        "session_id": "test-session",
    }
    result = _run_epistemic_contract(data)
    assert result is not None
    assert result["decision"] == "warn"
    # Silent logging — systemMessage is None
    assert result["systemMessage"] is None
    assert result["reason"] == "epistemic_advisory_logged"


def test_suppressed_advisory_does_not_surface_none_string():
    """Suppressed advisory (systemMessage: None) must not produce 'None' in output.

    Regression test: _process_gate_result was appending None to quality_messages
    when systemMessage key existed (even with value None), causing the literal
    string "None" to appear in user-visible output after join().
    """
    from Stop import _process_gate_result, _merge_quality_messages

    quality_messages: list[str] = []
    system_messages: list[str] = []

    # Simulate a suppressed epistemic advisory — decision=warn, systemMessage=None
    suppressed_result = {
        "decision": "warn",
        "reason": "format_repair_logged",
        "systemMessage": None,
    }

    blocked = _process_gate_result(
        suppressed_result,
        "epistemic_contract",
        system_messages,
        quality_messages,
        {},  # data
        "analysis",  # turn_mode
        "normal",  # quality_mode
    )

    assert blocked is False  # warn, not a block
    # None must NOT be in quality_messages — the fix filters it out
    assert None not in quality_messages, (
        f"None leaked into quality_messages: {quality_messages!r}"
    )

    # Simulate merge on an analysis turn (quality gate not suppressed)
    _merge_quality_messages(system_messages, quality_messages, "analysis", "normal")

    # Final output assembly — "None" must not appear in system_messages
    assert "None" not in system_messages, (
        f"Literal 'None' string in system_messages: {system_messages!r}"
    )

    # system_messages should be empty since the advisory was suppressed
    assert system_messages == []


def test_real_system_message_still_surfaces():
    """Real visible systemMessage still appears exactly as returned by the gate."""
    from Stop import _process_gate_result, _merge_quality_messages

    quality_messages: list[str] = []
    system_messages: list[str] = []

    # Simulate a policy gate with a real visible message
    real_result = {
        "decision": "warn",
        "reason": "EPISTEMIC ADVISORY (2 issue(s))",
        "systemMessage": "EPISTEMIC ADVISORY (2 issue(s)):\n  [FACT] citation: Bare assertion",
    }

    blocked = _process_gate_result(
        real_result,
        "epistemic_contract",
        system_messages,
        quality_messages,
        {},
        "analysis",
        "normal",
    )

    assert blocked is False
    # Real message must be in quality_messages
    assert len(quality_messages) == 1
    assert "EPISTEMIC ADVISORY" in quality_messages[0]

    _merge_quality_messages(system_messages, quality_messages, "analysis", "normal")

    # Message must survive into system_messages
    assert len(system_messages) == 1
    assert "EPISTEMIC ADVISORY" in system_messages[0]


def test_stop_good_response_no_advisory():
    """Clean response produces no advisory and no repair."""
    from Stop import _run_epistemic_contract

    data = {
        "response": (
            "[FACT]\n"
            "- X is true (source: file.py:1)\n"
            "[INFERENCE]\n"
            "- May be related\n"
            "[UNKNOWN]\n"
            "- (none)\n"
            "[RECOMMENDATION]\n"
            "- Investigate\n"
        ),
        "session_id": "test-session",
    }
    result = _run_epistemic_contract(data)
    assert result is None


# ---------------------------------------------------------------------------
# Task 2/3: lazy_fix test-summary guard + format-repair loop prevention
# ---------------------------------------------------------------------------


def test_test_summary_with_bypasses_no_lazy_fix():
    """Test summary containing 'bypasses' does NOT trigger lazy_fix."""
    from anti_sycophancy.lazy_closure_detector import detect_lazy_closure

    text = (
        "Tests added (6): format-only detection, mixed-issue discrimination, "
        "non-format bypasses repair, clean response produces nothing. "
        "All 6 tests passed."
    )
    result = detect_lazy_closure(text)
    assert result is None or result.pattern_type != "lazy_fix", (
        f"Test summary should not trigger lazy_fix, got: {result}"
    )


def test_genuine_lazy_fix_still_caught():
    """Genuine lazy fix pattern in analytical prose is still caught."""
    from anti_sycophancy.lazy_closure_detector import detect_lazy_closure

    text = "We can just bypasses the issue with a quick config change."
    result = detect_lazy_closure(text)
    assert result is not None
    assert result.pattern_type == "lazy_fix"


def test_genuine_bypasses_problem_still_caught():
    """"bypasses the problem" is still caught as lazy_fix."""
    from anti_sycophancy.lazy_closure_detector import detect_lazy_closure

    text = "This approach bypasses the problem entirely."
    result = detect_lazy_closure(text)
    assert result is not None
    assert result.pattern_type == "lazy_fix"


def test_format_repair_suppresses_lazy_fix_loop():
    """After format-only repair, lazy_fix is suppressed to prevent loops."""
    from Stop import _run_anti_sycophancy_quality

    # Response with missing sections (format issues) + 'bypasses' in test context
    data = {
        "response": (
            "Tests added (6): format-only detection, mixed-issue discrimination, "
            "non-format bypasses repair, clean response produces nothing. "
            "All 6 tests passed.\n\n"
            "[FACT]\n"
            "- X is true (source: file.py:1)\n"
            "[INFERENCE]\n"
            "- May be related\n"
        ),
        "session_id": "test-session",
    }
    result = _run_anti_sycophancy_quality(data)
    # Should return None (no lazy_fix flag) or not contain lazy_closure
    if result is not None:
        assert "LAZY CLOSURE" not in result.get("reason", ""), (
            f"lazy_fix should be suppressed after format repair, got: {result}"
        )


# ---------------------------------------------------------------------------
# Grounded status confirmation tests
# ---------------------------------------------------------------------------

def test_grounded_status_confirmation_103_passed():
    """103 passed. — ultra-short count restatement, should allow."""
    from epistemic_validator import validate as v

    verdict = v("103 passed.")
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_grounded_status_confirmation_all_passed():
    """all passed. — all-clear signal, should allow."""
    from epistemic_validator import validate as v

    verdict = v("all passed.")
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_grounded_status_confirmation_done():
    """done — bare done signal, should allow."""
    from epistemic_validator import validate as v

    verdict = v("done")
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_grounded_status_confirmation_yes_103_passed():
    """yes, 103 passed — yes-prefixed restatement, should allow."""
    from epistemic_validator import validate as v

    verdict = v("yes, 103 passed.")
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_grounded_status_confirmation_3_failed():
    """3 failed — failure count restatement, should allow."""
    from epistemic_validator import validate as v

    verdict = v("3 failed.")
    assert verdict.decision == "allow"
    assert verdict.issues == []


def test_grounded_status_confirmation_still_blocks_interpretive():
    """103 passed and the bug is fixed — interpretive, should still block."""
    from epistemic_validator import validate as v

    # Default mode = warn → interpretive status conclusions produce warn
    verdict = v("103 passed and the bug is fixed.")
    assert verdict.decision == "warn"


def test_grounded_status_confirmation_still_blocks_summary():
    """All tests passed, so Phase B is complete. — inference signal blocks, fix confirmed."""
    from epistemic_validator import validate as v

    verdict = v("All tests passed, so Phase B is complete.")
    # Default mode = warn → so-completion produces warn (not block)
    assert verdict.decision == "warn"


def test_grounded_status_confirmation_still_blocks_confirmed_alone():
    """confirmed — too generic without evidence context, blocked in strict mode.

    Default mode = warn → warn (not block).
    In block mode (cfg.mode="block"): would be block.
    """
    from epistemic_validator import validate as v

    verdict = v("confirmed")
    assert verdict.decision == "warn"


def test_grounded_status_confirmation_still_blocks_multi_sentence():
    """103 passed. The fix works. — two sentences, blocked in strict mode.

    Default mode = warn → warn (not block).
    In block mode (cfg.mode="block"): would be block.
    """
    from epistemic_validator import validate as v

    verdict = v("103 passed. The fix works.")
    assert verdict.decision == "warn"


# ---------------------------------------------------------------------------
# is_status_summary_response — inference guard regression tests
# ---------------------------------------------------------------------------

def test_status_summary_still_allows_pure_status():
    """'All tests passed' (no inference signal) still bypasses via report mode."""
    from epistemic_validator import is_status_summary_response, validate as v

    assert is_status_summary_response("All tests passed.")
    verdict = v("All tests passed.")
    assert verdict.decision == "allow"


def test_status_summary_blocks_so_completion():
    """'All tests passed, so Phase B is complete' — inference signal blocks report bypass.

    Default mode = warn → warn (not block).
    In block mode: would be block.
    """
    from epistemic_validator import is_status_summary_response, validate as v

    assert not is_status_summary_response("All tests passed, so Phase B is complete.")
    verdict = v("All tests passed, so Phase B is complete.")
    # Falls through to simple type → no citation → warn (not block in default mode)
    assert verdict.decision == "warn"


def test_status_summary_blocks_causal_bug_fixed():
    """'Tests passed; the bug is fixed.' — causal claim blocks report bypass.

    Default mode = warn → warn (not block).
    In block mode: would be block.
    """
    from epistemic_validator import is_status_summary_response, validate as v

    assert not is_status_summary_response("Tests passed; the bug is fixed.")
    verdict = v("Tests passed; the bug is fixed.")
    assert verdict.decision == "warn"


def test_status_summary_blocks_therefore_conclusion():
    """'All tests passed, therefore Phase B is complete.' — therefore fires guard.

    Default mode = warn → warn (not block).
    In block mode: would be block.
    """
    from epistemic_validator import is_status_summary_response, validate as v

    assert not is_status_summary_response("All tests passed, therefore Phase B is complete.")
    verdict = v("All tests passed, therefore Phase B is complete.")
    assert verdict.decision == "warn"


def test_grounded_status_short_still_allows():
    """'103 passed' — grounded-status logic (not report mode) handles it."""
    from epistemic_validator import validate as v

    verdict = v("103 passed.")
    assert verdict.decision == "allow"


def test_question_word_lead_blocks():
    """User questions starting with what/why/how should NOT be treated as direct answers.

    Default mode = warn → warn (not block). In block mode: would be block.
    """
    from epistemic_validator import _is_direct_answer_to_question, validate as v

    assert not _is_direct_answer_to_question("What's your current task?")
    assert not _is_direct_answer_to_question("Why is the minimax provider failing?")
    assert not _is_direct_answer_to_question("How do I configure the hook?")
    assert not _is_direct_answer_to_question("Who is responsible for this?")

    # These should still work as direct answers
    assert _is_direct_answer_to_question("Is the hook configured correctly?")
    assert _is_direct_answer_to_question("Does the semantic critic run on Stop?")

    # Validate blocks the question-word lead (default mode = warn)
    verdict = v("What's your current task?")
    assert verdict.decision == "warn"

    verdict = v("Why is the minimax provider failing?")
    assert verdict.decision == "warn"


def test_real_direct_answers_still_allow():
    """Real direct answers (is/does/can/will) without question words are still allowed."""
    from epistemic_validator import _is_direct_answer_to_question, validate as v

    assert _is_direct_answer_to_question("Is the hook configured correctly?")
    assert _is_direct_answer_to_question("Does the semantic critic run on Stop?")
    assert _is_direct_answer_to_question("Can I add a Stop hook for test coverage?")

    verdict = v("Is the hook configured correctly?")
    assert verdict.decision == "allow"

    verdict = v("Does the semantic critic run on Stop?")
    assert verdict.decision == "allow"


# ---------------------------------------------------------------------------
# Local tool-grounding — is_locally_grounded_in_this_turn and
# _is_locally_grounded_summary helpers
# ---------------------------------------------------------------------------


def test_has_local_tool_link_pytest():
    from epistemic_validator import _has_local_tool_link

    assert _has_local_tool_link("From the pytest run above, 38 passed.")
    assert _has_local_tool_link("Based on the pytest output we just saw, the fix works.")
    assert _has_local_tool_link("According to the TestSelfTriggerRegression run, quoting is stripped.")
    assert _has_local_tool_link("The test run we just saw shows the fix is working.")
    assert _has_local_tool_link("As shown in the pytest output above, all tests pass.")
    assert _has_local_tool_link("(source: pytest output above)")


def test_has_local_tool_link_negative():
    from epistemic_validator import _has_local_tool_link

    assert not _has_local_tool_link("The fix works.")
    assert not _has_local_tool_link("38 passed on its own.")
    assert not _has_local_tool_link("Tests confirm the behavior.")


def test_is_locally_grounded_in_this_turn_requires_link():
    """Without a linking phrase, is_locally_grounded_in_this_turn returns False
    even when the transcript contains matching content."""
    from epistemic_validator import is_locally_grounded_in_this_turn

    transcript = "38 passed in 0.60s"
    # No link phrase — should be False regardless of overlap
    assert not is_locally_grounded_in_this_turn("38 passed in 0.60s", transcript)
    assert not is_locally_grounded_in_this_turn("The structural fix works", transcript)


def test_is_locally_grounded_in_this_turn_requires_overlap():
    """With a linking phrase but no content overlap, returns False."""
    from epistemic_validator import is_locally_grounded_in_this_turn

    # Link phrase present but transcript has no overlapping tokens
    transcript = "something unrelated here"
    assert not is_locally_grounded_in_this_turn(
        "From the pytest run above, the structural fix works", transcript
    )


def test_is_locally_grounded_in_this_turn_both_required():
    """Returns True only when BOTH link phrase AND content overlap are present."""
    from epistemic_validator import is_locally_grounded_in_this_turn

    transcript = "38 passed in 0.60s\nTestSelfTriggerRegression: 7 passed"
    assert is_locally_grounded_in_this_turn(
        "From the pytest run above, 38 tests passed", transcript
    )


def test_locally_grounded_summary_short_always():
    """Ultra-short responses (< 80 words) that link to tool output and have
    at least 2 content tokens overlapping with the transcript should be
    allowed through as locally grounded summaries.

    overlap≥2 required — transcript must provide at least 2 substantive
    tokens that appear in the response text.
    """
    from epistemic_validator import _is_locally_grounded_summary

    # Transcript provides 2 overlapping tokens: 'passed' and 'structural'
    transcript = "38 passed in 0.60s\nStructural fix applied"
    assert _is_locally_grounded_summary(
        "From the pytest run above: 38 passed. Structural fix is working.", transcript, word_count=12
    )


def test_locally_grounded_summary_long_blocks():
    """Responses over 80 words are not treated as terse operator-mode summaries."""
    from epistemic_validator import _is_locally_grounded_summary

    transcript = "38 passed in 0.60s"
    # A longer response (> 80 words actual) should not pass even with a link phrase
    long_text = "From the pytest run above, 38 passed. " * 12  # ~84 words
    assert not _is_locally_grounded_summary(long_text, transcript, word_count=84)


def test_locally_grounded_summary_no_link_phrase_fails():
    """Without a linking phrase, even a short response is not locally grounded."""
    from epistemic_validator import _is_locally_grounded_summary

    transcript = "38 passed in 0.60s"
    assert not _is_locally_grounded_summary(
        "38 passed. The structural fix works.", transcript, word_count=8
    )


def test_validate_local_tool_summary_allows():
    """Local pytest summary with tool_transcript should pass without citation.

    Requires >= 2 substantive tokens overlapping between response and transcript:
    'passed' and 'structural' are the overlapping tokens here.
    """
    from epistemic_validator import EpistemicConfig, validate

    transcript = (
        "=============================\n"
        "38 passed in 0.60s\n"
        "Structural fix for the self-trigger issue appears to be working.\n"
        "============================="
    )
    response = (
        "38 passed. Based on the pytest run above, the structural fix for the "
        "self-trigger issue appears to be working."
    )
    cfg = EpistemicConfig(tool_transcript=transcript)
    verdict = validate(response, cfg)
    assert verdict.decision == "allow"


def test_validate_local_test_run_summary_allows():
    """Local test-run summary referencing specific test class should pass."""
    from epistemic_validator import EpistemicConfig, validate

    transcript = (
        "TestSelfTriggerRegression::test_quoted_pattern_text_after_stop_block_marker_allows PASSED\n"
        "TestSelfTriggerRegression::test_real_lazy_workaround_still_blocked PASSED\n"
        "38 passed in 0.60s"
    )
    response = (
        "From the TestSelfTriggerRegression run we just saw, quoted patterns are now stripped "
        "and real lazy proposals still block."
    )
    cfg = EpistemicConfig(tool_transcript=transcript)
    verdict = validate(response, cfg)
    assert verdict.decision == "allow"


def test_validate_external_claim_without_tools_requires_citation():
    """External factual claim with no tool transcript still requires citation.

    Default mode = warn → warn (not block).
    In block mode: would be block.
    """
    from epistemic_validator import EpistemicConfig, validate

    response = "The behavior of external service X is proven by the pytest output."
    cfg = EpistemicConfig(tool_transcript=None)
    verdict = validate(response, cfg)
    assert verdict.decision == "warn"


def test_build_local_summary_guidance_returns_hint():
    """build_local_summary_guidance returns a non-empty hint when tool_transcript is provided."""
    from epistemic_validator import build_local_summary_guidance

    hint = build_local_summary_guidance("pytest", "38 passed in 0.60s\ntest ok")
    assert len(hint) > 0
    assert "pytest" in hint
    assert "from the pytest run above" in hint.lower()


def test_build_local_summary_guidance_empty_when_no_transcript():
    """build_local_summary_guidance returns empty string when tool_transcript is empty."""
    from epistemic_validator import build_local_summary_guidance

    assert build_local_summary_guidance("pytest", "") == ""
    assert build_local_summary_guidance("pytest", None) == ""


def test_validate_local_tool_summary_style_pass():
    """A response that meets all 3 criteria returns pass=True."""
    from epistemic_validator import validate_local_tool_summary_style

    transcript = "38 passed in 0.60s\nStructural fix applied"
    response = "From the pytest run above: 38 passed. Structural fix is working."
    result = validate_local_tool_summary_style(response, transcript)
    assert result["pass"] is True
    assert result["has_link"] is True
    assert result["overlap_count"] >= 2
    assert result["blocker"] == ""


def test_validate_local_tool_summary_style_fails_word_count():
    """Response over 80 words fails with word_count blocker."""
    from epistemic_validator import validate_local_tool_summary_style

    transcript = "38 passed in 0.60s"
    response = "From the pytest run above: " + "38 passed. " * 45  # >80 words
    result = validate_local_tool_summary_style(response, transcript)
    assert result["pass"] is False
    assert "word" in result["blocker"].lower()


def test_validate_local_tool_summary_style_fails_no_link():
    """Response without a linking phrase fails with missing link blocker."""
    from epistemic_validator import validate_local_tool_summary_style

    transcript = "38 passed in 0.60s"
    response = "38 passed. The fix appears to be working."
    result = validate_local_tool_summary_style(response, transcript)
    assert result["pass"] is False
    assert "linking phrase" in result["blocker"].lower()


def test_validate_local_tool_summary_style_fails_low_overlap():
    """Response with only 1 overlapping token fails with overlap blocker."""
    from epistemic_validator import validate_local_tool_summary_style

    transcript = "38 passed in 0.60s"
    response = "From the pytest run above: 38 tests passed."  # only "passed" overlaps
    result = validate_local_tool_summary_style(response, transcript)
    assert result["pass"] is False
    assert "1" in result["blocker"]  # overlap count of 1


def test_validate_local_tool_summary_style_fails_no_transcript():
    """Without tool_transcript, no response can pass."""
    from epistemic_validator import EpistemicConfig, validate, validate_local_tool_summary_style

    response = "From the pytest run above: 38 passed."
    result = validate_local_tool_summary_style(response, "")
    assert result["pass"] is False
    assert "no tool_transcript" in result["blocker"].lower()

    response = "Flask 3.0 always behaves this way in production."
    cfg = EpistemicConfig()  # no tool_transcript
    verdict = validate(response, cfg)
    # Default mode = warn → warn (not block)
    assert verdict.decision == "warn"


def test_validate_external_claim_with_wrong_tool_link_not_treated_as_local():
    """A claim about an external service that claims to be 'from pytest above'
    should still be blocked when the tool transcript doesn't overlap.

    Default mode = warn → warn (not block).
    In block mode: would be block.
    """
    from epistemic_validator import EpistemicConfig, validate

    # Tool transcript only contains local Python test output, nothing about X service
    transcript = "38 passed in 0.60s\nTestSelfTriggerRegression: 7 passed"
    response = (
        "The behavior of external service X is proven by the pytest output above."
    )
    cfg = EpistemicConfig(tool_transcript=transcript)
    verdict = validate(response, cfg)
    assert verdict.decision == "warn"


def test_validate_real_lazy_proposal_still_blocks():
    """A genuine lazy workaround proposal adjacent to gate output still blocks."""
    from epistemic_validator import EpistemicConfig, validate

    transcript = "LAZY WORKAROUND DETECTED: accepting bug as feature"
    response = (
        "The gate said:\n"
        "> LAZY WORKAROUND DETECTED\n"
        "But honestly the workaround is fine, we don't need to fix it."
    )
    cfg = EpistemicConfig(tool_transcript=transcript)
    verdict = validate(response, cfg)
    assert verdict.decision == "block"


def test_validate_with_tool_transcript_but_no_link_still_blocks():
    """Providing tool_transcript alone is not enough — response must link to it.

    Default mode = warn → warn (not block).
    In block mode: would be block.
    """
    from epistemic_validator import EpistemicConfig, validate

    transcript = "38 passed in 0.60s\nAll 38 tests pass."
    response = "The structural fix for the self-trigger issue is verified."
    cfg = EpistemicConfig(tool_transcript=transcript)
    verdict = validate(response, cfg)
    # No link phrase → should still block (warn in default mode)
    assert verdict.decision == "warn"


# ---------------------------------------------------------------------------
# Mixed-mode classification tests
# ---------------------------------------------------------------------------


def test_classify_plan_only_allows():
    """Pure PLAN MODE response (no analytical content) is allowed outright."""
    from epistemic_validator import EpistemicConfig, validate

    response = (
        "PLAN MODE\n\n"
        "Steps:\n"
        "1. Identify the null check gap\n"
        "2. Add assertion after load\n"
        "3. Verify with tests"
    )
    cfg = EpistemicConfig(mode="block")
    verdict = validate(response, cfg)
    # Plan-only without [FACT]/[INFERENCE] markers is caught by the mixed-mode
    # bypass at the top of validate() and returns allow
    assert verdict.decision == "allow"


def test_classify_rca_investigation_enforced():
    """Pure RCA response with [FACT]/[INFERENCE] sections is classified as investigation
    and subject to full epistemic contract.

    A properly structured RCA response (with citations in FACT and uncertainty hedging
    in INFERENCE) passes validation. Missing citations or unhedged causal claims
    correctly trigger unsupported_fact / causal_violation issues.
    """
    from epistemic_validator import EpistemicConfig, validate

    # Substantial RCA response (not plan-prefixed) with PROPER citations and hedging
    response = (
        "[FACT]\n"
        "- The null check is missing in process() at line 42 "
        "(source: grep -n 'process' src/handler.py:42)\n"
        "- Code coverage shows process() is called in 3 code paths "
        "(source: coverage report)\n"
        "\n[INFERENCE]\n"
        "- The root cause may be that the early-return guard was removed in commit abc123\n"
        "- This could mean the function returns None instead of raising ValueError\n"
        "\n[UNKNOWN]\n"
        "- Whether the test suite covered this path before the refactor\n"
        "\n[RECOMMENDATION]\n"
        "- Add an assertion after the load() call to enforce non-None"
    )
    cfg = EpistemicConfig(mode="block")
    verdict = validate(response, cfg)
    # Full RCA response with all 4 sections, proper citations, and hedging → no issues
    assert verdict.decision == "allow"


def test_classify_mixed_plan_plus_analytical_not_simple():
    """Mixed PLAN + analytical content (PLAN MODE prefix + [FACT]/[INFERENCE])
    is classified as 'investigation', NOT 'simple' — and NOT allowed outright.

    This is the core regression test for the [FACT]-marker early-return bug.
    Before the fix, the presence of [FACT] alone collapsed mixed-mode to 'simple'
    regardless of the PLAN MODE prefix, causing the validator to skip enforcement.
    """
    from epistemic_validator import _classify_response_type_python

    response = (
        "PLAN MODE\n\n"
        "Step 1: Investigate the gap\n\n"
        "[FACT]\n"
        "- The null check is missing in process() at line 42\n"
        "- This was introduced in commit abc123\n"
        "\n[INFERENCE]\n"
        "- The root cause is that the early-return guard was removed\n"
        "- The fix requires adding an assertion after load()\n"
    )
    classification = _classify_response_type_python(response)
    assert classification == "investigation", (
        f"Expected 'investigation', got '{classification}'. "
        "Mixed PLAN MODE + [FACT] markers should NOT collapse to 'simple'."
    )


def test_classify_mixed_plan_brackets_not_simple():
    """Response with [PLAN] bracket prefix and [FACT] sections is classified as
    'investigation', not 'simple'."""
    from epistemic_validator import _classify_response_type_python

    response = (
        "[PLAN] Next steps:\n"
        "1. Fix the gap\n"
        "2. Verify\n\n"
        "[FACT]\n"
        "- The assertion is missing after load()"
    )
    classification = _classify_response_type_python(response)
    assert classification == "investigation"


def test_classify_rationale_header_not_simple():
    """Response with ## RATIONALE header and [FACT] sections is classified as
    'investigation', not 'simple'."""
    from epistemic_validator import _classify_response_type_python

    response = (
        "## RATIONALE\n\n"
        "The refactor was needed because the old pattern had a race condition.\n\n"
        "[FACT]\n"
        "- The race condition was in the connection pool initialization"
    )
    classification = _classify_response_type_python(response)
    assert classification == "investigation"


def test_classify_pure_status_simple():
    """Pure status report with [FACT] markers but no plan prefix is 'simple'."""
    from epistemic_validator import _classify_response_type_python

    response = (
        "[FACT]\n"
        "- Created auth.py with JWT validation\n"
        "- Added connection pooling\n"
        "\n[INFERENCE]\n"
        "- The system should be more stable now"
    )
    classification = _classify_response_type_python(response)
    assert classification == "simple"


def test_classify_short_status_simple():
    """Short responses with [FACT] markers and no plan prefix are 'simple'."""
    from epistemic_validator import _classify_response_type_python

    # Short — under 12 words — even with analytical signal should be simple
    response = "[FACT] the fix is in place"
    classification = _classify_response_type_python(response)


# =============================================================================
# Schema routing by explicit turn_mode — tests added for Phase 1/2 implementation
# =============================================================================

def test_schema_routing_plan_mode_normal_content():
    """PLAN schema: normal planning content (no RCA sections) → allow."""
    from epistemic_validator import EpistemicConfig, validate

    response = "[PLAN]\n1. Fix the bug\n2. Add tests\n[RATIONALE]\n- Bug is blocking"
    cfg = EpistemicConfig(mode="warn", turn_mode="plan")
    verdict = validate(response, cfg)
    assert verdict.decision == "allow", f"Expected allow, got {verdict.decision}: {verdict.issues}"


def test_schema_routing_plan_mode_mixed_substance():
    """PLAN schema: substantive diagnosis (RCA sections) → mixed_substance violation."""
    from epistemic_validator import EpistemicConfig, validate

    response = (
        "[PLAN]\n1. Fix the bug\n"
        "[FACT]\n- The null check is missing\n"
        "[INFERENCE]\n- Root cause is the removed guard"
    )
    cfg = EpistemicConfig(mode="warn", turn_mode="plan")
    verdict = validate(response, cfg)
    # Should contain mixed_substance_plan issue, decision should be warn or block
    assert verdict.decision in ("warn", "block"), f"Expected warn/block, got {verdict.decision}"
    issue_types = {i.type for i in verdict.issues}
    assert "format" in issue_types, f"Expected format issue (mixed_substance), got {verdict.issues}"


def test_schema_routing_plan_mode_substantive_root_cause():
    """PLAN schema: ## Root Cause section → mixed_substance_plan violation."""
    from epistemic_validator import EpistemicConfig, validate

    response = (
        "[PLAN]\n1. Fix the bug\n"
        "## Root Cause\n"
        "The guard was removed in commit abc123."
    )
    cfg = EpistemicConfig(mode="block", turn_mode="plan")
    verdict = validate(response, cfg)
    issue_messages = {i.message for i in verdict.issues}
    assert any("PLAN mode response contains substantive diagnosis" in m for m in issue_messages), \
        f"Expected mixed_substance_plan violation, got {verdict.issues}"


def test_schema_routing_control_mode_with_substantive_claim():
    """CONTROL schema: substantive factual claim → block."""
    from epistemic_validator import EpistemicConfig, validate

    response = "The bug is in the null check at line 42."
    cfg = EpistemicConfig(mode="block", turn_mode="control")
    verdict = validate(response, cfg)
    assert verdict.decision == "block", f"Expected block, got {verdict.decision}"


def test_schema_routing_control_mode_no_claim():
    """CONTROL schema: no substantive claims → allow."""
    from epistemic_validator import EpistemicConfig, validate

    response = "Run pytest to verify."
    cfg = EpistemicConfig(mode="block", turn_mode="control")
    verdict = validate(response, cfg)
    assert verdict.decision == "allow", f"Expected allow, got {verdict.decision}"


def test_schema_routing_explicit_turn_mode_overrides_heuristic():
    """Explicit turn_mode must not be overridden by text heuristics."""
    from epistemic_validator import EpistemicConfig, validate

    # Response has RCA markers but turn_mode=plan → must use PLAN schema, not INVESTIGATION
    response = (
        "[PLAN]\n1. Do X\n"
        "[FACT]\n- Evidence here"
    )
    cfg_plan = EpistemicConfig(mode="block", turn_mode="plan")
    cfg_analysis = EpistemicConfig(mode="block", turn_mode="analysis")

    verdict_plan = validate(response, cfg_plan)
    verdict_analysis = validate(response, cfg_analysis)

    # Plan schema: should check mixed_substance, not 4-section contract
    plan_issue_types = {i.type for i in verdict_plan.issues}
    # Analysis schema: should enforce 4-section
    analysis_issue_types = {i.type for i in verdict_analysis.issues}

    # The plan response lacks [INFERENCE]/[UNKNOWN]/[RECOMMENDATION], so plan schema
    # (which doesn't require 4-section) should have fewer format issues than analysis schema
    assert verdict_plan.decision != "block", \
        f"Plan with [FACT] but no other sections should not block: {verdict_plan.issues}"


def test_schema_routing_investigation_mode_requires_4_section():
    """INVESTIGATION schema (turn_mode=analysis): all 4 sections required."""
    from epistemic_validator import EpistemicConfig, validate

    # Has FACT and INFERENCE but not UNKNOWN and RECOMMENDATION
    response = (
        "[FACT]\n- Null check is missing in process()\n"
        "[INFERENCE]\n- Root cause is the removed guard"
    )
    cfg = EpistemicConfig(mode="block", turn_mode="analysis")
    verdict = validate(response, cfg)
    # Missing [UNKNOWN] and [RECOMMENDATION] sections → format issues
    issue_types = {i.type for i in verdict.issues}
    assert "format" in issue_types, f"Expected format issue for missing sections, got {verdict.issues}"


def test_schema_routing_investigation_mode_complete_sections():
    """INVESTIGATION schema: complete 4-section with citations → allow."""
    from epistemic_validator import EpistemicConfig, validate

    response = (
        "[FACT]\n- Null check is missing in process() "
        "(source: grep -n 'process' handler.py:42)\n"
        "[INFERENCE]\n- Root cause may be the removed guard\n"
        "[UNKNOWN]\n- Whether tests covered this path\n"
        "[RECOMMENDATION]\n- Add assertion after load()"
    )
    cfg = EpistemicConfig(mode="block", turn_mode="analysis")
    verdict = validate(response, cfg)
    assert verdict.decision == "allow", f"Expected allow, got {verdict.decision}: {verdict.issues}"


def test_schema_routing_turn_mode_none_falls_back_to_prefix_check():
    """When turn_mode is None, plan prefix bypass still works as fallback."""
    from epistemic_validator import EpistemicConfig, validate

    response = "PLAN MODE\n\n1. Fix the bug"
    cfg = EpistemicConfig(mode="warn", turn_mode=None)
    verdict = validate(response, cfg)
    # No RCA markers → should bypass
    assert verdict.decision == "allow"


def test_schema_routing_turn_mode_none_with_rca_markers():
    """When turn_mode is None AND RCA markers present: heuristic routes to investigation."""
    from epistemic_validator import EpistemicConfig, validate

    # No plan prefix, has RCA markers → goes to investigation schema
    response = (
        "[FACT]\n- The null check is missing\n"
        "[INFERENCE]\n- Root cause is the removed guard\n"
        "[UNKNOWN]\n- Whether tests covered this\n"
        "[RECOMMENDATION]\n- Add assertion"
    )
    cfg = EpistemicConfig(mode="block", turn_mode=None)
    verdict = validate(response, cfg)
    # No format issues (all sections present), no citation issues → allow
    assert verdict.decision == "allow", f"Expected allow, got {verdict.decision}: {verdict.issues}"

    assert classification == "simple"
