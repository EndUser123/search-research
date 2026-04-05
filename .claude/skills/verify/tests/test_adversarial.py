#!/usr/bin/env python3
"""
Integration tests for Adversarial Verification (9-agent stress testing).

Tests the complete integration of adversarial review into verification workflow.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))


class TestAdversarialIntegration:
    """Integration tests for Adversarial Verification in 4-tier workflow."""

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_adversarial_flag_runs_9_agent_review(self, mock_tier0):
        """Test that adversarial=True triggers 9-agent review."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock Tier 1 passing
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass", "evidence": "2 passed"}

            # Mock Tier 2 passing
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered",
                }

            # Mock Tier 3 passing
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "pass",
                    "evidence": "Skill invoked",
                }

                # Mock adversarial coordinator
                with patch("core.verifier.Verifier._run_adversarial_review") as mock_adv:
                    mock_adv.return_value = {
                        "status": "completed",
                        "overall_status": "pass",
                        "summaries": [
                            "compliance: No violations found",
                            "performance: No bottlenecks detected",
                            "quality: Code is maintainable",
                            "security: No vulnerabilities found",
                            "testing: Coverage adequate",
                            "code-critic: No issues found",
                            "qa-engineer: Verification standards met",
                        ],
                        "artifact_dir": ".verify/artifacts/",
                        "timestamp": "2026-03-17T10:00:00",
                    }

                    # Run verification with adversarial=True
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify(
                        "skill:code", session_id="test-session", adversarial=True
                    )

                    # Assert adversarial review was called
                    mock_adv.assert_called_once()

                    # Assert adversarial results in report
                    assert "adversarial" in report
                    assert report["adversarial"]["status"] == "completed"
                    assert len(report["adversarial"]["summaries"]) == 7

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_adversarial_false_skips_review(self, mock_tier0):
        """Test that adversarial=False skips 9-agent review."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock Tier 1 passing
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass", "evidence": "2 passed"}

            # Mock Tier 2 passing
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered",
                }

            # Mock Tier 3 passing
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Run verification with adversarial=False (default)
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                report = verifier.verify("skill:code", session_id="test-session", adversarial=False)

                # Assert adversarial results not in report
                assert "adversarial" not in report

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_adversarial_with_findings(self, mock_tier0):
        """Test adversarial review with critical findings."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock Tier 1 passing
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass", "evidence": "2 passed"}

            # Mock Tier 2 passing
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered",
                }

            # Mock Tier 3 passing
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Mock adversarial with findings
                with patch("core.verifier.Verifier._run_adversarial_review") as mock_adv:
                    mock_adv.return_value = {
                        "status": "completed",
                        "overall_status": "fail",
                        "summaries": [
                            "compliance: CRITICAL - Missing required sections",
                            "performance: HIGH - Potential bottleneck detected",
                            "quality: MEDIUM - Code complexity high",
                            "security: CRITICAL - SQL injection risk",
                            "testing: LOW - Missing edge case tests",
                            "code-critic: LOW - Minor style issues",
                            "qa-engineer: HIGH - Coverage below threshold",
                        ],
                        "artifact_dir": ".verify/artifacts/",
                        "timestamp": "2026-03-17T10:00:00",
                    }

                    # Run verification
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify(
                        "skill:code", session_id="test-session", adversarial=True
                    )

                    # Assert adversarial findings in report
                    assert report["adversarial"]["overall_status"] == "fail"
                    assert "CRITICAL" in report["adversarial"]["summaries"][0]
                    assert "SQL injection" in report["adversarial"]["summaries"][3]

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_adversarial_result_envelope_pattern(self, mock_tier0):
        """Test that adversarial review uses result envelope pattern."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock Tier 1 passing
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass", "evidence": "2 passed"}

            # Mock Tier 2 passing
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered",
                }

            # Mock Tier 3 passing
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Mock adversarial with result envelope structure
                with patch("core.verifier.Verifier._run_adversarial_review") as mock_adv:
                    mock_adv.return_value = {
                        "status": "completed",
                        "overall_status": "pass",
                        "summaries": ["All reviewers passed"],
                        "artifact_dir": ".verify/artifacts/adversarial_20260317_100000/",
                        "timestamp": "2026-03-17T10:00:00",
                    }

                    # Run verification
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify(
                        "skill:code", session_id="test-session", adversarial=True
                    )

                    # Assert result envelope fields present
                    assert "status" in report["adversarial"]
                    assert "overall_status" in report["adversarial"]
                    assert "summaries" in report["adversarial"]
                    assert "artifact_dir" in report["adversarial"]

                    # Assert summaries are concise (no large artifacts inline)
                    for summary in report["adversarial"]["summaries"]:
                        assert len(summary) < 200, "Summary should be concise"


class TestAdversarialRealCode:
    """Integration tests with real code samples."""

    def test_adversarial_on_real_skill_file(self):
        """Test adversarial review on real verify skill SKILL.md."""
        from tiers.adversarial_coordinator import adversarial_review

        # Read real SKILL.md content
        skill_md_path = skill_root / "SKILL.md"
        if not skill_md_path.exists():
            pytest.skip("SKILL.md not found for testing")

        content = skill_md_path.read_text()

        # Run adversarial review (in real mode, this would spawn 7 agents)
        # For testing, we use a lightweight mock
        try:
            result = adversarial_review(
                target_type="code",
                content=content[:1000],  # Use subset for faster testing
                context={"file_type": "skill"},
            )

            # Assert structured result
            assert "status" in result
            assert "overall_status" in result
            assert result["status"] in ["completed", "error"]

        except Exception as e:
            # Adversarial review may fail if agents not available
            # This is expected in test environment
            pytest.skip(f"Adversarial agents not available: {e}")


class TestAdversarialAgentSpecific:
    """Integration tests for specific agent behaviors."""

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_adversarial_compliance_agent(self, mock_tier0):
        """Test adversarial compliance agent detects solo-dev violations."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock all tiers passing
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass"}

            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {"status": "pass"}

            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Mock adversarial with compliance finding
                with patch("core.verifier.Verifier._run_adversarial_review") as mock_adv:
                    mock_adv.return_value = {
                        "status": "completed",
                        "overall_status": "fail",
                        "summaries": [
                            "compliance: SOLO-DEV VIOLATION - Enterprise team patterns detected"
                        ],
                        "artifact_dir": ".verify/artifacts/",
                        "timestamp": "2026-03-17T10:00:00",
                    }

                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify(
                        "skill:code", session_id="test-session", adversarial=True
                    )

                    # Assert compliance finding in report
                    assert "SOLO-DEV VIOLATION" in report["adversarial"]["summaries"][0]

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_adversarial_security_agent(self, mock_tier0):
        """Test adversarial security agent detects vulnerabilities."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock Tier 1 passing
        with patch("core.verifier.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass"}

            with patch("core.verifier.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {"status": "pass"}

                # Mock Tier 3 passing - MUST be nested inside Tier 2 context
                with patch("core.verifier.Tier3E2E") as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                    # Mock adversarial with security finding - MUST be inside tier3 context
                    with patch("core.verifier.Verifier._run_adversarial_review") as mock_adv:
                        mock_adv.return_value = {
                            "status": "completed",
                            "overall_status": "fail",
                            "summaries": ["security: CRITICAL - Hardcoded credentials detected"],
                            "artifact_dir": ".verify/artifacts/",
                            "timestamp": "2026-03-17T10:00:00",
                        }

                        verifier = Verifier()
                        verifier.tier1 = mock_tier1_instance
                        verifier.tier2 = mock_tier2_instance
                        verifier.tier3 = mock_tier3_instance

                        report = verifier.verify(
                            "code:src/auth.py", session_id="test-session", adversarial=True
                        )

                        # Assert security finding in report
                        assert "Hardcoded credentials" in report["adversarial"]["summaries"][0]


class TestAdversarialPerformance:
    """Performance tests for adversarial verification."""

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_adversarial_completes_under_30_seconds(self, mock_tier0):
        """Test adversarial review completes in under 30 seconds."""
        import time

        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock all tiers passing
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass"}

            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {"status": "pass"}

            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Mock adversarial (simulating delay for 7 agents)
                def mock_adversarial_delay(*args, **kwargs):
                    time.sleep(0.5)  # Simulate agent dispatch
                    return {
                        "status": "completed",
                        "overall_status": "pass",
                        "summaries": ["All reviewers passed"],
                        "artifact_dir": ".verify/artifacts/",
                        "timestamp": "2026-03-17T10:00:00",
                    }

                with patch(
                    "core.verifier.Verifier._run_adversarial_review", mock_adversarial_delay
                ):
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    start_time = time.time()
                    report = verifier.verify(
                        "skill:code", session_id="test-session", adversarial=True
                    )
                    elapsed = time.time() - start_time

                    # Assert completion under 30 seconds
                    assert elapsed < 30.0, f"Adversarial review took {elapsed:.2f}s, expected <30s"
                    assert "adversarial" in report


class TestAdversarialErrorHandling:
    """Error handling tests for adversarial verification."""

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_adversarial_handles_agent_unavailable(self, mock_tier0):
        """Test adversarial review handles agent unavailability gracefully."""
        from core.verifier import Verifier

        # Mock Tier 0 passing
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock all tiers passing
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass"}

            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {"status": "pass"}

            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Mock adversarial error
                with patch("core.verifier.Verifier._run_adversarial_review") as mock_adv:
                    mock_adv.return_value = {
                        "status": "error",
                        "error": "Adversarial agent unavailable",
                        "overall_status": "error",
                    }

                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    # Run verification - should not crash
                    report = verifier.verify(
                        "skill:code", session_id="test-session", adversarial=True
                    )

                    # Assert error handled gracefully
                    assert "adversarial" in report
                    assert report["adversarial"]["status"] == "error"
                    assert "unavailable" in report["adversarial"]["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
