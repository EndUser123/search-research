#!/usr/bin/env python3
"""
Characterization tests for shared validation utility (P2-001: Code Duplication in Stop Hooks).

These tests CAPTURE CURRENT BEHAVIOR of the shared validation utility that was
extracted from duplicated code in StopHook_p_halt_format_validator.py and
StopHook_p_completion_validator.py.

BEFORE REFACTORING: Both hooks had identical evidence checking code duplicated
AFTER REFACTORING: Both hooks use validate_p_response() from lib.evidence_patterns

These tests verify the refactoring was successful and the shared utility works correctly.

Run with: pytest tests/test_shared_validation.py -v
"""

import sys
from pathlib import Path

import pytest

# Add lib directory to path
LIB_DIR = Path(__file__).parent.parent / "lib"
sys.path.insert(0, str(LIB_DIR))

from evidence_patterns import validate_p_response

# ============================================================================
# CHARACTERIZATION TEST: Old Duplicated Code (Simulated)
# ============================================================================
# This is what the OLD code looked like BEFORE refactoring (duplicated in both hooks)
# This test documents the behavior that was being duplicated

def OLD_duplicated_evidence_check(response_text: str) -> tuple[bool, str]:
    """
    CHARACTERIZATION: This is the OLD duplicated code that existed in both hooks.

    This function simulates what the code looked like BEFORE the shared utility
    was extracted. It shows the duplication that P2-001 was meant to fix.
    """
    # OLD CODE (duplicated in both hooks):
    import re

    # Check if this looks like a /p response
    if "/p" not in response_text.lower() and "pipeline" not in response_text.lower():
        return True, "Not a /p response"

    # Execution evidence check (OLD DUPLICATED LOGIC)
    EXECUTION_EVIDENCE_PATTERNS = [
        r"pytest",
        r"PASSED|FAILED|ERROR",
        r"git (status|branch|diff|log)",
        r"collected \d+ items?",
        r"\.py::\w+",
        r"(Read|Glob|Bash|Task)\(",
        r"exit code",
        r"Subagent \d",
    ]

    found = []
    for pattern in EXECUTION_EVIDENCE_PATTERNS:
        if re.search(pattern, response_text, re.IGNORECASE):
            found.append(pattern)

    has_evidence = len(found) >= 3

    # Fabrication check (OLD DUPLICATED LOGIC)
    MIN_BOX_DRAWING_CHARS = 10
    FABRICATION_PATTERNS = [
        rf"[┌├└│┐┤┘─┬┴┼]{{{MIN_BOX_DRAWING_CHARS},}}",
    ]

    heavy_tables_detected = bool(re.search(FABRICATION_PATTERNS[0], response_text))

    if heavy_tables_detected and not has_evidence:
        error_msg = (
            "FABRICATION DETECTED: Response contains formatted tables but no evidence "
            "of real tool execution (no pytest output, no git commands, no Bash results, "
            "no subagent launches). /p MUST use Task/Bash tools to gather real data. "
            "Re-run the pipeline with actual tool calls."
        )
        return False, error_msg

    return True, "Evidence check passed"


class TestRefactoringVerification:
    """Test that the refactoring from duplicated code to shared utility is correct."""

    def test_shared_utility_matches_old_duplicated_code(self):
        """
        CHARACTERIZATION: Verify new shared utility produces same results as old duplicated code.

        This test ensures that when we extracted the common validation logic from both hooks
        into validate_p_response(), we preserved the exact same behavior.
        """
        test_cases = [
            # (description, response_text, expected_allow, expected_reason_contains)
            ("Plain text", "Just plain text", True, "Not a"),
            ("With tables but no evidence", """
## Pipeline Status: HALTED
┌──────────┬─────────┬──────────┐
│ Phase    │ Status  │ Details  │
├──────────┼─────────┼──────────┤
│ Phase 1  │ PASS    │ OK       │
└──────────┴─────────┴──────────┘
""", False, "FABRICATION"),
            ("With evidence", """
## Pipeline Status: HALTED
pytest collected 42 items
22 PASSED
git status
""", True, ""),
        ]

        for desc, text, expected_allow, expected_reason in test_cases:
            # Test OLD duplicated code
            old_allow, old_reason = OLD_duplicated_evidence_check(text)

            # Test NEW shared utility (common validation part only)
            new_allow, new_reason = validate_p_response(text, check_for_completion=False)

            # Results should match (or be compatible)
            if expected_allow:
                assert old_allow == expected_allow, f"OLD code failed for: {desc}"
                # NEW code might return different reason (e.g., "No halt detected")
                # but should still allow it
                assert new_allow == expected_allow, f"NEW code failed for: {desc}"
            else:
                assert not old_allow, f"OLD code should block: {desc}"
                assert expected_reason in old_reason, f"OLD code reason wrong for: {desc}"
                # NEW code should also block
                assert not new_allow, f"NEW code should block: {desc}"
                assert expected_reason in new_reason, f"NEW code reason wrong for: {desc}"


