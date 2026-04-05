"""
Pytest configuration and fixtures for yt-fts tests.

This module provides common fixtures and test configuration.
"""

import sys
from pathlib import Path

import pytest

# Add src directory to path for imports
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))


@pytest.fixture(autouse=True)
def load_display_plugins():
    """
    Automatically load built-in display plugins for all tests.

    This fixture runs automatically for all tests to ensure the
    plugin registry is populated before any test code runs.
    """
    from yt_fts.display import load_builtin_plugins
    load_builtin_plugins()


@pytest.fixture
def mock_console():
    """Provide a mock Rich console for testing."""
    from rich.console import Console
    from io import StringIO

    console = Console(
        width=80,
        force_terminal=True,
        file=StringIO(),
    )
    return console


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary database path for testing."""
    return tmp_path / "test_subtitles.db"
