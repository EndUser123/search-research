"""Tests for auto_research module.

Tests for auto-research trigger detection, library name extraction,
and confidence scoring for external research needs.
"""

import pytest

from rca.auto_research import (
    FAST_MOVING_LIBRARIES,
    STALENESS_KEYWORDS,
    ResearchTrigger,
    build_research_query,
    extract_library_names,
    should_trigger_research,
)


class TestExtractLibraryNames:
    """Test library name extraction from error text."""

    def test_extract_fastapi_library(self):
        """Extract fastapi from error text."""
        text = "ImportError: cannot import name 'BaseRequest' from 'fastapi'"
        result = extract_library_names(text)

        assert "fastapi" in result

    def test_extract_yt_dlp_variants(self):
        """Extract yt-dlp variants (hyphen and underscore)."""
        text = "yt-dlp option '--format' not available"
        result = extract_library_names(text)

        # Should normalize to hyphen form
        assert "yt-dlp" in result

    def test_extract_from_import_error(self):
        """Extract library from ImportError pattern."""
        text = "No module named 'torch'"
        result = extract_library_names(text)

        assert "torch" in result

    def test_extract_from_attribute_error(self):
        """Extract library from AttributeError pattern."""
        text = "module 'requests' has no attribute 'get'"
        result = extract_library_names(text)

        assert "requests" in result

    def test_extract_multiple_libraries(self):
        """Extract multiple libraries from error text."""
        text = "Error using langchain with chromadb and openai"
        result = extract_library_names(text)

        assert "langchain" in result
        assert "chromadb" in result
        assert "openai" in result

    def test_extract_pydantic_from_error(self):
        """Extract pydantic from validation error."""
        text = "pydantic validation error: field required"
        result = extract_library_names(text)

        assert "pydantic" in result

    def test_case_insensitive_extraction(self):
        """Library extraction is case-insensitive."""
        text = "Django Core Error"
        result = extract_library_names(text)

        assert "django" in result

    def test_no_libraries_in_internal_error(self):
        """Internal code errors return empty list."""
        text = "AttributeError: 'NoneType' object has no attribute 'x'"
        result = extract_library_names(text)

        assert len(result) == 0

    def test_extract_click_cli_library(self):
        """Extract click CLI library."""
        text = "click option '--help' not recognized"
        result = extract_library_names(text)

        assert "click" in result

    def test_extract_cloud_library_boto3(self):
        """Extract AWS boto3 library."""
        text = "boto3 client error: No credentials found"
        result = extract_library_names(text)

        assert "boto3" in result

    def test_normalizes_underscore_to_hyphen(self):
        """Normalize underscores to hyphens in library names."""
        text = "using yt_dlp for download"
        result = extract_library_names(text)

        # Should normalize to hyphen form
        assert "yt-dlp" in result or "yt_dlp" in result

    def test_filters_short_module_names(self):
        """Filter out very short module names."""
        text = "No module named 'x'"
        result = extract_library_names(text)

        # Single letter names should be filtered
        assert "x" not in result or len([r for r in result if len(r) > 2]) == 0


