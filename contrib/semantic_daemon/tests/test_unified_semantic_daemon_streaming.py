"""TDD tests for UnifiedSemanticDaemon streaming integration with JsonlWatcher.

AT-006: Integrate JsonlWatcher with UnifiedSemanticDaemon for real-time
JSONL file detection and incremental index updates.

Tests verify:
- JsonlWatcher instance is added to daemon
- Watcher thread starts on daemon initialization
- Callbacks are wired to IncrementalIndexUpdater
- Watermark state is persisted every 10 seconds

RED Phase: All tests should FAIL until implementation is complete.
"""

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Setup path - add project root
csf_root = Path(__file__).parent.parent.parent.parent.parent


class TestDaemonHasJsonlWatcherAttr:
    """Tests for JsonlWatcher attribute existence on UnifiedSemanticDaemon."""

    def test_daemon_has_jsonl_watcher_attr(self):
        """
        Test that UnifiedSemanticDaemon has a jsonl_watcher attribute.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for jsonl_watcher attribute
        Then: The attribute should exist
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        from src.ingestion.jsonl_watcher import JsonlWatcher

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "jsonl_watcher"
        ), "UnifiedSemanticDaemon should have jsonl_watcher attribute"
        assert isinstance(
            daemon.jsonl_watcher, JsonlWatcher
        ), "jsonl_watcher should be an instance of JsonlWatcher"

    def test_daemon_has_watcher_thread_attr(self):
        """
        Test that UnifiedSemanticDaemon has a watcher_thread attribute.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for watcher_thread attribute
        Then: The attribute should exist for tracking the watcher thread
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "_jsonl_watcher_thread"
        ), "UnifiedSemanticDaemon should have _jsonl_watcher_thread attribute"
        # Initially None, set when daemon starts
        assert daemon._jsonl_watcher_thread is None or isinstance(
            daemon._jsonl_watcher_thread, threading.Thread
        ), "_jsonl_watcher_thread should be None or a Thread instance"


class TestDaemonStartsJsonlWatcherThread:
    """Tests for JsonlWatcher thread starting on daemon initialization."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_daemon_starts_jsonl_watcher_thread(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that JsonlWatcher thread is started when daemon starts.

        Given: UnifiedSemanticDaemon is started
        When: The daemon reaches ready state
        Then: A JsonlWatcher thread should be running
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations to allow daemon startup
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()  # Non-blocking wait

        daemon = UnifiedSemanticDaemon()

        # Start the daemon
        started = daemon.start()

        assert started, "Daemon should start successfully"

        # Verify watcher thread was created and started
        assert hasattr(
            daemon, "_jsonl_watcher_thread"
        ), "Daemon should have _jsonl_watcher_thread attribute"
        assert (
            daemon._jsonl_watcher_thread is not None
        ), "Watcher thread should be created after daemon starts"
        assert isinstance(
            daemon._jsonl_watcher_thread, threading.Thread
        ), "_jsonl_watcher_thread should be a Thread instance"
        assert (
            daemon._jsonl_watcher_thread.is_alive()
        ), "Watcher thread should be alive after daemon starts"

        # Cleanup
        daemon.stop()

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_watcher_thread_has_correct_name(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that the JsonlWatcher thread has a descriptive name.

        Given: Daemon starts the watcher thread
        When: We check the thread name
        Then: It should have a descriptive name like 'JsonlWatcher'
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()
        daemon.start()

        assert daemon._jsonl_watcher_thread is not None
        assert (
            "jsonl" in daemon._jsonl_watcher_thread.name.lower()
            or "watcher" in daemon._jsonl_watcher_thread.name.lower()
        ), f"Thread name should contain 'jsonl' or 'watcher', got: {daemon._jsonl_watcher_thread.name}"

        daemon.stop()


class TestJsonlCallbackWiresToIncrementalUpdater:
    """Tests for callback integration with IncrementalIndexUpdater."""

    def test_daemon_has_incremental_updater_attr(self):
        """
        Test that UnifiedSemanticDaemon has an incremental_updater attribute.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for incremental_updater attribute
        Then: The attribute should exist
        """
        from search_research.backends.local.chs_incremental import (
            IncrementalIndexUpdater,
        )
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "_incremental_updater"
        ), "UnifiedSemanticDaemon should have _incremental_updater attribute"
        assert isinstance(
            daemon._incremental_updater, IncrementalIndexUpdater
        ), "_incremental_updater should be an instance of IncrementalIndexUpdater"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    @patch("src.ingestion.jsonl_watcher.win32file.ReadDirectoryChangesW")
    def test_jsonl_callback_wires_to_incremental_updater(
        self,
        mock_read_changes,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that JsonlWatcher callback is wired to IncrementalIndexUpdater.

        Given: Daemon is running with JsonlWatcher active
        When: A JSONL file change is detected
        Then: IncrementalIndexUpdater should be called with the file path
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        # Mock ReadDirectoryChangesW to return empty (no changes for basic test)
        mock_read_changes.return_value = []

        daemon = UnifiedSemanticDaemon()
        daemon.start()

        # Verify that callback wiring exists
        # The callback should be a method that calls _incremental_updater
        assert hasattr(
            daemon, "_on_jsonl_file_changed"
        ), "Daemon should have _on_jsonl_file_changed callback method"

        # Verify the callback is callable
        assert callable(daemon._on_jsonl_file_changed), "_on_jsonl_file_changed should be callable"

        daemon.stop()

    def test_callback_calls_incremental_updater_with_file_path(self):
        """
        Test that the callback method calls IncrementalIndexUpdater with file path.

        Given: Daemon with IncrementalIndexUpdater
        When: _on_jsonl_file_changed is called with a file path
        Then: IncrementalIndexUpdater.update_from_file() should be called
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Mock the incremental updater to track calls
        update_called = []
        original_update = daemon._incremental_updater.update_from_file

        def mock_update(file_path):
            update_called.append(file_path)

        daemon._incremental_updater.update_from_file = mock_update

        # Call the callback
        test_file = "/path/to/test.jsonl"
        daemon._on_jsonl_file_changed(test_file)

        # Verify updater was called
        assert len(update_called) > 0, "IncrementalIndexUpdater.update_from_file should be called"
        assert (
            update_called[0] == test_file
        ), f"Updater should be called with {test_file}, got {update_called[0]}"


