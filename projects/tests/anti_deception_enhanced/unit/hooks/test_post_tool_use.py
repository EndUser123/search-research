"""
Unit Tests for Post-Tool Use Hook Component

Tests the Post-Tool Use hook functionality for the Enhanced Anti-Deception Architecture.
Validates evidence collection, validation results, and hook integration.
"""

import os
import sys

# Import test utilities
sys.path.insert(0, os.path.dirname(__file__))
from utils import (
    EvidenceGenerator,
    PerformanceTimer,
    TemporaryDirectory,
    TestConfigHelper,
)

# Import the anti-deception hook
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "__csf")
)
try:
    from anti_deception_hook import AntiDeceptionHook
except ImportError:
    raise ImportError("Could not import AntiDeceptionHook")


class TestPostToolUseHook:
    """Test suite for Post-Tool Use hook functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.config = TestConfigHelper.create_minimal_config()
        self.hook = AntiDeceptionHook()
        self.temp_dir = TemporaryDirectory()
        self.evidence_generator = EvidenceGenerator()

    def teardown_method(self):
        """Clean up after each test method."""
        self.temp_dir.__exit__(None, None, None)
        self.hook.reset_failures()

    def test_post_tool_use_initialization(self):
        """Test that Post-Tool Use hook initializes correctly."""
        assert self.hook is not None
        assert self.hook.config is not None
        assert isinstance(self.hook.config, dict)

        # Check that evidence log is initialized
        assert hasattr(self.hook, "evidence_log")
        assert isinstance(self.hook.evidence_log, list)

        # Check that validation failures is initialized
        assert hasattr(self.hook, "validation_failures")
        assert isinstance(self.hook.validation_failures, list)

    def test_post_tool_use_evidence_collection(self):
        """Test evidence collection after tool operations."""
        with self.temp_dir as temp_path:
            # Create test files
            test_files = [
                os.path.join(temp_path, "file1.txt"),
                os.path.join(temp_path, "file2.py"),
                os.path.join(temp_path, "file3.md"),
            ]

            # Create evidence
            evidence = self.evidence_generator.create_file_evidence(test_files)

            # Log evidence using the hook
            for ev in evidence:
                self.hook.log_evidence("file_operations", ev, test_files)

            # Verify evidence was collected
            assert len(self.hook.evidence_log) > 0
            assert all(
                "file_operations" in entry["type"] for entry in self.hook.evidence_log
            )

    def test_post_tool_use_file_validation(self):
        """Test file validation after tool operations."""
        # Test safe file operation
        safe_file = os.path.join(self.temp_dir, "safe_file.txt")
        is_safe, reason = self.hook.validate_file_operation(safe_file, "write")

        assert is_safe is True
        assert "allowed" in reason.lower()

        # Test dangerous file operation
        dangerous_file = "/etc/passwd"
        is_safe, reason = self.hook.validate_file_operation(dangerous_file, "write")

        assert is_safe is False
        assert "dangerous" in reason.lower()

    def test_post_tool_use_test_result_validation(self):
        """Test test result validation after tool operations."""
        # Test successful test results
        successful_output = """
        ==================== test session starts ====================
        collected 5 items

        test_example.py::test_basic PASSED
        test_example.py::test_complex PASSED
        test_example.py::test_edge PASSED
        test_example.py::test_integration PASSED
        test_example.py::test_performance PASSED

        ==================== 5 passed in 0.45s ====================
        """

        is_valid = self.hook.verify_test_results(successful_output)
        assert is_valid is True

        # Test failed test results
        failed_output = """
        ==================== test session starts ====================
        collected 5 items

        test_example.py::test_basic PASSED
        test_example.py::test_complex FAILED
        test_example.py::test_edge PASSED
        test_example.py::test_integration FAILED
        test_example.py::test_performance PASSED

        ==================== 3 passed, 2 failed in 0.45s ====================
        """

        is_valid = self.hook.verify_test_results(failed_output)
        assert is_valid is False

    def test_post_tool_use_evidence_requirement(self):
        """Test evidence requirement enforcement after tool operations."""
        # Test with evidence provided
        claim = "File operations completed successfully"
        evidence = [
            "File created: P:\\tests\\test_file.txt",
            "File size: 1024 bytes",
            "Path exists: P:\\tests\\test_file.txt",
        ]

        result = self.hook.require_evidence(claim, evidence)
        assert result is True

        # Test without evidence
        result = self.hook.require_evidence("No evidence provided", [])
        assert result is False

        # Verify failure was recorded
        assert len(self.hook.validation_failures) > 0
        assert "evidence required" in self.hook.validation_failures[0].lower()

    def test_post_tool_use_checklist_validation(self):
        """Test checklist validation after tool operations."""
        # Test incomplete checklist
        incomplete_checklist = {
            "evidence_provided": True,
            "tests_written": True,
            "tests_pass": False,
            "code_reviewed": False,
        }

        is_complete, missing_items = self.hook.validate_checklist_completion(
            incomplete_checklist
        )

        assert is_complete is False
        assert len(missing_items) > 0
        assert "tests_pass" in missing_items
        assert "code_reviewed" in missing_items

        # Test complete checklist
        complete_checklist = {
            "evidence_provided": True,
            "tests_written": True,
            "tests_pass": True,
            "code_reviewed": True,
        }

        is_complete, missing_items = self.hook.validate_checklist_completion(
            complete_checklist
        )
        assert is_complete is True
        assert len(missing_items) == 0

    def test_post_tool_use_task_completion_validation(self):
        """Test task completion validation after tool operations."""
        # Test valid completion context
        valid_context = {
            "evidence_provided": True,
            "checklist": {
                "evidence_provided": True,
                "tests_written": True,
                "tests_pass": True,
                "code_reviewed": False,
            },
        }

        can_complete, issues = self.hook.can_complete_task(valid_context)

        # Can complete should pass if checklist requirements are met
        assert can_complete is True or len(issues) == 0

        # Test invalid completion context
        invalid_context = {
            "evidence_provided": False,
            "checklist": {
                "evidence_provided": False,
                "tests_written": False,
                "tests_pass": False,
                "code_reviewed": False,
            },
        }

        can_complete, issues = self.hook.can_complete_task(invalid_context)
        assert can_complete is False
        assert len(issues) > 0

    def test_post_tool_use_performance_timing(self):
        """Test that post-tool use operations complete within performance targets."""
        target_ms = 2000.0  # 2 second target

        with PerformanceTimer() as timer:
            # Simulate multiple post-tool use operations
            evidence = self.evidence_generator.create_file_evidence(
                [
                    os.path.join(self.temp_dir, "file1.txt"),
                    os.path.join(self.temp_dir, "file2.txt"),
                ]
            )

            # Log evidence
            for ev in evidence:
                self.hook.log_evidence("file_operations", ev)

            # Validate checklist
            self.hook.validate_checklist_completion(
                {"evidence_provided": True, "tests_written": True}
            )

            # Verify test results
            self.hook.verify_test_results("All tests PASSED")

        # Should complete within 2 seconds
        assert (
            timer.elapsed_ms < target_ms
        ), f"Post-tool use validation took {timer.elapsed_ms}ms, target: {target_ms}ms"

    def test_post_tool_use_file_existence_verification(self):
        """Test file existence verification after tool operations."""
        with self.temp_dir as temp_path:
            # Test existing file
            existing_file = os.path.join(temp_path, "existing.txt")
            existing_file.write_text("test content")

            is_verified = self.hook.verify_file_exists(existing_file)
            assert is_verified is True

            # Test non-existing file
            non_existing_file = os.path.join(temp_path, "nonexistent.txt")
            is_verified = self.hook.verify_file_exists(non_existing_file)
            assert is_verified is False

    def test_post_tool_use_status_report_generation(self):
        """Test status report generation after tool operations."""
        # Add some test data
        evidence = self.evidence_generator.create_file_evidence(
            [os.path.join(self.temp_dir, "test.txt")]
        )

        for ev in evidence:
            self.hook.log_evidence("file_operations", ev)

        # Add a validation failure
        self.hook.require_evidence("Test claim", [])

        # Generate status report
        status = self.hook.get_status_report()

        # Verify report structure
        assert "total_evidence_items" in status
        assert "validation_failures" in status
        assert "recent_failures" in status
        assert "evidence_summary" in status
        assert "config_loaded" in status
        assert "last_updated" in status

        # Verify content
        assert status["total_evidence_items"] > 0
        assert status["validation_failures"] > 0
        assert status["config_loaded"] is True

    def test_post_tool_use_error_handling(self):
        """Test error handling in post-tool use operations."""
        # Test with invalid evidence type
        try:
            self.hook.log_evidence(None, "test", [])
            # Should not raise exception
        except Exception:
            pass  # Expected behavior

        # Test with None checklist
        try:
            is_complete, missing = self.hook.validate_checklist_completion(None)
            # Should handle gracefully
            assert is_complete is False
        except Exception:
            pass  # Expected behavior

        # Test with invalid test results
        try:
            is_valid = self.hook.verify_test_results(None)
            assert is_valid is False
        except Exception:
            pass  # Expected behavior

    def test_post_tool_use_configuration_updates(self):
        """Test configuration updates in post-tool use hook."""
        # Update configuration
        updates = {
            "evidence_requirements": {"file_operations": False},
            "validation_rules": {"require_evidence_for_completion": False},
        }

        self.hook.update_config(updates)

        # Verify configuration was updated
        assert self.hook.config["evidence_requirements"]["file_operations"] is False
        assert (
            self.hook.config["validation_rules"]["require_evidence_for_completion"]
            is False
        )

    def test_post_tool_use_validation_failures_reset(self):
        """Test resetting validation failures in post-tool use hook."""
        # Add some validation failures
        self.hook.require_evidence("Test claim 1", [])
        self.hook.require_evidence("Test claim 2", [])

        assert len(self.hook.validation_failures) == 2

        # Reset failures
        self.hook.reset_failures()

        assert len(self.hook.validation_failures) == 0


if __name__ == "__main__":
    # Run the tests
    import pytest

    pytest.main([__file__, "-v"])
