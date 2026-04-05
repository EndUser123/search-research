#!/usr/bin/env python3
"""
Unit tests for Tier 0 checklist verification module.

Tests follow TDD approach: define expected behavior first, then implement.
These tests MUST FAIL initially (RED phase).
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

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


# Test fixtures
@pytest.fixture
def sample_skill_checklist_items():
    """Sample skill checklist items for testing."""
    return [
        {"id": "CHK001", "item": "SKILL.md exists", "status": "pass"},
        {"id": "CHK002", "item": "Skill has tests", "status": "fail"},
        {"id": "CHK003", "item": "Skill registered in router", "status": "pass"}
    ]


@pytest.fixture
def sample_hook_checklist_items():
    """Sample hook checklist items for testing."""
    return [
        {"id": "CHK001", "item": "Hook file exists", "status": "pass"},
        {"id": "CHK002", "item": "Hook has type hints", "status": "pass"},
        {"id": "CHK003", "item": "Hook registered", "status": "partial"}
    ]


@pytest.fixture
def sample_feature_checklist_items():
    """Sample feature checklist items for testing."""
    return [
        {"id": "CHK001", "item": "Feature documented in spec.md", "status": "pass"},
        {"id": "CHK002", "item": "Tests exist", "status": "pass"},
        {"id": "CHK003", "item": "Integration verified", "status": "pass"}
    ]


# ChecklistResult Tests
class TestChecklistResult:
    """Test ChecklistResult data structure."""

    def test_checklist_result_creation(self):
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

    def test_checklist_result_partial_status(self):
        """Test ChecklistResult supports partial status."""
        result = ChecklistResult(
            status="partial",
            items_checked=3,
            items_passed=2,
            findings=["1 item failed"]
        )

        assert result.status == "partial"
        assert result.items_passed == 2

    def test_checklist_result_fail_status(self):
        """Test ChecklistResult supports fail status."""
        result = ChecklistResult(
            status="fail",
            items_checked=3,
            items_passed=0,
            findings=["All items failed"]
        )

        assert result.status == "fail"
        assert result.items_passed == 0


# SkillChecklist Tests
class TestSkillChecklist:
    """Test skill-specific checklist verification."""

    def test_skill_checklist_verify_exists(self):
        """Test SkillChecklist class has verify method."""
        checklist = SkillChecklist()
        assert hasattr(checklist, 'verify')

    @patch('tiers.tier0_checklist.Path.exists')
    def test_skill_checklist_passes_all_items(self, mock_exists):
        """Test skill checklist returns pass when all items pass."""
        mock_exists.return_value = True

        checklist = SkillChecklist()
        result = checklist.verify("arch", "P:/.claude/skills/arch")

        assert result.status == "pass"
        assert result.items_checked > 0
        assert result.items_passed == result.items_checked

    @patch('tiers.tier0_checklist.Path.exists')
    def test_skill_checklist_fails_missing_items(self, mock_exists):
        """Test skill checklist returns fail when critical items missing."""
        # Mock SKILL.md exists but tests don't
        def exists_side_effect(path):
            return "SKILL.md" in str(path)

        mock_exists.side_effect = exists_side_effect

        checklist = SkillChecklist()
        result = checklist.verify("arch", "P:/.claude/skills/arch")

        assert result.status in ["fail", "partial"]
        assert result.items_passed < result.items_checked
        assert len(result.findings) > 0


# HookChecklist Tests
class TestHookChecklist:
    """Test hook-specific checklist verification."""

    def test_hook_checklist_verify_exists(self):
        """Test HookChecklist class has verify method."""
        checklist = HookChecklist()
        assert hasattr(checklist, 'verify')

    @patch('tiers.tier0_checklist.Path.exists')
    def test_hook_checklist_passes_all_items(self, mock_exists):
        """Test hook checklist returns pass when all items pass."""
        mock_exists.return_value = True

        checklist = HookChecklist()
        result = checklist.verify("breadcrumb_init", "P:/.claude/hooks")

        assert result.status == "pass"
        assert result.items_checked > 0
        assert result.items_passed == result.items_checked

    @patch('tiers.tier0_checklist.Path.exists')
    def test_hook_checklist_partial_status(self, mock_exists):
        """Test hook checklist returns partial for some failures."""
        # Mock hook file exists but not registered
        def exists_side_effect(path):
            return "breadcrumb_init.py" in str(path)

        mock_exists.side_effect = exists_side_effect

        checklist = HookChecklist()
        result = checklist.verify("breadcrumb_init", "P:/.claude/hooks")

        assert result.status in ["partial", "fail"]
        assert len(result.findings) > 0


# FeatureChecklist Tests
class TestFeatureChecklist:
    """Test feature-specific checklist verification."""

    def test_feature_checklist_verify_exists(self):
        """Test FeatureChecklist class has verify method."""
        checklist = FeatureChecklist()
        assert hasattr(checklist, 'verify')

    @patch('tiers.tier0_checklist.Path.exists')
    def test_feature_checklist_passes_all_items(self, mock_exists):
        """Test feature checklist returns pass when all items pass."""
        mock_exists.return_value = True

        checklist = FeatureChecklist()
        result = checklist.verify("search", "P:/features/search")

        assert result.status == "pass"
        assert result.items_checked > 0
        assert result.items_passed == result.items_checked


# run_checklist_verification Tests
class TestRunChecklistVerification:
    """Test main checklist verification function."""

    def test_function_exists(self):
        """Test run_checklist_verification function exists."""
        assert callable(run_checklist_verification)

    def test_skill_target_uses_skill_checklist(self):
        """Test skill target uses SkillChecklist."""
        with patch('tiers.tier0_checklist.SkillChecklist') as mock_checklist:
            mock_instance = Mock()
            mock_instance.verify.return_value = ChecklistResult(
                status="pass",
                items_checked=3,
                items_passed=3,
                findings=["All checks passed"]
            )
            mock_checklist.return_value = mock_instance

            result = run_checklist_verification("skill", "arch")

            # Verify SkillChecklist was instantiated
            mock_checklist.assert_called_once()
            # Verify verify was called with correct parameters
            mock_instance.verify.assert_called_once()
            assert result.status == "pass"

    def test_hook_target_uses_hook_checklist(self):
        """Test hook target uses HookChecklist."""
        with patch('tiers.tier0_checklist.HookChecklist') as mock_checklist:
            mock_instance = Mock()
            mock_instance.verify.return_value = ChecklistResult(
                status="pass",
                items_checked=3,
                items_passed=3,
                findings=["All checks passed"]
            )
            mock_checklist.return_value = mock_instance

            result = run_checklist_verification("hook", "breadcrumb_init")

            # Verify HookChecklist was instantiated
            mock_checklist.assert_called_once()
            mock_instance.verify.assert_called_once()
            assert result.status == "pass"

    def test_feature_target_uses_feature_checklist(self):
        """Test feature target uses FeatureChecklist."""
        with patch('tiers.tier0_checklist.FeatureChecklist') as mock_checklist:
            mock_instance = Mock()
            mock_instance.verify.return_value = ChecklistResult(
                status="pass",
                items_checked=3,
                items_passed=3,
                findings=["All checks passed"]
            )
            mock_checklist.return_value = mock_instance

            result = run_checklist_verification("feature", "search")

            # Verify FeatureChecklist was instantiated
            mock_checklist.assert_called_once()
            mock_instance.verify.assert_called_once()
            assert result.status == "pass"

    def test_invalid_target_type_raises_error(self):
        """Test invalid target type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid target type"):
            run_checklist_verification("invalid_type", "something")

    def test_returns_checklist_result_dict(self):
        """Test function returns dict with ChecklistResult fields."""
        with patch('tiers.tier0_checklist.SkillChecklist') as mock_checklist:
            mock_instance = Mock()
            mock_instance.verify.return_value = ChecklistResult(
                status="pass",
                items_checked=5,
                items_passed=5,
                findings=["Check 1 passed", "Check 2 passed"]
            )
            mock_checklist.return_value = mock_instance

            result = run_checklist_verification("skill", "arch")

            # Verify result is a dict with expected keys
            assert isinstance(result, dict)
            assert "status" in result
            assert "items_checked" in result
            assert "items_passed" in result
            assert "findings" in result

            # Verify values match
            assert result["status"] == "pass"
            assert result["items_checked"] == 5
            assert result["items_passed"] == 5
            assert len(result["findings"]) == 2

    @patch('tiers.tier0_checklist.SkillChecklist')
    def test_collects_evidence_from_checklist(self, mock_checklist):
        """Test function collects evidence from checklist findings."""
        mock_instance = Mock()
        mock_instance.verify.return_value = ChecklistResult(
            status="partial",
            items_checked=3,
            items_passed=2,
            findings=[
                "SKILL.md exists: PASS",
                "Tests directory: FAIL",
                "Router registration: PASS"
            ]
        )
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("skill", "arch")

        # Verify evidence is collected in findings
        assert len(result["findings"]) == 3
        assert any("PASS" in f for f in result["findings"])
        assert any("FAIL" in f for f in result["findings"])
        assert result["status"] == "partial"


