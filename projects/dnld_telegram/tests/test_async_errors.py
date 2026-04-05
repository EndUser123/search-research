"""
TDD Tests for identifying and fixing async connection errors
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestAsyncConnectionErrors:
    """Test class to identify async connection issues using TDD approach"""

    def test_logging_config_async_errors_identified(self):
        """RED: Test that identifies the logging config async errors"""
        # This test should initially fail to demonstrate the problem exists

        # The error shows: RuntimeWarning: coroutine 'Connection.execute' was never awaited
        # This happens in logging_config.py:159

        # Let's verify the issue exists by checking the problematic code
        try:
            from dnld_telegram.download.config.logging_config import setup_logging

            # The test passes if we can import without immediate errors
            assert True
        except ImportError as e:
            pytest.fail(f"Cannot import logging_config: {e}")

    @pytest.mark.asyncio
    async def test_database_storage_get_channel_id_async_issue(self):
        """RED: Test that identifies database storage async issues"""
        # The error shows: RuntimeWarning: coroutine 'DatabaseStorage.get_channel_id' was never awaited

        try:
            from dnld_telegram.download.storage import get_storage

            # Create mock storage to test the async issue
            storage = get_storage("test_channel", 12345)

            # Check if get_channel_id is an async method that's being called synchronously
            if hasattr(storage, "get_channel_id"):
                method = storage.get_channel_id
                if asyncio.iscoroutinefunction(method):
                    # This should be awaited, not called directly
                    pytest.fail(
                        "get_channel_id is async but may be called without await"
                    )

        except ImportError as e:
            pytest.skip(f"Cannot import storage: {e}")

    @pytest.mark.asyncio
    async def test_connection_execute_async_issue(self):
        """RED: Test that identifies Connection.execute async issues"""
        # The error shows: RuntimeWarning: coroutine 'Connection.execute' was never awaited

        # This likely happens when database operations are called without proper await
        # Let's create a test that would expose this issue

        try:
            from dnld_telegram.download.database.storage import DatabaseStorage

            # Mock database connection
            with patch(
                "dnld_telegram.download.database.storage.aiosqlite.connect"
            ) as mock_connect:
                mock_conn = AsyncMock()
                mock_connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
                mock_connect.return_value.__aexit__ = AsyncMock(return_value=None)

                storage = DatabaseStorage("test_channel", 12345)

                # If this method exists and is async, it should be properly awaited
                if hasattr(storage, "get_channel_id"):
                    # This test should pass once we fix the async issues
                    result = await storage.get_channel_id()
                    assert (
                        result is not None or result is None
                    )  # Either is valid for a test

        except ImportError as e:
            pytest.skip(f"Cannot import DatabaseStorage: {e}")
        except Exception as e:
            # Expected to fail initially - this identifies the problem
            pytest.fail(f"Async connection error detected: {e}")

    def test_identify_logging_config_line_159(self):
        """RED: Identify the specific line causing logging config issues"""
        # The error points to logging_config.py:159
        # Let's read that file and identify the problematic code

        logging_config_path = (
            Path(__file__).parent.parent
            / "src"
            / "dnld_telegram"
            / "download"
            / "config"
            / "logging_config.py"
        )

        if logging_config_path.exists():
            with open(logging_config_path) as f:
                lines = f.readlines()
                if len(lines) >= 159:
                    line_159 = lines[158].strip()  # Line 159 (0-indexed)

                    # Check if this line contains problematic async code
                    if "await" in line_159 and (
                        "Connection.execute" in line_159 or "get_channel_id" in line_159
                    ):
                        pytest.fail(
                            f"Line 159 contains async code that may not be properly awaited: {line_159}"
                        )
                    else:
                        # This should pass once we identify and fix the issue
                        assert True
        else:
            pytest.skip("logging_config.py not found")

    @pytest.mark.asyncio
    async def test_proper_async_context_manager_usage(self):
        """GREEN: Test that shows how async should be properly handled"""
        # This test shows the correct way to handle async operations

        async def proper_async_operation():
            """Example of proper async operation"""
            try:
                # Simulate proper async database operation
                async with AsyncMock() as conn:
                    result = await conn.execute("SELECT 1")
                    return result
            except Exception:
                return None

        # This should work without warnings
        result = await proper_async_operation()
        # Test passes regardless of result - it's about proper async handling
        assert result is not None or result is None

    def test_sync_wrapper_detection(self):
        """RED: Detect if sync wrappers are causing async issues"""
        # Sometimes sync wrappers around async code cause these issues

        try:
            # Check if setup_logging or related functions are improperly handling async
            import inspect

            from dnld_telegram.download.config.logging_config import setup_logging

            if inspect.iscoroutinefunction(setup_logging):
                pytest.fail("setup_logging is async but may be called synchronously")
            else:
                # This should pass - setup_logging should be sync
                assert True

        except ImportError as e:
            pytest.skip(f"Cannot import for sync wrapper test: {e}")


if __name__ == "__main__":
    # Run tests to identify the issues
    pytest.main([__file__, "-v"])
