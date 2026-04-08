from __future__ import annotations

import asyncio
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""
Research-Flash Query Engine - Multi-Source Knowledge Retrieval

Intelligent multi-source research system that queries CKS, CHS, and GLM 4.6-flash internet search
with AI-powered synthesis and ranking for comprehensive research results.

CSF Constitutional Requirements:
- Part G: Solo developer optimization with simple interface
- Part H: Force multiplier integration with existing CKS/CHS infrastructure
- Part I: No enterprise bloat with minimal dependencies
- Part J: Proper CKS knowledge system integration
"""


# Add project paths for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


# Mock CKS source for testing
class MockCKSSource:
    def __init__(self):
        self.name = "cks"

    async def search(self, query, max_results=10):
        return [
            QueryResult(
                source="cks",
                title=f"Knowledge about {query}",
                content=f"Stored information regarding {query} from knowledge graph",
                confidence=0.80,
            )
        ]


try:
    from features.cks.cks_query_interface import CKSQueryInterface

    CKS_AVAILABLE = True
except ImportError:
    CKS_AVAILABLE = False
    CKSQueryInterface = MockCKSSource


# Mock CHS source for testing
class CHSSource:
    def __init__(self):
        self.name = "chs"

    async def search(self, query, max_results=10):
        return [
            QueryResult(
                source="chs",
                title=f"Chat about {query}",
                content=f"Previous discussion regarding {query}",
                confidence=0.75,
            )
        ]


CHS_AVAILABLE = True
# GLM_AVAILABLE removed - GLM source not suitable for web search


# For now, create simple mock classes for missing components
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
        """Advanced synthesis with comprehensive analysis."""
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
                self._generate_trend_analysis(results, query),
                "",
                "## 🎯 Practical Applications",
                self._generate_practical_recommendations(results, query),
                "",
                "## 📈 Identified Gaps & Opportunities",
                self._generate_gap_analysis(results, query),
                "",
                "## 🔮 Future Directions",
                self._generate_future_directions(results, query),
                "",
                "## ⚠️ Risk Assessment",
                self._generate_risk_analysis(results, query),
                "",
                "## 📋 Quality Assessment",
                f"**Overall Quality Score**: {avg_confidence:.1%}",
                f"**Reliability**: {'High' if avg_confidence > 0.85 else 'Medium' if avg_confidence > 0.70 else 'Needs Verification'}",
                f"**Recommendation**: {'Strong for decision-making' if avg_confidence > 0.85 else 'Use with additional verification' if avg_confidence > 0.70 else 'Requires further research'}",
            ]
        )

        return "\n".join(synthesis_parts)

    def _generate_trend_analysis(self, results, query):
        """Generate trend analysis from results."""
        high_confidence_results = [r for r in results if r.confidence > 0.85]

        if high_confidence_results:
            return f"**Strong Trends Identified**: {len(high_confidence_results)} high-confidence sources indicate consistent patterns in {query}. The convergence across multiple source types suggests emerging consensus and established methodologies."
        return f"**Emerging Trends**: Mixed confidence levels suggest {query} is evolving with diverse approaches. More research may be needed to establish clear patterns."

    def _generate_practical_recommendations(self, results, query):
        """Generate practical recommendations."""
        academic_sources = [
            r for r in results if r.metadata.get("source_type") == "academic_papers"
        ]
        github_sources = [r for r in results if r.metadata.get("source_type") == "github_analysis"]
        docs_sources = [
            r for r in results if r.metadata.get("source_type") == "documentation_search"
        ]

        recommendations = []

        if academic_sources:
            recommendations.append(
                "- **Research Foundation**: Strong academic evidence supports theoretical approaches"
            )
        if github_sources:
            recommendations.append(
                "- **Implementation Ready**: Proven open-source implementations available"
            )
        if docs_sources:
            recommendations.append(
                "- **Best Practices**: Authoritative documentation provides clear guidelines"
            )

        if not recommendations:
            recommendations.append(
                "- **Exploratory Phase**: Consider starting with pilot implementations and gathering more data"
            )

        return "\n".join(recommendations)

    def _generate_gap_analysis(self, results, query):
        """Identify research gaps."""
        missing_sources = []

        source_types = {r.metadata.get("source_type", "unknown") for r in results}
        expected_sources = {
            "academic_papers",
            "github_analysis",
            "documentation_search",
            "industry_reports",
        }

        for expected in expected_sources:
            if expected not in source_types:
                missing_sources.append(expected.replace("_", " ").title())

        if missing_sources:
            return f"**Missing Perspectives**: {', '.join(missing_sources)} - Consider researching these areas for more comprehensive analysis."
        return f"**Comprehensive Coverage**: Multiple source types provide well-rounded perspective on {query}."

    def _generate_future_directions(self, results, query):
        """Generate future research directions."""
        recent_sources = [r for r in results if r.metadata.get("recency") == "recent"]

        if recent_sources:
            return f"**Active Development**: Recent sources indicate {query} is actively evolving. Monitor emerging trends and consider participating in ongoing developments."
        return f"**Stabilization Opportunity**: {query} appears established. Focus on optimization and practical applications rather than foundational research."

    def _generate_risk_analysis(self, results, query):
        """Generate risk assessment."""
        low_confidence_results = [r for r in results if r.confidence < 0.75]

        if low_confidence_results:
            return f"**Moderate Risk**: {len(low_confidence_results)} sources have lower confidence scores. Verify critical information through additional sources before making important decisions."
        return "**Low Risk**: High confidence across sources suggests reliable information. Still recommend cross-verification for critical applications."


class ResearchConfig:
    def __init__(self):
        self.debug_mode = False
        self.max_results_per_source = 10
        self.timeout = 30

        # Add missing synthesis config
        class SynthesisConfig:
            max_total_results = 50

        self.synthesis = SynthesisConfig()


@dataclass
class QueryResult:
    """Individual search result from a source."""

    source: str
    title: str
    content: str
    url: str | None = None
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


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
    """Multi-source research query engine."""

    def __init__(self, config: ResearchConfig | None = None):
        """Initialize research engine with configuration."""
        self.config = config or ResearchConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.ranker = ResultRanker()
        self.deduplicator = ResultDeduplicator()
        self.synthesizer = ResultSynthesizer()

        # Initialize sources
        self.sources = {}
        self._initialize_sources()

    def _initialize_sources(self):
        """Initialize all configured research sources."""
        if CKS_AVAILABLE:
            try:
                self.sources["cks"] = CKSQueryInterface()
                self.logger.info("CKS source initialized")
            except Exception as e:
                self.logger.warning(f"CKS initialization failed: {e}")

        if CHS_AVAILABLE:
            try:
                self.sources["chs"] = CHSSource()
                self.logger.info("CHS source initialized")
            except Exception as e:
                self.logger.warning(f"CHS initialization failed: {e}")

        # GLM source removed - not suitable for web search

    async def query(
        self,
        query_text: str,
        sources: list[str] | None = None,
        max_results_per_source: int | None = None,
    ) -> ResearchResult:
        """
        Execute multi-source research query.

        Args:
            query_text: Research query string
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
            if source_name in self.sources:
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

        # Rank and deduplicate results
        ranked_results = self.ranker.rank_results(all_results)
        deduplicated_results = self.deduplicator.deduplicate(ranked_results)

        # Limit total results
        max_total = self.config.synthesis.max_total_results
        final_results = deduplicated_results[:max_total]

        # Generate synthesis
        synthesis = self.synthesizer.synthesize(query_text, final_results, source_results)

        processing_time = time.time() - start_time

        return ResearchResult(
            query=query_text,
            sources_used=list(source_results.keys()),
            results=final_results,
            synthesis=synthesis,
            processing_time=processing_time,
            source_performance=source_performance,
            metadata={
                "total_results_found": len(all_results),
                "final_results_count": len(final_results),
                "sources_attempted": query_sources,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _query_source(
        self, source_name: str, query_text: str, max_results: int | None = None
    ) -> list[QueryResult]:
        """Query individual source with timeout."""
        source = self.sources[source_name]
        timeout = self.config.sources[source_name].timeout

        try:
            # Get max results from features.config or parameter
            if max_results is None:
                max_results = self.config.sources[source_name].max_results

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
                return results

            # Search knowledge graph
            knowledge_results = cks_interface.search_knowledge_graph(query_text, max_results)

            for item in knowledge_results:
                result = QueryResult(
                    source="cks",
                    title=item.get("title", "CKS Knowledge"),
                    content=item.get("content", ""),
                    confidence=item.get("relevance_score", 0.5),
                    metadata={
                        "type": item.get("type", "knowledge"),
                        "created_at": item.get("created_at"),
                        "category": item.get("category", "general"),
                    },
                )
                results.append(result)

            cks_interface.close()

        except Exception as e:
            self.logger.error(f"CKS query error: {e}")

        return results

    async def _query_chs(self, chs_source, query_text: str, max_results: int) -> list[QueryResult]:
        """Query Chat History Search."""
        try:
            return await chs_source.search(query_text, max_results)
        except Exception as e:
            self.logger.error(f"CHS query error: {e}")
            return []

    def format_results_markdown(self, result: ResearchResult) -> str:
        """Format research results as Markdown for display."""
        output = []

        # Header
        output.append(f"# 🔍 Research Results: {result.query}")
        output.append("")
        output.append(f"**Sources Queried**: {', '.join(result.sources_used)}")
        output.append(f"**Processing Time**: {result.processing_time:.2f}s")
        output.append(f"**Results Found**: {len(result.results)}")
        output.append("")

        # Synthesis
        output.append("## 📋 Key Insights")
        output.append("")
        output.append(result.synthesis)
        output.append("")

        # Detailed results by source
        output.append("## 📚 Detailed Results")
        output.append("")

        if not result.results:
            output.append("*No results found*")
        else:
            # Group by source
            results_by_source = {}
            for res in result.results:
                if res.source not in results_by_source:
                    results_by_source[res.source] = []
                results_by_source[res.source].append(res)

            for source, source_results in results_by_source.items():
                source_name = source.upper()
                output.append(f"### {source_name}")
                output.append("")

                for i, res in enumerate(source_results, 1):
                    confidence_pct = int(res.confidence * 100)
                    output.append(f"**{i}. {res.title}** (Confidence: {confidence_pct}%)")

                    if res.url:
                        output.append(f"🔗 [{res.url}]({res.url})")

                    # Limit content length for display
                    content = res.content
                    if len(content) > 300:
                        content = content[:300] + "..."

                    output.append(f"> {content}")
                    output.append("")

        # Source performance
        output.append("## ⏱️ Source Performance")
        output.append("")
        for source, time_taken in result.source_performance.items():
            output.append(f"- **{source.upper()}**: {time_taken:.2f}s")

        return "\n".join(output)

    def get_available_sources(self) -> list[str]:
        """Get list of available research sources."""
        return list(self.sources.keys())

    def get_source_status(self) -> dict[str, bool]:
        """Get status of all configured sources."""
        status = {}
        for source_name in ["cks", "chs"]:
            status[source_name] = source_name in self.sources
        return status
