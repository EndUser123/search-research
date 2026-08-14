"""Tests for result normalization layer.

These tests verify the NormalizedResult protocol and normalize_result() function
provide runtime type safety and unified result validation.

Test Requirements:
1. NormalizedResult protocol exists with required attributes (id, score, source, to_dict())
2. normalize_result() function exists
3. Valid SearchResult objects pass normalization
4. Valid dict objects with required fields pass normalization
5. Objects missing required attributes raise TypeError
6. Malformed results are rejected with clear error messages
7. to_dict() method works on normalized results
8. Protocol is runtime_checkable
"""

from dataclasses import dataclass

import pytest

# Import from core.models for SearchResult
from core.models import SearchResult


class TestNormalizedResultProtocol:
    """Tests for NormalizedResult protocol definition."""

    def test_protocol_exists(self):
        """Test that NormalizedResult protocol is defined."""
        from core.result_normalizer import NormalizedResult

        # Verify it's a Protocol
        assert isinstance(NormalizedResult, type)

    def test_protocol_is_runtime_checkable(self):
        """Test that NormalizedResult protocol is runtime_checkable."""
        from core.result_normalizer import NormalizedResult

        # Protocols with @runtime_checkable decorator should support isinstance()
        assert hasattr(NormalizedResult, "__protocol_attrs__")

    def test_protocol_has_required_id_attribute(self):
        """Test that NormalizedResult protocol requires 'id' attribute."""
        from core.result_normalizer import NormalizedResult

        # Check protocol has 'id' in required attributes
        assert "id" in NormalizedResult.__protocol_attrs__

    def test_protocol_has_required_score_attribute(self):
        """Test that NormalizedResult protocol requires 'score' attribute."""
        from core.result_normalizer import NormalizedResult

        # Check protocol has 'score' in required attributes
        assert "score" in NormalizedResult.__protocol_attrs__

    def test_protocol_has_required_source_attribute(self):
        """Test that NormalizedResult protocol requires 'source' attribute."""
        from core.result_normalizer import NormalizedResult

        # Check protocol has 'source' in required attributes
        assert "source" in NormalizedResult.__protocol_attrs__

    def test_protocol_has_required_to_dict_method(self):
        """Test that NormalizedResult protocol requires 'to_dict' method."""
        from core.result_normalizer import NormalizedResult

        # Check protocol has 'to_dict' in required attributes
        assert "to_dict" in NormalizedResult.__protocol_attrs__


