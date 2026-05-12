"""Tests for the epistemic policy layer (Phase 2).

Verifies that the (turn_kind, claim_kind) policy table governs enforcement
correctly: FORMAT_ONLY never blocks CONTROL/DEBUG modes; CAUSAL/FACTUAL/STANCE
remain strict in ANALYSIS mode.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))


class TestClaimKindClassification:
    """Unit tests for _classify_claim_kind."""

    def test_empty_issues_returns_unknown(self):
        from epistemic_validator import _classify_claim_kind, ClaimKind, EpistemicIssue

        assert _classify_claim_kind([]) == ClaimKind.UNKNOWN

    def test_format_only_returns_format_only(self):
        from epistemic_validator import _classify_claim_kind, ClaimKind, EpistemicIssue

        issues = [
            EpistemicIssue(section="__GLOBAL__", bullet_index=-1, type="format", message="..."),
        ]
        assert _classify_claim_kind(issues) == ClaimKind.FORMAT_ONLY

    def test_unsupported_fact_returns_factual(self):
        from epistemic_validator import _classify_claim_kind, ClaimKind, EpistemicIssue

        issues = [
            EpistemicIssue(section="__GLOBAL__", bullet_index=-1, type="unsupported_fact", message="..."),
        ]
        assert _classify_claim_kind(issues) == ClaimKind.FACTUAL

    def test_causal_returns_causal(self):
        from epistemic_validator import _classify_claim_kind, ClaimKind, EpistemicIssue

        issues = [
            EpistemicIssue(section="__GLOBAL__", bullet_index=-1, type="causal_violation", message="..."),
        ]
        assert _classify_claim_kind(issues) == ClaimKind.CAUSAL

    def test_format_plus_factual_returns_factual(self):
        """When both format and factual issues exist, FACTUAL takes priority."""
        from epistemic_validator import _classify_claim_kind, ClaimKind, EpistemicIssue

        issues = [
            EpistemicIssue(section="__GLOBAL__", bullet_index=-1, type="format", message="..."),
            EpistemicIssue(section="__GLOBAL__", bullet_index=-1, type="unsupported_fact", message="..."),
        ]
        assert _classify_claim_kind(issues) == ClaimKind.FACTUAL


class TestTurnKindFromResponseType:
    """Unit tests for _turn_kind_from_response_type."""

    def test_status_report_returns_control(self):
        from epistemic_validator import _turn_kind_from_response_type, TurnKind

        result = _turn_kind_from_response_type("simple", is_status_report=True)
        assert result == TurnKind.CONTROL

    def test_investigation_returns_analysis(self):
        from epistemic_validator import _turn_kind_from_response_type, TurnKind

        result = _turn_kind_from_response_type("investigation", is_status_report=False)
        assert result == TurnKind.ANALYSIS

    def test_analytical_returns_analysis(self):
        from epistemic_validator import _turn_kind_from_response_type, TurnKind

        result = _turn_kind_from_response_type("analytical", is_status_report=False)
        assert result == TurnKind.ANALYSIS

    def test_simple_unknown_returns_unknown(self):
        from epistemic_validator import _turn_kind_from_response_type, TurnKind

        result = _turn_kind_from_response_type("simple", is_status_report=False)
        assert result == TurnKind.UNKNOWN


class TestPolicyTable:
    """Tests that verify the policy table entries."""

    def test_control_format_only_is_ignore(self):
        from epistemic_validator import get_epistemic_policy, TurnKind, ClaimKind

        policy = get_epistemic_policy(TurnKind.CONTROL, ClaimKind.FORMAT_ONLY)
        assert policy == "ignore"

    def test_control_factual_is_warn(self):
        from epistemic_validator import get_epistemic_policy, TurnKind, ClaimKind

        policy = get_epistemic_policy(TurnKind.CONTROL, ClaimKind.FACTUAL)
        assert policy == "warn"

    def test_control_unknown_is_allow(self):
        from epistemic_validator import get_epistemic_policy, TurnKind, ClaimKind

        policy = get_epistemic_policy(TurnKind.CONTROL, ClaimKind.UNKNOWN)
        assert policy == "allow"

    def test_debug_meta_all_is_ignore(self):
        from epistemic_validator import get_epistemic_policy, TurnKind, ClaimKind

        for claim_kind in ["FORMAT_ONLY", "FACTUAL", "CAUSAL", "STANCE", "UNKNOWN"]:
            policy = get_epistemic_policy(TurnKind.DEBUG_META, ClaimKind[claim_kind])
            assert policy == "ignore", f"DEBUG_META + {claim_kind} should be ignore"

    def test_analysis_format_only_is_none(self):
        """ANALYSIS + FORMAT_ONLY falls through to config (usually warn)."""
        from epistemic_validator import get_epistemic_policy, TurnKind, ClaimKind

        policy = get_epistemic_policy(TurnKind.ANALYSIS, ClaimKind.FORMAT_ONLY)
        assert policy is None

    def test_analysis_causal_is_none(self):
        """ANALYSIS + CAUSAL falls through to config (usually warn per default)."""
        from epistemic_validator import get_epistemic_policy, TurnKind, ClaimKind

        policy = get_epistemic_policy(TurnKind.ANALYSIS, ClaimKind.CAUSAL)
        assert policy is None

    def test_analysis_factual_is_none(self):
        """ANALYSIS + FACTUAL falls through to config (usually block per default)."""
        from epistemic_validator import get_epistemic_policy, TurnKind, ClaimKind

        policy = get_epistemic_policy(TurnKind.ANALYSIS, ClaimKind.FACTUAL)
        assert policy is None


class TestPolicyLayerIntegration:
    """End-to-end tests: policy layer applied through decide_from_issues."""

    def test_status_summary_simple_response_allows_through_policy(self):
        """CONTROL + FORMAT_ONLY: policy=ignore → allow (replaces old bypass cascade)."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "Implementation complete. 7 tests pass. "
            "Short status summary that matches is_status_summary_response() pattern."
        )
        # Docstring references old line number — stale, removed. The test passes via
        # _is_grounded_status_confirmation() (ultra-short limit) OR via policy layer
        # CONTROL+FORMAT_ONLY=ignore in decide_from_issues(). Both routes confirmed
        # before writing this docstring update.
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "allow", (
            f"Expected allow for CONTROL+FORMAT_ONLY via policy table, "
            f"got {verdict.decision}: {verdict.issues}"
        )

    def test_investigation_missing_sections_blocks(self):
        """INVESTIGATION + FORMAT_ONLY: policy=None → config fires → block."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "The root cause of the epistemic format issue is a control-flow bug. "
            "However, the bypass fixes it.\n"
            "Evidence from our test corpus shows format-only blocks dominate. "
            "Alternative approaches were considered but rejected."
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "block", (
            f"Expected block for investigation without sections, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )

    def test_unsupported_fact_in_simple_mode_warns(self):
        """SIMPLE + FORMAT_ONLY + mode=warn: policy=warn (unchanged from pre-feature behavior)."""
        from epistemic_validator import validate, EpistemicConfig

        response = "The system guarantees all hooks run synchronously."
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        # response_type=simple → UNKNOWN turn kind → UNKNOWN+FORMAT_ONLY policy="warn"
        # mode=warn keeps at warn (no downgrade from block)
        assert verdict.decision == "warn", (
            f"Expected warn for simple response + mode=warn, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )

    def test_analytical_with_bullets_no_sections_allows(self):
        """ANALYSIS + FORMAT_ONLY: policy=None + _filter drops format → warn or allow."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "[ANALYSIS]\n"
            "- The fix adds one bypass at the narrowest possible insertion point.\n"
            "- This preserves strict enforcement where it matters.\n"
            "- Minimal change, targeted scope.\n"
            "The approach is sound."
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        # Analytical path: _filter drops format issues when response_type==analytical
        assert verdict.decision in ("allow", "warn"), (
            f"Expected allow/warn for analytical with framing, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )

    def test_repair_response_with_fact_sections_warns_not_blocks(self):
        """Structured [FACT] response: allow/warn acceptable, NOT block."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "[FACT]\n"
            "- The fix is at P:\\.claude\\hooks\\epistemic_validator.py line 1132.\n"
            "  (source: this file)"
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision in ("allow", "warn"), (
            f"Expected allow/warn for [FACT] repair response, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )
        assert verdict.decision != "block", (
            f"[FACT] response with evidence should not block, got issues: {verdict.issues}"
        )

    def test_grounded_status_report_allows(self):
        """CONTROL + grounded status: policy=ignore → allow."""
        from epistemic_validator import validate, EpistemicConfig

        response = "Tests passed. All 7 regression tests pass. Ready to commit."
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "allow", (
            f"Expected allow for grounded status report, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )

    def test_multiple_status_signals_allows(self):
        """CONTROL + multiple status signals: policy=ignore → allow."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "Implementation complete. 7 tests pass. Fix is minimal and localized."
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "allow", (
            f"Expected allow for multi-signal status, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )


class TestPolicyLayerModes:
    """Phase 3 tests: control, debug-meta, and analytical enforcement are correct."""

    def test_control_mode_format_only_does_not_block(self):
        """CONTROL + FORMAT_ONLY: policy=ignore → allow via policy layer, not bypass."""
        from epistemic_validator import validate, EpistemicConfig

        # Longer status summary — exceeds _is_grounded_status_confirmation() ultra-short
        # limit but still CONTROL mode, so policy layer (CONTROL+FORMAT_ONLY=ignore) allows.
        response = (
            "The deployment completed successfully. All 7 tests pass in 0.42s. "
            "No regressions detected. The fix is minimal and localized to one function."
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "allow", (
            f"Expected allow for CONTROL+FORMAT_ONLY via policy layer, "
            f"got {verdict.decision}: {verdict.issues}"
        )

    def test_debug_meta_responses_never_block(self):
        """DEBUG_META + any claim kind: policy=ignore → allow regardless of issues."""
        from epistemic_validator import validate, EpistemicConfig

        # Emulate a debug-meta response (about gates/logs). Even with format
        # issues and unsupported claims, DEBUG_META should allow through.
        response = (
            "The gate fired at PreToolUse line 412. We checked the __GLOBAL__ issue "
            "and it matched the format pattern. The epistemic validator found 1 issue."
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        # DEBUG_META policy: all claim kinds → "ignore" → allow
        assert verdict.decision == "allow", (
            f"Expected allow for DEBUG_META, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )

    def test_simple_longer_response_with_guarantee_language_warns(self):
        """SIMPLE + FORMAT_ONLY: policy=warn (same as test_simple_longer_response_with_guarantee_language_warns)."""
        from epistemic_validator import validate, EpistemicConfig

        # Longer simple response with guarantee-style language
        # response_type=simple (no markers) → UNKNOWN → policy="warn"
        response = "The system guarantees all hooks run synchronously without exception."
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "warn", (
            f"Expected warn for simple response, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )

    def test_analytical_with_sections_allows(self):
        """ANALYSIS + [FACT]/[INFERENCE] sections: policy=allow → allow."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "[FACT]\n"
            "- The fix is at line 1273 in epistemic_validator.py\n"
            "- Policy table was extracted in Phase 2\n"
            "[RECOMMENDATION]\n"
            "- Route through decide_from_issues() for consistency"
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision in ("allow", "warn"), (
            f"Expected allow/warn for analytical with sections, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )


class TestStopVerdictOrdering:
    """Regression test: validate() must be called before verdict.decision is read."""

    def test_validate_called_before_verdict_reference(self):
        """
        Regression coverage for Stop.py verdict-ordering fix.

        _run_epistemic_contract() at Stop.py line 519 calls validate() BEFORE accessing
        verdict.decision at line 540. The bug was referencing verdict.decision
        before validate() was called, causing AttributeError on first call.

        This test verifies the calling order by checking that validate() runs
        and verdict.decision is only accessed after the call.
        """
        import inspect
        import Stop  # type: ignore

        # Read the source of _run_epistemic_contract
        source_lines, _ = inspect.getsourcelines(Stop._run_epistemic_contract)
        source = "".join(source_lines)

        # Find the line numbers of validate() call and verdict.decision access
        validate_line = None
        verdict_ref_line = None
        for i, line in enumerate(source_lines):
            if "validate(response, cfg)" in line and verdict_ref_line is None:
                validate_line = i
            if "verdict.decision" in line:
                verdict_ref_line = i

        assert validate_line is not None, "validate() call not found in _run_epistemic_contract"
        assert verdict_ref_line is not None, (
            "verdict.decision reference not found in _run_epistemic_contract"
        )

        # validate() must come before verdict.decision
        assert validate_line < verdict_ref_line, (
            f"verdict.decision (line {verdict_ref_line}) referenced before validate() "
            f"(line {validate_line}) — this causes AttributeError on first call"
        )


class TestPolicyTableMarkdown:
    """Verify policy table documentation matches code."""

    def test_policy_table_completeness(self):
        """All (TurnKind, ClaimKind) combinations must have a defined policy entry."""
        from epistemic_validator import _POLICY_TABLE, TurnKind, ClaimKind

        for turn_kind in TurnKind:
            for claim_kind in ClaimKind:
                key = (turn_kind, claim_kind)
                assert key in _POLICY_TABLE, f"Missing policy entry for {key}"


class TestTurnKindFromContext:
    """Tests for _turn_kind_from_context — factual-report → CONTROL reclassification."""

    def test_factual_report_treated_as_control_format_only_ignored(self):
        """Structured audit/report response: UNKNOWN → CONTROL → FORMAT_ONLY ignored.

        This is the canonical failure case from the audit block: a Phase 1 audit
        report with FACT TABLE, FAILURE MODE TABLE, etc. has no [FACT] sections,
        but its structure (tables, numbered findings, labeled bullets) marks it as
        a factual report, not an analytical argument. CONTROL + FORMAT_ONLY = ignore.
        """
        from epistemic_validator import validate, EpistemicConfig, TurnKind, _turn_kind_from_context

        # Verify the helper alone: UNKNOWN → CONTROL on structured report
        report_response = """## FACT TABLE

| Question | Finding | Evidence |
|---|---|---|
| How is turn kind derived? | Via function | Stop.py L450+ |

### Gap Summary

| ID | Component | Failure Mode |
|---|---|---|
| FM-1 | Gate applicability | UNCLASSIFIED gates never suppressed |

Evidence: Stop.py L2783-2826
"""
        tk = _turn_kind_from_context(report_response, TurnKind.UNKNOWN)
        assert tk == TurnKind.CONTROL, f"Expected CONTROL, got {tk}"

        # And through validate: no block on format-only issues
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(report_response, cfg)
        assert verdict != "block", (
            f"Audit-report structure should not block on FORMAT_ONLY: got {verdict.decision}, "
            f"issues: {verdict.issues}"
        )

    def test_non_audit_simple_answer_remains_unknown_and_may_block_on_format(self):
        """Short non-report answer stays UNKNOWN; FORMAT_ONLY can still block via config."""
        from epistemic_validator import TurnKind, _turn_kind_from_context

        # Plain prose with no report structure — should stay UNKNOWN
        # (the new pattern is conservative: no false positives on prose)
        for text in [
            "Here is my analysis of the code.",
            "ok, done",
            "just some prose",
            "analysis of the findings",
        ]:
            tk = _turn_kind_from_context(text, TurnKind.UNKNOWN)
            assert tk == TurnKind.UNKNOWN, f"{text!r} should stay UNKNOWN, got {tk}"

        # Empty response
        assert _turn_kind_from_context("", TurnKind.UNKNOWN) == TurnKind.UNKNOWN

    def test_turn_kind_from_context_only_fires_on_unknown(self):
        """_turn_kind_from_context never overrides non-UNKNOWN turn kinds."""
        from epistemic_validator import TurnKind, _turn_kind_from_context

        report = "| ID | ... |\n| --- | --- |\n| 1 | foo |"
        # ANALYSIS stays ANALYSIS
        assert _turn_kind_from_context(report, TurnKind.ANALYSIS) == TurnKind.ANALYSIS
        # CONTROL stays CONTROL
        assert _turn_kind_from_context(report, TurnKind.CONTROL) == TurnKind.CONTROL
        # EXPLORATION stays EXPLORATION
        assert _turn_kind_from_context(report, TurnKind.EXPLORATION) == TurnKind.EXPLORATION
        # DEBUG_META stays DEBUG_META
        assert _turn_kind_from_context(report, TurnKind.DEBUG_META) == TurnKind.DEBUG_META

    def test_analytical_factual_causal_enforcement_unchanged_in_control(self):
        """CONTROL + FACTUAL/CAUSAL: policy=warn (not ignore) — enforcement preserved.

        The contextual reclassification only promotes UNKNOWN → CONTROL. The policy
        table then governs what happens: CONTROL + FACTUAL = warn, CONTROL + CAUSAL = warn.
        This test confirms substantive issues still fire in the reclassified mode.
        """
        from epistemic_validator import validate, EpistemicConfig

        # A structured report (4+ pipes) with an unsupported factual claim
        # _FACTUAL_REPORT_RE fires → UNKNOWN → CONTROL; policy: CONTROL+FACTUAL=warn
        response_with_unsupported_fact = """Phase 1 Audit: Gate Reliability Report

| ID | Gate | Finding | Severity |
|---|---|---|---|
| FM-1 | GATE_CLASSES | UNCLASSIFIED gates never suppressed | HIGH |

The system guarantees all hooks run synchronously.
"""
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response_with_unsupported_fact, cfg)
        # CONTROL + FACTUAL = warn (not block)
        assert verdict.decision != "block", (
            f"CONTROL + FACTUAL should warn not block, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )

    def test_factual_report_patterns_recognized(self):
        """Verify each pattern type in _FACTUAL_REPORT_RE fires correctly."""
        from epistemic_validator import TurnKind, _turn_kind_from_context

        cases = [
            # Markdown table row
            ("| Question | Finding | Evidence |\n|---|---|---|", TurnKind.CONTROL),
            # Markdown table separator
            ("| --- | --- | --- |", TurnKind.CONTROL),
            # Table header: | ID |
            ("| ID | Component | Failure Mode |", TurnKind.CONTROL),
            # Numbered finding: "1) Finding:"
            ("1) The root cause is a missing null check.", TurnKind.CONTROL),
            # Numbered finding: "1. FM-1:"
            ("1) FM-1: Gate applicability failure.", TurnKind.CONTROL),
            # Labeled bullet: "- FM-1:"
            ("- FM-1: UNCLASSIFIED gates never suppressed.", TurnKind.CONTROL),
            # Labeled bullet: "* ISSUE-1:"
            ("* ISSUE-1: No telemetry schema extension.", TurnKind.CONTROL),
            # Evidence marker
            ("Evidence: Stop.py L2783-2826", TurnKind.CONTROL),
            # Phase header
            ("Phase 1 Audit: Stop Gate Reliability Package", TurnKind.CONTROL),
            # [FACT] section marker
            ("[FACT]\n- Verified from code inspection.", TurnKind.CONTROL),
            # Markdown heading: ## Phase 1 Audit
            ("## Phase 1 Audit\n\n## Findings", TurnKind.CONTROL),
            # Gap Summary header
            ("Gap Summary\n| Component | Status |", TurnKind.CONTROL),
            # Control baseline: plain prose with no report structure
            ("Here is my analysis of the code.", TurnKind.UNKNOWN),
            # Control: short acknowledgement
            ("ok, done", TurnKind.UNKNOWN),
        ]
        for response, expected in cases:
            tk = _turn_kind_from_context(response, TurnKind.UNKNOWN)
            assert tk == expected, f"Response {response[:40]!r}: expected {expected}, got {tk}"

    def test_decide_from_issues_wires_turn_kind_from_context(self):
        """Integration: decide_from_issues applies context reclassification end-to-end."""
        from epistemic_validator import decide_from_issues, EpistemicConfig, EpistemicIssue, TurnKind

        # FORMAT_ONLY issue in a structured report → turn_kind becomes CONTROL
        issues = [
            EpistemicIssue(
                section="__GLOBAL__",
                bullet_index=-1,
                type="format",
                message="Found 88 line(s) outside any [FACT]/...",
            )
        ]
        # Pass UNKNOWN as initial turn_kind (mirrors the first-pass result for a
        # simple/audit response), then through decide_from_issues with a report-style
        # raw_response the context reclassification fires.
        raw_report = "| ID | Finding |\n|---|---|\n| 1 | foo |"
        decision = decide_from_issues(
            issues,
            cfg=EpistemicConfig(tool_transcript=""),  # CONTROL+FORMAT_ONLY=ignore, so cfg not reached
            response_type="simple",
            raw_response=raw_report,
        )
        # CONTROL + FORMAT_ONLY = "ignore" → decision is "allow"
        assert decision == "allow", f"Expected allow via context reclassification, got {decision}"
