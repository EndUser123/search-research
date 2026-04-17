from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from modules.knowledge_system.agent_interface import EnhancedAgentInterface

from ..utils.logging_utils import setup_logging

"""CKS Knowledge Base Integration.

Integration layer for the CSF Knowledge System (CKS) to leverage
proven solution patterns and repository knowledge for fix suggestions.

CKS Capabilities:
- Solution Discovery: Find existing solutions for similar problems
- Pattern Matching: Identify relevant coding patterns and best practices
- Knowledge Retrieval: Access curated knowledge base of solutions
- Learning Integration: Store and retrieve successful fix patterns
- Expert Recommendations: Get advice from domain expert patterns

Integration Features:
- Pattern Search: Search for relevant solution patterns
- Solution Discovery: Find existing implementations for similar issues
- Best Practice Retrieval: Get proven best practices for specific scenarios
- Knowledge Storage: Store successful fix patterns for future use
- Expert Insights: Access domain expert recommendations
"""


# Add project root to path BEFORE any imports
project_root = Path(__file__).parent.parent.parent.parent.parent


class CKSSearchType(Enum):
    """Types of CKS searches."""

    SOLUTION_PATTERNS = "solution_patterns"
    BEST_PRACTICES = "best_practices"
    ISSUE_INSIGHTS = "issue_insights"
    DOMAIN_KNOWLEDGE = "domain_knowledge"
    EXPERT_RECOMMENDATIONS = "expert_recommendations"
    SIMILAR_IMPLEMENTATIONS = "similar_implementations"


@dataclass
class CKSSearchRequest:
    """Request for CKS knowledge search."""

    search_type: CKSSearchType
    query: str
    context: dict[str, Any] = field(default_factory=dict)
    filters: dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    include_metadata: bool = True


@dataclass
class CKSSearchResult:
    """Result from CKS knowledge search."""

    success: bool
    patterns: list[dict[str, Any]]
    total_found: int
    search_time: float
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    error_message: str | None = None


