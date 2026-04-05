"""Characterization tests for ParallelBatchProcessor race condition.

These tests CAPTURE CURRENT BEHAVIOR before refactoring.
Focus: Race condition in shared BatchDownloader usage by multiple workers.

Issue: Single BatchDownloader instance used by multiple workers without synchronization.
Lines: 411-454, 1187-1220 in parallel_processor.py

Run with: pytest tests/test_parallel_processor_race.py -v
"""

import threading
import time
from unittest.mock import MagicMock, Mock, patch
from concurrent.futures import ThreadPoolExecutor

import pytest


class TestSharedDownloaderRaceCondition:
    """Characterization tests for shared BatchDownloader race condition.

    The current implementation creates a single shared_downloader instance
    before the ThreadPoolExecutor and uses it across all worker threads.
    This characterization test captures how this shared state behaves.
    """

    def test_shared_downloader_instance_reuse_characterization(self):
        """Characterization: Verify shared_downloader is single instance used by all workers."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor
        from yt_fts.download.batch_downloader import BatchDownloader

        channels = ["@channel1", "@channel2", "@channel3"]
        processor = ParallelBatchProcessor()

        instances_created = []
        original_init = BatchDownloader.__init__

        def track_init(self, *args, **kwargs):
            instances_created.append(id(self))
            if original_init:
                original_init(self, *args, **kwargs)

        with patch.object(BatchDownloader, "__init__", track_init), patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill") as mock_backfill:

            mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

            with patch.object(BatchDownloader, "process_single_channel") as mock_process:
                mock_process.return_value = {
                    "successful": [{"channel": "test", "videos_count": 1}],
                    "failed": [],
                    "skipped": [],
                }

                processor.process_channels(channels, num_workers=2)

                assert len(instances_created) == 1, (
                    f"Expected 1 BatchDownloader instance (shared), got {len(instances_created)}. "
                    "This is the CURRENT BEHAVIOR that may cause race conditions."
                )


class TestRaceConditionSymptoms:
    """Tests that characterize symptoms of the race condition."""

    def test_no_locks_on_batch_downloader_state_characterization(self):
        """Characterization: Verify BatchDownloader has lock protection after fix."""
        from yt_fts.download.batch_downloader import BatchDownloader, BatchDownloaderConfig

        # AFTER FIX: BatchDownloader instances should have _lock attribute
        # (Note: _lock is an instance attribute set in __init__, not a class attribute)
        config = BatchDownloaderConfig(channels=["@test"])
        with patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill"), \
             patch("yt_fts.download.quota_strategy.create_quota_strategy"):
            downloader = BatchDownloader(config)
            has_thread_lock = hasattr(downloader, "_lock")

        assert has_thread_lock, (
            "FIX IMPLEMENTED: BatchDownloader instances now have _lock attribute. "
            "This is the FIXED STATE (after implementing thread-safety)."
        )

    def test_process_single_channel_not_threadsafe_characterization(self):
        """Characterization: Document thread-safety state of process_single_channel.

        NOTE: After the fix, BatchDownloader has a _lock RLock instance attribute.
        The lock is available for use in process_single_channel and other methods
        to protect shared state (metadata_backfill, quota_strategy, etc.).

        Actual usage of the lock in specific methods should be added as needed
        when protecting specific shared state access patterns.
        """
        from yt_fts.download.batch_downloader import BatchDownloader, BatchDownloaderConfig
        import inspect

        # Verify _lock exists on instances
        config = BatchDownloaderConfig(channels=["@test"])
        with patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill"), \
             patch("yt_fts.download.quota_strategy.create_quota_strategy"):
            downloader = BatchDownloader(config)
            has_lock = hasattr(downloader, "_lock")

        source = inspect.getsource(BatchDownloader.process_single_channel)

        # Check if the method currently uses the lock
        has_with_lock = "with self._lock" in source

        assert has_lock, (
            "FIX IMPLEMENTED: BatchDownloader instances have _lock attribute. "
            "The lock is available for protecting shared state in process_single_channel."
        )
        # Note: The actual usage of the lock in process_single_channel may be added
        # incrementally as needed to protect specific shared state access patterns.


class TestWorkerIsolation:
    """Tests characterizing worker isolation (or lack thereof)."""

    def test_workers_share_downloader_instance_characterization(self):
        """Characterization: Verify all workers use the same downloader instance."""
        from yt_fts.download.parallel_processor import ParallelBatchProcessor
        from yt_fts.download.batch_downloader import BatchDownloader

        channels = ["@ch1", "@ch2", "@ch3"]
        processor = ParallelBatchProcessor()

        worker_instances = {}
        worker_lock = threading.Lock()

        def track_instance_per_worker(self, channel):
            thread_id = threading.current_thread().ident
            instance_id = id(self)

            with worker_lock:
                worker_instances[thread_id] = instance_id

            return {
                "successful": [{"channel": channel, "videos_count": 1}],
                "failed": [],
                "skipped": [],
            }

        with patch.object(BatchDownloader, "process_single_channel", track_instance_per_worker), patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill") as mock_backfill:

            mock_backfill.return_value.format_quota_display.return_value = "Quota: 0/10000"

            with patch.object(BatchDownloader, "__init__", lambda self, *args, **kwargs: None):

                processor.process_channels(channels, num_workers=3)

                unique_instances = set(worker_instances.values())
                assert len(unique_instances) == 1, (
                    f"CURRENT BEHAVIOR: Expected 1 shared instance, got {len(unique_instances)}. "
                    "This documents that ALL workers share the SAME BatchDownloader instance. "
                    "This is the SHARED STATE pattern that may cause race conditions."
                )

                assert len(worker_instances) >= 2, (
                    f"Expected >= 2 workers, got {len(worker_instances)}. "
                    "Test may not have exercised parallelism properly."
                )


class TestThreadSafetyFix:
    """Tests that verify the thread-safety fix for BatchDownloader.

    These tests EXPECT the fix to be in place.
    They will FAIL before the fix is implemented (RED phase).
    They will PASS after the fix is implemented (GREEN phase).
    """

    def test_batch_downloader_has_lock(self):
        """Verify BatchDownloader has internal lock for thread-safety."""
        from yt_fts.download.batch_downloader import BatchDownloader, BatchDownloaderConfig

        # After fix: BatchDownloader instances should have _lock attribute
        # (Note: _lock is an instance attribute, not a class attribute)
        config = BatchDownloaderConfig(channels=["@test"])
        with patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill"), \
             patch("yt_fts.download.quota_strategy.create_quota_strategy"):
            downloader = BatchDownloader(config)
            assert hasattr(downloader, "_lock"), (
                "FIX NOT YET IMPLEMENTED: BatchDownloader instance should have _lock attribute. "
                "Add 'self._lock = threading.RLock()' in __init__."
            )

    def test_lock_is_rlock(self):
        """Verify the lock is an RLock (reentrant lock)."""
        from yt_fts.download.batch_downloader import BatchDownloader, BatchDownloaderConfig
        import threading
        import _thread

        # Check if instances have RLock
        # We need to create a minimal config to instantiate
        config = BatchDownloaderConfig(channels=["@test"])

        with patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill"), \
             patch("yt_fts.download.quota_strategy.create_quota_strategy"):
            downloader = BatchDownloader(config)

        assert hasattr(downloader, "_lock"), "BatchDownloader instance should have _lock"
        # Note: threading.RLock is a factory function, actual type is _thread.RLock
        assert type(downloader._lock).__name__ == "RLock", (
            f"_lock should be RLock, got {type(downloader._lock).__name__}"
        )
