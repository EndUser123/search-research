"""
Tests for two-daemon architecture configuration system.

These tests verify the configuration system that supports separate dreaming and search daemons
with distinct mutex names, PID files, and configuration parameters.

Run with: pytest tests/test_two_daemon_architecture.py -v
"""

import pytest
from config.daemon_config import DAEMON_TYPES, get_daemon_config


class TestDaemonConfigStructure:
    """Tests for DAEMON_TYPES configuration structure."""

    def test_dreaming_config_exists(self):
        """
        Test that DAEMON_TYPES has a 'dreaming' key.

        Given: DAEMON_TYPES is defined
        When: Accessing DAEMON_TYPES
        Then: 'dreaming' key should exist
        """
        assert 'dreaming' in DAEMON_TYPES, "DAEMON_TYPES should have 'dreaming' key"

    def test_search_config_exists(self):
        """
        Test that DAEMON_TYPES has a 'search' key.

        Given: DAEMON_TYPES is defined
        When: Accessing DAEMON_TYPES
        Then: 'search' key should exist
        """
        assert 'search' in DAEMON_TYPES, "DAEMON_TYPES should have 'search' key"


class TestGetDaemonConfig:
    """Tests for get_daemon_config function."""

    def test_get_daemon_config_returns_dreaming_config(self):
        """
        Test that get_daemon_config returns correct config for dreaming daemon.

        Given: DAEMON_TYPES has 'dreaming' config
        When: Calling get_daemon_config('dreaming')
        Then: Should return dreaming configuration dict
        """
        config = get_daemon_config('dreaming')
        assert config is not None, "get_daemon_config('dreaming') should return a config"
        assert isinstance(config, dict), "Config should be a dictionary"
        assert 'mutex_name' in config, "Dreaming config should have 'mutex_name'"
        assert 'pid_file' in config, "Dreaming config should have 'pid_file'"

    def test_get_daemon_config_returns_search_config(self):
        """
        Test that get_daemon_config returns correct config for search daemon.

        Given: DAEMON_TYPES has 'search' config
        When: Calling get_daemon_config('search')
        Then: Should return search configuration dict
        """
        config = get_daemon_config('search')
        assert config is not None, "get_daemon_config('search') should return a config"
        assert isinstance(config, dict), "Config should be a dictionary"
        assert 'mutex_name' in config, "Search config should have 'mutex_name'"
        assert 'pid_file' in config, "Search config should have 'pid_file'"

    def test_get_daemon_config_raises_on_unknown_type(self):
        """
        Test that get_daemon_config raises ValueError for unknown daemon_type.

        Given: DAEMON_TYPES has 'dreaming' and 'search' configs
        When: Calling get_daemon_config with unknown daemon type
        Then: Should raise ValueError with descriptive message
        """
        with pytest.raises(ValueError) as exc_info:
            get_daemon_config('unknown_daemon')

        assert "Unknown daemon type" in str(exc_info.value), \
            "Error message should mention unknown daemon type"


class TestMutexConfiguration:
    """Tests for mutex name configuration."""

    def test_dreaming_mutex_name_is_correct(self):
        """
        Test that dreaming daemon config has correct mutex name.

        Given: Dreaming daemon configuration exists
        When: Accessing dreaming config's mutex_name
        Then: Should be "Global\\ClaudeInsightDaemon"
        """
        config = get_daemon_config('dreaming')
        assert config['mutex_name'] == "Global\\ClaudeInsightDaemon", \
            f"Dreaming mutex should be 'Global\\ClaudeInsightDaemon', got '{config.get('mutex_name')}'"

    def test_search_mutex_name_is_correct(self):
        """
        Test that search daemon config has correct mutex name.

        Given: Search daemon configuration exists
        When: Accessing search config's mutex_name
        Then: Should be "Global\\ClaudeSearchDaemon"
        """
        config = get_daemon_config('search')
        assert config['mutex_name'] == "Global\\ClaudeSearchDaemon", \
            f"Search mutex should be 'Global\\ClaudeSearchDaemon', got '{config.get('mutex_name')}'"

    def test_mutex_names_are_different(self):
        """
        Test that dreaming and search mutex names are different.

        Given: Both dreaming and search daemon configs exist
        When: Comparing their mutex_name values
        Then: They should be different strings
        """
        dreaming_config = get_daemon_config('dreaming')
        search_config = get_daemon_config('search')

        assert dreaming_config['mutex_name'] != search_config['mutex_name'], \
            "Dreaming and search daemons should have different mutex names"


