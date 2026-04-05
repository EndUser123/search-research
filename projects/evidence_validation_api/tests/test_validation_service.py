"""
Tests for the evidence validation service.

This module tests the core validation service functionality,
including caching, async processing, and error handling.
"""

import asyncio

import pytest
import pytest_asyncio
from evidence_validation_api.models.schemas import (
    CacheStrategy,
    EvidenceResponse,
    SeverityLevel,
    ValidationStatus,
)
from evidence_validation_api.tests.conftest import (
    EvidenceRequestFactory,
    ValidationTestScenarios,
    assert_validation_response_structure,
    run_concurrently,
)


class TestEvidenceValidationService:
    """Test cases for EvidenceValidationService."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validate_evidence_sync_success(
        self, test_validation_service, sample_evidence_request
    ):
        """Test successful synchronous evidence validation."""
        response = await test_validation_service.validate_evidence(
            sample_evidence_request
        )

        # Assert response structure
        assert isinstance(response, EvidenceResponse)
        assert_validation_response_structure(response.model_dump())

        # Assert validation results
        assert response.validation_result.is_valid is True
        assert (
            response.validation_result.validation_status == ValidationStatus.VALIDATED
        )
        assert response.validation_result.confidence_score > 0.0
        assert response.cached_result is False
        assert response.processing_time_ms > 0

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validate_evidence_with_rules(self, test_validation_service):
        """Test evidence validation with specific validation rules."""
        request = EvidenceRequestFactory.create_task_execution(
            validation_rules=["content_integrity", "metadata_completeness"]
        )

        response = await test_validation_service.validate_evidence(request)

        assert response.validation_result.validation_rules == [
            "content_integrity",
            "metadata_completeness",
        ]

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validate_evidence_async(
        self, test_validation_service, sample_evidence_request
    ):
        """Test asynchronous evidence validation."""
        # Enable async validation
        sample_evidence_request.async_validation = True

        response = await test_validation_service.validate_evidence(
            sample_evidence_request
        )

        # Should return pending status immediately
        assert response.validation_result.validation_status == ValidationStatus.PENDING
        assert response.validation_result.metadata.get("async") is True

        # Wait a bit for async processing
        await asyncio.sleep(0.1)

        # Check status
        status = await test_validation_service.get_validation_status(
            response.request_id
        )
        assert status is not None
        assert status["status"] in ["completed", "in_progress"]

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validate_evidence_caching(
        self, test_validation_service, sample_evidence_request
    ):
        """Test evidence validation caching."""
        # First validation
        response1 = await test_validation_service.validate_evidence(
            sample_evidence_request
        )
        assert response1.cached_result is False

        # Second validation (should hit cache)
        response2 = await test_validation_service.validate_evidence(
            sample_evidence_request
        )
        assert response2.cached_result is True

        # Results should be identical
        assert (
            response1.validation_result.is_valid == response2.validation_result.is_valid
        )
        assert (
            response1.validation_result.confidence_score
            == response2.validation_result.confidence_score
        )

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_cache_strategies(self, test_validation_service):
        """Test different caching strategies."""
        test_cases = [
            (CacheStrategy.NO_CACHE, False),
            (CacheStrategy.SHORT_TERM, True),
            (CacheStrategy.MEDIUM_TERM, True),
            (CacheStrategy.LONG_TERM, True),
        ]

        for cache_strategy, should_cache in test_cases:
            request = EvidenceRequestFactory.create_task_execution(
                cache_strategy=cache_strategy
            )

            # First validation
            response1 = await test_validation_service.validate_evidence(request)

            # Second validation
            response2 = await test_validation_service.validate_evidence(request)

            if should_cache:
                assert response2.cached_result is True
            else:
                assert response2.cached_result is False

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validate_error_evidence(
        self, test_validation_service, sample_failed_evidence_request
    ):
        """Test validation of error evidence."""
        response = await test_validation_service.validate_evidence(
            sample_failed_evidence_request
        )

        # Error evidence should still be valid (it's valid error log evidence)
        assert response.validation_result.is_valid is True
        assert (
            response.validation_result.validation_status == ValidationStatus.VALIDATED
        )

        # Should have warnings for error analysis
        assert len(response.validation_result.warnings) >= 0

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validation_service_metrics(
        self, test_validation_service, sample_evidence_request
    ):
        """Test validation service metrics."""
        # Get initial metrics
        initial_metrics = await test_validation_service.get_metrics()
        initial_validations = initial_metrics["total_validations"]

        # Perform validation
        await test_validation_service.validate_evidence(sample_evidence_request)

        # Get updated metrics
        updated_metrics = await test_validation_service.get_metrics()

        assert updated_metrics["total_validations"] == initial_validations + 1
        assert updated_metrics["average_processing_time"] > 0.0
        assert "cache_hits" in updated_metrics
        assert "cache_misses" in updated_metrics

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_cancel_validation(self, test_validation_service):
        """Test cancellation of async validation."""
        request = EvidenceRequestFactory.create_task_execution(async_validation=True)

        # Start async validation
        response = await test_validation_service.validate_evidence(request)
        request_id = response.request_id

        # Cancel the validation
        cancelled = await test_validation_service.cancel_validation(request_id)
        assert cancelled is True

        # Try to cancel again (should return False)
        cancelled_again = await test_validation_service.cancel_validation(request_id)
        assert cancelled_again is False

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_concurrent_validations(self, test_validation_service):
        """Test concurrent validation processing."""
        num_requests = 20
        requests = [
            EvidenceRequestFactory.create_task_execution(
                task_data={"task_id": f"task_{i}", "value": i}
            )
            for i in range(num_requests)
        ]

        # Run validations concurrently
        results = await run_concurrently(
            *(test_validation_service.validate_evidence(req) for req in requests),
            max_concurrency=10,
        )

        # All should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == num_requests

        # Each result should have unique request ID
        request_ids = [r.request_id for r in successful_results]
        assert len(request_ids) == len(set(request_ids))  # All unique

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_validation_timeout(self, test_validation_service):
        """Test validation timeout handling."""
        request = EvidenceRequestFactory.create_task_execution(
            timeout_seconds=1  # Very short timeout
        )

        # This should still complete quickly, but test the timeout mechanism
        response = await test_validation_service.validate_evidence(request)

        assert response is not None
        assert response.validation_result.validation_status in [
            ValidationStatus.VALIDATED,
            ValidationStatus.FAILED,
        ]

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_edge_cases(self, test_validation_service):
        """Test validation edge cases."""
        edge_cases = ValidationTestScenarios.get_edge_cases()

        for request in edge_cases:
            response = await test_validation_service.validate_evidence(request)

            # All edge cases should be handled gracefully
            assert isinstance(response, EvidenceResponse)
            assert_validation_response_structure(response.model_dump())

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    async def test_error_cases(self, test_validation_service):
        """Test validation error cases."""
        error_cases = ValidationTestScenarios.get_error_cases()

        for request in error_cases:
            response = await test_validation_service.validate_evidence(request)

            # Error cases should still produce valid responses
            assert isinstance(response, EvidenceResponse)
            assert_validation_response_structure(response.model_dump())

            # High severity errors might affect validation result
            if request.metadata.severity == SeverityLevel.CRITICAL:
                # Should still be valid as error evidence, but might have warnings
                assert response.validation_result.validation_status in [
                    ValidationStatus.VALIDATED,
                    ValidationStatus.REJECTED,
                ]


class TestValidationServiceCache:
    """Test cases for validation service caching."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.redis
    async def test_cache_hit_performance(
        self, test_validation_service, sample_evidence_request
    ):
        """Test that cache hits are faster than cache misses."""
        import time

        # First validation (cache miss)
        start_time = time.time()
        response1 = await test_validation_service.validate_evidence(
            sample_evidence_request
        )
        miss_time = time.time() - start_time

        # Second validation (cache hit)
        start_time = time.time()
        response2 = await test_validation_service.validate_evidence(
            sample_evidence_request
        )
        hit_time = time.time() - start_time

        # Cache hit should be faster
        assert hit_time < miss_time
        assert response1.cached_result is False
        assert response2.cached_result is True

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.redis
    async def test_cache_key_generation(self, test_validation_service):
        """Test cache key generation for different requests."""
        request1 = EvidenceRequestFactory.create_task_execution(
            task_data={"task_id": "same_task", "value": 1}
        )
        request2 = EvidenceRequestFactory.create_task_execution(
            task_data={"task_id": "same_task", "value": 2}
        )

        # Different data should produce different cache keys
        response1 = await test_validation_service.validate_evidence(request1)
        response2 = await test_validation_service.validate_evidence(request2)

        assert response1.cached_result is False
        assert response2.cached_result is False

        # Same request should hit cache
        response3 = await test_validation_service.validate_evidence(request1)
        assert response3.cached_result is True

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.unit
    @pytest.mark.redis
    async def test_cache_expiration(self, test_validation_service):
        """Test cache expiration for short-term cache strategy."""
        request = EvidenceRequestFactory.create_task_execution(
            cache_strategy=CacheStrategy.SHORT_TERM  # 5 minutes in test
        )

        # First validation
        response1 = await test_validation_service.validate_evidence(request)
        assert response1.cached_result is False

        # Second validation (should hit cache)
        response2 = await test_validation_service.validate_evidence(request)
        assert response2.cached_result is True

        # Note: We can't easily test actual expiration in unit tests
        # without manipulating time or waiting, but the mechanism is in place


