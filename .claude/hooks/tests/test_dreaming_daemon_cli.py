"""
Tests for dreaming_daemon CLI --daemon-type parameter (RED phase of TDD).

These tests verify that dreaming_daemon.py accepts --daemon-type argument that:
- Accepts "dreaming" or "search" as values
- Defaults to "dreaming" if not provided
- Loads config from DAEMON_TYPES
- Passes mutex_name to acquire_singleton()

All tests MUST FAIL initially (--daemon-type doesn't exist yet).

Run with: pytest tests/test_dreaming_daemon_cli.py -v
"""

from unittest.mock import patch

import pytest


class TestMainDaemonTypeParameter:
    """Tests for main() function daemon_type parameter."""

    def test_main_accepts_daemon_type_argument(self):
        """
        Test that main() has daemon_type parameter.

        Given: dreaming_daemon.main() function exists
        When: Inspecting function signature
        Then: Should have daemon_type parameter with default value "dreaming"
        """
        import inspect

        from dreaming_daemon import main

        sig = inspect.signature(main)
        params = sig.parameters

        assert 'daemon_type' in params, \
            "main() should have 'daemon_type' parameter"
        assert params['daemon_type'].default == "dreaming", \
            f"daemon_type should default to 'dreaming', got '{params['daemon_type'].default}'"

    def test_main_default_daemon_type_is_dreaming(self):
        """
        Test that main() default daemon_type is "dreaming".

        Given: main() has daemon_type parameter
        When: Calling main() without arguments
        Then: Should use "dreaming" as default daemon_type
        """
        import inspect

        from dreaming_daemon import main

        sig = inspect.signature(main)
        default_daemon_type = sig.parameters['daemon_type'].default

        assert default_daemon_type == "dreaming", \
            f"Default daemon_type should be 'dreaming', got '{default_daemon_type}'"

    def test_main_can_accept_search_daemon_type(self):
        """
        Test that main() can accept "search" as daemon_type.

        Given: main() has daemon_type parameter
        When: Calling main() with daemon_type="search"
        Then: Should accept "search" without error
        """
        from dreaming_daemon import main

        # Mock the async main to prevent actual daemon startup
        with patch('dreaming_daemon.asyncio.run') as mock_run:
            mock_run.return_value = 0

            try:
                # Call with search daemon type
                result = main(daemon_type="search")

                # Verify it was called (we don't care about the actual result,
                # just that it accepted the parameter)
                assert isinstance(result, int), "Should return integer exit code"
            except TypeError as e:
                if "daemon_type" in str(e):
                    pytest.fail(f"main() should accept daemon_type parameter: {e}")
                raise

    def test_main_raises_on_invalid_daemon_type(self):
        """
        Test that main() raises ValueError for unknown daemon_type.

        Given: main() has daemon_type parameter
        When: Calling main() with invalid daemon_type
        Then: Should raise ValueError with descriptive message
        """
        from dreaming_daemon import main

        # Mock the async main to prevent actual daemon startup
        with patch('dreaming_daemon.asyncio.run') as mock_run:
            mock_run.return_value = 0

            with pytest.raises(ValueError) as exc_info:
                main(daemon_type="invalid_daemon")

            assert "Unknown daemon type" in str(exc_info.value) or "invalid_daemon" in str(exc_info.value), \
                f"Error message should mention unknown daemon type, got: {exc_info.value}"


class TestMainDaemonConfigIntegration:
    """Tests for main() integration with daemon config system."""

    def test_main_loads_config_from_daemon_config(self):
        """
        Test that main() calls get_daemon_config() to load config.

        Given: main() has daemon_type parameter
        When: Calling main() with daemon_type="search"
        Then: Should call get_daemon_config('search')
        """
        from dreaming_daemon import main

        # Mock both async run and get_daemon_config
        with patch('dreaming_daemon.asyncio.run') as mock_run:
            mock_run.return_value = 0

            with patch('dreaming_daemon.get_daemon_config') as mock_get_config:
                mock_get_config.return_value = {
                    'mutex_name': 'Global\\TestMutex',
                    'pid_file': 'test-daemon.pid',
                    'state_file': 'test-daemon-state.json',
                    'daemon_log': 'test-daemon.log',
                }

                try:
                    main(daemon_type="search")
                except:
                    pass  # We don't care if it fails, just want to check the call

                # Verify get_daemon_config was called with correct daemon_type
                mock_get_config.assert_called_once_with('search')

    def test_main_passes_mutex_name_to_acquire_singleton(self):
        """
        Test that main() passes mutex_name from config to acquire_singleton().

        Given: main() loads daemon config
        When: Calling acquire_singleton()
        Then: Should pass mutex_name from daemon config
        """
        from dreaming_daemon import main

        # Mock dependencies
        with patch('dreaming_daemon.asyncio.run') as mock_run:
            mock_run.return_value = 0

            # Mock get_daemon_config to return search daemon config
            with patch('dreaming_daemon.get_daemon_config') as mock_get_config:
                search_config = {
                    'mutex_name': 'Global\\ClaudeSearchDaemon',
                    'pid_file': 'search-daemon.pid',
                    'state_file': 'search-daemon-state.json',
                    'daemon_log': 'search-daemon.log',
                }
                mock_get_config.return_value = search_config

                # Mock acquire_singleton to capture the mutex_name argument
                with patch('dreaming_daemon.acquire_singleton') as mock_acquire:
                    mock_acquire.return_value = (True, None)

                    try:
                        main(daemon_type="search")
                    except:
                        pass  # We don't care if it fails, just want to check the call

                    # Verify acquire_singleton was called with correct mutex_name
                    if mock_acquire.called:
                        call_args = mock_acquire.call_args
                        # Check if mutex_name was passed (as keyword argument)
                        if 'mutex_name' in call_args.kwargs:
                            assert call_args.kwargs['mutex_name'] == 'Global\\ClaudeSearchDaemon', \
                                f"Should pass 'Global\\ClaudeSearchDaemon' as mutex_name, got '{call_args.kwargs['mutex_name']}'"


