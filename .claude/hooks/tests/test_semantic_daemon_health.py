#!/usr/bin/env python3
r"""
Tests for SessionStart_semantic_daemon.py health check warning behavior.

These tests verify that when _check_daemon_health() fails to connect to the daemon,
it prints a visible warning to stderr (not just debug logging).

Run: pytest P:\.claude\hooks\tests\test_semantic_daemon_health.py -v
"""

import sys
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parents[1]
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


@pytest.fixture
def fresh_module_state() -> Generator[None, None, None]:
    """
    Fixture to ensure fresh module state for each test.

    This removes the module from sys.modules to prevent state leakage
    between tests without using importlib.reload().
    """
    module_name = "SessionStart_semantic_daemon"
    # Remove before test
    sys.modules.pop(module_name, None)
    try:
        yield
    finally:
        # Remove after test
        sys.modules.pop(module_name, None)


class TestDaemonHealthCheckWarning:
    """Tests for daemon health check failure warning behavior."""

    def test_health_check_failure_warns_to_stderr(
        self, capsys, fresh_module_state
    ) -> None:
        """
        RED TEST: Verify that daemon health check failures print visible warning to stderr.

        Test that when _check_daemon_health() fails to connect to the daemon,
        it prints a visible warning message to stderr containing "Health check failed".

        Given: DaemonClient raises connection exception
        When: _check_daemon_health() is called
        Then: Warning message should be printed to stderr (not just logger.debug())

        Current behavior: Exception is silently logged with logger.debug()
        Expected behavior: Warning should be visible in stderr
        """
        # Arrange: Mock DaemonClient to raise exception
        mock_daemon_client_class = Mock(side_effect=Exception("Connection refused: Pipe not found"))

        # Patch the import at the point where _check_daemon_health imports it
        with patch("sys.path", [str(HOOKS_DIR)]):
            # Import the module with our patch in place
            import SessionStart_semantic_daemon as module

            # Patch the DaemonClient import inside the _check_daemon_health function
            with patch.object(module.sys, "path", [str(HOOKS_DIR), "P:/__csf/src"]):
                # Mock the daemons.daemon_client module
                mock_daemon_module = MagicMock()
                mock_daemon_module.DaemonClient = mock_daemon_client_class

                with patch.dict(sys.modules, {"daemons.daemon_client": mock_daemon_module}):
                    # Act: Call _check_daemon_health with mocked DaemonClient
                    module._check_daemon_health()

        # Get stderr output
        captured = capsys.readouterr()
        stderr_output = captured.err

        # Assert: Warning should be printed to stderr
        assert stderr_output != "", (
            f"Expected warning message in stderr when health check fails. "
            f"Current stderr output: {stderr_output!r}\n"
            f"Expected: Visible warning in stderr containing 'daemon health check failed' "
            f"or similar error message."
        )
        # Verify the stderr contains daemon/health related keywords
        stderr_lower = stderr_output.lower()
        assert "daemon" in stderr_lower or "health" in stderr_lower, (
            f"Expected stderr to contain 'daemon' or 'health' related keywords. "
            f"Got: {stderr_output!r}"
        )

    def test_health_check_failure_on_timeout(
        self, capsys, fresh_module_state
    ) -> None:
        """
        RED TEST: Verify that daemon health check timeout prints visible warning to stderr.

        Test that when _check_daemon_health() times out connecting to the daemon,
        it prints a visible warning message to stderr.

        Given: DaemonClient.is_daemon_alive() times out
        When: _check_daemon_health() is called
        Then: Warning message should be printed to stderr

        Current behavior: Timeout exception is silently logged with logger.debug()
        Expected behavior: Warning should be visible in stderr
        """
        # Arrange: Mock DaemonClient to raise timeout exception
        mock_client = Mock()
        mock_client.is_daemon_alive.side_effect = TimeoutError("Health check timeout after 2.0s")
        mock_daemon_client_class = Mock(return_value=mock_client)

        # Import the module
        import SessionStart_semantic_daemon as module

        # Mock the daemons.daemon_client module
        mock_daemon_module = MagicMock()
        mock_daemon_module.DaemonClient = mock_daemon_client_class

        with patch.dict(sys.modules, {"daemons.daemon_client": mock_daemon_module}):
            # Act: Call _check_daemon_health with mocked DaemonClient
            module._check_daemon_health()

        # Get stderr output
        captured = capsys.readouterr()
        stderr_output = captured.err

        # Assert: Warning should be printed to stderr
        assert "timeout" in stderr_output.lower() or \
               "health check" in stderr_output.lower() or \
               "daemon" in stderr_output.lower(), (
            f"Expected timeout warning message in stderr. "
            f"Current stderr output: {stderr_output!r}\n"
            f"Current behavior: Timeout exception is only logged via logger.debug()"
        )

    def test_health_check_import_error_warns_to_stderr(
        self, capsys, fresh_module_state
    ) -> None:
        """
        RED TEST: Verify that import errors during health check print visible warning to stderr.

        Test that when _check_daemon_health() fails to import DaemonClient,
        it prints a visible warning message to stderr.

        Given: DaemonClient import fails
        When: _check_daemon_health() is called
        Then: Warning message should be printed to stderr

        Current behavior: ImportError is silently caught and logged via logger.debug()
        Expected behavior: Warning should be visible in stderr
        """
        # Import the module
        import SessionStart_semantic_daemon as module

        # Mock the daemons.daemon_client module to raise ImportError on access
        mock_daemon_module = MagicMock()
        mock_daemon_module.DaemonClient = side_effect = ImportError("No module named 'daemons.daemon_client'")

        with patch.dict(sys.modules, {"daemons.daemon_client": mock_daemon_module}):
            # Act: Call _check_daemon_health with failing DaemonClient import
            module._check_daemon_health()

        # Get stderr output
        captured = capsys.readouterr()
        stderr_output = captured.err

        # Assert: Warning should be printed to stderr
        assert "health check" in stderr_output.lower() or \
               "daemon" in stderr_output.lower() or \
               "warning" in stderr_output.lower(), (
            f"Expected warning message in stderr when DaemonClient import fails. "
            f"Current stderr output: {stderr_output!r}\n"
            f"Current behavior: Import errors are silently caught and logged via logger.debug()"
        )


