"""
Unit tests for BatchDownloader thread-safe database connection handling.

Tests cover thread-local storage behavior, connection caching per thread,
connection tracking across threads, and double-checked locking pattern.
"""

import threading
from threading import Lock, Thread, current_thread
from unittest.mock import MagicMock

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


@pytest.fixture
def mock_connection_factory():
    """Factory that creates unique mock connections per call."""
    created_connections = []
    connection_counter = [0]

    def create_connection(timeout=None):
        conn = MagicMock()
        conn.id = connection_counter[0]
        conn.thread_name = current_thread().name
        connection_counter[0] += 1
        created_connections.append(conn)
        return conn

    create_connection.created_connections = created_connections
    create_connection.counter = connection_counter
    return create_connection


class TestThreadSafeDatabaseConnection:
    """
    Tests for thread-safe database connection management.

    Tests verify:
    - Connections are cached per thread using thread-local storage
    - Different threads get different connections
    - All connections are tracked in _all_conns
    - Connections are reused within the same thread
    - Double-checked locking prevents race conditions
    """

    def test_connection_cached_per_thread(self, batch_downloader, mock_connection_factory):
        """
        Test that database connection is cached in thread-local storage.

        Given: A BatchDownloader instance with thread-local storage initialized
        When: _get_thread_db_connection is called twice in the same thread
        Then: The same connection object is returned (cached)
        And: get_db_connection is only called once
        """
        # Act
        conn1 = batch_downloader._get_thread_db_connection(mock_connection_factory)
        conn2 = batch_downloader._get_thread_db_connection(mock_connection_factory)

        # Assert
        assert conn1 is conn2, "Same connection should be returned from thread-local cache"
        assert mock_connection_factory.counter[0] == 1, "get_db_connection should only be called once"

    def test_different_threads_get_different_connections(self, batch_downloader, mock_connection_factory):
        """
        Test that different threads get different database connections.

        Given: A BatchDownloader instance
        When: _get_thread_db_connection is called from multiple threads concurrently
        Then: Each thread receives a unique connection object
        And: Connections are isolated per thread (thread-local storage works)
        """
        # Create a list to collect results from each thread
        results = []
        results_lock = Lock()

        def thread_worker():
            """Worker function that gets a connection and records it."""
            conn = batch_downloader._get_thread_db_connection(mock_connection_factory)
            with results_lock:
                results.append({
                    "thread_id": current_thread().ident,
                    "thread_name": current_thread().name,
                    "connection": conn,
                    "connection_id": conn.id,
                })

        # Act - Create multiple threads that will each call _get_thread_db_connection
        threads = []
        num_threads = 5
        for i in range(num_threads):
            t = Thread(target=thread_worker, name=f"TestThread-{i}")
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Assert
        assert len(results) == num_threads, f"Expected {num_threads} results, got {len(results)}"

        # Each thread should have gotten a unique connection
        connection_ids = [r["connection_id"] for r in results]
        assert len(set(connection_ids)) == num_threads,             f"Expected {num_threads} unique connections, got {len(set(connection_ids))}: {connection_ids}"

        # Verify connections are different objects
        connections = [r["connection"] for r in results]
        for i, conn1 in enumerate(connections):
            for j, conn2 in enumerate(connections):
                if i != j:
                    assert conn1 is not conn2, f"Thread {i} and Thread {j} should have different connections"

    def test_all_conns_tracking(self, batch_downloader, mock_connection_factory):
        """
        Test that all connections are tracked in _all_conns list.

        Given: A BatchDownloader instance with empty _all_conns
        When: Multiple threads create connections via _get_thread_db_connection
        Then: All created connections are tracked in _all_conns
        And: Each connection appears exactly once in the tracking list
        """
        # Ensure _all_conns starts empty
        initial_count = len(batch_downloader._all_conns)

        # Create threads that will each create a connection
        threads = []
        num_threads = 4
        for i in range(num_threads):
            t = Thread(
                target=lambda: batch_downloader._get_thread_db_connection(mock_connection_factory),
                name=f"TrackingThread-{i}"
            )
            threads.append(t)

        # Act - Start all threads
        for t in threads:
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        # Assert - All connections should be tracked
        tracked_connections = batch_downloader._all_conns[initial_count:]  # Only new ones
        assert len(tracked_connections) == num_threads,             f"Expected {num_threads} tracked connections, got {len(tracked_connections)}"

        # Verify each connection in _all_conns is unique
        assert len(set(tracked_connections)) == num_threads,             "All tracked connections should be unique objects"

    def test_connection_reuse_in_same_thread(self, batch_downloader, mock_connection_factory):
        """
        Test that connection is reused across multiple calls in the same thread.

        Given: A BatchDownloader instance
        When: The same thread calls _get_thread_db_connection multiple times
        Then: The same cached connection is returned each time
        And: get_db_connection is only called once (lazy initialization)
        """
        # Arrange - Track call count
        call_count = [0]
        original_factory = mock_connection_factory

        def counting_factory(timeout=None):
            call_count[0] += 1
            return original_factory(timeout=timeout)

        # Act - Call multiple times in this thread
        conn1 = batch_downloader._get_thread_db_connection(counting_factory)
        conn2 = batch_downloader._get_thread_db_connection(counting_factory)
        conn3 = batch_downloader._get_thread_db_connection(counting_factory)

        # Assert
        assert conn1 is conn2 is conn3, "All calls should return the same cached connection"
        assert call_count[0] == 1, f"Expected 1 call to factory, got {call_count[0]}"

    def test_double_checked_locking_pattern(self, batch_downloader):
        """
        Test that double-checked locking prevents race condition.

        Given: A BatchDownloader instance with thread-local storage
        When: Multiple threads simultaneously check for cached connection
        Then: Only one thread creates the connection per thread
        And: The lock prevents duplicate connection creation
        And: The double-check inside lock prevents redundant creation

        This test verifies:
        1. First check (before lock) - fast path for cached connections
        2. Lock acquisition - serializes concurrent access
        3. Second check (after lock) - prevents redundant creation if another
           thread created while we waited for the lock
        """
        # Track synchronization events
        barrier = threading.Barrier(5)  # 5 threads must reach barrier together
        results = []
        results_lock = Lock()

        # A slow factory that helps expose race conditions
        factory_counter = [0]
        factory_lock = Lock()

        def slow_connection_factory(timeout=None):
            """Factory that simulates slow connection creation."""
            with factory_lock:
                factory_counter[0] += 1
                conn_id = factory_counter[0]
            # Simulate connection creation time
            import time
            time.sleep(0.01)
            conn = MagicMock()
            conn.id = conn_id
            conn.thread_name = current_thread().name
            return conn

        def concurrent_thread_worker():
            """
            Worker that tries to get connection simultaneously with other threads.

            The barrier ensures all threads reach the connection call at the same time,
            maximizing the chance of exposing race conditions.
            """
            # Wait for all threads to be ready
            barrier.wait()

            # All threads call simultaneously - this is where race could happen
            conn = batch_downloader._get_thread_db_connection(slow_connection_factory)

            # Record result
            with results_lock:
                results.append({
                    "thread_id": current_thread().ident,
                    "connection_id": conn.id,
                })

            # Call again - should use cached version
            conn2 = batch_downloader._get_thread_db_connection(slow_connection_factory)
            assert conn is conn2, "Second call should return cached connection"

        # Act - Create and start threads
        threads = []
        num_threads = 5
        for i in range(num_threads):
            t = Thread(target=concurrent_thread_worker, name=f"ConcurrentThread-{i}")
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Assert - Each thread should have gotten a unique connection
        assert len(results) == num_threads,             f"Expected {num_threads} results, got {len(results)}"

        connection_ids = [r["connection_id"] for r in results]
        unique_ids = set(connection_ids)

        # Each thread gets exactly one connection (no duplicates per thread)
        assert len(unique_ids) == num_threads,             f"Expected {num_threads} unique connections, got {len(unique_ids)}: {connection_ids}"

        # Verify factory was called exactly once per thread
        assert factory_counter[0] == num_threads,             f"Factory should be called {num_threads} times (once per thread), got {factory_counter[0]}"

    def test_thread_local_storage_isolation(self, batch_downloader, mock_connection_factory):
        """
        Test that thread-local storage properly isolates connections between threads.

        Given: A BatchDownloader with _thread_local storage
        When: Thread A stores a connection and Thread B calls _get_thread_db_connection
        Then: Thread B does NOT see Thread A's connection
        And: Each thread has its own isolated connection
        """
        # Act - Main thread gets a connection
        main_conn = batch_downloader._get_thread_db_connection(mock_connection_factory)

        # Create a thread that will get its own connection
        thread_conn = [None]

        def worker():
            thread_conn[0] = batch_downloader._get_thread_db_connection(mock_connection_factory)

        t = Thread(target=worker)
        t.start()
        t.join()

        # Assert - Connections should be different
        assert main_conn is not thread_conn[0],             "Main thread and worker thread should have different connections"

        # Verify main thread's connection is still cached
        main_conn2 = batch_downloader._get_thread_db_connection(mock_connection_factory)
        assert main_conn is main_conn2, "Main thread should still have its connection cached"

    def test_concurrent_access_with_lock(self, batch_downloader, mock_connection_factory):
        """
        Test that _conns_lock properly protects _all_conns during concurrent access.

        Given: Multiple threads creating connections simultaneously
        When: All threads append to _all_conns via _get_thread_db_connection
        Then: _all_conns contains all connections without corruption
        And: No connections are lost due to race condition
        """
        num_threads = 10
        threads = []

        def worker():
            batch_downloader._get_thread_db_connection(mock_connection_factory)

        # Act - Launch many threads concurrently
        for i in range(num_threads):
            t = Thread(target=worker, name=f"LockTestThread-{i}")
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Assert - All connections should be tracked
        # Note: _all_conns may have connections from other tests, so we check the count
        # of connections added during this test
        assert len(batch_downloader._all_conns) >= num_threads,             f"Expected at least {num_threads} connections in _all_conns"

        # Verify all are unique
        unique_conns = set(batch_downloader._all_conns)
        assert len(unique_conns) == len(batch_downloader._all_conns),             "_all_conns should not contain duplicates"

    def test_connection_cached_after_thread_local_attribute_set(self, batch_downloader, mock_connection_factory):
        """
        Test that once _thread_local.conn is set, it's consistently returned.

        Given: A thread has a cached connection in _thread_local.conn
        When: _get_thread_db_connection is called again
        Then: The cached connection is returned without calling the factory
        And: The factory counter is not incremented (factory was not called)
        """
        # First, get a connection normally
        conn1 = batch_downloader._get_thread_db_connection(mock_connection_factory)
        initial_count = mock_connection_factory.counter[0]

        # Act - Call again, should return cached connection
        conn2 = batch_downloader._get_thread_db_connection(mock_connection_factory)

        # Assert
        assert conn1 is conn2, "Should return the cached connection"
        assert mock_connection_factory.counter[0] == initial_count,             "Factory should not be called when connection is already cached"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
