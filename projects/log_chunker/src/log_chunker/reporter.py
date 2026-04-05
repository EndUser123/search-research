"""Report generation for log analysis results."""

import json
from pathlib import Path

from rich.console import Console

from .config import ChunkingConfig
from .data_models import IntelligenceReport


class Reporter:
    """Generates reports from intelligence analysis results."""

    def __init__(self, console: Console = None):
        """Initialize the reporter."""
        self.console = console

    def save_intelligence_report(
        self, report: IntelligenceReport, output_dir: Path, config: ChunkingConfig
    ):
        """Save intelligence report to files."""
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON report
        json_file = (
            output_dir / f"{Path(report.log_source).stem}_IntelligenceReport.json"
        )

        # Convert report to dict for JSON serialization
        report_dict = {
            "report_version": report.report_version,
            "log_source": report.log_source,
            "total_lines_processed": report.total_lines_processed,
            "error_patterns": [
                {
                    "pattern_id": ep.pattern_id,
                    "template": ep.template,
                    "occurrences": ep.occurrences,
                    "severity": ep.severity,
                    "confidence": ep.confidence,
                    "first_occurrence_line": ep.first_occurrence_line,
                    "last_occurrence_line": ep.last_occurrence_line,
                    "related_chunks": ep.related_chunks,
                }
                for ep in report.error_patterns
            ],
            "correlations": [
                {
                    "group_id": cg.group_id,
                    "error_pattern_ids": cg.error_pattern_ids,
                    "frequency": cg.frequency,
                    "time_window_minutes": cg.time_window_minutes,
                    "confidence": cg.confidence,
                    "description": cg.description,
                }
                for cg in report.correlations
            ],
            "anomalies": [
                {
                    "anomaly_id": a.anomaly_id,
                    "anomaly_type": a.anomaly_type,
                    "description": a.description,
                    "confidence": a.confidence,
                    "start_line": a.start_line,
                    "end_line": a.end_line,
                    "related_chunks": a.related_chunks,
                }
                for a in report.anomalies
            ],
            "timeline": [
                {
                    "event_id": te.event_id,
                    "timestamp": te.timestamp.isoformat() if te.timestamp else None,
                    "event_type": te.event_type,
                    "description": te.description,
                    "line_number": te.line_number,
                    "related_chunk_id": te.related_chunk_id,
                    "causality_links": te.causality_links,
                }
                for te in report.timeline
            ],
            "semantic_clusters": [
                {
                    "cluster_id": sc.cluster_id,
                    "label": sc.label,
                    "chunk_ids": sc.chunk_ids,
                    "coherence_score": sc.coherence_score,
                    "keywords": sc.keywords,
                }
                for sc in report.semantic_clusters
            ],
            "plugin_analysis_results": report.plugin_analysis_results,
        }

        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        # Create simple markdown report
        md_file = output_dir / f"{Path(report.log_source).stem}_summary.md"
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# Log Analysis Report: {report.log_source}\n\n")
            f.write(f"**Report Version**: {report.report_version}\n")
            f.write(f"**Total Lines Processed**: {report.total_lines_processed:,}\n\n")

            if report.error_patterns:
                f.write("## Error Patterns\n\n")
                for ep in report.error_patterns:
                    f.write(
                        f"- **{ep.pattern_id}** (severity: {ep.severity}): {ep.occurrences} occurrences\n"
                    )
                f.write("\n")

            if report.anomalies:
                f.write("## Anomalies\n\n")
                for a in report.anomalies:
                    f.write(
                        f"- **{a.anomaly_id}**: {a.description} (confidence: {a.confidence:.2f})\n"
                    )
                f.write("\n")

            if report.correlations:
                f.write("## Correlations\n\n")
                for c in report.correlations:
                    f.write(
                        f"- **{c.group_id}**: {c.description} (confidence: {c.confidence:.2f})\n"
                    )
                f.write("\n")

            if report.semantic_clusters:
                f.write("## Semantic Clusters\n\n")
                for sc in report.semantic_clusters:
                    f.write(
                        f"- **{sc.label}**: {len(sc.chunk_ids)} chunks (keywords: {', '.join(sc.keywords)})\n"
                    )
                f.write("\n")

        if self.console:
            self.console.print(f"✅ Reports saved to: {output_dir}")
            self.console.print(f"   - JSON: {json_file.name}")
            self.console.print(f"   - Summary: {md_file.name}")
        else:
            print(f"✅ Reports saved to: {output_dir}")
            print(f"   - JSON: {json_file.name}")
            print(f"   - Summary: {md_file.name}")

    def display_chunking_results(self, result) -> None:
        """Display comprehensive chunking results with enhanced formatting."""
        if not self.console:
            self._display_plain_results(result)
            return

        try:
            from rich.panel import Panel
            from rich.table import Table

            # Create main results table
            results_table = Table(
                title="Chunking Results Summary",
                show_header=True,
                header_style="bold cyan",
            )
            results_table.add_column("Metric", style="cyan", width=25)
            results_table.add_column("Value", style="white", width=30)

            # Basic metrics
            chunks = getattr(result, "chunks", [])
            processing_time = getattr(result, "total_processing_time", 0.0)
            results_table.add_row("Total Chunks Generated", f"{len(chunks):,}")
            results_table.add_row("Processing Time", f"{processing_time:.2f} seconds")

            # Quality metrics if available
            quality_metrics = getattr(result, "quality_metrics", {})
            if quality_metrics:
                for metric, value in quality_metrics.items():
                    if isinstance(value, float):
                        results_table.add_row(
                            f"Quality: {metric.title()}", f"{value:.3f}"
                        )
                    else:
                        results_table.add_row(f"Quality: {metric.title()}", str(value))

            # Intelligence report summary
            intelligence_report = getattr(result, "intelligence_report", None)
            if intelligence_report:
                error_patterns = getattr(intelligence_report, "error_patterns", [])
                anomalies = getattr(intelligence_report, "anomalies", [])
                correlations = getattr(intelligence_report, "correlations", [])

                results_table.add_row("Error Patterns Found", str(len(error_patterns)))
                results_table.add_row("Anomalies Detected", str(len(anomalies)))
                results_table.add_row("Correlations Found", str(len(correlations)))

            # Display in a panel
            results_panel = Panel(
                results_table,
                title="[bold green]Processing Complete![/bold green]",
                border_style="green",
            )
            self.console.print(results_panel)

            # Show chunk details if available
            if chunks:
                self._display_chunk_summary(chunks)

        except ImportError:
            self._display_plain_results(result)

    def _display_chunk_summary(self, chunks):
        """Display a summary of chunks."""
        try:
            from rich.table import Table

            chunk_table = Table(
                title="Chunk Details (First 5)",
                show_header=True,
                header_style="bold yellow",
            )
            chunk_table.add_column("ID", style="cyan", width=8)
            chunk_table.add_column("Size (chars)", style="green", width=12)
            chunk_table.add_column("Lines", style="yellow", width=8)
            chunk_table.add_column("Preview", style="white", width=50)

            for i, (chunk_content, chunk_info) in enumerate(chunks[:5]):
                chunk_id = getattr(chunk_info, "chunk_id", i)
                chunk_size = len(chunk_content)
                line_count = chunk_content.count("\n") + 1
                preview = chunk_content.replace("\n", " ")[:47]
                if len(chunk_content) > 47:
                    preview += "..."

                chunk_table.add_row(
                    str(chunk_id), f"{chunk_size:,}", str(line_count), preview
                )

            if len(chunks) > 5:
                chunk_table.add_row(
                    "...", "...", "...", f"... and {len(chunks) - 5} more chunks"
                )

            self.console.print(chunk_table)

        except ImportError:
            pass

    def _display_plain_results(self, result):
        """Fallback display for when Rich is not available."""
        print("\n" + "=" * 60)
        print("CHUNKING RESULTS SUMMARY")
        print("=" * 60)

        chunks = getattr(result, "chunks", [])
        processing_time = getattr(result, "total_processing_time", 0.0)

        print(f"Total Chunks Generated: {len(chunks)}")
        print(f"Processing Time: {processing_time:.2f} seconds")

        quality_metrics = getattr(result, "quality_metrics", {})
        if quality_metrics:
            print("\nQuality Metrics:")
            for metric, value in quality_metrics.items():
                print(f"  {metric}: {value}")

        intelligence_report = getattr(result, "intelligence_report", None)
        if intelligence_report:
            print("\nIntelligence Analysis:")
            error_patterns = getattr(intelligence_report, "error_patterns", [])
            anomalies = getattr(intelligence_report, "anomalies", [])
            correlations = getattr(intelligence_report, "correlations", [])

            print(f"  Error Patterns: {len(error_patterns)}")
            print(f"  Anomalies: {len(anomalies)}")
            print(f"  Correlations: {len(correlations)}")

        print("=" * 60)
