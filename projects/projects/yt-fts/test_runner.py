#!/usr/bin/env python3
"""
Simple test runner for the inconsistency system tests.

This runs the tests without pytest to avoid path issues.
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_test_method(test_instance, method_name):
    """Run a single test method and return result."""
    try:
        method = getattr(test_instance, method_name)
        test_instance.setup_method()
        result = method()
        test_instance.teardown_method()
        return True, None
    except Exception as e:
        test_instance.teardown_method()
        return False, str(e)


def run_tests():
    """Run all tests in the inconsistency system test suite."""
    from tests.test_inconsistency_system import (
        TestAutoRepairManager,
        TestBatchDownloaderInconsistencyDetection,
        TestInconsistencyLogger,
        TestIntegrationInconsistencySystem,
    )

    test_classes = [
        TestInconsistencyLogger,
        TestAutoRepairManager,
        TestBatchDownloaderInconsistencyDetection,
        TestIntegrationInconsistencySystem,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print(f"{'='*60}")

        # Get all test methods
        test_methods = [
            method for method in dir(test_class) if method.startswith("test_")
        ]

        for method_name in test_methods:
            total_tests += 1
            print(f"  Running {method_name}...", end=" ")

            # Create test instance
            test_instance = test_class()

            # Run the test
            success, error = run_test_method(test_instance, method_name)

            if success:
                print("✓ PASSED")
                passed_tests += 1
            else:
                print(f"✗ FAILED: {error}")
                failed_tests.append(f"{test_class.__name__}.{method_name}: {error}")

    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {len(failed_tests)}")

    if failed_tests:
        print("\nFailed tests:")
        for failure in failed_tests:
            print(f"  - {failure}")
        return 1
    print("\nAll tests passed! 🎉")
    return 0


if __name__ == "__main__":
    sys.exit(run_tests())
