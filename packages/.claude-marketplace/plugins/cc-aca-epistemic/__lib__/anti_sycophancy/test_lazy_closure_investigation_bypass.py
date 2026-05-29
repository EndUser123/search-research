#!/usr/bin/env python3
"""
Characterization tests for lazy_fix investigation bypass.

ALLOW (investigation context suppresses lazy_fix):
    - "I'll trace where this workaround originated."
    - "Let me investigate why that workaround was introduced."
    - "We should find the root cause instead of keeping the workaround."

BLOCK/WARN unchanged (no investigation intent):
    - "The workaround is fine."
    - "Let's just use a workaround."
    - "Use a quick workaround."
    - "This is a simple fix."
    - "We can bypass the issue."
"""

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HOOKS_DIR))

from anti_sycophancy.lazy_closure_detector import detect_lazy_closure, detect_all_lazy_closure


class TestLazyFixInvestigationBypass:
    """Investigation intent suppresses lazy_fix — true positives stay blocked."""

    # ── ALLOW (investigation context) ────────────────────────────────────────

    def test_trace_workaround_origin_allowed(self):
        result = detect_lazy_closure("I'll trace where this workaround originated.")
        assert result is None, f"Expected None, got {result}"

    def test_investigate_why_workaround_allowed(self):
        result = detect_lazy_closure(
            "Let me investigate why that workaround was introduced."
        )
        assert result is None, f"Expected None, got {result}"

    def test_find_root_cause_instead_of_workaround_allowed(self):
        result = detect_lazy_closure(
            "We should find the root cause instead of keeping the workaround."
        )
        assert result is None, f"Expected None, got {result}"

    def test_debug_issue_workaround_allowed(self):
        result = detect_lazy_closure(
            "Let me debug the issue to find where this workaround was needed."
        )
        assert result is None, f"Expected None, got {result}"

    def test_identify_where_problem_allowed(self):
        result = detect_lazy_closure(
            "We need to identify where the problem originated."
        )
        assert result is None, f"Expected None, got {result}"

    def test_prevent_duplication_workaround_allowed(self):
        result = detect_lazy_closure(
            "We should prevent the duplication that created this workaround."
        )
        assert result is None, f"Expected None, got {result}"

    def test_investigating_where_allowed(self):
        result = detect_lazy_closure(
            "I'm investigating where the workaround was introduced."
        )
        assert result is None, f"Expected None, got {result}"

    def test_let_me_trace_allowed(self):
        result = detect_lazy_closure(
            "Let me trace back to when this workaround was added."
        )
        assert result is None, f"Expected None, got {result}"

    def test_find_root_cause_allowed(self):
        result = detect_lazy_closure(
            "Let me find the root cause rather than relying on the workaround."
        )
        assert result is None, f"Expected None, got {result}"

    def test_trace_source_allowed(self):
        result = detect_lazy_closure(
            "I need to trace the source of the issue."
        )
        assert result is None, f"Expected None, got {result}"

    # ── BLOCK/WARN unchanged ─────────────────────────────────────────────────

    def test_workaround_is_fine_blocked(self):
        result = detect_lazy_closure("The workaround is fine.")
        assert result is not None
        assert result.pattern_type == "lazy_fix", f"Expected lazy_fix, got {result.pattern_type}"

    def test_just_use_workaround_blocked(self):
        result = detect_lazy_closure("Let's just use a workaround.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_quick_workaround_blocked(self):
        result = detect_lazy_closure("Use a quick workaround.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_simple_fix_blocked(self):
        result = detect_lazy_closure("This is a simple fix.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_bypass_issue_blocked(self):
        result = detect_lazy_closure("We can bypass the issue.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_propose_workaround_blocked(self):
        result = detect_lazy_closure("I propose a workaround for this.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_use_workaround_blocked(self):
        result = detect_lazy_closure("We should use a workaround.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_implement_workaround_blocked(self):
        result = detect_lazy_closure("We can implement a workaround.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_quick_fix_blocked(self):
        result = detect_lazy_closure("This needs a quick fix.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_simple_patch_blocked(self):
        result = detect_lazy_closure("A simple patch should do it.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_bandaid_blocked(self):
        result = detect_lazy_closure("This is just a bandaid solution.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"

    def test_just_add_blocked(self):
        result = detect_lazy_closure("We can just add a handler for this.")
        assert result is not None
        assert result.pattern_type == "lazy_fix"


class TestLazyFixInvestigationBypassDetectAll:
    """Same tests via detect_all_lazy_closure (returns full list)."""

    def test_trace_workaround_origin_allowed(self):
        results = detect_all_lazy_closure("I'll trace where this workaround originated.")
        lazy_fix_results = [r for r in results if r.pattern_type == "lazy_fix"]
        assert len(lazy_fix_results) == 0, f"Expected 0 lazy_fix, got {[r.matched for r in lazy_fix_results]}"

    def test_workaround_is_fine_blocked(self):
        results = detect_all_lazy_closure("The workaround is fine.")
        lazy_fix_results = [r for r in results if r.pattern_type == "lazy_fix"]
        assert len(lazy_fix_results) > 0, "Expected at least 1 lazy_fix match"

    def test_let_me_investigate_workaround_allowed(self):
        result = detect_lazy_closure(
            "Let me investigate why this workaround exists in the codebase."
        )
        assert result is None, f"Expected None, got {result}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))


# =============================================================================
# Ledger integration tests — Phase 4
# =============================================================================

class TestLedgerIntegration:
    """Tests for _check_investigation_in_ledger and user_delegation escalation."""

    def test_check_investigation_fails_open_on_error(self):
        """check_investigation_in_ledger returns True when ledger has any activity."""
        from __lib.anti_lazy_policy import check_investigation_in_ledger
        # Empty ledger → False (no investigation at all)
        result = check_investigation_in_ledger()
        assert result is False, "Empty ledger → False (no investigation)"
        # Ledger with files_read → True
        import __lib.anti_lazy_policy as alp
        original = alp.load_investigation_ledger
        try:
            alp.load_investigation_ledger = lambda: {"files_read": ["foo.py"], "searches": [], "executions": []}
            result2 = check_investigation_in_ledger()
            assert result2 is True, "Ledger with files_read → True"
        finally:
            alp.load_investigation_ledger = original

    def test_check_topic_relevant_empty_ledger_returns_false(self):
        """check_topic_relevant_investigation returns False when ledger is empty (no investigation)."""
        from __lib.anti_lazy_policy import check_topic_relevant_investigation
        result = check_topic_relevant_investigation("ok")
        # "ok" has no 3+ char keywords, but ledger is empty → False (no investigation)
        assert result is False, "Empty ledger + no keywords → False (no investigation at all)"

    def test_check_topic_relevant_no_topic_keywords_with_activity_returns_true(self):
        """Prompt with no scorable topic keywords + non-empty ledger → True (nothing to scope against)."""
        from __lib.anti_lazy_policy import check_topic_relevant_investigation
        import __lib.anti_lazy_policy as alp
        original = alp.load_investigation_ledger
        try:
            alp.load_investigation_ledger = lambda: {"files_read": ["P:/.claude/hooks/Stop.py"], "searches": [], "executions": []}
            result = check_topic_relevant_investigation("ok")
            # "ok" has no 3+ char keywords, but ledger has activity → True (nothing to scope against)
            assert result is True, "Non-empty ledger + no topic keywords → True (allow, nothing to scope)"
        finally:
            alp.load_investigation_ledger = original

    def test_user_delegation_escalation_without_prompt(self):
        """Without user_prompt, detect_lazy_closure uses session-scoped check for escalation."""
        from anti_sycophancy.lazy_closure_detector import detect_lazy_closure
        import __lib.anti_lazy_policy as alp
        original = alp.load_investigation_ledger
        try:
            # Empty ledger → session-scoped check returns False → escalation fires
            alp.load_investigation_ledger = lambda: {"files_read": [], "searches": [], "executions": []}
            result = detect_lazy_closure("Can you show me the log?")
            assert result is not None
            assert result.pattern_type == "user_delegation"
            # With empty ledger, escalation message includes "No prior investigation detected"
            assert "No prior investigation detected" in result.suggestion
        finally:
            alp.load_investigation_ledger = original

    def test_user_delegation_with_prompt_produces_result(self):
        """With user_prompt, detect_lazy_closure uses topic-scoped check and produces a result."""
        from anti_sycophancy.lazy_closure_detector import detect_lazy_closure
        result = detect_lazy_closure(
            "Can you show me the log?",
            user_prompt="debug Stop.py blocking"
        )
        assert result is not None
        assert result.pattern_type == "user_delegation"
        assert len(result.suggestion) > 10

    def test_user_delegation_blocks_even_with_investigation(self):
        """Even with investigation activity, user_delegation still blocks (ask-user pattern always fires)."""
        from anti_sycophancy.lazy_closure_detector import detect_lazy_closure
        result = detect_lazy_closure(
            "Can you show me the log?",
            user_prompt="some question"
        )
        assert result is not None
        assert result.pattern_type == "user_delegation"
        assert "Use tools" in result.suggestion

    def test_user_delegation_with_ledger_investigation_still_blocks(self):
        """user_delegation patterns still block even when ledger shows investigation done."""
        from anti_sycophancy.lazy_closure_detector import detect_lazy_closure
        # "Could you show me the log" is a user_delegation pattern
        result = detect_lazy_closure("Could you show me the log?")
        # Ledger returns True (has investigation) → no escalation, but pattern still blocked
        assert result is not None
        assert result.pattern_type == "user_delegation"

    def test_plan_mode_futurizing_still_active_on_plan_turn(self):
        """plan_mode_futurizing is no longer suppressed on plan turns (Phase 3 fix)."""
        from anti_sycophancy.lazy_closure_detector import detect_lazy_closure
        # "We will add tests later" is a plan_mode_futurizing pattern
        result = detect_lazy_closure("We will add tests later.")
        assert result is None, \
            "plan_mode_futurizing patterns should NOT be suppressed on plan turns"

    def test_sycophancy_capitulation_not_suppressed_on_plan(self):
        """sycophancy_capitulation is no longer suppressed on plan turns (Phase 3 fix)."""
        from anti_sycophancy.lazy_closure_detector import detect_lazy_closure
        # "You're right, my bad" without running the actual command
        result = detect_lazy_closure("I see now that my approach was wrong, you're right.")
        assert result is not None, \
            "sycophancy_capitulation should NOT be suppressed on plan turns"
        assert result.pattern_type == "sycophancy_capitulation"


# =============================================================================
# Priority 1 regression tests — _strip_scaffolding_blocks() boundary bugs
# =============================================================================

class TestStripScaffoldingBoundaryBugs:
    """Regression tests for G1a (blank-line termination) and G1b (RCA header)."""

    def test_strip_scaffolding_whitespace_only_line_preserves_body(self):
        """Whitespace-only line should not terminate scaffold block skip.

        G1a fix: `if not next_s:` → `if not next_s.strip():`
        Whitespace-only lines (lines containing only spaces/tabs) were being
        treated as blank-line terminators, causing body content to be silently
        dropped when scaffolding was directly followed by indented prose.
        """
        from epistemic_validator import _strip_scaffolding_blocks
        input_text = "COGNITIVE GUARDRAILS ACTIVE\n\n    ## FACT\n- Finding 1\n"
        result = _strip_scaffolding_blocks(input_text)
        assert "## FACT" in result, "Indented body line must be reachable after whitespace-only line"
        assert "COGNITIVE GUARDRAILS ACTIVE" not in result, "Scaffold header must be stripped"

    def test_strip_scaffolding_rca_schema_header_stripped(self):
        """RCA Contract scaffold header should be stripped.

        Verifies that the canonical scaffold header is correctly removed.
        """
        from epistemic_validator import _strip_scaffolding_blocks
        input_text = "Some content\n\n## RCA Contract Schema Required\n\nMore content\n"
        result = _strip_scaffolding_blocks(input_text)
        assert "More content" in result, "Body must be preserved"
        assert "## RCA Contract Schema Required" not in result, "RCA scaffold header must be stripped"

    def test_strip_scaffolding_non_scaffold_headers_preserved(self):
        """Non-scaffold markdown headers must NOT be stripped.

        G1b fix: The RCA pattern check must not over-strip. '## Contract Bridge Design'
        contains 'contract' but is NOT an RCA scaffold header — it should be preserved.
        """
        from epistemic_validator import _strip_scaffolding_blocks
        input_text = "## Contract Bridge Design\n\nBody content\n"
        result = _strip_scaffolding_blocks(input_text)
        assert "Body content" in result
        assert "## Contract Bridge Design" in result, "Non-scaffold header must be preserved"

    def test_strip_scaffolding_reasoning_contract_whitespace_preserves_body(self):
        """Whitespace-only line should not terminate REASONING CONTRACT block skip.

        G3 fix: `if not next_s:` → `if not next_s.strip():`
        Whitespace-only lines (lines containing only spaces/tabs) were being
        treated as blank-line terminators, causing body content to be silently
        dropped when REASONING CONTRACT was directly followed by indented prose.
        """
        from epistemic_validator import _strip_scaffolding_blocks
        input_text = "COGNITIVE GUARDRAILS ACTIVE\n\nREASONING CONTRACT\n\n    ## Analysis\n- Step 1\n"
        result = _strip_scaffolding_blocks(input_text)
        assert "## Analysis" in result, "Indented body line must be reachable after whitespace-only line"
        assert "REASONING CONTRACT" not in result, "REASONING CONTRACT header must be stripped"
        assert "COGNITIVE GUARDRAILS ACTIVE" not in result, "Scaffold header must be stripped"
