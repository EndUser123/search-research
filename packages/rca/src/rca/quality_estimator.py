#!/usr/bin/env python3
"""
quality_estimator.py - Quality Coverage Estimation for rca Tier 1

This module provides quality estimation for investigations based on available
tools and issue type. It helps determine how effective a local-only investigation
can be compared to a full investigation with all tools available.

Components:
- QualityEstimator: Main class for quality calculations
- estimate_quality_coverage: Standalone function for quick estimates
- ISSUE_TYPE_WEIGHTS: Tool weight requirements per issue type
- TOOL_WEIGHTS: Generic tool capability weights

Author: TDD Cycle for rca Tier 1
Version: 1.0.0
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


# =============================================================================
# Weight Definitions
# =============================================================================

# Tool capability weights
# How much each tool contributes to investigation quality generally
TOOL_WEIGHTS: dict[str, float] = {
    # Local tools (always available)
    "Grep": 0.35,    # Pattern matching, code search
    "Read": 0.35,    # File content inspection
    "Bash": 0.20,    # Command execution, testing
    "Write": 0.10,   # Making changes (less for investigation)
    "Edit": 0.10,    # Making changes (less for investigation)
    "Glob": 0.05,    # File finding (utility)

    # Remote tools (not available in local-only mode)
    "WebSearch": 0.25,      # Finding similar issues online
    "Firecrawl": 0.30,      # Web scraping for docs
    "AgenticBrowser": 0.25, # Interactive browser testing
    "SemanticSearch": 0.20, # Semantic code search
    "VectorSearch": 0.20,   # Vector-based search
    "KnowledgeBase": 0.15,  # Internal knowledge base
    "CKS": 0.15,            # Claude Knowledge System
}


# Issue type specific requirements
# Each issue type has different tool needs
ISSUE_TYPE_WEIGHTS: dict[str, dict[str, float]] = {
    # Syntax/parse errors - local tools are very effective
    "syntax_error": {
        "Grep": 0.40,
        "Read": 0.40,
        "Bash": 0.20,
        "WebSearch": 0.00,   # Not needed for syntax errors
        "Firecrawl": 0.00,
    },

    # Runtime errors - local tools good, web search helpful for similar issues
    "runtime_error": {
        "Grep": 0.30,
        "Read": 0.40,
        "Bash": 0.15,
        "WebSearch": 0.10,   # Somewhat helpful
        "Firecrawl": 0.05,
    },

    # Network/API errors - web tools very important for checking status
    "network_error": {
        "Grep": 0.15,
        "Read": 0.25,
        "Bash": 0.10,
        "WebSearch": 0.35,   # Very helpful for service status
        "Firecrawl": 0.15,
    },

    # Import/module errors - local tools are usually sufficient
    "import_error": {
        "Grep": 0.40,
        "Read": 0.45,
        "Bash": 0.15,
        "WebSearch": 0.00,
        "Firecrawl": 0.00,
    },

    # Type errors - local tools with type checkers are effective
    "type_error": {
        "Grep": 0.25,
        "Read": 0.40,
        "Bash": 0.25,        # For running mypy/pyright
        "WebSearch": 0.05,
        "Firecrawl": 0.05,
    },

    # Configuration errors - local tools usually sufficient
    "config_error": {
        "Grep": 0.30,
        "Read": 0.50,
        "Bash": 0.15,
        "WebSearch": 0.05,
        "Firecrawl": 0.00,
    },

    # Performance issues - web tools helpful for research
    "performance": {
        "Grep": 0.25,
        "Read": 0.30,
        "Bash": 0.20,
        "WebSearch": 0.15,
        "Firecrawl": 0.10,
    },

    # Test failures - local tools very effective
    "test_failure": {
        "Grep": 0.30,
        "Read": 0.40,
        "Bash": 0.25,        # Running tests
        "WebSearch": 0.05,
        "Firecrawl": 0.00,
    },

    # Default weights for unknown issue types
    "default": {
        "Grep": 0.30,
        "Read": 0.35,
        "Bash": 0.20,
        "WebSearch": 0.10,
        "Firecrawl": 0.05,
    },
}


# =============================================================================
# Quality Estimator Class
# =============================================================================

class QualityEstimator:
    """Estimate investigation quality based on available tools.

    Provides methods to calculate how effective an investigation can be
    given the available tools and the type of issue being investigated.

    Attributes:
        issue_type: The type of issue being investigated
        available_tools: List of available tool names

    Examples:
        >>> estimator = QualityEstimator("syntax_error", ["Grep", "Read", "Bash"])
        >>> estimator.calculate_coverage()
        1.0
        >>> estimator = QualityEstimator("network_error", ["Grep", "Read", "Bash"])
        >>> estimator.calculate_coverage()
        0.5  # Missing web tools
    """

    def __init__(
        self,
        issue_type: str = "default",
        available_tools: list[str] | None = None,
    ):
        """Initialize the quality estimator.

        Args:
            issue_type: Type of issue (e.g., "syntax_error", "network_error")
            available_tools: List of available tool names
        """
        self.issue_type = issue_type.lower()
        self.available_tools = available_tools or []
        self._weights = self._get_weights_for_issue()

    def _get_weights_for_issue(self) -> dict[str, float]:
        """Get tool weights for the current issue type.

        Returns:
            Dictionary mapping tool names to weights
        """
        # Try exact match first
        if self.issue_type in ISSUE_TYPE_WEIGHTS:
            return ISSUE_TYPE_WEIGHTS[self.issue_type]

        # Try partial match
        for key, weights in ISSUE_TYPE_WEIGHTS.items():
            if key != "default" and key in self.issue_type:
                return weights

        # Use default
        return ISSUE_TYPE_WEIGHTS["default"]

    def calculate_coverage(self) -> float:
        """Calculate quality coverage score.

        Returns:
            Coverage score between 0.0 (no tools) and 1.0 (ideal tool set)

        Examples:
            >>> estimator = QualityEstimator("syntax_error", ["Grep", "Read", "Bash"])
            >>> 0.0 <= estimator.calculate_coverage() <= 1.0
            True
        """
        if not self.available_tools:
            return 0.0

        available_set = set(tool for tool in self.available_tools if tool)
        coverage = 0.0

        for tool, weight in self._weights.items():
            if tool in available_set:
                coverage += weight

        return min(coverage, 1.0)

    def get_missing_tools(self) -> list[str]:
        """Get tools that would improve quality but are unavailable.

        Returns:
            List of missing tool names sorted by importance

        Examples:
            >>> estimator = QualityEstimator("network_error", ["Grep", "Read"])
            >>> missing = estimator.get_missing_tools()
            >>> "WebSearch" in missing
            True
        """
        available_set = set(tool for tool in self.available_tools if tool)
        missing = []

        for tool, weight in sorted(self._weights.items(), key=lambda x: -x[1]):
            if tool not in available_set and weight > 0:
                missing.append(tool)

        return missing

    def get_quality_rating(self) -> str:
        """Get human-readable quality rating.

        Returns:
            Quality rating: "Excellent", "Good", "Fair", "Poor", "None"

        Examples:
            >>> estimator = QualityEstimator("syntax_error", ["Grep", "Read", "Bash"])
            >>> estimator.get_quality_rating() in ["Excellent", "Good", "Fair", "Poor", "None"]
            True
        """
        coverage = self.calculate_coverage()

        if coverage >= 0.9:
            return "Excellent"
        elif coverage >= 0.7:
            return "Good"
        elif coverage >= 0.5:
            return "Fair"
        elif coverage >= 0.2:
            return "Poor"
        else:
            return "None"

    def get_recommendations(self) -> list[str]:
        """Get recommendations for improving investigation quality.

        Returns:
            List of recommendation strings

        Examples:
            >>> estimator = QualityEstimator("network_error", ["Grep", "Read"])
            >>> recs = estimator.get_recommendations()
            >>> len(recs) > 0
            True
        """
        recommendations = []
        missing = self.get_missing_tools()
        coverage = self.calculate_coverage()

        # Low coverage warning
        if coverage < 0.5:
            recommendations.append(
                f"Low quality coverage ({coverage:.1%}). "
                f"Investigation may be inconclusive."
            )

        # Tool-specific recommendations
        if "WebSearch" in missing and self._weights.get("WebSearch", 0) > 0.1:
            recommendations.append(
                "WebSearch would help find similar issues and solutions online."
            )

        if "Firecrawl" in missing and self._weights.get("Firecrawl", 0) > 0.1:
            recommendations.append(
                "Firecrawl would help scrape documentation and examples."
            )

        if "AgenticBrowser" in missing:
            recommendations.append(
                "Browser automation would help test interactive features."
            )

        if coverage >= 0.9:
            recommendations.append(
                "Quality coverage is excellent. Local tools should be sufficient."
            )

        return recommendations


# =============================================================================
# Standalone Functions
# =============================================================================

def estimate_quality_coverage(
    issue_type: str,
    available_tools: list[str],
) -> float:
    """Estimate investigation quality coverage.

    Standalone function for quick quality estimation without creating
    a QualityEstimator instance.

    Args:
        issue_type: The type of issue (e.g., "syntax_error", "runtime_error")
        available_tools: List of available tool names

    Returns:
        Quality coverage between 0.0 and 1.0

    Examples:
        >>> estimate_quality_coverage("syntax_error", ["Grep", "Read", "Bash"])
        1.0
        >>> estimate_quality_coverage("network_error", ["Grep", "Read"])
        0.4
        >>> estimate_quality_coverage("unknown", ["Grep", "Read"])
        0.65
    """
    estimator = QualityEstimator(issue_type, available_tools)
    return estimator.calculate_coverage()


def get_quality_summary(
    issue_type: str,
    available_tools: list[str],
) -> dict[str, Any]:
    """Get a complete quality assessment summary.

    Args:
        issue_type: The type of issue
        available_tools: List of available tool names

    Returns:
        Dictionary with coverage, rating, missing tools, and recommendations

    Examples:
        >>> summary = get_quality_summary("syntax_error", ["Grep", "Read"])
        >>> "coverage" in summary
        True
        >>> "rating" in summary
        True
        >>> "missing_tools" in summary
        True
        >>> "recommendations" in summary
        True
    """
    estimator = QualityEstimator(issue_type, available_tools)

    return {
        "issue_type": issue_type,
        "coverage": estimator.calculate_coverage(),
        "rating": estimator.get_quality_rating(),
        "missing_tools": estimator.get_missing_tools(),
        "recommendations": estimator.get_recommendations(),
        "available_tools": available_tools,
    }


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "QualityEstimator",
    "estimate_quality_coverage",
    "get_quality_summary",
    "ISSUE_TYPE_WEIGHTS",
    "TOOL_WEIGHTS",
]