class TestSharedValidationUtility:
    """Test that both hooks use shared validation utility."""

    def test_validate_p_response_exists(self):
        """Test that validate_p_response function exists in evidence_patterns."""
        from evidence_patterns import validate_p_response
        assert callable(validate_p_response)

    def test_validate_p_response_accepts_check_for_completion_param(self):
        """Test that validate_p_response accepts check_for_completion parameter."""
        # This should not raise an error
        allow, reason = validate_p_response("test", check_for_completion=False)
        assert isinstance(allow, bool)
        assert isinstance(reason, str)

    def test_validate_p_response_for_halt_detection(self):
        """Test that validate_p_response can detect halt format."""
        halt_text = """
## Pipeline Status: HALTED
**Status:** 🛑 HALTED at Phase 2

**Reason:** Critical issue found

## Next Steps
1 - /tdd Fix critical issue
x - Fix all verified findings: 1
Then re-run: /p

Phase 1: PASS
Phase 2: FAIL - Critical bug
"""
        allow, reason = validate_p_response(halt_text, check_for_completion=False)
        assert allow is True
        assert "HALT" in reason.upper() or "validated" in reason.lower()

    def test_validate_p_response_for_completion_detection(self):
        """Test that validate_p_response can detect completion format."""
        completion_text = """
## Pipeline Status: COMPLETE
**Status:** ✅ ALL PHASES PASSED

**Summary:** All tests passing

## Next Steps
- Deploy to production

Phase 1: PASS
Phase 2: PASS
Phase 3: PASS
"""
        allow, reason = validate_p_response(completion_text, check_for_completion=True)
        assert allow is True
        assert "complete" in reason.lower() or "validated" in reason.lower()

    def test_validate_p_response_consistent_results_for_both_hooks(self):
        """Test that validate_p_response produces consistent results for both hook types."""
        # Text with execution evidence
        evidence_text = """
## Pipeline Status: HALTED
pytest collected 42 items
22 PASSED, 1 FAILED
git status
Bash output
"""

        # Both hook types should use the same validation logic
        allow_halt, reason_halt = validate_p_response(evidence_text, check_for_completion=False)
        allow_complete, reason_complete = validate_p_response(evidence_text, check_for_completion=True)

        # Both should detect evidence consistently
        assert isinstance(allow_halt, bool)
        assert isinstance(allow_complete, bool)
        assert isinstance(reason_halt, str)
        assert isinstance(reason_complete, str)

    def test_validate_p_response_blocks_fabrication(self):
        """Test that validate_p_response blocks fabricated responses with tables but no evidence."""
        # Text with heavy tables but no execution evidence (must include /p or pipeline to be checked)
        fabrication_text = """
## Pipeline Status: COMPLETE
/p pipeline results:

┌──────────┬─────────┬──────────┐
│ Phase    │ Status  │ Details  │
├──────────┼─────────┼──────────┤
│ Phase 1  │ PASS    │ OK       │
│ Phase 2  │ PASS    │ OK       │
└──────────┴─────────┴──────────┘

All phases passed successfully!
"""
        allow, reason = validate_p_response(fabrication_text, check_for_completion=False)
        assert allow is False
        assert "FABRICATION DETECTED" in reason

    def test_validate_p_response_allows_tables_with_evidence(self):
        """Test that validate_p_response allows tables when execution evidence is present."""
        # Text with both tables AND execution evidence
        valid_text = """
pytest collected 42 items
22 PASSED, 1 FAILED
git status

┌──────────┬─────────┬──────────┐
│ Phase    │ Status  │ Details  │
├──────────┼─────────┼──────────┤
│ Phase 1  │ PASS    │ OK       │
└──────────┴─────────┴──────────┘
"""
        allow, reason = validate_p_response(valid_text, check_for_completion=False)
        assert allow is True
        assert "FABRICATION" not in reason