class TestPidFileConfiguration:
    """Tests for PID file configuration."""

    def test_dreaming_pid_file_is_configured(self):
        """
        Test that dreaming daemon config has correct PID file.

        Given: Dreaming daemon configuration exists
        When: Accessing dreaming config's pid_file
        Then: Should end with "dreaming-daemon.pid"
        """
        config = get_daemon_config('dreaming')
        assert 'dreaming-daemon.pid' in config['pid_file'], \
            f"Dreaming PID file should contain 'dreaming-daemon.pid', got '{config.get('pid_file')}'"

    def test_search_pid_file_is_configured(self):
        """
        Test that search daemon config has correct PID file.

        Given: Search daemon configuration exists
        When: Accessing search config's pid_file
        Then: Should end with "search-daemon.pid"
        """
        config = get_daemon_config('search')
        assert 'search-daemon.pid' in config['pid_file'], \
            f"Search PID file should contain 'search-daemon.pid', got '{config.get('pid_file')}'"


class TestMutexParameterization:
    """Tests for configurable mutex names in dreaming_mutex (RED phase).

    These tests verify that acquire_singleton and _create_windows_mutex
    accept and use configurable mutex_name parameter.

    All tests MUST FAIL initially (parameter doesn't exist yet).
    """

    def test_acquire_singleton_accepts_mutex_name_param(self):
        """
        Test that acquire_singleton accepts mutex_name parameter.

        Given: acquire_singleton function exists
        When: Inspecting function signature
        Then: Should have mutex_name parameter with default value
        """
        import inspect

        from dreaming_mutex import acquire_singleton

        sig = inspect.signature(acquire_singleton)
        params = sig.parameters

        assert 'mutex_name' in params, \
            "acquire_singleton should have 'mutex_name' parameter"
        assert params['mutex_name'].default is not inspect.Parameter.empty, \
            "mutex_name should have a default value"

    def test_acquire_singleton_default_mutex_is_dreaming(self):
        """
        Test that acquire_singleton default mutex_name is dreaming daemon mutex.

        Given: acquire_singleton has mutex_name parameter
        When: Calling without mutex_name argument
        Then: Should use "Global\\ClaudeInsightDaemon" as default
        """
        import inspect

        from dreaming_mutex import acquire_singleton

        sig = inspect.signature(acquire_singleton)
        default_mutex = sig.parameters['mutex_name'].default

        assert default_mutex == "Global\\ClaudeInsightDaemon", \
            f"Default mutex_name should be 'Global\\ClaudeInsightDaemon', got '{default_mutex}'"

    def test_acquire_singleton_can_use_search_mutex(self):
        """
        Test that acquire_singleton can accept search daemon mutex name.

        Given: acquire_singleton has mutex_name parameter
        When: Passing search daemon mutex name
        Then: Should accept "Global\\ClaudeSearchDaemon" without error
        """
        import tempfile

        from dreaming_mutex import acquire_singleton

        # Use temp files for testing
        with tempfile.NamedTemporaryFile(suffix='.pid', delete=False) as tmp_pid:
            pid_file = tmp_pid.name

        try:
            # This should accept the parameter (will fail to acquire if already running)
            # We're just testing that the parameter is accepted
            success, msg = acquire_singleton(
                pid_file,
                mutex_name="Global\\ClaudeSearchDaemon",
                force=True
            )
            # We don't care about success/failure, just that it accepts the param
            assert isinstance(success, bool), "Should return success boolean"
        except TypeError as e:
            if "mutex_name" in str(e):
                pytest.fail(f"acquire_singleton should accept mutex_name parameter: {e}")
            raise
        finally:
            # Cleanup
            import os
            if os.path.exists(pid_file):
                os.unlink(pid_file)

    def test_acquire_singleton_passes_mutex_to_create_func(self):
        """
        Test that acquire_singleton passes mutex_name to _create_windows_mutex.

        Given: acquire_singleton called with custom mutex_name
        When: Function calls _create_windows_mutex
        Then: Should pass the provided mutex_name parameter

        This test verifies the integration between acquire_singleton and
        _create_windows_mutex functions.
        """
        import tempfile
        from unittest.mock import patch

        from dreaming_mutex import acquire_singleton

        with tempfile.NamedTemporaryFile(suffix='.pid', delete=False) as tmp_pid:
            pid_file = tmp_pid.name

        try:
            # Mock _create_windows_mutex to capture the mutex_name argument
            with patch('dreaming_mutex._create_windows_mutex') as mock_create:
                mock_create.return_value = (True, None, True)

                acquire_singleton(
                    pid_file,
                    mutex_name="Global\\TestMutex",
                    force=True
                )

                # Verify that _create_windows_mutex was called with the mutex_name
                mock_create.assert_called_once()
                call_args = mock_create.call_args

                # Check if mutex_name was passed (as positional or keyword argument)
                if 'mutex_name' in call_args.kwargs:
                    assert call_args.kwargs['mutex_name'] == "Global\\TestMutex", \
                        "Should pass mutex_name as keyword argument"
                elif len(call_args.args) > 0:
                    assert call_args.args[0] == "Global\\TestMutex", \
                        "Should pass mutex_name as positional argument"
                else:
                    pytest.fail("_create_windows_mutex not called with mutex_name argument")

        finally:
            import os
            if os.path.exists(pid_file):
                os.unlink(pid_file)

    def test_create_windows_mutex_accepts_mutex_name_param(self):
        """
        Test that _create_windows_mutex accepts mutex_name parameter.

        Given: _create_windows_mutex function exists
        When: Inspecting function signature
        Then: Should have mutex_name parameter with default value
        """
        import inspect

        from dreaming_mutex import _create_windows_mutex

        sig = inspect.signature(_create_windows_mutex)
        params = sig.parameters

        assert 'mutex_name' in params, \
            "_create_windows_mutex should have 'mutex_name' parameter"
        assert params['mutex_name'].default is not inspect.Parameter.empty, \
            "mutex_name should have a default value"

    def test_create_windows_mutex_uses_provided_mutex_name(self):
        """
        Test that _create_windows_mutex uses provided mutex_name in CreateMutexW.

        Given: _create_windows_mutex has mutex_name parameter
        When: Called with custom mutex_name
        Then: Should use that name in CreateMutexW call

        This test verifies that the mutex_name parameter is actually used
        in the Windows API call, not just accepted and ignored.
        """
        from unittest.mock import MagicMock, patch

        from dreaming_mutex import _create_windows_mutex

        # Mock the Windows API call
        with patch('ctypes.windll.kernel32.CreateMutexW') as mock_create_mutex:
            with patch('ctypes.windll.kernel32.GetLastError') as mock_get_last_error:
                # Setup mocks
                mock_handle = MagicMock()
                mock_create_mutex.return_value = mock_handle
                mock_get_last_error.return_value = 0  # No error (new mutex)

                # Call with custom mutex name
                success, handle, is_new = _create_windows_mutex(mutex_name="Global\\TestMutex")

                # Verify CreateMutexW was called with the correct mutex name
                mock_create_mutex.assert_called_once()
                call_args = mock_create_mutex.call_args

                # CreateMutexW(signature: security, initial_owner, name)
                # Third argument should be the mutex name
                assert len(call_args.args) >= 3, "CreateMutexW should be called with 3 arguments"
                assert call_args.args[2] == "Global\\TestMutex", \
                    f"CreateMutexW third argument should be 'Global\\TestMutex', got '{call_args.args[2]}'"
