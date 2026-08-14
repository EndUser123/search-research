"""TDD tests for UnifiedSemanticDaemon health check endpoint.

AT-009: Add health check for index freshness and path consistency

Tests verify:
- /health endpoint exists and returns JSON
- Health check returns status: healthy when all checks pass
- Health check returns status: degraded when DB missing
- Health check returns status: degraded when FAISS missing
- Health check returns status: degraded when watermark stale (>30s)
- Health check response includes checked paths and watermark age

RED Phase: All tests should FAIL until implementation is complete.
"""

import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Setup path - add project root
csf_root = Path(__file__).parent.parent.parent.parent.parent


class TestHealthEndpointExists:
    """Tests for health endpoint existence."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_health_action_returns_response(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health action is recognized and returns a response.

        Given: UnifiedSemanticDaemon is running
        When: A request with action="health" is processed
        Then: The daemon should return a health check response
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

        # Create health check request
        request = {"action": "health"}

        # Process the request
        response = daemon._process_request(request)

        # Verify response structure
        assert response is not None, "Health check should return a response"
        assert isinstance(response, dict), "Health check response should be a dictionary"
        assert "status" in response, "Health check response should include 'status' field"

    def test_health_endpoint_via_client(self):
        """
        Test that health endpoint can be called via client.

        Given: Daemon is running with health endpoint
        When: Client sends health check request
        Then: Client should receive health status response

        Note: This test verifies the client API for health checks.
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Verify daemon has health check capability
        # (This will be implemented as a method or action handler)
        assert hasattr(
            daemon, "_process_request"
        ), "Daemon should have _process_request method for handling actions"

        # Health action should return status field (will fail until implemented)
        request = {"action": "health"}
        response = daemon._process_request(request)

        # This assertion will fail until health action is implemented
        # Currently it returns {'error': 'Empty query', 'results': [], 'scope': 'cks'}
        assert response.get("status") in (
            "healthy",
            "degraded",
        ), "Health action should return status field with 'healthy' or 'degraded'"


