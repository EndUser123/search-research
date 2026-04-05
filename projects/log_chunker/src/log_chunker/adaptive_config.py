from typing import Any

from log_chunker.config import ChunkingConfig
from log_chunker.data_models import ContentAnalysis


class AdaptiveChunker:
    """Adaptive chunking configuration analyzer."""

    def analyze_and_recommend(
        self, config: ChunkingConfig, content: str
    ) -> tuple[dict[str, Any], ContentAnalysis]:
        """Analyze content and recommend configuration updates.

        Args:
            config: Current chunking configuration
            content: Sample content to analyze

        Returns:
            Tuple of (recommended_config_updates, analysis_object)
        """
        # Placeholder implementation - returns empty recommendations
        # and a basic analysis object
        return {}, ContentAnalysis(
            content_length=len(content),
            avg_line_length=len(content) / max(1, content.count("\n")),
            detected_patterns=[],
            recommended_config={},
        )


def print_log_message(console, message, location=""):
    """Print a formatted log message to the console."""
    if console:
        console.print(f"[{location}] {message}" if location else message)
    else:
        print(message)
    pass


def _merge_configs(base_config, override_config):
    """Merge configuration with override values."""
    # Convert ChunkingConfig to dict if needed
    if hasattr(base_config, "model_dump"):
        # Pydantic model
        base_dict = base_config.model_dump()
    elif hasattr(base_config, "__dict__"):
        # Dataclass or object with attributes
        base_dict = {
            k: v for k, v in base_config.__dict__.items() if not k.startswith("_")
        }
    else:
        # Already a dict
        base_dict = base_config

    # Merge override config
    if isinstance(override_config, dict):
        merged_dict = {**base_dict, **override_config}
    else:
        merged_dict = base_dict

    # Return the same type as the input
    if hasattr(base_config, "model_validate"):
        # Pydantic model
        return base_config.__class__.model_validate(merged_dict)
    elif hasattr(base_config, "__class__") and hasattr(
        base_config.__class__, "__annotations__"
    ):
        # Dataclass
        return base_config.__class__(**merged_dict)
    else:
        # Dict
        return merged_dict


def display_analysis(analysis_data: ContentAnalysis, console=None) -> str:
    """Display analysis results with enhanced Rich formatting.

    Args:
        analysis_data: ContentAnalysis object with results
        console: Optional Rich console for enhanced display

    Returns:
        String representation of analysis results
    """
    if console:
        try:
            from rich.panel import Panel
            from rich.table import Table
            from rich.text import Text

            # Create analysis table
            analysis_table = Table(show_header=False, box=None, padding=(0, 1))
            analysis_table.add_column("Metric", style="cyan", width=25)
            analysis_table.add_column("Value", style="white")

            # Add analysis data
            analysis_table.add_row(
                "Content Length", f"{analysis_data.content_length:,} chars"
            )
            analysis_table.add_row(
                "Avg Line Length", f"{analysis_data.avg_line_length:.1f} chars"
            )
            analysis_table.add_row(
                "Detected Patterns", str(len(analysis_data.detected_patterns))
            )

            # Add pattern details if available
            if analysis_data.detected_patterns:
                analysis_table.add_row("", "")  # Separator
                analysis_table.add_row("[bold]Pattern Details:[/bold]", "")
                for i, pattern in enumerate(
                    analysis_data.detected_patterns[:5]
                ):  # Show first 5
                    analysis_table.add_row(f"  Pattern {i + 1}", pattern)

            # Add recommendations if available
            if analysis_data.recommended_config:
                analysis_table.add_row("", "")  # Separator
                analysis_table.add_row("[bold]Recommendations:[/bold]", "")
                for key, value in analysis_data.recommended_config.items():
                    analysis_table.add_row(f"  {key}", str(value))

            # Create panel with the table
            analysis_panel = Panel(
                analysis_table,
                title="[bold]Content Analysis Results[/bold]",
                border_style="cyan",
            )

            console.print(analysis_panel)
            return "Analysis displayed with Rich formatting"

        except ImportError:
            # Fallback to basic display if Rich not available
            pass

    # Basic string representation for fallback
    result = (
        f"Content Analysis Results:\n"
        f"- Content length: {analysis_data.content_length:,} chars\n"
        f"- Avg line length: {analysis_data.avg_line_length:.1f} chars\n"
        f"- Detected patterns: {len(analysis_data.detected_patterns)}"
    )

    if analysis_data.detected_patterns:
        result += "\n\nDetected Patterns:"
        for i, pattern in enumerate(analysis_data.detected_patterns[:5]):
            result += f"\n  {i + 1}. {pattern}"

    if analysis_data.recommended_config:
        result += "\n\nRecommended Configuration:"
        for key, value in analysis_data.recommended_config.items():
            result += f"\n  {key}: {value}"

    return result
