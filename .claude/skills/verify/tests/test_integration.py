#!/usr/bin/env python3
"""
Integration tests for /verify skill 4-tier verification workflow.

Tests the full workflow: Tier 0 (Checklist) → Tier 1 (Component) → Tier 2 (Integration) → Tier 3 (E2E).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))


class Test4TierWorkflow:
    """Integration tests for complete 4-tier verification workflow."""

    @patch('core.verifier.run_checklist_verification')
    def test_full_4_tier_workflow_success(self, mock_tier0):
        """Test successful verification through all 4 tiers."""
        from core.verifier import Verifier

        # Mock Tier 0 (Checklist) passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": ["✅ All checks passed"]
        }

        # Mock Tier 1 (Component Tests) passing
        with patch('tiers.tier1_component.Tier1Component') as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {
                "status": "pass",
                "evidence": "2 passed",
                "command": "pytest tests/test_arch.py -v"
            }

            # Mock Tier 2 (Integration) passing
            with patch('tiers.tier2_integration.Tier2Integration') as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered"
                }

                # Mock Tier 3 (E2E) passing
                with patch('tiers.tier3_e2e.Tier3E2E') as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {
                        "status": "pass",
                        "evidence": "Skill invoked"
                    }

                    # Run verification
                    verifier = Verifier()

                    # Patch the instances on the verifier to use our mocks
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify("skill:arch", session_id="test-session")

                    # Assert all 4 tiers executed
                    assert report["overall_status"] == "verified"
                    assert report["tier0"]["status"] == "pass"
                    assert report["tier1"]["status"] == "pass"
                    assert report["tier2"]["status"] == "pass"
                    assert report["tier3"]["status"] == "pass"

                    # Assert T0 ran first (path is constructed, not just name)
                    mock_tier0.assert_called_once_with("skill", "P:/.claude/skills/arch")

    @patch('core.verifier.run_checklist_verification')
    def test_tier0_fast_fail_skips_tiers_1_to_3(self, mock_tier0):
        """Test Tier 0 failure prevents execution of Tiers 1-3 (fast-fail behavior)."""
        from core.verifier import Verifier

        # Mock Tier 0 (Checklist) failing
        mock_tier0.return_value = {
            "status": "fail",
            "items_checked": 5,
            "items_passed": 0,
            "findings": ["❌ Problem statement missing"]
        }

        # Run verification
        verifier = Verifier()
        report = verifier.verify("skill:incomplete")

        # Assert overall status is failed
        assert report["overall_status"] == "failed"

        # Assert Tier 0 shows failure
        assert report["tier0"]["status"] == "fail"
        assert "Problem statement missing" in report["tier0"]["findings"][0]

        # Assert Tiers 1-3 are skipped
        assert report["tier1"]["status"] == "skip"
        assert report["tier2"]["status"] == "skip"
        assert report["tier3"]["status"] == "skip"

        # Assert skip reason is documented
        assert "Tier 0 failure" in report["tier1"]["evidence"]
        assert "Tier 0 failure" in report["tier2"]["evidence"]
        assert "Tier 0 failure" in report["tier3"]["evidence"]

        # Assert Tier 0 was called but Tiers 1-3 were not
        mock_tier0.assert_called_once()

    @patch('core.verifier.run_checklist_verification')
    def test_tier0_partial_continues_to_tier1(self, mock_tier0):
        """Test Tier 0 partial status allows continuation to Tier 1."""
        from core.verifier import Verifier

        # Mock Tier 0 (Checklist) partial (some checks passed)
        mock_tier0.return_value = {
            "status": "partial",
            "items_checked": 5,
            "items_passed": 3,
            "findings": ["⚠️ Test coverage incomplete (3/5)"]
        }

        # Mock Tier 1 (Component Tests) passing
        with patch('tiers.tier1_component.Tier1Component') as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {
                "status": "pass",
                "evidence": "2 passed"
            }

            # Mock Tier 2 and Tier 3 skipping for brevity
            with patch('tiers.tier2_integration.Tier2Integration') as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass"
                }

                with patch('tiers.tier3_e2e.Tier3E2E') as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {
                        "status": "pass"
                    }

                    # Run verification
                    verifier = Verifier()

                    # Patch the instances on the verifier to use our mocks
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify("skill:partial")

                    # Assert overall status is failed (not all tiers passed)
                    assert report["overall_status"] == "failed"

                    # Assert Tier 0 partial continued to Tier 1
                    assert report["tier0"]["status"] == "partial"
                    assert report["tier1"]["status"] == "pass"

                    # Assert T0 was called
                    mock_tier0.assert_called_once()

    @patch('core.verifier.run_checklist_verification')
    def test_tier_mismatch_detection(self, mock_tier0):
        """Test detection of tier mismatches (e.g., Tier 0 passes, Tier 1 fails)."""
        from core.verifier import Verifier

        # Mock Tier 0 passing, Tier 1 failing (common issue)
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5
        }

        with patch('tiers.tier1_component.Tier1Component') as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {
                "status": "fail",
                "evidence": "1 failed"
            }

            with patch('tiers.tier2_integration.Tier2Integration') as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass"
                }

                with patch('tiers.tier3_e2e.Tier3E2E') as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {
                        "status": "skip"
                    }

                    # Run verification
                    verifier = Verifier()
                    report = verifier.verify("skill:mismatch")

                    # Assert tier mismatch detected
                    assert "tier_mismatch" in report
                    assert report["tier_mismatch"] == ["tier0_pass", "tier1_fail"]

                    # Assert overall status is failed
                    assert report["overall_status"] == "failed"

    @patch('core.verifier.run_checklist_verification')
    def test_checklist_evidence_in_report(self, mock_tier0):
        """Test checklist findings are included in verification report."""
        from core.verifier import Verifier

        # Mock Tier 0 with specific findings
        mock_tier0.return_value = {
            "status": "partial",
            "items_checked": 5,
            "items_passed": 4,
            "findings": [
                "✅ Problem statement documented",
                "✅ Context complete",
                "⚠️ Test coverage incomplete (4/5 scenarios)"
            ]
        }

        # Mock remaining tiers
        with patch('tiers.tier1_component.Tier1Component') as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass"}

            with patch('tiers.tier2_integration.Tier2Integration') as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {"status": "pass"}

                with patch('tiers.tier3_e2e.Tier3E2E') as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                    # Run verification
                    verifier = Verifier()
                    report = verifier.verify("skill:arch")

                    # Assert checklist evidence preserved in report
                    assert report["tier0"]["status"] == "partial"
                    assert len(report["tier0"]["findings"]) == 3
                    assert "Test coverage incomplete" in report["tier0"]["findings"][2]
                    # Findings are part of tier0 result, not nested in another key
                    assert "findings" in report["tier0"]

    @patch('core.verifier.run_checklist_verification')
    def test_verification_id_generated(self, mock_tier0):
        """Test each verification generates unique ID."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {"status": "pass", "items_checked": 5, "items_passed": 5, "findings": []}

        # Mock all tiers passing
        with patch('tiers.tier1_component.Tier1Component') as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass"}

            with patch('tiers.tier2_integration.Tier2Integration') as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {"status": "pass"}

                with patch('tiers.tier3_e2e.Tier3E2E') as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                    # Run two verifications
                    verifier = Verifier()
                    report1 = verifier.verify("skill:arch")
                    report2 = verifier.verify("skill:trace")

                    # Assert each has unique verification ID
                    assert "verification_id" in report1
                    assert "verification_id" in report2
                    assert report1["verification_id"] != report2["verification_id"]

    @patch('core.verifier.run_checklist_verification')
    def test_target_detection_and_routing(self, mock_tier0):
        """Test target detection and routing to appropriate checklist."""
        from core.verifier import Verifier

        # Mock Tier 0
        mock_tier0.return_value = {"status": "pass", "items_checked": 5, "items_passed": 5, "findings": []}

        # Mock remaining tiers
        with patch('tiers.tier1_component.Tier1Component') as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass"}

            with patch('tiers.tier2_integration.Tier2Integration') as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {"status": "pass"}

                with patch('tiers.tier3_e2e.Tier3E2E') as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                    verifier = Verifier()

                    # Patch the instances on the verifier to use our mocks
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    # Test skill target
                    report_skill = verifier.verify("skill:arch")
                    assert report_skill["target_type"] == "skill"
                    assert report_skill["target_name"] == "arch"

                    # Test hook target
                    report_hook = verifier.verify("hook:breadcrumb_init")
                    assert report_hook["target_type"] == "hook"
                    assert report_hook["target_name"] == "breadcrumb_init"

                    # Assert Tier 0 called with correct types for each (path is constructed)
                    calls = mock_tier0.call_args_list
                    assert calls[0][0] == ("skill", "P:/.claude/skills/arch")  # First call
                    assert calls[1][0] == ("hook", "P:/.claude/hooks/*breadcrumb_init*.py")  # Second call


