"""Tests for SearchResult models."""

import pytest
from datetime import datetime
from core.models import SearchResult


def test_search_result_to_dict():
    """Test SearchResult.to_dict() produces correct output."""
    result = SearchResult(
        title="Test",
        content="Content",
        source="test",
        score=0.95,
        url="https://example.com",
    )
    d = result.to_dict()
    assert d["title"] == "Test"
    assert d["content"] == "Content"
    assert d["source"] == "test"
    assert d["score"] == 0.95
    assert d["url"] == "https://example.com"
    assert d["cached"] == False


def test_search_result_from_dict():
    """Test SearchResult.from_dict() reconstructs from cache dict."""
    original = SearchResult(
        title="Cached Result",
        content="Cached content",
        source="cache",
        score=0.85,
        url="https://cached.example.com",
        file_path=None,
        line_number=None,
        backend="cache",
        fetched=False,
        fetch_time=None,
        created_at=datetime(2024, 1, 15, 10, 30, 0),
        cached=True,
        metadata={"key": "value"},
    )
    d = original.to_dict()
    reconstructed = SearchResult.from_dict(d)

    assert reconstructed.title == original.title
    assert reconstructed.content == original.content
    assert reconstructed.source == original.source
    assert reconstructed.score == original.score
    assert reconstructed.url == original.url
    assert reconstructed.cached == original.cached
    assert reconstructed.metadata == original.metadata


def test_search_result_from_dict_roundtrip():
    """Test that to_dict -> from_dict produces equivalent object."""
    result = SearchResult(
        title="Roundtrip Test",
        content="Testing roundtrip",
        source="pytest",
        score=1.0,
    )

    # Simulate cache storage and retrieval
    cached_dicts = [r.to_dict() for r in [result]]
    retrieved = [SearchResult.from_dict(d) for d in cached_dicts]

    assert len(retrieved) == 1
    assert retrieved[0].title == result.title
    assert retrieved[0].content == result.content
    assert retrieved[0].source == result.source
    assert retrieved[0].score == result.score


def test_search_result_required_fields():
    """Test SearchResult requires title, content, source, score."""
    with pytest.raises(TypeError):
        SearchResult()  # Missing required fields

    with pytest.raises(TypeError):
        SearchResult(title="Test")  # Missing content, source, score
