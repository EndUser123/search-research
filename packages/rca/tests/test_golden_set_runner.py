"""Tests for golden_set_runner module.

Tests for golden set test execution and validation.
"""

import pytest

from rca.golden_set_runner import (
    GoldenSetResult,
    GoldenSetRunner,
    TestOutcome,
)


class TestTestOutcome:
    """Test TestOutcome enum."""

    def test_outcome_values(self):
        """TestOutcome has expected values."""
        assert TestOutcome.PASSED.value == "passed"
        assert TestOutcome.FAILED.value == "failed"
        assert TestOutcome.SKIPPED.value == "skipped"
        assert TestOutcome.ERROR.value == "error"


class TestGoldenSetResult:
    """Test GoldenSetResult dataclass."""

    def test_result_creation(self):
        """GoldenSetResult can be created."""
        result = GoldenSetResult(
            test_name="test_basic_rca",
            outcome=TestOutcome.PASSED,
            duration_seconds=1.5,
            message="Test passed successfully",
        )

        assert result.test_name == "test_basic_rca"
        assert result.outcome == TestOutcome.PASSED

    def test_result_with_error_details(self):
        """Result can include error details."""
        result = GoldenSetResult(
            test_name="test_faulty_case",
            outcome=TestOutcome.FAILED,
            duration_seconds=0.5,
            message="Assertion failed",
            error_type="AssertionError",
            stack_trace="Traceback...",
        )

        assert result.error_type == "AssertionError"
        assert result.stack_trace is not None


class TestGoldenSetRunnerInit:
    """Test GoldenSetRunner initialization."""

    def test_runner_creation(self):
        """GoldenSetRunner can be created."""
        runner = GoldenSetRunner()

        assert runner is not None

    def test_runner_with_test_directory(self):
        """Runner can be created with test directory."""
        runner = GoldenSetRunner(test_dir="/path/to/tests")

        assert runner.test_dir == "/path/to/tests"


class TestRunGoldenSet:
    """Test golden set execution."""

    def test_run_single_test(self):
        """Single test can be run."""
        runner = GoldenSetRunner()

        # Mock test execution
        result = runner.run_test("test_basic_rca")

        assert result is not None
        assert result.test_name == "test_basic_rca"

    def test_run_all_tests(self):
        """All golden set tests can be run."""
        runner = GoldenSetRunner()

        results = runner.run_all()

        assert results is not None
        assert isinstance(results, list)


class TestGetResultsSummary:
    """Test results summary generation."""

    def test_summary_includes_counts(self):
        """Summary includes test counts."""
        runner = GoldenSetRunner()

        results = [
            GoldenSetResult("test1", TestOutcome.PASSED, 1.0, "OK"),
            GoldenSetResult("test2", TestOutcome.FAILED, 0.5, "Failed"),
            GoldenSetResult("test3", TestOutcome.PASSED, 1.2, "OK"),
        ]

        summary = runner.get_summary(results)

        assert summary.total_tests == 3
        assert summary.passed_count == 2
        assert summary.failed_count == 1

    def test_summary_includes_duration(self):
        """Summary includes total duration."""
        runner = GoldenSetRunner()

        results = [
            GoldenSetResult("test1", TestOutcome.PASSED, 1.0, "OK"),
            GoldenSetResult("test2", TestOutcome.PASSED, 2.0, "OK"),
        ]

        summary = runner.get_summary(results)

        assert summary.total_duration >= 3.0


class TestFilterResults:
    """Test result filtering."""

    def test_filter_by_outcome(self):
        """Results can be filtered by outcome."""
        runner = GoldenSetRunner()

        results = [
            GoldenSetResult("test1", TestOutcome.PASSED, 1.0, "OK"),
            GoldenSetResult("test2", TestOutcome.FAILED, 0.5, "Failed"),
            GoldenSetResult("test3", TestOutcome.PASSED, 1.2, "OK"),
        ]

        passed = runner.filter_results(results, TestOutcome.PASSED)

        assert len(passed) == 2
        assert all(r.outcome == TestOutcome.PASSED for r in passed)

    def test_filter_by_pattern(self):
        """Results can be filtered by name pattern."""
        runner = GoldenSetRunner()

        results = [
            GoldenSetResult("test_rca_1", TestOutcome.PASSED, 1.0, "OK"),
            GoldenSetResult("test_perf_1", TestOutcome.PASSED, 1.0, "OK"),
            GoldenSetResult("test_rca_2", TestOutcome.PASSED, 1.0, "OK"),
        ]

        rca_tests = runner.filter_by_name(results, pattern="rca")

        assert len(rca_tests) == 2
        assert all("rca" in r.test_name for r in rca_tests)


class TestValidateGoldenSet:
    """Test golden set validation."""

    def test_validate_passing_rate(self):
        """Passing rate can be validated."""
        runner = GoldenSetRunner()

        results = [
            GoldenSetResult("test1", TestOutcome.PASSED, 1.0, "OK"),
            GoldenSetResult("test2", TestOutcome.PASSED, 1.0, "OK"),
            GoldenSetResult("test3", TestOutcome.FAILED, 0.5, "Failed"),
        ]

        is_valid = runner.validate_passing_rate(results, threshold=0.6)

        assert is_valid is True  # 2/3 = 66.6% > 60%

    def test_validate_fails_below_threshold(self):
        """Validation fails below threshold."""
        runner = GoldenSetRunner()

        results = [
            GoldenSetResult("test1", TestOutcome.PASSED, 1.0, "OK"),
            GoldenSetResult("test2", TestOutcome.FAILED, 0.5, "Failed"),
            GoldenSetResult("test3", TestOutcome.FAILED, 0.5, "Failed"),
        ]

        is_valid = runner.validate_passing_rate(results, threshold=0.7)

        assert is_valid is False  # 1/3 = 33.3% < 70%


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_results_list(self):
        """Empty results list is handled."""
        runner = GoldenSetRunner()

        summary = runner.get_summary([])

        assert summary.total_tests == 0
        assert summary.passed_count == 0

    def test_all_skipped_results(self):
        """All skipped results are handled."""
        runner = GoldenSetRunner()

        results = [
            GoldenSetResult("test1", TestOutcome.SKIPPED, 0, "Skipped"),
            GoldenSetResult("test2", TestOutcome.SKIPPED, 0, "Skipped"),
        ]

        summary = runner.get_summary(results)

        assert summary.skipped_count == 2
