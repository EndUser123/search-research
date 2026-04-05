"""Tests for walkthrough_generator module.

Tests for RCA walkthrough generation and formatting.
"""

import pytest

from rca.walkthrough_generator import (
    WalkthroughGenerator,
    WalkthroughSection,
    WalkthroughStyle,
)


class TestWalkthroughStyle:
    """Test WalkthroughStyle enum."""

    def test_style_values(self):
        """WalkthroughStyle has expected values."""
        assert WalkthroughStyle.CONCISE.value == "concise"
        assert WalkthroughStyle.DETAILED.value == "detailed"
        assert WalkthroughStyle.TUTORIAL.value == "tutorial"


class TestWalkthroughSection:
    """Test WalkthroughSection dataclass."""

    def test_section_creation(self):
        """WalkthroughSection can be created."""
        section = WalkthroughSection(
            title="Problem Identification",
            content="Detected error in handler.py",
            order=1,
        )

        assert section.title == "Problem Identification"
        assert section.order == 1

    def test_section_with_evidence(self):
        """Section can include evidence references."""
        section = WalkthroughSection(
            title="Root Cause",
            content="Null pointer dereference",
            order=2,
            evidence_refs=["stack_trace_1", "log_entry_2"],
        )

        assert len(section.evidence_refs) == 2


class TestWalkthroughGeneratorInit:
    """Test WalkthroughGenerator initialization."""

    def test_generator_creation(self):
        """WalkthroughGenerator can be created."""
        generator = WalkthroughGenerator()

        assert generator is not None

    def test_generator_with_style(self):
        """Generator can be created with specific style."""
        generator = WalkthroughGenerator(style=WalkthroughStyle.DETAILED)

        assert generator.style == WalkthroughStyle.DETAILED


class TestGenerateWalkthrough:
    """Test walkthrough generation."""

    def test_generate_basic_walkthrough(self):
        """Basic walkthrough can be generated."""
        generator = WalkthroughGenerator()

        walkthrough = generator.generate(
            problem="Error in data processing",
            root_cause="Missing null check",
            fix="Added validation",
            steps=[
                "Read error logs",
                "Identified null pointer",
                "Added if check",
            ],
        )

        assert walkthrough is not None
        assert len(walkthrough.sections) > 0

    def test_walkthrough_includes_all_sections(self):
        """Walkthrough includes standard sections."""
        generator = WalkthroughGenerator()

        walkthrough = generator.generate(
            problem="Test problem",
            root_cause="Test cause",
            fix="Test fix",
            steps=["Step 1", "Step 2"],
        )

        titles = [s.title for s in walkthrough.sections]

        assert "Problem" in titles or "Issue" in titles
        assert "Root Cause" in titles or "Cause" in titles
        assert "Fix" in titles or "Resolution" in titles

    def test_detailed_walkthrough(self):
        """Detailed style includes more information."""
        generator = WalkthroughGenerator(style=WalkthroughStyle.DETAILED)

        walkthrough = generator.generate(
            problem="Test problem",
            root_cause="Test cause",
            fix="Test fix",
            steps=["Step 1"],
            evidence=["Log entry", "Stack trace"],
        )

        # Detailed walkthrough should have more sections
        assert len(walkthrough.sections) >= 3


class TestAddSection:
    """Test adding sections to walkthrough."""

    def test_add_custom_section(self):
        """Custom section can be added."""
        generator = WalkthroughGenerator()

        walkthrough = generator.generate(
            problem="Test",
            root_cause="Cause",
            fix="Fix",
            steps=["Step 1"],
        )

        generator.add_section(
            walkthrough,
            title="Lessons Learned",
            content="Always validate inputs",
            order=99,
        )

        titles = [s.title for s in walkthrough.sections]
        assert "Lessons Learned" in titles


class TestFormatWalkthrough:
    """Test walkthrough formatting."""

    def test_format_as_markdown(self):
        """Walkthrough can be formatted as markdown."""
        generator = WalkthroughGenerator()

        walkthrough = generator.generate(
            problem="Test problem",
            root_cause="Test cause",
            fix="Test fix",
            steps=["Step 1", "Step 2"],
        )

        markdown = generator.format_markdown(walkthrough)

        assert len(markdown) > 0
        assert "#" in markdown  # Markdown headers

    def test_format_as_text(self):
        """Walkthrough can be formatted as plain text."""
        generator = WalkthroughGenerator()

        walkthrough = generator.generate(
            problem="Test problem",
            root_cause="Test cause",
            fix="Test fix",
            steps=["Step 1"],
        )

        text = generator.format_text(walkthrough)

        assert len(text) > 0


class TestIncludeEvidence:
    """Test evidence inclusion in walkthrough."""

    def test_include_evidence_references(self):
        """Evidence can be included in walkthrough."""
        generator = WalkthroughGenerator()

        walkthrough = generator.generate(
            problem="Test problem",
            root_cause="Test cause",
            fix="Test fix",
            steps=["Step 1"],
            evidence=["Stack trace line 42", "Error log entry"],
        )

        # Check that evidence is mentioned
        content = " ".join([s.content for s in walkthrough.sections])

        assert "evidence" in content.lower() or "stack" in content.lower() or "log" in content.lower()


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_steps_list(self):
        """Empty steps list is handled."""
        generator = WalkthroughGenerator()

        walkthrough = generator.generate(
            problem="Test",
            root_cause="Cause",
            fix="Fix",
            steps=[],
        )

        assert walkthrough is not None

    def test_very_long_content(self):
        """Very long content is handled."""
        generator = WalkthroughGenerator()

        long_content = "Test content " * 1000

        walkthrough = generator.generate(
            problem=long_content,
            root_cause=long_content,
            fix=long_content,
            steps=["Step 1"],
        )

        assert walkthrough is not None

    def test_special_characters_in_content(self):
        """Special characters are handled."""
        generator = WalkthroughGenerator()

        walkthrough = generator.generate(
            problem="Error: <>&\"'",
            root_cause="Null @ # $ %",
            fix="Fix with * + - =",
            steps=["Step 1"],
        )

        assert walkthrough is not None
