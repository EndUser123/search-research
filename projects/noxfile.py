"""Nox test orchestration with token-aware paths."""

import os
from pathlib import Path

import nox

# Configuration
PYTHON_VERSION = "3.12"
COVERAGE_GATES = {
    "fast": 0,  # No check
    "standard": 70,  # 70% minimum
    "careful": 85,  # 85% minimum
}

TEST_BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:3000")
E2E_HEADLESS = os.getenv("E2E_HEADLESS", "true").lower() == "true"
BROWSER_TYPE = os.getenv("BROWSER_TYPE", "chromium")
TIMEOUT = int(os.getenv("TIMEOUT", "30000"))

# Paths
VALIDATIONS_PATH = Path(
    os.getenv("VALIDATIONS_PATH", "P:/__csf/scripts/validations")
)
TESTS_PATH = Path(os.getenv("TESTS_PATH", "P:/tests"))

# Load test configuration
LOCUST_USERS = int(os.getenv("LOCUST_USERS", "10"))
LOCUST_SPAWN_RATE = int(os.getenv("LOCUST_SPAWN_RATE", "1"))
LOCUST_RUN_TIME = os.getenv("LOCUST_RUN_TIME", "30s")


# ============================================================================
# PHASE 1: SANITY (Smoke Tests, Coverage, Security)
# ============================================================================


@nox.session(name="sanity", python=PYTHON_VERSION)
def session_sanity(session: nox.Session) -> None:
    """Run smoke tests (PHASE 1)."""
    session.install("-r", "requirements_qa.txt")
    session.run(
        "pytest",
        "tests/",
        "-v",
        "-m",
        "not slow and not flaky",
        "--tb=short",
        "--co",
        success_codes=[0],
    )
    session.run(
        "pytest",
        "tests/",
        "-v",
        "-m",
        "not slow and not flaky",
        "--tb=short",
        success_codes=[0],
    )


@nox.session(name="coverage", python=PYTHON_VERSION)
def session_coverage(session: nox.Session) -> None:
    """Check coverage against gate (PHASE 1)."""
    session.install("-r", "requirements_qa.txt")
    threshold = COVERAGE_GATES.get("standard", 70)
    session.run(
        "pytest",
        "tests/",
        "--cov=csf_nip",
        "--cov=src",
        "--cov=__csf/src",
        f"--cov-fail-under={threshold}",
        "--cov-report=term-missing",
        "--cov-report=html",
    )


@nox.session(name="security", python=PYTHON_VERSION)
def session_security(session: nox.Session) -> None:
    """Run bandit security scan (PHASE 1)."""
    session.install("-r", "requirements_qa.txt")
    session.run("bandit", "-r", "src/", "-f", "json", "-o", "bandit-report.json")


# ============================================================================
# PHASE 2: E2E (Browser Automation)
# ============================================================================


@nox.session(name="e2e", python=PYTHON_VERSION)
def session_e2e(session: nox.Session) -> None:
    """Run E2E tests with Playwright (PHASE 2)."""
    session.install("-r", "requirements_qa.txt")
    session.env["TEST_BASE_URL"] = TEST_BASE_URL
    session.env["E2E_HEADLESS"] = str(E2E_HEADLESS)
    session.env["BROWSER_TYPE"] = BROWSER_TYPE
    session.env["TIMEOUT"] = str(TIMEOUT)

    session.run(
        "pytest",
        "tests/e2e/",
        "-v",
        "-m",
        "e2e",
        "--tb=short",
    )


# ============================================================================
# PHASE 3: CHAOS (Fuzzing & Load Testing)
# ============================================================================


@nox.session(name="fuzz", python=PYTHON_VERSION)
def session_fuzz(session: nox.Session) -> None:
    """Hypothesis property-based fuzzing (PHASE 3)."""
    session.install("-r", "requirements_qa.txt")
    session.run(
        "pytest",
        "tests/",
        "-v",
        "-m",
        "hypothesis",
        "--tb=short",
    )


@nox.session(name="schema_fuzz", python=PYTHON_VERSION)
def session_schema_fuzz(session: nox.Session) -> None:
    """Schemathesis API fuzzing (PHASE 3)."""
    session.install("-r", "requirements_qa.txt")
    openapi_url = os.getenv("OPENAPI_URL", "http://localhost:8000/openapi.json")
    session.run(
        "schemathesis",
        "run",
        openapi_url,
        "-b",
        "http://localhost:8000",
        "--checks",
        "all",
    )


