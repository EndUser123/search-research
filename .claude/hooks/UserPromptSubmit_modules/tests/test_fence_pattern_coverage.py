"""
Test-Driven Pattern Development for FENC (Chesterton's Fence) Pattern Coverage

Following CLAUDE.md Test-Driven Pattern Development protocol:
1. Create test corpus first - Gather real examples (positive and negative cases)
2. Write test script - Create automated test
3. Verify baseline - Run test to confirm current behavior
4. Modify pattern - Apply fix with test coverage
5. Verify improvement - Confirm 0 regressions, better accuracy

This file establishes BASELINE behavior before ADR-20260322 implementation.
"""

import pytest
from cognitive_enhancers import _IMPL_RE, _MODIFY_RE


class TestFENCEBaselineCoverage:
    """Document current FENC trigger rate before ADR-20260322 changes."""

    def test_baseline_positive_cases_currently_missed(self):
        """
        BASELINE: These prompts SHOULD trigger FENCE but currently DON'T.
        This documents the bug that ADR-20260322 aims to fix.
        """
        # Positive cases that SHOULD trigger FENCE but currently DON'T (via _MODIFY_RE)
        # Note: These may still trigger implementation intent via _IMPL_RE
        missed_cases = [
            "improve the auth system",
            "enhance the payment module",
            "optimize the database queries",
            "extend the user management",
            "modify the existing code",
            "update the current implementation",
            "change the legacy system",
        ]

        for prompt in missed_cases:
            # Check if _MODIFY_RE matches (FENCE-specific pattern)
            modify_match = _MODIFY_RE.search(prompt)
            impl_match = _IMPL_RE.search(prompt)

            # BASELINE ASSERTION: These DON'T match _MODIFY_RE (this is the bug)
            # They MAY match _IMPL_RE (that's different - implementation intent vs FENCE)
            if modify_match is None:
                # This is expected baseline - _MODIFY_RE doesn't have these words yet
                pass  # Baseline: modify_match is False (documents current bug)
            else:
                # If this fails, it means Option A was already implemented
                pytest.fail(
                    f"Baseline assumption violated: {prompt} matches _MODIFY_RE. "
                    "Option A may already be implemented."
                )

    def test_baseline_negative_cases_should_not_trigger_fence(self):
        """
        BASELINE: These prompts should NOT trigger FENCE.
        They're new code creation, not modification of existing code.
        """
        negative_cases = [
            "create a new feature",
            "build a new module",
            "write documentation",
            "design a new system",
            "implement from scratch",
        ]

        for prompt in negative_cases:
            modify_match = _MODIFY_RE.search(prompt)
            impl_match = _IMPL_RE.search(prompt)

            # These should NOT trigger FENCE (no modification of existing code)
            # _MODIFY_RE should not match
            assert modify_match is None, (
                f"Baseline violated: {prompt} matches _MODIFY_RE. "
                "This should not match because it's creating NEW code, not modifying existing code."
            )

    def test_baseline_current_modify_re_words(self):
        """Document which words are currently in _MODIFY_RE pattern."""
        # Test that current _MODIFY_RE words work
        current_modify_cases = [
            "refactor the auth system",
            "change the payment module",
            "modify the database",
            "update the implementation",
            "fix the legacy code",
            "replace the system",
            "rewrite the module",
            "convert the code",
            "migrate the data",
            "restructure the component",
        ]

        for prompt in current_modify_cases:
            assert (
                _MODIFY_RE.search(prompt) is not None
            ), f"Baseline: {prompt} should match _MODIFY_RE (currently supported word)"

    def test_baseline_pattern_overlap_analysis(self):
        """
        BASELINE: Analyze pattern overlap between _IMPL_RE and _MODIFY_RE.
        This documents which words appear in BOTH patterns.
        """
        overlap_cases = [
            "change the system",  # Both _IMPL_RE and _MODIFY_RE have "change"
            "modify the code",  # Both have "modify"
            "update the module",  # Both have "update"
            "fix the bug",  # Both have "fix"
        ]

        for prompt in overlap_cases:
            impl_match = _IMPL_RE.search(prompt)
            modify_match = _MODIFY_RE.search(prompt)

            # Document: These trigger BOTH patterns
            # This is intentional - implementation intent + FENCE trigger
            assert impl_match is not None, f"{prompt} should trigger implementation intent"
            assert modify_match is not None, f"{prompt} should trigger modify pattern"

    def test_baseline_improve_optimize_extend_enhance_not_in_modify_re(self):
        """
        BASELINE: Document that 'improve|optimize|extend|enhance' are NOT in _MODIFY_RE.
        This is the bug that ADR-20260322 Option A aims to fix.
        """
        not_in_modify_re = [
            "improve the system",
            "optimize the database",
            "extend the functionality",
            "enhance the module",
        ]

        for prompt in not_in_modify_re:
            # BASELINE: These DON'T match _MODIFY_RE (this is the bug)
            modify_match = _MODIFY_RE.search(prompt)
            assert modify_match is None, (
                f"Baseline: {prompt} should NOT match _MODIFY_RE yet. "
                "This documents the current bug before ADR implementation."
            )

            # But they DO match _IMPL_RE (implementation intent)
            impl_match = _IMPL_RE.search(prompt)
            assert (
                impl_match is not None
            ), f"Baseline: {prompt} should match _IMPL_RE (implementation intent)"


class TestFENCEImprovedCoverage:
    """
    Tests that will PASS AFTER ADR-20260322 Option A is implemented.
    Run these after adding 'improve|optimize|extend|enhance' to _MODIFY_RE.
    """

    @pytest.mark.skipif(
        True,  # Skip until Option A is implemented
        reason="Option A not implemented yet - add improve|optimize|extend|enhance to _MODIFY_RE",
    )
    def test_option_a_improve_triggers_fence(self):
        """After Option A: 'improve the auth system' should trigger FENCE."""
        assert _MODIFY_RE.search("improve the auth system") is not None

    @pytest.mark.skipif(
        True,  # Skip until Option A is implemented
        reason="Option A not implemented yet",
    )
    def test_option_a_optimize_triggers_fence(self):
        """After Option A: 'optimize the database' should trigger FENCE."""
        assert _MODIFY_RE.search("optimize the database queries") is not None

    @pytest.mark.skipif(
        True,  # Skip until Option A is implemented
        reason="Option A not implemented yet",
    )
    def test_option_a_extend_triggers_fence(self):
        """After Option A: 'extend the functionality' should trigger FENCE."""
        assert _MODIFY_RE.search("extend the user management") is not None

    @pytest.mark.skipif(
        True,  # Skip until Option A is implemented
        reason="Option A not implemented yet",
    )
    def test_option_a_enhance_triggers_fence(self):
        """After Option A: 'enhance the module' should trigger FENCE."""
        assert _MODIFY_RE.search("enhance the payment module") is not None


def test_fence_context_re_not_implemented():
    """
    BASELINE: Verify that _FENCE_CONTEXT_RE does NOT exist.
    This documents that Option B was never implemented.
    """
    import cognitive_enhancers

    # Verify pattern doesn't exist
    assert not hasattr(
        cognitive_enhancers, "_FENCE_CONTEXT_RE"
    ), "Baseline: _FENCE_CONTEXT_RE should not exist. Option B was never implemented."


if __name__ == "__main__":
    # Run baseline tests
    pytest.main([__file__, "-v", "-k", "baseline"])
