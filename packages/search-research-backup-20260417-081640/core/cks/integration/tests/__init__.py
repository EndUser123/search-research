import asyncio
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import pytest

"""CSF CKS Integration Tests

This package contains comprehensive tests for all integration components
including HDMA, Serena, Chat History, and Web Content clients.

Test Coverage:
- Unit tests for individual client functionality
- Integration tests for end-to-end workflows
- Performance tests for scalability
- Security tests for vulnerability detection
- Constitutional compliance tests

Test Categories:
- Unit Tests: Individual component testing
- Integration Tests: Multi-component workflows
- Mock Tests: Testing with mock external dependencies
- End-to-End Tests: Complete workflow testing
- Performance Tests: Scalability and efficiency
- Security Tests: Vulnerability and compliance testing

Test Strategy:
- Test-Driven Development (TDD) approach
- Red-Green-Refactor cycle
- Comprehensive edge case coverage
- Evidence-based testing with measurable outcomes
- CSF constitutional compliance validation

Example:
    >>> pytest src/features/cks/integration/tests/
    >>> pytest src/features/cks/integration/tests/test_hdma_client.py -v
    >>> pytest src/features/cks/integration/tests/ -k "test_security" --cov=src/features/cks/integration

"""


# Test fixtures
@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file for testing."""
    python_file = temp_dir / "test_sample.py"
    python_file.write_text(
        """
def example_function():
    '''Example function for testing.'''
    return "Hello, World!"

class ExampleClass:
    '''Example class for testing.'''

    def __init__(self):
        self.value = 42

    def method(self):
        return self.value * 2

if __name__ == "__main__":
    print(example_function())
    obj = ExampleClass()
    print(obj.method())
""",
    )
    return str(python_file)


@pytest.fixture
def sample_config():
    """Create sample integration configuration."""
    from ..utils.integration_factory import IntegrationSystemConfig

    return IntegrationSystemConfig(
        global_timeout_seconds=30,
        global_retry_attempts=2,
        enable_all_clients=True,
        log_level="DEBUG",
    )


# Test utilities
class MockAsyncResponse:
    """Mock async response for testing HTTP clients."""

    def __init__(
        self,
        status: int,
        data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> None:
        self.status = status
        self.data = data or {}
        self.text_data = text or ""

    async def json(self):
        return self.data

    async def text(self):
        return self.text_data

    def __aenter__(self):
        return self

    def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def create_test_clients():
    """Create test clients for integration testing."""
    from ..utils.integration_factory import IntegrationFactory

    factory = IntegrationFactory.create_minimal()
    clients = await factory.create_all_clients()
    return clients, factory


# Test markers
# pytest_plugins = []  # Removed: non-top-level


# Custom markers for test categorization
def pytest_configure(config) -> None:
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers",
        "unit: Mark test as unit test",
    )
    config.addinivalue_line(
        "markers",
        "integration: Mark test as integration test",
    )
    config.addinivalue_line(
        "markers",
        "security: Mark test as security test",
    )
    config.addinivalue_line(
        "markers",
        "performance: Mark test as performance test",
    )
    config.addinivalue_line(
        "markers",
        "mock: Mark test as using external mocks",
    )
    config.addinivalue_line(
        "markers",
        "slow: Mark test as slow running",
    )


# Test configuration
# pytest_plugins = []  # Removed: non-top-level
