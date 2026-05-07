"""HDMA Backend - Hybrid Dual-Map Architecture search.

Wraps HDMAAnalyzer from knowledge.analysis.hdma.analyzer for use in
unified search router. Provides query interface for architectural analysis
including components, dependencies, anti-patterns, and system health.

Query patterns supported:
- "components" - List all architectural components
- "dependencies for <component>" - Show dependencies for a component
- "anti-patterns" - Detect architectural anti-patterns
- "bottlenecks" - Find system bottlenecks
- "architectural issues" - Find critical architectural problems
- "system analysis" - Full system architecture overview
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

# Import the HDMAAnalyzer from the correct location
try:
    from knowledge.analysis.hdma.analyzer import (
        ArchitecturalAntiPattern,
        ArchitecturalComponent,
        ComponentRelationship,
        HDMAAnalyzer,
        IssueSeverity,
    )

    HDMA_AVAILABLE = True
except ImportError:
    HDMA_AVAILABLE = False
    HDMAAnalyzer = None  # type: ignore[misc, assignment]
    ArchitecturalComponent = None  # type: ignore[misc, assignment]
    ArchitecturalAntiPattern = None  # type: ignore[misc, assignment]
    ComponentRelationship = None  # type: ignore[misc, assignment]
    IssueSeverity = None  # type: ignore[misc, assignment]

from ...backend_health import BackendHealthRegistry

logger = logging.getLogger(__name__)


class HDMABackend:
    """
    Backend wrapper for HDMA architectural analysis.

    Provides search interface over HDMAAnalyzer with query
    parsing for components, dependencies, and anti-pattern detection.
    """

    BACKEND_NAME: str = "HDMA"

    def __init__(
        self,
        root_paths: list[str] | None = None,
        enable_health_tracking: bool = True,
    ) -> None:
        """Initialize HDMA backend.

        Args:
            root_paths: Root directories to analyze
            enable_health_tracking: Track backend health status
        """
        self._root_paths = root_paths or ["P:\\\\__csf/src"]
        self._enable_health = enable_health_tracking

        # HDMA analyzer and cached analysis result
        self._analyzer: Any = None
        self._analysis_result: Any = None
        self._analysis_initialized = False

        self._health: BackendHealthRegistry | None = (
            BackendHealthRegistry() if enable_health_tracking else None
        )

        if HDMA_AVAILABLE:
            self._initialize_analyzer()
        else:
            if self._health:
                self._health.record_result(
                    self.BACKEND_NAME,
                    success=False,
                    error="HDMAAnalyzer not available from knowledge.analysis.hdma.analyzer",
                )

    def _initialize_analyzer(self) -> None:
        """Initialize the HDMA analyzer (lazy loading)."""
        if not HDMA_AVAILABLE or HDMAAnalyzer is None:
            return

        try:
            # Create analyzer with the first root path
            primary_path = Path(self._root_paths[0]) if self._root_paths else Path("P:\\\\__csf/src")
            if not primary_path.exists():
                # Fallback to current directory
                primary_path = Path.cwd()

            # Try to create the analyzer - it may fail due to missing dependencies
            # (e.g., ASTAnalyzer is set to None in the hdma module)
            self._analyzer = HDMAAnalyzer(config={"performance_threshold_ms": 1000.0})
            self._primary_path = primary_path
            self._analysis_initialized = True

            if self._health:
                self._health.record_result(self.BACKEND_NAME, success=True)
        except TypeError as e:
            # HDMAAnalyzer has missing dependencies (ASTAnalyzer = None)
            # This is expected for the current state of the module
            logger.info(f"HDMA analyzer has missing dependencies: {e}")
            if self._health:
                self._health.record_result(
                    self.BACKEND_NAME,
                    success=False,
                    error="HDMAAnalyzer dependencies not available (ASTAnalyzer)",
                )
        except Exception as e:
            logger.warning(f"HDMA analyzer initialization failed: {e}")
            if self._health:
                self._health.record_result(
                    self.BACKEND_NAME,
                    success=False,
                    error=str(e),
                )

    def _ensure_analysis(self) -> bool:
        """Ensure HDMA analysis has been run. Returns True if successful."""
        if not self._analysis_initialized or self._analyzer is None:
            return False

        if self._analysis_result is not None:
            return True  # Already analyzed

        try:
            logger.info(f"Running HDMA analysis on {self._primary_path}")
            self._analysis_result = self._analyzer.analyze_system(self._primary_path)

            if self._health:
                self._health.record_result(self.BACKEND_NAME, success=True)
            return True
        except Exception as e:
            logger.warning(f"HDMA analysis failed: {e}")
            if self._health:
                self._health.record_result(
                    self.BACKEND_NAME,
                    success=False,
                    error=str(e),
                )
            return False

    def has_index(self) -> bool:
        """Check if HDMA analysis has been built."""
        return self._analysis_initialized and self._analyzer is not None

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search HDMA for matching patterns.

        Args:
            query: Search query (e.g., "components", "dependencies", "anti-patterns")
            limit: Maximum results to return

        Returns:
            List of search results with standardized format
        """
        if not self.has_index():
            return self._get_fallback_results(query, "HDMA backend not initialized")

        query_lower = query.lower().strip()

        # Ensure analysis is run
        if not self._ensure_analysis() or self._analysis_result is None:
            return self._get_fallback_results(
                query, "HDMA analysis not available - dependencies may be incomplete"
            )

        # Parse query pattern
        if "component" in query_lower:
            # List components
            return self._search_components(limit)
        elif "depend" in query_lower:
            # Dependencies
            target = self._extract_target(query, "depend")
            return self._search_dependencies(target, limit)
        elif (
            "anti-pattern" in query_lower
            or "antipattern" in query_lower
            or "architectural issue" in query_lower
        ):
            # Anti-patterns
            return self._search_anti_patterns(limit)
        elif "bottleneck" in query_lower:
            # Bottlenecks
            return self._search_bottlenecks(limit)
        elif "architecture" in query_lower or "system analysis" in query_lower:
            # Architecture overview
            return self._search_architecture_overview(limit)
        elif "recommendation" in query_lower:
            # Recommendations
            return self._search_recommendations(limit)
        elif "critical" in query_lower or "issue" in query_lower:
            # Critical issues
            return self._search_critical_issues(limit)
        else:
            # Default: search by component name
            return self._search_by_name(query, limit)

    def _get_fallback_results(self, query: str, reason: str) -> list[dict[str, Any]]:
        """Get fallback results when analysis is not available."""
        return [
            {
                "id": f"hdma_fallback_{hash(query)}",
                "source": self.BACKEND_NAME,
                "backend": self.BACKEND_NAME,
                "title": "HDMA Analysis Unavailable",
                "content": f"{reason}. Ensure knowledge.analysis.hdma.analyzer is properly installed.",
                "score": 0.3,
                "reason": "fallback",
                "metadata": {
                    "query": query,
                    "reason": reason,
                },
            }
        ]

    def _extract_target(self, query: str, prefix: str) -> str:
        """Extract target name from query string."""
        query_lower = query.lower()
        if prefix in query_lower:
            # Handle both "dependencies for X" and "dependencies X"
            for marker in ["dependencies for", "dependencies", "dependency for"]:
                if marker in query_lower:
                    return query_lower.replace(marker, "").strip()
        return query.strip()

    def _component_to_result(
        self,
        comp: ArchitecturalComponent,
        reason: str = "component",
    ) -> dict[str, Any]:
        """Convert ArchitecturalComponent to search result format."""
        return {
            "id": f"hdma_comp_{comp.name}",
            "source": self.BACKEND_NAME,
            "backend": self.BACKEND_NAME,
            "title": comp.name,
            "content": (
                f"{comp.name} ({comp.component_type.value}) - "
                f"complexity: {comp.complexity_score:.2f}, "
                f"coupling: {comp.coupling_score:.2f}"
            ),
            "score": 0.7 + (comp.stability_score * 0.2),
            "reason": reason,
            "metadata": {
                "file_path": comp.file_path,
                "line_number": comp.line_number,
                "component_type": comp.component_type.value,
                "complexity_score": comp.complexity_score,
                "coupling_score": comp.coupling_score,
                "cohesion_score": comp.cohesion_score,
                "stability_score": comp.stability_score,
                "functions": comp.functions[:10],  # Limit for metadata
                "classes": comp.classes[:10],
            },
        }

    def _anti_pattern_to_result(
        self,
        ap: ArchitecturalAntiPattern,
        reason: str = "anti-pattern",
    ) -> dict[str, Any]:
        """Convert ArchitecturalAntiPattern to search result format."""
        severity_map = {"CRITICAL": 1.0, "HIGH": 0.9, "MEDIUM": 0.7, "LOW": 0.5}
        return {
            "id": f"hdma_ap_{ap.pattern_name.lower().replace(' ', '_')}",
            "source": self.BACKEND_NAME,
            "backend": self.BACKEND_NAME,
            "title": ap.pattern_name,
            "content": (
                f"{ap.description}\n"
                f"Impact: {ap.impact_assessment}\n"
                f"Recommendation: {ap.recommendation}"
            ),
            "score": severity_map.get(
                ap.severity.value if hasattr(ap.severity, "value") else str(ap.severity), 0.7
            ),
            "reason": reason,
            "metadata": {
                "anti_pattern_type": ap.anti_pattern_type,
                "severity": ap.severity.value
                if hasattr(ap.severity, "value")
                else str(ap.severity),
                "components_affected": ap.components_affected,
                "structural_indicators": ap.structural_indicators[:5],
                "behavioral_indicators": ap.behavioral_indicators[:5],
                "confidence_score": ap.confidence_score,
            },
        }

    def _search_components(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        """List all architectural components."""
        if not self._analysis_result or not hasattr(self._analysis_result, "structural_map"):
            return []

        results = []
        structural = self._analysis_result.structural_map

        for name, comp in list(structural.components.items())[:limit]:
            results.append(self._component_to_result(comp, "architectural component"))

        return results

    def _search_dependencies(
        self,
        target: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find dependencies for a component or module."""
        if not self._analysis_result or not hasattr(self._analysis_result, "structural_map"):
            return []

        results = []
        structural = self._analysis_result.structural_map
        target_lower = target.lower()

        # Find matching component(s)
        for name, comp in structural.components.items():
            if target_lower in name.lower():
                # Get dependencies
                deps = structural.get_component_dependencies(name)
                for dep_name in deps[:limit]:
                    dep_comp = structural.components.get(dep_name)
                    if dep_comp:
                        results.append(
                            {
                                "id": f"hdma_dep_{name}_{dep_name}",
                                "source": self.BACKEND_NAME,
                                "backend": self.BACKEND_NAME,
                                "title": f"{name} → {dep_name}",
                                "content": f"{name} depends on {dep_name} ({dep_comp.component_type.value})",
                                "score": 0.7,
                                "reason": f"dependency for {name}",
                                "metadata": {
                                    "source": name,
                                    "target": dep_name,
                                    "target_type": dep_comp.component_type.value,
                                },
                            }
                        )

        return results[:limit]

    def _search_anti_patterns(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Detect architectural anti-patterns."""
        if not self._analysis_result or not hasattr(self._analysis_result, "anti_patterns"):
            return []

        results = []
        anti_patterns = self._analysis_result.anti_patterns

        # Sort by severity (CRITICAL first)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_patterns = sorted(
            anti_patterns,
            key=lambda ap: severity_order.get(
                ap.severity.value if hasattr(ap.severity, "value") else str(ap.severity), 99
            ),
        )

        for ap in sorted_patterns[:limit]:
            results.append(self._anti_pattern_to_result(ap, "architectural anti-pattern"))

        return results

    def _search_bottlenecks(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Find system bottlenecks from behavioral analysis."""
        if not self._analysis_result or not hasattr(self._analysis_result, "behavioral_map"):
            return []

        results = []
        behavioral = self._analysis_result.behavioral_map

        # Get performance bottlenecks
        bottlenecks = behavioral.get_performance_bottlenecks(threshold_ms=1000.0)

        for pattern in bottlenecks[:limit]:
            results.append(
                {
                    "id": f"hdma_bn_{hash(pattern.pattern_type)}",
                    "source": self.BACKEND_NAME,
                    "backend": self.BACKEND_NAME,
                    "title": f"{pattern.pattern_type.value} bottleneck",
                    "content": (
                        f"Performance issue: {pattern.duration_ms:.0f}ms duration, "
                        f"success rate: {pattern.success_rate:.1%}"
                    ),
                    "score": 0.8,
                    "reason": "performance bottleneck",
                    "metadata": {
                        "pattern_type": pattern.pattern_type.value,
                        "duration_ms": pattern.duration_ms,
                        "success_rate": pattern.success_rate,
                        "components_involved": pattern.components_involved,
                        "frequency": pattern.frequency,
                    },
                }
            )

        return results

    def _search_architecture_overview(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Get architecture overview with system metrics."""
        if not self._analysis_result:
            return []

        result = self._analysis_result
        structural = result.structural_map if hasattr(result, "structural_map") else None
        behavioral = result.behavioral_map if hasattr(result, "behavioral_map") else None

        overview_result = {
            "id": "hdma_arch_overview",
            "source": self.BACKEND_NAME,
            "backend": self.BACKEND_NAME,
            "title": "System Architecture Overview",
            "content": self._format_architecture_overview(result, structural, behavioral),
            "score": 0.8,
            "reason": "architecture overview",
            "metadata": {
                "total_components": len(structural.components) if structural else 0,
                "total_relationships": len(structural.relationships) if structural else 0,
                "anti_patterns_found": len(result.anti_patterns)
                if hasattr(result, "anti_patterns")
                else 0,
                "analysis_duration_ms": result.analysis_duration_ms
                if hasattr(result, "analysis_duration_ms")
                else 0,
                "system_metrics": result.system_metrics
                if hasattr(result, "system_metrics")
                else {},
            },
        }

        return [overview_result]

    def _format_architecture_overview(
        self,
        result: Any,
        structural: Any,
        behavioral: Any,
    ) -> str:
        """Format architecture overview as readable text."""
        lines = [
            "=== HDMA Architecture Overview ===",
        ]

        if structural:
            lines.append(f"Components: {len(structural.components)}")
            lines.append(f"Relationships: {len(structural.relationships)}")
            complexity = structural.calculate_system_complexity()
            lines.append(f"System Complexity: {complexity:.2f}")

        if hasattr(result, "anti_patterns"):
            critical_count = len(
                [
                    ap
                    for ap in result.anti_patterns
                    if hasattr(ap, "severity")
                    and (ap.severity.value if hasattr(ap.severity, "value") else str(ap.severity))
                    in ("CRITICAL", "HIGH")
                ]
            )
            lines.append(f"Critical Issues: {critical_count}/{len(result.anti_patterns)}")

        if hasattr(result, "system_metrics"):
            lines.append(f"Analysis Duration: {result.analysis_duration_ms:.0f}ms")

        return "\n".join(lines)

    def _search_recommendations(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Get high-impact recommendations."""
        if not self._analysis_result:
            return []

        recommendations = self._analysis_result.get_high_impact_recommendations()

        results = []
        for i, rec in enumerate(list(recommendations)[:limit]):
            results.append(
                {
                    "id": f"hdma_rec_{i}",
                    "source": self.BACKEND_NAME,
                    "backend": self.BACKEND_NAME,
                    "title": f"Recommendation #{i + 1}",
                    "content": rec,
                    "score": 0.85,
                    "reason": "recommendation",
                    "metadata": {
                        "priority": "high",
                        "type": "recommendation",
                    },
                }
            )

        return results

    def _search_critical_issues(
        self,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Get critical architectural issues."""
        if not self._analysis_result:
            return []

        critical = self._analysis_result.get_critical_issues()

        results = []
        for ap in list(critical)[:limit]:
            results.append(self._anti_pattern_to_result(ap, "critical architectural issue"))

        return results

    def _search_by_name(
        self,
        name: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Search for components by name pattern."""
        if not self._analysis_result or not hasattr(self._analysis_result, "structural_map"):
            return []

        results = []
        structural = self._analysis_result.structural_map
        name_lower = name.lower()

        for comp_name, comp in structural.components.items():
            if name_lower in comp_name.lower():
                results.append(self._component_to_result(comp, f"match for '{name}'"))
                if len(results) >= limit:
                    break

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get HDMA statistics."""
        if not self._analysis_initialized or not self._analyzer:
            return {"error": "HDMA not initialized"}

        stats = {
            "analyzer_initialized": True,
            "analysis_run": self._analysis_result is not None,
        }

        if self._analysis_result:
            structural = self._analysis_result.structural_map

            stats.update(
                {
                    "total_components": len(structural.components) if structural else 0,
                    "total_relationships": len(structural.relationships) if structural else 0,
                    "anti_patterns_found": len(self._analysis_result.anti_patterns)
                    if hasattr(self._analysis_result, "anti_patterns")
                    else 0,
                    "correlations_found": len(self._analysis_result.correlations)
                    if hasattr(self._analysis_result, "correlations")
                    else 0,
                    "system_complexity": structural.calculate_system_complexity()
                    if structural
                    else 0.0,
                    "analysis_duration_ms": self._analysis_result.analysis_duration_ms
                    if hasattr(self._analysis_result, "analysis_duration_ms")
                    else 0,
                }
            )

            # Count critical issues
            if hasattr(self._analysis_result, "get_critical_issues"):
                try:
                    stats["critical_issues"] = len(self._analysis_result.get_critical_issues())
                except Exception:
                    pass

        return stats
