"""
Test suite for dreaming insights schema module (T-006).

These tests follow RED-GREEN-REFACTOR TDD cycle:
- RED: Tests fail initially (no implementation)
- GREEN: Minimal implementation to pass tests
- REFACTOR: Improve code quality while tests pass

Module: dreaming_insights.py

Requirements from plan T-006:
- Define PrincipleStats dataclass
- Define Pattern dataclass
- Define DreamingInsights dataclass
- Implement to_markdown() -> str method
- Use dataclasses.asdict() for JSON serialization
- All fields have type hints

Acceptance criteria:
1. JSON output validates against schema
2. Markdown output is human-readable
3. All fields have type hints

Run with: pytest P:/.claude/hooks/tests/test_dreaming_insights.py -v
"""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import module to test (will fail until implementation exists)
try:
    from dreaming_insights import DreamingInsights, Pattern, PrincipleStats
    MODULE_EXISTS = True
except ImportError:
    MODULE_EXISTS = False


class TestPrincipleStatsDataclass:
    """Test PrincipleStats dataclass structure and behavior."""

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_principle_stats_is_dataclass(self) -> None:
        """
        Test that PrincipleStats is a dataclass.

        Given: dreaming_insights module is imported
        When: Checking PrincipleStats type
        Then: PrincipleStats is a dataclass with correct fields
        """
        from dataclasses import is_dataclass

        assert is_dataclass(PrincipleStats)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_principle_stats_has_required_fields(self) -> None:
        """
        Test that PrincipleStats has required fields.

        Given: PrincipleStats dataclass
        When: Creating instance
        Then: Has fields: principle, count, first_seen, last_seen
        """
        stats = PrincipleStats(
            principle="test_principle",
            count=5,
            first_seen="2025-03-07T10:00:00",
            last_seen="2025-03-07T11:00:00"
        )

        assert hasattr(stats, 'principle')
        assert hasattr(stats, 'count')
        assert hasattr(stats, 'first_seen')
        assert hasattr(stats, 'last_seen')

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_principle_stats_field_types(self) -> None:
        """
        Test that PrincipleStats fields have correct types.

        Given: PrincipleStats instance
        When: Accessing fields
        Then: Fields have correct types (str, int, str, str)
        """
        stats = PrincipleStats(
            principle="test_principle",
            count=5,
            first_seen="2025-03-07T10:00:00",
            last_seen="2025-03-07T11:00:00"
        )

        assert isinstance(stats.principle, str)
        assert isinstance(stats.count, int)
        assert isinstance(stats.first_seen, str)
        assert isinstance(stats.last_seen, str)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_principle_stats_serializable_to_dict(self) -> None:
        """
        Test that PrincipleStats can be serialized to dict.

        Given: PrincipleStats instance
        When: Using dataclasses.asdict()
        Then: Returns dict with all fields
        """
        from dataclasses import asdict

        stats = PrincipleStats(
            principle="test_principle",
            count=5,
            first_seen="2025-03-07T10:00:00",
            last_seen="2025-03-07T11:00:00"
        )

        stats_dict = asdict(stats)

        assert isinstance(stats_dict, dict)
        assert stats_dict["principle"] == "test_principle"
        assert stats_dict["count"] == 5
        assert stats_dict["first_seen"] == "2025-03-07T10:00:00"
        assert stats_dict["last_seen"] == "2025-03-07T11:00:00"


class TestPatternDataclass:
    """Test Pattern dataclass structure and behavior."""

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_pattern_is_dataclass(self) -> None:
        """
        Test that Pattern is a dataclass.

        Given: dreaming_insights module is imported
        When: Checking Pattern type
        Then: Pattern is a dataclass with correct fields
        """
        from dataclasses import is_dataclass

        assert is_dataclass(Pattern)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_pattern_has_required_fields(self) -> None:
        """
        Test that Pattern has required fields.

        Given: Pattern dataclass
        When: Creating instance
        Then: Has fields: pattern_type, description, examples
        """
        pattern = Pattern(
            pattern_type="test_pattern",
            description="A test pattern",
            examples=["example1", "example2"]
        )

        assert hasattr(pattern, 'pattern_type')
        assert hasattr(pattern, 'description')
        assert hasattr(pattern, 'examples')

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_pattern_field_types(self) -> None:
        """
        Test that Pattern fields have correct types.

        Given: Pattern instance
        When: Accessing fields
        Then: Fields have correct types (str, str, list)
        """
        pattern = Pattern(
            pattern_type="test_pattern",
            description="A test pattern",
            examples=["example1", "example2"]
        )

        assert isinstance(pattern.pattern_type, str)
        assert isinstance(pattern.description, str)
        assert isinstance(pattern.examples, list)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_pattern_serializable_to_dict(self) -> None:
        """
        Test that Pattern can be serialized to dict.

        Given: Pattern instance
        When: Using dataclasses.asdict()
        Then: Returns dict with all fields
        """
        from dataclasses import asdict

        pattern = Pattern(
            pattern_type="test_pattern",
            description="A test pattern",
            examples=["example1", "example2"]
        )

        pattern_dict = asdict(pattern)

        assert isinstance(pattern_dict, dict)
        assert pattern_dict["pattern_type"] == "test_pattern"
        assert pattern_dict["description"] == "A test pattern"
        assert pattern_dict["examples"] == ["example1", "example2"]


