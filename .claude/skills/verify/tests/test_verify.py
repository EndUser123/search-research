#!/usr/bin/env python3
"""
Unit tests for /verify skill verification workflow.

Tests follow TDD approach: define expected behavior first, then implement.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))


# Test fixtures
@pytest.fixture
def sample_skill_target():
    """Sample skill target for testing."""
    return {"type": "skill", "name": "arch", "path": "P:/.claude/skills/arch/SKILL.md"}


@pytest.fixture
def sample_hook_target():
    """Sample hook target for testing."""
    return {
        "type": "hook",
        "name": "breadcrumb_init",
        "path": "P:/.claude/hooks/UserPromptSubmit_breadcrumb_init.py",
    }


@pytest.fixture
def sample_code_target():
    """Sample code target for testing."""
    return {
        "type": "code",
        "name": "handoff.py",
        "path": "P:/packages/handoff/src/handoff/__init__.py",
    }


# Target Detection Tests
class TestTargetDetection:
    """Test target type detection from user input."""

    def test_detect_skill_target(self):
        """Test skill target detection."""
        from core.verifier import Verifier

        verifier = Verifier()
        target = verifier.detect_target("skill:arch")

        assert target["type"] == "skill"
        assert target["name"] == "arch"

    def test_detect_hook_target(self):
        """Test hook target detection."""
        from core.verifier import Verifier

        verifier = Verifier()
        target = verifier.detect_target("hook:breadcrumb_init")

        assert target["type"] == "hook"
        assert target["name"] == "breadcrumb_init"

    def test_detect_code_target(self):
        """Test code target detection."""
        from core.verifier import Verifier

        verifier = Verifier()
        target = verifier.detect_target("src/handoff.py")

        assert target["type"] == "code"
        assert target["name"] == "handoff.py"

    def test_auto_detect_skill_from_name(self):
        """Test auto-detect skill from bare name."""
        from core.verifier import Verifier

        verifier = Verifier()
        target = verifier.detect_target("arch")

        # Should detect as skill (exists in skills directory)
        assert target["type"] == "skill"

    def test_invalid_target_format(self):
        """Test invalid target format raises error."""
        from core.verifier import Verifier

        verifier = Verifier()

        with pytest.raises(ValueError, match="Invalid target format"):
            verifier.detect_target("")


# Tier 0: Checklist Verification Tests
class TestTier0ChecklistVerification:
    """Test Tier 0 checklist-based verification (fast-fail layer)."""

    def test_checklist_result_structure(self):
        """Test ChecklistResult has required fields."""
        from tiers.tier0_checklist import ChecklistResult

        # Create sample result
        result = ChecklistResult(
            status="pass",
            items_checked=5,
            items_passed=5,
            findings=["✅ Problem statement documented", "✅ Context complete"],
        )

        # Assert structure
        assert result.status == "pass"
        assert result.items_checked == 5
        assert result.items_passed == 5
        assert len(result.findings) == 2
        assert all(isinstance(f, str) for f in result.findings)

    def test_checklist_result_to_dict(self):
        """Test ChecklistResult converts to dict correctly."""
        from tiers.tier0_checklist import ChecklistResult

        result = ChecklistResult(
            status="partial",
            items_checked=5,
            items_passed=3,
            findings=["✅ Item 1", "❌ Item 2", "⚠️ Item 3"],
        )

        result_dict = result.to_dict()

        assert result_dict["status"] == "partial"
        assert result_dict["items_checked"] == 5
        assert result_dict["items_passed"] == 3
        assert len(result_dict["findings"]) == 3

    def test_verification_checklist_base_class(self):
        """Test VerificationChecklist base class interface."""
        from skills.verification.checklists import VerificationChecklist

        # Verify abstract class cannot be instantiated
        with pytest.raises(TypeError):
            VerificationChecklist()

        # Verify class has abstract method verify_target
        assert hasattr(VerificationChecklist, "verify_target")
        # Verify helper methods exist
        assert hasattr(VerificationChecklist, "_create_result")
        assert hasattr(VerificationChecklist, "_calculate_status")

    def test_skill_checklist_pass_scenario(self):
        """Test skill checklist returns PASS status."""
        from skills.verification.checklists import SkillChecklist

        checklist = SkillChecklist()
        result = checklist.verify_target("P:/.claude/skills/verify")

        # verify/SKILL.md has all required sections
        assert result["status"] in ["pass", "partial"]
        assert result["items_checked"] > 0
        assert isinstance(result["findings"], list)

    def test_hook_checklist_fail_scenario(self):
        """Test hook checklist returns FAIL status for missing hook."""
        from skills.verification.checklists import HookChecklist

        checklist = HookChecklist()
        result = checklist.verify_target("nonexistent_hook.py")

        # Should fail or return partial for nonexistent hook
        assert result["status"] in ["fail", "partial"]
        assert isinstance(result["items_checked"], int)

    def test_checklist_evidence_collection(self):
        """Test checklist verification collects structured evidence."""
        from skills.verification.checklists import SkillChecklist

        checklist = SkillChecklist()
        result = checklist.verify_target("P:/.claude/skills/verify")

        # Evidence should include findings
        assert "findings" in result
        assert isinstance(result["findings"], list)
        # Each finding should be a string
        assert all(isinstance(f, str) for f in result["findings"])

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_tier0_fast_fail_behavior(self, mock_checklist):
        """Test Tier 0 fast-fail prevents execution of Tiers 1-3."""
        from core.verifier import Verifier
        from tiers.tier0_checklist import ChecklistResult

        # Mock Tier 0 failing
        mock_result = ChecklistResult(
            status="fail",
            items_checked=5,
            items_passed=0,
            findings=["❌ Problem statement missing"],
        )
        mock_checklist.return_value = mock_result.to_dict()

        verifier = Verifier()
        report = verifier.verify("skill:incomplete")

        # Overall status should be failed
        assert report["overall_status"] == "failed"
        # Tier 0 should show fail
        assert report["tier0"]["status"] == "fail"
        # Tiers 1-3 should be skipped
        assert report["tier1"]["status"] == "skip"
        assert report["tier2"]["status"] == "skip"
        assert report["tier3"]["status"] == "skip"
        # Skip reason should be documented
        assert "Tier 0 failure" in report["tier1"]["evidence"]


# Tier 1: Component Tests
class TestTier1ComponentTests:
    """Test Tier 1 component test execution."""

    @patch("tiers.tier1_component.subprocess.run")
    def test_run_pytest_success(self, mock_run):
        """Test successful pytest execution."""
        from tiers.tier1_component import Tier1Component

        # Mock successful pytest output
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "tests/test_arch.py::test_arch_activation PASSED\n"
            "tests/test_arch.py::test_arch_intent PASSED\n"
            "2 passed in 0.15s"
        )
        mock_run.return_value = mock_result

        tier1 = Tier1Component()
        result = tier1.run_tests("skill", "arch")

        assert result["status"] == "pass"
        assert "2 passed" in result["evidence"]
        assert result["command"] == "pytest .claude/skills/arch/tests/ -v"

    @patch("tiers.tier1_component.subprocess.run")
    def test_run_pytest_failure(self, mock_run):
        """Test pytest failure detection."""
        from tiers.tier1_component import Tier1Component

        # Mock failed pytest output
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = (
            "tests/test_arch.py::test_arch_activation FAILED\n1 failed, 1 passed in 0.20s"
        )
        mock_run.return_value = mock_result

        tier1 = Tier1Component()
        result = tier1.run_tests("skill", "arch")

        assert result["status"] == "fail"
        assert "1 failed" in result["evidence"]

    def test_no_tests_found(self):
        """Test handling when no tests exist for target."""
        from tiers.tier1_component import Tier1Component

        tier1 = Tier1Component()
        result = tier1.run_tests("skill", "nonexistent")

        # Should not fail, but report no tests
        assert result["status"] in ["skip", "fail"]
        assert "no tests" in result["evidence"].lower()


# Tier 2: Integration Tests
class TestTier2IntegrationCheck:
    """Test Tier 2 integration verification."""

    @patch("tiers.tier2_integration.subprocess.run")
    def test_hook_registration_check(self, mock_run):
        """Test hook registration verification."""
        from tiers.tier2_integration import Tier2Integration

        # Mock successful hook registration check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Hook registered: Stop_router.py"
        mock_run.return_value = mock_result

        tier2 = Tier2Integration()
        result = tier2.check_integration("hook", "breadcrumb_init")

        assert result["status"] == "pass"
        assert "hook file found" in result["evidence"].lower()

    @patch("tiers.tier2_integration.subprocess.run")
    def test_hook_chain_execution(self, mock_run):
        """Test hook chain executes without exceptions."""
        from tiers.tier2_integration import Tier2Integration

        # Mock successful hook chain execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '{"decision": "allow"}'
        mock_run.return_value = mock_result

        tier2 = Tier2Integration()
        result = tier2.check_hook_chain("breadcrumb_init")

        assert result["status"] == "pass"
        assert "allow" in result["evidence"]

    def test_hook_not_registered(self):
        """Test detection of unregistered hook."""
        from tiers.tier2_integration import Tier2Integration

        tier2 = Tier2Integration()
        result = tier2.check_integration("hook", "nonexistent_hook")

        assert result["status"] == "fail"
        assert "hook file not found" in result["evidence"].lower()


# Tier 3: E2E Tests
class TestTier3E2ETest:
    """Test Tier 3 E2E verification."""

    @patch("tiers.tier3_e2e.load_tool_events")
    def test_skill_invocation_evidence(self, mock_load):
        """Test skill invocation evidence detection."""
        from tiers.tier3_e2e import Tier3E2E

        # Mock tool events with skill invocation
        mock_load.return_value = [
            {
                "name": "Skill",
                "command": "arch",
                "timestamp": "2026-03-10T10:00:00",
                "success": True,
            }
        ]

        tier3 = Tier3E2E()
        result = tier3.check_e2e("skill", "arch", session_id="test-session")

        assert result["status"] == "pass"
        assert "skill invocation" in result["evidence"].lower()

    @patch("tiers.tier3_e2e.load_tool_events")
    def test_no_e2e_evidence(self, mock_load):
        """Test failure when no E2E evidence found."""
        from tiers.tier3_e2e import Tier3E2E

        # Mock empty tool events
        mock_load.return_value = []

        tier3 = Tier3E2E()
        result = tier3.check_e2e("skill", "arch", session_id="test-session")

        assert result["status"] == "fail"
        assert "no e2e evidence" in result["evidence"].lower()

    def test_e2e_tracker_integration(self):
        """Test E2E tracker integration - track_workflow can be called without error."""
        from tiers.tier3_e2e import Tier3E2E

        tier3 = Tier3E2E()
        # track_workflow uses dynamic import and gracefully handles missing tracker
        # Just verify it can be called without raising an exception
        tier3.track_workflow(
            workflow_type="skill_invocation",
            target="arch",
            session_id="test-session",
            terminal_id="test-terminal",
            stages=[{"stage": "test", "status": "passed"}],
            overall="success",
        )

        # If we got here without exception, the method works correctly
        # The actual external tracker may or may not be called depending on availability


# Verification Orchestrator Tests
class TestVerificationOrchestrator:
    """Test full verification workflow orchestration."""

    @patch("core.verifier.run_checklist_verification")
    @patch("core.verifier.Tier3E2E")
    @patch("core.verifier.Tier2Integration")
    @patch("core.verifier.Tier1Component")
    def test_full_verification_pass(self, mock_tier1, mock_tier2, mock_tier3, mock_tier0):
        """Test successful 4-tier verification."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }
        # Mock all tiers passing
        mock_tier1.return_value.run_tests.return_value = {
            "status": "pass",
            "evidence": "2 passed",
            "command": "pytest tests/test_arch.py -v",
        }
        mock_tier2.return_value.check_integration.return_value = {
            "status": "pass",
            "evidence": "Hook registered",
        }
        mock_tier3.return_value.check_e2e.return_value = {
            "status": "pass",
            "evidence": "Skill invoked",
        }

        verifier = Verifier()
        report = verifier.verify("skill:arch", session_id="test-session")

        assert report["overall_status"] == "verified"
        assert report["tier0"]["status"] == "pass"
        assert report["tier1"]["status"] == "pass"
        assert report["tier2"]["status"] == "pass"
        assert report["tier3"]["status"] == "pass"

    @patch("core.verifier.run_checklist_verification")
    @patch("core.verifier.Tier3E2E")
    @patch("core.verifier.Tier2Integration")
    @patch("core.verifier.Tier1Component")
    def test_tier1_failure_blocks_verification(
        self, mock_tier1, mock_tier2, mock_tier3, mock_tier0
    ):
        """Test Tier 1 failure prevents verified status."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }
        # Mock Tier 1 failing
        mock_tier1.return_value.run_tests.return_value = {
            "status": "fail",
            "evidence": "1 failed",
            "command": "pytest tests/test_arch.py -v",
        }
        mock_tier2.return_value.check_integration.return_value = {
            "status": "pass",
            "evidence": "Hook registered",
        }
        mock_tier3.return_value.check_e2e.return_value = {
            "status": "pass",
            "evidence": "Skill invoked",
        }

        verifier = Verifier()
        report = verifier.verify("skill:arch", session_id="test-session")

        assert report["overall_status"] == "failed"
        assert report["tier1"]["status"] == "fail"
        # Tier 2 and 3 should still run (evidence gathering)
        assert "tier2" in report
        assert "tier3" in report

    @patch("core.verifier.run_checklist_verification")
    @patch("core.verifier.Tier3E2E")
    @patch("core.verifier.Tier2Integration")
    @patch("core.verifier.Tier1Component")
    def test_tier_mismatch_detected(self, mock_tier1, mock_tier2, mock_tier3, mock_tier0):
        """Test detection of tier mismatches (Tier 1 passes, Tier 2 fails)."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }
        # Mock Tier 1 passing, Tier 2 failing (common integration issue)
        mock_tier1.return_value.run_tests.return_value = {
            "status": "pass",
            "evidence": "2 passed",
            "command": "pytest tests/test_arch.py -v",
        }
        mock_tier2.return_value.check_integration.return_value = {
            "status": "fail",
            "evidence": "Hook not registered in router",
        }
        mock_tier3.return_value.check_e2e.return_value = {
            "status": "skip",
            "evidence": "Skipped due to Tier 2 failure",
        }

        verifier = Verifier()
        report = verifier.verify("skill:arch", session_id="test-session")

        assert report["overall_status"] == "failed"
        assert "tier_mismatch" in report
        assert report["tier_mismatch"] == ["tier1_pass", "tier2_fail"]