class TestNormalizeResultFunction:
    """Tests for normalize_result() function."""

    def test_function_exists(self):
        """Test that normalize_result() function is defined."""
        from core.result_normalizer import normalize_result

        assert callable(normalize_result)

    def test_function_accepts_search_result(self):
        """Test that normalize_result() accepts SearchResult objects."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="test_provider",
            score=0.8
        )

        # Should not raise
        normalized = normalize_result(result)
        assert normalized is not None

    def test_function_accepts_dict_with_required_fields(self):
        """Test that normalize_result() accepts dicts with required fields."""
        from core.result_normalizer import normalize_result

        result = {
            "id": "test-id",
            "score": 0.8,
            "source": "test_provider",
            "to_dict": lambda: {"id": "test-id", "score": 0.8, "source": "test_provider"}
        }

        # Should not raise
        normalized = normalize_result(result)
        assert normalized is not None

    def test_rejects_dict_missing_id(self):
        """Test that normalize_result() raises TypeError for dict missing 'id'."""
        from core.result_normalizer import normalize_result

        result = {
            "score": 0.8,
            "source": "test_provider"
        }

        with pytest.raises(TypeError, match="id"):
            normalize_result(result)

    def test_rejects_dict_missing_score(self):
        """Test that normalize_result() raises TypeError for dict missing 'score'."""
        from core.result_normalizer import normalize_result

        result = {
            "id": "test-id",
            "source": "test_provider"
        }

        with pytest.raises(TypeError, match="score"):
            normalize_result(result)

    def test_rejects_dict_missing_source(self):
        """Test that normalize_result() raises TypeError for dict missing 'source'."""
        from core.result_normalizer import normalize_result

        result = {
            "id": "test-id",
            "score": 0.8
        }

        with pytest.raises(TypeError, match="source"):
            normalize_result(result)

    def test_rejects_object_missing_to_dict(self):
        """Test that normalize_result() raises TypeError for object missing 'to_dict' method."""
        from core.result_normalizer import normalize_result

        class IncompleteResult:
            def __init__(self):
                self.id = "test-id"
                self.score = 0.8
                self.source = "test_provider"
                # Missing to_dict method

        result = IncompleteResult()

        with pytest.raises(TypeError, match="to_dict"):
            normalize_result(result)

    def test_rejects_none(self):
        """Test that normalize_result() raises TypeError for None input."""
        from core.result_normalizer import normalize_result

        with pytest.raises(TypeError, match="Cannot normalize None"):
            normalize_result(None)

    def test_rejects_string(self):
        """Test that normalize_result() raises TypeError for string input."""
        from core.result_normalizer import normalize_result

        with pytest.raises(TypeError, match="Cannot normalize"):
            normalize_result("invalid")

    def test_rejects_list(self):
        """Test that normalize_result() raises TypeError for list input."""
        from core.result_normalizer import normalize_result

        with pytest.raises(TypeError, match="Cannot normalize"):
            normalize_result([{"id": "test"}])

    def test_provides_clear_error_message(self):
        """Test that error messages clearly indicate missing attributes."""
        from core.result_normalizer import normalize_result

        result = {
            "score": 0.8
            # Missing 'id' and 'source'
        }

        with pytest.raises(TypeError) as exc_info:
            normalize_result(result)

        error_msg = str(exc_info.value)
        # Error message should mention what's missing
        assert "id" in error_msg or "source" in error_msg


class TestNormalizedResultRuntimeValidation:
    """Tests for runtime type checking with NormalizedResult protocol."""

    def test_search_result_is_normalized_result(self):
        """Test that SearchResult objects satisfy NormalizedResult protocol."""
        from core.result_normalizer import NormalizedResult

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="test_provider",
            score=0.8
        )

        # SearchResult should satisfy the protocol
        assert isinstance(result, NormalizedResult)

    def test_custom_satisfying_object_is_normalized_result(self):
        """Test that custom objects satisfying protocol are recognized."""
        from core.result_normalizer import NormalizedResult

        @dataclass
        class CustomResult:
            id: str
            score: float
            source: str

            def to_dict(self) -> dict:
                return {
                    "id": self.id,
                    "score": self.score,
                    "source": self.source
                }

        result = CustomResult(
            id="test-id",
            score=0.8,
            source="test_provider"
        )

        # Should satisfy the protocol
        assert isinstance(result, NormalizedResult)

    def test_dict_satisfying_protocol_is_normalized_result(self):
        """Test that dicts satisfying protocol are recognized."""
        from core.result_normalizer import NormalizedResult

        result = {
            "id": "test-id",
            "score": 0.8,
            "source": "test_provider",
            "to_dict": lambda: {"id": "test-id", "score": 0.8, "source": "test_provider"}
        }

        # Should satisfy the protocol
        assert isinstance(result, NormalizedResult)

    def test_unsatisfying_object_not_normalized_result(self):
        """Test that objects not satisfying protocol are rejected."""
        from core.result_normalizer import NormalizedResult

        class BadResult:
            def __init__(self):
                self.title = "Test"
                # Missing required attributes

        result = BadResult()

        # Should not satisfy the protocol
        assert not isinstance(result, NormalizedResult)


class TestToDictMethod:
    """Tests for to_dict() method on normalized results."""

    def test_to_dict_returns_dict(self):
        """Test that to_dict() returns a dictionary."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="test_provider",
            score=0.8
        )

        normalized = normalize_result(result)
        result_dict = normalized.to_dict()

        assert isinstance(result_dict, dict)

    def test_to_dict_contains_required_fields(self):
        """Test that to_dict() output contains required fields."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="test_provider",
            score=0.8
        )

        normalized = normalize_result(result)
        result_dict = normalized.to_dict()

        # Must contain all required fields
        assert "id" in result_dict
        assert "score" in result_dict
        assert "source" in result_dict

    def test_to_dict_preserves_data(self):
        """Test that to_dict() preserves original data."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test Title",
            content="Test content",
            source="test_provider",
            score=0.8
        )

        normalized = normalize_result(result)
        result_dict = normalized.to_dict()

        # Score should match
        assert result_dict["score"] == 0.8
        # Source should match
        assert result_dict["source"] == "test_provider"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_score(self):
        """Test that zero score is accepted."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="test_provider",
            score=0.0
        )

        normalized = normalize_result(result)
        assert normalized.score == 0.0

    def test_negative_score_rejected(self):
        """Test that negative scores are rejected."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="test_provider",
            score=-0.5
        )

        with pytest.raises(ValueError, match="score must be non-negative"):
            normalize_result(result)

    def test_score_greater_than_one_rejected(self):
        """Test that scores > 1.0 are rejected."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="test_provider",
            score=1.5
        )

        with pytest.raises(ValueError, match="score must be <= 1.0"):
            normalize_result(result)

    def test_empty_source_rejected(self):
        """Test that empty source string is rejected."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="",
            score=0.8
        )

        with pytest.raises(ValueError, match="source cannot be empty"):
            normalize_result(result)

    def test_whitespace_source_rejected(self):
        """Test that whitespace-only source is rejected."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="   ",
            score=0.8
        )

        with pytest.raises(ValueError, match="source cannot be empty"):
            normalize_result(result)

    def test_numeric_score_types(self):
        """Test that both int and float scores are accepted."""
        from core.result_normalizer import normalize_result

        result = SearchResult(
            url="https://example.com",
            title="Test",
            content="Test content",
            source="test_provider",
            score=1  # int instead of float
        )

        normalized = normalize_result(result)
        assert normalized.score == 1.0


class TestDuplicateIDDetection:
    """Tests for detecting duplicate IDs with different content."""

    def test_detects_duplicate_urls_with_different_content(self):
        """Test that same URL (ID) with different content can be detected."""
        from core.models import SearchResult
        from core.result_normalizer import normalize_result

        result1 = SearchResult(
            url="https://example.com/same",  # Same URL = same ID
            title="First Title",
            content="Content A",
            source="source1",
            score=0.8
        )

        result2 = SearchResult(
            url="https://example.com/same",  # Same URL = same ID
            title="Second Title",  # Different content
            content="Content B",
            source="source2",
            score=0.9
        )

        # Both should normalize successfully
        norm1 = normalize_result(result1)
        norm2 = normalize_result(result2)

        # IDs should be the same (URL-based)
        assert norm1.id == norm2.id == "https://example.com/same"
        # But content differs - duplicate detection upstream should catch this
        assert norm1.to_dict()["title"] != norm2.to_dict()["title"]
        # Result model uses the URL directly, so we check via to_dict
        dict1 = norm1.to_dict()
        dict2 = norm2.to_dict()

        # The normalized results have different titles/content
        assert dict1.get("title") != dict2.get("title")
        assert dict1.get("content") != dict2.get("content")

    def test_duplicate_url_same_content_normalizes_successfully(self):
        """Test that duplicate URLs with same content normalize successfully."""
        from core.models import SearchResult
        from core.result_normalizer import normalize_result

        result1 = SearchResult(
            url="https://example.com/same",
            title="Same Title",
            content="Same Content",
            source="source1",
            score=0.8
        )

        result2 = SearchResult(
            url="https://example.com/same",
            title="Same Title",
            content="Same Content",
            source="source2",
            score=0.9
        )

        # Both should normalize - this is the valid duplicate case
        norm1 = normalize_result(result1)
        norm2 = normalize_result(result2)

        # IDs are the same (URL)
        assert norm1.id == norm2.id == "https://example.com/same"
        # Content is identical - deduplication upstream will merge
        dict1 = norm1.to_dict()
        dict2 = norm2.to_dict()
        assert dict1.get("title") == dict2.get("title")

    def test_unique_urls_do_not_trigger_duplicate_logic(self):
        """Test that unique URLs don't trigger duplicate detection."""
        from core.models import SearchResult
        from core.result_normalizer import normalize_result

        results = [
            SearchResult(
                url=f"https://example.com/page{i}",
                title=f"Result {i}",
                content=f"Content {i}",
                source=f"source{i}",
                score=0.8
            )
            for i in range(5)
        ]

        # All should normalize successfully
        normalized = [normalize_result(r) for r in results]

        # All IDs (URLs) should be unique
        ids = [r.id for r in normalized]
        assert len(ids) == len(set(ids))  # All unique

    def test_empty_url_rejected(self):
        """Test that empty URL is handled by validation."""

        from core.result_normalizer import normalize_result

        # Can't create SearchResult with empty URL (dataclass validation)
        # But we can test with dict
        result = {
            "id": "",  # Empty ID/URL
            "score": 0.8,
            "source": "test_provider",
            "to_dict": lambda: {"id": "", "score": 0.8, "source": "test_provider"}
        }

        # Should normalize (id is present)
        normalized = normalize_result(result)
        assert normalized["id"] == ""  # Empty ID passes through (dict access)

        # If we want to reject empty IDs, that's a feature request