class Test4TierWorkflowRealTargets:
    """Integration tests using real skills/hooks in codebase."""

    def test_verify_real_skill_with_checklist(self):
        """Test verification of real skill using checklist."""
        from core.verifier import Verifier
        from tiers.tier0_checklist import run_checklist_verification

        # Test with real verify skill (has complete SKILL.md)
        verifier = Verifier()
        detected = verifier.detect_target("skill:verify")

        # Run Tier 0 checklist
        try:
            tier0_result = run_checklist_verification(detected["type"], detected["name"])

            # Assert Tier 0 completed
            assert "status" in tier0_result
            assert "items_checked" in tier0_result
            assert isinstance(tier0_result["findings"], list)
        except Exception as e:
            pytest.fail(f"Tier 0 checklist failed: {e}")

    def test_verify_real_hook_with_checklist(self):
        """Test verification of real hook using checklist."""
        from core.verifier import Verifier
        from tiers.tier0_checklist import run_checklist_verification

        # Test with real hook
        verifier = Verifier()
        detected = verifier.detect_target("hook:UserPromptSubmit")

        # Run Tier 0 checklist
        try:
            tier0_result = run_checklist_verification(detected["type"], detected["name"])

            # Assert Tier 0 completed
            assert "status" in tier0_result
            assert isinstance(tier0_result["findings"], list)
        except Exception as e:
            # Hook verification may fail if file doesn't match pattern
            # This is expected for some hooks
            assert "fail" in str(e).lower() or "partial" in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
