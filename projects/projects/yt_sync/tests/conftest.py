from unittest.mock import AsyncMock

import pytest
from faker import Faker


# Global fixtures available to all tests
@pytest.fixture
def faker():
    """Provides Faker instance for test data generation."""
    return Faker()


@pytest.fixture
def mock_async():
    """Factory for creating AsyncMock with proper cleanup."""
    mocks = []

    def _create_mock(**kwargs):
        mock = AsyncMock(**kwargs)
        mocks.append(mock)
        return mock

    yield _create_mock
    # Cleanup
    for mock in mocks:
        mock.reset_mock()


@pytest.fixture(autouse=True)
def fast_tests(monkeypatch):
    """Make all tests fast by default."""
    # Patch sleep functions to return immediately
    monkeypatch.setattr("time.sleep", lambda x: None)
    monkeypatch.setattr("asyncio.sleep", AsyncMock())