class TestDreamingInsightsDataclass:
    """Test DreamingInsights dataclass structure and behavior."""

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_dreaming_insights_is_dataclass(self) -> None:
        """
        Test that DreamingInsights is a dataclass.

        Given: dreaming_insights module is imported
        When: Checking DreamingInsights type
        Then: DreamingInsights is a dataclass with correct fields
        """
        from dataclasses import is_dataclass

        assert is_dataclass(DreamingInsights)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_dreaming_insights_has_required_fields(self) -> None:
        """
        Test that DreamingInsights has required fields.

        Given: DreamingInsights dataclass
        When: Creating instance
        Then: Has fields: generated_at, total_events, principle_stats, patterns, recommendations
        """
        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=[],
            patterns=[],
            recommendations=[]
        )

        assert hasattr(insights, 'generated_at')
        assert hasattr(insights, 'total_events')
        assert hasattr(insights, 'principle_stats')
        assert hasattr(insights, 'patterns')
        assert hasattr(insights, 'recommendations')

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_dreaming_insights_field_types(self) -> None:
        """
        Test that DreamingInsights fields have correct types.

        Given: DreamingInsights instance
        When: Accessing fields
        Then: Fields have correct types (str, int, list, list, list)
        """
        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=[],
            patterns=[],
            recommendations=[]
        )

        assert isinstance(insights.generated_at, str)
        assert isinstance(insights.total_events, int)
        assert isinstance(insights.principle_stats, list)
        assert isinstance(insights.patterns, list)
        assert isinstance(insights.recommendations, list)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_dreaming_insights_with_nested_dataclasses(self) -> None:
        """
        Test DreamingInsights with nested PrincipleStats and Pattern.

        Given: DreamingInsights with nested data
        When: Creating instance with nested dataclasses
        Then: Nested data is preserved correctly
        """
        principle_stats = [
            PrincipleStats(
                principle="principle1",
                count=10,
                first_seen="2025-03-07T10:00:00",
                last_seen="2025-03-07T11:00:00"
            )
        ]

        patterns = [
            Pattern(
                pattern_type="pattern1",
                description="Test pattern",
                examples=["ex1", "ex2"]
            )
        ]

        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=principle_stats,
            patterns=patterns,
            recommendations=["rec1", "rec2"]
        )

        assert len(insights.principle_stats) == 1
        assert isinstance(insights.principle_stats[0], PrincipleStats)
        assert len(insights.patterns) == 1
        assert isinstance(insights.patterns[0], Pattern)
        assert len(insights.recommendations) == 2


