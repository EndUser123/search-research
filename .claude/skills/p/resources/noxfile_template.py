import os

import nox

# Environment configuration
VALIDATIONS_PATH = os.getenv("VALIDATIONS_PATH", "P:/__csf/scripts/validations")
TESTS_PATH = os.getenv("TESTS_PATH", "P:/tests")

# Define sessions
nox.options.sessions = ["sanity", "coverage", "security"]


@nox.session(python=["3.11"])
def sanity(session):
    """Run smoke tests and validations."""
    session.install("pytest", "pytest-rerunfailures")
    session.run("python", f"{VALIDATIONS_PATH}/validate_config.py", external=True)
    session.run(
        "pytest",
        f"{TESTS_PATH}/test_smoke.py",
        "--reruns",
        "2",
        "--reruns-delay",
        "1",
        external=True,
    )
    session.run("python", f"{VALIDATIONS_PATH}/validate_imports.py", external=True)


@nox.session
def coverage(session):
    """Check test coverage."""
    session.install("pytest", "pytest-cov", "pytest-rerunfailures")
    session.run(
        "pytest", "--cov=src", "--cov-fail-under=80", "--reruns", "2", external=True
    )


@nox.session
def security(session):
    """Run security scan with Bandit."""
    session.install("bandit")
    session.run("bandit", "-r", "src/", "-ll", external=True)


@nox.session
def fuzz(session):
    """Run property-based tests with Hypothesis."""
    session.install("hypothesis", "pytest")
    session.run("pytest", "-m", "hypothesis", external=True)


@nox.session
def schema_fuzz(session):
    """Fuzz API with Schemathesis."""
    session.install("schemathesis")
    session.run("st", "run", "http://localhost:8000/openapi.json", external=True)


@nox.session
def stress(session):
    """Run load tests with Locust."""
    session.install("locust")
    session.run(
        "locust",
        "--headless",
        "-u",
        "10",
        "-r",
        "1",
        "--run-time",
        "30s",
        external=True,
    )