class TestHealthCheckWhenAllHealthy:
    """Tests for health check status when all systems are healthy."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_healthy_when_db_exists(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check returns healthy when DB exists.

        Given: Chat history database exists at expected path
        When: Health check is performed
        Then: Status should be 'healthy' and db_exists should be True
        """
        from pathlib import Path

        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Create a temporary DB file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            temp_db_path = Path(f.name)
            f.write("")  # Empty DB file

        try:
            # Mock _get_chs_db_path to return temp file
            with patch.object(daemon, "_get_chs_db_path", return_value=temp_db_path):
                # Mock FAISS_INDEX_PATH constant to exist
                with patch(
                    "search_research.contrib.semantic_daemon.unified_semantic_daemon.FAISS_INDEX_PATH", temp_db_path.parent
                ):
                    # Set recent watermark time
                    daemon._last_watermark_save_time = time.time()

                    request = {"action": "health"}
                    response = daemon._process_request(request)

                    assert (
                        response.get("status") == "healthy"
                    ), f"Status should be healthy when all checks pass, got {response.get('status')}"
                    assert (
                        response.get("db_exists") is True
                    ), "db_exists should be True when DB file exists"
        finally:
            # Cleanup temp file
            if temp_db_path.exists():
                temp_db_path.unlink()

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_healthy_when_faiss_exists(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check returns healthy when FAISS index exists.

        Given: FAISS index exists at expected path
        When: Health check is performed
        Then: Status should be 'healthy' and faiss_exists should be True
        """
        from pathlib import Path

        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Create temporary FAISS directory
        with tempfile.TemporaryDirectory() as temp_dir:
            faiss_path = Path(temp_dir)
            # Create index file
            (faiss_path / "index.faiss").touch()

            # Mock paths to exist
            with patch.object(
                daemon, "_get_chs_db_path", return_value=faiss_path / "chat_history.db"
            ):
                # Create DB
                (faiss_path / "chat_history.db").touch()

                with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.FAISS_INDEX_PATH", faiss_path):
                    # Set recent watermark time
                    daemon._last_watermark_save_time = time.time()

                    request = {"action": "health"}
                    response = daemon._process_request(request)

                    assert (
                        response.get("status") == "healthy"
                    ), f"Status should be healthy when FAISS exists, got {response.get('status')}"
                    assert (
                        response.get("faiss_exists") is True
                    ), "faiss_exists should be True when FAISS index exists"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_healthy_when_watermark_fresh(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check returns healthy when watermark is fresh (<30s).

        Given: Watermark was saved less than 30 seconds ago
        When: Health check is performed
        Then: Status should be 'healthy' and watermark_age should be < 30
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Set watermark time to recent (5 seconds ago)
        daemon._last_watermark_save_time = time.time() - 5.0

        # Mock DB and FAISS to exist
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "chat_history.db").touch()
            (temp_path / "index.faiss").touch()

            with patch.object(
                daemon, "_get_chs_db_path", return_value=temp_path / "chat_history.db"
            ):
                with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.FAISS_INDEX_PATH", temp_path):
                    request = {"action": "health"}
                    response = daemon._process_request(request)

                    assert (
                        response.get("status") == "healthy"
                    ), "Status should be healthy when watermark is fresh"
                    assert (
                        "watermark_age_seconds" in response
                    ), "Response should include watermark_age_seconds"
                    assert (
                        response.get("watermark_age_seconds") < 30
                    ), f"watermark_age should be < 30 seconds, got {response.get('watermark_age_seconds')}"


class TestHealthCheckWhenDegraded:
    """Tests for health check status when systems are degraded."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_degraded_when_db_missing(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check returns degraded when DB is missing.

        Given: Chat history database does not exist
        When: Health check is performed
        Then: Status should be 'degraded' and db_exists should be False
        """
        from pathlib import Path

        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Mock _get_chs_db_path to return non-existent path
        non_existent_db = Path("/tmp/does_not_exist_chat_history.db")

        with patch.object(daemon, "_get_chs_db_path", return_value=non_existent_db):
            # Set recent watermark time
            daemon._last_watermark_save_time = time.time()

            request = {"action": "health"}
            response = daemon._process_request(request)

            assert (
                response.get("status") == "degraded"
            ), f"Status should be degraded when DB is missing, got {response.get('status')}"
            assert (
                response.get("db_exists") is False
            ), "db_exists should be False when DB file does not exist"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_degraded_when_faiss_missing(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check returns degraded when FAISS index is missing.

        Given: FAISS index does not exist at expected path
        When: Health check is performed
        Then: Status should be 'degraded' and faiss_exists should be False
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Mock FAISS path to non-existent directory
        non_existent_faiss = Path("/tmp/does_not_exist_faiss")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            temp_db = Path(f.name)

        try:
            with patch.object(daemon, "_get_chs_db_path", return_value=temp_db):
                with patch(
                    "search_research.contrib.semantic_daemon.unified_semantic_daemon.FAISS_INDEX_PATH", non_existent_faiss
                ):
                    # Set recent watermark time
                    daemon._last_watermark_save_time = time.time()

                    request = {"action": "health"}
                    response = daemon._process_request(request)

                    assert (
                        response.get("status") == "degraded"
                    ), f"Status should be degraded when FAISS is missing, got {response.get('status')}"
                    assert (
                        response.get("faiss_exists") is False
                    ), "faiss_exists should be False when FAISS index does not exist"
        finally:
            if temp_db.exists():
                temp_db.unlink()

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_degraded_when_watermark_stale(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check returns degraded when watermark is stale (>30s).

        Given: Watermark was saved more than 30 seconds ago
        When: Health check is performed
        Then: Status should be 'degraded' and watermark_age should be > 30
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Set watermark time to stale (60 seconds ago)
        daemon._last_watermark_save_time = time.time() - 60.0

        # Mock DB and FAISS to exist
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "chat_history.db").touch()
            (temp_path / "index.faiss").touch()

            with patch.object(
                daemon, "_get_chs_db_path", return_value=temp_path / "chat_history.db"
            ):
                with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.FAISS_INDEX_PATH", temp_path):
                    request = {"action": "health"}
                    response = daemon._process_request(request)

                    assert (
                        response.get("status") == "degraded"
                    ), "Status should be degraded when watermark is stale"
                    assert (
                        "watermark_age_seconds" in response
                    ), "Response should include watermark_age_seconds"
                    assert (
                        response.get("watermark_age_seconds") >= 30
                    ), f"watermark_age should be >= 30 seconds for degraded, got {response.get('watermark_age_seconds')}"


class TestHealthCheckResponseFields:
    """Tests for health check response field completeness."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_response_includes_db_path(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check response includes the DB path being checked.

        Given: Health check is performed
        When: Response is returned
        Then: Response should include db_path field
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
            temp_db = Path(f.name)

        try:
            with patch.object(daemon, "_get_chs_db_path", return_value=temp_db):
                request = {"action": "health"}
                response = daemon._process_request(request)

                assert "db_path" in response, "Health check response should include db_path"
                assert isinstance(
                    response.get("db_path"), (str, Path)
                ), "db_path should be a string or Path object"
        finally:
            if temp_db.exists():
                temp_db.unlink()

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_response_includes_faiss_path(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check response includes the FAISS path being checked.

        Given: Health check is performed
        When: Response is returned
        Then: Response should include faiss_path field
        """
        from pathlib import Path

        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Use actual FAISS_INDEX_PATH constant

        request = {"action": "health"}
        response = daemon._process_request(request)

        assert "faiss_path" in response, "Health check response should include faiss_path"
        assert isinstance(
            response.get("faiss_path"), (str, Path)
        ), "faiss_path should be a string or Path object"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_response_includes_watermark_age(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check response includes watermark age.

        Given: Health check is performed
        When: Response is returned
        Then: Response should include watermark_age_seconds field
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Set a specific watermark time
        test_time = time.time() - 15.0  # 15 seconds ago
        daemon._last_watermark_save_time = test_time

        request = {"action": "health"}
        response = daemon._process_request(request)

        assert (
            "watermark_age_seconds" in response
        ), "Health check response should include watermark_age_seconds"
        assert isinstance(
            response.get("watermark_age_seconds"), (int, float)
        ), "watermark_age_seconds should be a number"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_response_includes_all_status_fields(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that health check response includes all status fields.

        Given: Health check is performed
        When: Response is returned
        Then: Response should include status, db_exists, faiss_exists,
              and watermark_age_seconds fields
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        request = {"action": "health"}
        response = daemon._process_request(request)

        # Verify all required fields are present
        required_fields = ["status", "db_exists", "faiss_exists", "watermark_age_seconds"]

        for field in required_fields:
            assert field in response, f"Health check response should include '{field}' field"


class TestHealthCheckIntegration:
    """Integration tests for health check functionality."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_health_check_with_all_healthy(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test complete health check when all systems are healthy.

        Given: DB exists, FAISS exists, watermark is fresh
        When: Health check is performed
        Then: Response should indicate healthy status with all checks passing
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Set up healthy state
        daemon._last_watermark_save_time = time.time() - 5.0  # 5 seconds ago

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "chat_history.db").touch()
            (temp_path / "index.faiss").touch()

            with patch.object(
                daemon, "_get_chs_db_path", return_value=temp_path / "chat_history.db"
            ):
                with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.FAISS_INDEX_PATH", temp_path):
                    request = {"action": "health"}
                    response = daemon._process_request(request)

                    # Verify healthy status
                    assert (
                        response.get("status") == "healthy"
                    ), "All systems healthy should return status=healthy"

                    # Verify all checks pass
                    assert response.get("db_exists") is True, "DB should exist"
                    assert response.get("faiss_exists") is True, "FAISS should exist"
                    assert (
                        response.get("watermark_age_seconds") < 30
                    ), "Watermark should be fresh (<30s)"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_health_check_with_multiple_failures(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test health check when multiple systems are degraded.

        Given: DB missing, FAISS missing, watermark stale
        When: Health check is performed
        Then: Response should indicate degraded status
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Set up degraded state
        daemon._last_watermark_save_time = time.time() - 60.0  # 60 seconds ago (stale)

        # Mock paths to non-existent locations
        non_existent_db = Path("/tmp/does_not_exist_chat_history.db")
        non_existent_faiss = Path("/tmp/does_not_exist_faiss")

        with patch.object(daemon, "_get_chs_db_path", return_value=non_existent_db):
            with patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.FAISS_INDEX_PATH", non_existent_faiss):
                request = {"action": "health"}
                response = daemon._process_request(request)

                # Verify degraded status
                assert (
                    response.get("status") == "degraded"
                ), "Multiple failures should return status=degraded"

                # Verify failures are reported
                assert response.get("db_exists") is False, "DB missing should be reported"
                assert response.get("faiss_exists") is False, "FAISS missing should be reported"
                assert (
                    response.get("watermark_age_seconds") >= 30
                ), "Stale watermark should be reported"
