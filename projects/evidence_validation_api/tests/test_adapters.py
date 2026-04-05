"""
Tests for the evidence validation adapters.

This module tests the adapter classes that provide interfaces
for different system components.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from evidence_validation_api.adapters.base import (
    ComponentAdapter,
    HTTPAdapter,
    WebSocketAdapter,
)
from evidence_validation_api.adapters.cicd import CIPlatformAdapter
from evidence_validation_api.adapters.data import DatabaseAdapter
from evidence_validation_api.adapters.workflow import (
    TaskQueueAdapter,
    WorkflowEngineAdapter,
)
from evidence_validation_api.models.schemas import (
    CacheStrategy,
    EvidenceRequest,
    EvidenceResponse,
    EvidenceType,
)
from evidence_validation_api.tests.conftest import EvidenceRequestFactory


class TestComponentAdapter:
    """Test cases for the base ComponentAdapter class."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_component_adapter_initialization(self):
        """Test ComponentAdapter initialization."""
        adapter = ComponentAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
            api_key="test_key",
        )

        assert adapter.component_name == "test_component"
        assert adapter.component_version == "1.0.0"
        assert adapter.base_url == "http://localhost:8000"
        assert adapter.api_key == "test_key"
        assert isinstance(adapter.client_id, type(uuid4()))

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_create_evidence_request(self):
        """Test evidence request creation."""
        adapter = ComponentAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
        )

        evidence_data = {"task_result": "success"}
        evidence_type = EvidenceType.TASK_EXECUTION
        metadata = {"workflow_id": "workflow_123", "task_id": "task_456", "priority": 8}

        request = adapter.create_evidence_request(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=["content_integrity"],
            async_validation=False,
            cache_strategy=CacheStrategy.MEDIUM_TERM,
        )

        assert isinstance(request, EvidenceRequest)
        assert request.evidence.data == evidence_data
        assert request.metadata.evidence_type == evidence_type
        assert request.metadata.source_system == "test_component"
        assert request.metadata.source_component == "test_component_v1.0.0"
        assert request.metadata.workflow_id == "workflow_123"
        assert request.metadata.task_id == "task_456"
        assert request.validation_rules == ["content_integrity"]
        assert request.async_validation is False
        assert request.cache_strategy == CacheStrategy.MEDIUM_TERM