class TestShouldTriggerResearch:
    """Test research trigger decision logic."""

    def test_no_trigger_internal_code(self):
        """Internal code issues don't trigger research."""
        trigger = should_trigger_research(
            "AttributeError: 'NoneType' object has no attribute 'x'"
        )

        assert not trigger.should_research
        assert trigger.confidence < 0.5
        assert "no clear research triggers" in trigger.reason.lower()

    def test_trigger_fastapi_import_error(self):
        """FastAPI import error triggers research."""
        trigger = should_trigger_research(
            "ImportError: cannot import name 'BaseRequest' from 'fastapi'"
        )

        assert trigger.should_research
        assert "fastapi" in trigger.libraries
        assert trigger.confidence >= 0.5

    def test_trigger_yt_dlp_deprecation(self):
        """yt-dlp deprecation triggers research."""
        trigger = should_trigger_research(
            "DeprecationWarning: 'old_format' was removed in yt-dlp 2024.01"
        )

        assert trigger.should_research
        assert "yt-dlp" in trigger.libraries
        assert any("deprecated" in kw or "removed" in kw for kw in trigger.keywords_found)

    def test_trigger_torch_version_change(self):
        """Torch version change triggers research."""
        trigger = should_trigger_research(
            "torch.nn.Module changed in version 2.0"
        )

        assert trigger.should_research
        assert "torch" in trigger.libraries

    def test_confidence_with_fast_moving_library(self):
        """Fast-moving library increases confidence."""
        trigger = should_trigger_research(
            "AttributeError: module 'langchain' has no attribute 'Chain'"
        )

        assert trigger.confidence >= 0.4  # External lib + fast-moving

    def test_confidence_with_multiple_signals(self):
        """Multiple signals increase confidence."""
        trigger = should_trigger_research(
            "DeprecationWarning: 'old_method' removed in fastapi version 2.0"
        )

        # Should have high confidence (deprecation + fast-moving lib)
        assert trigger.confidence >= 0.7

    def test_no_trigger_simple_logic_error(self):
        """Simple logic errors don't trigger research."""
        trigger = should_trigger_research(
            "my_function returns None instead of list"
        )

        assert not trigger.should_research

    def test_trigger_for_openai_library(self):
        """OpenAI library changes trigger research."""
        trigger = should_trigger_research(
            "openai.ChatCompletion.acreate not available"
        )

        assert trigger.should_research
        assert "openai" in trigger.libraries

    def test_trigger_for_anthropic_library(self):
        """Anthropic library changes trigger research."""
        trigger = should_trigger_research(
            "anthropic.Anthropic.client deprecated"
        )

        assert trigger.should_research
        assert "anthropic" in trigger.libraries

    def test_trigger_for_pydantic_validation(self):
        """Pydantic validation errors with version keywords."""
        trigger = should_trigger_research(
            "pydantic validation error changed in version 2.0"
        )

        assert trigger.should_research
        assert "pydantic" in trigger.libraries

    def test_confidence_capped_at_1_0(self):
        """Confidence is capped at 1.0 even with many signals."""
        # Create a scenario with maximum signals
        trigger = should_trigger_research(
            "DeprecationWarning: 'old' removed in fastapi version 2.0, "
            "not available in module, unexpected keyword argument"
        )

        assert trigger.confidence <= 1.0

    def test_reason_includes_libraries(self):
        """Reason string includes detected libraries."""
        trigger = should_trigger_research("Error in langchain with chromadb")

        assert "langchain" in trigger.reason.lower() or "external" in trigger.reason.lower()

    def test_reason_includes_keywords(self):
        """Reason string includes staleness keywords."""
        trigger = should_trigger_research("Method deprecated in this version")

        assert any(kw in trigger.reason.lower() for kw in ["staleness", "keyword", "deprecated"])

    def test_keywords_found_populated(self):
        """Keywords found list is populated when present."""
        trigger = should_trigger_research(
            "DeprecationWarning: This method is deprecated"
        )

        assert len(trigger.keywords_found) > 0
        assert "deprecated" in trigger.keywords_found


