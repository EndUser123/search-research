#!/usr/bin/env python3
"""
Golden Set Runner - Week 3 RCA Enhancement

Runs golden set test cases for temporal validation.
Provides automated regression testing for RCA enhancements.

Author: CSF Development Team
Version: 1.0.0
Part of: Week 3 RCA Enhancements
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .temporal_check import TemporalCheck, TemporalCheckResult


@dataclass
class GoldenSetResult:
    """Result of a golden set test run."""
    test_id: str
    test_name: str
    passed: bool
    expected_verdict: str
    actual_verdict: str
    warnings_matched: bool
    error_message: str = ""
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "passed": self.passed,
            "expected_verdict": self.expected_verdict,
            "actual_verdict": self.actual_verdict,
            "warnings_matched": self.warnings_matched,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms
        }


@dataclass
class GoldenSetSummary:
    """Summary of golden set test run."""
    total_tests: int
    passed: int
    failed: int
    skipped: int
    results: list[GoldenSetResult] = field(default_factory=list)
    executed_at: datetime = field(default_factory=datetime.now)

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "pass_rate": self.pass_rate,
            "executed_at": self.executed_at.isoformat(),
            "results": [r.to_dict() for r in self.results]
        }


class GoldenSetRunner:
    """
    Runs golden set test cases for RCA enhancements.

    Tests temporal check functionality against known test cases
    to ensure correct behavior and prevent regressions.
    """

    def __init__(self, golden_set_path: str | None = None):
        """
        Initialize golden set runner.

        Args:
            golden_set_path: Path to golden_set.json file
        """
        if golden_set_path is None:
            # Default to tests/lib/rca/golden/golden_set.json
            # Path from src/rca/golden_set_runner.py
            # Need to go up levels to project root
            current_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
            golden_set_path = current_dir / "tests" / "lib" / "rca" / "golden" / "golden_set.json"

        self.golden_set_path = Path(golden_set_path)
        self.checker = TemporalCheck()
        self.test_data = self._load_golden_set()

    def _load_golden_set(self) -> dict:
        """Load golden set test data from JSON file."""
        try:
            with open(self.golden_set_path) as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "metadata": {
                    "name": "RCA Golden Set",
                    "version": "1.0.0"
                },
                "tests": [],
                "metrics": {}
            }

    def run_all(self) -> GoldenSetSummary:
        """
        Run all golden set tests.

        Returns:
            GoldenSetSummary with results
        """
        tests = self.test_data.get("tests", [])
        results = []

        for test in tests:
            result = self._run_test(test)
            results.append(result)

        # Build summary
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)

        return GoldenSetSummary(
            total_tests=len(results),
            passed=passed,
            failed=failed,
            skipped=0,
            results=results
        )

    def run_test_by_id(self, test_id: str) -> GoldenSetResult | None:
        """
        Run a specific test by ID.

        Args:
            test_id: Test identifier

        Returns:
            GoldenSetResult or None if test not found
        """
        tests = self.test_data.get("tests", [])

        for test in tests:
            if test.get("id") == test_id:
                return self._run_test(test)

        return None

    def _run_test(self, test: dict) -> GoldenSetResult:
        """
        Run a single golden set test.

        Args:
            test: Test case dictionary

        Returns:
            GoldenSetResult
        """
        import time
        start = time.time()

        test_id = test.get("id", "unknown")
        test_name = test.get("name", "Unnamed Test")
        hypothesis = test.get("hypothesis", "")
        expected_verdict = test.get("expected_verdict", "UNKNOWN")
        context = test.get("context", {})
        expected_warnings = test.get("expected_warnings", [])

        try:
            # Run temporal check
            result = self.checker.check(hypothesis, context)

            actual_verdict = result.verdict.value
            verdict_match = actual_verdict == expected_verdict

            # Check warnings
            warnings_match = self._check_warnings(result, expected_warnings)

            # Test passes if verdict and warnings match
            passed = verdict_match and warnings_match

            # Build error message if failed
            error_message = ""
            if not passed:
                errors = []
                if not verdict_match:
                    errors.append(f"Verdict mismatch: expected {expected_verdict}, got {actual_verdict}")
                if not warnings_match:
                    errors.append(f"Warnings mismatch: expected {len(expected_warnings)} warnings, got {len(result.warnings)}")
                error_message = "; ".join(errors)

            execution_time = (time.time() - start) * 1000

            return GoldenSetResult(
                test_id=test_id,
                test_name=test_name,
                passed=passed,
                expected_verdict=expected_verdict,
                actual_verdict=actual_verdict,
                warnings_matched=warnings_match,
                error_message=error_message,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return GoldenSetResult(
                test_id=test_id,
                test_name=test_name,
                passed=False,
                expected_verdict=expected_verdict,
                actual_verdict="ERROR",
                warnings_matched=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )

    def _check_warnings(
        self,
        result: TemporalCheckResult,
        expected_warnings: list[dict]
    ) -> bool:
        """
        Check if warnings match expected.

        Args:
            result: Temporal check result
            expected_warnings: Expected warning specifications

        Returns:
            True if warnings match expectations
        """
        # If no warnings expected, result should have none
        if not expected_warnings:
            return len(result.warnings) == 0

        # Check each expected warning
        for expected in expected_warnings:
            api = expected.get("api", "")
            severity = expected.get("severity", "")

            # Find matching warning in result
            found = False
            for warning in result.warnings:
                if api.lower() in warning.api.lower():
                    if severity and warning.severity != severity:
                        continue
                    found = True
                    break

            if not found:
                return False

        return True

    def print_summary(self, summary: GoldenSetSummary) -> None:
        """
        Print summary of golden set test run.

        Args:
            summary: GoldenSetSummary to print
        """
        print(f"\n{'='*60}")
        print("Golden Set Test Results")
        print(f"{'='*60}")
        print(f"Total: {summary.total_tests} | Passed: {summary.passed} | Failed: {summary.failed}")
        print(f"Pass Rate: {summary.pass_rate:.1f}%")
        print(f"{'='*60}\n")

        if summary.failed > 0:
            print("Failed Tests:")
            for result in summary.results:
                if not result.passed:
                    print(f"  [{result.test_id}] {result.test_name}")
                    print(f"    {result.error_message}")
            print()

    def get_metrics(self) -> dict:
        """
        Get golden set metrics.

        Returns:
            Dictionary with metrics
        """
        return self.test_data.get("metrics", {})


def run_golden_set(golden_set_path: str | None = None) -> GoldenSetSummary:
    """
    Convenience function to run golden set tests.

    Args:
        golden_set_path: Optional path to golden_set.json

    Returns:
        GoldenSetSummary with results
    """
    runner = GoldenSetRunner(golden_set_path)
    summary = runner.run_all()
    runner.print_summary(summary)
    return summary


if __name__ == "__main__":
    import sys

    # Allow command-line path override
    path = sys.argv[1] if len(sys.argv) > 1 else None

    summary = run_golden_set(path)

    # Exit with error code if any tests failed
    sys.exit(0 if summary.failed == 0 else 1)