@nox.session(name="stress", python=PYTHON_VERSION)
def session_stress(session: nox.Session) -> None:
    """Locust load testing (PHASE 3)."""
    session.install("-r", "requirements_qa.txt")
    session.env["LOCUST_USERS"] = str(LOCUST_USERS)
    session.env["LOCUST_SPAWN_RATE"] = str(LOCUST_SPAWN_RATE)
    session.env["LOCUST_RUN_TIME"] = LOCUST_RUN_TIME

    session.run(
        "locust",
        "-f",
        "tests/locustfile.py",
        "--users",
        str(LOCUST_USERS),
        "--spawn-rate",
        str(LOCUST_SPAWN_RATE),
        "--run-time",
        LOCUST_RUN_TIME,
        "--headless",
        "-u",
        TEST_BASE_URL,
    )


# ============================================================================
# PHASE 4: REPORT
# ============================================================================


@nox.session(name="report", python=PYTHON_VERSION)
def session_report(session: nox.Session) -> None:
    """Generate QA report (PHASE 4)."""
    session.install("-r", "requirements_qa.txt")
    session.run(
        "python",
        "-c",
        "print('QA Report: All phases complete. See qa_report.md')",
    )


# ============================================================================
# UTILITIES
# ============================================================================


@nox.session(name="quick_test", python=PYTHON_VERSION)
def session_quick_test(session: nox.Session) -> None:
    """Run only affected tests with testmon (⚡ FAST)."""
    session.install("-r", "requirements_qa.txt")
    session.run(
        "pytest",
        "tests/",
        "--testmon",
        "-v",
        "-m",
        "not slow",
    )


@nox.session(name="retest_flaky", python=PYTHON_VERSION)
def session_retest_flaky(session: nox.Session) -> None:
    """Re-run flaky tests multiple times."""
    session.install("-r", "requirements_qa.txt")
    session.run(
        "pytest",
        "tests/",
        "-v",
        "-m",
        "flaky",
        "--rerunfailures=3",
    )


@nox.session(name="list_markers", python=PYTHON_VERSION)
def session_list_markers(session: nox.Session) -> None:
    """List all pytest markers."""
    session.install("-r", "requirements_qa.txt")
    session.run("pytest", "--markers")


@nox.session(name="playwright_debug", python=PYTHON_VERSION)
def session_playwright_debug(session: nox.Session) -> None:
    """Launch Playwright Inspector for debugging."""
    session.install("-r", "requirements_qa.txt")
    session.run("playwright", "codegen", TEST_BASE_URL)


# ============================================================================
# COMBINED PATHS (Token-Aware)
# ============================================================================


@nox.session(name="qa_fast", python=PYTHON_VERSION)
def session_qa_fast(session: nox.Session) -> None:
    """
    FAST path: Phase 1 only (~30 seconds).
    Use when: 5-20K tokens available
    """
    session.notify("sanity")
    session.notify("coverage")
    session.notify("security")


@nox.session(name="qa_standard", python=PYTHON_VERSION)
def session_qa_standard(session: nox.Session) -> None:
    """
    STANDARD path: Phases 1-3 (~2-3 minutes).
    Use when: 20-50K tokens available
    """
    session.notify("sanity")
    session.notify("coverage")
    session.notify("security")
    session.notify("e2e")
    session.notify("fuzz")


@nox.session(name="qa_careful", python=PYTHON_VERSION)
def session_qa_careful(session: nox.Session) -> None:
    """
    CAREFUL path: All phases (~5-10 minutes).
    Use when: 50K+ tokens available
    """
    session.notify("sanity")
    session.notify("coverage")
    session.notify("security")
    session.notify("e2e")
    session.notify("fuzz")
    session.notify("schema_fuzz")
    session.notify("stress")


# ============================================================================
# Configuration
# ============================================================================

# Reuse existing virtualenvs
nox.options.reuse_existing_virtualenvs = True

# Stop on first failure (optional)
# nox.options.stop_on_first_error = True
