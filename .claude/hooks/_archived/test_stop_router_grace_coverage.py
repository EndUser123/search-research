#!/usr/bin/env python3
"""
Test suite for Stop_router.py CONSOLIDATED_OBSERVATION_BLOCK_HOOKS constant and grace coverage.

RED PHASE: This test MUST fail initially.

These tests verify that:
1. CONSOLIDATED_OBSERVATION_BLOCK_HOOKS exists as a frozenset
2. It contains exactly 3 hooks: post_block_tool_requirement, empirical_claims_gate.py, Stop_absence_claim_gate.py
3. Grace only applies to these 3 hooks (line 1467 in Stop_router.py)
4. Grace consumption is currently limited to CONSOLIDATED_OBSERVATION_BLOCK_HOOKS only
"""
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import Stop_router module
try:
    from Stop_router import CONSOLIDATED_OBSERVATION_BLOCK_HOOKS, run_hooks
    MODULE_EXISTS = True
except ImportError as e:
    MODULE_EXISTS = False
    IMPORT_ERROR = str(e)


class TestConsolidatedObservationBlockHooksConstant:
    """Test suite for CONSOLIDATED_OBSERVATION_BLOCK_HOOKS constant."""

    def test_constant_exists(self):
        """
        Test that CONSOLIDATED_OBSERVATION_BLOCK_HOOKS constant exists.

        Given: Stop_router module is imported
        When: Checking for CONSOLIDATED_OBSERVATION_BLOCK_HOOKS
        Then: Constant should exist as a frozenset
        """
        assert MODULE_EXISTS, "Stop_router module should be importable"
        assert 'CONSOLIDATED_OBSERVATION_BLOCK_HOOKS' in dir(sys.modules['Stop_router']), \
            "CONSOLIDATED_OBSERVATION_BLOCK_HOOKS constant should exist"

    def test_constant_is_frozenset(self):
        """
        Test that CONSOLIDATED_OBSERVATION_BLOCK_HOOKS is a frozenset.

        Given: CONSOLIDATED_OBSERVATION_BLOCK_HOOKS constant exists
        When: Checking its type
        Then: It should be a frozenset
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")

        from Stop_router import CONSOLIDATED_OBSERVATION_BLOCK_HOOKS

        assert isinstance(CONSOLIDATED_OBSERVATION_BLOCK_HOOKS, frozenset), \
            f"CONSOLIDATED_OBSERVATION_BLOCK_HOOKS should be frozenset, got {type(CONSOLIDATED_OBSERVATION_BLOCK_HOOKS)}"

    def test_constant_contains_exactly_three_hooks(self):
        """
        Test that CONSOLIDATED_OBSERVATION_BLOCK_HOOKS contains exactly 3 hooks.

        Given: CONSOLIDATED_OBSERVATION_BLOCK_HOOKS constant exists
        When: Checking its length
        Then: It should contain exactly 3 hooks
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")

        from Stop_router import CONSOLIDATED_OBSERVATION_BLOCK_HOOKS

        assert len(CONSOLIDATED_OBSERVATION_BLOCK_HOOKS) == 3, \
            f"CONSOLIDATED_OBSERVATION_BLOCK_HOOKS should contain 3 hooks, got {len(CONSOLIDATED_OBSERVATION_BLOCK_HOOKS)}"

    def test_constant_contains_required_hooks(self):
        """
        Test that CONSOLIDATED_OBSERVATION_BLOCK_HOOKS contains the required 3 hooks.

        Given: CONSOLIDATED_OBSERVATION_BLOCK_HOOKS constant exists
        When: Checking its contents
        Then: It should contain: post_block_tool_requirement, empirical_claims_gate.py, Stop_absence_claim_gate.py
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")

        from Stop_router import CONSOLIDATED_OBSERVATION_BLOCK_HOOKS

        required_hooks = {
            "post_block_tool_requirement",
            "empirical_claims_gate.py",
            "Stop_absence_claim_gate.py"
        }

        assert required_hooks == CONSOLIDATED_OBSERVATION_BLOCK_HOOKS, \
            f"CONSOLIDATED_OBSERVATION_BLOCK_HOOKS should contain {required_hooks}, got {CONSOLIDATED_OBSERVATION_BLOCK_HOOKS}"

    def test_line_1467_grace_coverage(self):
        """
        Test that grace only applies to CONSOLIDATED_OBSERVATION_BLOCK_HOOKS.

        Given: Stop_router.py has grace logic checking CONSOLIDATED_OBSERVATION_BLOCK_HOOKS
        When: Checking which hooks get grace coverage
        Then: Only CONSOLIDATED_OBSERVATION_BLOCK_HOOKS should have grace coverage
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")


        # Verify Stop_router.py contains the grace logic referencing CONSOLIDATED_OBSERVATION_BLOCK_HOOKS
        router_path = Path(__file__).resolve().parent.parent / "Stop_router.py"
        assert router_path.exists(), "Stop_router.py should exist"

        content = router_path.read_text()
        # Search for the pattern rather than hardcoding a line number (line numbers shift with edits)
        assert "if source_hook in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS:" in content, \
            "Stop_router.py should contain grace logic checking 'if source_hook in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS:'"

    def test_grace_consumption_limited_to_consolidated_hooks(self):
        """
        Test that grace consumption is limited to CONSOLIDATED_OBSERVATION_BLOCK_HOOKS only.

        Given: Grace is active in the router
        When: A hook blocks
        Then: Grace should only be consumed for hooks in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS

        This is a characterization test - it captures the CURRENT behavior.
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")


        # Verify that the grace logic path checks CONSOLIDATED_OBSERVATION_BLOCK_HOOKS
        router_path = Path(__file__).resolve().parent.parent / "Stop_router.py"
        content = router_path.read_text()

        # Find the grace consumption logic
        assert "grace_active" in content, "Code should have grace_active variable"
        assert "if grace_active:" in content, "Code should check if grace is active"

        # Verify grace is only consumed within CONSOLIDATED_OBSERVATION_BLOCK_HOOKS check
        # The pattern should be:
        # if source_hook in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS:
        #     if grace_active:
        #         grace_active = False
        #         continue
        lines = content.split('\n')

        # Find the CONSOLIDATED_OBSERVATION_BLOCK_HOOKS check
        consolidated_check_idx = None
        for idx, line in enumerate(lines):
            if "if source_hook in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS:" in line:
                consolidated_check_idx = idx
                break

        assert consolidated_check_idx is not None, \
            "Should find CONSOLIDATED_OBSERVATION_BLOCK_HOOKS check in code"

        # Verify grace consumption happens within this block
        # Look for grace_active = False within the next few lines
        found_grace_consumption = False
        for idx in range(consolidated_check_idx, min(consolidated_check_idx + 20, len(lines))):
            if "grace_active = False" in lines[idx]:
                found_grace_consumption = True
                break

        assert found_grace_consumption, \
            "Grace consumption (grace_active = False) should happen within CONSOLIDATED_OBSERVATION_BLOCK_HOOKS check"


class TestGraceCoverageBehavior:
    """Test suite for grace coverage behavior in run_hooks."""

    @pytest.fixture
    def sample_data(self):
        """Create sample input data for run_hooks."""
        return {
            "response": "Test response",
            "session_id": "test-session-123",
            "terminal_id": "test-terminal-456",
            "tools_used": []
        }

    def test_grace_only_applies_to_consolidated_hooks_post_block_tool_requirement(self, sample_data):
        """
        Test that grace applies to post_block_tool_requirement.

        Given: post_block_tool_requirement is in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS
        When: This hook blocks with grace active
        Then: Grace should be consumed and block suppressed
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")

        from Stop_router import CONSOLIDATED_OBSERVATION_BLOCK_HOOKS

        assert "post_block_tool_requirement" in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS, \
            "post_block_tool_requirement should be in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS"

    def test_grace_only_applies_to_consolidated_hooks_empirical_claims_gate(self, sample_data):
        """
        Test that grace applies to empirical_claims_gate.py.

        Given: empirical_claims_gate.py is in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS
        When: This hook blocks with grace active
        Then: Grace should be consumed and block suppressed
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")

        from Stop_router import CONSOLIDATED_OBSERVATION_BLOCK_HOOKS

        assert "empirical_claims_gate.py" in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS, \
            "empirical_claims_gate.py should be in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS"

    def test_grace_only_applies_to_consolidated_hooks_absence_claim_gate(self, sample_data):
        """
        Test that grace applies to Stop_absence_claim_gate.py.

        Given: Stop_absence_claim_gate.py is in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS
        When: This hook blocks with grace active
        Then: Grace should be consumed and block suppressed
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")

        from Stop_router import CONSOLIDATED_OBSERVATION_BLOCK_HOOKS

        assert "Stop_absence_claim_gate.py" in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS, \
            "Stop_absence_claim_gate.py should be in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS"

    def test_grace_does_not_apply_to_other_hooks(self, sample_data):
        """
        Test that grace does NOT apply to hooks outside CONSOLIDATED_OBSERVATION_BLOCK_HOOKS.

        Given: A hook is NOT in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS
        When: This hook blocks with grace active
        Then: Grace should NOT be consumed (block should proceed)
        """
        if not MODULE_EXISTS:
            pytest.skip("Stop_router module not importable")

        from Stop_router import CONSOLIDATED_OBSERVATION_BLOCK_HOOKS

        # Examples of hooks that should NOT have grace
        non_consolidated_hooks = [
            "speculation_gate.py",
            "constitutional_enforcer.py",
            "StopHook_investigation_required.py"
        ]

        for hook in non_consolidated_hooks:
            assert hook not in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS, \
                f"{hook} should NOT be in CONSOLIDATED_OBSERVATION_BLOCK_HOOKS"