class TestHTTPAdapter:
    """Test cases for HTTPAdapter class."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_http_adapter_initialization(self):
        """Test HTTPAdapter initialization."""
        adapter = HTTPAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
            api_key="test_key",
            timeout=30,
            max_retries=3,
        )

        assert adapter.timeout == 30
        assert adapter.max_retries == 3
        assert adapter._http_client is None

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_http_validate_evidence_success(self):
        """Test successful HTTP evidence validation."""
        adapter = HTTPAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
        )

        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": str(uuid4()),
            "evidence_id": str(uuid4()),
            "validation_result": {
                "is_valid": True,
                "confidence_score": 0.95,
                "validation_status": "validated",
            },
            "processing_time_ms": 150.0,
            "cached_result": False,
            "api_version": "1.0",
            "timestamp": "2024-01-01T00:00:00Z",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Test validation
            request = EvidenceRequestFactory.create_task_execution()
            response = await adapter.validate_evidence(
                evidence_data=request.evidence.data,
                evidence_type=request.metadata.evidence_type,
                metadata=request.metadata.model_dump(),
                validation_rules=request.validation_rules,
            )

            assert isinstance(response, EvidenceResponse)
            assert response.validation_result.is_valid is True
            mock_client.post.assert_called_once()

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_http_validate_evidence_error(self):
        """Test HTTP validation with error response."""
        adapter = HTTPAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
        )

        # Mock HTTP client with error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status.side_effect = Exception("HTTP 500")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Test validation
            request = EvidenceRequestFactory.create_task_execution()

            with pytest.raises(Exception) as exc_info:
                await adapter.validate_evidence(
                    evidence_data=request.evidence.data,
                    evidence_type=request.metadata.evidence_type,
                )

            assert "HTTP error 500" in str(exc_info.value)

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_http_get_validation_status(self):
        """Test getting validation status via HTTP."""
        adapter = HTTPAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
        )

        request_id = uuid4()
        status_data = {
            "request_id": str(request_id),
            "status": "completed",
            "validation_result": {"is_valid": True, "validation_status": "validated"},
        }

        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = status_data

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Test status check
            status = await adapter.get_validation_status(request_id)

            assert status == status_data
            mock_client.get.assert_called_once_with(
                f"http://localhost:8000/validate/{request_id}/status"
            )

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_http_cancel_validation(self):
        """Test cancelling validation via HTTP."""
        adapter = HTTPAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
        )

        request_id = uuid4()

        # Mock HTTP client
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.delete.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Test cancellation
            cancelled = await adapter.cancel_validation(request_id)

            assert cancelled is True
            mock_client.delete.assert_called_once_with(
                f"http://localhost:8000/validate/{request_id}"
            )


class TestWebSocketAdapter:
    """Test cases for WebSocketAdapter class."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_websocket_adapter_initialization(self):
        """Test WebSocketAdapter initialization."""
        adapter = WebSocketAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
        )

        assert adapter.ws_url == "ws://localhost:8000/ws"
        assert adapter._websocket is None
        assert adapter._connected is False
        assert isinstance(adapter.http_adapter, HTTPAdapter)

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_websocket_adapter_https_url(self):
        """Test WebSocket URL generation for HTTPS."""
        adapter = WebSocketAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="https://api.example.com",
        )

        assert adapter.ws_url == "wss://api.example.com/ws"

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_websocket_message_handler(self):
        """Test WebSocket message handler functionality."""
        adapter = WebSocketAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
        )

        # Test adding message handler
        handler_called = False
        test_data = {"type": "test", "message": "hello"}

        def test_handler(data):
            nonlocal handler_called
            handler_called = True
            assert data == test_data

        adapter.add_message_handler("test", test_handler)
        assert "test" in adapter._message_handlers

        # Test message handling
        await adapter._handle_message(json.dumps(test_data))
        assert handler_called is True

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_websocket_subscribe_validation(self):
        """Test WebSocket validation subscription."""
        adapter = WebSocketAdapter(
            component_name="test_component",
            component_version="1.0.0")
            base_url="http://localhost:8000",
        )

        # Mock WebSocket connection
        adapter._websocket = AsyncMock()
        adapter._connected = True

        callback_called = False
        request_id = uuid4()

        def test_callback(data):
            nonlocal callback_called
            callback_called = True

        # Test subscription
        await adapter.subscribe_to_validation(request_id, test_callback)
        assert "validation_completed" in adapter._message_handlers

        # Verify message was sent
        adapter._websocket.send_text.assert_called_once()
        sent_data = json.loads(adapter._websocket.send_text.call_args[0][0])
        assert sent_data["type"] == "subscribe_validation"
        assert sent_data["request_id"] == str(request_id)


