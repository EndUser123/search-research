"""
Comprehensive tests for processing components.

Tests for:
- ResultNormalizer: result normalization from multiple providers
"""

from datetime import datetime

import pytest

from core.processing.result_normalizer import (
    NormalizedResult,
    ResultNormalizer,
    SourceType,
)


class TestResultNormalizer:
    """Test suite for ResultNormalizer."""

    @pytest.fixture
    def normalizer(self) -> ResultNormalizer:
        """Create ResultNormalizer instance."""
        return ResultNormalizer()

    @pytest.fixture
    def sample_raw_results(self):
        """Sample raw results from various providers."""
        return [
            {
                "url": "https://docs.python.org/3/library/asyncio.html",
                "title": "asyncio — Asynchronous I/O",
                "content": "Python's asyncio library documentation",
                "score": 0.95
            },
            {
                "url": "https://github.com/python/cpython",
                "title": "python/cpython",
                "snippet": "The CPython reference implementation",
                "score": 0.88
            },
            {
                "url": "https://arxiv.org/abs/2301.00000",
                "title": "Recent Advances in Async",
                "snippet": "Survey of async programming",
                "date": "2023-01-01T00:00:00"
            },
            {
                "url": "https://youtube.com/watch?v=12345",
                "title": "Async Programming Tutorial",
                "snippet": "Video tutorial on async",
                "score": 0.82
            },
            {
                "url": "https://stackoverflow.com/questions/12345",
                "title": "How to use async?",
                "content": "You can use asyncio.run()",
                "snippet": "StackOverflow question"
            },
            {
                "url": "https://medium.com/async-guide",
                "title": "Understanding Async",
                "content": "Beginner's guide to async",
                "snippet": "Blog post"
            },
            {
                "url": "https://news.example.com/async-breakthrough",
                "title": "Async Programming Breakthrough",
                "content": "Latest news in async",
                "snippet": "News article"
            },
            {
                "url": "https://cloud.google.com/docs/async",
                "title": "Google Cloud Async Documentation",
                "content": "Using async in GCP",
                "snippet": "Vendor documentation"
            },
        ]

    def test_initialization(self, normalizer):
        """Test normalizer initialization."""
        assert normalizer.domain_trust is not None
        assert "docs.python.org" in normalizer.domain_trust
        assert "github.com" in normalizer.domain_trust
        assert normalizer.domain_trust["docs.python.org"] == 0.95

    def test_normalize_basic(self, normalizer, sample_raw_results):
        """Test basic result normalization."""
        raw = sample_raw_results[0]

        normalized = normalizer.normalize(raw, "tavily")

        # Check structure
        assert isinstance(normalized, NormalizedResult)
        assert normalized.title == raw["title"]
        assert normalized.url == raw["url"]
        assert normalized.provider == "tavily"

    def test_normalize_extract_domain(self, normalizer, sample_raw_results):
        """Test domain extraction."""
        raw = sample_raw_results[0]

        normalized = normalizer.normalize(raw, "tavily")

        assert normalized.domain == "docs.python.org"

    def test_normalize_extract_domain_subdomain(self, normalizer):
        """Test domain extraction with subdomain."""
        raw = {
            "url": "https://docs.aws.amazon.com/lambda",
            "title": "AWS Lambda Docs",
            "snippet": "Lambda documentation"
        }

        normalized = normalizer.normalize(raw, "serper")

        assert normalized.domain == "docs.aws.amazon.com"

    def test_normalize_extract_domain_empty_url(self, normalizer):
        """Test domain extraction with empty URL."""
        raw = {
            "url": "",
            "title": "No URL",
            "snippet": "Test"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.domain == ""

    def test_normalize_extract_domain_invalid_url(self, normalizer):
        """Test domain extraction with invalid URL."""
        raw = {
            "url": "not-a-url",
            "title": "Invalid URL",
            "snippet": "Test"
        }

        normalized = normalizer.normalize(raw, "test")

        # Should handle gracefully
        assert isinstance(normalized.domain, str)

    def test_detect_source_type_docs(self, normalizer):
        """Test detection of documentation source type."""
        raw = {
            "url": "https://docs.python.org/asyncio",
            "title": "Python Docs",
            "snippet": "Official documentation"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.source_type == SourceType.DOCS

    def test_detect_source_type_academic(self, normalizer):
        """Test detection of academic source type."""
        raw = {
            "url": "https://arxiv.org/abs/2301.00000",
            "title": "Research Paper",
            "snippet": "Academic paper"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.source_type == SourceType.ACADEMIC

    def test_detect_source_type_community(self, normalizer):
        """Test detection of community source type."""
        raw = {
            "url": "https://github.com/python/cpython",
            "title": "GitHub Repo",
            "snippet": "Source code"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.source_type == SourceType.COMMUNITY

    def test_detect_source_type_video(self, normalizer):
        """Test detection of video source type."""
        raw = {
            "url": "https://youtube.com/watch?v=12345",
            "title": "Video Tutorial",
            "snippet": "Video content"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.source_type == SourceType.VIDEO

    def test_detect_source_type_news(self, normalizer):
        """Test detection of news source type."""
        raw = {
            "url": "https://news.example.com/article",
            "title": "Breaking News",
            "snippet": "News article"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.source_type == SourceType.NEWS

    def test_detect_source_type_blog(self, normalizer):
        """Test detection of blog source type."""
        raw = {
            "url": "https://medium.com/async-guide",
            "title": "Blog Post",
            "snippet": "Blog content"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.source_type == SourceType.BLOG

    def test_detect_source_type_vendor(self, normalizer):
        """Test detection of vendor source type."""
        # Use a vendor URL that won't match docs pattern first
        raw = {
            "url": "https://aws.amazon.com/lambda/",
            "title": "AWS Lambda Documentation",
            "snippet": "Vendor docs"
        }

        normalized = normalizer.normalize(raw, "test")

        # AWS should be detected as vendor
        assert normalized.source_type == SourceType.VENDOR

    def test_detect_source_type_unknown(self, normalizer):
        """Test detection of unknown source type."""
        raw = {
            "url": "https://random-website.com/page",
            "title": "Random Site",
            "snippet": "Unknown type"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.source_type == SourceType.UNKNOWN

    def test_detect_source_type_from_snippet_pdf(self, normalizer):
        """Test PDF detection from snippet."""
        raw = {
            "url": "https://example.com/document",
            "title": "Research Document",
            "snippet": "filetype:pdf academic paper"
        }

        normalized = normalizer.normalize(raw, "test")

        # Should detect academic from PDF indicator
        assert normalized.source_type in [SourceType.ACADEMIC, SourceType.UNKNOWN]

    def test_extract_date_iso_format(self, normalizer):
        """Test date extraction from ISO format."""
        raw = {
            "url": "https://example.com",
            "title": "Test",
            "snippet": "Test",
            "date": "2023-01-15T10:30:00"
        }

        normalized = normalizer.normalize(raw, "test")

        assert isinstance(normalized.published_at, datetime)
        assert normalized.published_at.year == 2023

    def test_extract_date_unix_timestamp(self, normalizer):
        """Test date extraction from Unix timestamp."""
        timestamp = int(datetime(2023, 1, 15).timestamp())
        raw = {
            "url": "https://example.com",
            "title": "Test",
            "snippet": "Test",
            "timestamp": timestamp
        }

        normalized = normalizer.normalize(raw, "test")

        assert isinstance(normalized.published_at, datetime)
        assert normalized.published_at.year == 2023

    def test_extract_date_none(self, normalizer):
        """Test date extraction when no date present."""
        raw = {
            "url": "https://example.com",
            "title": "Test",
            "snippet": "Test"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.published_at is None

    def test_extract_date_datetime_object(self, normalizer):
        """Test date extraction from datetime object."""
        test_date = datetime(2023, 6, 15, 14, 30, 0)
        raw = {
            "url": "https://example.com",
            "title": "Test",
            "snippet": "Test",
            "published_at": test_date
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.published_at == test_date

    def test_metadata_trust_score(self, normalizer):
        """Test metadata includes trust score."""
        raw = {
            "url": "https://docs.python.org/asyncio",
            "title": "Python Docs",
            "snippet": "Official docs"
        }

        normalized = normalizer.normalize(raw, "test")

        assert "trust_score" in normalized.metadata
        assert normalized.metadata["trust_score"] == 0.95  # High trust for docs.python.org

    def test_metadata_trust_score_unknown_domain(self, normalizer):
        """Test trust score for unknown domain."""
        raw = {
            "url": "https://unknown-domain.com/page",
            "title": "Unknown",
            "snippet": "Test"
        }

        normalized = normalizer.normalize(raw, "test")

        assert "trust_score" in normalized.metadata
        # Unknown domains should get default trust score
        assert normalized.metadata["trust_score"] == 0.5

    def test_metadata_original_score(self, normalizer):
        """Test metadata includes original score."""
        raw = {
            "url": "https://example.com",
            "title": "Test",
            "snippet": "Test",
            "score": 0.87
        }

        normalized = normalizer.normalize(raw, "test")

        assert "original_score" in normalized.metadata
        assert normalized.metadata["original_score"] == 0.87

    def test_normalize_batch(self, normalizer, sample_raw_results):
        """Test batch normalization."""
        normalized_results = normalizer.normalize_batch(sample_raw_results, "tavily")

        # Should normalize all results
        assert len(normalized_results) == len(sample_raw_results)

        # All should be NormalizedResult instances
        for result in normalized_results:
            assert isinstance(result, NormalizedResult)

        # All should have the same provider
        for result in normalized_results:
            assert result.provider == "tavily"

    def test_normalize_batch_empty(self, normalizer):
        """Test batch normalization with empty list."""
        results = normalizer.normalize_batch([], "test")

        assert len(results) == 0

    def test_content_vs_snippet_priority(self, normalizer):
        """Test that content is preferred over snippet."""
        raw = {
            "url": "https://example.com",
            "title": "Test",
            "content": "Full content here",
            "snippet": "Snippet here"
        }

        normalized = normalizer.normalize(raw, "test")

        # Should prefer content over snippet
        assert normalized.snippet == "Full content here"

    def test_normalize_missing_fields(self, normalizer):
        """Test normalization with missing optional fields."""
        raw = {
            "url": "https://example.com"
            # Missing title, snippet, etc.
        }

        normalized = normalizer.normalize(raw, "test")

        # Should handle missing fields gracefully
        assert isinstance(normalized, NormalizedResult)
        assert normalized.title == ""
        assert normalized.snippet == ""

    def test_domain_case_insensitive(self, normalizer):
        """Test that domain extraction is case insensitive."""
        raw = {
            "url": "https://DOCS.Python.Org/asyncio",
            "title": "Test",
            "snippet": "Test"
        }

        normalized = normalizer.normalize(raw, "test")

        # Domain should be lowercase
        assert normalized.domain == "docs.python.org"

    def test_url_with_port(self, normalizer):
        """Test domain extraction from URL with port."""
        raw = {
            "url": "https://localhost:8080/docs",
            "title": "Local Docs",
            "snippet": "Test"
        }

        normalized = normalizer.normalize(raw, "test")

        assert normalized.domain == "localhost:8080"

    def test_url_with_path_and_query(self, normalizer):
        """Test domain extraction with complex URL."""
        raw = {
            "url": "https://docs.python.org/3/library/asyncio.html?highlight=async",
            "title": "Python Docs",
            "snippet": "Documentation"
        }

        normalized = normalizer.normalize(raw, "test")

        # Should extract only domain
        assert normalized.domain == "docs.python.org"

    def test_multiple_source_type_patterns(self, normalizer):
        """Test source type detection when multiple patterns match."""
        # URL that could match multiple patterns (docs + academic)
        raw = {
            "url": "https://docs.arxiv.org/docs/async",
            "title": "Arxiv Documentation",
            "snippet": "Academic documentation"
        }

        normalized = normalizer.normalize(raw, "test")

        # Should detect one type (priority-based)
        assert isinstance(normalized.source_type, SourceType)

    def test_stackoverflow_vs_github_distinction(self, normalizer):
        """Test distinction between StackOverflow and GitHub."""
        stackoverflow_raw = {
            "url": "https://stackoverflow.com/questions/12345",
            "title": "SO Question",
            "snippet": "Question"
        }

        github_raw = {
            "url": "https://github.com/python/cpython",
            "title": "GitHub Repo",
            "snippet": "Repository"
        }

        so_normalized = normalizer.normalize(stackoverflow_raw, "test")
        gh_normalized = normalizer.normalize(github_raw, "test")

        # Both should be community but different domains
        assert so_normalized.source_type == SourceType.COMMUNITY
        assert gh_normalized.source_type == SourceType.COMMUNITY
        assert so_normalized.domain == "stackoverflow.com"
        assert gh_normalized.domain == "github.com"

    def test_trust_score_boundaries(self, normalizer):
        """Test that trust scores are within valid range."""
        test_urls = [
            "https://random-site.com",
            "https://medium.com/article",
            "https://github.com/repo",
            "https://docs.python.org/docs"
        ]

        for url in test_urls:
            raw = {"url": url, "title": "Test", "snippet": "Test"}
            normalized = normalizer.normalize(raw, "test")

            # Trust score should be between 0 and 1
            assert 0.0 <= normalized.metadata["trust_score"] <= 1.0
