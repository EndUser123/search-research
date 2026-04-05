"""Characterization tests for ThreadPoolExecutor cleanup (P0-002)."""
import pytest
from unittest.mock import MagicMock, patch
from yt_fts.download.batch_channel_helpers import ChannelDownloadContext

class TestThreadPoolExecutorCleanup:
    """Tests for proper ThreadPoolExecutor lifecycle management."""
    
    def test_executor_property_creates_on_demand(self):
        """Characterize: executor property creates ThreadPoolExecutor lazily."""
        # Mock get_db_connection function
        mock_get_db_conn = MagicMock()
        
        context = ChannelDownloadContext(
            get_db_connection=mock_get_db_conn,
            max_workers=4,
            db_timeout=30.0
        )
        
        # Before accessing executor property
        assert context._executor is None, "Executor should be None initially"
        
        # After accessing executor property
        executor = context.executor
        assert executor is not None, "Executor should be created on first access"
        assert context._executor is not None, "Executor should be cached"
        
    def test_cleanup_shuts_down_executor(self):
        """Characterize: cleanup() method shuts down executor."""
        # Mock get_db_connection function
        mock_get_db_conn = MagicMock()
        
        context = ChannelDownloadContext(
            get_db_connection=mock_get_db_conn,
            max_workers=4,
            db_timeout=30.0
        )
        
        # Create executor by accessing property
        executor = context.executor
        assert not executor._shutdown, "Executor should not be shut down initially"
        
        # Call cleanup
        context.cleanup()
        
        # Verify executor was shut down
        assert executor._shutdown, "Executor should be shut down after cleanup()"
        assert context._executor is None, "Executor reference should be cleared"
        
    def test_context_manager_protocol(self):
        """Verify FIXED: Class implements context manager protocol.
        
        This ensures cleanup() is always called when used with 'with' statement.
        """
        # Mock get_db_connection function
        mock_get_db_conn = MagicMock()
        
        context = ChannelDownloadContext(
            get_db_connection=mock_get_db_conn,
            max_workers=4,
            db_timeout=30.0
        )
        
        # FIXED: __enter__ method exists and returns self
        assert hasattr(context, '__enter__') and callable(getattr(context, '__enter__')),             "FIXED: __enter__ is implemented"
        assert context.__enter__() is context, "__enter__ should return self"
        
        # FIXED: __exit__ method exists
        assert hasattr(context, '__exit__') and callable(getattr(context, '__exit__')),             "FIXED: __exit__ is implemented"
        
    def test_context_manager_usage(self):
        """Verify context manager ensures cleanup is called."""
        # Mock get_db_connection function
        mock_get_db_conn = MagicMock()
        
        with ChannelDownloadContext(
            get_db_connection=mock_get_db_conn,
            max_workers=4,
            db_timeout=30.0
        ) as context:
            # Create executor by accessing property
            executor = context.executor
            assert not executor._shutdown, "Executor should be running"
            
        # After exiting context, executor should be shut down
        assert executor._shutdown, "Executor should be shut down after context exit"
