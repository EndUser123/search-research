"""
Tests for lazy loading of channel names in the batch downloader.

Feature requirement:
- Channel header should display immediately WITHOUT blocking on API call
- Should show @handle or channel/ID... format immediately
- Actual channel name should be fetched later via existing RSS/API flow
- No 5-second timeout blocking

This test file targets the lazy loading behavior. The current implementation
uses _ensure_channel_name_in_db which has a 5-second blocking timeout. This
test should FAIL until lazy loading is properly implemented.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.download.batch_downloader import BatchDownloader


class TestChannelNameLazyLoading:
    """Test lazy loading of channel names during batch download."""

    @patch("yt_fts.db.channels.get_channel_name_from_db")
    def test_ensure_channel_name_in_db_should_not_block_on_missing_name(
        self, mock_get_name
    ):
        """
        Test that _ensure_channel_name_in_db does NOT block when no cached name exists.

        Given: A BatchDownloader instance with a channel that has no cached name
        When: _ensure_channel_name_in_db is called (as part of header display flow)
        Then: The method should return immediately (< 50ms) without blocking for API

        NOTE: This test demonstrates the blocking issue. The mock includes a sleep
        to simulate API call time. With lazy loading, this should NOT be called.
        """
        # Arrange - Simulate no cached name in database
        mock_get_name.return_value = None

        downloader = BatchDownloader(
            channels=["@testchannel"],
            suppress_verbose=True,
        )

        channel_id = "UCXxKeNggi1234567890ab"
        # Track if API was called
        api_called = []

        def slow_mock_discover_handle(*args, **kwargs):
            api_called.append(True)
            time.sleep(0.2)  # Simulate slow API
            return None

        # Create a mock API service that simulates slow response
        with patch("yt_fts.services.channel_service.ChannelHandleService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.discover_handle.side_effect = slow_mock_discover_handle
            mock_service.return_value = mock_instance

            # Act
            start_time = time.time()
            result_channel_id = downloader._ensure_channel_name_in_db(channel_id=channel_id)
            elapsed_ms = (time.time() - start_time) * 1000

            # Assert - With lazy loading, API should NOT be called
            # Current implementation DOES call it and blocks for timeout
            assert len(api_called) == 0, (
                f"API was called during header display. "
                f"Lazy loading should defer API calls until after header is displayed."
            )

            # If API is not called, should return very quickly
            assert elapsed_ms < 50, (
                f"_ensure_channel_name_in_db took {elapsed_ms:.2f}ms, "
                f"should be < 50ms for lazy loading."
            )

            # Should still return the channel_id unchanged (no blocking API fetch)
            assert result_channel_id == channel_id

    @patch("yt_fts.db.channels.get_channel_name_from_db")
    def test_ensure_channel_name_in_db_returns_fast_with_cached_name(
        self, mock_get_name
    ):
        """
        Test that _ensure_channel_name_in_db returns quickly when name is cached.

        Given: A channel with a cached human-readable name
        When: _ensure_channel_name_in_db is called
        Then: The method should return immediately without any API call
        """
        # Arrange - Simulate cached name exists
        mock_get_name.return_value = "Test Channel Name"

        downloader = BatchDownloader(
            channels=["@testchannel"],
            suppress_verbose=True,
        )

        channel_id = "UCXxKeNggi1234567890ab"
        # Act
        start_time = time.time()
        result_channel_id = downloader._ensure_channel_name_in_db(channel_id=channel_id)
        elapsed_ms = (time.time() - start_time) * 1000

        # Assert - Should return very quickly (< 10ms for cached case)
        assert elapsed_ms < 10, (
            f"_ensure_channel_name_in_db with cached name took {elapsed_ms:.2f}ms, "
            f"should be < 10ms"
        )
        assert result_channel_id == channel_id

    @patch("yt_fts.db.channels.get_channel_name_from_db")
    def test_header_display_does_not_call_slow_api_discovery(self, mock_get_name):
        """
        Test that header display flow does NOT call slow API discovery.

        Given: A BatchDownloader with a channel that has no cached name
        When: The header is displayed via _ensure_channel_name_in_db
        Then: No blocking API call should be made

        NOTE: This test FAILS because current implementation calls API via
        ChannelHandleService.discover_handle in a separate thread but still
        blocks for up to 5 seconds waiting for it.
        """
        # Arrange - No cached name
        mock_get_name.return_value = None

        downloader = BatchDownloader(
            channels=["@testchannel"],
            suppress_verbose=True,
        )

        channel_id = "UCXxKeNggi1234567890ab"
        # Track API calls
        api_calls = []

        def mock_discover_handle(*args, **kwargs):
            api_calls.append(("discover_handle", args, kwargs))
            # Simulate slow API that would cause timeout in current impl
            time.sleep(0.1)  # Small delay to show it's being called
            return None

        with patch("yt_fts.services.channel_service.ChannelHandleService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.discover_handle.side_effect = mock_discover_handle
            mock_service.return_value = mock_instance

            # Act
            start_time = time.time()
            downloader._ensure_channel_name_in_db(channel_id=channel_id)
            elapsed_ms = (time.time() - start_time) * 1000

            # Assert - For lazy loading, API should NOT be called at all
            # Current implementation DOES call it and blocks waiting
            assert len(api_calls) == 0, (
                f"API was called {len(api_calls)} times during header display. "
                f"Lazy loading should defer API calls until after header is displayed."
            )
            # Or if we allow background fetch, it should not block:
            # assert elapsed_ms < 50, "Should not wait for API call to complete"
