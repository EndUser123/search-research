"""Flow Visualizer for rca Action Graphs.

Generates visual representations of investigation paths as Mermaid diagrams,
ASCII art, or highlighted divergence views.

Author: CSF Development Team
Version: 1.0.0
Task: #986
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .action_tracer import Action, ActionGraph, ActionType


@dataclass
class VisualizationConfig:
    """Configuration for flow visualization."""

    show_timestamps: bool = False
    show_tool_names: bool = True
    show_phase: bool = True
    highlight_divergence: bool = True
    max_depth: int = 50  # Limit actions shown


class FlowVisualizer:
    """Generate visual representations of action flow.

    Supports multiple output formats:
    - Mermaid diagrams for rendering
    - ASCII art for terminal display
    - Divergence highlighting for RCA review

    Usage:
        >>> viz = FlowVisualizer()
        >>> mermaid = viz.render_mermaid(graph, config)
        >>> print(viz.render_text(graph))
        >>> print(viz.highlight_divergence(graph, divergence_point))
    """

    # Action type styling
    TYPE_COLORS = {
        ActionType.READ_FILE: "#90EE90",  # Light green
        ActionType.SEARCH_CODE: "#87CEEB",  # Sky blue
        ActionType.LIST_DIR: "#DDA0DD",  # Plum
        ActionType.TRACE_SYMBOL: "#FFD700",  # Gold
        ActionType.INSPECT_VARIABLE: "#FFA07A",  # Light salmon
        ActionType.EXECUTE_TEST: "#FFA500",  # Orange
        ActionType.FORM_HYPOTHESIS: "#FF69B4",  # Hot pink
        ActionType.VERIFY_HYPOTHESIS: "#32CD32",  # Lime green
        ActionType.ELIMINATE_CAUSE: "#FF6347",  # Tomato
        ActionType.SEARCH_HISTORY: "#E6E6FA",  # Lavender
        ActionType.FETCH_DOCS: "#F0E68C",  # Khaki
        ActionType.SYNTHESIZE: "#00CED1",  # Dark turquoise
        ActionType.RECORD_OUTCOME: "#DC143C",  # Crimson
        ActionType.UNKNOWN: "#D3D3D3",  # Light gray
    }

    TYPE_LABELS = {
        ActionType.READ_FILE: "[R] Read",
        ActionType.SEARCH_CODE: "[S] Search",
        ActionType.LIST_DIR: "[L] List",
        ActionType.TRACE_SYMBOL: "[T] Trace",
        ActionType.INSPECT_VARIABLE: "[I] Inspect",
        ActionType.EXECUTE_TEST: "[X] Test",
        ActionType.FORM_HYPOTHESIS: "[H] Hypothesis",
        ActionType.VERIFY_HYPOTHESIS: "[V] Verify",
        ActionType.ELIMINATE_CAUSE: "[E] Eliminate",
        ActionType.SEARCH_HISTORY: "[H] History",
        ActionType.FETCH_DOCS: "[D] Docs",
        ActionType.SYNTHESIZE: "[S] Synthesis",
        ActionType.RECORD_OUTCOME: "[O] Record",
        ActionType.UNKNOWN: "[?] Unknown",
    }

    def render_mermaid(
        self,
        graph: ActionGraph,
        config: VisualizationConfig | None = None,
    ) -> str:
        """Render action graph as Mermaid diagram.

        Args:
            graph: The ActionGraph to visualize
            config: Visualization options

        Returns:
            Mermaid diagram source code
        """
        config = config or VisualizationConfig()

        lines = [
            "graph TD",
            "    %% rca Action Flow",
            f'    %% Session: {graph.session_id}',
            "",
        ]

        # Track node IDs
        node_ids = {}
        for i, action in enumerate(graph.actions[: config.max_depth]):
            node_id = f"A{i}"
            node_ids[action.action_id] = node_id

            # Build label
            label = self._build_node_label(action, config)
            style = self._get_mermaid_style(node_id, action, config)

            lines.append(f"    {node_id}[\"{label}\"]")
            if style:
                lines.append(f"    {style}")

        # Add edges
        for i, action in enumerate(graph.actions[: config.max_depth]):
            if action.parent_action_id and action.parent_action_id in node_ids:
                parent_id = node_ids[action.parent_action_id]
                current_id = node_ids[action.action_id]
                lines.append(f"    {parent_id} --> {current_id}")

        # Add divergence highlight
        if config.highlight_divergence and graph.divergence_point:
            div_id = node_ids.get(graph.divergence_point.action_id)
            if div_id:
                lines.append("")
                lines.append(f"    class {div_id} divergence")
                lines.append("    classDef divergence stroke:#ff0000,stroke-width:3px")

        lines.append("")
        return "\n".join(lines)

    def _build_node_label(self, action: Action, config: VisualizationConfig) -> str:
        """Build HTML label for Mermaid node."""
        parts = [self.TYPE_LABELS.get(action.action_type, "❓")]

        if config.show_tool_names:
            parts.append(f"({action.tool_used})")

        if config.show_phase:
            parts.append(f"[P{action.phase}]")

        return " ".join(parts)

    def _get_mermaid_style(self, node_id: str, action: Action, config: VisualizationConfig) -> str | None:
        """Get Mermaid style definition for an action."""
        if not config.highlight_divergence:
            return None

        color = self.TYPE_COLORS.get(action.action_type, "#D3D3D3")
        return f"style {node_id} fill:{color}"

    def render_text(
        self,
        graph: ActionGraph,
        config: VisualizationConfig | None = None,
    ) -> str:
        """Render action graph as ASCII/Unicode art.

        Args:
            graph: The ActionGraph to visualize
            config: Visualization options

        Returns:
            ASCII art representation
        """
        config = config or VisualizationConfig()

        lines = [
            f"╔══ Action Flow: {graph.session_id}",
            "╠════════════════════════════════════════════════════",
            "",
        ]

        for i, action in enumerate(graph.actions[: config.max_depth]):
            # Indentation based on depth (simple linear)
            indent = "  " * i if i < 10 else "  " * 10

            # Action line
            icon = self.TYPE_LABELS.get(action.action_type, "❓").split()[0]

            line = f"{indent}{icon} {action.action_type.value}"

            if config.show_tool_names:
                line += f" via {action.tool_used}"

            if config.show_phase:
                line += f" [Phase {action.phase}]"

            lines.append(line)

            # Optional timestamp
            if config.show_timestamps:
                ts = action.timestamp.split("T")[1][:8]  # HH:MM:SS
                lines.append(f"{indent}   @ {ts}")

        lines.append("")
        lines.append(f"Total actions: {len(graph.actions)}")

        if graph.divergence_point:
            lines.append(f"⚠️  Divergence at: {graph.divergence_point.action_id}")

        return "\n".join(lines)

    def highlight_divergence(
        self,
        graph: ActionGraph,
        expected_path: list[ActionType] | None = None,
    ) -> str:
        """Generate comparison view showing where actual diverged from expected.

        Args:
            graph: The ActionGraph to analyze
            expected_path: Expected action types (optional, uses defaults if None)

        Returns:
            Formatted divergence report
        """
        if expected_path is None:
            # Use error path as default
            from .action_tracer import EXPECTED_PATHS
            expected_path = EXPECTED_PATHS.get("error", [])

        lines = [
            "╔══ Divergence Analysis",
            "╠════════════════════════════════════════════════════",
            "",
        ]

        # Build comparison
        actual_types = [a.action_type for a in graph.actions]

        lines.extend([
            "Expected vs. Actual:",
            "",
        ])

        max_len = max(len(expected_path), len(actual_types))

        divergence_found = False
        divergence_index = -1

        for i in range(max_len):
            expected = expected_path[i] if i < len(expected_path) else None
            actual = actual_types[i] if i < len(actual_types) else None

            if expected != actual:
                if not divergence_found:
                    divergence_index = i
                    divergence_found = True

                # Divergence line
                exp_str = expected.value if expected else "(end)"
                act_str = actual.value if actual else "(end)"

                lines.append(f"  {i:2d}. ❌ {exp_str:20s} → {act_str:20s} ← DIVERGENCE")
            else:
                # Match
                if expected:
                    lines.append(f"  {i:2d}. ✓  {expected.value:20s}")

        lines.append("")

        if divergence_found:
            lines.extend([
                f"📍 First divergence at index {divergence_index}",
                "",
            ])

            if graph.divergence_point:
                div = graph.divergence_point
                lines.extend([
                    "Diverging Action Details:",
                    f"  Type: {div.action_type.value}",
                    f"  Tool: {div.tool_used}",
                    f"  Phase: {div.phase}",
                    f"  Time: {div.timestamp}",
                    "",
                ])

                if div.tool_output_preview:
                    lines.extend([
                        "Output Preview:",
                        f"  {div.tool_output_preview[:200]}...",
                        "",
                    ])
        else:
            lines.extend([
                "✅ No divergence detected",
                "   Investigation followed expected path",
            ])

        return "\n".join(lines)

    def render_statistics(self, graph: ActionGraph) -> str:
        """Render statistics about the action graph.

        Args:
            graph: The ActionGraph to analyze

        Returns:
            Formatted statistics
        """
        lines = [
            "╔══ Action Statistics",
            "╠════════════════════════════════════════════════════",
            "",
        ]

        # Count by type
        type_counts = {}
        for action in graph.actions:
            at = action.action_type.value
            type_counts[at] = type_counts.get(at, 0) + 1

        lines.extend([
            "Action Type Distribution:",
            "",
        ])

        for action_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {action_type:20s}: {count:3d}")

        lines.append("")
        lines.append(f"Total Actions: {len(graph.actions)}")

        # Phase distribution
        phase_counts = {}
        for action in graph.actions:
            p = action.phase
            phase_counts[p] = phase_counts.get(p, 0) + 1

        lines.extend([
            "",
            "Phase Distribution:",
            "",
        ])

        for phase in sorted(phase_counts.keys()):
            lines.append(f"  Phase {phase}: {phase_counts[phase]} actions")

        lines.append("")

        # Time span
        if graph.actions:
            first_time = graph.actions[0].timestamp
            last_time = graph.actions[-1].timestamp
            lines.extend([
                "Time Span:",
                f"  Start: {first_time}",
                f"  End:   {last_time}",
                "",
            ])

        return "\n".join(lines)


def create_visualizer() -> FlowVisualizer:
    """Convenience function to create a FlowVisualizer.

    Returns:
        Configured FlowVisualizer instance
    """
    return FlowVisualizer()


# CLI integration helpers
def render_flow_from_session(
    session_id: str,
    format: str = "text",
) -> str:
    """Render action flow for a session.

    Args:
        session_id: RCA session identifier
        format: Output format (mermaid, text, stats)

    Returns:
        Rendered output
    """
    from .action_tracer import ActionTracer

    tracer = ActionTracer.load(session_id)
    graph = tracer.get_action_graph()

    viz = FlowVisualizer()

    if format == "mermaid":
        return viz.render_mermaid(graph)
    elif format == "stats":
        return viz.render_statistics(graph)
    else:
        return viz.render_text(graph)