class CKSIntegration:
    """Integration layer for CKS knowledge system.

    Attributes
    ----------
        logger: Structured logger for debugging and monitoring
        agent_interface: CKS agent interface for knowledge access
        cache: Search result cache for improved performance
        statistics: Usage and performance statistics

    Performance Metrics:
        - Search time: <1 second average for pattern searches
        - Cache hit rate: >70% for repeated searches
        - Pattern relevance: >80% relevance for top 5 results
        - Success rate: >95% for valid search requests

    """

    def __init__(self, log_level: str = "INFO") -> None:
        """Initialize CKS Integration.

        Args:
        ----
            log_level: Logging level for debugging

        """
        self.logger = setup_logging("CKSIntegration", log_level)

        # Initialize CKS agent interface
        try:
            self.agent_interface = EnhancedAgentInterface()
            self.cks_available = True
            self.logger.info("CKS system successfully initialized")
        except Exception as e:
            self.logger.exception(f"Failed to initialize CKS system: {e}")
            self.agent_interface = None
            self.cks_available = False

        # Initialize cache and statistics
        self.search_cache: dict[str, CKSSearchResult] = {}
        self.statistics = {
            "total_searches": 0,
            "successful_searches": 0,
            "cache_hits": 0,
            "average_search_time": 0.0,
            "patterns_found": 0,
            "searches_by_type": {},
        }

    async def search_solution_patterns(
        self,
        fix_type: Any,
        language: str,
        domain: str,
    ) -> list[dict[str, Any]]:
        """Search for solution patterns relevant to fix type and domain.

        Args:
        ----
            fix_type: Type of fix to search for
            language: Programming language
            domain: Technical domain (backend, frontend, etc.)

        Returns:
        -------
            List of relevant solution patterns

        Raises:
        ------
            RuntimeError: If CKS system is not available

        """
        if not self.cks_available:
            raise RuntimeError("CKS system not available for pattern search")

        search_request = CKSSearchRequest(
            search_type=CKSSearchType.SOLUTION_PATTERNS,
            query=f"{fix_type} {language} {domain}",
            context={
                "fix_type": str(fix_type),
                "language": language,
                "domain": domain,
            },
            filters={
                "language": language,
                "domain": domain,
                "pattern_type": "solution",
            },
            limit=10,
        )

        search_result = await self._execute_search(search_request)

        if search_result.success:
            return search_result.patterns
        self.logger.error(
            f"CKS solution pattern search failed: {search_result.error_message}",
        )
        return []

    async def get_issue_insights(self, context: Any) -> dict[str, Any]:
        """Get insights about specific issue from CKS knowledge base.

        Args:
        ----
            context: Issue context with description and code

        Returns:
        -------
            Issue insights and recommendations

        Raises:
        ------
            RuntimeError: If CKS system is not available

        """
        if not self.cks_available:
            raise RuntimeError("CKS system not available for issue insights")

        issue_description = getattr(context, "issue_description", "")
        affected_code = getattr(context, "affected_code", "")

        search_request = CKSSearchRequest(
            search_type=CKSSearchType.ISSUE_INSIGHTS,
            query=issue_description,
            context={
                "issue_description": issue_description,
                "code_sample": affected_code[:500],  # Limit code sample
                "file_path": getattr(context, "file_path", ""),
            },
            limit=5,
        )

        search_result = await self._execute_search(search_request)

        if search_result.success:
            return {
                "insights": search_result.patterns,
                "recommendations": search_result.suggestions,
                "confidence": search_result.confidence,
                "related_patterns": search_result.metadata.get("related_patterns", []),
            }
        self.logger.error(
            f"CKS issue insights search failed: {search_result.error_message}",
        )
        return {"error": search_result.error_message, "fallback_insights": True}

    async def search_best_practices(
        self,
        language: str,
        domain: str,
        topic: str,
    ) -> list[dict[str, Any]]:
        """Search for best practices specific to language, domain, and topic.

        Args:
        ----
            language: Programming language
            domain: Technical domain
            topic: Specific topic or concern

        Returns:
        -------
            List of best practice patterns

        Raises:
        ------
            RuntimeError: If CKS system is not available

        """
        if not self.cks_available:
            raise RuntimeError("CKS system not available for best practice search")

        search_request = CKSSearchRequest(
            search_type=CKSSearchType.BEST_PRACTICES,
            query=f"best practices {language} {domain} {topic}",
            context={
                "language": language,
                "domain": domain,
                "topic": topic,
            },
            filters={
                "pattern_type": "best_practice",
                "language": language,
            },
            limit=8,
        )

        search_result = await self._execute_search(search_request)

        if search_result.success:
            return search_result.patterns
        self.logger.error(
            f"CKS best practice search failed: {search_result.error_message}",
        )
        return []

    async def find_similar_implementations(
        self,
        code: str,
        language: str,
    ) -> list[dict[str, Any]]:
        """Find similar implementations in the knowledge base.

        Args:
        ----
            code: Code to find similar implementations for
            language: Programming language

        Returns:
        -------
            List of similar implementations

        Raises:
        ------
            RuntimeError: If CKS system is not available

        """
        if not self.cks_available:
            raise RuntimeError("CKS system not available for similarity search")

        # Extract key features from code for similarity matching
        code_features = self._extract_code_features(code)

        search_request = CKSSearchRequest(
            search_type=CKSSearchType.SIMILAR_IMPLEMENTATIONS,
            query=f"similar implementation {language}",
            context={
                "code_features": code_features,
                "language": language,
                "code_sample": code[:200],  # Limit code sample
            },
            filters={
                "language": language,
                "pattern_type": "implementation",
            },
            limit=6,
        )

        search_result = await self._execute_search(search_request)

        if search_result.success:
            return search_result.patterns
        self.logger.error(
            f"CKS similarity search failed: {search_result.error_message}",
        )
        return []

    async def get_expert_recommendations(
        self,
        issue_type: str,
        domain: str,
    ) -> list[dict[str, Any]]:
        """Get expert recommendations for specific issue type and domain.

        Args:
        ----
            issue_type: Type of issue
            domain: Technical domain

        Returns:
        -------
            List of expert recommendations

        Raises:
        ------
            RuntimeError: If CKS system is not available

        """
        if not self.cks_available:
            raise RuntimeError("CKS system not available for expert recommendations")

        search_request = CKSSearchRequest(
            search_type=CKSSearchType.EXPERT_RECOMMENDATIONS,
            query=f"expert recommendation {issue_type} {domain}",
            context={
                "issue_type": issue_type,
                "domain": domain,
            },
            filters={
                "pattern_type": "expert_recommendation",
                "domain": domain,
            },
            limit=5,
        )

        search_result = await self._execute_search(search_request)

        if search_result.success:
            return search_result.patterns
        self.logger.error(
            f"CKS expert recommendation search failed: {search_result.error_message}",
        )
        return []

    async def store_fix_pattern(self, fix_pattern: dict[str, Any]) -> bool:
        """Store successful fix pattern in CKS knowledge base.

        Args:
        ----
            fix_pattern: Fix pattern to store

        Returns:
        -------
            True if stored successfully, False otherwise

        """
        if not self.cks_available:
            self.logger.warning("CKS system not available - cannot store fix pattern")
            return False

        try:
            # Add pattern to CKS knowledge base
            result = self.agent_interface.add_pattern(
                title=fix_pattern.get("title", "Unnamed Fix Pattern"),
                description=fix_pattern.get("description", ""),
                evidence=fix_pattern.get("evidence", ""),
                code_example=fix_pattern.get("code_example", ""),
                tags=fix_pattern.get("tags", []),
                agent_attribution="automated_fix_suggestions",
            )

            if result.get("success", False):
                self.logger.info(
                    f"Successfully stored fix pattern: {fix_pattern.get('title', 'Unknown')}",
                )
                return True
            self.logger.error(
                f"Failed to store fix pattern: {result.get('error', 'Unknown error')}",
            )
            return False

        except Exception as e:
            self.logger.exception(f"Error storing fix pattern: {e}")
            return False

    async def _execute_search(self, request: CKSSearchRequest) -> CKSSearchResult:
        """Execute search request against CKS system.

        Args:
        ----
            request: Search request to execute

        Returns:
        -------
            Search result with patterns and metadata

        Raises:
        ------
            RuntimeError: If CKS system is not available

        """
        start_time = time.time()

        # Check cache first
        cache_key = self._generate_cache_key(request)
        if cache_key in self.search_cache:
            cached_result = self.search_cache[cache_key]
            self.statistics["cache_hits"] += 1
            self.logger.debug(f"Cache hit for {request.search_type.value} search")
            return cached_result

        if not self.cks_available:
            raise RuntimeError("CKS system not available for search execution")

        try:
            self.logger.debug(f"Executing CKS search: {request.search_type.value}")

            # Use agent interface for natural language search
            patterns = self.agent_interface.natural_search(
                query=request.query,
                limit=request.limit,
            )

            # Filter and process results based on search type and context
            filtered_patterns = self._filter_patterns(patterns, request)

            search_time = time.time() - start_time

            result = CKSSearchResult(
                success=True,
                patterns=filtered_patterns,
                total_found=len(patterns),
                search_time=search_time,
                confidence=self._calculate_search_confidence(
                    filtered_patterns,
                    request,
                ),
                metadata=self._generate_search_metadata(request, filtered_patterns),
                suggestions=self._generate_search_suggestions(
                    filtered_patterns,
                    request,
                ),
            )

            # Cache successful results
            self.search_cache[cache_key] = result
            self._update_search_statistics(
                request,
                True,
                search_time,
                len(filtered_patterns),
            )

            self.logger.debug(
                f"CKS search completed in {search_time:.2f}s, found {len(filtered_patterns)} patterns",
            )
            return result

        except Exception as e:
            search_time = time.time() - start_time
            self.logger.exception(f"CKS search failed: {e}")

            result = CKSSearchResult(
                success=False,
                patterns=[],
                total_found=0,
                search_time=search_time,
                confidence=0.0,
                error_message=str(e),
            )

            self._update_search_statistics(request, False, search_time, 0)
            return result

    def _extract_code_features(self, code: str) -> dict[str, Any]:
        """Extract key features from code for similarity matching.

        Args:
        ----
            code: Code to analyze

        Returns:
        -------
            Dictionary of code features

        """
        features = {
            "keywords": [],
            "imports": [],
            "functions": [],
            "classes": [],
            "complexity_indicators": [],
        }

        lines = code.split("\n")
        for line in lines:
            stripped = line.strip()

            # Extract keywords
            python_keywords = [
                "def",
                "class",
                "if",
                "for",
                "while",
                "try",
                "except",
                "with",
            ]
            for keyword in python_keywords:
                if stripped.startswith(keyword + " "):
                    features["keywords"].append(keyword)

            # Extract imports
            if stripped.startswith(("import ", "from ")):
                features["imports"].append(stripped)

            # Extract function definitions
            if stripped.startswith("def "):
                func_name = stripped.split("(")[0].replace("def ", "").strip()
                features["functions"].append(func_name)

            # Extract class definitions
            if stripped.startswith("class "):
                class_name = stripped.split("(")[0].replace("class ", "").strip()
                features["classes"].append(class_name)

        # Complexity indicators
        if len(lines) > 50:
            features["complexity_indicators"].append("long_file")
        if len(features["functions"]) > 10:
            features["complexity_indicators"].append("many_functions")
        if len(features["classes"]) > 5:
            features["complexity_indicators"].append("many_classes")

        return features

    def _filter_patterns(
        self,
        patterns: list[dict[str, Any]],
        request: CKSSearchRequest,
    ) -> list[dict[str, Any]]:
        """Filter patterns based on request criteria.

        Args:
        ----
            patterns: Raw patterns from CKS
            request: Search request with filters

        Returns:
        -------
            Filtered list of patterns

        """
        filtered_patterns = []

        for pattern in patterns:
            # Apply language filter
            if "language" in request.filters:
                pattern_language = pattern.get("language", "").lower()
                filter_language = request.filters["language"].lower()
                if pattern_language and filter_language not in pattern_language:
                    continue

            # Apply domain filter
            if "domain" in request.filters:
                pattern_domain = pattern.get("domain", "").lower()
                filter_domain = request.filters["domain"].lower()
                if pattern_domain and filter_domain not in pattern_domain:
                    continue

            # Apply pattern type filter
            if "pattern_type" in request.filters:
                pattern_type = pattern.get("type", "").lower()
                filter_type = request.filters["pattern_type"].lower()
                if pattern_type and filter_type not in pattern_type:
                    continue

            # Filter by relevance score
            relevance = pattern.get("relevance", 0.0)
            if relevance < 0.5:  # Minimum relevance threshold
                continue

            filtered_patterns.append(pattern)

        return filtered_patterns[: request.limit]

    def _calculate_search_confidence(
        self,
        patterns: list[dict[str, Any]],
        request: CKSSearchRequest,
    ) -> float:
        """Calculate confidence score for search results.

        Args:
        ----
            patterns: Search results
            request: Original search request

        Returns:
        -------
            Confidence score between 0.0 and 1.0

        """
        if not patterns:
            return 0.0

        # Base confidence from pattern quality
        avg_relevance = sum(p.get("relevance", 0.0) for p in patterns) / len(patterns)
        avg_confidence = sum(p.get("confidence", 0.0) for p in patterns) / len(patterns)

        # Combine metrics
        confidence = (avg_relevance + avg_confidence) / 2

        # Adjust based on number of results
        result_factor = min(1.0, len(patterns) / 5.0)  # Prefer more results up to 5

        return max(0.0, min(1.0, confidence * 0.8 + result_factor * 0.2))

    def _generate_search_metadata(
        self,
        request: CKSSearchRequest,
        patterns: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate metadata for search result.

        Args:
        ----
            request: Original search request
            patterns: Search results

        Returns:
        -------
            Metadata dictionary

        """
        return {
            "search_timestamp": datetime.now().isoformat(),
            "search_type": request.search_type.value,
            "query": request.query,
            "total_candidates": len(patterns),
            "filters_applied": bool(request.filters),
            "language_distribution": self._analyze_language_distribution(patterns),
            "confidence_distribution": self._analyze_confidence_distribution(patterns),
        }

    def _generate_search_suggestions(
        self,
        patterns: list[dict[str, Any]],
        request: CKSSearchRequest,
    ) -> list[str]:
        """Generate search suggestions based on results.

        Args:
        ----
            patterns: Search results
            request: Original search request

        Returns:
        -------
            List of suggestions

        """
        suggestions = []

        if not patterns:
            suggestions.append("Try broadening your search with more general terms")
            suggestions.append("Check for alternative keywords or synonyms")
            return suggestions

        # Suggest related searches
        tags = set()
        for pattern in patterns:
            pattern_tags = pattern.get("tags", [])
            tags.update(pattern_tags)

        if tags:
            top_tags = list(tags)[:3]
            suggestions.append(f"Related topics: {', '.join(top_tags)}")

        # Suggest different search types
        if request.search_type == CKSSearchType.SOLUTION_PATTERNS:
            suggestions.append("Consider searching for best practices for this domain")
        elif request.search_type == CKSSearchType.ISSUE_INSIGHTS:
            suggestions.append("Look for expert recommendations on this issue type")

        return suggestions[:3]  # Limit to top 3 suggestions

    def _analyze_language_distribution(
        self,
        patterns: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Analyze language distribution in patterns.

        Args:
        ----
            patterns: Search results

        Returns:
        -------
            Language distribution dictionary

        """
        distribution = {}
        for pattern in patterns:
            language = pattern.get("language", "unknown")
            distribution[language] = distribution.get(language, 0) + 1
        return distribution

    def _analyze_confidence_distribution(
        self,
        patterns: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Analyze confidence distribution in patterns.

        Args:
        ----
            patterns: Search results

        Returns:
        -------
            Confidence distribution dictionary

        """
        distribution = {"high": 0, "medium": 0, "low": 0}
        for pattern in patterns:
            confidence = pattern.get("confidence", 0.0)
            if confidence >= 0.8:
                distribution["high"] += 1
            elif confidence >= 0.6:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        return distribution

    def _generate_cache_key(self, request: CKSSearchRequest) -> str:
        """Generate cache key for search request.

        Args:
        ----
            request: Search request

        Returns:
        -------
            Cache key string

        """
        import hashlib

        key_data = {
            "search_type": request.search_type.value,
            "query": request.query,
            "filters": request.filters,
            "limit": request.limit,
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _update_search_statistics(
        self,
        request: CKSSearchRequest,
        success: bool,
        search_time: float,
        patterns_found: int,
    ) -> None:
        """Update search statistics.

        Args:
        ----
            request: Search request
            success: Whether search was successful
            search_time: Search processing time
            patterns_found: Number of patterns found

        """
        self.statistics["total_searches"] += 1

        if success:
            self.statistics["successful_searches"] += 1
            self.statistics["patterns_found"] += patterns_found

        # Update average search time
        total_time = (
            self.statistics["average_search_time"] * (self.statistics["total_searches"] - 1)
            + search_time
        )
        self.statistics["average_search_time"] = total_time / self.statistics["total_searches"]

        # Update search type statistics
        search_type = request.search_type.value
        self.statistics["searches_by_type"][search_type] = (
            self.statistics["searches_by_type"].get(search_type, 0) + 1
        )

    def get_statistics(self) -> dict[str, Any]:
        """Get search and usage statistics.

        Returns
        -------
            Statistics dictionary

        """
        stats = self.statistics.copy()

        if stats["total_searches"] > 0:
            stats["success_rate"] = stats["successful_searches"] / stats["total_searches"]
            stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_searches"]
            stats["avg_patterns_per_search"] = (
                stats["patterns_found"] / stats["successful_searches"]
                if stats["successful_searches"] > 0
                else 0
            )
        else:
            stats["success_rate"] = 0.0
            stats["cache_hit_rate"] = 0.0
            stats["avg_patterns_per_search"] = 0.0

        return stats

    def clear_cache(self) -> None:
        """Clear search cache."""
        self.search_cache.clear()
        self.logger.info("CKS search cache cleared")

    async def health_check(self) -> dict[str, Any]:
        """Perform health check on CKS integration.

        Returns
        -------
            Health status and diagnostics

        """
        health = {
            "cks_available": self.cks_available,
            "cache_size": len(self.search_cache),
            "statistics": self.get_statistics(),
        }

        # Test CKS system with simple search
        if self.cks_available and self.agent_interface:
            try:
                test_result = self.agent_interface.natural_search(
                    query="test search",
                    limit=1,
                )
                health["test_search"] = {
                    "success": True,
                    "results_found": len(test_result),
                }
            except Exception as e:
                health["test_search"] = {
                    "success": False,
                    "error": str(e),
                }

        health["status"] = (
            "healthy"
            if self.cks_available and health.get("test_search", {}).get("success", False)
            else "degraded"
        )
        return health
