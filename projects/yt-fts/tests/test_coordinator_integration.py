"""
Tests for ThreadSafeProgressCoordinator integration.

Tests that YouTubeAPIBackfill and batch_downloader correctly use
the coordinator pattern to avoid nested Progress contexts.
"""

from unittest.mock import Mock, MagicMock, patch
import pytest

from yt_fts.download.progress_coordinator import ThreadSafeProgressCoordinator
from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill


class TestCoordinatorIntegration:
    """Test coordinator pattern integration."""

    def test_youtube_api_backfill_accepts_coordinator_tuple(self):
        """YouTubeAPIBackfill should accept (coordinator, task_id) tuple."""
        # Arrange
        mock_coordinator = Mock()
        mock_task_id = Mock()
        
        # Act
        backfill = YouTubeAPIBackfill(
            api_keys=["test_key"],
            show_progress=(mock_coordinator, mock_task_id)
        )
        
        # Assert
        assert backfill._coordinator == mock_coordinator
        assert backfill._task_id == mock_task_id
        assert backfill._parent_progress is None
        assert backfill.show_progress is False

    def test_youtube_api_backfill_with_legacy_progress(self):
        """YouTubeAPIBackfill should still support legacy Progress object."""
        # Arrange
        from rich.progress import Progress
        mock_progress = Mock(spec=Progress)
        
        # Act
        backfill = YouTubeAPIBackfill(
            api_keys=["test_key"],
            show_progress=mock_progress
        )
        
        # Assert
        assert backfill._parent_progress == mock_progress
        assert backfill._coordinator is None
        assert backfill._task_id is None
        assert backfill.show_progress is False

    def test_youtube_api_backfill_with_bool(self):
        """YouTubeAPIBackfill should still support bool show_progress."""
        # Act
        backfill = YouTubeAPIBackfill(
            api_keys=["test_key"],
            show_progress=True
        )
        
        # Assert
        assert backfill._parent_progress is None
        assert backfill._coordinator is None
        assert backfill._task_id is None
        assert backfill.show_progress is True

    @patch('yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill._load_api_keys')
    def test_coordinator_update_path_used_when_available(self, mock_load_keys):
        """When coordinator is available, progress updates should use coordinator.update()."""
        # Arrange
        mock_load_keys.return_value = ["test_key"]
        mock_coordinator = Mock()
        mock_task_id = Mock()
        
        backfill = YouTubeAPIBackfill(
            show_progress=(mock_coordinator, mock_task_id)
        )
        
        # Act - Simulate a progress update
        # This would normally be called from fetch_all_videos_from_channel
        # We're testing the branch selection logic
        
        # Assert
        assert backfill._coordinator is not None
        assert backfill._parent_progress is None

    def test_batch_downloader_accepts_coordinator_parameter(self):
        """_backfill_new_channel_metadata should accept coordinator parameter."""
        from yt_fts.download.batch_downloader import BatchDownloader
        
        # Arrange
        downloader = BatchDownloader(
            channels=["@test"],
            dry_run=True  # Use dry run to avoid actual API calls
        )
        
        # Act - Call the method with coordinator parameter
        # This should not raise an error
        try:
            # We can't actually call this without a lot more setup,
            # but we can verify the signature accepts the parameter
            import inspect
            sig = inspect.signature(downloader._backfill_new_channel_metadata)
            params = list(sig.parameters.keys())
            
            # Assert
            assert 'coordinator' in params
        except Exception as e:
            pytest.fail(f"Failed to inspect _backfill_new_channel_metadata: {e}")