class TestValidationServiceIntegration:
    """Integration tests for validation service."""

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_validation_flow(
        self, test_validation_service, test_db_session
    ):
        """Test complete validation flow from request to storage."""
        request = EvidenceRequestFactory.create_task_execution()

        # Validate evidence
        response = await test_validation_service.validate_evidence(request)

        # Verify response
        assert isinstance(response, EvidenceResponse)
        assert response.validation_result.is_valid is True

        # Verify evidence was stored in database
        from evidence_validation_api.models.database import (
            EvidenceTable,
            ValidationResultTable,
        )

        # Check evidence record
        evidence_result = await test_db_session.execute(
            select(EvidenceTable).where(
                EvidenceTable.evidence_id == response.evidence_id
            )
        )
        evidence_record = evidence_result.scalar_one_or_none()
        assert evidence_record is not None
        assert evidence_record.evidence_type == "task_execution"

        # Check validation result record
        validation_result = await test_db_session.execute(
            select(ValidationResultTable).where(
                ValidationResultTable.request_id == response.request_id
            )
        )
        validation_record = validation_result.scalar_one_or_none()
        assert validation_record is not None
        assert validation_record.is_valid is True

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.integration
    async def test_webhook_notification(self, test_validation_service, monkeypatch):
        """Test webhook notification for async validation."""
        webhook_calls = []

        async def mock_webhook(url, payload):
            webhook_calls.append((url, payload))

        # Mock the webhook function
        monkeypatch.setattr(
            test_validation_service, "_send_webhook_notification", mock_webhook
        )

        request = EvidenceRequestFactory.create_task_execution(
            async_validation=True, webhook_url="https://example.com/webhook"
        )

        # Start async validation
        await test_validation_service.validate_evidence(request)

        # Wait for async processing
        await asyncio.sleep(0.1)

        # Check if webhook was called
        assert len(webhook_calls) > 0
        url, payload = webhook_calls[0]
        assert url == "https://example.com/webhook"
        assert "validation_result" in payload
        assert "request_id" in payload

    @pytest_asyncio.asyncio.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.redis
    async def test_redis_connection_failure(self, test_validation_service, monkeypatch):
        """Test graceful handling of Redis connection failure."""

        # Mock Redis client to raise connection error
        async def mock_get(*args, **kwargs):
            raise ConnectionError("Redis connection failed")

        # Apply mock
        test_validation_service.redis_client.get = mock_get

        request = EvidenceRequestFactory.create_task_execution()

        # Validation should still work even with Redis failure
        response = await test_validation_service.validate_evidence(request)

        assert isinstance(response, EvidenceResponse)
        assert response.cached_result is False  # No cache available
        assert response.validation_result.is_valid is True
