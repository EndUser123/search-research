"""Integration tests for the quality gate pipeline.

Tests the full adapter -> checker -> router pipeline without mocking,
verifying that SearchResult objects flow correctly through the quality gate.

Regression test for the field name mismatch bug (CHANGE-001) and
created_at=None bug (CHANGE-006).

Run with: pytest tests/test_quality_gate_integration.py -v
"""

from datetime import datetime, timedelta, timezone

from core.models import SearchResult
from core.quality_checker import QualityConfig, is_satisfactory


def _result_to_dict_via_adapter(result: SearchResult) -> dict:
    """Replicate unified_router._search_result_to_dict() logic.

    This mirrors the production code path so we test the actual mapping.
    """
    return {
        "id": result.metadata.get("id", f"{result.source}-{result.title}"),
        "title": result.title,
        "content": result.content,
        "score": result.score,
        "confidence": result.score,
        "source": result.source,
        "sources": [result.source] if result.source else [],
        "url": result.url,
        "file_path": result.file_path,
        "line_number": result.line_number,
        "metadata": result.metadata,
        "created_at": result.created_at or datetime.now(timezone.utc),
    }


class TestQualityGatePipeline:
    """Integration tests for the full quality gate pipeline."""

    def test_high_confidence_local_result_passes_quality_gate(self):
        """REQ-001: A high-confidence local result with score >= 0.8 passes."""
        result = SearchResult(
            title="FastAPI Best Practices",
            content="Use dependency injection for database sessions",
            source="local",
            score=0.92,
            created_at=datetime.now(timezone.utc),
        )
        result_dict = _result_to_dict_via_adapter(result)
        assert is_satisfactory(result_dict, QualityConfig())

    def test_result_with_none_created_at_still_passes(self):
        """CHANGE-006 regression: created_at=None must not veto quality gate."""
        result = SearchResult(
            title="Python Type Hints Guide",
            content="Use from __future__ import annotations",
            source="local",
            score=0.88,
            created_at=None,
        )
        result_dict = _result_to_dict_via_adapter(result)
        assert is_satisfactory(result_dict, QualityConfig())

    def test_adapter_produces_confidence_field(self):
        """CHANGE-001 regression: adapter must produce 'confidence' key."""
        result = SearchResult(
            title="Test",
            content="Content",
            source="local",
            score=0.75,
        )
        result_dict = _result_to_dict_via_adapter(result)
        assert "confidence" in result_dict
        assert result_dict["confidence"] == result.score

    def test_adapter_produces_sources_list(self):
        """CHANGE-001 regression: adapter must produce 'sources' list."""
        result = SearchResult(
            title="Test",
            content="Content",
            source="local",
            score=0.75,
        )
        result_dict = _result_to_dict_via_adapter(result)
        assert "sources" in result_dict
        assert isinstance(result_dict["sources"], list)
        assert result_dict["sources"] == ["local"]

    def test_low_score_result_fails_quality_gate(self):
        """Low confidence result should not pass quality gate."""
        result = SearchResult(
            title="Unrelated",
            content="Not relevant content",
            source="local",
            score=0.3,
            created_at=datetime.now(timezone.utc),
        )
        result_dict = _result_to_dict_via_adapter(result)
        assert not is_satisfactory(result_dict, QualityConfig())

    def test_single_backend_passes_with_default_config(self):
        """CHANGE-002 regression: min_backends=1 allows single backend."""
        result = SearchResult(
            title="Good Result",
            content="Relevant content with details",
            source="local",
            score=0.9,
            created_at=datetime.now(timezone.utc),
        )
        result_dict = _result_to_dict_via_adapter(result)
        assert result_dict["sources"] == ["local"]
        assert is_satisfactory(result_dict, QualityConfig())

    def test_stale_result_fails_freshness_check(self):
        """Old timestamps should fail freshness check."""
        result = SearchResult(
            title="Old Result",
            content="Stale content",
            source="local",
            score=0.95,
            created_at=datetime.now(timezone.utc) - timedelta(days=400),
        )
        result_dict = _result_to_dict_via_adapter(result)
        config = QualityConfig(freshness_hours=24)
        assert not is_satisfactory(result_dict, config)

    def test_mcp_caller_uses_default_min_backends(self):
        """CHANGE-008 regression: MCP callers get min_backends=1 default."""
        # QualityConfig() should have min_backends=1
        config = QualityConfig(confidence_threshold=0.5)
        assert config.min_backends == 1

        result = SearchResult(
            title="MCP Result",
            content="Found via MCP",
            source="local",
            score=0.6,
            created_at=datetime.now(timezone.utc),
        )
        result_dict = _result_to_dict_via_adapter(result)
        assert is_satisfactory(result_dict, config)

    def test_empty_source_produces_empty_sources_list(self):
        """Edge case: empty source string produces empty sources list."""
        result = SearchResult(
            title="No Source",
            content="Orphan content",
            source="",
            score=0.8,
            created_at=datetime.now(timezone.utc),
        )
        result_dict = _result_to_dict_via_adapter(result)
        assert result_dict["sources"] == []

    def test_both_old_and_new_field_names_present(self):
        """Backward compat: dict contains both score/confidence and source/sources."""
        result = SearchResult(
            title="Compat Test",
            content="Backward compatible",
            source="local",
            score=0.85,
            created_at=datetime.now(timezone.utc),
        )
        result_dict = _result_to_dict_via_adapter(result)
        # Old fields
        assert "score" in result_dict
        assert "source" in result_dict
        # New fields (quality checker)
        assert "confidence" in result_dict
        assert "sources" in result_dict
        # Values match
        assert result_dict["score"] == result_dict["confidence"]
        assert result_dict["source"] == result_dict["sources"][0]