class TestDaemonHealthCheckSuccess:
    """Tests for daemon health check success behavior (sanity checks)."""

    def test_health_check_success_no_warning(
        self, capsys, fresh_module_state
    ) -> None:
        """
        Verify that successful health check does NOT print warning to stderr.

        Given: DaemonClient.is_daemon_alive() returns True
        When: _check_daemon_health() is called
        Then: No warning should be printed to stderr (only status info)

        This is a sanity check to ensure we don't break the success case.
        """
        # Arrange: Mock successful health check
        mock_client = Mock()
        mock_client.is_daemon_alive = Mock(return_value=True)
        mock_daemon_client_class = Mock(return_value=mock_client)

        # Import the module
        import SessionStart_semantic_daemon as module

        # Mock the daemons.daemon_client module
        mock_daemon_module = MagicMock()
        mock_daemon_module.DaemonClient = mock_daemon_client_class

        with patch.dict(sys.modules, {"daemons.daemon_client": mock_daemon_module}):
            # Act: Call _check_daemon_health with successful health check
            module._check_daemon_health()

        # Get stderr output
        captured = capsys.readouterr()
        stderr_output = captured.err

        # Assert: Should show health status, not warning
        assert "daemon is alive" in stderr_output.lower() or \
               "✓" in stderr_output, (
            f"Expected health status message in stderr on success. "
            f"Current stderr output: {stderr_output!r}"
        )

        # Should NOT contain warning indicators
        assert "warning" not in stderr_output.lower() or \
               "health check failed" not in stderr_output, (
            f"Success case should not contain warning messages. "
            f"Current stderr output: {stderr_output!r}"
        )