class TestWatermarkStatePersisted:
    """Tests for watermark state persistence every 10 seconds."""

    def test_daemon_has_watermark_state_attr(self):
        """
        Test that UnifiedSemanticDaemon tracks watermark state.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for watermark state attributes
        Then: Watermark tracking attributes should exist
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "_watermark_state"
        ), "UnifiedSemanticDaemon should have _watermark_state attribute"
        assert isinstance(daemon._watermark_state, dict), "_watermark_state should be a dict"

    def test_daemon_has_last_watermark_save_time(self):
        """
        Test that daemon tracks last watermark save time.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for last save time attribute
        Then: The attribute should exist
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "_last_watermark_save_time"
        ), "UnifiedSemanticDaemon should have _last_watermark_save_time attribute"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    @patch("time.sleep")  # Mock sleep to control timing
    def test_watermark_state_persisted_every_10_seconds(
        self,
        mock_sleep,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that watermark state is persisted every 10 seconds.

        Given: Daemon is running
        When: 10 seconds pass
        Then: Watermark state should be persisted to disk
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event

        # Track persistence calls
        persist_calls = []
        persist_file_path = None

        def mock_write_text(path, content):
            persist_calls.append((path, content))

        mock_create_file.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Mock the _persist_watermark_state method
        original_persist = daemon._persist_watermark_state

        def mock_persist():
            persist_calls.append(time.time())

        daemon._persist_watermark_state = mock_persist

        # Set initial save time in the past
        daemon._last_watermark_save_time = time.time() - 11  # 11 seconds ago

        # Trigger idle work which should check watermark persistence
        daemon.check_idle_work()

        # Verify persistence was called
        assert (
            len(persist_calls) > 0
        ), "Watermark state should be persisted when 10 seconds have elapsed"

    def test_watermark_state_path_exists(self):
        """
        Test that watermark state file path is configured.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for watermark state path
        Then: A valid path should be configured
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "_watermark_state_path"
        ), "UnifiedSemanticDaemon should have _watermark_state_path attribute"
        assert daemon._watermark_state_path is not None, "Watermark state path should not be None"
        assert isinstance(
            daemon._watermark_state_path, Path
        ), "Watermark state path should be a Path object"
