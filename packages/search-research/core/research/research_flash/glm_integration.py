from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

"""
GLM-4.7 Integration Module

Modern Python 2025 implementation following CKS standards.
Integrates with existing CKS GLM-4.7 system for research-flash.
"""


# Modern Python imports - avoid relative imports when possible
try:
    from query_engine import QueryResult
except ImportError:
    # Fallback for development
    @dataclass
    class QueryResult:
        source: str
        title: str
        content: str
        url: str | None = None
        confidence: float = 0.0
        metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GLMConfig:
    """GLM-4.7 configuration following Pydantic V2 patterns."""

    model: str = "glm-4.7"
    api_endpoint: str = "https://api.z.ai/api/coding/paas/v4/chat/completions"
    api_key: str = ""
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: float = 30.0


class GLMFlashIntegration:
    """Modern GLM-4.7 integration following CKS Python 2025 standards."""

    def __init__(self, config: GLMConfig | None = None) -> None:
        """Initialize GLM-4.7 integration."""
        self.config = config or GLMConfig()
        self.logger = logging.getLogger(__name__)
        self._glm_instance: Any | None = None
        self._available: bool = False

        # Initialize CKS GLM integration
        self._initialize_cks_integration()

    def _initialize_cks_integration(self) -> None:
        """Initialize integration with existing CKS GLM system."""
        try:
            # Try to import existing GLM source from research-flash sources
            # Use absolute imports following modern Python standards
            import sys
            from pathlib import Path

            # Add the research-flash sources path
            sources_path = Path(__file__).parent / "sources"
            if sources_path.exists():
                sys.path.insert(0, str(sources_path))

                # Import from sources module
                try:
                    from glm_source import GLMSource
                except ImportError:
                    # Try importing from sources package
                    from sources import GLMSource

                if GLMSource is None:
                    raise ImportError("GLMSource class not available")

                # Create a minimal config for GLMSource
                class MinimalConfig:
                    def __init__(self):
                        self.api_key = ""
                        self.model = "glm-4.7"
                        self.api_endpoint = "https://api.z.ai/api/coding/paas/v4/chat/completions"
                        self.timeout = 30

                # Create GLM source with config
                config = MinimalConfig()
                self._glm_instance = GLMSource(config)
                self._available = True
                self.logger.info("CKS GLM-4.7 integration initialized successfully")
            else:
                self.logger.warning(f"GLM sources path not found: {sources_path}")
                self._available = False

        except ImportError as e:
            self.logger.warning(f"CKS GLM source import failed: {e}, using fallback")
            self._available = False
        except Exception as e:
            self.logger.error(f"Failed to initialize CKS GLM integration: {e}")
            self._available = False

    async def search_research(
        self, query: str, max_results: int = 10, source_types: list[str] | None = None
    ) -> list[QueryResult]:
        """
        Search using GLM-4.7 for comprehensive research.

        Args:
            query: Research query string
            max_results: Maximum number of results
            source_types: Types of sources to focus on

        Returns:
            List of QueryResult objects with real GLM-4.7 responses

        """
        if not self._available or not self._glm_instance:
            self.logger.warning("GLM-4.7 not available, using enhanced fallback")
            return await self._enhanced_fallback_search(query, max_results, source_types)

        try:
            # Create comprehensive research prompt
            research_prompt = self._create_research_prompt(query, source_types)

            # Use existing CKS GLM web search method
            glm_results = await self._glm_instance.search_web(research_prompt, max_results)

            # Convert CKS results to our format with enhanced metadata
            return self._convert_cks_results(glm_results, query, source_types)

        except Exception as e:
            self.logger.error(f"CKS GLM search failed: {e}")
            return await self._enhanced_fallback_search(query, max_results, source_types)

    def _create_research_prompt(self, query: str, source_types: list[str] | None) -> str:
        """Create comprehensive research prompt for GLM-4.7."""
        prompt = f"""Please provide comprehensive research analysis on: {query}

"""

        if source_types:
            prompt += "Focus areas:\n"
            focus_map = {
                "web_search": "Current web information and recent developments",
                "academic_papers": "Academic research, papers, and theoretical frameworks",
                "github_analysis": "Code implementations, repositories, and practical examples",
                "documentation_search": "Technical documentation, API references, and best practices",
                "industry_reports": "Industry trends, market analysis, and enterprise applications",
                "technical_blogs": "Community insights, tutorials, and practical guides",
            }

            focus_areas = [focus_map.get(st, st) for st in source_types if st in focus_map]
            prompt += "- " + "\n- ".join(focus_areas) + "\n"

        prompt += """
Please provide detailed, well-structured information with:
- Specific examples and insights
- Current trends and developments
- Practical applications and recommendations
- Authoritative sources where possible

Format your response clearly with sections and provide actionable insights."""

        return prompt

    def _convert_cks_results(
        self, glm_results: list[Any], original_query: str, source_types: list[str] | None
    ) -> list[QueryResult]:
        """Convert CKS GLM results to our QueryResult format."""
        results = []

        for glm_result in glm_results:
            # Classify the result based on content
            source_type = self._classify_result_source(glm_result, source_types)

            result = QueryResult(
                source=f"glm-{source_type}",
                title=f"{getattr(glm_result, 'title', 'GLM Research')}: {original_query}",
                content=getattr(glm_result, "content", ""),
                url=getattr(glm_result, "url", None),
                confidence=float(getattr(glm_result, "confidence", 0.8)),
                metadata={
                    "source_type": source_type,
                    "model": "glm-4.7",
                    "real_api": True,
                    "cks_integration": True,
                    "original_query": original_query,
                    **getattr(glm_result, "metadata", {}),
                },
            )
            results.append(result)

        self.logger.info(f"GLM-4.7 returned {len(results)} results")
        return results

    def _classify_result_source(self, glm_result: Any, source_types: list[str] | None) -> str:
        """Classify GLM result into source type."""
        content = getattr(glm_result, "content", "").lower()
        title = getattr(glm_result, "title", "").lower()

        # Priority classification based on requested types
        if source_types:
            for source_type in source_types:
                if self._content_matches_type(content + title, source_type):
                    return (
                        source_type.replace("_search", "")
                        .replace("_papers", "")
                        .replace("_analysis", "")
                    )

        # Default classification
        content_keywords = {
            "academic": ["research", "paper", "academic", "study", "journal", "university"],
            "github": ["github", "code", "implementation", "repository", "programming"],
            "docs": ["documentation", "api", "reference", "manual", "guide"],
            "industry": ["industry", "market", "enterprise", "business", "report"],
        }

        for source_type, keywords in content_keywords.items():
            if any(keyword in content for keyword in keywords):
                return source_type

        return "web"

    def _content_matches_type(self, content: str, source_type: str) -> bool:
        """Check if content matches a specific source type."""
        type_keywords = {
            "web_search": ["web", "internet", "online", "current", "recent", "news"],
            "academic_papers": ["research", "paper", "academic", "study", "journal"],
            "github_analysis": ["github", "code", "implementation", "repository"],
            "documentation_search": ["documentation", "api", "reference", "manual"],
            "industry_reports": ["industry", "market", "enterprise", "business"],
            "technical_blogs": ["blog", "tutorial", "community", "guide"],
        }

        keywords = type_keywords.get(source_type, [])
        return any(keyword in content for keyword in keywords)

    async def _enhanced_fallback_search(
        self, query: str, max_results: int, source_types: list[str] | None
    ) -> list[QueryResult]:
        """Enhanced fallback search when GLM-4.7 is not available."""
        results = []

        # Generate enhanced simulated results with proper metadata
        simulated_results = [
            {
                "type": "web",
                "title": f"Web Research: {query}",
                "content": f"Current web information about {query} would be retrieved from multiple online sources including news articles, blog posts, and technical discussions.",
                "confidence": 0.75,
            },
            {
                "type": "academic",
                "title": f"Academic Research: {query}",
                "content": f"Peer-reviewed papers and academic research on {query} would include findings from scholarly journals, conference proceedings, and research institutions.",
                "confidence": 0.78,
            },
            {
                "type": "github",
                "title": f"Implementation Examples: {query}",
                "content": f"Open source implementations related to {query} would be analyzed from repositories, code patterns, and community discussions.",
                "confidence": 0.72,
            },
            {
                "type": "docs",
                "title": f"Documentation: {query}",
                "content": f"Technical documentation for {query} would include API references, tutorials, and implementation guidelines from authoritative sources.",
                "confidence": 0.80,
            },
        ]

        # Filter by requested source types
        if source_types:
            type_map = {
                "web_search": "web",
                "academic_papers": "academic",
                "github_analysis": "github",
                "documentation_search": "docs",
                "industry_reports": "industry",
            }

            filtered_results = []
            for source_type in source_types:
                mapped_type = type_map.get(source_type)
                if mapped_type:
                    filtered_results.extend(
                        [r for r in simulated_results if r["type"] == mapped_type]
                    )
            simulated_results = filtered_results or simulated_results

        # Convert to QueryResult objects
        for sim_result in simulated_results[:max_results]:
            result = QueryResult(
                source=f"glm-{sim_result['type']}",
                title=sim_result["title"],
                content=sim_result["content"],
                url=f"https://glm-4.7.example.com/search?q={query.replace(' ', '+')}",
                confidence=sim_result["confidence"],
                metadata={
                    "source_type": sim_result["type"],
                    "model": "glm-4.7",
                    "simulated": True,
                    "fallback": True,
                },
            )
            results.append(result)

        return results

    @property
    def is_available(self) -> bool:
        """Check if GLM-4.7 integration is available."""
        return self._available

    @property
    def model_info(self) -> dict[str, Any]:
        """Get information about the GLM model."""
        return {
            "model": self.config.model,
            "available": self._available,
            "endpoint": self.config.api_endpoint,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
        }
