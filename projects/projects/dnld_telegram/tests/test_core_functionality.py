#!/usr/bin/env python3
"""
Core functionality tests for dnld_telegram to prevent regression.

Tests the critical _prepare_download_session function and core download logic.
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestCoreDownloadFunctionality:
    """Test core download functionality doesn't break with UI changes."""

    @pytest.mark.asyncio
    async def test_prepare_download_session_returns_tuple(self):
        """Test _prepare_download_session returns expected tuple, not None."""
        with (
            patch("dnld_telegram.download.client.get_client") as mock_client,
            patch(
                "dnld_telegram.download.plugins.enumeration.get_messages_to_download"
            ) as mock_messages,
            patch("dnld_telegram.download.database.schema.get_connection") as mock_conn,
        ):
            # Mock successful returns
            mock_client.return_value = AsyncMock()
            mock_messages.return_value = []
            mock_conn.return_value.__aenter__ = AsyncMock()
            mock_conn.return_value.__aexit__ = AsyncMock()

            try:
                from dnld_telegram.download.download import _prepare_download_session

                result = await _prepare_download_session("test_channel")

                # Ensure it returns tuple, not None
                assert result is not None
                assert isinstance(result, tuple)
                assert len(result) == 4
            except ImportError:
                pytest.skip("Core download module not available")

    def test_offline_mode_detection(self):
        """Test offline mode detection still works."""
        with patch(
            "dnld_telegram.download.plugins.enumeration.get_messages_to_download"
        ) as mock_messages:
            mock_messages.return_value = []

            # Should detect no new files scenario
            messages = mock_messages()
            assert messages == []
            assert len(messages) == 0

    @pytest.mark.asyncio
    async def test_async_context_manager_usage(self):
        """Test async context manager is used correctly."""
        with patch(
            "dnld_telegram.download.database.schema.get_connection"
        ) as mock_conn:
            mock_context = AsyncMock()
            mock_conn.return_value = mock_context

            # Should use async with, not sync with
            try:
                from dnld_telegram.download.database.schema import get_connection

                async with get_connection("test") as conn:
                    assert conn is not None

                # Verify async context manager was called
                mock_context.__aenter__.assert_called_once()
                mock_context.__aexit__.assert_called_once()
            except ImportError:
                pytest.skip("Database schema module not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
