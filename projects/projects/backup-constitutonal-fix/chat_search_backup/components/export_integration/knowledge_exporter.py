from __future__ import annotations

from dataclasses import field
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import logging
import os
import sys

from ...domain_models.chat_models import (
from ..interfaces.chat_interfaces import IExportIntegration
import csv
import xml.etree.ElementTree as ET

#!/usr/bin/env python3
"""Export Integration with CSF NIP Knowledge System
Advanced export functionality with knowledge system integration and evidence tracking.
"""


# Add CSF NIP paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent))
sys.path.append(
    str(Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "lib")
)

    AnalysisSession,
    ConversationPattern,
    ExportConfiguration,
    KnowledgeGraph,
    SearchResult,
    TemporalMetrics,
)


class EvidenceTracker:
    """Track evidence for analysis results."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def collect_evidence(
        self, query: str, results: list[SearchResult]
    ) -> dict[str, list[str]]:
        """Collect evidence for search results."""
        return {
            "query_terms": self._extract_query_terms(query),
            "matched_content": self._extract_matched_content(results),
            "semantic_sources": self._extract_semantic_sources(results),
            "temporal_context": self._extract_temporal_context(results),
            "context_switches": self._identify_context_switches(results),
            "topic_evolution": self._track_topic_evolution(results),
        }

    def _extract_query_terms(self, query: str) -> list[str]:
        """Extract terms from original query."""
        import re

        # Extract quoted phrases
        quoted_terms = re.findall(r'"([^"]+)"', query)

        # Extract code references
        code_refs = re.findall(r"`([^`]+)`", query)

        # Extract remaining terms
        clean_query = re.sub(r'"[^"]+"|`[^`]+`', "", query)
        words = re.findall(r"\b\w+\b", clean_query.lower())

        # Filter stop words
        stop_words = {
            "the",
            "is",
            "at",
            "which",
            "on",
            "and",
            "a",
            "to",
            "are",
            "as",
            "was",
            "were",
            "will",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
        }

        filtered_words = [
            word for word in words if word not in stop_words and len(word) > 2
        ]

        return quoted_terms + code_refs + filtered_words

    def _extract_matched_content(self, results: list[SearchResult]) -> list[str]:
        """Extract matched content snippets."""
        matched_content = []

        for result in results:
            # Add highlighted snippet if available
            if result.highlighted_snippet:
                matched_content.append(result.highlighted_snippet)

            # Add matched terms in context
            if result.matched_terms:
                context_snippet = self._create_context_snippet(
                    result.message.content, result.matched_terms
                )
                matched_content.append(context_snippet)

        return matched_content

    def _create_context_snippet(
        self, content: str, terms: list[str], context_size: int = 100
    ) -> str:
        """Create context snippet around matched terms."""
        for term in terms:
            # Find first occurrence of term
            index = content.lower().find(term.lower())
            if index != -1:
                start = max(0, index - context_size)
                end = min(len(content), index + len(term) + context_size)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."
                return snippet

        return content[:200] + "..." if len(content) > 200 else content

    def _extract_semantic_sources(self, results: list[SearchResult]) -> list[str]:
        """Extract semantic similarity sources."""
        semantic_sources = []

        for result in results:
            if result.semantic_similarity > 0.5:  # High similarity threshold
                source = (
                    f"semantic_{result.message.id}_{result.semantic_similarity:.2f}"
                )
                semantic_sources.append(source)

        return semantic_sources

    def _extract_temporal_context(self, results: list[SearchResult]) -> list[str]:
        """Extract temporal context information."""
        if not results:
            return []

        timestamps = [result.message.timestamp for result in results]
        earliest = datetime.fromtimestamp(min(timestamps) / 1000)
        latest = datetime.fromtimestamp(max(timestamps) / 1000)

        temporal_context = [
            f"time_range:{earliest.strftime('%Y-%m-%d')}_{latest.strftime('%Y-%m-%d')}",
            f"result_count:{len(results)}",
            f"time_span_days:{(latest - earliest).days + 1}",
        ]

        # Add temporal patterns
        time_groups = self._group_by_time_periods(results)
        for period, count in time_groups.items():
            temporal_context.append(f"period_{period}:{count}")

        return temporal_context

    def _group_by_time_periods(self, results: list[SearchResult]) -> dict[str, int]:
        """Group results by time periods."""
        time_groups = {}

        for result in results:
            dt = datetime.fromtimestamp(result.message.timestamp / 1000)
            period_key = dt.strftime("%Y-%m")  # Group by month
            time_groups[period_key] = time_groups.get(period_key, 0) + 1

        return time_groups

    def _identify_context_switches(self, results: list[SearchResult]) -> list[str]:
        """Identify context switches in results."""
        if not results:
            return []

        context_switches = []
        sorted_results = sorted(results, key=lambda r: r.message.timestamp)

        for i in range(1, len(sorted_results)):
            prev_context = sorted_results[i - 1].message.context.value
            curr_context = sorted_results[i].message.context.value

            if prev_context != curr_context:
                switch_info = f"switch:{prev_context}_to_{curr_context}"
                context_switches.append(switch_info)

        return context_switches

    def _track_topic_evolution(self, results: list[SearchResult]) -> list[str]:
        """Track topic evolution across results."""
        if not results:
            return []

        topic_evolution = []
        sorted_results = sorted(results, key=lambda r: r.message.timestamp)

        for result in sorted_results:
            if result.message.semantic_tags:
                topics_str = ",".join(
                    result.message.semantic_tags[:3]
                )  # Limit to top 3
                timestamp = datetime.fromtimestamp(
                    result.message.timestamp / 1000
                ).strftime("%Y-%m-%d")
                evolution_point = f"{timestamp}:{topics_str}"
                topic_evolution.append(evolution_point)

        return topic_evolution


class CSFNIpIntegrator:
    """Integrate with CSF NIP knowledge system."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def integrate_with_csf_nip(self, session: AnalysisSession) -> bool:
        """Integrate analysis results with CSF NIP knowledge system."""
        try:
            # Try to import CSF NIP components
            from modules.knowledge_system.src.sqlite_knowledge_curator import (
                SQLiteKnowledgeCurator,
            )

            curator = SQLiteKnowledgeCurator()

            # Store search patterns
            if session.patterns:
                self._store_patterns_in_knowledge_base(
                    curator, session.patterns, session.query
                )

            # Store temporal insights
            if session.temporal_metrics:
                self._store_temporal_insights(
                    curator, session.temporal_metrics, session.query
                )

            # Store knowledge graph
            if session.knowledge_graph:
                self._store_knowledge_graph_insights(
                    curator, session.knowledge_graph, session.query
                )

            # Store analysis session as learning
            self._store_analysis_learning(curator, session)

            self.logger.info(
                f"Successfully integrated session {session.session_id} with CSF NIP"
            )
            return True

        except ImportError as e:
            self.logger.warning(f"CSF NIP knowledge system not available: {e}")
            return False
        except Exception as e:
            self.logger.exception(f"Failed to integrate with CSF NIP: {e}")
            return False

    def store_patterns_in_knowledge_base(
        self, patterns: list[ConversationPattern]
    ) -> bool:
        """Store patterns in CSF NIP knowledge base."""
        try:
                SQLiteKnowledgeCurator,
            )

            curator = SQLiteKnowledgeCurator()

            for pattern in patterns:
                knowledge_item = {
                    "pattern_id": pattern.pattern_id,
                    "pattern_type": pattern.pattern_type,
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "evidence_count": len(pattern.evidence_entries),
                    "trend_direction": pattern.trend_direction,
                    "source": "chat_analysis",
                    "created_at": datetime.now().isoformat(),
                }

                curator.add_library_pattern(
                    pattern_type="conversation",
                    title=pattern.description,
                    description=json.dumps(knowledge_item, indent=2),
                    evidence=pattern.evidence_entries[:5],  # Limit evidence
                    confidence=pattern.confidence,
                )

            self.logger.info(f"Stored {len(patterns)} patterns in knowledge base")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to store patterns in knowledge base: {e}")
            return False

    def _store_patterns_in_knowledge_base(
        self, curator, patterns: list[ConversationPattern], query: str
    ) -> None:
        """Store patterns using curator instance."""
        for pattern in patterns:
            knowledge_item = {
                "pattern_id": pattern.pattern_id,
                "pattern_type": pattern.pattern_type,
                "description": pattern.description,
                "frequency": pattern.frequency,
                "confidence": pattern.confidence,
                "evidence_count": len(pattern.evidence_entries),
                "trend_direction": pattern.trend_direction,
                "query_context": query,
                "source": "chat_analysis",
                "created_at": datetime.now().isoformat(),
            }

            curator.add_library_pattern(
                pattern_type="conversation",
                title=pattern.description,
                description=json.dumps(knowledge_item, indent=2),
                evidence=pattern.evidence_entries[:5],
                confidence=pattern.confidence,
            )

    def _store_temporal_insights(
        self, curator, temporal_metrics: list[TemporalMetrics], query: str
    ) -> None:
        """Store temporal insights using curator instance."""
        for metric in temporal_metrics:
            insight = {
                "time_bucket": metric.time_bucket,
                "scale": metric.scale.value,
                "message_count": metric.message_count,
                "intensity_average": metric.intensity_average,
                "unique_topics": metric.unique_topics,
                "engagement_score": metric.engagement_score,
                "trend_slope": metric.trend_slope,
                "query_context": query,
                "source": "temporal_analysis",
                "created_at": datetime.now().isoformat(),
            }

            curator.add_library_pattern(
                pattern_type="temporal",
                title=f"Temporal Pattern: {metric.time_bucket}",
                description=json.dumps(insight, indent=2),
                evidence=[metric.time_bucket],
                confidence=0.8,
            )

    def _store_knowledge_graph_insights(
        self, curator, graph: KnowledgeGraph, query: str
    ) -> None:
        """Store knowledge graph insights using curator instance."""
        graph_insight = {
            "graph_id": graph.graph_id,
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "cluster_count": graph.cluster_count,
            "average_degree": graph.average_degree,
            "modularity": graph.modularity,
            "query_context": query,
            "source": "knowledge_graph_analysis",
            "created_at": datetime.now().isoformat(),
        }

        # Store top centrality nodes as insights
        central_nodes = sorted(
            graph.centrality_scores.items(), key=lambda x: x[1], reverse=True
        )[:5]
        graph_insight["central_concepts"] = central_nodes

        curator.add_library_pattern(
            pattern_type="knowledge_graph",
            title=f"Knowledge Graph: {graph.node_count} nodes",
            description=json.dumps(graph_insight, indent=2),
            evidence=[node for node, _ in central_nodes],
            confidence=0.9,
        )

    def _store_analysis_learning(self, curator, session: AnalysisSession) -> None:
        """Store analysis session as learning."""
        learning = {
            "session_id": session.session_id,
            "query": session.query,
            "result_count": len(session.results),
            "pattern_count": len(session.patterns),
            "confidence_score": session.confidence_score,
            "processing_time_ms": session.processing_time_ms,
            "cache_hit": session.cache_hit,
            "validation_status": session.validation_status,
            "evidence_categories": list(session.evidence_collected.keys()),
            "source": "chat_analysis_session",
            "created_at": datetime.now().isoformat(),
        }

        curator.add_library_pattern(
            pattern_type="learning",
            title=f"Analysis Learning: {session.query[:50]}",
            description=json.dumps(learning, indent=2),
            evidence=[session.session_id],
            confidence=session.confidence_score,
        )

    def create_tasks_from_findings(self, session: AnalysisSession) -> list[str]:
        """Create tasks from analysis findings."""
        tasks = []

        try:
            # Try to import ToolRegistry
            from modules.ToolRegistry.ToolRegistry import ToolRegistry

            tm = ToolRegistry()

            # Create tasks from patterns
            for pattern in session.patterns:
                if (
                    pattern.confidence > 0.7 and pattern.frequency > 1
                ):  # High confidence patterns
                    task_title = f"Investigate {pattern.pattern_type} pattern: {pattern.description[:50]}"
                    task_description = f"""
Pattern Analysis Finding:
- Type: {pattern.pattern_type}
- Description: {pattern.description}
- Frequency: {pattern.frequency}
- Confidence: {pattern.confidence:.2f}
- Query Context: {session.query}

Evidence: {len(pattern.evidence_entries)} supporting messages
Trend: {pattern.trend_direction}
                    """.strip()

                    task_id = tm.create_task(
                        title=task_title,
                        description=task_description,
                        priority="medium" if pattern.confidence > 0.8 else "low",
                        tags=["chat-analysis", "pattern", pattern.pattern_type],
                    )
                    tasks.append(task_id)

            # Create tasks from high-impact results
            high_impact_results = [
                r for r in session.results if r.relevance_score > 0.8
            ]
            if len(high_impact_results) > 5:
                task_title = f"Review high-impact findings for: {session.query[:50]}"
                task_description = f"""
High-Impact Results Review:
- Query: {session.query}
- High-Impact Results: {len(high_impact_results)}
- Average Score: {sum(r.relevance_score for r in high_impact_results) / len(high_impact_results):.3f}

Top results warrant further investigation and potential action.
                """.strip()

                task_id = tm.create_task(
                    title=task_title,
                    description=task_description,
                    priority="high",
                    tags=["chat-analysis", "high-impact", "review"],
                )
                tasks.append(task_id)

            self.logger.info(f"Created {len(tasks)} tasks from analysis findings")
            return tasks

        except ImportError as e:
            self.logger.warning(f"ToolRegistry not available: {e}")
            return []
        except Exception as e:
            self.logger.exception(f"Failed to create tasks: {e}")
            return []


