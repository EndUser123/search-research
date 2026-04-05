"""
Unit tests for BatchDownloader metadata operations.

Tests cover:
- Metadata backfill (subscriber count, playlist count)
- Channel freshness checking
- Display name formatting
"""

import pytest

from yt_fts.download.batch_downloader import BatchDownloader


@pytest.fixture
def batch_downloader():
    """Create a BatchDownloader instance for testing."""
    return BatchDownloader(
        channels=["@testchannel"],
        suppress_quota_print=True,
        suppress_verbose=True,
    )
