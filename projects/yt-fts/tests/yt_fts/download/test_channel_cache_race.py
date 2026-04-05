"""Characterization tests for channel_cache.py race conditions.

These tests CAPTURE CURRENT BEHAVIOR before refactoring.
Run with: pytest tests/yt_fts/download/test_channel_cache_race.py -v

Issue: P0-1 - Race condition in global stats and "reported" flag
"""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.download.channel_cache import (
    report_cache_status,
    print_aggregated_cache_status,
    _cache_stats,
    _cache_stats_lock,
)


class TestReportCacheStatusConcurrency:
    """Tests for report_cache_status() concurrent behavior."""

    def setup_method(self):
        """Reset global state before each test."""
        global _cache_stats, _cache_stats_lock
        with _cache_stats_lock:
            _cache_stats["cached"] = 0
            _cache_stats["new"] = 0
            _cache_stats["skipped_empty"] = 0
            _cache_stats["reported"] = False

    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = MagicMock()
        console.print = MagicMock()
        return console

    def test_sequential_report_accumulates_stats(self, mock_console):
        """Characterization: Sequential calls accumulate stats correctly."""
        # Arrange
        global _cache_stats

        # Act - Call report_cache_status three times sequentially
        report_cache_status(mock_console, cached_count=5, resolve_count=2, skipped_empty=1)
        report_cache_status(mock_console, cached_count=3, resolve_count=1, skipped_empty=0)
        report_cache_status(mock_console, cached_count=2, resolve_count=0, skipped_empty=1)

        # Assert - Stats should be accumulated
        with _cache_stats_lock:
            assert _cache_stats["cached"] == 10
            assert _cache_stats["new"] == 3
            assert _cache_stats["skipped_empty"] == 2

    def test_concurrent_report_accumulates_stats(self, mock_console):
        """Characterization: Concurrent calls accumulate stats (may have race)."""
        # Arrange
        global _cache_stats
        num_threads = 10
        results = []
        errors = []

        def worker(thread_id):
            """Worker that calls report_cache_status."""
            try:
                # Add small delay to increase chance of race
                time.sleep(0.001)
                report_cache_status(mock_console, cached_count=1, resolve_count=1, skipped_empty=0)
                results.append(thread_id)
            except Exception as e:
                errors.append((thread_id, e))

        # Act - Spawn threads concurrently
        threads = []
        for i in range(num_threads):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Assert - All threads completed
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == num_threads

        # Characterization: What is the actual accumulated value?
        with _cache_stats_lock:
            actual_cached = _cache_stats["cached"]
            actual_new = _cache_stats["new"]

        # Current behavior: Should be num_threads if no race
        # This assertion captures the ACTUAL behavior
        assert actual_cached == num_threads, f"Expected {num_threads}, got {actual_cached}"
        assert actual_new == num_threads, f"Expected {num_threads}, got {actual_new}"


class TestPrintAggregatedCacheStatusReportedFlag:
    """Tests for 'reported' flag behavior in print_aggregated_cache_status."""

    def setup_method(self):
        """Reset global state before each test."""
        global _cache_stats, _cache_stats_lock
        with _cache_stats_lock:
            _cache_stats["cached"] = 0
            _cache_stats["new"] = 0
            _cache_stats["skipped_empty"] = 0
            _cache_stats["reported"] = False

    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = MagicMock()
        console.print = MagicMock()
        return console

    def test_first_call_sets_reported_flag(self, mock_console):
        """Characterization: First call sets reported=True."""
        # Arrange
        global _cache_stats
        with _cache_stats_lock:
            _cache_stats["cached"] = 10
            _cache_stats["new"] = 5

        # Act
        print_aggregated_cache_status(mock_console)

        # Assert - Flag should be set
        with _cache_stats_lock:
            assert _cache_stats["reported"] is True

    def test_second_call_returns_early(self, mock_console):
        """Characterization: Second call with reported=True returns early."""
        # Arrange
        global _cache_stats
        with _cache_stats_lock:
            _cache_stats["cached"] = 10
            _cache_stats["new"] = 5
            _cache_stats["reported"] = True

        # Act - Call when already reported
        initial_print_count = mock_console.print.call_count
        print_aggregated_cache_status(mock_console)

        # Assert - No additional print should occur (early return)
        assert mock_console.print.call_count == initial_print_count

    def test_prints_correct_message_format(self, mock_console):
        """Characterization: Message format for cached + new channels."""
        # Arrange
        global _cache_stats
        with _cache_stats_lock:
            _cache_stats["cached"] = 10
            _cache_stats["new"] = 5

        # Act
        print_aggregated_cache_status(mock_console)

        # Assert - Check print was called with expected format
        assert mock_console.print.called
        call_args = mock_console.print.call_args_list[0]
        # The message contains the counts
        assert "10" in str(call_args) or "10" in str(call_args[0])
        assert "5" in str(call_args) or "5" in str(call_args[0])


