#!/usr/bin/env python3
"""Simple test runner to avoid pytest hanging issues."""

import sys
from pathlib import Path

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(skill_root))

from tiers.tier0_checklist import (
    ChecklistResult,
    FeatureChecklist,
    HookChecklist,
    SkillChecklist,
    run_checklist_verification,
)


def test_checklist_result_creation():
    """Test ChecklistResult can be created with required fields."""
    result = ChecklistResult(
        status="pass",
        items_checked=3,
        items_passed=3,
        findings=["All checks passed"]
    )

    assert result.status == "pass"
    assert result.items_checked == 3
    assert result.items_passed == 3
    assert result.findings == ["All checks passed"]
    print("✓ test_checklist_result_creation PASSED")

def test_checklist_result_partial_status():
    """Test ChecklistResult supports partial status."""
    result = ChecklistResult(
        status="partial",
        items_checked=3,
        items_passed=2,
        findings=["1 item failed"]
    )

    assert result.status == "partial"
    assert result.items_passed == 2
    print("✓ test_checklist_result_partial_status PASSED")

def test_checklist_result_fail_status():
    """Test ChecklistResult supports fail status."""
    result = ChecklistResult(
        status="fail",
        items_checked=3,
        items_passed=0,
        findings=["All items failed"]
    )

    assert result.status == "fail"
    assert result.items_passed == 0
    print("✓ test_checklist_result_fail_status PASSED")

def test_skill_checklist_verify_exists():
    """Test SkillChecklist class has verify method."""
    checklist = SkillChecklist()
    assert hasattr(checklist, 'verify_target')
    print("✓ test_skill_checklist_verify_exists PASSED")

def test_hook_checklist_verify_exists():
    """Test HookChecklist class has verify method."""
    checklist = HookChecklist()
    assert hasattr(checklist, 'verify_target')
    print("✓ test_hook_checklist_verify_exists PASSED")

def test_feature_checklist_verify_exists():
    """Test FeatureChecklist class has verify method."""
    checklist = FeatureChecklist()
    assert hasattr(checklist, 'verify_target')
    print("✓ test_feature_checklist_verify_exists PASSED")

def test_function_exists():
    """Test run_checklist_verification function exists."""
    assert callable(run_checklist_verification)
    print("✓ test_function_exists PASSED")

def test_invalid_target_type_raises_error():
    """Test invalid target type raises ValueError."""
    try:
        run_checklist_verification("invalid_type", "something")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid target type" in str(e)
        print("✓ test_invalid_target_type_raises_error PASSED")

if __name__ == "__main__":
    print("Running tests...\n")
    test_checklist_result_creation()
    test_checklist_result_partial_status()
    test_checklist_result_fail_status()
    test_skill_checklist_verify_exists()
    test_hook_checklist_verify_exists()
    test_feature_checklist_verify_exists()
    test_function_exists()
    test_invalid_target_type_raises_error()
    print("\n✅ ALL TESTS PASSED")
