"""
Pytest configuration and fixtures for yt-fts tests.

This module provides common fixtures and test configuration.
"""

import gc
import os
import sys
from pathlib import Path

import pytest

# Add src directory to path for imports
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Store original environment variables for restoration
_ORIG_ENV = os.environ.copy()


@pytest.fixture(autouse=True)
def load_display_plugins():
    """
    Automatically load built-in display plugins for all tests.

    This fixture runs automatically for all tests to ensure the
    plugin registry is populated before any test code runs.
    """
    from yt_fts.display import load_builtin_plugins
    load_builtin_plugins()
    yield
    # Reset global state after each test to prevent isolation issues
    _reset_global_state()


def _reset_global_state():
    """
    Reset global module state between tests to prevent test pollution.

    This addresses isolation issues where tests modify global variables
    that affect subsequent tests. Called automatically after each test.
    """
    # Restore environment variables (especially YT_FTS_DB_PATH)
    for key in list(os.environ.keys()):
        if key.startswith("YT_FTS_") and key not in _ORIG_ENV:
            del os.environ[key]
        elif key in _ORIG_ENV:
            os.environ[key] = _ORIG_ENV[key]

    try:
        # Reset database index flag so tests can create their own indexes
        import yt_fts.db.infra as infra_module
        infra_module._indexes_enabled = False
        infra_module._wal_mode_enabled = False
        # Close any cached database connections
        if hasattr(infra_module, '_connection_pool'):
            for conn in infra_module._connection_pool.values():
                try:
                    conn.close()
                except:
                    pass
            infra_module._connection_pool.clear()
    except (ImportError, AttributeError):
        pass

    try:
        # Clear any cached channel data
        import yt_fts.download.unified_discovery as discovery
        if hasattr(discovery, '_discovery_cache'):
            discovery._discovery_cache.clear()
    except (ImportError, AttributeError):
        pass

    try:
        # Disable telemetry to prevent database lock issues during tests
        import yt_fts.debug.telemetry as telemetry
        telemetry.set_telemetry_enabled(False)
    except (ImportError, AttributeError):
        pass

    # Force garbage collection to clean up any lingering database connections
    # Note: On Windows, gc.collect() can hang due to SQLite file locks
    # We use a gentler approach with just generation 0 collection
    try:
        gc.collect(0)  # Only collect young objects, avoid full collection that can hang
    except:
        pass  # If gc fails, continue anyway - connections will be cleaned up eventually


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
