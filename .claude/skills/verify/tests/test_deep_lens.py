#!/usr/bin/env python3
"""
Integration tests for Deep Lens Verification (6-lens code review).

Tests the complete integration of deep lens analysis into Tier 2 verification.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))


class TestDeepLensIntegration:
    """Integration tests for Deep Lens Verification in 4-tier workflow."""

    @patch("core.verifier.run_checklist_verification")
    def test_deep_lens_flag_runs_6_lens_analysis(self, mock_tier0):
        """Test that deep_lens=True triggers 6-lens code review in Tier 2."""
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
            mock_tier1_instance.run_tests.return_value = {
                "status": "pass",
                "evidence": "2 passed",
                "command": "pytest tests/test_arch.py -v",
            }

            # Mock Tier 2 with deep lens integration
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                # Simulate deep lens results
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered",
                    "deep_lens": {
                        "lenses_run": [
                            "state_edge_case",
                            "identity_invariants",
                            "io",
                            "concurrency",
                            "errors",
                            "tests",
                        ],
                        "findings": [
                            {
                                "lens": "state_edge_case",
                                "severity": "medium",
                                "findings": ["Missing edge case handling for empty input"],
                            }
                        ],
                    },
                }

                # Mock Tier 3 passing
                with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {
                        "status": "pass",
                        "evidence": "Skill invoked",
                    }

                    # Run verification with deep_lens=True
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify(
                        "skill:code", session_id="test-session", deep_lens=True
                    )

                    # Assert deep lens was called
                    mock_tier2_instance.check_integration.assert_called_once()
                    call_kwargs = mock_tier2_instance.check_integration.call_args[1]
                    assert call_kwargs["deep_lens"] is True

                    # Assert deep lens results in report
                    assert "deep_lens" in report["tier2"]
                    assert report["tier2"]["deep_lens"]["lenses_run"] == [
                        "state_edge_case",
                        "identity_invariants",
                        "io",
                        "concurrency",
                        "errors",
                        "tests",
                    ]

    @patch("core.verifier.run_checklist_verification")
    def test_deep_lens_false_skips_analysis(self, mock_tier0):
        """Test that deep_lens=False skips 6-lens analysis."""
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

            # Mock Tier 2 without deep lens
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered",
                    # No deep_lens key
                }

            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Run verification with deep_lens=False
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                report = verifier.verify("skill:code", session_id="test-session", deep_lens=False)

                # Assert deep lens was not called
                mock_tier2_instance.check_integration.assert_called_once()
                call_kwargs = mock_tier2_instance.check_integration.call_args[1]
                assert call_kwargs["deep_lens"] is False

                # Assert deep_lens key not in report or empty
                if "deep_lens" in report["tier2"]:
                    # If present, should be None or empty
                    assert (
                        report["tier2"]["deep_lens"] is None or report["tier2"]["deep_lens"] == {}
                    )

    @patch("tiers.tier0_checklist.run_checklist_verification")
    def test_deep_lens_with_code_target(self, mock_tier0):
        """Test deep lens analysis with code target type."""
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
            mock_tier1_instance.run_tests.return_value = {
                "status": "pass",
                "evidence": "Tests passed",
            }

            # Mock Tier 2 with deep lens for code target
            with patch("core.verifier.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Code analyzed",
                    "deep_lens": {
                        "lenses_run": [
                            "state_edge_case",
                            "identity_invariants",
                            "io",
                            "concurrency",
                            "errors",
                            "tests",
                        ],
                        "total_findings": 8,
                        "by_severity": {"critical": 1, "high": 2, "medium": 3, "low": 2},
                    },
                }

                # Mock Tier 3 passing - nested inside Tier 2 context
                with patch("core.verifier.Tier3E2E") as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                    # Run verification with code target
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify(
                        "code:src/module.py", session_id="test-session", deep_lens=True
                    )

                    # Assert deep lens ran for code target
                    assert report["tier2"]["deep_lens"]["total_findings"] == 8
                    assert report["tier2"]["deep_lens"]["by_severity"]["critical"] == 1

    @patch("core.verifier.run_checklist_verification")
    def test_deep_lens_combined_with_adversarial(self, mock_tier0):
        """Test deep lens can be combined with adversarial mode."""
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
            mock_tier1_instance.run_tests.return_value = {
                "status": "pass",
                "evidence": "Tests passed",
            }

            # Mock Tier 2 with both deep lens and integration check
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Integration verified",
                    "deep_lens": {
                        "lenses_run": [
                            "state_edge_case",
                            "identity_invariants",
                            "io",
                            "concurrency",
                            "errors",
                            "tests",
                        ],
                        "findings": [],
                    },
                }

            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Mock adversarial coordinator
                with patch("core.verifier.Verifier._run_adversarial_review") as mock_adv:
                    mock_adv.return_value = {
                        "status": "completed",
                        "overall_status": "pass",
                        "summaries": ["All reviewers passed"],
                        "timestamp": "2026-03-17T10:00:00",
                    }

                    # Run verification with both modes
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify(
                        "skill:arch", session_id="test-session", deep_lens=True, adversarial=True
                    )

                    # Assert both deep_lens and adversarial results in report
                    assert "deep_lens" in report["tier2"]
                    assert "adversarial" in report
                    assert report["adversarial"]["status"] == "completed"


class TestDeepLensRealCode:
    """Integration tests with real code samples."""

    def test_deep_lens_on_real_skill_file(self):
        """Test deep lens analysis on real verify skill SKILL.md."""
        from tiers.deep_lens_verifier import DeepLensVerifier

        # Read real SKILL.md content
        skill_md_path = skill_root / "SKILL.md"
        if not skill_md_path.exists():
            pytest.skip("SKILL.md not found for testing")

        content = skill_md_path.read_text()

        # Run deep lens analysis
        verifier = DeepLensVerifier()
        result = verifier.verify(content, context={"file_type": "skill"})

        # Assert structured result - verify() returns a dict
        assert "overall_status" in result
        assert result["overall_status"] in ["pass", "fail"]

        # Check each lens ran (6 lenses + overall_status key)
        expected_lenses = [
            "state_edge_case",
            "identity_invariants",
            "io",
            "concurrency",
            "errors",
            "tests",
        ]
        for expected in expected_lenses:
            assert expected in result
            # Each lens result should have lens_name attribute
            assert result[expected].lens_name == expected

    def test_deep_lens_on_python_code(self):
        """Test deep lens analysis on Python code."""
        from tiers.deep_lens_verifier import DeepLensVerifier

        # Sample Python code with various patterns
        code = '''
def process_data(data: list) -> dict:
    """Process data and return results."""
    if not data:
        return {}

    results = {}
    for item in data:
        if item in results:
            results[item] += 1
        else:
            results[item] = 1

    return results
'''

        # Run deep lens analysis
        verifier = DeepLensVerifier()
        result = verifier.verify(code, context={"file_type": "python"})

        # Assert analysis completed - verify() returns a dict
        assert "overall_status" in result
        assert result["overall_status"] in ["pass", "fail"]

        # Check for edge case lens findings (empty list handling)
        assert "state_edge_case" in result
        edge_case_lens = result["state_edge_case"]
        assert edge_case_lens is not None


class TestDeepLensLensSpecific:
    """Integration tests for specific lens behaviors."""

    def test_state_edge_case_lens_detects_missing_checks(self):
        """Test state edge case lens detects missing boundary checks."""
        from tiers.deep_lens_verifier import DeepLensVerifier

        # Code with missing boundary checks
        code = """
