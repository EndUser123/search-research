"""Tests for cognitive_mode_selector module.

Tests for cognitive mode detection and selection.
"""

import pytest

from rca.cognitive_mode_selector import (
    CognitiveMode,
    CognitiveModeSelector,
    TaskComplexity,
)


class TestCognitiveMode:
    """Test CognitiveMode enum."""

    def test_mode_values(self):
        """CognitiveMode has expected values."""
        assert CognitiveMode.ANALYTICAL.value == "analytical"
        assert CognitiveMode.INTUITIVE.value == "intuitive"
        assert CognitiveMode.HYBRID.value == "hybrid"


class TestTaskComplexity:
    """Test TaskComplexity enum."""

    def test_complexity_values(self):
        """TaskComplexity has expected values."""
        assert TaskComplexity.LOW.value == "low"
        assert TaskComplexity.MEDIUM.value == "medium"
        assert TaskComplexity.HIGH.value == "high"


class TestCognitiveModeSelectorInit:
    """Test CognitiveModeSelector initialization."""

    def test_selector_creation(self):
        """CognitiveModeSelector can be created."""
        selector = CognitiveModeSelector()

        assert selector is not None


class TestSelectMode:
    """Test mode selection."""

    def test_select_for_low_complexity(self):
        """Low complexity tasks use intuitive mode."""
        selector = CognitiveModeSelector()

        mode = selector.select_mode(complexity=TaskComplexity.LOW)

        assert mode == CognitiveMode.INTUITIVE

    def test_select_for_high_complexity(self):
        """High complexity tasks use analytical mode."""
        selector = CognitiveModeSelector()

        mode = selector.select_mode(complexity=TaskComplexity.HIGH)

        assert mode == CognitiveMode.ANALYTICAL

    def test_select_for_medium_complexity(self):
        """Medium complexity tasks use hybrid mode."""
        selector = CognitiveModeSelector()

        mode = selector.select_mode(complexity=TaskComplexity.MEDIUM)

        assert mode == CognitiveMode.HYBRID


class TestAssessComplexity:
    """Test complexity assessment."""

    def test_assess_simple_error(self):
        """Simple error is low complexity."""
        selector = CognitiveModeSelector()

        complexity = selector.assess_complexity(
            error_type="SyntaxError",
            stack_trace_lines=3,
            files_involved=1,
        )

        assert complexity == TaskComplexity.LOW

    def test_assess_complex_error(self):
        """Complex error is high complexity."""
        selector = CognitiveModeSelector()

        complexity = selector.assess_complexity(
            error_type="RaceCondition",
            stack_trace_lines=50,
            files_involved=10,
        )

        assert complexity == TaskComplexity.HIGH

    def test_assess_medium_error(self):
        """Medium complexity error."""
        selector = CognitiveModeSelector()

        complexity = selector.assess_complexity(
            error_type="AttributeError",
            stack_trace_lines=10,
            files_involved=3,
        )

        assert complexity in (TaskComplexity.LOW, TaskComplexity.MEDIUM)


class TestGetModeDescription:
    """Test mode description retrieval."""

    def test_analytical_description(self):
        """Analytical mode has description."""
        selector = CognitiveModeSelector()

        description = selector.get_mode_description(CognitiveMode.ANALYTICAL)

        assert description is not None
        assert len(description) > 0

    def test_intuitive_description(self):
        """Intuitive mode has description."""
        selector = CognitiveModeSelector()

        description = selector.get_mode_description(CognitiveMode.INTUITIVE)

        assert description is not None
        assert len(description) > 0


class TestEdgeCases:
    """Test edge cases."""

    def test_zero_stack_trace_lines(self):
        """Zero stack trace lines is handled."""
        selector = CognitiveModeSelector()

        complexity = selector.assess_complexity(
            error_type="Error",
            stack_trace_lines=0,
            files_involved=0,
        )

        assert complexity == TaskComplexity.LOW

    def test_very_large_stack_trace(self):
        """Very large stack trace is handled."""
        selector = CognitiveModeSelector()

        complexity = selector.assess_complexity(
            error_type="Error",
            stack_trace_lines=1000,
            files_involved=100,
        )

        assert complexity == TaskComplexity.HIGH

    def test_unknown_error_type(self):
        """Unknown error type defaults to medium complexity."""
        selector = CognitiveModeSelector()

        complexity = selector.assess_complexity(
            error_type="UnknownError",
            stack_trace_lines=5,
            files_involved=2,
        )

        assert complexity in (TaskComplexity.LOW, TaskComplexity.MEDIUM, TaskComplexity.HIGH)
