"""Root pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def test_artifacts_dir():
    """Return path to test artifacts config/dir."""
    return Path("tests/test_artifacts")


# Hypothesis Configuration
try:
    from hypothesis import settings

    settings.register_profile("ci", max_examples=5000, deadline=5000)
    settings.register_profile("dev", max_examples=100, deadline=500)
    settings.load_profile("dev")
except ImportError:
    pass


@pytest.fixture
def triage_scorer():
    """TriageScorer instance for testing."""
    from core_tools import get_scorer

    return get_scorer()


@pytest.fixture
def spec_validator(tmp_path):
    """SpecValidator instance for testing."""
    from core_tools import get_validator

    spec_file = tmp_path / "specify.md"
    impl_dir = tmp_path / "src"
    impl_dir.mkdir(parents=True, exist_ok=True)

    # Sample spec
    spec_text = "# Spec\n\n- User can login\n- Email validation works\n"
    spec_file.write_text(spec_text)
    return get_validator(spec_file, impl_dir)