class TestJSONSerialization:
    """Test JSON serialization of DreamingInsights."""

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_dreaming_insights_json_serializable(self) -> None:
        """
        Test that DreamingInsights can be serialized to JSON.

        Given: DreamingInsights instance with nested data
        When: Using dataclasses.asdict() and json.dumps()
        Then: Produces valid JSON string
        """
        from dataclasses import asdict

        principle_stats = [
            PrincipleStats(
                principle="principle1",
                count=10,
                first_seen="2025-03-07T10:00:00",
                last_seen="2025-03-07T11:00:00"
            )
        ]

        patterns = [
            Pattern(
                pattern_type="pattern1",
                description="Test pattern",
                examples=["ex1", "ex2"]
            )
        ]

        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=principle_stats,
            patterns=patterns,
            recommendations=["rec1", "rec2"]
        )

        # Convert to dict then JSON
        insights_dict = asdict(insights)
        json_str = json.dumps(insights_dict)

        # Verify JSON is valid
        assert isinstance(json_str, str)

        # Verify can deserialize
        loaded = json.loads(json_str)
        assert loaded["generated_at"] == "2025-03-07T12:00:00"
        assert loaded["total_events"] == 100
        assert len(loaded["principle_stats"]) == 1
        assert len(loaded["patterns"]) == 1
        assert len(loaded["recommendations"]) == 2

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_json_output_validates_schema(self) -> None:
        """
        Test that JSON output matches expected schema.

        Given: DreamingInsights instance
        When: Serialized to JSON
        Then: Output has all required keys and correct structure
        """
        from dataclasses import asdict

        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=50,
            principle_stats=[],
            patterns=[],
            recommendations=["Test recommendation"]
        )

        insights_dict = asdict(insights)

        # Verify required keys exist
        required_keys = ["generated_at", "total_events", "principle_stats", "patterns", "recommendations"]
        for key in required_keys:
            assert key in insights_dict

        # Verify data types
        assert isinstance(insights_dict["generated_at"], str)
        assert isinstance(insights_dict["total_events"], int)
        assert isinstance(insights_dict["principle_stats"], list)
        assert isinstance(insights_dict["patterns"], list)
        assert isinstance(insights_dict["recommendations"], list)


class TestMarkdownOutput:
    """Test to_markdown() method for human-readable output."""

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_to_markdown_method_exists(self) -> None:
        """
        Test that to_markdown() method exists.

        Given: DreamingInsights instance
        When: Checking for to_markdown method
        Then: Method exists and is callable
        """
        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=[],
            patterns=[],
            recommendations=[]
        )

        assert hasattr(insights, 'to_markdown')
        assert callable(insights.to_markdown)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_to_markdown_returns_string(self) -> None:
        """
        Test that to_markdown() returns string.

        Given: DreamingInsights instance
        When: Calling to_markdown()
        Then: Returns string
        """
        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=[],
            patterns=[],
            recommendations=[]
        )

        markdown = insights.to_markdown()

        assert isinstance(markdown, str)

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_to_markdown_contains_headers(self) -> None:
        """
        Test that to_markdown() contains section headers.

        Given: DreamingInsights with data
        When: Calling to_markdown()
        Then: Output contains expected markdown headers
        """
        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=[],
            patterns=[],
            recommendations=["Test recommendation"]
        )

        markdown = insights.to_markdown()

        # Check for common markdown headers
        assert "#" in markdown  # Has at least one header
        assert "Dreaming Insights" in markdown or "insights" in markdown.lower()

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_to_markdown_includes_principle_stats(self) -> None:
        """
        Test that to_markdown() includes principle stats.

        Given: DreamingInsights with principle_stats
        When: Calling to_markdown()
        Then: Output includes principle information
        """
        principle_stats = [
            PrincipleStats(
                principle="test_principle",
                count=5,
                first_seen="2025-03-07T10:00:00",
                last_seen="2025-03-07T11:00:00"
            )
        ]

        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=principle_stats,
            patterns=[],
            recommendations=[]
        )

        markdown = insights.to_markdown()

        # Should mention principle stats
        assert "principle" in markdown.lower() or "stat" in markdown.lower()

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_to_markdown_includes_patterns(self) -> None:
        """
        Test that to_markdown() includes patterns.

        Given: DreamingInsights with patterns
        When: Calling to_markdown()
        Then: Output includes pattern information
        """
        patterns = [
            Pattern(
                pattern_type="test_pattern",
                description="A test pattern",
                examples=["example1", "example2"]
            )
        ]

        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=[],
            patterns=patterns,
            recommendations=[]
        )

        markdown = insights.to_markdown()

        # Should mention patterns
        assert "pattern" in markdown.lower()

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_to_markdown_includes_recommendations(self) -> None:
        """
        Test that to_markdown() includes recommendations.

        Given: DreamingInsights with recommendations
        When: Calling to_markdown()
        Then: Output includes recommendations
        """
        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=[],
            patterns=[],
            recommendations=["Recommendation 1", "Recommendation 2"]
        )

        markdown = insights.to_markdown()

        # Should mention recommendations
        assert "recommendation" in markdown.lower()

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_to_markdown_is_human_readable(self) -> None:
        """
        Test that to_markdown() produces human-readable output.

        Given: DreamingInsights with full data
        When: Calling to_markdown()
        Then: Output is well-formatted and readable
        """
        principle_stats = [
            PrincipleStats(
                principle="test_principle",
                count=5,
                first_seen="2025-03-07T10:00:00",
                last_seen="2025-03-07T11:00:00"
            )
        ]

        patterns = [
            Pattern(
                pattern_type="test_pattern",
                description="A test pattern for testing",
                examples=["example1", "example2"]
            )
        ]

        insights = DreamingInsights(
            generated_at="2025-03-07T12:00:00",
            total_events=100,
            principle_stats=principle_stats,
            patterns=patterns,
            recommendations=["Test recommendation"]
        )

        markdown = insights.to_markdown()

        # Should have multiple lines (formatted)
        lines = markdown.strip().split("\n")
        assert len(lines) > 1

        # Should contain key data points
        assert "100" in markdown  # total_events
        assert "test_principle" in markdown or "principle" in markdown.lower()


