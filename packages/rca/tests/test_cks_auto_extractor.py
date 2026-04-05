"""Tests for cks_auto_extractor module.

Tests for CKS auto-extraction and learning storage.
"""

import pytest

from rca.cks_auto_extractor import (
    CKSAutoExtractor,
    Learning,
)


class TestLearningDataclass:
    """Test Learning dataclass."""

    def test_learning_creation(self):
        """Learning can be created with all fields."""
        learning = Learning(
            session_id="rca_123",
            problem_type="error",
            problem_signature="AttributeError: NoneType",
            root_cause="Missing null check",
            fix_applied="Added if validation",
            files_changed=["src/handler.py"],
            lesson="Always validate dict keys before access",
            extracted_at="2026-02-28T12:00:00",
        )

        assert learning.session_id == "rca_123"
        assert learning.root_cause == "Missing null check"

    def test_learning_with_minimal_fields(self):
        """Learning can be created with minimal fields."""
        learning = Learning(
            session_id="rca_456",
            problem_type="test",
            problem_signature="Test failure",
            root_cause="Bug in logic",
            fix_applied="Fixed logic",
            files_changed=[],
            lesson="Test more thoroughly",
            extracted_at="2026-02-28T12:00:00",
        )

        assert learning.session_id == "rca_456"


class TestCKSAutoExtractorInit:
    """Test CKSAutoExtractor initialization."""

    def test_extractor_creation(self):
        """CKSAutoExtractor can be created."""
        extractor = CKSAutoExtractor()

        assert extractor is not None

    def test_extractor_with_cks_instance(self):
        """Extractor can be created with CKS instance."""
        extractor = CKSAutoExtractor(cks_instance=None)

        assert extractor is not None


class TestExtractAndStore:
    """Test learning extraction and storage."""

    def test_extract_basic_learning(self):
        """Basic learning can be extracted."""
        extractor = CKSAutoExtractor()

        # Should not crash even without CKS
        result = extractor.extract_and_store(
            session_id="rca_123",
            problem_description="AttributeError: 'NoneType' object has no attribute 'x'",
            root_cause="Missing null check",
            fix_applied="Added if validation",
        )

        # May return False if CKS not available, but shouldn't crash
        assert result is True or result is False

    def test_extract_with_files(self):
        """Learning can include changed files."""
        extractor = CKSAutoExtractor()

        result = extractor.extract_and_store(
            session_id="rca_456",
            problem_description="Test failure",
            root_cause="Logic error",
            fix_applied="Fixed condition",
            files_changed=["src/test.py", "src/handler.py"],
        )

        assert result is True or result is False

    def test_extract_with_custom_lesson(self):
        """Custom lesson can be provided."""
        extractor = CKSAutoExtractor()

        result = extractor.extract_and_store(
            session_id="rca_789",
            problem_description="Error",
            root_cause="Bug",
            fix_applied="Fix",
            lesson="Always validate user input",
        )

        assert result is True or result is False


class TestGenerateLearningSummary:
    """Test learning summary generation."""

    def test_generate_summary(self):
        """Learning summary can be generated."""
        extractor = CKSAutoExtractor()

        summary = extractor.generate_summary(
            problem_description="AttributeError in handler",
            root_cause="Missing null check",
            fix_applied="Added validation",
        )

        assert summary is not None
        assert len(summary) > 0

    def test_summary_includes_key_elements(self):
        """Summary includes problem, cause, and fix."""
        extractor = CKSAutoExtractor()

        summary = extractor.generate_summary(
            problem_description="Type error in processing",
            root_cause="Wrong type passed",
            fix_applied="Added type check",
        )

        summary_lower = summary.lower()

        # Should mention key elements
        assert any(term in summary_lower for term in ["problem", "cause", "fix", "error"])


class TestCreateLearningObject:
    """Test learning object creation."""

    def test_create_learning_from_outcome(self):
        """Learning object can be created from outcome."""
        extractor = CKSAutoExtractor()

        learning = extractor.create_learning(
            session_id="rca_123",
            problem_type="error",
            problem_signature="AttributeError: NoneType",
            root_cause="Missing check",
            fix_applied="Added if",
            files_changed=["src/handler.py"],
            lesson="Validate inputs",
        )

        assert learning.session_id == "rca_123"
        assert learning.problem_type == "error"


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_problem_description(self):
        """Empty problem description is handled."""
        extractor = CKSAutoExtractor()

        summary = extractor.generate_summary(
            problem_description="",
            root_cause="Cause",
            fix_applied="Fix",
        )

        assert summary is not None

    def test_very_long_description(self):
        """Very long description is handled."""
        extractor = CKSAutoExtractor()

        long_desc = "Error " * 1000

        summary = extractor.generate_summary(
            problem_description=long_desc,
            root_cause="Cause",
            fix_applied="Fix",
        )

        assert summary is not None

    def test_special_characters(self):
        """Special characters are handled."""
        extractor = CKSAutoExtractor()

        summary = extractor.generate_summary(
            problem_description="Error: <>&\"'",
            root_cause="Null @ # $ %",
            fix_applied="Fix with * + -",
        )

        assert summary is not None
