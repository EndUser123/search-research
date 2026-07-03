"""Regression tests: epistemic format false-positive elimination.

Tests that grounded status summaries and other non-investigation substantive
responses are NOT blocked by the __GLOBAL__ format rule, while substantive
issues (unsupported fact, causal) still block appropriately.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))


class TestGroundedStatusSummaryBypass:
    """Case 1 & 2: Flat completion summary and grounded status report → allow."""

    def test_flat_completion_summary_allow(self):
        """Flat completion summary matching STATUS patterns → allow (not block)."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "Implementation complete. 7 tests pass. The bypass reuses "
            "the existing is_status_summary_response() helper at line 1132."
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "allow", (
            f"Expected allow for flat completion summary, got {verdict.decision}: "
            f"{verdict.issues}"
        )

    def test_grounded_status_report_with_local_context_allow(self):
        """Grounded status report with task-state context → allow."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "Tests passed. All 7 regression tests pass. Ready to commit when "
            "you give the word."
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "allow", (
            f"Expected allow for grounded status report, got block: "
            f"{verdict.issues}"
        )

    def test_multiple_status_signals_allow(self):
        """Multiple status signals in opening line → allow."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "Implementation complete. 7 tests pass. Fix is minimal and "
            "localized to one insertion point."
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        assert verdict.decision == "allow", (
            f"Expected allow for multi-signal status, got block: "
            f"{verdict.issues}"
        )


class TestAnalyticalProseAllow:
    """Case 3: Analytical prose with bullets outside sections, non-investigation → warn not block."""

    def test_analytical_prose_with_sections_but_no_fact_sections_allow(self):
        """Analytical prose with bullets and section framing but no [FACT] etc. → allow.

        When a response has analytical structure (bullets, reasoning) but no
        4-section contract markers, the analytical path filters format issues
        and allows through if there are no substantive issues.
        """
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
        # Analytical path does NOT hard-block on format; decision should be allow
        # (no substantive issues present in this response)
        assert verdict.decision == "allow", (
            f"Expected allow for analytical with section framing, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )


class TestInvestigationStillBlocks:
    """Case 4: Investigation response missing required epistemic structure → still block."""

    def test_investigation_missing_sections_still_blocks(self):
        """Investigation response without 4-section contract → block.

        Responses with investigation phrasing (root cause, however, alternative)
        and no [FACT]/[INFERENCE] markers are classified as investigation and
        require full 4-section framing.
        """
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
            f"Expected block for investigation missing sections, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )


class TestUnsupportedFactStillBlocks:
    """Case 5: Short unsupported factual claim in simple response → still block."""

    def test_unsupported_fact_simple_response_blocks(self):
        """Short unsupported factual claim without citation → block."""
        from epistemic_validator import validate, EpistemicConfig

        response = "The system guarantees all hooks run synchronously."
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        # System-level guarantee claim needs evidence — should block
        assert verdict.decision == "block", (
            f"Expected block for unsupported system guarantee, got: {verdict.decision}"
        )

    def test_unsupported_causal_claim_blocks(self):
        """Unsupported causal explanation → block (Case 6: causal without support)."""
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "This happens because the __GLOBAL__ format check fires before the "
            "downstream issue filtering can help."
        )
        cfg = EpistemicConfig(tool_transcript="", enable_causal_checks=True)
        verdict = validate(response, cfg)
        # Unsupported causal claim without evidence should block
        assert verdict.decision == "block", (
            f"Expected block for unsupported causal claim, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )


class TestRepairResponseUnchanged:
    """Case 7: Repair response → unchanged allow behavior."""

    def test_repair_response_with_structured_sections_warns_not_blocks(self):
        """Structured [FACT] response with evidence → allow (warn acceptable).

        A response with [FACT] sections and evidence markers goes through the
        structured path. It can warn about missing other sections but must
        NOT block. This is the unchanged behavior for repair-style responses.
        """
        from epistemic_validator import validate, EpistemicConfig

        response = (
            "[FACT]\n"
            "- The fix is at P:\\.claude\\hooks\\epistemic_validator.py line 1132.\n"
            "  (source: this file)"
        )
        cfg = EpistemicConfig(tool_transcript="")
        verdict = validate(response, cfg)
        # Structured path: warn about missing [INFERENCE]/[UNKNOWN]/[RECOMMENDATION]
        # but should NOT block. allow or warn are both acceptable here.
        assert verdict.decision in ("allow", "warn"), (
            f"Expected allow/warn for structured [FACT] response, got: {verdict.decision}, "
            f"issues: {verdict.issues}"
        )
        assert verdict.decision != "block", (
            f"[FACT] response with evidence should not block, got issues: {verdict.issues}"
        )