class TestWorkflowEngineAdapter:
    """Test cases for WorkflowEngineAdapter."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_workflow_engine_validate_task_execution(self):
        """Test task execution validation."""
        adapter = WorkflowEngineAdapter(
            workflow_engine="airflow",
            base_url="http://localhost:8000",
            api_key="test_key",
        )

        # Mock HTTP adapter
        adapter.http_adapter = AsyncMock()
        mock_response = MagicMock()
        mock_response.validation_result.is_valid = True
        adapter.http_adapter.validate_evidence.return_value = mock_response

        # Test task execution validation
        response = await adapter.validate_task_execution(
            task_id="task_123",
            dag_id="dag_456",
            execution_date=None,
            task_result={"status": "success"},
            task_logs="Task completed successfully",
            execution_time=120.5,
        )

        assert response == mock_response
        adapter.http_adapter.validate_evidence.assert_called_once()

        # Check the request arguments
        call_args = adapter.http_adapter.validate_evidence.call_args
        assert call_args[1]["evidence_type"] == EvidenceType.TASK_EXECUTION
        assert "task_123" in str(call_args)
        assert "dag_456" in str(call_args)

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_workflow_engine_validate_workflow_metrics(self):
        """Test workflow metrics validation."""
        adapter = WorkflowEngineAdapter(
            workflow_engine="airflow", base_url="http://localhost:8000"
        )

        # Mock HTTP adapter
        adapter.http_adapter = AsyncMock()
        mock_response = MagicMock()
        adapter.http_adapter.validate_evidence.return_value = mock_response

        # Test metrics validation
        metrics = {
            "dag_run_duration": 300.0,
            "task_success_rate": 0.95,
            "total_tasks": 20,
        }

        response = await adapter.validate_workflow_metrics(
            workflow_id="workflow_123", metrics=metrics
        )

        assert response == mock_response
        call_args = adapter.http_adapter.validate_evidence.call_args
        assert call_args[1]["evidence_type"] == EvidenceType.PERFORMANCE_METRIC


class TestTaskQueueAdapter:
    """Test cases for TaskQueueAdapter."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_task_queue_validate_task_result_success(self):
        """Test successful task result validation."""
        adapter = TaskQueueAdapter(
            task_queue_system="celery", base_url="http://localhost:8000"
        )

        # Mock HTTP adapter
        adapter.http_adapter = AsyncMock()
        mock_response = MagicMock()
        adapter.http_adapter.validate_evidence.return_value = mock_response

        # Test successful task result validation
        response = await adapter.validate_task_result(
            task_id="celery_task_123",
            task_name="process_data",
            worker_id="worker_1",
            args=["input_data"],
            kwargs={"option": "value"},
            result={"output": "processed_data"},
            success=True,
            runtime=45.2,
        )

        assert response == mock_response
        call_args = adapter.http_adapter.validate_evidence.call_args
        assert call_args[1]["evidence_type"] == EvidenceType.TASK_EXECUTION

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_task_queue_validate_task_result_failure(self):
        """Test failed task result validation."""
        adapter = TaskQueueAdapter(
            task_queue_system="celery",
            base_url="http://localhost:8000",
            validate_failures=True,
        )

        # Mock HTTP adapter
        adapter.http_adapter = AsyncMock()
        mock_response = MagicMock()
        adapter.http_adapter.validate_evidence.return_value = mock_response

        # Test failed task result validation
        response = await adapter.validate_task_result(
            task_id="celery_task_456",
            task_name="failing_task",
            success=False,
            exception="ValueError: Invalid input",
            traceback="Traceback...",
        )

        assert response == mock_response
        call_args = adapter.http_adapter.validate_evidence.call_args
        assert call_args[1]["evidence_type"] == EvidenceType.ERROR_LOG


