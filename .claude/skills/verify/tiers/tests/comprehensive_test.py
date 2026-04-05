#!/usr/bin/env python3
"""Comprehensive test to verify all GREEN phase requirements."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

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


def test_all():
    """Run all comprehensive tests."""
    print("=" * 70)
    print("COMPREHENSIVE GREEN PHASE VERIFICATION")
    print("=" * 70)
    print()

    # Test 1: ChecklistResult creation with all status types
    print("Test 1: ChecklistResult with all status types")
    result_pass = ChecklistResult(status="pass", items_checked=3, items_passed=3, findings=["All pass"])
    result_partial = ChecklistResult(status="partial", items_checked=3, items_passed=2, findings=["Some fail"])
    result_fail = ChecklistResult(status="fail", items_checked=3, items_passed=0, findings=["All fail"])
    assert result_pass.status == "pass"
    assert result_partial.status == "partial"
    assert result_fail.status == "fail"
    print("  ✓ All status types work correctly")

    # Test 2: Checklist classes have verify_target method
    print("\nTest 2: Checklist classes have verify_target method")
    skill_checklist = SkillChecklist()
    hook_checklist = HookChecklist()
    feature_checklist = FeatureChecklist()
    assert hasattr(skill_checklist, 'verify_target')
    assert hasattr(hook_checklist, 'verify_target')
    assert hasattr(feature_checklist, 'verify_target')
    print("  ✓ All checklist classes have verify_target method")

    # Test 3: run_checklist_verification with skill target
    print("\nTest 3: run_checklist_verification with skill target")
    with patch('tiers.tier0_checklist.SkillChecklist') as mock_checklist:
        mock_instance = Mock()
        mock_instance.verify_target.return_value = {
            'status': 'pass',
            'items_checked': 3,
            'items_passed': 3,
            'findings': ['All checks passed']
        }
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("skill", "arch")
        mock_checklist.assert_called_once()
        mock_instance.verify_target.assert_called_once()
        assert result['status'] == 'pass'
        print("  ✓ skill target uses SkillChecklist")

    # Test 4: run_checklist_verification with hook target
    print("\nTest 4: run_checklist_verification with hook target")
    with patch('tiers.tier0_checklist.HookChecklist') as mock_checklist:
        mock_instance = Mock()
        mock_instance.verify_target.return_value = {
            'status': 'pass',
            'items_checked': 3,
            'items_passed': 3,
            'findings': ['All checks passed']
        }
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("hook", "breadcrumb_init")
        mock_checklist.assert_called_once()
        mock_instance.verify_target.assert_called_once()
        assert result['status'] == 'pass'
        print("  ✓ hook target uses HookChecklist")

    # Test 5: run_checklist_verification with feature target
    print("\nTest 5: run_checklist_verification with feature target")
    with patch('tiers.tier0_checklist.FeatureChecklist') as mock_checklist:
        mock_instance = Mock()
        mock_instance.verify_target.return_value = {
            'status': 'pass',
            'items_checked': 3,
            'items_passed': 3,
            'findings': ['All checks passed']
        }
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("feature", "search")
        mock_checklist.assert_called_once()
        mock_instance.verify_target.assert_called_once()
        assert result['status'] == 'pass'
        print("  ✓ feature target uses FeatureChecklist")

    # Test 6: Invalid target type raises ValueError
    print("\nTest 6: Invalid target type raises ValueError")
    try:
        run_checklist_verification("invalid_type", "something")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid target type" in str(e)
        print("  ✓ ValueError raised for invalid target type")

    # Test 7: Returns dict with all required fields
    print("\nTest 7: Returns dict with all required fields")
    with patch('tiers.tier0_checklist.SkillChecklist') as mock_checklist:
        mock_instance = Mock()
        mock_instance.verify_target.return_value = {
            'status': 'pass',
            'items_checked': 5,
            'items_passed': 5,
            'findings': ['Check 1 passed', 'Check 2 passed']
        }
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("skill", "arch")
        assert isinstance(result, dict)
        assert "status" in result
        assert "items_checked" in result
        assert "items_passed" in result
        assert "findings" in result
        assert result["status"] == "pass"
        assert result["items_checked"] == 5
        assert result["items_passed"] == 5
        assert len(result["findings"]) == 2
        print("  ✓ Returns dict with all required fields")

    # Test 8: Evidence collection from findings
    print("\nTest 8: Evidence collection from findings")
    with patch('tiers.tier0_checklist.SkillChecklist') as mock_checklist:
        mock_instance = Mock()
        mock_instance.verify_target.return_value = {
            'status': 'partial',
            'items_checked': 3,
            'items_passed': 2,
            'findings': [
                "SKILL.md exists: PASS",
                "Tests directory: FAIL",
                "Router registration: PASS"
            ]
        }
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("skill", "arch")
        assert len(result["findings"]) == 3
        assert any("PASS" in f for f in result["findings"])
        assert any("FAIL" in f for f in result["findings"])
        assert result["status"] == "partial"
        print("  ✓ Evidence collected from findings")

    # Test 9: JSON serialization
    print("\nTest 9: JSON serialization")
    with patch('tiers.tier0_checklist.SkillChecklist') as mock_checklist:
        mock_instance = Mock()
        mock_instance.verify_target.return_value = {
            'status': 'pass',
            'items_checked': 3,
            'items_passed': 3,
            'findings': ['Check 1', 'Check 2', 'Check 3']
        }
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("skill", "arch")
        import json
        try:
            json_str = json.dumps(result)
            assert json_str is not None
            print("  ✓ Result is JSON serializable")
        except TypeError as e:
            assert False, f"Result not JSON serializable: {e}"

    # Test 10: Diagnostic information in findings
    print("\nTest 10: Diagnostic information in findings")
    with patch('tiers.tier0_checklist.HookChecklist') as mock_checklist:
        mock_instance = Mock()
        mock_instance.verify_target.return_value = {
            'status': 'fail',
            'items_checked': 3,
            'items_passed': 1,
            'findings': [
                "Hook file exists: PASS",
                "Type hints present: FAIL - Missing type hints on line 42",
                "Router registration: FAIL - Not found in router.py"
            ]
        }
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("hook", "test_hook")
        assert any("line 42" in f for f in result["findings"])
        assert any("router.py" in f for f in result["findings"])
        print("  ✓ Findings include diagnostic details")

    print()
    print("=" * 70)
    print("✅ ALL COMPREHENSIVE TESTS PASSED")
    print("=" * 70)
    print()
    print("Summary:")
    print("  - ChecklistResult: All status types working")
    print("  - SkillChecklist: verify_target method exists")
    print("  - HookChecklist: verify_target method exists")
    print("  - FeatureChecklist: verify_target method exists")
    print("  - run_checklist_verification: Correct checklist selection")
    print("  - Error handling: ValueError for invalid types")
    print("  - Return format: Dict with all required fields")
    print("  - Evidence collection: Findings properly collected")
    print("  - Serialization: JSON serializable")
    print("  - Diagnostics: Detailed information in findings")
    print()
    print("GREEN PHASE COMPLETE - Ready for REFACTOR phase")

if __name__ == "__main__":
    test_all()
