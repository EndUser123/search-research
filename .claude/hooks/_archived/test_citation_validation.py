"""Tests for citation validation hook (StopHook_cite_evidence.py).

TDD RED phase - tests must fail before implementation.

This hook enforces that claims about code behavior include proper citations.
"""

import sys
from pathlib import Path

# Add hooks to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import from the actual implementation
from StopHook_cite_evidence import check_citation


class TestClaimPatternDetection:
    """Tests for claim pattern detection."""

    def test_detects_function_behavior_claim(self):
        """Should detect claims about function behavior."""
        response = "The validate function processes user input."
        patterns = check_citation(response)
        assert patterns["has_claim"] is True
        # Check that we matched a pattern (matched_patterns contains regex, not just word)
        assert len(patterns.get("matched_patterns", [])) > 0

    def test_detects_module_behavior_claim(self):
        """Should detect claims about module behavior."""
        response = "This module handles authentication."
        patterns = check_citation(response, patterns_only=True)
        assert patterns["has_claim"] is True

    def test_detects_class_behavior_claim(self):
        """Should detect claims about class behavior."""
        response = "The RequestHandler class routes incoming requests."
        patterns = check_citation(response, patterns_only=True)
        assert patterns["has_claim"] is True

    def test_detects_file_reference_claim(self):
        """Should detect claims with file extensions."""
        # Pattern expects filename directly followed by verb (no "file" in between)
        response = "config.py loads settings from environment variables."
        patterns = check_citation(response, patterns_only=True)
        assert patterns["has_claim"] is True

    def test_ignores_questions(self):
        """Should not flag questions as claims."""
        response = "How does the handler process requests?"
        patterns = check_citation(response, patterns_only=True)
        assert patterns["has_claim"] is False

    def test_ignores_hedged_claims(self):
        """Should not flag hedged statements as claims requiring citation."""
        response = "The module might process requests, or it could delegate."
        patterns = check_citation(response, patterns_only=True)
        assert patterns["has_claim"] is False

    def test_ignores_meta_statements(self):
        """Should not flag meta-comments about investigation."""
        response = "Let me check the handler to see how it processes requests."
        patterns = check_citation(response, patterns_only=True)
        assert patterns["has_claim"] is False


class TestCitationDetection:
    """Tests for citation extraction and validation."""

    def test_detects_file_line_citation(self):
        """Should detect standard file:line citations."""
        response = "The handler processes requests (handler.py:45)."
        result = check_citation(response)
        assert result["has_citation"] is True
        assert result["citations"][0]["file"] == "handler.py"
        assert result["citations"][0]["line"] == "45"

    def test_detects_file_citation_without_line(self):
        """Should detect file-only citations (less ideal but still citation)."""
        response = "As shown in handler.py, the process handles routing."
        result = check_citation(response)
        assert result["has_citation"] is True

    def test_detects_per_citation_format(self):
        """Should detect 'Per file:line' format from constitution."""
        response = "Per handler.py:45, the process routes requests."
        result = check_citation(response)
        assert result["has_citation"] is True

    def test_detects_according_to_format(self):
        """Should detect 'According to file' citations."""
        response = "According to auth.py:123, validation occurs first."
        result = check_citation(response)
        assert result["has_citation"] is True

    def test_rejects_fake_evidence_markers(self):
        """Should NOT accept vague evidence markers without specific files."""
        response = "The handler processes requests. According to the code, it works."
        result = check_citation(response)
        assert result["has_citation"] is False
        # Should still detect claim
        assert result["has_claim"] is True

    def test_rejects_ambiguous_references(self):
        """Should NOT accept ambiguous references like 'the file' or 'the output'."""
        response = "The handler processes requests. The file shows this."
        result = check_citation(response)
        assert result["has_citation"] is False


class TestValidationLogic:
    """Tests for the main validation decision."""

    def test_claim_with_citation_passes(self):
        """Should PASS when claim has proper citation."""
        response = "The handler processes requests (handler.py:45)."
        result = check_citation(response)
        assert result["valid"] is True
        assert result["reason"] == "has_citation"

    def test_claim_without_citation_blocks(self):
        """Should BLOCK when claim has no citation."""
        response = "The handler processes requests efficiently."
        result = check_citation(response)
        assert result["valid"] is False
        assert result["reason"] == "claim_without_citation"

    def test_no_claim_passes(self):
        """Should PASS when no claim detected."""
        response = "I'll read the handler to understand how it works."
        result = check_citation(response)
        assert result["valid"] is True
        assert result["reason"] == "no_claim"

    def test_short_responses_pass(self):
        """Should PASS trivial short responses."""
        for short in ["OK", "Done", "Yes", "No", ""]:
            result = check_citation(short)
            assert result["valid"] is True

    def test_code_block_without_citation_blocks(self):
        """Should BLOCK code explanations without file references."""
        response = "The handler function processes requests."
        result = check_citation(response)
        # Has claim ("processes") but no citation
        assert result["has_claim"] is True
        assert result["has_citation"] is False
        assert result["valid"] is False


class TestErrorHandling:
    """Tests for robustness and edge cases."""

    def test_empty_response(self):
        """Should handle empty response gracefully."""
        result = check_citation("")
        assert result["valid"] is True

    def test_unicode_characters(self):
        """Should handle unicode in responses."""
        response = "The handler processes requests with emoji support."
        result = check_citation(response)
        assert result["valid"] is False  # Claim without citation

    def test_very_long_response(self):
        """Should handle long responses without performance issues."""
        long_text = "The handler processes requests. " * 1000
        result = check_citation(long_text)
        assert result["has_claim"] is True
        assert result["valid"] is False

    def test_multiple_citations(self):
        """Should detect multiple citations in one response."""
        response = "Handler A (auth.py:10) and Handler B (route.py:45) both process."
        result = check_citation(response)
        assert result["has_citation"] is True
        assert len(result["citations"]) >= 2


class TestWindowsCompatibility:
    """Tests for Windows path handling."""

    def test_windows_backslash_paths(self):
        """Should detect Windows-style paths."""
        response = "The code in handlers\\auth.py:45 processes requests."
        result = check_citation(response)
        assert result["has_citation"] is True

    def test_mixed_slash_paths(self):
        """Should detect mixed slash paths."""
        response = "See src/handlers\\auth.py:45 for details."
        result = check_citation(response)
        assert result["has_citation"] is True


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
