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
        """_check_investigation_in_ledger must return True on ledger errors."""
        from anti_sycophancy.lazy_closure_detector import _check_investigation_in_ledger
        # Function already verified: returns True when ledger unavailable
        result = _check_investigation_in_ledger()
        assert result is True, "Must fail open"

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
