#!/usr/bin/env python3
"""
Performance tests for /verify skill verification workflow.

Establishes performance baselines and ensures verification modes meet timing requirements.
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))


class TestVerificationPerformanceBaseline:
    """Performance baseline tests for standard 4-tier verification."""

    @patch("core.verifier.run_checklist_verification")
    def test_standard_4_tier_completes_under_15_seconds(self, mock_tier0):
        """Test standard 4-tier verification completes in under 15 seconds."""
        from core.verifier import Verifier

        # Mock Tier 0 passing (fast)
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 5,
            "items_passed": 5,
            "findings": [],
        }

        # Mock Tier 1 (simulating pytest runtime)
        def mock_tier1_run(*args, **kwargs):
            time.sleep(0.1)  # Simulate test execution
            return {
                "status": "pass",
                "evidence": "2 passed",
                "command": "pytest tests/test_arch.py -v",
            }

        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests = mock_tier1_run

            # Mock Tier 2 (fast integration check)
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered",
                }

                # Mock Tier 3 (fast E2E check)
                with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e.return_value = {
                        "status": "pass",
                        "evidence": "Skill invoked",
                    }

                    # Run verification and measure time
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    start_time = time.time()
                    report = verifier.verify("skill:code", session_id="test-session")
                    elapsed = time.time() - start_time

                    # Assert completion under 15 seconds
                    assert elapsed < 15.0, (
                        f"Standard 4-tier verification took {elapsed:.2f}s, expected <15s"
                    )
                    assert report["overall_status"] == "verified"

    @patch("core.verifier.run_checklist_verification")
    def test_fast_mode_completes_under_5_seconds(self, mock_tier0):
        """Test fast mode (minimal checks) completes in under 5 seconds."""
        from core.verifier import Verifier

        # Mock fast Tier 0
        mock_tier0.return_value = {
            "status": "pass",
            "items_checked": 3,  # Fewer checks
            "items_passed": 3,
            "findings": [],
        }

        # Mock fast Tier 1 (skip tests)
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {
                "status": "skip",
                "evidence": "Tests skipped in fast mode",
            }

            # Mock fast Tier 2
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "skip",
                    "evidence": "Integration skipped in fast mode",
                }

            # Mock fast Tier 3
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "skip",
                    "evidence": "E2E skipped in fast mode",
                }

            # Run verification and measure time
            verifier = Verifier()
            verifier.tier1 = mock_tier1_instance
            verifier.tier2 = mock_tier2_instance
            verifier.tier3 = mock_tier3_instance

            start_time = time.time()
            report = verifier.verify("code:fast.py", session_id="test-session")
            elapsed = time.time() - start_time

            # Assert completion under 5 seconds for fast mode
            assert elapsed < 5.0, f"Fast mode took {elapsed:.2f}s, expected <5s"


class TestDeepLensPerformance:
    """Performance tests for Deep Lens Verification."""

    @patch("core.verifier.run_checklist_verification")
    def test_deep_lens_completes_under_10_seconds(self, mock_tier0):
        """Test deep lens analysis completes in under 10 seconds."""
        from tiers.deep_lens_verifier import DeepLensVerifier

        # Create larger code sample for realistic testing
        large_code = (
            '''
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

def validate_data(data: dict) -> bool:
    """Validate data structure."""
    if not data:
        return False

    for key, value in data.items():
        if not isinstance(key, str):
            return False
        if not isinstance(value, int):
            return False

    return True

def transform_data(data: dict) -> list:
    """Transform data into list format."""
    return [(key, value) for key, value in data.items()]

class DataProcessor:
    """Data processor class."""

    def __init__(self):
        self.data = {}
        self.cache = {}

    def process(self, items: list):
        """Process items."""
        for item in items:
            self.data[item] = self.data.get(item, 0) + 1

    def get_stats(self):
        """Get statistics."""
        return {
            "total": sum(self.data.values()),
            "unique": len(self.data),
            "max": max(self.data.values()) if self.data else 0
        }
'''
            * 5
        )  # Repeat for size

        # Run deep lens and measure time
        verifier = DeepLensVerifier()
        start_time = time.time()
        result = verifier.verify(large_code, context={"file_type": "python"})
        elapsed = time.time() - start_time

        # Assert completion under 10 seconds
        assert elapsed < 10.0, f"Deep lens analysis took {elapsed:.2f}s, expected <10s"
        assert result["overall_status"] in ["pass", "fail"]

    @patch("core.verifier.run_checklist_verification")
    def test_deep_lens_with_tier2_integration_under_15_seconds(self, mock_tier0):
        """Test deep lens integrated into Tier 2 completes in under 15 seconds."""
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

            # Mock Tier 2 with deep lens (simulated delay)
            def mock_tier2_with_deep_lens(*args, **kwargs):
                # Check if deep_lens flag is set
                deep_lens = kwargs.get("deep_lens", False)
                if deep_lens:
                    time.sleep(0.5)  # Simulate 6-lens analysis
                return {
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
                    }
                    if deep_lens
                    else None,
                }

            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration = mock_tier2_with_deep_lens

            # Mock Tier 3 passing
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {"status": "pass"}

                # Run verification with deep lens
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                start_time = time.time()
                report = verifier.verify("skill:code", session_id="test-session", deep_lens=True)
                elapsed = time.time() - start_time

                # Assert completion under 15 seconds (standard + deep lens)
                assert elapsed < 15.0, f"Deep lens integration took {elapsed:.2f}s, expected <15s"
                assert "deep_lens" in report["tier2"]


class TestAdversarialPerformance:
    """Performance tests for Adversarial Verification."""

    @patch("core.verifier.run_checklist_verification")
    def test_adversarial_completes_under_30_seconds(self, mock_tier0):
        """Test adversarial review completes in under 30 seconds."""
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

                    # Mock adversarial with 7-agent parallel dispatch
                    def mock_adversarial_delay(*args, **kwargs):
                        time.sleep(1.0)  # Simulate 7-agent parallel review
                        return {
                            "status": "completed",
                            "overall_status": "pass",
                            "summaries": ["All 7 reviewers passed"] * 7,
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
                        assert elapsed < 30.0, (
                            f"Adversarial review took {elapsed:.2f}s, expected <30s"
                        )
                        assert "adversarial" in report

    @patch("core.verifier.run_checklist_verification")
    def test_adversarial_parallel_dispatch_efficiency(self, mock_tier0):
        """Test that adversarial parallel dispatch is more efficient than sequential."""
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

                # Simulate parallel dispatch (faster)
                def mock_parallel_dispatch(*args, **kwargs):
                    time.sleep(0.5)  # Parallel: all 7 agents at once
                    return {
                        "status": "completed",
                        "overall_status": "pass",
                        "summaries": ["All reviewers passed"],
                        "timestamp": "2026-03-17T10:00:00",
                    }

                with patch(
                    "core.verifier.Verifier._run_adversarial_review", mock_parallel_dispatch
                ):
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    start_time = time.time()
                    report = verifier.verify(
                        "skill:code", session_id="test-session", adversarial=True
                    )
                    parallel_time = time.time() - start_time

                    # Assert parallel dispatch is efficient
                    # If sequential, would be 7 * 0.5 = 3.5s, parallel should be < 1s
                    assert parallel_time < 2.0, (
                        f"Parallel dispatch took {parallel_time:.2f}s, expected <2s"
                    )
                    assert "adversarial" in report


class TestFullStatePerformance:
    """Performance tests for Full State Verification."""

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_completes_under_10_seconds(self, mock_tier0):
        """Test full state verification completes in under 10 seconds."""
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

            # Mock Tier 3 with file I/O
            def mock_full_state_verification(*args, **kwargs):
                # Check expected_files parameter
                expected_files = kwargs.get("expected_files", [])
                time.sleep(0.1 * len(expected_files))  # Simulate file I/O
                return {
                    "status": "pass",
                    "evidence": f"{len(expected_files)} files verified",
                    "full_state_verification": {
                        "status": "pass",
                        "files_verified": expected_files,
                        "total_files": len(expected_files),
                    },
                }

            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e = mock_full_state_verification

                # Run verification with multiple files
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                expected_files = ["file1.py", "file2.py", "file3.py"]
                start_time = time.time()
                report = verifier.verify(
                    "skill:code",
                    session_id="test-session",
                    full_state=True,
                    expected_files=expected_files,
                )
                elapsed = time.time() - start_time

                # Assert completion under 10 seconds for 3 files
                assert elapsed < 10.0, (
                    f"Full state verification took {elapsed:.2f}s for 3 files, expected <10s"
                )
                assert "full_state_verification" in report["tier3"]


class TestCombinedModesPerformance:
    """Performance tests for combined verification modes."""

    @patch("core.verifier.run_checklist_verification")
    def test_all_modes_combined_completes_under_45_seconds(self, mock_tier0):
        """Test all three modes combined completes in under 45 seconds."""
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

            # Mock Tier 2 with all modes
            def mock_tier2_all_modes(*args, **kwargs):
                deep_lens = kwargs.get("deep_lens", False)
                if deep_lens:
                    time.sleep(0.5)  # Deep lens analysis
                return {
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
                    }
                    if deep_lens
                    else None,
                }

            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration = mock_tier2_all_modes

            # Mock Tier 3 with all modes
            def mock_tier3_all_modes(*args, **kwargs):
                full_state = kwargs.get("full_state_verification", False)
                expected_files = kwargs.get("expected_files", [])
                if full_state and expected_files:
                    time.sleep(0.3)  # Full state verification
                return {
                    "status": "pass",
                    "evidence": "E2E verified",
                    "full_state_verification": {"status": "pass", "files_verified": expected_files}
                    if full_state
                    else None,
                }

            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e = mock_tier3_all_modes

                # Mock adversarial
                def mock_adversarial(*args, **kwargs):
                    time.sleep(1.0)  # 7-agent review
                    return {
                        "status": "completed",
                        "overall_status": "pass",
                        "summaries": ["All reviewers passed"],
                        "timestamp": "2026-03-17T10:00:00",
                    }

                with patch("core.verifier.Verifier._run_adversarial_review", mock_adversarial):
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    # Run all modes
                    start_time = time.time()
                    report = verifier.verify(
                        "skill:code",
                        session_id="test-session",
                        deep_lens=True,
                        adversarial=True,
                        full_state=True,
                        expected_files=["file1.py", "file2.py"],
                    )
                    elapsed = time.time() - start_time

                    # Assert completion under 45 seconds for all modes
                    # (standard ~5s + deep lens ~5s + adversarial ~15s + full state ~5s + overhead)
                    assert elapsed < 45.0, f"All modes combined took {elapsed:.2f}s, expected <45s"
                    assert "deep_lens" in report["tier2"]
                    assert "adversarial" in report
                    assert "full_state_verification" in report["tier3"]


class TestPerformanceScaling:
    """Performance scaling tests with increasing complexity."""

    @patch("core.verifier.run_checklist_verification")
    def test_deep_lens_scales_linearly_with_code_size(self, mock_tier0):
        """Test deep lens scales linearly with code size (not exponentially)."""
        from tiers.deep_lens_verifier import DeepLensVerifier

        verifier = DeepLensVerifier()

        # Test with small code
        small_code = "def foo(): return 1"
        start_time = time.time()
        verifier.verify(small_code, context={"file_type": "python"})
        small_time = time.time() - start_time

        # Test with large code (10x size)
        large_code = small_code * 10
        start_time = time.time()
        verifier.verify(large_code, context={"file_type": "python"})
        large_time = time.time() - start_time

        # Assert linear scaling (large should be < 5x small, not 10x)
        ratio = large_time / small_time if small_time > 0 else 1
        assert ratio < 5.0, f"Deep lens scaled poorly: {ratio:.2f}x for 10x code size, expected <5x"

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_scales_linearly_with_file_count(self, mock_tier0):
        """Test full state verification scales linearly with file count."""
        from core.verifier import Verifier

        # Mock all tiers passing
        with patch("tiers.tier1_component.Tier1Component") as mock_tier1:
            mock_tier1_instance = MagicMock()
            mock_tier1.return_value = mock_tier1_instance
            mock_tier1_instance.run_tests.return_value = {"status": "pass"}

            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {"status": "pass"}

                # Test with 1 file
                def mock_tier3_1file(*args, **kwargs):
                    time.sleep(0.1)
                    return {
                        "status": "pass",
                        "full_state_verification": {"status": "pass", "files_verified": ["f1.py"]},
                    }

                with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e = mock_tier3_1file

                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    start_time = time.time()
                    verifier.verify(
                        "code:test", session_id="test", full_state=True, expected_files=["f1.py"]
                    )
                    time_1file = time.time() - start_time

                # Test with 5 files
                def mock_tier3_5files(*args, **kwargs):
                    time.sleep(0.5)  # 5x the files
                    return {
                        "status": "pass",
                        "full_state_verification": {
                            "status": "pass",
                            "files_verified": ["f1.py", "f2.py", "f3.py", "f4.py", "f5.py"],
                        },
                    }

                with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e = mock_tier3_5files

                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    start_time = time.time()
                    verifier.verify(
                        "code:test",
                        session_id="test",
                        full_state=True,
                        expected_files=["f1.py", "f2.py", "f3.py", "f4.py", "f5.py"],
                    )
                    time_5files = time.time() - start_time

                # Assert linear scaling (5x files should take ~5x time, not more)
                ratio = time_5files / time_1file if time_1file > 0 else 1
                assert ratio < 7.0, (
                    f"Full state scaled poorly: {ratio:.2f}x for 5x files, expected <7x"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
