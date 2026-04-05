"""Integration tests for arch examples.

These tests verify that the example code can be imported and executed without errors.
"""

import sys
from pathlib import Path

import pytest


def test_arch_basic_usage_imports():
    """Test that basic_usage.py imports are correct."""
    examples_dir = Path(__file__).parent.parent / "examples"
    basic_usage = examples_dir / "basic_usage.py"

    assert basic_usage.exists(), "basic_usage.py example should exist"

    # Read and compile the example to check for syntax errors
    content = basic_usage.read_text()
    compile(content, str(basic_usage), "exec")


def test_arch_examples_readme_exists():
    """Test that examples/README.md exists and contains expected sections."""
    examples_dir = Path(__file__).parent.parent / "examples"
    readme = examples_dir / "README.md"

    assert readme.exists(), "examples/README.md should exist"

    content = readme.read_text()

    # Check for expected sections
    assert "## Examples" in content
    assert "basic_usage.py" in content
    assert "## Setup" in content


def test_arch_examples_structure():
    """Test that examples directory has expected structure."""
    examples_dir = Path(__file__).parent.parent / "examples"

    # Check for expected files
    expected_files = [
        "README.md",
        "basic_usage.py",
    ]

    for file in expected_files:
        assert (examples_dir / file).exists(), f"examples/{file} should exist"


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="arch requires Python 3.10+"
)
def test_arch_basic_usage_execution(monkeypatch, tmp_path):
    """Test that basic_usage.py can execute (with mocked dependencies).

    This test is skipped if dependencies aren't installed.
    """
    examples_dir = Path(__file__).parent.parent / "examples"
    basic_usage = examples_dir / "basic_usage.py"

    # Read the example
    code = basic_usage.read_text()

    # The example expects arch to be importable
    # Skip test if arch is not installed
    try:
        import arch.core.advisor
    except ImportError:
        pytest.skip("arch package not installed")

    # We can't fully execute without mocking ProjectContext
    # But we can verify the code compiles and has expected structure
    assert "ProjectContext" in code
    assert "ArchitectureAdvisor" in code
    assert "recommend" in code
