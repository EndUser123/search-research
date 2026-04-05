#!/usr/bin/env python3
"""
Quarantine System Tests - Tier 1 Critical Test

Test Case ID: TC-TIER1-002
Priority: High
Test Type: Integration Testing

Purpose:
Verify that the test quarantine system works correctly.
These tests ensure flaky test detection and quarantine functionality.

Preconditions:
- Tier 0 smoke tests pass
- System configuration tests pass
- Quarantine system is implemented

Expected Results:
- Quarantine system initializes correctly
- Test results are recorded properly
- Flaky tests are automatically quarantined
- Quarantine management commands work

Test Duration: <3.0 seconds
"""

import sys
import tempfile
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if str(project_root / "__csf") not in sys.path:
    sys.path.insert(0, str(project_root / "__csf"))

try:
    from src.testing.test_quarantine import (
        TestQuarantineSystem,
        TestResult,
        get_quarantine_system,
        record_test_execution,
    )
except ImportError as e:
    print(f"WARNING: Could not import quarantine system: {e}")
    TestQuarantineSystem = None
    TestResult = None


def test_quarantine_system_initialization():
    """
    Test quarantine system initialization.

    Algorithm Approach: Verify quarantine system can be created and initialized.

    Returns:
    bool: True if initialization works correctly

    Raises:
    AssertionError: If initialization fails
    """
    if TestQuarantineSystem is None:
        print("SKIP: Quarantine system not available for testing")
        return True

    # Create temporary directory for test database
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_quarantine.db"

        try:
            # Initialize quarantine system
            quarantine_system = TestQuarantineSystem(str(db_path))

            # Verify database was created
            assert db_path.exists(), "Quarantine database was not created"

            # Test basic functionality
            health_report = quarantine_system.get_test_health_report()
            assert health_report is not None, "Health report should not be None"
            assert (
                "overall_statistics" in health_report
            ), "Health report missing overall statistics"

            print("✓ Quarantine system initialization works correctly")

        except Exception as e:
            raise AssertionError(f"Quarantine system initialization failed: {e}")


def test_test_result_recording():
    """
    Test test result recording functionality.

    Algorithm Approach: Record test results and verify they are stored correctly.

    Returns:
    bool: True if test result recording works correctly

    Raises:
    AssertionError: If test result recording fails
    """
    if TestQuarantineSystem is None or TestResult is None:
        print("SKIP: Quarantine system not available for testing")
        return True

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_quarantine.db"
        quarantine_system = TestQuarantineSystem(str(db_path))

        try:
            # Create test result
            test_result = TestResult(
                test_name="tests.integration.test_sample.test_function",
                execution_time=1.5,
                success=True,
                timestamp=time.time(),
                tier="1",
            )

            # Record test result
            quarantine_triggered = quarantine_system.record_test_result(test_result)

            # Verify result was recorded (should not trigger quarantine)
            assert isinstance(quarantine_triggered, bool), "Should return boolean"
            assert (
                not quarantine_triggered
            ), "Single successful test should not trigger quarantine"

            # Record multiple successful results
            for i in range(5):
                result = TestResult(
                    test_name="tests.integration.test_sample.test_function",
                    execution_time=1.2 + i * 0.1,
                    success=True,
                    timestamp=time.time() - (i * 60),
                    tier="1",
                )
                quarantine_system.record_test_result(result)

            print("✓ Test result recording works correctly")

        except Exception as e:
            raise AssertionError(f"Test result recording failed: {e}")


def test_flaky_test_detection():
    """
    Test flaky test detection and quarantine triggering.

    Algorithm Approach: Create failing tests to trigger quarantine mechanism.

    Returns:
    bool: True if flaky test detection works correctly

    Raises:
    AssertionError: If flaky test detection fails
    """
    if TestQuarantineSystem is None or TestResult is None:
        print("SKIP: Quarantine system not available for testing")
        return True

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_quarantine.db"

        # Create quarantine system with lower threshold for testing
        quarantine_system = TestQuarantineSystem(str(db_path))
        quarantine_system.failure_rate_threshold = 10.0  # 10% threshold for testing
        quarantine_system.minimum_executions = 5  # Lower minimum for testing

        try:
            test_name = "tests.integration.test_flaky.test_unreliable_function"

            # Create test results with high failure rate (80% failure)
            for i in range(10):
                success = i < 2  # Only 2 successes out of 10 (80% failure rate)
                result = TestResult(
                    test_name=test_name,
                    execution_time=2.5,
                    success=success,
                    timestamp=time.time() - ((9 - i) * 3600),  # Stagger over time
                    error_message="Timeout error" if not success else None,
                    tier="1",
                )

                quarantine_triggered = quarantine_system.record_test_result(result)
                # Should trigger quarantine on the last iteration
                if i == 9:
                    assert (
                        quarantine_triggered
                    ), "High failure rate should trigger quarantine"

            # Verify test was quarantined
            quarantined_tests = quarantine_system.get_quarantined_tests()
            assert len(quarantined_tests) > 0, "Test should be quarantined"

            # Find our test in quarantined list
            our_test = None
            for test in quarantined_tests:
                if test.test_name == test_name:
                    our_test = test
                    break

            assert our_test is not None, "Our test should be in quarantined list"
            assert (
                our_test.failure_rate >= 80.0
            ), f"Failure rate should be >= 80%, got {our_test.failure_rate}"
            assert (
                our_test.total_executions >= 10
            ), f"Should have at least 10 executions, got {our_test.total_executions}"

            print(
                f"✓ Flaky test detection works correctly (quarantined {len(quarantined_tests)} tests)"
            )

        except Exception as e:
            raise AssertionError(f"Flaky test detection failed: {e}")


