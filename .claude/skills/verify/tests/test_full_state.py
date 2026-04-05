#!/usr/bin/env python3
"""
Integration tests for Full State Verification (Source→Logic→Read protocol).

Tests the complete integration of full state verification into Tier 3 workflow.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))


class TestFullStateIntegration:
    """Integration tests for Full State Verification in 4-tier workflow."""

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_flag_runs_verification(self, mock_tier0):
        """Test that full_state=True triggers state verification in Tier 3."""
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

            # Mock Tier 2 passing
            with patch("tiers.tier2_integration.Tier2Integration") as mock_tier2:
                mock_tier2_instance = MagicMock()
                mock_tier2.return_value = mock_tier2_instance
                mock_tier2_instance.check_integration.return_value = {
                    "status": "pass",
                    "evidence": "Hook registered",
                }

            # Mock Tier 3 with full state verification
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                # Simulate full state results
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "pass",
                    "evidence": "Skill invoked",
                    "full_state_verification": {
                        "status": "pass",
                        "files_verified": ["src/module.py", "tests/test_module.py"],
                        "source_definition": {
                            "type": "file",
                            "path": "src/module.py",
                            "exists": True,
                        },
                        "logic_verification": {"operation": "write", "verified": True},
                        "state_comparison": {
                            "expected": {"content": "test content"},
                            "actual": {"content": "test content"},
                            "match": True,
                        },
                    },
                }

                # Run verification with full_state=True
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                report = verifier.verify(
                    "skill:code",
                    session_id="test-session",
                    full_state=True,
                    expected_files=["src/module.py", "tests/test_module.py"],
                )

                # Assert full state was called with expected files
                mock_tier3_instance.check_e2e.assert_called_once()
                call_kwargs = mock_tier3_instance.check_e2e.call_args[1]
                assert call_kwargs["full_state_verification"] is True
                assert call_kwargs["expected_files"] == ["src/module.py", "tests/test_module.py"]

                # Assert full state results in report
                assert "full_state_verification" in report["tier3"]
                assert report["tier3"]["full_state_verification"]["status"] == "pass"
                assert report["tier3"]["full_state_verification"]["files_verified"] == [
                    "src/module.py",
                    "tests/test_module.py",
                ]

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_false_skips_verification(self, mock_tier0):
        """Test that full_state=False skips state verification."""
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

            # Mock Tier 3 without full state
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "pass",
                    "evidence": "Skill invoked",
                    # No full_state_verification key
                }

                # Run verification with full_state=False
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                report = verifier.verify("skill:code", session_id="test-session", full_state=False)

                # Assert full state was not called
                mock_tier3_instance.check_e2e.assert_called_once()
                call_kwargs = mock_tier3_instance.check_e2e.call_args[1]
                assert call_kwargs["full_state_verification"] is False

                # Assert full_state_verification key not in report or None
                if "full_state_verification" in report["tier3"]:
                    assert report["tier3"]["full_state_verification"] is None

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_detects_mismatch(self, mock_tier0):
        """Test full state verification detects state mismatches."""
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

            # Mock Tier 3 with state mismatch
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "fail",
                    "evidence": "State mismatch detected",
                    "full_state_verification": {
                        "status": "fail",
                        "files_verified": ["src/module.py"],
                        "source_definition": {
                            "type": "file",
                            "path": "src/module.py",
                            "exists": True,
                            "expected_size": 1024,
                        },
                        "logic_verification": {"operation": "write", "verified": True},
                        "state_comparison": {
                            "expected": {"size": 1024},
                            "actual": {"size": 512},
                            "match": False,
                            "differences": ["File size mismatch: expected 1024, got 512"],
                        },
                    },
                }

                # Run verification with full_state=True
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                report = verifier.verify(
                    "skill:code",
                    session_id="test-session",
                    full_state=True,
                    expected_files=["src/module.py"],
                )

                # Assert state mismatch detected
                assert report["tier3"]["status"] == "fail"
                assert report["tier3"]["full_state_verification"]["status"] == "fail"
                assert (
                    "File size mismatch"
                    in report["tier3"]["full_state_verification"]["state_comparison"][
                        "differences"
                    ][0]
                )

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_with_multiple_files(self, mock_tier0):
        """Test full state verification with multiple expected files."""
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

            # Mock Tier 3 with multiple files
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "pass",
                    "evidence": "All files verified",
                    "full_state_verification": {
                        "status": "pass",
                        "files_verified": ["src/module.py", "tests/test_module.py", "README.md"],
                        "total_files": 3,
                        "all_passed": True,
                    },
                }

                # Run verification with multiple expected files
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                report = verifier.verify(
                    "skill:code",
                    session_id="test-session",
                    full_state=True,
                    expected_files=["src/module.py", "tests/test_module.py", "README.md"],
                )

                # Assert all files verified
                assert report["tier3"]["full_state_verification"]["total_files"] == 3
                assert report["tier3"]["full_state_verification"]["all_passed"] is True
                assert len(report["tier3"]["full_state_verification"]["files_verified"]) == 3


class TestFullStateRealFiles:
    """Integration tests with real file verification."""

    def test_full_state_verify_file_exists(self):
        """Test full state verification on real file exists."""
        from tiers.full_state_verifier import FullStateVerifier

        # Use test file that should exist
        test_file = skill_root / "SKILL.md"

        if not test_file.exists():
            pytest.skip("SKILL.md not found for testing")

        # Create verifier and check file exists
        verifier = FullStateVerifier()
        result = verifier.verify_file_exists(str(test_file))

        # Assert result
        assert result.state_match is True
        assert result.source_definition.exists is True

    def test_full_state_verify_file_content(self):
        """Test full state verification on real file content."""
        import os

        # Create temporary test file
        import tempfile

        from tiers.full_state_verifier import FullStateVerifier

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("Test content for verification")
            temp_path = f.name

        try:
            # Verify file content
            verifier = FullStateVerifier()
            result = verifier.verify_file_content(
                temp_path, expected_content="Test content for verification"
            )

            # Assert result
            assert result.state_match is True
            assert result.source_definition.exists is True
        finally:
            # Cleanup
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_full_state_module_level_functions(self):
        """Test module-level convenience functions."""
        import os

        # Test module-level function
        import tempfile

        from tiers.full_state_verifier import verify_file_written

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("# Test Python file\nprint('Hello, World!')\n")
            temp_path = f.name

        try:
            # Use module-level function
            result = verify_file_written(temp_path)

            # Assert result structure
            assert hasattr(result, "status")
            assert hasattr(result, "source_definition")
            assert hasattr(result, "state_match")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestFullStateErrorHandling:
    """Error handling tests for full state verification."""

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_handles_missing_files(self, mock_tier0):
        """Test full state verification handles missing expected files."""
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

            # Mock Tier 3 with missing file
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "fail",
                    "evidence": "File not found",
                    "full_state_verification": {
                        "status": "fail",
                        "error": "Expected file does not exist: nonexistent.py",
                        "source_definition": {
                            "type": "file",
                            "path": "nonexistent.py",
                            "exists": False,
                        },
                    },
                }

                # Run verification
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                report = verifier.verify(
                    "skill:code",
                    session_id="test-session",
                    full_state=True,
                    expected_files=["nonexistent.py"],
                )

                # Assert error handled
                assert report["tier3"]["status"] == "fail"
                assert report["tier3"]["full_state_verification"]["status"] == "fail"
                assert "does not exist" in report["tier3"]["full_state_verification"]["error"]


class TestFullStatePerformance:
    """Performance tests for full state verification."""

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_completes_under_10_seconds(self, mock_tier0):
        """Test full state verification completes in under 10 seconds."""
        import time

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

                # Mock Tier 3 with file I/O delay
                def mock_full_state_delay(*args, **kwargs):
                    time.sleep(0.5)  # Simulate file I/O
                    return {
                        "status": "pass",
                        "evidence": "Files verified",
                        "full_state_verification": {
                            "status": "pass",
                            "files_verified": ["file1.py", "file2.py", "file3.py"],
                        },
                    }

                with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                    mock_tier3_instance = MagicMock()
                    mock_tier3.return_value = mock_tier3_instance
                    mock_tier3_instance.check_e2e = mock_full_state_delay

                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    start_time = time.time()
                    report = verifier.verify(
                        "skill:code",
                        session_id="test-session",
                        full_state=True,
                        expected_files=["file1.py", "file2.py", "file3.py"],
                    )
                    elapsed = time.time() - start_time

                    # Assert completion under 10 seconds
                    assert elapsed < 10.0, (
                        f"Full state verification took {elapsed:.2f}s, expected <10s"
                    )
                    assert "full_state_verification" in report["tier3"]


class TestFullStateCombinedModes:
    """Integration tests for full state combined with other modes."""

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_with_deep_lens(self, mock_tier0):
        """Test full state verification can be combined with deep lens."""
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

            # Mock Tier 2 with deep lens
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

            # Mock Tier 3 with full state
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "pass",
                    "evidence": "Files verified",
                    "full_state_verification": {
                        "status": "pass",
                        "files_verified": ["src/module.py"],
                    },
                }

                # Run verification with both modes
                verifier = Verifier()
                verifier.tier1 = mock_tier1_instance
                verifier.tier2 = mock_tier2_instance
                verifier.tier3 = mock_tier3_instance

                report = verifier.verify(
                    "skill:code",
                    session_id="test-session",
                    deep_lens=True,
                    full_state=True,
                    expected_files=["src/module.py"],
                )

                # Assert both modes results in report
                assert "deep_lens" in report["tier2"]
                assert "full_state_verification" in report["tier3"]

    @patch("core.verifier.run_checklist_verification")
    def test_full_state_with_adversarial(self, mock_tier0):
        """Test full state verification can be combined with adversarial."""
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

            # Mock Tier 3 with full state
            with patch("tiers.tier3_e2e.Tier3E2E") as mock_tier3:
                mock_tier3_instance = MagicMock()
                mock_tier3.return_value = mock_tier3_instance
                mock_tier3_instance.check_e2e.return_value = {
                    "status": "pass",
                    "evidence": "Files verified",
                    "full_state_verification": {
                        "status": "pass",
                        "files_verified": ["src/module.py"],
                    },
                }

                # Mock adversarial
                with patch("core.verifier.Verifier._run_adversarial_review") as mock_adv:
                    mock_adv.return_value = {
                        "status": "completed",
                        "overall_status": "pass",
                        "summaries": ["All reviewers passed"],
                    }

                    # Run verification with both modes
                    verifier = Verifier()
                    verifier.tier1 = mock_tier1_instance
                    verifier.tier2 = mock_tier2_instance
                    verifier.tier3 = mock_tier3_instance

                    report = verifier.verify(
                        "skill:code",
                        session_id="test-session",
                        adversarial=True,
                        full_state=True,
                        expected_files=["src/module.py"],
                    )

                    # Assert both modes results in report
                    assert "adversarial" in report
                    assert "full_state_verification" in report["tier3"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
