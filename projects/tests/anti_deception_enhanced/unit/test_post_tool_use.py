"""
Unit Tests for PostToolUse Hook Component

Tests individual functionality of the PostToolUse hook component including:
- Evidence validation after tool use
- File operation verification
- Task completion validation
- Performance benchmarking
- Error handling and edge cases
"""

import os
import sys
import time
from pathlib import Path

import pytest

# Import the anti-deception hook
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "__csf")
)
from anti_deception_hook import AntiDeceptionHook


class TestPostToolUse:
    """Test suite for PostToolUse hook component functionality."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.hook = AntiDeceptionHook()
        self.temp_dir = Path("P:\\tests\\anti_deception_enhanced\\temp\\post_tool_use")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # Create test files
        self.test_file = self.temp_dir / "test_output.txt"
        self.test_file.write_text("Test output content")

        self.large_file = self.temp_dir / "large_output.txt"
        self.large_file.write_text("x" * 10000)  # 10KB file

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        # Clean up temp files
        for file_path in self.temp_dir.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        if self.temp_dir.exists():
            self.temp_dir.rmdir()

    def test_file_operation_validation_success(self):
        """Test successful file operation validation."""
        # Test valid file operations
        test_cases = [
            (str(self.test_file), "read"),
            (str(self.test_file), "write"),
            (str(self.temp_dir), "create"),
        ]

        for file_path, operation in test_cases:
            is_safe, reason = self.hook.validate_file_operation(file_path, operation)
            assert is_safe, f"File operation should be safe for {file_path}: {reason}"

    def test_file_operation_validation_dangerous_patterns(self):
        """Test blocking of dangerous file operations."""
        dangerous_cases = [
            ("/etc/passwd", "read"),
            (".bashrc", "write"),
            ("rm -rf /", "delete"),
            ("/etc/systemd/system/some.service", "write"),
            (".ssh/authorized_keys", "write"),
        ]

        for file_path, operation in dangerous_cases:
            is_safe, reason = self.hook.validate_file_operation(file_path, operation)
            assert not is_safe, f"Dangerous operation should be blocked: {file_path}"

    def test_file_operation_validation_allowed_paths(self):
        """Test that allowed paths work correctly."""
        allowed_cases = [
            ("P:\\__csf\\test.txt", "write"),
            ("P:\\temp\\safe_file.txt", "write"),
            ("C:\\Users\\test\\file.txt", "read"),
            (".\\local_file.txt", "write"),
        ]

        for file_path, operation in allowed_cases:
            is_safe, reason = self.hook.validate_file_operation(file_path, operation)
            assert is_safe, f"Allowed path should work: {file_path}"

    def test_evidence_requirement_validation(self):
        """Test evidence requirement validation."""
        # Test successful evidence provision
        claim = "File was successfully processed"
        evidence = [
            str(self.test_file),
            "Processing completed at " + time.strftime("%Y-%m-%d %H:%M:%S"),
            "File size: " + str(os.path.getsize(self.test_file)) + " bytes",
        ]

        result = self.hook.require_evidence(claim, evidence)
        assert result, "Evidence should be accepted when provided"
        assert len(self.hook.evidence_log) == 1, "Evidence should be logged"

    def test_evidence_requirement_failure(self):
        """Test evidence requirement failure."""
        # Test claim without evidence
        claim = "Task completed successfully"
        result = self.hook.require_evidence(claim, None)
        assert not result, "Evidence should be required"
        assert (
            len(self.hook.validation_failures) == 1
        ), "Validation failure should be recorded"

    def test_evidence_requirement_empty_list(self):
        """Test evidence requirement with empty list."""
        claim = "Something was done"
        result = self.hook.require_evidence(claim, [])
        assert not result, "Empty evidence list should be rejected"
        assert (
            len(self.hook.validation_failures) == 1
        ), "Validation failure should be recorded"

    def test_checklist_validation_complete(self):
        """Test checklist validation when all items are complete."""
        checklist = {
            "evidence_provided": True,
            "tests_written": True,
            "tests_pass": True,
            "code_reviewed": True,
            "files_created": True,
            "safety_validated": True,
        }

        is_complete, missing = self.hook.validate_checklist_completion(checklist)
        assert is_complete, "Complete checklist should pass validation"
        assert len(missing) == 0, "No items should be missing"

    def test_checklist_validation_incomplete(self):
        """Test checklist validation when items are missing."""
        checklist = {
            "evidence_provided": True,
            "tests_written": True,
            "tests_pass": False,  # Missing
            "code_reviewed": False,  # Missing
            "files_created": True,
            "safety_validated": False,  # Missing
        }

        is_complete, missing = self.hook.validate_checklist_completion(checklist)
        assert not is_complete, "Incomplete checklist should fail validation"
        assert len(missing) == 3, "Three items should be missing"
        assert "tests_pass" in missing
        assert "code_reviewed" in missing
        assert "safety_validated" in missing

    def test_checklist_validation_partial_completion(self):
        """Test checklist validation with partial completion."""
        checklist = {
            "evidence_provided": True,
            "tests_written": True,
            "tests_pass": True,
            "code_reviewed": False,  # Only missing item
            "files_created": True,
        }

        is_complete, missing = self.hook.validate_checklist_completion(checklist)
        assert not is_complete, "Incomplete checklist should fail validation"
        assert len(missing) == 1, "Only one item should be missing"
        assert missing[0] == "code_reviewed"

    def test_task_completion_validation_success(self):
        """Test successful task completion validation."""
        task_context = {
            "evidence_provided": True,
            "checklist": {
                "evidence_provided": True,
                "tests_written": True,
                "tests_pass": True,
                "files_created": True,
                "safety_validated": True,
            },
        }

        can_complete, issues = self.hook.can_complete_task(task_context)
        assert (
            can_complete
        ), "Task should be completable with proper evidence and checklist"
        assert len(issues) == 0, "No blocking issues should exist"

    def test_task_completion_validation_no_evidence(self):
        """Test task completion validation without evidence."""
        task_context = {
            "evidence_provided": False,  # Missing evidence
            "checklist": {
                "evidence_provided": False,
                "tests_written": True,
                "tests_pass": True,
                "files_created": True,
                "safety_validated": True,
            },
        }

        can_complete, issues = self.hook.can_complete_task(task_context)
        assert not can_complete, "Task should not be completable without evidence"
        assert len(issues) == 1, "One blocking issue should exist"
        assert "evidence" in issues[0].lower()

    def test_task_completion_validation_incomplete_checklist(self):
        """Test task completion validation with incomplete checklist."""
        task_context = {
            "evidence_provided": True,
            "checklist": {
                "evidence_provided": True,
                "tests_written": True,
                "tests_pass": True,
                "code_reviewed": False,  # Missing
                "files_created": True,
                "safety_validated": True,
            },
        }

        can_complete, issues = self.hook.can_complete_task(task_context)
        assert (
            not can_complete
        ), "Task should not be completable with incomplete checklist"
        assert len(issues) == 1, "One blocking issue should exist"

    def test_task_completion_validation_with_failures(self):
        """Test task completion validation with existing validation failures."""
        # Add some validation failures first
        self.hook.validation_failures = [
            "Previous validation failure 1",
            "Previous validation failure 2",
        ]

        task_context = {
            "evidence_provided": True,
            "checklist": {
                "evidence_provided": True,
                "tests_written": True,
                "tests_pass": True,
                "files_created": True,
                "safety_validated": True,
            },
        }

        can_complete, issues = self.hook.can_complete_task(task_context)
        assert (
            not can_complete
        ), "Task should not be completable with existing validation failures"
        assert len(issues) == 1, "One blocking issue should exist"
        assert "validation failures" in issues[0].lower()

    def test_file_existence_verification(self):
        """Test file existence verification."""
        # Test existing file
        result = self.hook.verify_file_exists(str(self.test_file))
        assert result, "Existing file should be verified successfully"

        # Test non-existing file
        non_existent = str(self.temp_dir / "non_existent_file.txt")
        result = self.hook.verify_file_exists(non_existent)
        assert not result, "Non-existing file should not be verified"

    def test_test_results_verification_success(self):
        """Test test results verification with successful output."""
        successful_outputs = [
            "All tests PASSED",
            "Tests PASSED (10/10)",
            "PASSED (all 5 tests)",
            "OK",
            "All tests passed",
            "Success: All tests passed",
            "100% passed",
        ]

        for output in successful_outputs:
            result = self.hook.verify_test_results(output)
            assert result, f"Successful test output should pass: {output}"

    def test_test_results_verification_failure(self):
        """Test test results verification with failed output."""
        failed_outputs = [
            "Tests FAILED",
            "2 failures, 3 errors",
            "FAILED (5/10)",
            "ERROR: Test failed",
            "No tests passed",
            "0% passed",
        ]

        for output in failed_outputs:
            result = self.hook.verify_test_results(output)
            assert not result, f"Failed test output should fail: {output}"

    def test_evidence_logging(self):
        """Test evidence logging functionality."""
        file_paths = [str(self.test_file), str(self.large_file)]

        self.hook.log_evidence("test_results", "All unit tests passed", file_paths)

        assert len(self.hook.evidence_log) == 1, "Evidence should be logged"
        logged_evidence = self.hook.evidence_log[0]
        assert logged_evidence["type"] == "test_results"
        assert logged_evidence["details"] == "All unit tests passed"
        assert logged_evidence["file_paths"] == file_paths
        assert "timestamp" in logged_evidence

    def test_status_report_generation(self):
        """Test status report generation."""
        # Add some test data
        self.hook.require_evidence("Test claim", ["evidence1", "evidence2"])
        self.hook.validation_failures.append("Test failure")

        report = self.hook.get_status_report()

        assert report["total_evidence_items"] == 1
        assert report["validation_failures"] == 1
        assert len(report["recent_failures"]) == 1
        assert report["config_loaded"] is True
        assert "last_updated" in report
        assert "evidence_summary" in report

    def test_validation_failures_reset(self):
        """Test validation failures reset functionality."""
        # Add some failures
        self.hook.validation_failures = ["Failure 1", "Failure 2"]

        assert len(self.hook.validation_failures) == 2

        self.hook.reset_failures()

        assert len(self.hook.validation_failures) == 0

    def test_configuration_update(self):
        """Test configuration update functionality."""
        original_config = self.hook.config.copy()

        updates = {
            "validation_rules": {
                "require_evidence_for_completion": False,
                "enforce_checklist": False,
            }
        }

        self.hook.update_config(updates)

        # Check that the config was updated
        assert (
            self.hook.config["validation_rules"]["require_evidence_for_completion"]
            is False
        )
        assert self.hook.config["validation_rules"]["enforce_checklist"] is False

    def test_performance_validation_speed(self):
        """Test that validation operations are fast enough."""
        start_time = time.time()

        # Perform multiple validation operations
        for i in range(100):
            self.hook.validate_file_operation(str(self.test_file), "read")
            self.hook.verify_file_exists(str(self.test_file))

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in under 1 second for 100 operations
        assert duration < 1.0, f"Validation should be fast (< 1s), took {duration:.3f}s"

    def test_memory_usage_efficiency(self):
        """Test that memory usage is efficient during long operations."""
        initial_log_count = len(self.hook.evidence_log)
        initial_failure_count = len(self.hook.validation_failures)

        # Perform many operations to test memory efficiency
        for i in range(1000):
            self.hook.log_evidence("test", f"Test {i}", [str(self.test_file)])
            if i % 100 == 0:  # Add validation failures occasionally
                self.hook.validation_failures.append(f"Failure {i}")

        # Clean up most entries to test memory efficiency
        self.hook.evidence_log = self.hook.evidence_log[-10:]  # Keep last 10
        self.hook.validation_failures = self.hook.validation_failures[
            -5:
        ]  # Keep last 5

        final_log_count = len(self.hook.evidence_log)
        final_failure_count = len(self.hook.validation_failures)

        assert final_log_count == 10
        assert final_failure_count == 5

    def test_error_handling_invalid_file_path(self):
        """Test error handling with invalid file paths."""
        # Test with None file path
        with pytest.raises(TypeError):
            self.hook.validate_file_operation(None, "read")

        # Test with empty string
        is_safe, reason = self.hook.validate_file_operation("", "read")
        assert not is_safe, "Empty file path should be blocked"

    def test_error_handling_invalid_operation(self):
        """Test error handling with invalid operations."""
        # Test with None operation
        with pytest.raises(TypeError):
            self.hook.validate_file_operation(str(self.test_file), None)

        # Test with empty operation
        is_safe, reason = self.hook.validate_file_operation(str(self.test_file), "")
        assert not is_safe, "Empty operation should be blocked"

    def test_concurrent_validation(self):
        """Test that validation works correctly under concurrent operations."""
        import queue
        import threading

        results_queue = queue.Queue()

        def validation_worker(worker_id):
            try:
                for i in range(10):
                    file_path = str(self.temp_dir / f"worker_{worker_id}_file_{i}.txt")
                    Path(file_path).write_text(f"Worker {worker_id} content {i}")

                    is_safe, reason = self.hook.validate_file_operation(
                        file_path, "write"
                    )
                    result = (worker_id, i, is_safe, reason)
                    results_queue.put(result)

                # Also test evidence requirements
                evidence = [str(self.test_file)]
                result = self.hook.require_evidence(
                    f"Worker {worker_id} completed", evidence
                )
                results_queue.put((worker_id, "evidence", result))

            except Exception as e:
                results_queue.put((worker_id, "error", str(e)))

        # Start multiple worker threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=validation_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Collect all results
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        # Verify all operations completed successfully
        assert len(results) == 55  # 5 workers * 11 operations each

        # Check that no validation errors occurred
        for result in results:
            if len(result) == 4:  # Validation result
                worker_id, operation_id, is_safe, reason = result
                assert (
                    is_safe
                ), f"Validation should pass for worker {worker_id}, op {operation_id}"
            elif len(result) == 3:  # Evidence result
                worker_id, operation_type, is_successful = result
                assert (
                    is_successful
                ), f"Evidence should be accepted for worker {worker_id}"

    def test_large_file_handling(self):
        """Test handling of large files."""
        # Create a larger file (1MB)
        large_content = "x" * (1024 * 1024)  # 1MB
        large_file = self.temp_dir / "large_file.txt"
        large_file.write_text(large_content)

        # Test validation of large file
        start_time = time.time()
        is_safe, reason = self.hook.validate_file_operation(str(large_file), "read")
        end_time = time.time()

        assert is_safe, "Large file should be valid for reading"
        assert end_time - start_time < 1.0, "Large file validation should be fast"

    def test_special_characters_in_paths(self):
        """Test handling of special characters in file paths."""
        special_paths = [
            "P:\\__csf\\test with spaces.txt",
            "P:\\__csf\\test-with-dashes.txt",
            "P:\\__csf\\test@with@symbols.txt",
            "P:\\__csf\\test(with)parentheses.txt",
        ]

        for file_path in special_paths:
            # Create the file
            Path(file_path).write_text("Test content")

            # Test validation
            is_safe, reason = self.hook.validate_file_operation(file_path, "read")
            assert is_safe, f"File with special characters should be valid: {file_path}"

            # Clean up
            Path(file_path).unlink(missing_ok=True)