class TestReportedFlagRaceCondition:
    """Tests capturing the race condition between report and print."""

    def setup_method(self):
        """Reset global state before each test."""
        global _cache_stats, _cache_stats_lock
        with _cache_stats_lock:
            _cache_stats["cached"] = 0
            _cache_stats["new"] = 0
            _cache_stats["skipped_empty"] = 0
            _cache_stats["reported"] = False

    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = MagicMock()
        console.print = MagicMock()
        return console

    def test_concurrent_report_and_print_potential_race(self, mock_console):
        """Characterization: Concurrent report and print may race.

        This test captures the CURRENT BEHAVIOR when:
        - Multiple threads call report_cache_status() (writing stats)
        - One thread calls print_aggregated_cache_status() (reading stats + setting flag)

        The race: stats read and "reported" flag check/set are not atomic.
        """
        # Arrange
        global _cache_stats
        print_count = [0]
        final_stats = {}

        def reporting_worker(thread_id):
            """Worker that continuously reports stats."""
            for _ in range(100):
                report_cache_status(mock_console, cached_count=1, resolve_count=0, skipped_empty=0)
                time.sleep(0.0001)  # Tiny delay to allow context switch

        def printing_worker():
            """Worker that attempts to print aggregated stats."""
            print_aggregated_cache_status(mock_console)
            print_count[0] += 1

            # Capture stats after print
            with _cache_stats_lock:
                final_stats["cached"] = _cache_stats["cached"]
                final_stats["new"] = _cache_stats["new"]
                final_stats["reported"] = _cache_stats["reported"]

        # Act - Start threads concurrently
        report_threads = []
        for i in range(5):
            t = threading.Thread(target=reporting_worker, args=(i,))
            report_threads.append(t)
            t.start()

        # Give reporting threads time to accumulate some stats
        time.sleep(0.01)

        # Start print thread
        print_thread = threading.Thread(target=printing_worker)
        print_thread.start()

        # Wait for completion
        print_thread.join(timeout=5)
        for t in report_threads:
            t.join(timeout=5)

        # Assert - Characterize actual behavior
        assert print_count[0] == 1, "Print should have been called once"

        # Capture what actually happened
        with _cache_stats_lock:
            final_cached = _cache_stats["cached"]
            final_reported = _cache_stats["reported"]

        # Characterization: Document actual state
        # This test passes with current behavior; fix should maintain behavior
        assert final_cached > 0, "Some stats should have been accumulated"
        assert final_reported is True, "Flag should be set after print"

    def test_multiple_print_calls_only_one_succeeds(self, mock_console):
        """Characterization: Multiple concurrent print calls - only one prints.

        This test DOCUMENTS the ACTUAL behavior: the lock prevents multiple prints,
        but there is still a race between reading stats and setting the flag.
        """
        # Arrange
        global _cache_stats
        with _cache_stats_lock:
            _cache_stats["cached"] = 10
            _cache_stats["new"] = 5
            _cache_stats["reported"] = False

        print_count = [0]
        lock = threading.Lock()

        def print_worker():
            """Worker that calls print_aggregated_cache_status."""
            print_aggregated_cache_status(mock_console)
            with lock:
                print_count[0] += 1

        # Act - Spawn multiple print threads simultaneously
        threads = []
        for _ in range(10):
            t = threading.Thread(target=print_worker)
            threads.append(t)

        # Start all at once
        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Assert - Characterize: How many prints actually occurred?
        # Current behavior: Only 1 print occurs (the lock serializes access)
        assert print_count[0] >= 1, "At least one print should occur"

        # Document how many actually printed
        actual_prints = mock_console.print.call_count

        # Characterization: Current behavior results in exactly 1 print
        # The race condition is that stats are read BEFORE checking reported flag,
        # so stats could be stale by the time print occurs
        assert actual_prints == 1, f"Expected 1 print (current behavior), got {actual_prints}"


class TestReportedFlagIsolation:
    """Tests for reported flag isolation between test runs."""

    def setup_method(self):
        """Reset global state before each test."""
        global _cache_stats, _cache_stats_lock
        with _cache_stats_lock:
            _cache_stats["cached"] = 0
            _cache_stats["new"] = 0
            _cache_stats["skipped_empty"] = 0
            _cache_stats["reported"] = False

    @pytest.fixture
    def mock_console(self):
        """Create a mock Rich console."""
        console = MagicMock()
        console.print = MagicMock()
        return console

    def test_reported_flag_persists_across_calls(self, mock_console):
        """Characterization: Once set, reported flag persists until manually reset."""
        # Arrange & Act
        global _cache_stats
        with _cache_stats_lock:
            _cache_stats["cached"] = 5
            _cache_stats["new"] = 3

        print_aggregated_cache_status(mock_console)

        # Flag should be set
        with _cache_stats_lock:
            assert _cache_stats["reported"] is True

        # Try to print again - should be blocked
        mock_console.print.reset_mock()
        print_aggregated_cache_status(mock_console)

        # No new print should occur
        assert mock_console.print.call_count == 0