def get_item(items: list, index: int):
    return items[index]  # No bounds checking
"""

        verifier = DeepLensVerifier()
        result = verifier.verify(code, context={"file_type": "python"})

        # Find state/edge-case lens result - verify() returns dict
        assert "state_edge_case" in result
        edge_case_lens = result["state_edge_case"]

        assert edge_case_lens is not None
        # Should detect potential issue with list access
        assert edge_case_lens.status in ["partial", "fail"]

    def test_concurrency_lens_detects_race_conditions(self):
        """Test concurrency lens detects potential race conditions."""
        from tiers.deep_lens_verifier import DeepLensVerifier

        # Code with potential race condition
        code = """
import threading

counter = 0

def increment():
    global counter
    counter += 1  # Not thread-safe
"""

        verifier = DeepLensVerifier()
        result = verifier.verify(code, context={"file_type": "python"})

        # Find concurrency lens result - verify() returns dict
        assert "concurrency" in result
        concurrency_lens = result["concurrency"]

        assert concurrency_lens is not None
        # Should flag global variable without lock
        assert concurrency_lens.status in ["partial", "fail"]

    def test_errors_lens_detects_missing_error_handling(self):
        """Test errors lens detects missing error handling."""
        from tiers.deep_lens_verifier import DeepLensVerifier

        # Code without error handling
        code = """
def read_file(path: str) -> str:
    f = open(path)  # No error handling
    return f.read()
"""

        verifier = DeepLensVerifier()
        result = verifier.verify(code, context={"file_type": "python"})

        # Find errors lens result - verify() returns dict
        assert "errors" in result
        errors_lens = result["errors"]

        assert errors_lens is not None
        # Should flag missing try-except
        assert errors_lens.status in ["partial", "fail"]


class TestDeepLensPerformance:
    """Performance tests for deep lens verification."""

    def test_deep_lens_completes_under_10_seconds(self):
        """Test deep lens analysis completes in under 10 seconds."""
        import time

        from tiers.deep_lens_verifier import DeepLensVerifier

        # Larger code sample
        code = (
            """
def function_one(x: int) -> int:
    return x * 2

def function_two(x: int) -> int:
    return x + 10

def function_three(x: int) -> int:
    return x - 5

def main():
    results = []
    for i in range(100):
        results.append(function_one(i))
        results.append(function_two(i))
        results.append(function_three(i))
    return results
"""
            * 10
        )  # Repeat for size

        verifier = DeepLensVerifier()
        start_time = time.time()
        result = verifier.verify(code, context={"file_type": "python"})
        elapsed = time.time() - start_time

        # Assert completion under 10 seconds
        assert elapsed < 10.0, f"Deep lens took {elapsed:.2f}s, expected <10s"
        assert "overall_status" in result
        assert result["overall_status"] in ["pass", "fail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
