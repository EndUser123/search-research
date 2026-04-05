"""
Test configuration and fixtures for the evidence validation API.

This module provides pytest fixtures and configuration for testing
the evidence validation system with async support.
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from evidence_validation_api.config.settings import Settings
from evidence_validation_api.main import app
from evidence_validation_api.models.database import (
    DatabaseManager,
    get_database_manager,
)
from evidence_validation_api.models.schemas import (
    CacheStrategy,
    EvidenceContent,
    EvidenceMetadata,
    EvidenceRequest,
    EvidenceType,
    SeverityLevel,
    ValidationStatus,
)
from evidence_validation_api.services.validation_service import (
    EvidenceValidationService,
)
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Test settings
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_evidence_validation.db"
TEST_REDIS_URL = "redis://localhost:6379/15"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_settings():
    """Test configuration settings."""
    return Settings(
        database__database_url=TEST_DATABASE_URL,
        redis__redis_url=TEST_REDIS_URL,
        validation__max_concurrent_validations=10,
        validation__default_timeout=5,
        api__debug=True,
        monitoring__log_level="DEBUG",
    )


@pytest_asyncio.fixture(scope="session")
async def test_database_manager(test_settings):
    """Test database manager."""
    # Create test database
    db_manager = DatabaseManager(TEST_DATABASE_URL)
    await db_manager.create_tables()

    yield db_manager

    # Clean up test database
    await db_manager.drop_tables()
    await db_manager.close()


@pytest_asyncio.fixture
async def test_db_session(test_database_manager) -> AsyncGenerator[AsyncSession, None]:
    """Test database session."""
    async with test_database_manager.get_session() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def test_redis_client():
    """Test Redis client."""
    try:
        import redis.asyncio as redis

        client = redis.from_url(TEST_REDIS_URL, decode_responses=True)

        # Test connection
        await client.ping()

        # Clear test database
        await client.flushdb()

        yield client

        # Clean up
        await client.flushdb()
        await client.close()

    except Exception as e:
        pytest.skip(f"Redis not available for testing: {e}")


@pytest_asyncio.fixture
async def test_validation_service(test_database_manager, test_redis_client):
    """Test evidence validation service."""
    service = EvidenceValidationService(
        db_manager=test_database_manager,
        redis_url=TEST_REDIS_URL,
        default_timeout=5,
        max_concurrent_validations=10,
    )

    await service.initialize()

    yield service

    await service.shutdown()


@pytest_asyncio.fixture
async def test_client(test_validation_service) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client for FastAPI application."""

    # Override dependencies
    app.dependency_overrides[get_database_manager] = (
        lambda: test_validation_service.db_manager
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Clean up dependencies
    app.dependency_overrides.clear()


@pytest.fixture
def sync_test_client():
    """Synchronous test client for FastAPI."""
    return TestClient(app)


@pytest_asyncio.fixture
async def sample_evidence_request():
    """Sample evidence request for testing."""
    return EvidenceRequest(
        evidence=EvidenceContent(
            content_type="application/json",
            data={
                "task_result": "success",
                "execution_time": 120.5,
                "output": {"status": "completed", "items_processed": 1000},
            },
        ),
        metadata=EvidenceMetadata(
            evidence_type=EvidenceType.TASK_EXECUTION,
            source_system="test_system",
            source_component="test_component",
            timestamp=datetime.now(UTC),
            workflow_id="test_workflow",
            task_id="test_task",
            user_id="test_user",
            severity=SeverityLevel.MEDIUM,
        ),
        validation_rules=["content_integrity", "metadata_completeness"],
        cache_strategy=CacheStrategy.MEDIUM_TERM,
        async_validation=False,
    )


@pytest_asyncio.fixture
async def sample_failed_evidence_request():
    """Sample failing evidence request for testing."""
    return EvidenceRequest(
        evidence=EvidenceContent(
            content_type="application/json",
            data={
                "error": "Task failed",
                "execution_time": 300.0,
                "error_details": "Connection timeout",
            },
        ),
        metadata=EvidenceMetadata(
            evidence_type=EvidenceType.ERROR_LOG,
            source_system="test_system",
            source_component="test_component",
            timestamp=datetime.now(UTC),
            workflow_id="test_workflow",
            task_id="test_task",
            user_id="test_user",
            severity=SeverityLevel.HIGH,
        ),
        validation_rules=["error_analysis", "content_integrity"],
        cache_strategy=CacheStrategy.SHORT_TERM,
        async_validation=False,
    )


@pytest_asyncio.fixture
async def sample_large_evidence_request():
    """Sample large evidence request for testing size limits."""
    large_data = {
        "large_array": list(range(10000)),
        "nested_data": {"level1": {"level2": {"level3": "deeply nested value"}}},
        "metadata": {
            "description": "Large evidence payload for testing",
            "tags": ["test", "large", "payload"],
        },
    }

    return EvidenceRequest(
        evidence=EvidenceContent(
            content_type="application/json",
            data=large_data,
            size_bytes=len(str(large_data).encode()),
        ),
        metadata=EvidenceMetadata(
            evidence_type=EvidenceType.PERFORMANCE_METRIC,
            source_system="test_system",
            timestamp=datetime.now(UTC),
            severity=SeverityLevel.LOW,
        ),
        validation_rules=["content_integrity"],
        cache_strategy=CacheStrategy.SHORT_TERM,
        async_validation=False,
    )


# Factory fixtures using factory_boy pattern
class EvidenceRequestFactory:
    """Factory for creating EvidenceRequest objects for testing."""

    @staticmethod
    def create_task_execution(
        evidence_type: EvidenceType = EvidenceType.TASK_EXECUTION,
        source_system: str = "test_system",
        task_data: dict = None,
        validation_rules: list = None,
        async_validation: bool = False,
        cache_strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM,
    ) -> EvidenceRequest:
        """Create a task execution evidence request."""
        if task_data is None:
            task_data = {
                "task_id": "task_123",
                "status": "completed",
                "execution_time": 45.2,
                "result": {"output": "success"},
            }

        if validation_rules is None:
            validation_rules = ["content_integrity", "metadata_completeness"]

        return EvidenceRequest(
            evidence=EvidenceContent(content_type="application/json", data=task_data),
            metadata=EvidenceMetadata(
                evidence_type=evidence_type,
                source_system=source_system,
                source_component="task_executor",
                timestamp=datetime.now(UTC),
                workflow_id="workflow_123",
                task_id="task_123",
                severity=SeverityLevel.MEDIUM,
            ),
            validation_rules=validation_rules,
            cache_strategy=cache_strategy,
            async_validation=async_validation,
        )

    @staticmethod
    def create_error_log(
        source_system: str = "test_system",
        error_data: dict = None,
        severity: SeverityLevel = SeverityLevel.HIGH,
    ) -> EvidenceRequest:
        """Create an error log evidence request."""
        if error_data is None:
            error_data = {
                "error_code": "VALIDATION_FAILED",
                "error_message": "Evidence validation failed",
                "stack_trace": "Traceback (most recent call last): ...",
                "context": {"component": "validator"},
            }

        return EvidenceRequest(
            evidence=EvidenceContent(content_type="application/json", data=error_data),
            metadata=EvidenceMetadata(
                evidence_type=EvidenceType.ERROR_LOG,
                source_system=source_system,
                source_component="error_handler",
                timestamp=datetime.now(UTC),
                severity=severity,
                tags=["error", "validation"],
            ),
            validation_rules=["error_analysis"],
            cache_strategy=CacheStrategy.SHORT_TERM,
            async_validation=False,
        )

    @staticmethod
    def create_performance_metric(
        metric_name: str = "response_time",
        metric_value: float = 150.5,
        source_system: str = "test_system",
    ) -> EvidenceRequest:
        """Create a performance metric evidence request."""
        metric_data = {
            "metric_name": metric_name,
            "metric_value": metric_value,
            "metric_unit": "milliseconds",
            "context": {"endpoint": "/api/validate", "method": "POST"},
        }

        return EvidenceRequest(
            evidence=EvidenceContent(content_type="application/json", data=metric_data),
            metadata=EvidenceMetadata(
                evidence_type=EvidenceType.PERFORMANCE_METRIC,
                source_system=source_system,
                source_component="metrics_collector",
                timestamp=datetime.now(UTC),
                tags=["performance", "metrics"],
            ),
            validation_rules=["metric_validity"],
            cache_strategy=CacheStrategy.SHORT_TERM,
            async_validation=False,
        )


class ValidationTestScenarios:
    """Collection of common test scenarios for validation testing."""

    @staticmethod
    def get_basic_validation_cases() -> list[EvidenceRequest]:
        """Get basic validation test cases."""
        return [
            EvidenceRequestFactory.create_task_execution(),
            EvidenceRequestFactory.create_error_log(),
            EvidenceRequestFactory.create_performance_metric(),
        ]

    @staticmethod
    def get_edge_cases() -> list[EvidenceRequest]:
        """Get edge case validation test cases."""
        return [
            # Empty data
            EvidenceRequestFactory.create_task_execution(task_data={}),
            # Very long task ID
            EvidenceRequestFactory.create_task_execution(
                task_data={"task_id": "x" * 1000}
            ),
            # Extreme values
            EvidenceRequestFactory.create_performance_metric(metric_value=999999.99),
            # No validation rules
            EvidenceRequestFactory.create_task_execution(validation_rules=[]),
        ]

    @staticmethod
    def get_error_cases() -> list[EvidenceRequest]:
        """Get error case validation test cases."""
        return [
            # High severity error
            EvidenceRequestFactory.create_error_log(severity=SeverityLevel.CRITICAL),
            # Complex error with stack trace
            EvidenceRequestFactory.create_error_log(
                error_data={
                    "error_code": "SYSTEM_ERROR",
                    "error_message": "Database connection failed",
                    "stack_trace": "A" * 5000,  # Long stack trace
                    "context": {"retry_count": 3, "timeout": 30},
                }
            ),
            # Validation error
            EvidenceRequestFactory.create_error_log(
                error_data={
                    "validation_errors": ["Missing required field", "Invalid format"]
                }
            ),
        ]


# Pytest marks for test categorization
pytest_plugins = []


# Custom markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests (fast)")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (skip with -m 'not slow')"
    )
    config.addinivalue_line("markers", "redis: marks tests that require Redis")
    config.addinivalue_line("markers", "postgres: marks tests that require PostgreSQL")
    config.addinivalue_line(
        "markers", "websocket: marks tests that use WebSocket functionality"
    )


