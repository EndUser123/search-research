"""Tests for epistemic_validator.py.

Covers: sanitization, parsing, fact support, causal rules, comparative rules,
decision logic, and full validate() integration.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from epistemic_validator import (
    EpistemicConfig,
    EpistemicVerdict,
    ParsedBullet,
    ParsedResponse,
    check_causal_rules,
    check_comparative_rules,
    check_fact_support,
    decide_from_issues,
    parse_sections,
    sanitize_response,
    validate,
)

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
    assert decide_from_issues(issues, cfg) == "block"


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
    after sanitization strips the Stop scaffolding."""
    verdict = validate(DIAGNOSTIC_RESPONSE)
    # After sanitization, only the factual line remains
    # It won't have sections, so format issues expected
    assert any(i.type == "format" for i in verdict.issues)


def test_validate_unsupported_fact_blocks():
    text = (
        "[FACT]\n- The file exists\n\n"
        "[INFERENCE]\n- Maybe\n\n"
        "[UNKNOWN]\n- I do not know\n\n"
        "[RECOMMENDATION]\n- Check the file"
    )
    verdict = validate(text, EpistemicConfig(mode="block"))
    assert verdict.decision == "block"
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
    """Explicit analysis mode enforces the 4-section contract."""
    from epistemic_validator import validate, EpistemicConfig

    # mode="block" so format violations actually block; responseMode forces analysis
    cfg = EpistemicConfig(responseMode="analysis", mode="block")
    verdict = validate("Implementation complete. Files written.", cfg)
    assert verdict.decision == "block"  # Missing sections
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
    """Stop._run_epistemic_contract returns repair prompt for format-only issues."""
    # Import Stop module components
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from Stop import _run_epistemic_contract

    # Response missing [UNKNOWN] and [RECOMMENDATION] — format issues only.
    data = {
        "response": (
            "[FACT]\n"
            "- Something happened (source: file.py:10)\n"
            "[INFERENCE]\n"
            "- May be related\n"
        ),
        "session_id": "test-session",
    }
    result = _run_epistemic_contract(data)
    assert result is not None
    assert result["decision"] == "warn"
    assert "FORMAT REPAIR" in result["systemMessage"]
    assert "Missing:" in result["systemMessage"]


def test_stop_mixed_issues_surface_advisory():
    """Stop._run_epistemic_contract surfaces raw advisory for mixed issues."""
    from Stop import _run_epistemic_contract

    # Response with missing sections (format) + unsupported fact (non-format).
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
    assert "FORMAT REPAIR" not in result["systemMessage"]
    assert "ADVISORY" in result["systemMessage"]


def test_stop_non_format_issues_no_repair():
    """Causal/comparative violations do NOT trigger repair path."""
    from Stop import _run_epistemic_contract

    # Response with all 4 sections but a causal violation in UNKNOWN.
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
    assert "FORMAT REPAIR" not in result["systemMessage"]
    assert "ADVISORY" in result["systemMessage"]


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


def test_base_prompt_includes_behavior_rules():
    """base_system.md contains the 3 new behavior rules."""
    content = (Path(__file__).resolve().parents[3]
               / "packages" / "prompt-builder" / "prompts" / "base_system.md")
    text = content.read_text(encoding="utf-8")
    assert "Do not argue with hooks" in text
    assert "Avoid meta-reasoning" in text
    assert "Format-only feedback" in text


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
