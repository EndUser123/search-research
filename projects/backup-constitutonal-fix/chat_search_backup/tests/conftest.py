from __future__ import annotations

import sys
from pathlib import Path

import pytest

#!/usr/bin/env python3
"""CSF NIP Chat Search Test Configuration.

Pytest configuration for chat search testing.
"""



# Add CSF NIP path for test imports
csf_nip_root = Path(__file__).parent.parent.parent.parent.parent.parent
if str(csf_nip_root) not in sys.path:
    sys.path.append(str(csf_nip_root))


@pytest.fixture(scope="session")
def test_logger():
    """Provide a test logger."""
    import logging

    logger = logging.getLogger("test")
    logger.setLevel(logging.DEBUG)

    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


@pytest.fixture
def mock_csf_nip_components() -> bool:
    """Mock CSF NIP components that might not be available."""
    import sys
    from unittest.mock import Mock

    # Mock modules that might not be available
    sys.modules["src.lib.core_utils.embedding_manager"] = Mock()
    sys.modules["src.lib.core_utils.api_failover_system"] = Mock()
    sys.modules["src.lib.core_utils.numpy_helpers"] = Mock()

    return True


@pytest.fixture(autouse=True)
def configure_logging(test_logger) -> None:
    """Configure logging for tests."""
    # Set logging level for all loggers
    logging.getLogger().setLevel(logging.WARNING)  # Reduce noise in tests


def pytest_configure(config) -> None:
    """Pytest configuration."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

    # Configure test output
    config.option.verbose = True
    config.option.tb = "short"
    config.option.showlocals = True
