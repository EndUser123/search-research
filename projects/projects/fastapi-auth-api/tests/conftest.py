"""
Pytest configuration and fixtures for FastAPI authentication API testing.

Test Case ID: TC-CONFIG-001
Priority: High
Test Type: Configuration Testing

Purpose:
Provide centralized fixtures and configuration for all authentication API tests.

Preconditions:
- Test environment is set up with pytest
- Required dependencies are installed
- Database connections are available for integration tests

Expected Results:
- All tests can access common fixtures
- Database is properly initialized and cleaned up
- Test client is available for API testing
"""

import asyncio
import os
import tempfile
from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from src.app.core.database import get_db
from src.app.core.security import get_password_hash
from src.app.main import app
from src.app.models.user import User


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an instance of the default event loop for the test session.

    Algorithm Approach: Session-scoped event loop for async test support
    Time Complexity: O(1) - Single initialization
    Space Complexity: O(1) - Constant space usage

    Yields:
    asyncio.AbstractEventLoop: Event loop instance for async operations
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client() -> TestClient:
    """
    Create a test client for FastAPI application.

    Algorithm Approach: Standard FastAPI test client with sync interface
    Time Complexity: O(1) - Client creation
    Space Complexity: O(1) - Constant memory overhead

    Returns:
    TestClient: Configured test client for API testing
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for FastAPI application.

    Algorithm Approach: Async client with proper cleanup
    Time Complexity: O(1) - Client creation and cleanup
    Space Complexity: O(1) - Constant memory overhead

    Yields:
    AsyncClient: Async test client for API testing
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    """
    Create a temporary database for testing.

    Algorithm Approach: Temporary file database with auto-cleanup
    Time Complexity: O(1) - File creation and deletion
    Space Complexity: O(1) - Temporary file space

    Yields:
    str: Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def test_user_data() -> dict:
    """
    Provide test user data for authentication testing.

    Algorithm Approach: Standardized test data structure
    Time Complexity: O(1) - Data creation
    Space Complexity: O(1) - Constant data size

    Returns:
    dict: Test user data with email, password, and additional fields
    """
    return {
        "email": "test@example.com",
        "password": "SecureTestPassword123!",
        "full_name": "Test User",
    }


@pytest.fixture
def test_user_hashed() -> dict:
    """
    Provide test user data with hashed password for database seeding.

    Algorithm Approach: Pre-hashed password for database testing
    Time Complexity: O(1) - Hash computation
    Space Complexity: O(1) - Constant data size

    Returns:
    dict: Test user data with hashed password
    """
    return {
        "email": "test@example.com",
        "password_hash": get_password_hash("SecureTestPassword123!"),
        "full_name": "Test User",
        "is_active": True,
        "is_verified": True,
    }


@pytest.fixture
async def test_user_in_db(temp_db: str, test_user_hashed: dict) -> User:
    """
    Create a test user in the database for testing.

    Algorithm Approach: Database user creation with proper cleanup
    Time Complexity: O(1) - Single database operation
    Space Complexity: O(1) - Single user record

    Args:
    temp_db: Path to temporary database
    test_user_hashed: User data with hashed password

    Returns:
    User: Created user instance
    """
    # Override database dependency for testing
    app.dependency_overrides[get_db] = lambda: None  # Mock for testing

    # Create user using the User model (simplified for testing)
    user = User(
        email=test_user_hashed["email"],
        password_hash=test_user_hashed["password_hash"],
        full_name=test_user_hashed["full_name"],
        is_active=test_user_hashed["is_active"],
        is_verified=test_user_hashed["is_verified"],
    )

    yield user

    # Cleanup dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def invalid_user_data() -> dict:
    """
    Provide invalid user data for negative testing.

    Algorithm Approach: Various invalid data scenarios
    Time Complexity: O(1) - Data creation
    Space Complexity: O(1) - Constant data size

    Returns:
    dict: Invalid user data for testing validation
    """
    return {
        "email": "invalid-email",
        "password": "123",  # Too short
        "full_name": "",  # Empty name
    }


@pytest.fixture
def rate_limit_headers() -> dict:
    """
    Provide rate limiting headers for testing.

    Algorithm Approach: Standard rate limiting header format
    Time Complexity: O(1) - Header creation
    Space Complexity: O(1) - Constant header size

    Returns:
    dict: Rate limiting headers
    """
    return {
        "X-RateLimit-Limit": "5",
        "X-RateLimit-Remaining": "4",
        "X-RateLimit-Reset": "1640995200",
    }


@pytest.fixture
def jwt_test_data() -> dict:
    """
    Provide JWT token test data.

    Algorithm Approach: Standard JWT payload structure
    Time Complexity: O(1) - Payload creation
    Space Complexity: O(1) - Constant payload size

    Returns:
    dict: JWT token test data
    """
    return {
        "sub": "test@example.com",
        "exp": 1640995200,  # Fixed timestamp for testing
        "iat": 1640991600,
        "type": "access",
    }


@pytest.fixture
def mock_config() -> dict:
    """
    Provide mock configuration for testing.

    Algorithm Approach: Test-specific configuration values
    Time Complexity: O(1) - Config creation
    Space Complexity: O(1) - Constant config size

    Returns:
    dict: Mock configuration values
    """
    return {
        "SECRET_KEY": "test-secret-key-for-jwt-signing-12345",
        "ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": 30,
        "PASSWORD_PEPPER": "test-pepper-value",
        "BCRYPT_ROUNDS": 12,
        "RATE_LIMIT_REQUESTS": 5,
        "RATE_LIMIT_WINDOW": 300,
    }


@pytest.fixture
def mock_redis():
    """
    Mock Redis for testing rate limiting functionality.

    Algorithm Approach: Mock Redis client with expected behavior
    Time Complexity: O(1) - Mock setup
    Space Complexity: O(1) - Minimal mock overhead

    Yields:
    MockRedis: Mocked Redis client for testing
    """

    class MockRedis:
        def __init__(self):
            self.storage = {}

        async def get(self, key: str):
            return self.storage.get(key)

        async def set(self, key: str, value: str, ex: int = None):
            self.storage[key] = value
            return True

        async def incr(self, key: str):
            if key not in self.storage:
                self.storage[key] = "1"
            else:
                self.storage[key] = str(int(self.storage[key]) + 1)
            return int(self.storage[key])

        async def expire(self, key: str, seconds: int):
            # Mock expiration - would use proper TTL in real Redis
            return True

    return MockRedis()


# Test markers for categorization
pytest_plugins = []


def pytest_configure(config):
    """
    Configure pytest with custom markers.

    Algorithm Approach: Standard pytest configuration
    Time Complexity: O(1) - Configuration setup
    Space Complexity: O(1) - Marker registration

    Args:
    config: Pytest configuration object
    """
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "security: mark test as a security test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "auth: mark test as authentication-related")