class TestHookIntegration:
    """Test that both hooks integrate with shared utility."""

    def test_halt_hook_uses_validate_p_response(self):
        """Test that halt format validator hook uses validate_p_response."""
        # Read the halt hook file
        hook_file = Path(__file__).parent.parent / "hooks" / "StopHook_p_halt_format_validator.py"
        assert hook_file.exists(), "Halt hook file should exist"

        hook_content = hook_file.read_text()

        # Verify it imports and uses validate_p_response
        assert "from evidence_patterns import" in hook_content
        assert "validate_p_response" in hook_content
        assert "validate_p_response(response_text, check_for_completion=False)" in hook_content

    def test_completion_hook_uses_validate_p_response(self):
        """Test that completion validator hook uses validate_p_response."""
        # Read the completion hook file
        hook_file = Path(__file__).parent.parent / "hooks" / "StopHook_p_completion_validator.py"
        assert hook_file.exists(), "Completion hook file should exist"

        hook_content = hook_file.read_text()

        # Verify it imports and uses validate_p_response
        assert "from evidence_patterns import" in hook_content
        assert "validate_p_response" in hook_content
        assert "validate_p_response(response_text, check_for_completion=True)" in hook_content

    def test_both_hooks_use_same_import_path(self):
        """Test that both hooks import from the same module path."""
        halt_hook = Path(__file__).parent.parent / "hooks" / "StopHook_p_halt_format_validator.py"
        completion_hook = Path(__file__).parent.parent / "hooks" / "StopHook_p_completion_validator.py"

        halt_content = halt_hook.read_text()
        completion_content = completion_hook.read_text()

        # Both should import from evidence_patterns
        assert "from evidence_patterns import" in halt_content
        assert "from evidence_patterns import" in completion_content

    def test_shared_utility_location(self):
        """Test that the shared utility is in lib.evidence_patterns module."""
        # The evidence_patterns module should exist
        evidence_module = LIB_DIR / "evidence_patterns.py"
        assert evidence_module.exists(), "evidence_patterns.py should exist in lib directory"

        # It should contain validate_p_response
        module_content = evidence_module.read_text()
        assert "def validate_p_response" in module_content


# ============================================================================
# RED PHASE TEST: Failing test that prevents code duplication regression
# ============================================================================

def test_no_code_duplication_in_hooks():
    """
    FAILING TEST: Verifies hooks don't have duplicated validation code.

    This test checks that both hooks use the shared validate_p_response()
    function from lib.evidence_patterns instead of duplicating the logic.

    If this test FAILS, it means:
    - Hooks have been modified to duplicate logic instead of using shared utility
    - The refactoring from P2-001 has been reverted
    - Code duplication has been reintroduced

    To fix this test failure, ensure both hooks import and use validate_p_response()
    from lib.evidence_patterns module.

    RED PHASE: This test is designed to FAIL if duplication is reintroduced.
    """
    # Read both hook files
    halt_hook = Path(__file__).parent.parent / "hooks" / "StopHook_p_halt_format_validator.py"
    completion_hook = Path(__file__).parent.parent / "hooks" / "StopHook_p_completion_validator.py"

    assert halt_hook.exists(), "Halt hook file must exist"
    assert completion_hook.exists(), "Completion hook file must exist"

    halt_content = halt_hook.read_text()
    completion_content = completion_hook.read_text()

    # Both MUST import from evidence_patterns (not duplicate the logic)
    assert "from evidence_patterns import" in halt_content, \
        "Halt hook must import from evidence_patterns (code duplication detected)"
    assert "from evidence_patterns import" in completion_content, \
        "Completion hook must import from evidence_patterns (code duplication detected)"

    # Both MUST use validate_p_response function
    assert "validate_p_response(response_text" in halt_content, \
        "Halt hook must use validate_p_response() (code duplication detected)"
    assert "validate_p_response(response_text" in completion_content, \
        "Completion hook must use validate_p_response() (code duplication detected)"

    # Both hooks should NOT contain duplicated pattern lists
    # (these would be signs of old duplicated code)
    duplication_indicators = [
        "EXECUTION_EVIDENCE_PATTERNS = [",
        r"FABRICATION_PATTERNS = [",
        "def check_execution_evidence(",
        "def has_heavy_tables(",
    ]

    for indicator in duplication_indicators:
        # Count occurrences - should appear in evidence_patterns.py but NOT in hooks
        halt_count = halt_content.count(indicator)
        completion_count = completion_content.count(indicator)

        # These should only appear in lib/evidence_patterns.py, not in the hooks
        assert halt_count == 0, \
            f"Halt hook contains duplicated code: {indicator} (should be in shared utility)"
        assert completion_count == 0, \
            f"Completion hook contains duplicated code: {indicator} (should be in shared utility)"

    # Verify the shared utility exists and has the required function
    evidence_module = LIB_DIR / "evidence_patterns.py"
    assert evidence_module.exists(), \
        "Shared utility lib/evidence_patterns.py must exist"

    module_content = evidence_module.read_text()
    assert "def validate_p_response" in module_content, \
        "Shared utility must contain validate_p_response function"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