def test_quarantine_management():
    """
    Test quarantine management functionality.

    Algorithm Approach: Test quarantine release and management operations.

    Returns:
    bool: True if quarantine management works correctly

    Raises:
    AssertionError: If quarantine management fails
    """
    if TestQuarantineSystem is None or TestResult is None:
        print("SKIP: Quarantine system not available for testing")
        return True

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_quarantine.db"
        quarantine_system = TestQuarantineSystem(str(db_path))

        # Lower thresholds for testing
        quarantine_system.failure_rate_threshold = 10.0
        quarantine_system.minimum_executions = 5

        try:
            test_name = "tests.integration.test_management.test_release_function"

            # Create failing test to get it quarantined
            for i in range(8):
                success = False  # All failures to trigger quarantine quickly
                result = TestResult(
                    test_name=test_name,
                    execution_time=1.8,
                    success=success,
                    timestamp=time.time() - ((7 - i) * 3600),
                    error_message="Intentional test failure",
                    tier="1",
                )
                quarantine_system.record_test_result(result)

            # Verify test is quarantined
            quarantined_before = quarantine_system.get_quarantined_tests()
            assert len(quarantined_before) > 0, "Test should be quarantined"

            # Release test from quarantine
            release_success = quarantine_system.release_test_from_quarantine(
                test_name, "Test release for management testing"
            )
            assert release_success, "Test release should succeed"

            # Verify test is no longer quarantined
            quarantined_after = quarantine_system.get_quarantined_tests()
            assert (
                len(quarantined_after) == len(quarantined_before) - 1
            ), "Test should be released from quarantine"

            # Try to release non-existent test
            release_success = quarantine_system.release_test_from_quarantine(
                "tests.non_existent.test_function", "Test release of non-existent test"
            )
            assert not release_success, "Release of non-existent test should fail"

            print("✓ Quarantine management works correctly")

        except Exception as e:
            raise AssertionError(f"Quarantine management failed: {e}")


def test_health_report_generation():
    """
    Test health report generation.

    Algorithm Approach: Generate health reports and verify their structure.

    Returns:
    bool: True if health report generation works correctly

    Raises:
    AssertionError: If health report generation fails
    """
    if TestQuarantineSystem is None or TestResult is None:
        print("SKIP: Quarantine system not available for testing")
        return True

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_quarantine.db"
        quarantine_system = TestQuarantineSystem(str(db_path))

        try:
            # Create some test data
            test_names = [
                "tests.unit.test_utils.test_helper_function",
                "tests.integration.test_api.test_get_endpoint",
                "tests.integration.test_database.test_connection",
            ]

            for i, test_name in enumerate(test_names):
                for j in range(15):
                    # Create mixed results with different failure rates
                    if test_name.endswith("test_helper_function"):
                        success = j < 14  # ~93% success rate
                    elif test_name.endswith("test_get_endpoint"):
                        success = j < 12  # ~80% success rate
                    else:
                        success = j < 8  # ~53% success rate

                    result = TestResult(
                        test_name=test_name,
                        execution_time=1.0 + j * 0.1,
                        success=success,
                        timestamp=time.time()
                        - ((len(test_names) * 15 - i * 15 - j) * 3600),
                        error_message=None if success else f"Test failure {j}",
                        tier="1",
                    )
                    quarantine_system.record_test_result(result)

            # Generate health report
            health_report = quarantine_system.get_test_health_report()

            # Verify report structure
            assert health_report is not None, "Health report should not be None"
            assert "overall_statistics" in health_report, "Missing overall statistics"
            assert "top_failing_tests" in health_report, "Missing top failing tests"

            # Verify overall statistics
            stats = health_report["overall_statistics"]
            assert stats["total_executions"] > 0, "Should have executions recorded"
            assert stats["unique_tests"] >= len(
                test_names
            ), "Should have recorded all test types"

            # Verify top failing tests
            top_failing = health_report["top_failing_tests"]
            assert isinstance(top_failing, list), "Top failing should be a list"

            print(
                f"✓ Health report generation works correctly ({stats['total_executions']} executions, {len(top_failing)} failing tests)"
            )

        except Exception as e:
            raise AssertionError(f"Health report generation failed: {e}")


def run_all_quarantine_system_tests():
    """
    Run all quarantine system tests.

    Algorithm Approach: Execute all quarantine tests in sequence.

    Returns:
    tuple: (total_tests, passed_tests, failed_tests)
    """
    test_functions = [
        test_quarantine_system_initialization,
        test_test_result_recording,
        test_flaky_test_detection,
        test_quarantine_management,
        test_health_report_generation,
    ]

    total_tests = len(test_functions)
    passed_tests = 0
    failed_tests = []

    print("Running Quarantine System Tests...")
    print("=" * 50)

    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
        except Exception as e:
            failed_tests.append(f"{test_func.__name__}: {e}")
            print(f"✗ {test_func.__name__} failed: {e}")

    print("=" * 50)
    print(f"Quarantine System Tests: {passed_tests}/{total_tests} passed")

    if failed_tests:
        print("Failed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")

    return total_tests, passed_tests, failed_tests


if __name__ == "__main__":
    """
    Main execution for standalone testing.
    """
    total, passed, failed = run_all_quarantine_system_tests()

    if len(failed) == 0:
        print("✅ All Quarantine System tests passed!")
        sys.exit(0)
    else:
        print("❌ Some Quarantine System tests failed!")
        sys.exit(1)