class TestDatabaseAdapter:
    """Test cases for DatabaseAdapter."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_database_validate_query_execution(self):
        """Test query execution validation."""
        adapter = DatabaseAdapter(
            database_type="postgresql", base_url="http://localhost:8000"
        )

        # Mock HTTP adapter
        adapter.http_adapter = AsyncMock()
        mock_response = MagicMock()
        adapter.http_adapter.validate_evidence.return_value = mock_response

        # Test query execution validation
        response = await adapter.validate_query_execution(
            query="SELECT * FROM users WHERE active = true",
            database_name="app_db",
            execution_time=25.5,
            rows_affected=100,
            user="app_user",
        )

        assert response == mock_response
        call_args = adapter.http_adapter.validate_evidence.call_args
        assert call_args[1]["evidence_type"] == EvidenceType.DATABASE_OPERATION
        assert "SELECT * FROM users" in str(call_args)

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_database_validate_migration(self):
        """Test database migration validation."""
        adapter = DatabaseAdapter(
            database_type="postgresql",
            base_url="http://localhost:8000",
            validate_migrations=True,
        )

        # Mock HTTP adapter
        adapter.http_adapter = AsyncMock()
        mock_response = MagicMock()
        adapter.http_adapter.validate_evidence.return_value = mock_response

        # Test migration validation
        response = await adapter.validate_database_migration(
            migration_id="001_add_user_table",
            migration_version="1.0.0")
            database_name="app_db",
            direction="up",
            tables_affected=["users"],
            execution_time=120.0,
            checksum="abc123",
            success=True,
        )

        assert response == mock_response
        call_args = adapter.http_adapter.validate_evidence.call_args
        assert "001_add_user_table" in str(call_args)
        assert call_args[1]["evidence_type"] == EvidenceType.DATABASE_OPERATION


class TestCIPlatformAdapter:
    """Test cases for CIPlatformAdapter."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_ci_validate_build_execution(self):
        """Test CI build execution validation."""
        adapter = CIPlatformAdapter(
            ci_platform="github_actions", base_url="http://localhost:8000"
        )

        # Mock WebSocket adapter
        adapter.ws_adapter = AsyncMock()
        mock_response = MagicMock()
        mock_response.request_id = uuid4()
        adapter.ws_adapter.validate_evidence.return_value = mock_response
        adapter.ws_adapter.subscribe_to_validation = AsyncMock()

        # Test build execution validation
        response = await adapter.validate_build_execution(
            build_id="build_123",
            project_name="my_project",
            branch="main",
            commit_hash="abc123def",
            status="success",
            start_time=None,  # Will use current time
            build_number="456",
        )

        assert response == mock_response
        adapter.ws_adapter.validate_evidence.assert_called_once()
        adapter.ws_adapter.subscribe_to_validation.assert_called_once()

        # Check call arguments
        call_args = adapter.ws_adapter.validate_evidence.call_args
        assert call_args[1]["evidence_type"] == EvidenceType.TASK_EXECUTION
        assert "github_actions" in str(call_args)

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_ci_validate_test_execution(self):
        """Test CI test execution validation."""
        adapter = CIPlatformAdapter(
            ci_platform="gitlab_ci",
            base_url="http://localhost:8000",
            validate_tests=True,
        )

        # Mock WebSocket adapter
        adapter.ws_adapter = AsyncMock()
        mock_response = MagicMock()
        adapter.ws_adapter.validate_evidence.return_value = mock_response

        # Test test execution validation
        test_results = [
            {"test_name": "test_api", "status": "passed", "time": 1.2},
            {"test_name": "test_model", "status": "failed", "time": 2.1},
        ]

        response = await adapter.validate_test_execution(
            test_suite_id="suite_123",
            build_id="build_456",
            project_name="my_project",
            test_framework="pytest",
            total_tests=100,
            passed_tests=95,
            failed_tests=5,
            skipped_tests=0,
            test_results=test_results,
            coverage_report={"total": 85.5, "lines": 87.2},
        )

        assert response == mock_response
        call_args = adapter.ws_adapter.validate_evidence.call_args
        assert call_args[1]["evidence_type"] == EvidenceType.TEST_RESULT


class TestAdapterIntegration:
    """Integration tests for adapters."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.integration
    async def test_adapter_factory_pattern(self):
        """Test that different adapters follow the same interface."""
        # Create different adapter types
        adapters = [
            WorkflowEngineAdapter("airflow", "http://localhost:8000"),
            TaskQueueAdapter("celery", "http://localhost:8000"),
            DatabaseAdapter("postgresql", "http://localhost:8000"),
            CIPlatformAdapter("github_actions", "http://localhost:8000"),
        ]

        # All should have the same interface methods
        for adapter in adapters:
            assert hasattr(adapter, "validate_evidence")
            assert hasattr(adapter, "get_validation_status")
            assert hasattr(adapter, "cancel_validation")
            assert hasattr(adapter, "close")

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.integration
    async def test_adapter_evidence_request_creation(self):
        """Test that adapters create consistent evidence requests."""
        adapters = [
            WorkflowEngineAdapter("airflow", "http://localhost:8000"),
            TaskQueueAdapter("celery", "http://localhost:8000"),
        ]

        base_evidence_data = {"task_id": "test_task", "status": "completed"}
        evidence_type = EvidenceType.TASK_EXECUTION

        for adapter in adapters:
            request = adapter.create_evidence_request(
                evidence_data=base_evidence_data, evidence_type=evidence_type
            )

            assert isinstance(request, EvidenceRequest)
            assert request.evidence.data == base_evidence_data
            assert request.metadata.evidence_type == evidence_type
            assert request.metadata.source_system == adapter.component_name
            assert adapter.component_version in request.metadata.source_component
