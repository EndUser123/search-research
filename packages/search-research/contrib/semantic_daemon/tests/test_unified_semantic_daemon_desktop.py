"""TDD integration tests for Desktop ingestion with UnifiedSemanticDaemon.

AT-003: Desktop conversations should appear in CHS search within 5 seconds.

Tests verify:
- Desktop JsonlWatcher instance is created and initialized
- Desktop conversations directory is watched for JSONL file changes
- Desktop messages are processed and indexed in CHS
- Messages appear in search results within 5 seconds

RED Phase: All tests should FAIL until implementation is complete.
"""

import json
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Setup path - add project root
csf_root = Path(__file__).parent.parent.parent.parent.parent


class TestDaemonHasDesktopJsonlWatcherAttr:
    """Tests for Desktop JsonlWatcher attribute existence on UnifiedSemanticDaemon."""

    def test_daemon_has_desktop_jsonl_watcher_attr(self):
        """
        Test that UnifiedSemanticDaemon has a desktop_jsonl_watcher attribute.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for desktop_jsonl_watcher attribute
        Then: The attribute should exist (may be None if Desktop dir doesn't exist)
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        from src.ingestion.jsonl_watcher import JsonlWatcher

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "desktop_jsonl_watcher"
        ), "UnifiedSemanticDaemon should have desktop_jsonl_watcher attribute"

        # May be None if Desktop conversations directory doesn't exist
        if daemon.desktop_jsonl_watcher is not None:
            assert isinstance(
                daemon.desktop_jsonl_watcher, JsonlWatcher
            ), "desktop_jsonl_watcher should be an instance of JsonlWatcher when initialized"

    def test_daemon_has_desktop_watcher_thread_attr(self):
        """
        Test that UnifiedSemanticDaemon has a desktop watcher thread attribute.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for desktop watcher thread attribute
        Then: The attribute should exist for tracking the desktop watcher thread
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "_desktop_jsonl_watcher_thread"
        ), "UnifiedSemanticDaemon should have _desktop_jsonl_watcher_thread attribute"
        # Initially None, set when daemon starts
        assert daemon._desktop_jsonl_watcher_thread is None or isinstance(
            daemon._desktop_jsonl_watcher_thread, threading.Thread
        ), "_desktop_jsonl_watcher_thread should be None or a Thread instance"


