"""Tests for flow_visualizer module.

Tests visualization generation for action graphs.

Author: CSF Development Team
Task: #986
"""

import pytest

from rca.action_tracer import (
    Action,
    ActionGraph,
    ActionType,
)
from rca.flow_visualizer import (
    FlowVisualizer,
    VisualizationConfig,
    create_visualizer,
)


@pytest.fixture
def sample_graph():
    """Create a sample action graph for testing."""
    actions = [
        Action(
            action_id="act_001",
            action_type=ActionType.SEARCH_HISTORY,
            timestamp="2026-02-16T12:00:00",
            tool_used="Skill",
            tool_input={"skill": "search"},
            tool_output_hash="hash1",
            tool_output_preview="Found similar issues",
            phase=-1,
            session_id="rca_test",
            terminal_id="term_001",
        ),
        Action(
            action_id="act_002",
            action_type=ActionType.READ_FILE,
            timestamp="2026-02-16T12:00:30",
            tool_used="Read",
            tool_input={"file_path": "error.log"},
            tool_output_hash="hash2",
            tool_output_preview="[ERROR] ...",
            phase=0,
            parent_action_id="act_001",
            session_id="rca_test",
            terminal_id="term_001",
        ),
        Action(
            action_id="act_003",
            action_type=ActionType.TRACE_SYMBOL,
            timestamp="2026-02-16T12:01:00",
            tool_used="Serena",
            tool_input={"name_path": "MyClass"},
            tool_output_hash="hash3",
            tool_output_preview="Found 3 references",
            phase=1,
            parent_action_id="act_002",
            session_id="rca_test",
            terminal_id="term_001",
        ),
    ]

    return ActionGraph(
        session_id="rca_test",
        actions=actions,
        divergence_point=None,
        expected_path_type="error",
        created_at="2026-02-16T12:00:00",
        updated_at="2026-02-16T12:01:00",
    )


@pytest.fixture
def divergence_graph():
    """Create a graph with a divergence point."""
    actions = [
        Action(
            action_id="act_001",
            action_type=ActionType.SEARCH_HISTORY,
            timestamp="2026-02-16T12:00:00",
            tool_used="Skill",
            tool_input={},
            tool_output_hash="h1",
            tool_output_preview="",
            phase=-1,
            session_id="rca_test",
            terminal_id="term_001",
        ),
        Action(
            action_id="act_002",
            action_type=ActionType.LIST_DIR,  # Unexpected: should be READ_FILE
            timestamp="2026-02-16T12:00:30",
            tool_used="Glob",
            tool_input={},
            tool_output_hash="h2",
            tool_output_preview="",
            phase=0,
            parent_action_id="act_001",
            session_id="rca_test",
            terminal_id="term_001",
        ),
    ]

    return ActionGraph(
        session_id="rca_test",
        actions=actions,
        divergence_point=actions[1],  # Divergence at act_002
        expected_path_type="error",
        created_at="2026-02-16T12:00:00",
        updated_at="2026-02-16T12:00:30",
    )


class TestFlowVisualizer:
    """Test FlowVisualizer class."""

    def test_render_mermaid(self, sample_graph):
        """Mermaid diagram is generated correctly."""
        viz = FlowVisualizer()
        output = viz.render_mermaid(sample_graph)

        assert "graph TD" in output
        assert "A0" in output
        assert "A1" in output
        assert "A2" in output
        assert "-->" in output  # Edges

    def test_render_mermaid_with_divergence(self, divergence_graph):
        """Divergence is highlighted in Mermaid output."""
        config = VisualizationConfig(highlight_divergence=True)
        viz = FlowVisualizer()
        output = viz.render_mermaid(divergence_graph, config)

        assert "divergence" in output
        assert "stroke:#ff0000" in output  # Red highlight

    def test_render_text(self, sample_graph):
        """Text rendering produces ASCII art."""
        viz = FlowVisualizer()
        output = viz.render_text(sample_graph)

        assert "Action Flow:" in output
        assert "rca_test" in output
        assert "Total actions: 3" in output
        assert "search_history" in output.lower()

    def test_render_text_with_timestamps(self, sample_graph):
        """Timestamps can be included in text output."""
        config = VisualizationConfig(show_timestamps=True)
        viz = FlowVisualizer()
        output = viz.render_text(sample_graph, config)

        # Check for time format HH:MM:SS
        assert "12:00:" in output

    def test_render_text_without_tool_names(self, sample_graph):
        """Tool names can be excluded."""
        config = VisualizationConfig(show_tool_names=False)
        viz = FlowVisualizer()
        output = viz.render_text(sample_graph, config)

        # Should still have action types
        assert "search_history" in output.lower()

    def test_highlight_divergence_no_divergence(self, sample_graph):
        """Report shows no divergence when path matches."""
        viz = FlowVisualizer()
        output = viz.highlight_divergence(sample_graph, [
            ActionType.SEARCH_HISTORY,
            ActionType.READ_FILE,
            ActionType.TRACE_SYMBOL,
        ])

        assert "No divergence detected" in output

    def test_highlight_divergence_with_divergence(self, divergence_graph):
        """Report shows divergence details."""
        viz = FlowVisualizer()
        output = viz.highlight_divergence(divergence_graph, [
            ActionType.SEARCH_HISTORY,
            ActionType.READ_FILE,  # Expected but got LIST_DIR
        ])

        assert "First divergence" in output
        assert "list_dir" in output

    def test_render_statistics(self, sample_graph):
        """Statistics are calculated correctly."""
        viz = FlowVisualizer()
        output = viz.render_statistics(sample_graph)

        assert "Action Statistics" in output
        assert "Action Type Distribution" in output
        assert "Phase Distribution" in output
        assert "Time Span" in output

    def test_type_labels_coverage(self):
        """All ActionTypes have display labels."""
        viz = FlowVisualizer()

        for action_type in ActionType:
            label = viz.TYPE_LABELS.get(action_type)
            assert label is not None, f"Missing label for {action_type}"
            assert isinstance(label, str)

    def test_type_colors_coverage(self):
        """All ActionTypes have display colors."""
        viz = FlowVisualizer()

        for action_type in ActionType:
            color = viz.TYPE_COLORS.get(action_type)
            assert color is not None, f"Missing color for {action_type}"
            assert color.startswith("#")


class TestVisualizationConfig:
    """Test VisualizationConfig dataclass."""

    def test_default_config(self):
        """Default configuration values."""
        config = VisualizationConfig()

        assert config.show_timestamps is False
        assert config.show_tool_names is True
        assert config.show_phase is True
        assert config.highlight_divergence is True
        assert config.max_depth == 50

    def test_custom_config(self):
        """Configuration can be customized."""
        config = VisualizationConfig(
            show_timestamps=True,
            show_tool_names=False,
            max_depth=10,
        )

        assert config.show_timestamps is True
        assert config.show_tool_names is False
        assert config.max_depth == 10


class TestCreateHelper:
    """Test convenience helper."""

    def test_create_visualizer(self):
        """Helper creates configured visualizer."""
        viz = create_visualizer()

        assert isinstance(viz, FlowVisualizer)