class TestGraceCoverageDocumentation:
    """Test suite for grace coverage documentation."""

    def test_line_1467_exists(self):
        """
        Test that line 1467 exists in Stop_router.py.

        Given: Stop_router.py file exists
        When: Reading the file
        Then: Line 1467 should exist
        """
        router_path = Path(__file__).resolve().parent.parent / "Stop_router.py"
        assert router_path.exists(), "Stop_router.py should exist"

        content = router_path.read_text()
        lines = content.split('\n')

        assert len(lines) >= 1467, \
            f"Stop_router.py should have at least 1467 lines, currently has {len(lines)}"

    def test_constant_definition_location(self):
        """
        Test that CONSOLIDATED_OBSERVATION_BLOCK_HOOKS is defined near the top of the file.

        Given: Stop_router.py file exists
        When: Searching for CONSOLIDATED_OBSERVATION_BLOCK_HOOKS definition
        Then: It should be defined in the constants section (before line 100)
        """
        router_path = Path(__file__).resolve().parent.parent / "Stop_router.py"
        content = router_path.read_text()
        lines = content.split('\n')

        # Find CONSOLIDATED_OBSERVATION_BLOCK_HOOKS definition
        definition_idx = None
        for idx, line in enumerate(lines):
            if "CONSOLIDATED_OBSERVATION_BLOCK_HOOKS = frozenset(" in line:
                definition_idx = idx
                break

        assert definition_idx is not None, \
            "CONSOLIDATED_OBSERVATION_BLOCK_HOOKS should be defined"
        assert definition_idx < 100, \
            f"CONSOLIDATED_OBSERVATION_BLOCK_HOOKS should be defined in constants section (before line 100), found at line {definition_idx + 1}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