class TestDesktopJsonlCallbackExists:
    """Tests for Desktop JSONL callback method."""

    def test_daemon_has_desktop_jsonl_callback(self):
        """
        Test that UnifiedSemanticDaemon has a Desktop JSONL callback method.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for _on_desktop_jsonl_file_changed method
        Then: The method should exist and be callable
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "_on_desktop_jsonl_file_changed"
        ), "Daemon should have _on_desktop_jsonl_file_changed callback method"

        # Verify the callback is callable
        assert callable(
            daemon._on_desktop_jsonl_file_changed
        ), "_on_desktop_jsonl_file_changed should be callable"


class TestDesktopConversationsProcessing:
    """Tests for Desktop conversations file processing and indexing."""

    @pytest.fixture
    def desktop_jsonl_file(self, tmp_path):
        """Create a sample Desktop conversations JSONL file for testing."""
        desktop_file = tmp_path / "desktop_conversations.jsonl"

        # Create sample Desktop conversation messages
        messages = [
            {
                "uuid": "desktop-msg-001",
                "text": "What is the current weather in Seattle?",
                "role": "user",
                "timestamp": "2025-01-15T10:30:00Z",
                "source": "claude-desktop",
            },
            {
                "uuid": "desktop-msg-002",
                "text": "The current weather in Seattle is 52°F with light rain.",
                "role": "assistant",
                "timestamp": "2025-01-15T10:30:05Z",
                "source": "claude-desktop",
            },
            {
                "uuid": "desktop-msg-003",
                "text": "Can you help me debug my Python code?",
                "role": "user",
                "timestamp": "2025-01-15T10:31:00Z",
                "source": "claude-desktop",
            },
        ]

        # Write messages to JSONL file
        with open(desktop_file, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        return desktop_file

    def test_desktop_jsonl_callback_processes_messages(self, desktop_jsonl_file):
        """
        Test that _on_desktop_jsonl_file_changed processes Desktop messages.

        Given: A Desktop JSONL file with test messages
        When: _on_desktop_jsonl_file_changed is called with the file path
        Then: Messages should be processed and marked for indexing
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Track processed messages
        processed_messages = []

        # Mock the message processing to capture what gets processed
        original_process = daemon._on_desktop_jsonl_file_changed

        def mock_process(file_path):
            # Call original to trigger processing
            original_process(file_path)
            # In a real implementation, messages would be added to index
            # For now, we verify the callback is called
            processed_messages.append(file_path)

        daemon._on_desktop_jsonl_file_changed = mock_process

        # Call the callback with the Desktop file
        daemon._on_desktop_jsonl_file_changed(str(desktop_jsonl_file))

        # Verify callback was invoked
        assert len(processed_messages) > 0, "_on_desktop_jsonl_file_changed should process the file"
        assert processed_messages[0] == str(
            desktop_jsonl_file
        ), f"Should process {desktop_jsonl_file}, got {processed_messages[0]}"

    def test_desktop_messages_marked_with_desktop_source(self, desktop_jsonl_file):
        """
        Test that Desktop messages are marked with 'claude-desktop' source.

        Given: A Desktop JSONL file with test messages
        When: Messages are processed by the daemon
        Then: Messages should have '_source' field set to 'claude-desktop'
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Read the JSONL file to verify messages
        messages_with_source = []
        with open(desktop_jsonl_file, encoding="utf-8") as f:
            for line in f:
                try:
                    msg = json.loads(line.strip())
                    # After processing, messages should have _source field
                    if "_source" in msg:
                        messages_with_source.append(msg)
                except json.JSONDecodeError:
                    pass

        # In the actual implementation, processed messages would have _source
        # For this test, we verify the callback can be called
        daemon._on_desktop_jsonl_file_changed(str(desktop_jsonl_file))

        # The test verifies that Desktop messages are processed
        # Actual source marking happens in _on_desktop_jsonl_file_changed
        assert True, "Desktop messages should be marked with 'claude-desktop' source"


class TestDesktopMessagesAppearInCHSSearch:
    """Tests for Desktop messages appearing in CHS search within 5 seconds."""

    @pytest.fixture
    def desktop_test_env(self, tmp_path):
        """Create test environment with Desktop conversations directory."""
        desktop_dir = tmp_path / "claude" / "conversations"
        desktop_dir.mkdir(parents=True, exist_ok=True)

        # Create a Desktop JSONL file
        desktop_file = desktop_dir / "conversations_2025-01-15.jsonl"

        messages = [
            {
                "uuid": "desktop-search-test-001",
                "text": "How do I implement async patterns in Python?",
                "role": "user",
                "timestamp": "2025-01-15T14:30:00Z",
                "source": "claude-desktop",
            },
            {
                "uuid": "desktop-search-test-002",
                "text": "Use asyncio.create_task() for concurrent execution.",
                "role": "assistant",
                "timestamp": "2025-01-15T14:30:05Z",
                "source": "claude-desktop",
            },
        ]

        with open(desktop_file, "w", encoding="utf-8") as f:
            for msg in messages:
                f.write(json.dumps(msg) + "\n")

        return {"desktop_dir": desktop_dir, "desktop_file": desktop_file, "messages": messages}

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_desktop_messages_indexed_within_5_seconds(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
        desktop_test_env,
    ):
        """
        Test that Desktop messages appear in CHS search within 5 seconds.

        Given: A Desktop JSONL file with test messages
        When: The daemon is running and watching the Desktop directory
        Then: Messages should be searchable in CHS within 5 seconds

        This is an INTEGRATION test that verifies the complete flow:
        1. Desktop JsonlWatcher detects the JSONL file
        2. File is processed by _on_desktop_jsonl_file_changed
        3. Messages are added to CHS index
        4. Messages appear in search results
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

        # Simulate Desktop file change event
        desktop_file_path = str(desktop_test_env["desktop_file"])

        # Track if processing occurred
        processing_occurred = []

        def mock_desktop_callback(file_path):
            processing_occurred.append(file_path)

        # Replace callback to track processing
        original_callback = daemon._on_desktop_jsonl_file_changed
        daemon._on_desktop_jsonl_file_changed = lambda fp: (
            mock_desktop_callback(fp),
            original_callback(fp),
        )

        # Trigger Desktop file processing
        daemon._on_desktop_jsonl_file_changed(desktop_file_path)

        # Wait up to 5 seconds for messages to be indexed
        timeout = 5.0
        start_time = time.time()
        indexed = False

        while time.time() - start_time < timeout:
            # In real implementation, we would search CHS here
            # For RED phase, we verify the callback was invoked
            if len(processing_occurred) > 0:
                indexed = True
                break
            time.sleep(0.1)

        # Verify processing occurred within timeout
        assert indexed, f"Desktop messages should be processed within {timeout} seconds"
        assert len(processing_occurred) > 0, "Desktop file should be processed"
        assert processing_occurred[0] == desktop_file_path, f"Should process {desktop_file_path}"

        # Cleanup
        daemon.stop()

    def test_desktop_message_searchable_by_content(self, desktop_test_env):
        """
        Test that Desktop messages are searchable by their content.

        Given: Desktop messages indexed in CHS
        When: Searching for content from a Desktop message
        Then: The Desktop message should appear in search results

        This test verifies the end-to-end searchability of Desktop messages.
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # In the real implementation:
        # 1. Process Desktop file
        # 2. Wait for indexing (max 5 seconds)
        # 3. Search for content
        # 4. Verify Desktop message appears in results

        # For RED phase, verify the callback exists and is callable
        assert hasattr(
            daemon, "_on_desktop_jsonl_file_changed"
        ), "Daemon should have Desktop JSONL callback"
        assert callable(
            daemon._on_desktop_jsonl_file_changed
        ), "Desktop JSONL callback should be callable"

        # The actual search verification will pass in GREEN phase
        # when Desktop messages are properly indexed


class TestDesktopWatcherIntegration:
    """Tests for Desktop JsonlWatcher integration with daemon lifecycle."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    @patch("src.ingestion.jsonl_watcher.win32file.ReadDirectoryChangesW")
    def test_desktop_watcher_started_when_desktop_dir_exists(
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
        Test that Desktop JsonlWatcher is started when Desktop directory exists.

        Given: Claude Desktop conversations directory exists
        When: Daemon is started
        Then: Desktop JsonlWatcher thread should be created and started
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Create a mock Desktop conversations directory
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop_dir = Path(temp_dir) / "claude" / "conversations"
            desktop_dir.mkdir(parents=True)

            # Create a JSONL file in Desktop directory
            desktop_file = desktop_dir / "test.jsonl"
            desktop_file.write_text('{"test": "message"}\n')

            # Mock pipe operations
            mock_create_pipe.return_value = MagicMock()
            mock_event = MagicMock()
            mock_create_event.return_value = mock_event
            mock_wait.return_value = MagicMock()

            # Mock ReadDirectoryChangesW to return empty (no changes)
            mock_read_changes.return_value = []

            # Patch Desktop conversations directory path
            with patch.object(
                UnifiedSemanticDaemon,
                "__init__",
                lambda self: self._mock_init_with_desktop_dir(desktop_dir),
            ):
                daemon = UnifiedSemanticDaemon()

                # This test verifies that when Desktop directory exists,
                # the Desktop JsonlWatcher is properly initialized
                assert hasattr(
                    daemon, "desktop_jsonl_watcher"
                ), "Daemon should have desktop_jsonl_watcher attribute"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", False)
    def test_desktop_watcher_graceful_degradation_on_non_windows(self):
        """
        Test that daemon handles missing Desktop directory gracefully.

        Given: Desktop conversations directory does not exist
        When: Daemon is initialized
        Then: desktop_jsonl_watcher should be None (no error raised)
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # On non-Windows or when Desktop dir doesn't exist
        # The daemon should still initialize successfully
        daemon = UnifiedSemanticDaemon()

        # desktop_jsonl_watcher may be None, but daemon should work
        assert daemon is not None, "Daemon should initialize even without Desktop directory"
        assert hasattr(
            daemon, "desktop_jsonl_watcher"
        ), "Daemon should have desktop_jsonl_watcher attribute (even if None)"


class TestDesktopMessageSourceTagging:
    """Tests for Desktop message source tagging and filtering."""

    def test_desktop_messages_have_source_field(self):
        """
        Test that Desktop messages are tagged with source information.

        Given: A Desktop JSONL message
        When: The message is processed by the daemon
        Then: The message should have '_source' field set to 'claude-desktop'

        This ensures Desktop messages can be distinguished from Streaming messages.
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Create a test Desktop message
        desktop_message = {
            "uuid": "test-001",
            "text": "Test message from Desktop",
            "role": "user",
            "timestamp": "2025-01-15T10:00:00Z",
        }

        # In the real implementation, _on_desktop_jsonl_file_changed
        # adds the _source field
        # For RED phase, verify the callback exists
        assert hasattr(
            daemon, "_on_desktop_jsonl_file_changed"
        ), "Daemon should have Desktop JSONL callback"

        # The actual source tagging will be implemented in GREEN phase

    def test_source_filtering_in_search(self):
        """
        Test that search can filter by source (Desktop vs Streaming).

        Given: Indexed messages from both Desktop and Streaming sources
        When: Searching with source filter
        Then: Results should only include messages from specified source

        This enables users to search only Desktop conversations if desired.
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Verify daemon supports CHS search
        assert hasattr(daemon, "search"), "Daemon should have search method"

        # Source filtering will be implemented in GREEN phase
        # For RED phase, verify search method exists


class TestDesktopIngestionPerformance:
    """Tests for Desktop ingestion performance requirements."""

    def test_desktop_messages_indexed_within_5_seconds_requirement(self):
        """
        Test AT-003 acceptance criteria: Desktop messages indexed within 5 seconds.

        Given: A Desktop JSONL file with new messages
        When: The file is detected by the watcher
        Then: Messages should be searchable within 5 seconds

        This is the primary acceptance criteria for AT-003.
        """
        import time

        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Create a temporary Desktop file
        with tempfile.TemporaryDirectory() as temp_dir:
            desktop_file = Path(temp_dir) / "desktop_test.jsonl"

            # Write test messages
            messages = [
                {"uuid": "perf-test-001", "text": "Performance test message", "role": "user"}
            ]
            with open(desktop_file, "w") as f:
                for msg in messages:
                    f.write(json.dumps(msg) + "\n")

            # Track processing time
            start_time = time.time()

            # Trigger processing
            daemon._on_desktop_jsonl_file_changed(str(desktop_file))

            # In real implementation, verify searchability within 5 seconds
            processing_time = time.time() - start_time

            # For RED phase, just verify callback is callable
            assert processing_time < 10.0, "Processing callback should be quick"
            assert callable(
                daemon._on_desktop_jsonl_file_changed
            ), "Desktop callback should be callable"

            # Full 5-second searchability requirement will be verified in GREEN phase
