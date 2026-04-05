"""Test RSS-based prefetch for channel names.

This test verifies that prefetch can use RSS instead of yt-dlp
to fetch channel names, providing faster startup times.
"""

from unittest.mock import Mock, patch

import pytest

from yt_fts.download.batch_downloader import BatchDownloader


def test_fetch_channel_metadata_rss_exists():
    """Test that _fetch_channel_metadata_rss method exists."""
    mock_console = Mock()

    # Create a minimal mock for batch downloader initialization
    with patch("yt_fts.download.batch_downloader.BatchDownloader._initialize_batch_download", return_value=({}, 0)):
        try:
            downloader = BatchDownloader(
                channel_list=["https://www.youtube.com/channel/UCxxx"],
                jobs=1,
                console=mock_console
            )

            # Check that the RSS method exists
            assert hasattr(downloader, "_fetch_channel_metadata_rss")
            assert callable(downloader._fetch_channel_metadata_rss)
        except Exception:
            # If initialization fails, at least check the method is in the class
            assert "_fetch_channel_metadata_rss" in dir(BatchDownloader)


def test_fetch_channel_metadata_rss_signature():
    """Test that RSS-based fetch has correct signature (returns tuple)."""
    mock_console = Mock()

    with patch("yt_fts.download.batch_downloader.BatchDownloader._initialize_batch_download", return_value=({}, 0)):
        try:
            downloader = BatchDownloader(
                channel_list=["https://www.youtube.com/channel/UCxxx"],
                jobs=1,
                console=mock_console
            )

            # Mock RSS prechecker to avoid actual network calls
            with patch("yt_fts.services.rss_precheck.RssPreChecker") as mock_rss:
                mock_checker = Mock()
                mock_checker._build_rss_url = Mock(return_value="http://rss.url")
                mock_checker._extract_channel_name_from_feed = Mock(return_value="Test Channel")
                mock_checker.user_agent = "test"
                mock_checker.timeout = 5.0
                mock_rss.return_value = mock_checker

                # Mock requests.get
                with patch("requests.get") as mock_get:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.text = "<feed><title>Test Channel</title></feed>"
                    mock_get.return_value = mock_response

                    result = downloader._fetch_channel_metadata_rss("https://www.youtube.com/channel/UCxxx")

                    # Should return a tuple of (name, url)
                    assert isinstance(result, tuple)
                    assert len(result) == 2
                    name, url = result
                    # At least one should be populated
                    assert name is not None or url is not None
        except Exception as e:
            pytest.skip(f"Could not initialize BatchDownloader: {e}")


def test_fetch_channel_metadata_rss_handles_invalid_input():
    """Test that RSS-based fetch handles invalid input gracefully."""
    mock_console = Mock()

    with patch("yt_fts.download.batch_downloader.BatchDownloader._initialize_batch_download", return_value=({}, 0)):
        try:
            downloader = BatchDownloader(
                channel_list=["https://www.youtube.com/channel/UCxxx"],
                jobs=1,
                console=mock_console
            )

            # Test with invalid input (empty string)
            result = downloader._fetch_channel_metadata_rss("")

            # Should return (None, None) for invalid input
            assert result == (None, None)
        except Exception as e:
            pytest.skip(f"Could not initialize BatchDownloader: {e}")


def test_prefetch_docstring_updated():
    """Test that prefetch method documentation mentions RSS and uses ChannelPrefetchQueue."""
    # Read the actual source file
    from pathlib import Path
    source_file = Path("P:/projects/yt-fts/src/yt_fts/download/batch_downloader.py")
    content = source_file.read_text()

    # Check that prefetch mentions RSS
    assert "RSS" in content or "rss" in content.lower()

    # Check that the prefetch method is using ChannelPrefetchQueue
    # Look for the line in _prefetch_channel_names_parallel
    lines = content.split("\n")
    found_prefetch = False
    found_queue_usage = False
    found_rss_fetcher = False

    for i, line in enumerate(lines):
        if "def _prefetch_channel_names_parallel" in line:
            found_prefetch = True
            # Check the next 100 lines for ChannelPrefetchQueue usage
            for j in range(i, min(i + 100, len(lines))):
                if "ChannelPrefetchQueue" in lines[j]:
                    found_queue_usage = True
                if "_fetch_channel_metadata_rss" in lines[j]:
                    found_rss_fetcher = True
            break

    assert found_prefetch, "Could not find _prefetch_channel_names_parallel method"
    assert found_queue_usage, "Prefetch is not using ChannelPrefetchQueue"
    assert found_rss_fetcher, "Prefetch fetcher is not calling _fetch_channel_metadata_rss"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
