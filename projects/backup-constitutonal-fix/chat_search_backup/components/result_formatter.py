from __future__ import annotations

from datetime import datetime
from enum import auto
from pathlib import Path
from typing import Any
import json
import logging
import os
import re
import statistics

from ..interfaces.analysis_interfaces import (

#!/usr/bin/env python3
"""Result Formatter Implementation
Follows CSF NIP standards for result formatting and export.
"""


    AnalysisResult,
    IConfigurationManager,
    ILogger,
    IResultFormatter,
)


class ResultFormatter(IResultFormatter):
    """Result formatter following SRP with comprehensive formatting capabilities."""

    def __init__(self, container=None) -> None:
        self.container = container
        self.logger = container.resolve(ILogger) if container else None
        self.config_manager = (
            container.resolve(IConfigurationManager) if container else None
        )

        # Format configurations
        self._format_config = self._load_format_configuration()

    async def format_results(self, result: AnalysisResult, format_type: str) -> str:
        """Format analysis results in specified format."""
        try:
            if not result:
                return "Error: No results to format"

            if self.logger:
                await self.logger.debug(f"Formatting results in {format_type} format")

            if format_type.lower() == "json":
                return await self._format_json(result)
            if format_type.lower() == "html":
                return await self._format_html(result)
            if format_type.lower() == "markdown":
                return await self._format_markdown(result)
            if format_type.lower() == "plain":
                return await self._format_plain_text(result)
            if format_type.lower() == "summary":
                return await self._format_summary(result)
            if format_type.lower() == "detailed":
                return await self._format_detailed(result)
            return await self._format_json(result)  # Default to JSON

        except Exception as e:
            error_msg = f"Error formatting results: {e}"
            if self.logger:
                await self.logger.exception(error_msg)
            return error_msg

    async def export_results(self, result: AnalysisResult, file_path: str) -> bool:
        """Export results to file with automatic format detection."""
        try:
            if not result:
                if self.logger:
                    await self.logger.error("No results to export")
                return False

            file_path = Path(file_path)
            format_type = self._detect_format_from_path(file_path)

            if self.logger:
                await self.logger.info(
                    f"Exporting results to {file_path} as {format_type}"
                )

            formatted_result = await self.format_results(result, format_type)

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(formatted_result)

            if self.logger:
                await self.logger.info(f"Results exported successfully to {file_path}")

            return True

        except Exception as e:
            error_msg = f"Error exporting results: {e}"
            if self.logger:
                await self.logger.exception(error_msg)
            return False

    async def create_summary(self, result: AnalysisResult) -> str:
        """Create executive summary of analysis results."""
        try:
            if not result:
                return "No analysis results available"

            if self.logger:
                await self.logger.debug("Creating executive summary")

            summary_sections = []

            # Executive Overview
            summary_sections.append(await self._create_executive_overview(result))

            # Key Insights
            summary_sections.append(await self._create_key_insights(result))

            # Critical Findings
            summary_sections.append(await self._create_critical_findings(result))

            # Recommendations
            summary_sections.append(await self._create_recommendations(result))

            # Next Steps
            summary_sections.append(await self._create_next_steps(result))

            # Combine sections
            full_summary = "\n\n".join(summary_sections)

            if self.logger:
                await self.logger.info("Executive summary created successfully")

            return full_summary

        except Exception as e:
            error_msg = f"Error creating summary: {e}"
            if self.logger:
                await self.logger.exception(error_msg)
            return error_msg

    async def _format_json(self, result: AnalysisResult) -> str:
        """Format results as JSON."""
        try:
            # Convert result to dictionary with proper serialization
            result_dict = {
                "metadata": {
                    "analysis_timestamp": datetime.now().isoformat(),
                    "format_version": "1.0",
                    "generated_by": "CSF NIP Chat History Analyzer",
                },
                "summary": result.summary,
                "patterns": result.patterns,
                "statistics": result.statistics,
                "context": result.context,
                "additional_metadata": result.metadata,
            }

            # Handle datetime serialization
            def json_serializer(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                if hasattr(obj, "__dict__"):
                    return obj.__dict__
                return str(obj)

            return json.dumps(result_dict, indent=2, default=json_serializer)

        except Exception as e:
            return json.dumps({"error": f"JSON formatting error: {e}"})

    async def _format_html(self, result: AnalysisResult) -> str:
        """Format results as HTML report."""
        try:
            return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat History Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .section { margin-bottom: 30px; }
        .section h2 { color: #333; border-bottom: 2px solid #007acc; padding-bottom: 5px; }
        .pattern { background: #f9f9f9; padding: 10px; margin: 10px 0; border-left: 4px solid #007acc; }
        .stat { background: #e8f4f8; padding: 10px; margin: 5px 0; border-radius: 3px; }
        .critical { background: #ffe6e6; border-left-color: #cc0000; }
        .positive { background: #e6ffe6; border-left-color: #00cc00; }
        .warning { background: #fff3cd; border-left-color: #ffcc00; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Chat History Analysis Report</h1>
        <p>Generated on: {timestamp}</p>
        <p>Analysis Summary: {analysis_summary}</p>
    </div>

    <div class="section">
        <h2>Executive Summary</h2>
        {executive_summary}
    </div>

    <div class="section">
        <h2>Detected Patterns</h2>
        {patterns_section}
    </div>

    <div class="section">
        <h2>Statistics & Metrics</h2>
        {statistics_section}
    </div>

    <div class="section">
        <h2>Context Analysis</h2>
        {context_section}
    </div>

    <div class="footer">
        <p>Report generated by CSF NIP Chat History Analyzer</p>
        <p>For questions or support, please refer to the documentation</p>
    </div>
</body>
</html>
            """.format(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                analysis_summary=self._extract_analysis_summary(result),
                executive_summary=await self._create_executive_overview(result),
                patterns_section=await self._create_patterns_html_section(result),
                statistics_section=await self._create_statistics_html_section(result),
                context_section=await self._create_context_html_section(result),
            )

        except Exception as e:
            return f"<html><body><h1>Error</h1><p>HTML formatting error: {e}</p></body></html>"

    async def _format_markdown(self, result: AnalysisResult) -> str:
        """Format results as Markdown."""
        try:
            markdown_sections = []

            # Header
            markdown_sections.append("# Chat History Analysis Report")
            markdown_sections.append(
                f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            markdown_sections.append("")

            # Executive Summary
            markdown_sections.append("## Executive Summary")
            markdown_sections.append(await self._create_executive_overview(result))
            markdown_sections.append("")

            # Patterns
            markdown_sections.append("## Detected Patterns")
            markdown_sections.append(
                await self._create_patterns_markdown_section(result)
            )
            markdown_sections.append("")

            # Statistics
            markdown_sections.append("## Statistics & Metrics")
            markdown_sections.append(
                await self._create_statistics_markdown_section(result)
            )
            markdown_sections.append("")

            # Context
            markdown_sections.append("## Context Analysis")
            markdown_sections.append(
                await self._create_context_markdown_section(result)
            )
            markdown_sections.append("")

            # Footer
            markdown_sections.append("---")
            markdown_sections.append(
                "*Report generated by CSF NIP Chat History Analyzer*"
            )

            return "\n".join(markdown_sections)

        except Exception as e:
            return f"# Error\n\nMarkdown formatting error: {e}"

    async def _format_plain_text(self, result: AnalysisResult) -> str:
        """Format results as plain text."""
        try:
            text_sections = []

            # Header
            text_sections.append("CHAT HISTORY ANALYSIS REPORT")
            text_sections.append("=" * 50)
            text_sections.append(
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            text_sections.append("")

            # Executive Summary
            text_sections.append("EXECUTIVE SUMMARY")
            text_sections.append("-" * 20)
            text_sections.append(await self._create_executive_overview(result))
            text_sections.append("")

            # Patterns
            text_sections.append("DETECTED PATTERNS")
            text_sections.append("-" * 20)
            text_sections.append(await self._create_patterns_text_section(result))
            text_sections.append("")

            # Statistics
            text_sections.append("STATISTICS & METRICS")
            text_sections.append("-" * 20)
            text_sections.append(await self._create_statistics_text_section(result))
            text_sections.append("")

            # Context
            text_sections.append("CONTEXT ANALYSIS")
            text_sections.append("-" * 20)
            text_sections.append(await self._create_context_text_section(result))
            text_sections.append("")

            return "\n".join(text_sections)

        except Exception as e:
            return f"PLAIN TEXT REPORT\n\nError formatting results: {e}"

    async def _format_summary(self, result: AnalysisResult) -> str:
        """Format results as brief summary."""
        return await self.create_summary(result)

    async def _format_detailed(self, result: AnalysisResult) -> str:
        """Format results as detailed report."""
        return await self._format_html(result)  # HTML provides the most detailed format

    def _detect_format_from_path(self, file_path: Path) -> str:
        """Detect format type from file extension."""
        suffix = file_path.suffix.lower()

        format_map = {
            ".json": "json",
            ".html": "html",
            ".htm": "html",
            ".md": "markdown",
            ".txt": "plain",
            ".csv": "csv",
        }

        return format_map.get(suffix, "json")

    def _load_format_configuration(self) -> dict[str, Any]:
        """Load format configuration."""
        return {
            "max_preview_length": 200,
            "include_metadata": True,
            "include_timestamps": True,
            "confidence_threshold": 0.7,
            "pattern_highlighting": True,
            "statistical_rounding": 3,
        }

    def _extract_analysis_summary(self, result: AnalysisResult) -> str:
        """Extract brief analysis summary."""
        if not result.summary:
            return "No summary available"

        total_messages = result.summary.get("total_messages", 0)
        participants = result.summary.get("unique_participants", 0)
        duration = result.summary.get("conversation_duration_hours", 0)

        return f"{total_messages} messages from {participants} participants over {duration:.1f} hours"

    async def _create_executive_overview(self, result: AnalysisResult) -> str:
        """Create executive overview section."""
        overview_items = []

        if result.summary:
            total_messages = result.summary.get("total_messages", 0)
            participants = result.summary.get("unique_participants", 0)
            duration = result.summary.get("conversation_duration_hours", 0)

            overview_items.append(
                f"**Conversation Scale:** {total_messages} messages exchanged between {participants} participants",
            )
            overview_items.append(
                f"**Duration:** {duration:.1f} hours of active conversation"
            )
            overview_items.append(
                f"**Message Frequency:** {total_messages / max(duration, 0.1):.1f} messages per hour"
            )

        if result.patterns:
            pattern_count = len(result.patterns)
            overview_items.append(
                f"**Patterns Identified:** {pattern_count} distinct conversation patterns detected"
            )

        if result.statistics:
            overview_items.append(
                "**Statistical Analysis:** Comprehensive metrics computed across multiple dimensions"
            )

        return "\n".join(overview_items)

    async def _create_key_insights(self, result: AnalysisResult) -> str:
        """Create key insights section."""
        insights = []

        # Extract insights from patterns
        if result.patterns:
            for pattern in result.patterns[:3]:  # Top 3 patterns
                pattern_type = pattern.get("type", "unknown")
                pattern_name = pattern.get("pattern", "unnamed")
                confidence = pattern.get("confidence", 0)
                insights.append(
                    f"• **{pattern_type.title()}:** {pattern_name.replace('_', ' ').title()} (Confidence: {confidence:.1%})",
                )

        # Extract insights from statistics
        if result.statistics and "conversation_metrics" in result.statistics:
            metrics = result.statistics["conversation_metrics"]
            if "participant_count" in metrics:
                insights.append(
                    f"• **Participation:** {metrics['participant_count']} unique participants engaged"
                )

        if not insights:
            insights.append("• No significant insights identified")

        return "\n".join(insights)

    async def _create_critical_findings(self, result: AnalysisResult) -> str:
        """Create critical findings section."""
        findings = []

        # Check for security concerns
        if result.patterns:
            security_patterns = [
                p for p in result.patterns if "security" in str(p).lower()
            ]
            if security_patterns:
                findings.append(
                    "• **Security Considerations:** Potential security patterns detected - review recommended",
                )

        # Check for performance concerns
        if result.statistics and "performance_metrics" in result.statistics:
            findings.append(
                "• **Performance Analysis:** Detailed performance metrics available for optimization"
            )

        # Check for participation issues
        if result.statistics and "participant_metrics" in result.statistics:
            participation = result.statistics["participant_metrics"]
            if "participation_distribution" in participation:
                distribution = participation["participation_distribution"]
                max_ratio = max(distribution.values()) if distribution else 0
                if max_ratio > 0.7:
                    findings.append(
                        "• **Participation Imbalance:** High concentration of messages from single participant",
                    )

        if not findings:
            findings.append("• No critical issues identified")

        return "\n".join(findings)

    async def _create_recommendations(self, result: AnalysisResult) -> str:
        """Create recommendations section."""
        recommendations = []

        # General recommendations based on analysis
        if result.patterns:
            recommendations.append(
                "• **Pattern Monitoring:** Continue monitoring identified conversation patterns for trend analysis",
            )

        if result.statistics:
            recommendations.append(
                "• **Statistical Tracking:** Maintain statistical baseline for future comparisons"
            )

        recommendations.append(
            "• **Regular Analysis:** Schedule periodic analysis to track conversation evolution"
        )
        recommendations.append(
            "• **Participant Engagement:** Consider strategies to balance participant engagement if needed",
        )

        return "\n".join(recommendations)

    async def _create_next_steps(self, result: AnalysisResult) -> str:
        """Create next steps section."""
        steps = [
            "• Review detailed patterns and statistics in full report",
            "• Consider implementing conversation optimization strategies",
            "• Schedule follow-up analysis to measure improvements",
            "• Export results for sharing with stakeholders",
        ]

        return "\n".join(steps)

    async def _create_patterns_html_section(self, result: AnalysisResult) -> str:
        """Create patterns section for HTML."""
        if not result.patterns:
            return "<p>No patterns detected</p>"

        html_parts = []
        for pattern in result.patterns:
            pattern_type = pattern.get("type", "unknown")
            pattern_name = pattern.get("pattern", "unnamed")
            confidence = pattern.get("confidence", 0)
            count = pattern.get("count", 0)

            css_class = "pattern"
            if confidence > 0.8:
                css_class += " positive"
            elif confidence < 0.5:
                css_class += " warning"

            html_parts.append(
                f"""
            <div class="{css_class}">
                <strong>{pattern_type.title()}: {pattern_name.replace("_", " ").title()}</strong><br>
                Confidence: {confidence:.1%}<br>
                Occurrences: {count}
            </div>
            """
            )

        return "".join(html_parts)

    async def _create_statistics_html_section(self, result: AnalysisResult) -> str:
        """Create statistics section for HTML."""
        if not result.statistics:
            return "<p>No statistics available</p>"

        html_parts = []
        for category, stats in result.statistics.items():
            html_parts.append(f"<h3>{category.replace('_', ' ').title()}</h3>")

            if isinstance(stats, dict):
                html_parts.append("<table>")
                html_parts.append("<tr><th>Metric</th><th>Value</th></tr>")
                for key, value in stats.items():
                    display_value = self._format_stat_value(value)
                    html_parts.append(
                        f"<tr><td>{key.replace('_', ' ').title()}</td><td>{display_value}</td></tr>"
                    )
                html_parts.append("</table>")
            else:
                html_parts.append(f"<p>{stats}</p>")

        return "".join(html_parts)

    async def _create_context_html_section(self, result: AnalysisResult) -> str:
        """Create context section for HTML."""
        if not result.context:
            return "<p>No context analysis available</p>"

        html_parts = []
        for key, value in result.context.items():
            html_parts.append(f"<h3>{key.replace('_', ' ').title()}</h3>")
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    html_parts.append(
                        f"<p><strong>{subkey.replace('_', ' ').title()}:</strong> {subvalue}</p>"
                    )
            else:
                html_parts.append(f"<p>{value}</p>")

        return "".join(html_parts)

    async def _create_patterns_markdown_section(self, result: AnalysisResult) -> str:
        """Create patterns section for Markdown."""
        if not result.patterns:
            return "No patterns detected"

        markdown_parts = []
        for pattern in result.patterns:
            pattern_type = pattern.get("type", "unknown")
            pattern_name = pattern.get("pattern", "unnamed")
            confidence = pattern.get("confidence", 0)
            count = pattern.get("count", 0)

            markdown_parts.append(
                f"- **{pattern_type.title()}:** {pattern_name.replace('_', ' ').title()}"
            )
            markdown_parts.append(f"  - Confidence: {confidence:.1%}")
            markdown_parts.append(f"  - Occurrences: {count}")
            markdown_parts.append("")

        return "\n".join(markdown_parts)

    async def _create_statistics_markdown_section(self, result: AnalysisResult) -> str:
        """Create statistics section for Markdown."""
        if not result.statistics:
            return "No statistics available"

        markdown_parts = []
        for category, stats in result.statistics.items():
            markdown_parts.append(f"### {category.replace('_', ' ').title()}")

            if isinstance(stats, dict):
                for key, value in stats.items():
                    display_value = self._format_stat_value(value)
                    markdown_parts.append(
                        f"- **{key.replace('_', ' ').title()}:** {display_value}"
                    )
            else:
                markdown_parts.append(f"{stats}")
            markdown_parts.append("")

        return "\n".join(markdown_parts)

    async def _create_context_markdown_section(self, result: AnalysisResult) -> str:
        """Create context section for Markdown."""
        if not result.context:
            return "No context analysis available"

        markdown_parts = []
        for key, value in result.context.items():
            markdown_parts.append(f"### {key.replace('_', ' ').title()}")
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    markdown_parts.append(
                        f"- **{subkey.replace('_', ' ').title()}:** {subvalue}"
                    )
            else:
                markdown_parts.append(f"{value}")
            markdown_parts.append("")

        return "\n".join(markdown_parts)

    async def _create_patterns_text_section(self, result: AnalysisResult) -> str:
        """Create patterns section for plain text."""
        if not result.patterns:
            return "No patterns detected"

        text_parts = []
        for i, pattern in enumerate(result.patterns, 1):
            pattern_type = pattern.get("type", "unknown")
            pattern_name = pattern.get("pattern", "unnamed")
            confidence = pattern.get("confidence", 0)
            count = pattern.get("count", 0)

            text_parts.append(
                f"{i}. {pattern_type.upper()}: {pattern_name.replace('_', ' ').title()}"
            )
            text_parts.append(f"   Confidence: {confidence:.1%} | Occurrences: {count}")
            text_parts.append("")

        return "\n".join(text_parts)

    async def _create_statistics_text_section(self, result: AnalysisResult) -> str:
        """Create statistics section for plain text."""
        if not result.statistics:
            return "No statistics available"

        text_parts = []
        for category, stats in result.statistics.items():
            text_parts.append(f"{category.upper()}")
            text_parts.append("-" * len(category))

            if isinstance(stats, dict):
                for key, value in stats.items():
                    display_value = self._format_stat_value(value)
                    text_parts.append(
                        f"  {key.replace('_', ' ').title()}: {display_value}"
                    )
            else:
                text_parts.append(f"  {stats}")
            text_parts.append("")

        return "\n".join(text_parts)

    async def _create_context_text_section(self, result: AnalysisResult) -> str:
        """Create context section for plain text."""
        if not result.context:
            return "No context analysis available"

        text_parts = []
        for key, value in result.context.items():
            text_parts.append(f"{key.upper()}")
            text_parts.append("-" * len(key))
            if isinstance(value, dict):
                for subkey, subvalue in value.items():
                    text_parts.append(
                        f"  {subkey.replace('_', ' ').title()}: {subvalue}"
                    )
            else:
                text_parts.append(f"  {value}")
            text_parts.append("")

        return "\n".join(text_parts)

    def _format_stat_value(self, value: Any) -> str:
        """Format statistical value for display."""
        if isinstance(value, float):
            if value < 0.01:
                return f"{value:.4f}"
            if value < 1:
                return f"{value:.3f}"
            if value < 100:
                return f"{value:.2f}"
            return f"{value:.1f}"
        if isinstance(value, dict):
            return f"Dictionary with {len(value)} items"
        if isinstance(value, list):
            return f"List with {len(value)} items"
        return str(value)