# Integration Tests
class TestChecklistIntegration:
    """Test checklist verification integration with evidence system."""

    @patch('tiers.tier0_checklist.SkillChecklist')
    def test_checklist_result_serializable(self, mock_checklist):
        """Test checklist result can be serialized to JSON."""
        mock_instance = Mock()
        mock_instance.verify.return_value = ChecklistResult(
            status="pass",
            items_checked=3,
            items_passed=3,
            findings=["Check 1", "Check 2", "Check 3"]
        )
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("skill", "arch")

        # Should be JSON serializable
        import json
        try:
            json_str = json.dumps(result)
            assert json_str is not None
        except TypeError as e:
            pytest.fail(f"Result not JSON serializable: {e}")

    @patch('tiers.tier0_checklist.HookChecklist')
    def test_checklist_findings_include_diagnostics(self, mock_checklist):
        """Test checklist findings include diagnostic information."""
        mock_instance = Mock()
        mock_instance.verify.return_value = ChecklistResult(
            status="fail",
            items_checked=3,
            items_passed=1,
            findings=[
                "Hook file exists: PASS",
                "Type hints present: FAIL - Missing type hints on line 42",
                "Router registration: FAIL - Not found in router.py"
            ]
        )
        mock_checklist.return_value = mock_instance

        result = run_checklist_verification("hook", "test_hook")

        # Verify findings include diagnostic details
        assert any("line 42" in f for f in result["findings"])
        assert any("router.py" in f for f in result["findings"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
