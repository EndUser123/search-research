"""Auto-scaffolded test for youtube."""

import pytest  # noqa: F401
from core.providers.you import YouBackend


def test_youtube_exists():
    """Smoke test: YouBackend can be imported."""
    assert YouBackend is not None


# TODO: Add more tests based on actual functionality
# Run: pytest tests/test_youtube.py -v
