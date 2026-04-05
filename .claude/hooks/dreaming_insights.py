"""Dreaming insights schema module (T-006).

Defines dataclasses for dreaming daemon insights output:
- PrincipleStats: Statistics for principle violations
- Pattern: Detected patterns with examples
- DreamingInsights: Complete insights report with markdown rendering

Usage:
    from dreaming_insights import DreamingInsights, PrincipleStats, Pattern

    insights = DreamingInsights(
        generated_at="2025-03-07T12:00:00",
        total_events=100,
        principle_stats=[...],
        patterns=[...],
        recommendations=[...]
    )

    # Get markdown output
    markdown = insights.to_markdown()

    # Get JSON output
    from dataclasses import asdict
    import json
    json_output = json.dumps(asdict(insights))
"""
from dataclasses import dataclass
from typing import Any


@dataclass
class PrincipleStats:
    """Statistics for a single principle violation type.

    Attributes:
        principle: Name of the principle (e.g., "context_awareness")
        count: Number of times this principle was violated
        first_seen: ISO timestamp of first violation
        last_seen: ISO timestamp of most recent violation
    """
    principle: str
    count: int
    first_seen: str
    last_seen: str


@dataclass
class Pattern:
    """A detected pattern with examples.

    Attributes:
        pattern_type: Type of pattern (e.g., "scope_creep", "vague_directive")
        description: Human-readable description of the pattern
        examples: List of example instances (can be strings, dicts, etc.)
    """
    pattern_type: str
    description: str
    examples: list[Any]


@dataclass
class DreamingInsights:
    """Complete insights report from dreaming daemon analysis.

    Attributes:
        generated_at: ISO timestamp when insights were generated
        total_events: Total number of events analyzed
        principle_stats: List of principle violation statistics
        patterns: List of detected patterns
        recommendations: List of recommendation strings
    """
    generated_at: str
    total_events: int
    principle_stats: list[PrincipleStats]
    patterns: list[Pattern]
    recommendations: list[str]

    def to_markdown(self) -> str:
        """Convert insights to human-readable markdown format.

        Returns:
            str: Markdown-formatted insights report
        """
        lines = [
            "# Dreaming Insights",
            "",
            f"**Generated:** {self.generated_at}",
            f"**Events Analyzed:** {self.total_events}",
            "",
        ]

        # Principle Statistics section
        if self.principle_stats:
            lines.append("## Principle Statistics")
            lines.append("")
            for stats in self.principle_stats:
                lines.append(f"### {stats.principle}")
                lines.append(f"- **Count:** {stats.count}")
                lines.append(f"- **First Seen:** {stats.first_seen}")
                lines.append(f"- **Last Seen:** {stats.last_seen}")
                lines.append("")

        # Patterns section
        if self.patterns:
            lines.append("## Detected Patterns")
            lines.append("")
            for pattern in self.patterns:
                lines.append(f"### {pattern.pattern_type}")
                lines.append(f"{pattern.description}")
                lines.append("")
                if pattern.examples:
                    lines.append("**Examples:**")
                    for example in pattern.examples:
                        # Handle both string and dict examples
                        if isinstance(example, dict):
                            example_str = ", ".join(f"{k}={v}" for k, v in example.items())
                            lines.append(f"- {example_str}")
                        else:
                            lines.append(f"- {example}")
                    lines.append("")

        # Recommendations section
        if self.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        return "\n".join(lines)