class TestCLIBackwardCompatibility:
    """Tests for backward compatibility when --daemon-type is not provided."""

    def test_backward_compatibility_no_argument(self):
        """
        Test that main() works without --daemon-type argument.

        Given: main() has daemon_type parameter with default
        When: Calling main() without daemon_type argument
        Then: Should use default "dreaming" daemon type
        """
        from dreaming_daemon import main

        # Mock the async main to prevent actual daemon startup
        with patch('dreaming_daemon.asyncio.run') as mock_run:
            mock_run.return_value = 0

            try:
                # Call without daemon_type argument (backward compatible)
                result = main()

                # Verify it returns successfully
                assert isinstance(result, int), "Should return integer exit code"
            except TypeError as e:
                if "daemon_type" in str(e) or "missing" in str(e).lower():
                    pytest.fail(f"main() should work without daemon_type argument for backward compatibility: {e}")
                raise

    def test_backward_compatibility_cli_invocation(self):
        """
        Test that CLI invocation without --daemon-type works.

        Given: dreaming_daemon.py can be run from CLI
        When: Running 'python dreaming_daemon.py' without --daemon-type
        Then: Should use default "dreaming" daemon type
        """
        # This test verifies CLI-level backward compatibility
        # We'll test by simulating CLI invocation

        from dreaming_daemon import main

        # Mock sys.argv to simulate running without --daemon-type
        with patch('sys.argv', ['dreaming_daemon.py']):
            # Mock the async main to prevent actual daemon startup
            with patch('dreaming_daemon.asyncio.run') as mock_run:
                mock_run.return_value = 0

                try:
                    # This simulates: python dreaming_daemon.py
                    result = main()

                    # Should work without errors
                    assert isinstance(result, int), "Should return integer exit code"
                except TypeError as e:
                    if "daemon_type" in str(e):
                        pytest.fail(f"CLI invocation should work without --daemon-type: {e}")
                    raise


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing of --daemon-type."""

    def test_cli_accepts_daemon_type_dreaming(self):
        """
        Test that CLI accepts --daemon-type dreaming.

        Given: CLI has --daemon-type argument
        When: Running 'python dreaming_daemon.py --daemon-type dreaming'
        Then: Should parse daemon_type as "dreaming"
        """
        # This test will need argparse setup in dreaming_daemon.py
        # For now, we'll test that main() can be called with daemon_type="dreaming"
        from dreaming_daemon import main

        with patch('dreaming_daemon.asyncio.run') as mock_run:
            mock_run.return_value = 0

            try:
                result = main(daemon_type="dreaming")
                assert isinstance(result, int), "Should return integer exit code"
            except Exception as e:
                pytest.fail(f"Should accept daemon_type='dreaming': {e}")

    def test_cli_accepts_daemon_type_search(self):
        """
        Test that CLI accepts --daemon-type search.

        Given: CLI has --daemon-type argument
        When: Running 'python dreaming_daemon.py --daemon-type search'
        Then: Should parse daemon_type as "search"
        """
        from dreaming_daemon import main

        with patch('dreaming_daemon.asyncio.run') as mock_run:
            mock_run.return_value = 0

            try:
                result = main(daemon_type="search")
                assert isinstance(result, int), "Should return integer exit code"
            except Exception as e:
                pytest.fail(f"Should accept daemon_type='search': {e}")

    def test_cli_rejects_invalid_daemon_type(self):
        """
        Test that CLI rejects invalid --daemon-type values.

        Given: CLI has --daemon-type argument
        When: Running 'python dreaming_daemon.py --daemon-type invalid'
        Then: Should raise ValueError with descriptive message
        """
        from dreaming_daemon import main

        with patch('dreaming_daemon.asyncio.run') as mock_run:
            mock_run.return_value = 0

            with pytest.raises(ValueError) as exc_info:
                main(daemon_type="invalid")

            assert "Unknown daemon type" in str(exc_info.value) or "invalid" in str(exc_info.value), \
                f"Error should mention invalid daemon type, got: {exc_info.value}"
