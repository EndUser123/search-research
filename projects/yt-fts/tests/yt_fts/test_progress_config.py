"""Test progress configuration in yt_fts.config."""

import pytest


def test_batch_progress_config_exists():
    """Test that BATCH_PROGRESS_CONFIG can be imported."""
    from yt_fts.config import BATCH_PROGRESS_CONFIG

    assert BATCH_PROGRESS_CONFIG is not None


def test_single_channel_progress_config_exists():
    """Test that SINGLE_CHANNEL_PROGRESS_CONFIG can be imported."""
    from yt_fts.config import SINGLE_CHANNEL_PROGRESS_CONFIG

    assert SINGLE_CHANNEL_PROGRESS_CONFIG is not None


def test_worker_progress_config_exists():
    """Test that WORKER_PROGRESS_CONFIG can be imported."""
    from yt_fts.config import WORKER_PROGRESS_CONFIG

    assert WORKER_PROGRESS_CONFIG is not None


def test_batch_progress_config_has_transient_true():
    """Test that BATCH_PROGRESS_CONFIG has transient=True."""
    from yt_fts.config import BATCH_PROGRESS_CONFIG

    assert BATCH_PROGRESS_CONFIG.get("transient") is True


def test_single_channel_progress_config_has_transient_true():
    """Test that SINGLE_CHANNEL_PROGRESS_CONFIG has transient=True."""
    from yt_fts.config import SINGLE_CHANNEL_PROGRESS_CONFIG

    assert SINGLE_CHANNEL_PROGRESS_CONFIG.get("transient") is True


def test_worker_progress_config_has_transient_true():
    """Test that WORKER_PROGRESS_CONFIG has transient=True."""
    from yt_fts.config import WORKER_PROGRESS_CONFIG

    assert WORKER_PROGRESS_CONFIG.get("transient") is True


def test_progress_can_be_imported_from_config():
    """Test that Progress can be imported from yt_fts.config."""
    from yt_fts.config import Progress

    assert Progress is not None
    from rich.progress import Progress as RichProgress
    assert Progress is RichProgress  # Should be the same class
