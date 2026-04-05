"""
Test Runner and Validation Utilities
======================================

Comprehensive test runner for the Enhanced Anti-Deception Architecture
with reporting, performance analysis, and validation utilities.
"""

import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", ".claude", "hooks")
)
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "__csf", "lib")
)


@dataclass
class TestResult:
    """Test result data structure."""

    test_name: str
    status: str  # 'passed', 'failed', 'skipped', 'error'
    duration: float
    error_message: str | None = None
    performance_metrics: dict[str, Any] | None = None
    evidence_generated: list[str] | None = None


@dataclass
class TestSuiteReport:
    """Complete test suite report."""

    suite_name: str
    execution_time: float
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    test_results: list[TestResult]
    performance_summary: dict[str, Any]
    coverage_metrics: dict[str, float] | None = None
    timestamp: str = ""


class EnhancedTestRunner:
    """Enhanced test runner with performance monitoring and validation."""

    def __init__(self, test_directory: str = None):
        """Initialize test runner."""
        self.test_directory = test_directory or os.path.dirname(__file__)
        self.results: list[TestResult] = []
        self.start_time: float | None = None
        self.end_time: float | None = None

    def run_unit_tests(self) -> TestSuiteReport:
        """Run all unit tests."""
        print("Running Unit Tests...")
        print("=" * 50)

        unit_test_dir = Path(self.test_directory) / "unit_tests"
        if not unit_test_dir.exists():
            return self._create_empty_report(
                "Unit Tests", "Unit test directory not found"
            )

        return self._run_pytest_suite(str(unit_test_dir), "Unit Tests")

    def run_integration_tests(self) -> TestSuiteReport:
        """Run all integration tests."""
        print("Running Integration Tests...")
        print("=" * 50)

        integration_test_dir = Path(self.test_directory) / "integration_tests"
        if not integration_test_dir.exists():
            return self._create_empty_report(
                "Integration Tests", "Integration test directory not found"
            )

        return self._run_pytest_suite(str(integration_test_dir), "Integration Tests")

    def run_performance_tests(self) -> TestSuiteReport:
        """Run all performance tests."""
        print("Running Performance Tests...")
        print("=" * 50)

        performance_test_dir = Path(self.test_directory) / "performance_tests"
        if not performance_test_dir.exists():
            return self._create_empty_report(
                "Performance Tests", "Performance test directory not found"
            )

        return self._run_pytest_suite(str(performance_test_dir), "Performance Tests")

    def run_scenario_tests(self) -> TestSuiteReport:
        """Run all scenario tests."""
        print("Running Scenario Tests...")
        print("=" * 50)

        scenario_test_dir = Path(self.test_directory) / "scenario_tests"
        if not scenario_test_dir.exists():
            return self._create_empty_report(
                "Scenario Tests", "Scenario test directory not found"
            )

        return self._run_pytest_suite(str(scenario_test_dir), "Scenario Tests")

    def run_all_tests(self) -> dict[str, TestSuiteReport]:
        """Run all test suites."""
        print("Running Complete Enhanced Anti-Deception Test Suite")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        reports = {}

        # Run each test suite
        test_suites = [
            ("unit", self.run_unit_tests),
            ("integration", self.run_integration_tests),
            ("performance", self.run_performance_tests),
            ("scenario", self.run_scenario_tests),
        ]

        for suite_name, runner in test_suites:
            try:
                report = runner()
                reports[suite_name] = report
                print(f"\n{suite_name.title()} Tests completed:")
                print(
                    f"   Total: {report.total_tests}, Passed: {report.passed}, Failed: {report.failed}"
                )
                if report.failed > 0:
                    print(f"   FAILED: {report.failed} test(s) failed")
                print()
            except Exception as e:
                print(f"Error running {suite_name} tests: {e}")
                reports[suite_name] = self._create_empty_report(
                    f"{suite_name.title()} Tests", str(e)
                )

        return reports

    def _run_pytest_suite(self, test_path: str, suite_name: str) -> TestSuiteReport:
        """Run pytest suite and collect results."""
        start_time = time.time()

        # pytest command with JSON reporting
        pytest_args = [
            sys.executable,
            "-m",
            "pytest",
            test_path,
            "--verbose",
            "--tb=short",
            "--json-report",
            f"--json-report-file={test_path}/report.json",
        ]

        try:
            # Run pytest
            result = subprocess.run(
                pytest_args,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Parse JSON report if available
            report_file = Path(test_path) / "report.json"
            if report_file.exists():
                with open(report_file) as f:
                    json_report = json.load(f)
                return self._parse_pytest_report(
                    json_report, suite_name, time.time() - start_time
                )
            else:
                # Fallback parsing from stdout
                return self._parse_pytest_output(
                    result.stdout, suite_name, time.time() - start_time
                )

        except subprocess.TimeoutExpired:
            return self._create_timeout_report(suite_name, time.time() - start_time)
        except Exception as e:
            return self._create_error_report(
                suite_name, str(e), time.time() - start_time
            )

    def _parse_pytest_report(
        self, json_report: dict[str, Any], suite_name: str, duration: float
    ) -> TestSuiteReport:
        """Parse pytest JSON report."""
        summary = json_report.get("summary", {})
        tests = json_report.get("tests", [])

        test_results = []
        for test in tests:
            test_result = TestResult(
                test_name=test.get("nodeid", "unknown"),
                status="passed" if test.get("outcome") == "passed" else "failed",
                duration=test.get("duration", 0.0),
                error_message=test.get("call", {}).get("longrepr")
                if test.get("outcome") != "passed"
                else None,
            )
            test_results.append(test_result)

        performance_summary = self._calculate_performance_metrics(test_results)

        return TestSuiteReport(
            suite_name=suite_name,
            execution_time=duration,
            total_tests=summary.get("total", len(tests)),
            passed=summary.get("passed", 0),
            failed=summary.get("failed", 0),
            skipped=summary.get("skipped", 0),
            errors=summary.get("error", 0),
            test_results=test_results,
            performance_summary=performance_summary,
            timestamp=datetime.now().isoformat(),
        )

    def _parse_pytest_output(
        self, stdout: str, suite_name: str, duration: float
    ) -> TestSuiteReport:
        """Parse pytest output when JSON report not available."""
        lines = stdout.split("\n")

        # Simple parsing logic
        total_tests = 0
        passed = 0
        failed = 0
        skipped = 0
        errors = 0

        for line in lines:
            if " passed" in line and " failed" in line:
                # Parse summary line like "5 passed, 2 failed in 1.23s"
                parts = line.split()[0:4]
                for i, part in enumerate(parts):
                    if part.isdigit() and i + 1 < len(parts):
                        count = int(part)
                        if "passed" in parts[i + 1]:
                            passed = count
                        elif "failed" in parts[i + 1]:
                            failed = count
                        elif "skipped" in parts[i + 1]:
                            skipped = count
                        elif "error" in parts[i + 1]:
                            errors = count
                total_tests = passed + failed + skipped + errors
                break

        return TestSuiteReport(
            suite_name=suite_name,
            execution_time=duration,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            test_results=[],
            performance_summary={},
            timestamp=datetime.now().isoformat(),
        )

    def _calculate_performance_metrics(
        self, test_results: list[TestResult]
    ) -> dict[str, Any]:
        """Calculate performance metrics from test results."""
        if not test_results:
            return {}

        durations = [result.duration for result in test_results if result.duration > 0]

        return {
            "total_test_time": sum(durations),
            "average_test_time": sum(durations) / len(durations) if durations else 0,
            "slowest_test": max(durations) if durations else 0,
            "fastest_test": min(durations) if durations else 0,
            "tests_under_1s": len([d for d in durations if d < 1.0]),
            "tests_over_2s": len([d for d in durations if d > 2.0]),
        }

    def _create_empty_report(self, suite_name: str, reason: str) -> TestSuiteReport:
        """Create empty report when tests can't run."""
        return TestSuiteReport(
            suite_name=suite_name,
            execution_time=0.0,
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=0,
            test_results=[],
            performance_summary={"error": reason},
            timestamp=datetime.now().isoformat(),
        )

    def _create_timeout_report(
        self, suite_name: str, duration: float
    ) -> TestSuiteReport:
        """Create timeout report."""
        return TestSuiteReport(
            suite_name=suite_name,
            execution_time=duration,
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=1,
            test_results=[
                TestResult(
                    test_name="test_suite_timeout",
                    status="error",
                    duration=duration,
                    error_message="Test suite timed out after 5 minutes",
                )
            ],
            performance_summary={"timeout": True},
            timestamp=datetime.now().isoformat(),
        )

    def _create_error_report(
        self, suite_name: str, error: str, duration: float
    ) -> TestSuiteReport:
        """Create error report."""
        return TestSuiteReport(
            suite_name=suite_name,
            execution_time=duration,
            total_tests=0,
            passed=0,
            failed=0,
            skipped=0,
            errors=1,
            test_results=[
                TestResult(
                    test_name="test_suite_error",
                    status="error",
                    duration=duration,
                    error_message=error,
                )
            ],
            performance_summary={"error": error},
            timestamp=datetime.now().isoformat(),
        )


class TestReporter:
    """Generate comprehensive test reports."""

    @staticmethod
    def generate_console_report(reports: dict[str, TestSuiteReport]) -> str:
        """Generate console-friendly test report."""
        report_lines = []

        # Header
        report_lines.append("Enhanced Anti-Deception Architecture Test Report")
        report_lines.append("=" * 60)
        report_lines.append(
            f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report_lines.append("")

        # Summary
        total_tests = sum(report.total_tests for report in reports.values())
        total_passed = sum(report.passed for report in reports.values())
        total_failed = sum(report.failed for report in reports.values())
        total_skipped = sum(report.skipped for report in reports.values())
        total_errors = sum(report.errors for report in reports.values())
        total_time = sum(report.execution_time for report in reports.values())

        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        report_lines.append("OVERALL SUMMARY")
        report_lines.append("-" * 20)
        report_lines.append(f"Total Tests:     {total_tests}")
        report_lines.append(f"Passed:          {total_passed} ({success_rate:.1f}%)")
        report_lines.append(f"Failed:          {total_failed}")
        report_lines.append(f"Skipped:         {total_skipped}")
        report_lines.append(f"Errors:          {total_errors}")
        report_lines.append(f"Total Time:      {total_time:.2f}s")
        report_lines.append("")

        # Suite details
        report_lines.append("SUITE DETAILS")
        report_lines.append("-" * 20)

        for suite_name, report in reports.items():
            status = "PASS" if report.failed == 0 and report.errors == 0 else "FAIL"
            report_lines.append(f"{status} {suite_name.title()}:")
            report_lines.append(
                f"   Tests: {report.total_tests}, Passed: {report.passed}, Failed: {report.failed}"
            )
            if report.failed > 0 or report.errors > 0:
                report_lines.append("   Issues detected - see detailed report")
            report_lines.append("")

        # Performance summary
        report_lines.append("PERFORMANCE SUMMARY")
        report_lines.append("-" * 25)

        for suite_name, report in reports.items():
            perf = report.performance_summary
            if perf and "total_test_time" in perf:
                report_lines.append(f"{suite_name.title()}:")
                report_lines.append(
                    f"   Average test time: {perf.get('average_test_time', 0):.3f}s"
                )
                report_lines.append(
                    f"   Slowest test: {perf.get('slowest_test', 0):.3f}s"
                )
                if perf.get("tests_over_2s", 0) > 0:
                    report_lines.append(
                        f"   WARNING: {perf['tests_over_2s']} tests over 2s"
                    )
                report_lines.append("")

        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 18)

        if total_failed > 0:
            report_lines.append("• Fix failing tests before deploying to production")

        slow_suites = [
            name for name, report in reports.items() if report.execution_time > 10
        ]
        if slow_suites:
            report_lines.append(
                f"• Consider optimizing slow test suites: {', '.join(slow_suites)}"
            )

        if total_errors > 0:
            report_lines.append("• Investigate and fix test execution errors")

        if success_rate >= 95:
            report_lines.append("Excellent test suite health!")
        elif success_rate >= 80:
            report_lines.append("Good test suite health")
        else:
            report_lines.append("Test suite needs improvement")

        return "\n".join(report_lines)

    @staticmethod
    def generate_json_report(
        reports: dict[str, TestSuiteReport], output_path: str = None
    ) -> str:
        """Generate JSON test report."""
        report_data = {
            "summary": {
                "total_tests": sum(r.total_tests for r in reports.values()),
                "total_passed": sum(r.passed for r in reports.values()),
                "total_failed": sum(r.failed for r in reports.values()),
                "total_skipped": sum(r.skipped for r in reports.values()),
                "total_errors": sum(r.errors for r in reports.values()),
                "total_execution_time": sum(r.execution_time for r in reports.values()),
                "success_rate": (
                    sum(r.passed for r in reports.values())
                    / sum(r.total_tests for r in reports.values())
                    * 100
                )
                if sum(r.total_tests for r in reports.values()) > 0
                else 0,
            },
            "suites": {name: asdict(report) for name, report in reports.items()},
            "generated_at": datetime.now().isoformat(),
        }

        json_report = json.dumps(report_data, indent=2)

        if output_path:
            with open(output_path, "w") as f:
                f.write(json_report)

        return json_report

    @staticmethod
    def validate_performance_requirements(
        reports: dict[str, TestSuiteReport],
    ) -> dict[str, Any]:
        """Validate that performance requirements are met."""
        validation_results = {"validation_passed": True, "issues": [], "metrics": {}}

        # Check performance tests specifically
        if "performance" in reports:
            perf_report = reports["performance"]

            # Check sub-2 second validation requirement
            for test_result in perf_report.test_results:
                if test_result.duration > 2.0:
                    validation_results["validation_passed"] = False
                    validation_results["issues"].append(
                        {
                            "type": "performance_violation",
                            "test": test_result.test_name,
                            "duration": test_result.duration,
                            "limit": 2.0,
                            "description": f"Test exceeded 2 second limit by {test_result.duration - 2.0:.3f}s",
                        }
                    )

            # Check performance summary metrics
            perf_summary = perf_report.performance_summary
            if perf_summary:
                avg_time = perf_summary.get("average_test_time", 0)
                if avg_time > 1.0:
                    validation_results["issues"].append(
                        {
                            "type": "performance_warning",
                            "metric": "average_test_time",
                            "value": avg_time,
                            "description": f"Average test time ({avg_time:.3f}s) is above optimal",
                        }
                    )

                slow_tests = perf_summary.get("tests_over_2s", 0)
                if slow_tests > 0:
                    validation_results["issues"].append(
                        {
                            "type": "performance_warning",
                            "metric": "slow_tests",
                            "value": slow_tests,
                            "description": f"{slow_tests} tests exceeded 2 second limit",
                        }
                    )

        validation_results["metrics"] = {
            "total_test_suites": len(reports),
            "suites_with_failures": len([r for r in reports.values() if r.failed > 0]),
            "suites_with_errors": len([r for r in reports.values() if r.errors > 0]),
            "total_execution_time": sum(r.execution_time for r in reports.values()),
        }

        return validation_results


def main():
    """Main test runner entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enhanced Anti-Deception Architecture Test Runner"
    )
    parser.add_argument(
        "--suite",
        choices=["unit", "integration", "performance", "scenario", "all"],
        default="all",
        help="Test suite to run",
    )
    parser.add_argument("--output", help="Output directory for reports")
    parser.add_argument("--json-report", help="Path for JSON report file")
    parser.add_argument(
        "--validate-performance",
        action="store_true",
        help="Validate performance requirements",
    )

    args = parser.parse_args()

    # Initialize test runner
    runner = EnhancedTestRunner()

    # Run tests
    if args.suite == "all":
        reports = runner.run_all_tests()
    elif args.suite == "unit":
        reports = {"unit": runner.run_unit_tests()}
    elif args.suite == "integration":
        reports = {"integration": runner.run_integration_tests()}
    elif args.suite == "performance":
        reports = {"performance": runner.run_performance_tests()}
    elif args.suite == "scenario":
        reports = {"scenario": runner.run_scenario_tests()}

    # Generate reports
    console_report = TestReporter.generate_console_report(reports)
    print(console_report)

    # Generate JSON report if requested
    if args.json_report:
        json_report = TestReporter.generate_json_report(reports, args.json_report)
        print(f"\nJSON report saved to: {args.json_report}")

    # Validate performance if requested
    if args.validate_performance:
        validation = TestReporter.validate_performance_requirements(reports)
        print("\nPerformance Validation:")
        if validation["validation_passed"]:
            print("   PASS: All performance requirements met")
        else:
            print("   FAIL: Performance issues detected:")
            for issue in validation["issues"]:
                print(f"      • {issue['description']}")

    # Exit with appropriate code
    total_failed = sum(r.failed for r in reports.values())
    total_errors = sum(r.errors for r in reports.values())

    if total_failed > 0 or total_errors > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
