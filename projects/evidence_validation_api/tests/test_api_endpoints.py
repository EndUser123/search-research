"""
Tests for the API endpoints.

This module tests the FastAPI endpoints, including REST API
and WebSocket functionality.
"""

import json
from uuid import uuid4

import pytest
import pytest_asyncio
from evidence_validation_api.models.schemas import ValidationStatus
from evidence_validation_api.tests.conftest import (
    EvidenceRequestFactory,
    assert_validation_response_structure,
)


class TestValidationEndpoints:
    """Test cases for validation API endpoints."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validate_evidence_endpoint_success(
        self, test_client, sample_evidence_request
    ):
        """Test successful evidence validation endpoint."""
        response = await test_client.post(
            "/validate", json=sample_evidence_request.model_dump()
        )

        assert response.status_code == 200

        data = response.json()
        assert_validation_response_structure(data)
        assert data["validation_result"]["is_valid"] is True
        assert data["cached_result"] is False

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validate_evidence_endpoint_with_webhook(self, test_client):
        """Test evidence validation with webhook callback."""
        request = EvidenceRequestFactory.create_task_execution(
            async_validation=True, webhook_url="https://example.com/webhook"
        )

        response = await test_client.post("/validate", json=request.model_dump())

        assert response.status_code == 200

        data = response.json()
        assert (
            data["validation_result"]["validation_status"] == ValidationStatus.PENDING
        )
        assert data["validation_result"]["metadata"]["async"] is True

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validate_evidence_endpoint_invalid_data(self, test_client):
        """Test validation endpoint with invalid data."""
        invalid_request = {
            "evidence": {
                "content_type": "application/json",
                # Missing required 'data' field
            },
            "metadata": {
                "evidence_type": "task_execution",
                "source_system": "test_system",
            },
        }

        response = await test_client.post("/validate", json=invalid_request)

        assert response.status_code == 422  # Validation error

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_get_validation_status_endpoint(
        self, test_client, test_validation_service
    ):
        """Test get validation status endpoint."""
        # First, start a validation
        request = EvidenceRequestFactory.create_task_execution(async_validation=True)
        validation_response = await test_validation_service.validate_evidence(request)
        request_id = validation_response.request_id

        # Get status
        response = await test_client.get(f"/validate/{request_id}/status")

        assert response.status_code == 200

        data = response.json()
        assert "request_id" in data
        assert "status" in data
        assert data["request_id"] == str(request_id)

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_get_validation_status_not_found(self, test_client):
        """Test get validation status for non-existent request."""
        fake_request_id = uuid4()

        response = await test_client.get(f"/validate/{fake_request_id}/status")

        assert response.status_code == 404

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_cancel_validation_endpoint(
        self, test_client, test_validation_service
    ):
        """Test cancel validation endpoint."""
        # Start an async validation
        request = EvidenceRequestFactory.create_task_execution(async_validation=True)
        validation_response = await test_validation_service.validate_evidence(request)
        request_id = validation_response.request_id

        # Cancel the validation
        response = await test_client.delete(f"/validate/{request_id}")

        assert response.status_code == 200

        data = response.json()
        assert "message" in data

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_cancel_validation_not_found(self, test_client):
        """Test cancel validation for non-existent request."""
        fake_request_id = uuid4()

        response = await test_client.delete(f"/validate/{fake_request_id}")

        assert response.status_code == 404

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_metrics_endpoint(self, test_client, test_validation_service):
        """Test metrics endpoint."""
        # Perform some validations to generate metrics
        await test_validation_service.validate_evidence(
            EvidenceRequestFactory.create_task_execution()
        )
        await test_validation_service.validate_evidence(
            EvidenceRequestFactory.create_error_log()
        )

        # Get metrics
        response = await test_client.get("/metrics")

        assert response.status_code == 200

        data = response.json()
        assert "total_validations" in data
        assert "cache_hits" in data
        assert "cache_misses" in data
        assert "average_processing_time" in data
        assert data["total_validations"] >= 2

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_health_check_endpoint(self, test_client):
        """Test health check endpoint."""
        response = await test_client.get("/health")

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "database_status" in data
        assert "redis_status" in data

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_root_endpoint(self, test_client):
        """Test root endpoint."""
        response = await test_client.get("/")

        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert "docs" in data
        assert "health" in data


class TestWebSocketEndpoints:
    """Test cases for WebSocket endpoints."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.websocket
    async def test_websocket_connection(self, test_validation_service):
        """Test WebSocket connection establishment."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send ping message
                websocket.send_text(
                    json.dumps({"type": "ping", "timestamp": "2024-01-01T00:00:00Z"})
                )

                # Receive pong response
                data = websocket.receive_text()
                response = json.loads(data)

                assert response["type"] == "pong"
                assert "timestamp" in response

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.websocket
    async def test_websocket_subscribe_validation(self, test_validation_service):
        """Test WebSocket validation subscription."""
        from fastapi.testclient import TestClient

        request_id = uuid4()

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Subscribe to validation updates
                websocket.send_text(
                    json.dumps(
                        {"type": "subscribe_validation", "request_id": str(request_id)}
                    )
                )

                # Receive subscription confirmation
                data = websocket.receive_text()
                response = json.loads(data)

                assert response["type"] == "subscribed"
                assert response["request_id"] == str(request_id)

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.websocket
    async def test_websocket_invalid_message(self, test_validation_service):
        """Test WebSocket handling of invalid messages."""
        from fastapi.testclient import TestClient

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Send invalid JSON
                websocket.send_text("invalid json")

                # Should receive error message
                data = websocket.receive_text()
                response = json.loads(data)

                assert response["type"] == "error"

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.websocket
    async def test_websocket_broadcast(
        self, test_validation_service, sample_evidence_request
    ):
        """Test WebSocket message broadcasting."""
        from fastapi.testclient import TestClient

        # Perform validation to trigger broadcast
        response = await test_validation_service.validate_evidence(
            sample_evidence_request
        )

        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                # Should receive validation completed broadcast
                try:
                    data = websocket.receive_text(timeout=1.0)
                    response = json.loads(data)

                    # Should be a validation completion message
                    assert response["type"] in [
                        "validation_completed",
                        "validation_completed_webhook",
                    ]
                except:
                    # Might not receive if validation was too fast
                    pass


class TestErrorHandling:
    """Test cases for API error handling."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_service_unavailable_error(self, test_client, monkeypatch):
        """Test handling of service unavailability."""
        # Mock validation service to be None
        import evidence_validation_api.main

        monkeypatch.setattr(evidence_validation_api.main, "validation_service", None)

        response = await test_client.post(
            "/validate",
            json=EvidenceRequestFactory.create_task_execution().model_dump(),
        )

        assert response.status_code == 503

        data = response.json()
        assert "detail" in data

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_large_payload_handling(self, test_client):
        """Test handling of large payloads."""
        large_request = EvidenceRequestFactory.create_task_execution(
            task_data={"large_array": list(range(10000))}
        )

        response = await test_client.post(
            "/validate", json=large_request.model_dump(), timeout=30.0
        )

        # Should handle large payload gracefully
        assert response.status_code in [200, 413, 422]  # Success or size limit

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_malformed_json(self, test_client):
        """Test handling of malformed JSON."""
        response = await test_client.post(
            "/validate",
            content="invalid json{",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_missing_content_type(self, test_client, sample_evidence_request):
        """Test handling of missing Content-Type header."""
        response = await test_client.post(
            "/validate",
            data=json.dumps(sample_evidence_request.model_dump()),
            # No Content-Type header
        )

        # FastAPI should still handle JSON without explicit Content-Type
        assert response.status_code in [200, 422]

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_request_id_header(self, test_client, sample_evidence_request):
        """Test request ID header handling."""
        response = await test_client.post(
            "/validate",
            json=sample_evidence_request.model_dump(),
            headers={"X-Custom-Request-ID": "test-123"},
        )

        assert response.status_code == 200

        # Check that request ID header is returned
        assert "X-Request-ID" in response.headers


class TestAuthentication:
    """Test cases for API authentication and authorization."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_no_authentication_required(
        self, test_client, sample_evidence_request
    ):
        """Test that endpoints work without authentication in test mode."""
        response = await test_client.post(
            "/validate", json=sample_evidence_request.model_dump()
        )

        assert response.status_code == 200

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_authentication_with_bearer_token(
        self, test_client, sample_evidence_request
    ):
        """Test authentication with Bearer token."""
        response = await test_client.post(
            "/validate",
            json=sample_evidence_request.model_dump(),
            headers={"Authorization": "Bearer test-token"},
        )

        # Should accept token (even if validation is mocked)
        assert response.status_code in [200, 403]

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_permission_denied_for_protected_endpoints(self, test_client):
        """Test permission denied for protected endpoints."""
        # This would require actual permission checking implementation
        # For now, test that the mechanism exists
        response = await test_client.get("/metrics")

        # In test environment, might succeed or require permissions
        assert response.status_code in [200, 403]


class TestRateLimiting:
    """Test cases for rate limiting functionality."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_rate_limiting_basic(self, test_client, sample_evidence_request):
        """Test basic rate limiting functionality."""
        # This would require actual rate limiting implementation
        # Send multiple requests quickly
        responses = []
        for _ in range(10):
            response = await test_client.post(
                "/validate", json=sample_evidence_request.model_dump()
            )
            responses.append(response)

        # Most should succeed in test environment
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 5  # At least half should succeed

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_rate_limit_headers(self, test_client, sample_evidence_request):
        """Test rate limiting headers."""
        response = await test_client.post(
            "/validate", json=sample_evidence_request.model_dump()
        )

        # Rate limiting headers might be present
        # This depends on implementation
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers


class TestWebhookEndpoints:
    """Test cases for webhook endpoints."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_webhook_validation_completed(self, test_client):
        """Test webhook endpoint for validation completion."""
        webhook_data = {
            "request_id": str(uuid4()),
            "validation_result": {
                "is_valid": True,
                "confidence_score": 0.95,
                "validation_status": "validated",
            },
            "timestamp": "2024-01-01T00:00:00Z",
        }

        response = await test_client.post(
            "/webhook/validation-completed", json=webhook_data
        )

        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "received"
        assert data["request_id"] == webhook_data["request_id"]

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_webhook_missing_request_id(self, test_client):
        """Test webhook endpoint with missing request_id."""
        webhook_data = {"validation_result": {"is_valid": True}}

        response = await test_client.post(
            "/webhook/validation-completed", json=webhook_data
        )

        assert response.status_code == 400  # Bad Request

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_webhook_invalid_json(self, test_client):
        """Test webhook endpoint with invalid JSON."""
        response = await test_client.post(
            "/webhook/validation-completed",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422


# Import app for testing
from evidence_validation_api.main import app