# Test utilities
async def create_validation_result(
    is_valid: bool = True,
    confidence_score: float = 0.95,
    validation_status: ValidationStatus = ValidationStatus.VALIDATED,
    violations: list = None,
    warnings: list = None,
    recommendations: list = None,
) -> dict:
    """Create a validation result dictionary for testing."""
    return {
        "is_valid": is_valid,
        "confidence_score": confidence_score,
        "validation_status": validation_status,
        "validated_at": datetime.now(UTC).isoformat(),
        "validator_id": "test_validator",
        "validation_rules": ["test_rule"],
        "violations": violations or [],
        "warnings": warnings or [],
        "recommendations": recommendations or [],
        "metadata": {"test": True},
    }


async def assert_validation_response_structure(response: dict):
    """Assert that validation response has correct structure."""
    required_fields = [
        "request_id",
        "evidence_id",
        "validation_result",
        "processing_time_ms",
        "cached_result",
        "api_version",
        "timestamp",
    ]

    for field in required_fields:
        assert field in response, f"Missing required field: {field}"

    # Assert validation result structure
    validation_result = response["validation_result"]
    required_validation_fields = [
        "is_valid",
        "confidence_score",
        "validation_status",
        "validated_at",
        "validation_rules",
        "violations",
        "warnings",
        "recommendations",
        "metadata",
    ]

    for field in required_validation_fields:
        assert field in validation_result, f"Missing validation result field: {field}"


# Test database helpers
async def insert_test_evidence(
    session: AsyncSession, evidence_type: str, source_system: str, data: dict
) -> str:
    """Insert test evidence into database."""
    from evidence_validation_api.models.database import EvidenceTable

    evidence = EvidenceTable(
        evidence_id=uuid4(),
        evidence_type=evidence_type,
        source_system=source_system,
        timestamp=datetime.now(UTC),
        content_type="application/json",
        content_hash="test_hash",
        data=data,
    )

    session.add(evidence)
    await session.commit()
    await session.refresh(evidence)

    return str(evidence.evidence_id)


# Async test helper functions
async def run_concurrently(*coroutines, max_concurrency: int = 10):
    """Run coroutines with limited concurrency."""
    semaphore = asyncio.Semaphore(max_concurrency)

    async def limited_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(
        *(limited_coro(coro) for coro in coroutines), return_exceptions=True
    )
