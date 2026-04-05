"""Shared pytest fixtures for ai-cli tests.

This file contains fixtures that are shared across multiple test files.
Fixtures defined here are automatically discovered by pytest.
"""

import pytest


@pytest.fixture
def temp_dir(tmp_path):
    """
    Pytest fixture providing a temporary directory for testing.

    Uses pytest's built-in tmp_path fixture (autouse).
    Scope: function level (default).
    Returns: Path object to temporary directory.

    Usage:
        def test_example(temp_dir):
            test_file = temp_dir / "test.txt"
            test_file.write_text("content")
    """
    return tmp_path
