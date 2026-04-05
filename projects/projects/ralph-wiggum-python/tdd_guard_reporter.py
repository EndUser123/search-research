"""
TDD Guard Pytest Reporter

Captures pytest test results for TDD Guard enforcement.

Based on tdd-guard-pytest from: https://github.com/nizos/tdd-guard

Installation:
    1. Put this file in your project root or tests/ directory
    2. Add to pytest.ini:
       [pytest]
       tdd_guard_project_root = /path/to/project
       tdd_guard_output_dir = .claude/tdd-guard/data

    Or add to pyproject.toml:
       [tool.pytest.ini_options]
       tdd_guard_project_root = "/path/to/project"
       tdd_guard_output_dir = ".claude/tdd-guard/data"
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.reports import TestReport


class TDDGuardReporter:
    """Pytest reporter that saves test results for TDD Guard."""

    def __init__(self, config: Config) -> None:
        """Initialize the reporter."""
        self.config = config
        self.project_root = Path.cwd()

        # Read configuration from pytest.ini or pyproject.toml
        self.project_root = Path(
            config.getoption("tdd_guard_project_root") or os.environ.get("TDD_GUARD_PROJECT_ROOT") or str(Path.cwd())
        )

        self.output_dir = Path(
            config.getoption("tdd_guard_output_dir") or os.environ.get("TDD_GUARD_OUTPUT_DIR") or ".claude/tdd-guard/data"
        )

        # Make output_dir relative to project_root if not absolute
        if not self.output_dir.is_absolute():
            self.output_dir = self.project_root / self.output_dir

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Test tracking
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.errors = 0

        # Test details
        self.test_results = []

    def pytest_collection_finish(self, session: object) -> None:
        """Called after test collection has finished."""
        self.total_tests = len(session.items) if hasattr(session, 'items') else 0

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Called when test report is available."""
        if report.when == "call":  # Only care about the actual test call
            test_name = report.nodeid

            result = {
                "name": test_name,
                "outcome": report.outcome,
                "duration": report.duration,
            }

            if report.outcome == "passed":
                self.passed_tests += 1
            elif report.outcome == "failed":
                self.failed_tests += 1
                if report.longrepr:
                    result["failure"] = str(report.longrepr)[:500]  # Truncate long errors
            elif report.outcome == "skipped":
                self.skipped_tests += 1

            self.test_results.append(result)

    def pytest_sessionfinish(self, session: object, exitstatus: int) -> None:
        """Called after test session finishes."""
        output_file = self.output_dir / "test.json"

        results = {
            "total": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "skipped": self.skipped_tests,
            "errors": self.errors,
            "hasFailures": self.failed_tests > 0,
            "hasTests": self.total_tests > 0,
            "tests": self.test_results[-20:],  # Last 20 tests
        }

        output_file.write_text(json.dumps(results, indent=2))

        # Also update TDD state
        tdd_state_file = self.project_root / ".claude" / "tdd-state.json"
        if results.get("hasFailures"):
            test_name = str(self.test_results[0].get("name", "")) if self.test_results else ""
            tdd_state = {"phase": "RED", "test_file": test_name, "last_check": "sessionfinish"}
        elif results.get("total", 0) > 0:
            test_name = str(self.test_results[0].get("name", "")) if self.test_results else ""
            tdd_state = {"phase": "GREEN", "test_file": test_name, "last_check": "sessionfinish"}
        else:
            tdd_state = {"phase": "IDLE", "test_file": None, "last_check": "sessionfinish"}

        tdd_state_file.parent.mkdir(parents=True, exist_ok=True)
        tdd_state_file.write_text(json.dumps(tdd_state, indent=2))


def pytest_configure(config: Config) -> None:
    """Register the reporter."""
    reporter = TDDGuardReporter(config)
    config.pluginmanager.register(reporter, "tdd-guard-reporter")


def pytest_addoption(parser):
    """Add pytest options."""
    group = parser.getgroup("tdd-guard", "TDD Guard Pytest Reporter")
    group.addoption(
        "--tdd-guard-project-root",
        action="store",
        dest="tdd_guard_project_root",
        help="Project root directory for TDD Guard"
    )
    group.addoption(
        "--tdd-guard-output-dir",
        action="store",
        dest="tdd_guard_output_dir",
        help="Output directory for TDD Guard test results"
    )
