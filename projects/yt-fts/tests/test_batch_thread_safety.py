"""Tests for thread safety and race conditions in batch_downloader.py.

This module tests for:
- Thread-local initialization race conditions (BUG-002, BUG-010)
- Concurrent database connection access
"""

import threading
import time
from unittest.mock import MagicMock

import pytest

from yt_fts.download.batch_downloader import BatchDownloader


class TestThreadLocalRaceCondition:
    """Test thread-local storage initialization is thread-safe."""

    def test_thread_local_initialized_in_init(self):
        """Test that _thread_local is initialized in __init__, not lazily.
        
        Regression test for BUG-002/BUG-010: Previously, _thread_local was
        initialized lazily, causing race conditions. The fix initializes it
        once in __init__ using double-checked locking pattern.
        """
        config = MagicMock()
        config.max_workers = 4
        config.timeout_per_video = 300
        config.continue_on_error = True
        
        downloader = BatchDownloader([])
        
        # After __init__, _thread_local should already be initialized
        assert hasattr(downloader, '_thread_local'), '_thread_local not initialized in __init__'
        assert hasattr(downloader, '_conns_lock'), '_conns_lock not initialized in __init__'
        assert hasattr(downloader, '_all_conns'), '_all_conns not initialized in __init__'

    def test_concurrent_threads_get_unique_connections(self):
        """Test that concurrent threads each get their own DB connection.
        
        This tests the fix for BUG-002/BUG-010: Each thread should get its
        own connection via thread-local storage, and multiple calls from the
        same thread should return the same connection.
        """
        config = MagicMock()
        config.max_workers = 4
        config.timeout_per_video = 300
        config.continue_on_error = True
        
        downloader = BatchDownloader([])
        
        # Mock DB connection function
        def mock_get_db_connection(timeout=30.0):
            conn = MagicMock()
            conn.execute = MagicMock()
            return conn
        
        connections_by_thread = {}
        errors = []
        
        def get_conn_for_thread(thread_id):
            try:
                conn = downloader._get_thread_db_connection(mock_get_db_connection)
                connections_by_thread[thread_id] = id(conn)
                time.sleep(0.01)
                # Get it again - should be the same connection for this thread
                conn2 = downloader._get_thread_db_connection(mock_get_db_connection)
                assert id(conn2) == id(conn), f'Thread {thread_id} got different connections'
            except Exception as e:
                errors.append((thread_id, e))
        
        threads = []
        num_threads = 5
        
        for i in range(num_threads):
            t = threading.Thread(target=get_conn_for_thread, args=(i,))
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # No errors should occur
        assert len(errors) == 0, f'Threads had errors: {errors}'
        
        # Each thread should have its own unique connection
        unique_conns = set(connections_by_thread.values())
        assert len(unique_conns) == num_threads, f'Expected {num_threads} unique connections, got {len(unique_conns)}'
        
        # Verify total connections tracked
        assert len(downloader._all_conns) == num_threads, f'Expected {num_threads} tracked connections, got {len(downloader._all_conns)}'

    def test_high_concurrency_stress_test(self):
        """Stress test with many threads to verify thread safety."""
        config = MagicMock()
        config.max_workers = 10
        config.timeout_per_video = 300
        config.continue_on_error = True
        
        downloader = BatchDownloader([])
        
        def mock_get_db_connection(timeout=30.0):
            conn = MagicMock()
            return conn
        
        results = {}
        errors = []
        
        def worker(thread_id):
            try:
                for _ in range(5):  # Multiple calls per thread
                    conn = downloader._get_thread_db_connection(mock_get_db_connection)
                    results[thread_id] = id(conn)
                    time.sleep(0.001)
            except Exception as e:
                errors.append((thread_id, e))
        
        threads = []
        num_threads = 20
        
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f'Stress test had errors: {errors}'
        assert len(results) == num_threads, f'Expected {num_threads} threads to complete'
        assert len(downloader._all_conns) == num_threads, f'Expected {num_threads} connections'