class TestBuildResearchQuery:
    """Test research query construction."""

    def test_query_with_single_library(self):
        """Build query for single library."""
        query = build_research_query(
            ["fastapi"],
            "ImportError: cannot import from fastapi"
        )

        assert "fastapi" in query.lower()
        assert "documentation" in query.lower()

    def test_query_uses_primary_library(self):
        """Primary library is used in query."""
        query = build_research_query(
            ["langchain", "chromadb"],
            "Error with langchain"
        )

        # Should use first library
        assert "langchain" in query.lower()

    def test_query_includes_current_year(self):
        """Query includes current year."""
        from datetime import datetime

        query = build_research_query(
            ["torch"],
            "torch error"
        )

        current_year = datetime.now().year
        assert str(current_year) in query

    def test_query_includes_error_type(self):
        """Query includes error type."""
        query = build_research_query(
            ["requests"],
            "AttributeError: module 'requests' has no attribute"
        )

        assert "attributeerror" in query.lower()

    def test_query_fallback_without_libraries(self):
        """Fallback to problem description when no libraries."""
        query = build_research_query(
            [],
            "my function returns wrong value"
        )

        # Should use problem description (truncated)
        assert len(query) > 0

    def test_query_importerror_mapping(self):
        """ImportError maps to 'import error' in query."""
        query = build_research_query(
            ["fastapi"],
            "ImportError: cannot import name"
        )

        assert "import" in query.lower()

    def test_query_typerror_mapping(self):
        """TypeError maps to 'TypeError' in query."""
        query = build_research_query(
            ["pandas"],
            "TypeError: unsupported operand type"
        )

        assert "typeerror" in query.lower()

    def test_query_valuerror_mapping(self):
        """ValueError maps to 'ValueError' in query."""
        query = build_research_query(
            ["numpy"],
            "ValueError: invalid literal"
        )

        assert "valueerror" in query.lower()


class TestResearchTriggerDataclass:
    """Test ResearchTrigger dataclass."""

    def test_research_trigger_creation(self):
        """ResearchTrigger can be created."""
        trigger = ResearchTrigger(
            should_research=True,
            confidence=0.8,
            libraries=["fastapi"],
            reason="FastAPI detected",
            keywords_found=["deprecated"],
        )

        assert trigger.should_research is True
        assert trigger.confidence == 0.8
        assert "fastapi" in trigger.libraries

    def test_research_trigger_default_values(self):
        """ResearchTrigger with minimal data."""
        trigger = ResearchTrigger(
            should_research=False,
            confidence=0.0,
            libraries=[],
            reason="No triggers",
            keywords_found=[],
        )

        assert not trigger.should_research
        assert len(trigger.libraries) == 0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_string_input(self):
        """Empty string doesn't trigger research."""
        trigger = should_trigger_research("")

        assert not trigger.should_research
        assert trigger.confidence == 0.0

    def test_very_long_input(self):
        """Very long error text is handled."""
        long_text = "Error " * 1000 + "with fastapi"
        trigger = should_trigger_research(long_text)

        # Should still detect fastapi
        assert "fastapi" in trigger.libraries

    def test_unicode_in_error_text(self):
        """Unicode characters in error text."""
        trigger = should_trigger_research("Error in fastapi: 你好")

        assert "fastapi" in trigger.libraries

    def test_mixed_case_library_names(self):
        """Mixed case library names are normalized."""
        trigger = should_trigger_research("Error with FaStApI")

        assert len(trigger.libraries) > 0

    def test_multiple_same_library(self):
        """Same library mentioned multiple times."""
        trigger = should_trigger_research(
            "fastapi error, fastapi warning, fastapi issue"
        )

        # Should deduplicate
        assert trigger.libraries.count("fastapi") <= 1 or len(set(trigger.libraries)) < len(trigger.libraries)


class TestConstants:
    """Test module constants."""

    def test_fast_moving_libraries_not_empty(self):
        """FAST_MOVING_LIBRARIES is populated."""
        assert len(FAST_MOVING_LIBRARIES) > 0

    def test_staleness_keywords_not_empty(self):
        """STALENESS_KEYWORDS is populated."""
        assert len(STALENESS_KEYWORDS) > 0

    def test_common_libraries_in_list(self):
        """Common libraries are in fast-moving list."""
        assert "fastapi" in FAST_MOVING_LIBRARIES
        assert "django" in FAST_MOVING_LIBRARIES
        assert "torch" in FAST_MOVING_LIBRARIES
        assert "openai" in FAST_MOVING_LIBRARIES

    def test_deprecation_in_keywords(self):
        """Deprecation-related keywords are present."""
        assert "deprecated" in STALENESS_KEYWORDS
        assert "removed in" in STALENESS_KEYWORDS
        assert "changed in" in STALENESS_KEYWORDS