# Report Generation Tests
class TestReportGeneration:
    """Test verification report generation."""

    def test_generate_markdown_report(self):
        """Test markdown report generation."""
        from report import VerificationReport

        report_data = {
            "target": "skill:arch",
            "overall_status": "verified",
            "tier1": {
                "status": "pass",
                "evidence": "2 passed",
                "command": "pytest tests/test_arch.py -v",
            },
            "tier2": {"status": "pass", "evidence": "Hook registered"},
            "tier3": {"status": "pass", "evidence": "Skill invoked"},
        }

        generator = VerificationReport()
        markdown = generator.generate_markdown(report_data)

        assert "[VERIFY]" in markdown
        assert "**Overall Status**: ✅ VERIFIED" in markdown
        # Accept either "Tier 1:" or "**TIER1**:" format
        assert "Tier 1: ✅ PASS" in markdown or "**TIER1**: ✅ PASS" in markdown
        assert "Tier 2: ✅ PASS" in markdown or "**TIER2**: ✅ PASS" in markdown
        assert "Tier 3: ✅ PASS" in markdown or "**TIER3**: ✅ PASS" in markdown

    def test_generate_json_report(self):
        """Test JSON report generation."""
        from report import VerificationReport

        report_data = {
            "target": "skill:arch",
            "overall_status": "verified",
            "tier1": {"status": "pass", "evidence": "2 passed"},
            "tier2": {"status": "pass", "evidence": "Hook registered"},
            "tier3": {"status": "pass", "evidence": "Skill invoked"},
        }

        generator = VerificationReport()
        json_output = generator.generate_json(report_data)

        parsed = json.loads(json_output)
        assert parsed["overall_status"] == "verified"
        assert parsed["tier1"]["status"] == "pass"


# Integration Tests (Real Skills/Hooks)
class TestRealSkillVerification:
    """Integration tests against real skills/hooks in codebase."""

    def test_verify_trace_skill(self):
        """Test verification of /trace skill (real target)."""
        from core.verifier import Verifier

        verifier = Verifier()

        # Skip if skill doesn't exist
        trace_skill = Path("P:/.claude/skills/trace/SKILL.md")
        if not trace_skill.exists():
            pytest.skip("trace skill not found")

        # Run Tier 1 only (fast check)
        result = verifier.detect_target("skill:trace")

        assert result["type"] == "skill"
        assert result["name"] == "trace"

    def test_verify_evidence_store_hook(self):
        """Test verification of evidence_store.py (real hook)."""
        from core.verifier import Verifier

        verifier = Verifier()

        # Skip if hook doesn't exist
        hook_file = Path("P:/.claude/hooks/evidence_store.py")
        if not hook_file.exists():
            pytest.skip("evidence_store.py not found")

        # Run Tier 1 only (fast check)
        result = verifier.detect_target("hook:evidence_store")

        assert result["type"] == "hook"
        assert "evidence_store" in result["name"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
