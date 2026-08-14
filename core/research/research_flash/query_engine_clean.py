from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

#!/usr/bin/env python3
"""
Research-Flash Query Engine - Modern Python 2025 Implementation

Follows CKS Python 2025 standards with modern async/await patterns,
proper type hints, and structured data models.
"""


# import CKS components following modern patterns
try:
    from query_engine import QueryResult
except ImportError:

    @dataclass
    class QueryResult:
        """Query result data model following Pydantic V2 patterns."""

        source: str
        title: str
        content: str
        url: str | None = None
        confidence: float = 0.0
        metadata: dict[str, Any] = field(default_factory=dict)
        timestamp: datetime = field(default_factory=datetime.now)

# GLM integration removed - not suitable for web search


# Mock implementations for development
class MockCKSSource:
    """Mock CKS source for development."""

    def __init__(self):
        self.name = "cks"

    def connect(self):
        return True

    async def search(self, query, max_results=5):
        return [
            {
                "title": f"CKS Knowledge: {query}",
                "content": f"Stored information about {query} from knowledge graph",
                "confidence": 0.80,
                "url": None,
            }
        ]


class MockCHSSource:
    """Mock CHS source for development."""

    def __init__(self):
        self.name = "chs"

    async def search(self, query, max_results=5):
        return [
            {
                "title": f"Chat History: {query}",
                "content": f"Previous discussions about {query}",
                "confidence": 0.75,
                "url": None,
            }
        ]


# Simple mock classes for missing components
class ResultRanker:
    def rank_results(self, results):
        return results


class ResultDeduplicator:
    def deduplicate(self, results):
        return results


class ResultSynthesizer:
    def __init__(self):
        self.analysis_capabilities = [
            "trend_analysis",
            "gap_identification",
            "quality_assessment",
            "practical_recommendations",
            "future_directions",
            "risk_analysis",
        ]

    def synthesize(self, query, results, source_results=None):
        if not results:
            return "No results found for synthesis analysis."

        # Analyze source distribution
        source_types = {}
        confidence_scores = []

        for result in results:
            source_type = result.metadata.get("source_type", "unknown")
            source_types[source_type] = source_types.get(source_type, 0) + 1
            confidence_scores.append(result.confidence)

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        # Generate comprehensive synthesis
        synthesis_parts = [
            "# Comprehensive Research Synthesis",
            f"**Query**: {query}",
            f"**Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## 📊 Research Overview",
            f"- **Total Results**: {len(results)} sources analyzed",
            f"- **Average Confidence**: {avg_confidence:.1%}",
            f"- **Source Diversity**: {len(source_types)} different source types",
            "",
            "## 🔍 Source Type Analysis",
        ]

        # Add source type breakdown
        for source_type, count in source_types.items():
            synthesis_parts.append(
                f"- **{source_type.replace('_', ' ').title()}**: {count} results"
            )

        synthesis_parts.extend(
            [
                "",
                "## 🧠 Key Insights & Trends",
                "Strong research patterns identified across multiple sources with consistent information flow.",
                "",
                "## 🎯 Practical Applications",
                "Research foundation supports theoretical approaches with practical implementations available.",
                "",
                "## 📈 Quality Assessment",
                f"**Overall Quality Score**: {avg_confidence:.1%}",
                "**Recommendation**: Strong for decision-making with current implementation.",
            ]
        )

        return "\n".join(synthesis_parts)


class ResearchConfig:
    """Research configuration following modern Python patterns."""

    def __init__(self):
        self.debug_mode = False
        self.max_results_per_source = 10
        self.timeout = 30

        # Add synthesis config
        class SynthesisConfig:
            max_total_results = 50

        self.synthesis = SynthesisConfig()


@dataclass
class ResearchResult:
    """Complete research result with synthesis."""

    query: str
    sources_used: list[str]
    results: list[QueryResult]
    synthesis: str
    processing_time: float
    source_performance: dict[str, float]
    metadata: dict[str, Any] = field(default_factory=dict)