class TestTypeHints:
    """Test that all fields have proper type hints."""

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_principle_stats_has_type_hints(self) -> None:
        """
        Test that PrincipleStats has type hints.

        Given: PrincipleStats dataclass
        When: Checking type annotations
        Then: All fields have type hints
        """
        # Check if dataclass has __annotations__
        assert hasattr(PrincipleStats, '__annotations__')

        annotations = PrincipleStats.__annotations__

        # Verify required fields have annotations
        assert 'principle' in annotations
        assert 'count' in annotations
        assert 'first_seen' in annotations
        assert 'last_seen' in annotations

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_pattern_has_type_hints(self) -> None:
        """
        Test that Pattern has type hints.

        Given: Pattern dataclass
        When: Checking type annotations
        Then: All fields have type hints
        """
        assert hasattr(Pattern, '__annotations__')

        annotations = Pattern.__annotations__

        assert 'pattern_type' in annotations
        assert 'description' in annotations
        assert 'examples' in annotations

    @pytest.mark.skipif(not MODULE_EXISTS, reason="dreaming_insights module not implemented yet")
    def test_dreaming_insights_has_type_hints(self) -> None:
        """
        Test that DreamingInsights has type hints.

        Given: DreamingInsights dataclass
        When: Checking type annotations
        Then: All fields have type hints
        """
        assert hasattr(DreamingInsights, '__annotations__')

        annotations = DreamingInsights.__annotations__

        assert 'generated_at' in annotations
        assert 'total_events' in annotations
        assert 'principle_stats' in annotations
        assert 'patterns' in annotations
        assert 'recommendations' in annotations


class TestGreenPhase:
    """Tests verifying implementation exists (GREEN phase complete)."""

    def test_module_exists(self) -> None:
        """Verify module exists and is importable."""
        try:
            from dreaming_insights import DreamingInsights, Pattern, PrincipleStats
            assert PrincipleStats is not None
            assert Pattern is not None
            assert DreamingInsights is not None
        except ImportError:
            pytest.fail("dreaming_insights module not implemented yet")

    def test_principle_stats_is_dataclass(self) -> None:
        """Verify PrincipleStats is a dataclass."""
        from dataclasses import is_dataclass
        try:
            from dreaming_insights import PrincipleStats
            assert is_dataclass(PrincipleStats)
        except ImportError:
            pytest.skip("dreaming_insights module not implemented yet")

    def test_pattern_is_dataclass(self) -> None:
        """Verify Pattern is a dataclass."""
        from dataclasses import is_dataclass
        try:
            from dreaming_insights import Pattern
            assert is_dataclass(Pattern)
        except ImportError:
            pytest.skip("dreaming_insights module not implemented yet")

    def test_dreaming_insights_is_dataclass(self) -> None:
        """Verify DreamingInsights is a dataclass."""
        from dataclasses import is_dataclass
        try:
            from dreaming_insights import DreamingInsights
            assert is_dataclass(DreamingInsights)
        except ImportError:
            pytest.skip("dreaming_insights module not implemented yet")

    def test_dreaming_insights_has_to_markdown(self) -> None:
        """Verify DreamingInsights has to_markdown method."""
        try:
            from dreaming_insights import DreamingInsights
            insights = DreamingInsights(
                generated_at="2025-03-07T12:00:00",
                total_events=100,
                principle_stats=[],
                patterns=[],
                recommendations=[]
            )
            assert hasattr(insights, 'to_markdown')
            assert callable(insights.to_markdown)
        except ImportError:
            pytest.skip("dreaming_insights module not implemented yet")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