class FormatExporter:
    """Handle different export formats."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def export_to_json(
        self, data: Any, config: ExportConfiguration, output_path: str
    ) -> bool:
        """Export data to JSON format."""
        try:
            export_data = {
                "export_metadata": {
                    "export_id": config.export_id,
                    "generated_at": datetime.now().isoformat(),
                    "format": "json",
                    "configuration": config.to_dict(),
                },
                "data": data,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info(f"Exported data to JSON: {output_path}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to export to JSON: {e}")
            return False

    def export_to_csv(
        self, data: Any, config: ExportConfiguration, output_path: str
    ) -> bool:
        """Export data to CSV format."""
        try:
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                if isinstance(data, list) and data and isinstance(data[0], dict):
                    # Handle list of dictionaries
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    # Handle other data types - convert to tabular format
                    f.write("Type,Content,Metadata\n")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            f.write(f"{key},{value!s},\n")
                    else:
                        f.write(f"data,{data!s},\n")

            self.logger.info(f"Exported data to CSV: {output_path}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to export to CSV: {e}")
            return False

    def export_to_markdown(
        self, data: Any, config: ExportConfiguration, output_path: str
    ) -> bool:
        """Export data to Markdown format."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# Chat Analysis Export\n\n")
                f.write(
                    f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(f"**Export ID:** {config.export_id}\n\n")

                # Use custom template if provided
                if config.custom_template:
                    content = self._apply_template(data, config.custom_template)
                    f.write(content)
                else:
                    content = self._format_data_as_markdown(data, config)
                    f.write(content)

            self.logger.info(f"Exported data to Markdown: {output_path}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to export to Markdown: {e}")
            return False

    def export_to_xml(
        self, data: Any, config: ExportConfiguration, output_path: str
    ) -> bool:
        """Export data to XML format."""
        try:
            root = ET.Element("chat_analysis_export")

            # Add metadata
            metadata = ET.SubElement(root, "metadata")
            ET.SubElement(metadata, "export_id").text = config.export_id
            ET.SubElement(metadata, "generated_at").text = datetime.now().isoformat()
            ET.SubElement(metadata, "format").text = "xml"

            # Add data
            data_element = ET.SubElement(root, "data")
            self._dict_to_xml(data, data_element)

            tree = ET.ElementTree(root)
            tree.write(output_path, encoding="utf-8", xml_declaration=True)

            self.logger.info(f"Exported data to XML: {output_path}")
            return True

        except Exception as e:
            self.logger.exception(f"Failed to export to XML: {e}")
            return False

    def _dict_to_xml(self, data: Any, parent: ET.Element) -> None:
        """Convert dictionary to XML elements."""
        if isinstance(data, dict):
            for key, value in data.items():
                child = ET.SubElement(parent, key.replace(" ", "_"))
                self._dict_to_xml(value, child)
        elif isinstance(data, list):
            for item in data:
                child = ET.SubElement(parent, "item")
                self._dict_to_xml(item, child)
        else:
            parent.text = str(data)

    def _apply_template(self, data: Any, template: str) -> str:
        """Apply custom template to data."""
        # Simple template substitution - in production, use proper templating engine
        try:
            import re

            # Replace placeholders
            result = template

            # Replace {{data}} with formatted data
            if "{{data}}" in result:
                formatted_data = json.dumps(data, indent=2, default=str)
                result = result.replace("{{data}}", formatted_data)

            # Replace other placeholders
            placeholders = re.findall(r"\{\{(\w+)\}\}", result)
            for placeholder in placeholders:
                if placeholder == "timestamp":
                    result = result.replace(
                        "{{" + placeholder + "}}", datetime.now().isoformat()
                    )
                elif placeholder == "export_id":
                    result = result.replace(
                        "{{" + placeholder + "}}", str(hash(data) % 1000000)
                    )

            return result

        except Exception as e:
            self.logger.exception(f"Failed to apply template: {e}")
            return f"Template Error: {e!s}\n\nRaw Data:\n{json.dumps(data, indent=2, default=str)}"

    def _format_data_as_markdown(self, data: Any, config: ExportConfiguration) -> str:
        """Format data as Markdown."""
        if isinstance(data, list):
            output = f"## Results ({len(data)} items)\n\n"
            for i, item in enumerate(data[: config.max_results], 1):
                output += f"### {i}. "
                if isinstance(item, dict):
                    if "title" in item:
                        output += item["title"]
                    elif "name" in item:
                        output += item["name"]
                    else:
                        output += f"Item {i}"

                    output += "\n\n"
                    for key, value in item.items():
                        if key not in {"title", "name"}:
                            output += f"**{key}:** {value}\n"
                    output += "\n"
                else:
                    output += f"{item}\n\n"
            return output

        if isinstance(data, dict):
            output = "## Data Overview\n\n"
            for key, value in data.items():
                output += f"### {key}\n\n"
                if isinstance(value, (dict, list)):
                    output += (
                        f"```json\n{json.dumps(value, indent=2, default=str)}\n```\n\n"
                    )
                else:
                    output += f"{value}\n\n"
            return output

        return f"## Data\n\n```\n{data!s}\n```"


class EnhancedKnowledgeExporter(IExportIntegration):
    """Enhanced knowledge exporter with comprehensive integration."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.evidence_tracker = EvidenceTracker()
        self.csf_nip_integrator = CSFNIpIntegrator()
        self.format_exporter = FormatExporter()

    def export_search_results(
        self, results: list[SearchResult], config: ExportConfiguration
    ) -> bool:
        """Export search results to specified format."""
        try:
            # Prepare data for export
            export_data = []

            for result in results:
                result_data = {
                    "rank": results.index(result) + 1,
                    "id": result.message.id,
                    "content": result.message.content,
                    "timestamp": datetime.fromtimestamp(
                        result.message.timestamp / 1000
                    ).isoformat(),
                    "context": result.message.context.value,
                    "project": result.message.project_name,
                    "relevance_score": result.relevance_score,
                    "matched_terms": result.matched_terms,
                    "semantic_similarity": result.semantic_similarity,
                    "temporal_relevance": result.temporal_relevance,
                    "confidence": result.confidence_score,
                    "semantic_tags": result.message.semantic_tags,
                    "intensity": result.message.intensity_score,
                    "evidence_sources": result.evidence_sources,
                }

                # Add processing metadata if included
                if config.include_evidence:
                    result_data["processing_metadata"] = result.processing_metadata

                export_data.append(result_data)

            # Generate output path if not provided
            if not config.output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                config.output_path = f"chat_search_results_{timestamp}.{config.format}"

            # Export based on format
            success = self._export_by_format(export_data, config)

            if success:
                self.logger.info(f"Successfully exported {len(results)} search results")
            return success

        except Exception as e:
            self.logger.exception(f"Failed to export search results: {e}")
            return False

    def export_patterns(
        self, patterns: list[ConversationPattern], config: ExportConfiguration
    ) -> bool:
        """Export patterns to specified format."""
        try:
            export_data = []

            for pattern in patterns:
                pattern_data = {
                    "pattern_id": pattern.pattern_id,
                    "type": pattern.pattern_type,
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "confidence": pattern.confidence,
                    "time_span_days": pattern.time_span_days,
                    "context_distribution": {
                        ctx.value: count
                        for ctx, count in pattern.context_distribution.items()
                    },
                    "sample_messages": pattern.sample_messages,
                    "temporal_distribution": pattern.temporal_distribution,
                    "related_patterns": pattern.related_patterns,
                    "evidence_count": len(pattern.evidence_entries),
                    "last_observed": (
                        pattern.last_observed.isoformat()
                        if pattern.last_observed
                        else None
                    ),
                    "trend_direction": pattern.trend_direction,
                }

                # Add processing metadata if included
                if config.include_evidence:
                    pattern_data["evidence_entries"] = pattern.evidence_entries[
                        :10
                    ]  # Limit evidence

                export_data.append(pattern_data)

            # Generate output path if not provided
            if not config.output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                config.output_path = f"chat_patterns_{timestamp}.{config.format}"

            # Export based on format
            success = self._export_by_format(export_data, config)

            if success:
                self.logger.info(f"Successfully exported {len(patterns)} patterns")
            return success

        except Exception as e:
            self.logger.exception(f"Failed to export patterns: {e}")
            return False

    def export_temporal_analysis(
        self, metrics: list[TemporalMetrics], config: ExportConfiguration
    ) -> bool:
        """Export temporal analysis to specified format."""
        try:
            export_data = []

            for metric in metrics:
                metric_data = {
                    "time_bucket": metric.time_bucket,
                    "scale": metric.scale.value,
                    "message_count": metric.message_count,
                    "intensity_average": metric.intensity_average,
                    "intensity_peak": metric.intensity_peak,
                    "topic_distribution": metric.topic_distribution,
                    "context_distribution": {
                        ctx.value: count
                        for ctx, count in metric.context_distribution.items()
                    },
                    "unique_topics": metric.unique_topics,
                    "engagement_score": metric.engagement_score,
                    "trend_slope": metric.trend_slope,
                    "trend_significance": metric.trend_significance,
                    "seasonality_detected": metric.seasonality_detected,
                }

                export_data.append(metric_data)

            # Generate output path if not provided
            if not config.output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                config.output_path = f"temporal_analysis_{timestamp}.{config.format}"

            # Export based on format
            success = self._export_by_format(export_data, config)

            if success:
                self.logger.info(
                    f"Successfully exported {len(metrics)} temporal metrics"
                )
            return success

        except Exception as e:
            self.logger.exception(f"Failed to export temporal analysis: {e}")
            return False

    def export_knowledge_graph(
        self, graph: KnowledgeGraph, config: ExportConfiguration
    ) -> bool:
        """Export knowledge graph to specified format."""
        try:
            export_data = {
                "graph_metadata": {
                    "graph_id": graph.graph_id,
                    "node_count": graph.node_count,
                    "edge_count": graph.edge_count,
                    "cluster_count": graph.cluster_count,
                    "average_degree": graph.average_degree,
                    "modularity": graph.modularity,
                    "last_updated": graph.last_updated.isoformat(),
                },
                "nodes": graph.nodes,
                "edges": graph.edges,
                "topics": graph.topics,
                "clusters": graph.clusters,
                "centrality_scores": graph.centrality_scores,
            }

            # Generate output path if not provided
            if not config.output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                config.output_path = f"knowledge_graph_{timestamp}.{config.format}"

            # Export based on format
            success = self._export_by_format(export_data, config)

            if success:
                self.logger.info("Successfully exported knowledge graph")
            return success

        except Exception as e:
            self.logger.exception(f"Failed to export knowledge graph: {e}")
            return False

    def integrate_with_csf_nip(self, session: AnalysisSession) -> bool:
        """Integrate analysis results with CSF NIP knowledge system."""
        return self.csf_nip_integrator.integrate_with_csf_nip(session)

    def store_patterns_in_knowledge_base(
        self, patterns: list[ConversationPattern]
    ) -> bool:
        """Store patterns in CSF NIP knowledge base."""
        return self.csf_nip_integrator.store_patterns_in_knowledge_base(patterns)

    def create_tasks_from_findings(self, session: AnalysisSession) -> list[str]:
        """Create tasks from analysis findings."""
        return self.csf_nip_integrator.create_tasks_from_findings(session)

    def _export_by_format(self, data: Any, config: ExportConfiguration) -> bool:
        """Export data using specified format."""
        format_handlers = {
            "json": self.format_exporter.export_to_json,
            "csv": self.format_exporter.export_to_csv,
            "markdown": self.format_exporter.export_to_markdown,
            "xml": self.format_exporter.export_to_xml,
        }

        handler = format_handlers.get(config.format.lower())
        if not handler:
            self.logger.error(f"Unsupported export format: {config.format}")
            return False

        return handler(data, config, config.output_path)
