"""Tests for LLM citation hook module."""

from unittest.mock import MagicMock, patch
import pytest

from yt_fts.search.llm_citation_hook import (
    track_citations,
    CitationTrackingError,
    CitationTracker,
    track_citations_decorator,
)


@pytest.fixture
def mock_extractor():
    extractor = MagicMock()
    extractor.extract_citations.return_value = [
        {"video_id": "abc123", "timestamp": "10:30", "text": "example citation"}
    ]
    return extractor


@pytest.fixture
def mock_llm_context():
    context = MagicMock()
    context.get_query.return_value = "test query"
    context.get_result_ids.return_value = ["id1", "id2"]
    return context


class TestCitationTracker:
    def test_initialization(self):
        tracker = CitationTracker("test query", ["id1", "id2"])
        assert tracker.query == "test query"
        assert tracker.result_ids == ["id1", "id2"]
        assert tracker.response is None
        assert tracker.citations == []

    def test_set_response_extracts_citations(self, mock_extractor):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=mock_extractor
        ):
            tracker = CitationTracker("query", ["id1"])
            tracker.set_response("Response with citation")
            
            assert tracker.response == "Response with citation"
            assert len(tracker.citations) == 1

    def test_get_response(self):
        tracker = CitationTracker("query", ["id1"])
        tracker.set_response("Test response")
        assert tracker.get_response() == "Test response"

    def test_get_citations(self, mock_extractor):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=mock_extractor
        ):
            tracker = CitationTracker("query", ["id1"])
            tracker.set_response("Response")
            citations = tracker.get_citations()
            assert isinstance(citations, list)


class TestTrackCitationsContextManager:
    def test_tracks_citations(self, mock_extractor):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=mock_extractor
        ):
            with track_citations("test query", ["id1", "id2"]) as tracker:
                tracker.set_response("Response with citation to abc123 at 10:30")
            
            mock_extractor.extract_citations.assert_called_once()
            citations = tracker.get_citations()
            assert len(citations) == 1

    def test_without_response(self):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=MagicMock()
        ):
            with track_citations("test query", ["id1", "id2"]) as tracker:
                pass
            assert tracker.get_citations() == []

    def test_stores_metadata(self):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=MagicMock()
        ):
            with track_citations("test query", ["id1", "id2", "id3"]) as tracker:
                assert tracker.query == "test query"
                assert tracker.result_ids == ["id1", "id2", "id3"]


class TestTrackCitationsDecorator:
    def test_tracks_citations(self, mock_extractor):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=mock_extractor
        ):
            @track_citations_decorator(query_arg="prompt", result_ids_arg="ids")
            def ask_llm(prompt, ids):
                return "Response with citation"
            
            result = ask_llm(prompt="test", ids=["id1"])
            assert result == "Response with citation"
            mock_extractor.extract_citations.assert_called_once()

    def test_with_function_args(self, mock_extractor):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=mock_extractor
        ):
            @track_citations_decorator(query_arg="query", result_ids_arg="result_ids")
            def ask_llm(query, result_ids, model="gpt-3"):
                return f"Response for {query}"
            
            result = ask_llm(query="test", result_ids=["id1"], model="gpt-4")
            assert "Response for test" in result


class TestCitationTrackingError:
    def test_error_message(self):
        error = CitationTrackingError("Failed to extract citations")
        assert "Failed to extract citations" in str(error)

    def test_is_exception(self):
        error = CitationTrackingError("Test")
        assert isinstance(error, Exception)


class TestEdgeCases:
    def test_empty_result_ids(self):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=MagicMock()
        ):
            with track_citations("test query", []) as tracker:
                tracker.set_response("Some response")
            assert tracker.result_ids == []

    def test_none_response(self):
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=MagicMock()
        ):
            with track_citations("test query", ["id1"]) as tracker:
                tracker.set_response(None)
            assert tracker.get_response() is None

    def test_unicode_response(self, mock_extractor):
        mock_extractor.extract_citations.return_value = []
        
        with patch(
            "yt_fts.search.llm_citation_hook.get_citation_extractor",
            return_value=mock_extractor
        ):
            with track_citations("test", ["id1"]) as tracker:
                tracker.set_response("Response with unicode chars")
            mock_extractor.extract_citations.assert_called_once()
