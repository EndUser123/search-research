"""Test fixtures."""

import pytest

@pytest.fixture
def sample_data():
    """Sample test data."""
    return {"key": "value"}

@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    return {
        "task_description": "test task",
        "mode": "test",
    }