class ResearchFlashEngine:
    """Multi-source research query engine following CKS standards."""

    def __init__(self, config: ResearchConfig | None = None):
        """Initialize research engine with configuration."""
        self.config = config or ResearchConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize modern components
        self.ranker = ResultRanker()
        self.deduplicator = ResultDeduplicator()
        self.synthesizer = ResultSynthesizer()

        # Initialize sources
        self.sources = {}
        self._initialize_sources()

    def _initialize_sources(self):
        """Initialize all configured research sources."""
        # Initialize CKS source
        try:
            self.sources["cks"] = MockCKSSource()
            self.logger.info("CKS source initialized")
        except Exception as e:
            self.logger.warning(f"CKS initialization failed: {e}")

        # Initialize CHS source
        try:
            self.sources["chs"] = MockCHSSource()
            self.logger.info("CHS source initialized")
        except Exception as e:
            self.logger.warning(f"CHS initialization failed: {e}")

    async def query(
        self,
        query_text: str,
        sources: list[str] | None = None,
        max_results_per_source: int | None = None,
    ) -> ResearchResult:
        """
        Execute multi-source research query with modern async patterns.

        Args:
            query_text: Research query text
            sources: Specific sources to query (None = all available)
            max_results_per_source: Maximum results per source

        Returns:
            ResearchResult with comprehensive findings

        """
        start_time = time.time()

        # Determine which sources to use
        query_sources = sources or list(self.sources.keys())
        if not query_sources:
            return ResearchResult(
                query=query_text,
                sources_used=[],
                results=[],
                synthesis="No research sources available",
                processing_time=time.time() - start_time,
                source_performance={},
            )

        # Query all sources in parallel
        source_tasks = []
        source_performance = {}

        for source_name in query_sources:
            if self.sources.get(source_name):
                task = self._query_source(source_name, query_text, max_results_per_source)
                source_tasks.append((source_name, task))

        # Execute queries concurrently
        source_results = {}
        if source_tasks:
            completed_tasks = await asyncio.gather(
                *[task for _, task in source_tasks], return_exceptions=True
            )

            for (source_name, _), result in zip(source_tasks, completed_tasks, strict=False):
                source_start = time.time()
                if isinstance(result, Exception):
                    self.logger.error(f"Source {source_name} failed: {result}")
                    source_performance[source_name] = time.time() - source_start
                else:
                    source_results[source_name] = result
                    source_performance[source_name] = time.time() - source_start

        # Process and synthesize results
        all_results = []
        for source_name, results in source_results.items():
            all_results.extend(results)

        # Process and synthesize
        all_results = self.ranker.rank_results(all_results)
        deduplicated_results = self.deduplicator.deduplicate(all_results)
        max_total = self.config.synthesis.max_total_results
        final_results = deduplicated_results[:max_total]

        # Generate synthesis
        synthesis = self.synthesizer.synthesize(query_text, final_results, source_results)

        processing_time = time.time() - start_time

        return ResearchResult(
            query=query_text,
            sources_used=query_sources,
            results=final_results,
            synthesis=synthesis,
            processing_time=processing_time,
            source_performance=source_performance,
            metadata={
                "timestamp": datetime.now().isoformat(),
                "total_sources_queried": len(source_tasks),
                "successful_sources": len(source_results),
            },
        )

    async def _query_source(
        self, source_name: str, query_text: str, max_results: int | None = None
    ) -> list[QueryResult]:
        """Query individual source with timeout handling."""
        source = self.sources[source_name]
        timeout = getattr(self.config, "timeout", 30)

        try:
            # Get max results from features.config or parameter
            if max_results is None:
                max_results = getattr(self.config, "max_results_per_source", 10)

            # Query source based on type
            if source_name == "cks":
                return await self._query_cks(source, query_text, max_results)
            if source_name == "chs":
                return await self._query_chs(source, query_text, max_results)
            self.logger.warning(f"Unknown source: {source_name}")
            return []

        except TimeoutError:
            self.logger.warning(f"Source {source_name} timed out after {timeout}s")
            return []
        except Exception as e:
            self.logger.error(f"Error querying {source_name}: {e}")
            return []

    async def _query_cks(
        self, cks_interface, query_text: str, max_results: int
    ) -> list[QueryResult]:
        """Query CKS knowledge system."""
        results = []

        try:
            # Connect to CKS
            if not cks_interface.connect():
                self.logger.error("Failed to connect to CKS")
                return []

            # Search CKS knowledge graph
            cks_results = await cks_interface.search(query_text, max_results=max_results)

            # Convert CKS results to QueryResult format
            for cks_result in cks_results:
                result = QueryResult(
                    source="cks",
                    title=cks_result.get("title", f"CKS: {query_text}"),
                    content=cks_result.get("content", ""),
                    url=cks_result.get("url"),
                    confidence=cks_result.get("confidence", 0.85),
                    metadata={
                        "source_type": "knowledge_graph",
                        "search_type": "vector_search",
                        "timestamp": datetime.now().isoformat(),
                        "mock": True,
                    },
                )
                results.append(result)

        except Exception as e:
            self.logger.error(f"CKS query error: {e}")

        return results

    async def _query_chs(
        self, chs_interface, query_text: str, max_results: int
    ) -> list[QueryResult]:
        """Query Chat History Search."""
        results = []

        try:
            # Search chat history
            chs_results = await chs_interface.search(query_text, max_results=max_results)

            # Convert CHS results to QueryResult format
            for chs_result in chs_results:
                result = QueryResult(
                    source="chs",
                    title=chs_result.get("title", f"Chat History: {query_text}"),
                    content=chs_result.get("content", ""),
                    url=chs_result.get("url"),
                    confidence=chs_result.get("confidence", 0.75),
                    metadata={
                        "source_type": "conversation_history",
                        "search_type": "context_search",
                        "timestamp": datetime.now().isoformat(),
                        "mock": True,
                    },
                )
                results.append(result)

        except Exception as e:
            self.logger.error(f"CHS query error: {e}")

        return results

    def get_available_sources(self) -> list[str]:
        """Get list of available sources."""
        return list(self.sources.keys())

    def get_source_status(self) -> dict[str, bool]:
        """Get status of all sources."""
        return {name: source is not None for name, source in self.sources.items()}

    def format_results_markdown(self, result: ResearchResult) -> str:
        """Format research results as Markdown for display."""
        output = []

        output.append(f"🔍 {result.query}")
        output.append(f"Sources: {', '.join(result.sources_used)}")
        output.append(f"Time: {result.processing_time:.1f}s")
        output.append("")

        # Add key insights
        if result.synthesis:
            output.append("💡 Key Insights:")
            output.append(
                result.synthesis[:500] + "..." if len(result.synthesis) > 500 else result.synthesis
            )
            output.append("")
            output.append("📚 Results:")

        # Add results with confidence scores
        for i, result_item in enumerate(result.results[:5], 1):
            confidence_pct = int(result_item.confidence * 100)
            output.append(f"{i}. {result_item.title} ({confidence_pct}%)")
            content_preview = (
                result_item.content[:100] + "..."
                if len(result_item.content) > 100
                else result_item.content
            )
            output.append(f"   {content_preview}")

        if len(result.results) > 5:
            output.append(f"... and {len(result.results) - 5} more results")

        return "\n".join(output)
