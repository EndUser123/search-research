"""Pytest configuration and fixtures."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add search_research package to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_query():
    """Sample search query for testing."""
    return "FastAPI patterns"


@pytest.fixture
def sample_results():
    """Sample search results for testing."""
    from datetime import datetime

    return [
        {
            "title": "FastAPI Route",
            "content": "FastAPI route decorator example",
            "url": None,
            "file_path": "app.py",
            "line_number": 10,
            "source": "CDS",
            "score": 0.95,
            "metadata": {},
            "created_at": datetime.now(),
            "cached": False,
        },
        {
            "title": "Best Practices",
            "content": "FastAPI best practices guide",
            "url": "https://example.com/fastapi",
            "file_path": None,
            "line_number": None,
            "source": "Tavily",
            "score": 0.85,
            "metadata": {},
            "created_at": datetime.now(),
            "cached": False,
        },
    ]


@pytest.fixture
def mock_backend():
    """Mock search backend for testing."""
    backend = MagicMock()
    backend.search.return_value = []
    backend.available = True
    backend.BACKEND_NAME = "MockBackend"
    return backend


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporary cache directory for testing."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def no_api_keys(monkeypatch):
    """Ensure no API keys are set for testing graceful degradation."""
    for key in ["TAVILY_API_KEY", "SERPER_API_KEY", "EXA_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
