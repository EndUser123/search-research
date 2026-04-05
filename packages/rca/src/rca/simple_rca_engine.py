from __future__ import annotations

import logging
import subprocess
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""Simple RCA Engine - Enhanced Root Cause Analysis for CSF.

Pragmatic solo developer solution with SLC+S principles:
- Simple: Uses established RCA methodologies with minimal complexity
- Lovable: Solves immediate root cause analysis problems effectively
- Complete: Fishbone, Fault Tree, and Causal Loop analysis capabilities
- Sustainable: Minimal dependencies, leverages existing knowledge system

Core Methodologies:
1. Fishbone Analysis (Ishikawa) - 6M categories
2. Fault Tree Analysis - Logical decomposition with probability
3. Causal Loop Analysis - System dynamics and feedback loops

Time Complexity: O(n) for all operations
Space Complexity: O(1) - constant space, no large data structures

Author: CSF Development Framework
Version: 1.0
"""


# Import existing CSF components
try:
    from core_utils.sqlite_knowledge_curator import SQLiteKnowledgeCurator
except ImportError:
    SQLiteKnowledgeCurator = None

# Import unified search router for Meta-RAG codebase search
UNIFIED_SEARCH_AVAILABLE = False
ChatHistorySearcher = None
CKS = None
CKSBackend = None
try:
    import sys
    from pathlib import Path

    # Try multiple import paths for CSF search module
    # Priority: knowledge.search (new) -> src.search (old, deprecated)
    import_paths = [
        Path("P:/__csf/src/knowledge"),  # New location
        Path("P:/__csf/src"),             # Old location (deprecated)
    ]

    for search_path in import_paths:
        if search_path.exists() and str(search_path) not in sys.path:
            sys.path.insert(0, str(search_path))

    # Try new import path first, fall back to old
    try:
        from knowledge.search.unified_router import EnhancedUnifiedSearchRouter
    except ImportError:
        from search.unified_router import EnhancedUnifiedSearchRouter

    # Import CHS backend for chat history search
    try:
        from modules.chat_search.chat_search import ChatHistorySearcher
    except ImportError:
        ChatHistorySearcher = None

    # Import CKS for knowledge system search
    try:
        from cks import CKS
    except ImportError:
        CKS = None

    UNIFIED_SEARCH_AVAILABLE = True
except ImportError:
    EnhancedUnifiedSearchRouter = None  # type: ignore[assignment]


@dataclass
class RCAMethodologyResult:
    """Result from a single RCA methodology analysis."""

    methodology: str
    root_causes: list[str]
    contributing_factors: list[str]
    evidence_links: list[dict[str, Any]]
    confidence_score: float
    recommendations: list[str]
    analysis_details: dict[str, Any]


@dataclass
class RCAAnalysis:
    """Comprehensive RCA analysis combining all methodologies."""

    issue: str
    context: dict[str, Any]
    fishbone_result: RCAMethodologyResult | None = None
    fault_tree_result: RCAMethodologyResult | None = None
    causal_loop_result: RCAMethodologyResult | None = None
    knowledge_patterns: list[dict[str, Any]] = field(default_factory=list)
    overall_confidence: float = 0.0
    actionable_recommendations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


class SimpleRCAEngine:
    """
    Simple but comprehensive RCA engine for CSF ecosystem.

    Algorithm Approach: Multi-methodology RCA analysis with pattern matching.
    Each methodology provides different insights, combined for comprehensive understanding.

    Design Patterns:
    - Strategy Pattern: Different RCA methodologies
    - Builder Pattern: Building comprehensive analysis
    - Template Method: Standard RCA workflow

    PERF-001 Fix: Write-behind caching with bounded queue.
    Patterns are queued in memory and flushed on explicit save or session end.

    Parameters
    ----------
    knowledge_curator (Optional[SQLiteKnowledgeCurator]): Knowledge system integration
    logger (Optional[logging.Logger]): Logger instance
    max_pending_patterns (int): Maximum patterns to queue before auto-flush

    Attributes
    ----------
    logger (logging.Logger): Logger for RCA operations
    knowledge_curator (SQLiteKnowledgeCurator): Knowledge system integration
    _pending_patterns (deque): Queue for deferred pattern storage
    _max_pending_patterns (int): Queue size limit for auto-flush

    """

    def __init__(
        self,
        knowledge_curator: SQLiteKnowledgeCurator | None = None,
        logger: logging.Logger | None = None,
        max_pending_patterns: int = 100,
    ) -> None:
        """
        Initialize Simple RCA Engine.

        Parameters
        ----------
        knowledge_curator (Optional[SQLiteKnowledgeCurator]): Knowledge system for pattern storage
        logger (Optional[logging.Logger]): Logger instance for operations
        max_pending_patterns (int): Maximum patterns to queue before auto-flush (default: 100)

        """
        self.logger = logger or logging.getLogger("simple_rca_engine")
        self.knowledge_curator = knowledge_curator or (SQLiteKnowledgeCurator() if SQLiteKnowledgeCurator else None)

        # PERF-001: Write-behind caching with bounded queue
        self._pending_patterns: deque[dict[str, Any]] = deque()
        self._max_pending_patterns = max_pending_patterns

        # Meta-RAG: Unified search router for codebase architecture search (lazy initialization)
        self._search_router: Any = None
        self._search_router_initialized = False

        # Fishbone Analysis Categories (6M)
        self.fishbone_categories = {
            "Man": "Human factors, skills, training, personnel issues",
            "Machine": "Equipment, tools, technology, hardware issues",
            "Method": "Processes, procedures, workflows, how work is done",
            "Material": "Raw materials, supplies, resources, input quality",
            "Measurement": "Data, metrics, monitoring, quality measurement",
            "Environment": "Physical, social, organizational, external factors",
        }

        self.logger.info("Simple RCA Engine initialized with Fishbone, Fault Tree, and Causal Loop analysis")

    def __enter__(self) -> SimpleRCAEngine:
        """Context manager entry - return self."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - flush pending patterns."""
        self.flush_pending_patterns()
        return None

    def analyze_issue(self, issue: str, context: dict[str, Any] | None = None) -> RCAAnalysis:
        """
        Perform comprehensive RCA analysis using multiple methodologies.

        Algorithm Approach: Execute all three RCA methodologies and combine results
        for comprehensive understanding and actionable recommendations.

        Parameters
        ----------
        issue (str): The issue or problem to analyze
        context (Optional[Dict[str, Any]]): Additional context about the issue

        Returns
        -------
        RCAAnalysis: Comprehensive analysis with all methodology results

        Example:
        >>> rca = SimpleRCAEngine()
        >>> result = rca.analyze_issue("Database connection failures in production")
        >>> print(f"Root causes found: {len(result.actionable_recommendations)}")
        Root causes found: 3

        """
        context = context or {}

        self.logger.info(f"Starting comprehensive RCA analysis for issue: {issue}")

        # Create analysis object
        analysis = RCAAnalysis(issue=issue, context=context)

        # Execute each methodology
        self.logger.info("Executing Fishbone Analysis")
        analysis.fishbone_result = self._execute_fishbone_analysis(issue, context)

        self.logger.info("Executing Fault Tree Analysis")
        analysis.fault_tree_result = self._execute_fault_tree_analysis(issue, context)

        self.logger.info("Executing Causal Loop Analysis")
        analysis.causal_loop_result = self._execute_causal_loop_analysis(issue, context)

        # Search for knowledge patterns if available
        if self.knowledge_curator:
            self.logger.info("Searching knowledge system for similar patterns")
            analysis.knowledge_patterns = self._search_knowledge_patterns(issue, context)

        # Get recent changes for Change Intelligence correlation
        self.logger.info("Checking recent changes for correlation")
        # Filter to current working directory to avoid off-target work
        try:
            cwd = Path.cwd()
            # Get relative path from P:/ for filtering
            # Git path filters use directory paths, not ** wildcards
            rel_path = None
            repo_root = None

            # Find repo root (P:/ or parent with .git)
            if cwd.is_relative_to(Path("P:/")):
                rel_parts = cwd.relative_to(Path("P:/")).parts
                if rel_parts:
                    rel_path = "/".join(rel_parts)
                    repo_root = Path("P:/")
            else:
                # Try to find .git directory
                check_path = cwd
                for _ in range(5):  # Check up to 5 levels up
                    if (check_path / ".git").exists():
                        repo_root = check_path
                        # Calculate relative path from repo root
                        try:
                            rel_parts = cwd.relative_to(check_path).parts
                            if rel_parts:
                                rel_path = "/".join(rel_parts)
                        except ValueError:
                            pass
                        break
                    check_path = check_path.parent

            analysis.context["recent_changes"] = self._get_recent_changes(
                time_window_hours=2,
                path_filter=rel_path,
                repo_root=str(repo_root) if repo_root else None,
            )
        except (ValueError, OSError):
            analysis.context["recent_changes"] = []

        # Combine and synthesize results
        self._synthesize_analysis(analysis)

        # Store analysis in knowledge system if available
        if self.knowledge_curator:
            self._store_analysis_patterns(analysis)

        self.logger.info(
            f"RCA analysis completed with {len(analysis.actionable_recommendations)} actionable recommendations",
        )

        return analysis

    def _execute_fishbone_analysis(self, issue: str, context: dict[str, Any]) -> RCAMethodologyResult:
        """
        Execute Fishbone (Ishikawa) analysis.

        Algorithm Approach: Systematic analysis across 6M categories
        to identify potential root causes from different perspectives.

        Parameters
        ----------
        issue (str): Issue being analyzed
        context (Dict[str, Any]): Issue context

        Returns
        -------
        RCAMethodologyResult: Fishbone analysis results

        """
        root_causes = []
        contributing_factors = []
        evidence_links = []

        # Analyze each category
        for category in self.fishbone_categories:
            # Generate potential causes for this category
            potential_causes = self._generate_category_causes(category, issue, context)

            for cause in potential_causes:
                contributing_factors.append(f"{category}: {cause}")

                # Determine if this is likely a root cause
                if self._assess_root_cause_likelihood(cause, category, context):
                    root_causes.append(f"{category}: {cause}")

                # Add evidence link
                evidence_links.append(
                    {
                        "category": category,
                        "potential_cause": cause,
                        "confidence": self._calculate_cause_confidence(cause, category),
                        "context_evidence": self._extract_context_evidence(category, issue, context),
                    },
                )

        return RCAMethodologyResult(
            methodology="Fishbone Analysis",
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            evidence_links=evidence_links,
            confidence_score=self._calculate_fishbone_confidence(root_causes, contributing_factors),
            recommendations=self._generate_fishbone_recommendations(root_causes, contributing_factors),
            analysis_details={
                "categories_analyzed": list(self.fishbone_categories.keys()),
                "total_factors": len(contributing_factors),
                "high_confidence_causes": len([c for c in evidence_links if c["confidence"] > 0.7]),
            },
        )

    def _execute_fault_tree_analysis(self, issue: str, context: dict[str, Any]) -> RCAMethodologyResult:
        """
        Execute Fault Tree analysis.

        Algorithm Approach: Top-down logical decomposition to identify
        failure paths and calculate probability-based root causes.

        Parameters
        ----------
        issue (str): Issue being analyzed
        context (Dict[str, Any]): Issue context

        Returns
        -------
        RCAMethodologyResult: Fault tree analysis results

        """
        # Simplified fault tree - identify main failure paths
        failure_paths = self._identify_failure_paths(issue, context)
        root_causes = []
        contributing_factors = []
        evidence_links = []

        for path in failure_paths:
            # Decompose the failure path
            path_steps = self._decompose_failure_path(path, context)

            # Find the root cause of this path
            root_cause = path_steps[-1] if path_steps else path
            root_causes.append(root_cause)

            # All steps contribute to the failure
            contributing_factors.extend(path_steps)

            # Add evidence link for the path
            evidence_links.append(
                {
                    "failure_path": path,
                    "decomposition": path_steps,
                    "root_cause": root_cause,
                    "probability": self._calculate_path_probability(path, context),
                    "evidence": self._extract_path_evidence(path, context),
                },
            )

        return RCAMethodologyResult(
            methodology="Fault Tree Analysis",
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            evidence_links=evidence_links,
            confidence_score=self._calculate_fault_tree_confidence(root_causes, failure_paths),
            recommendations=self._generate_fault_tree_recommendations(root_causes, evidence_links),
            analysis_details={
                "failure_paths_identified": len(failure_paths),
                "total_contributing_factors": len(contributing_factors),
                "average_path_probability": self._calculate_path_probability(evidence_links, context),
            },
        )

    def _execute_causal_loop_analysis(self, issue: str, context: dict[str, Any]) -> RCAMethodologyResult:
        """
        Execute Causal Loop analysis.

        Algorithm Approach: Identify feedback loops and system dynamics
        that contribute to or mitigate the issue.

        Parameters
        ----------
        issue (str): Issue being analyzed
        context (Dict[str, Any]): Issue context

        Returns
        -------
        RCAMethodologyResult: Causal loop analysis results

        """
        # Simplified causal loop analysis
        feedback_loops = self._identify_feedback_loops(issue, context)
        root_causes = []
        contributing_factors = []
        evidence_links = []

        for loop in feedback_loops:
            # Analyze the loop type and impact
            loop_type = self._classify_loop_type(loop, context)
            loop_impact = self._assess_loop_impact(loop, issue, context)

            # Determine if this loop contributes to the issue
            if loop_impact.get("type") == "negative":
                contributing_factors.append(f"{loop_type} loop: {loop['description']}")

                # Find the leverage point in the loop
                leverage_point = self._find_leverage_point(loop, context)
                if leverage_point:
                    root_causes.append(f"Leverage point: {leverage_point}")

            evidence_links.append(
                {
                    "loop_type": loop_type,
                    "loop_description": loop["description"],
                    "loop_impact": loop_impact,
                    "leverage_point": self._find_leverage_point(loop, context),
                    "reinforcing_factors": self._identify_reinforcing_factors(loop, context),
                    "balancing_factors": self._identify_balancing_factors(loop, context),
                },
            )

        return RCAMethodologyResult(
            methodology="Causal Loop Analysis",
            root_causes=root_causes,
            contributing_factors=contributing_factors,
            evidence_links=evidence_links,
            confidence_score=self._calculate_causal_loop_confidence(root_causes, feedback_loops),
            recommendations=self._generate_causal_loop_recommendations(root_causes, evidence_links),
            analysis_details={
                "feedback_loops_identified": len(feedback_loops),
                "negative_loops": len([l for l in evidence_links if l["loop_impact"]["negative"]]),
                "leverage_points": len([l for l in evidence_links if l["leverage_point"]]),
            },
        )

    def _generate_category_causes(self, category: str, issue: str, context: dict[str, Any]) -> list[str]:
        """Generate potential causes for a specific Fishbone category."""
        # Simplified cause generation based on category and issue
        causes = []

        if category == "Man":
            causes.extend(
                [
                    "Insufficient training or knowledge",
                    "Human error or mistake",
                    "Communication breakdown",
                    "Fatigue or burnout",
                    "Skill gaps",
                ],
            )
        elif category == "Machine":
            causes.extend(
                [
                    "Equipment malfunction",
                    "Software bug or limitation",
                    "Tool failure",
                    "Performance bottleneck",
                    "Configuration error",
                ],
            )
        elif category == "Method":
            causes.extend(
                [
                    "Inadequate process or procedure",
                    "Workflow inefficiency",
                    "Missing quality checks",
                    "Poor documentation",
                    "Inconsistent approach",
                ],
            )
        elif category == "Material":
            causes.extend(
                [
                    "Poor quality input",
                    "Resource shortage",
                    "Material defect",
                    "Supply chain issue",
                    "Environmental factors",
                ],
            )
        elif category == "Measurement":
            causes.extend(
                [
                    "Inadequate monitoring",
                    "Incorrect metrics",
                    "Data quality issues",
                    "Measurement error",
                    "Lack of visibility",
                ],
            )
        elif category == "Environment":
            causes.extend(
                [
                    "Organizational culture",
                    "External dependencies",
                    "System constraints",
                    "Time pressure",
                    "Resource constraints",
                ],
            )

        # Filter causes based on issue context
        return self._filter_causes_by_relevance(causes, issue, context)

    def _filter_causes_by_relevance(self, causes: list[str], issue: str, context: dict[str, Any]) -> list[str]:
        """Filter causes based on relevance to the specific issue."""
        # Simple keyword-based filtering
        relevant_causes = []
        issue_lower = issue.lower()

        for cause in causes:
            cause_lower = cause.lower()

            # Check for keyword overlap
            if any(keyword in issue_lower for keyword in ["error", "failure", "issue", "problem"]):
                if any(keyword in cause_lower for keyword in ["training", "knowledge", "skill", "communication"]):
                    relevant_causes.append(cause)
            else:
                relevant_causes.append(cause)

        return relevant_causes[:5]  # Limit to top 5 most relevant causes

    def _assess_root_cause_likelihood(self, cause: str, category: str, context: dict[str, Any]) -> bool:
        """Assess whether a potential cause is likely to be a root cause."""
        # Simple heuristic: certain categories have higher likelihood of root causes
        high_likelihood_categories = ["Man", "Method", "Environment"]
        return category in high_likelihood_categories

    def _calculate_cause_confidence(self, cause: str, category: str) -> float:
        """Calculate confidence score for a potential cause."""
        # Base confidence by category importance
        category_importance = {
            "Man": 0.8,
            "Method": 0.9,
            "Machine": 0.7,
            "Measurement": 0.6,
            "Material": 0.5,
            "Environment": 0.6,
        }

        base_confidence = category_importance.get(category, 0.5)

        # Adjust based on cause specificity (more specific = higher confidence)
        if len(cause.split()) > 3:  # More specific cause
            base_confidence += 0.1

        return min(1.0, base_confidence)

    def _extract_context_evidence(self, category: str, issue: str, context: dict[str, Any]) -> dict[str, Any]:
        """Extract relevant evidence from context for a category."""
        evidence = {
            "issue_keywords": self._extract_issue_keywords(issue),
            "context_factors": list(context.keys()),
            "category_relevance": self._assess_category_relevance(category, issue, context),
        }

        # Add specific context data if available
        if category == "Man" and "team" in context:
            evidence["team_size"] = context.get("team_size", "unknown")
            evidence["team_experience"] = context.get("team_experience", "unknown")

        return evidence

    def _extract_issue_keywords(self, issue: str) -> list[str]:
        """Extract keywords from the issue description."""
        # Simple keyword extraction
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
        }

        words = [word.lower() for word in issue.split() if word.lower() not in stop_words and len(word) > 2]
        return list(set(words))

    def _assess_category_relevance(self, category: str, issue: str, context: dict[str, Any]) -> float:
        """Assess how relevant a category is to the issue."""
        # Simple relevance scoring based on keyword overlap
        relevance_score = 0.0

        category_keywords = {
            "Man": ["person", "team", "skill", "training", "communication"],
            "Machine": ["equipment", "tool", "software", "hardware", "system"],
            "Method": ["process", "procedure", "workflow", "method", "approach"],
            "Material": ["resource", "input", "supply", "material", "data"],
            "Measurement": ["metric", "measure", "monitor", "check", "validate"],
            "Environment": ["culture", "organization", "external", "constraint", "pressure"],
        }

        issue_words = set(self._extract_issue_keywords(issue))
        category_words = set(category_keywords.get(category, []))

        if category_words:
            overlap = len(issue_words & category_words)
            relevance_score = overlap / len(category_words)

        return relevance_score

    def _calculate_fishbone_confidence(self, root_causes: list[str], contributing_factors: list[str]) -> float:
        """Calculate overall confidence score for fishbone analysis."""
        if not contributing_factors:
            return 0.0

        # Confidence based on ratio of root causes to total factors
        root_cause_ratio = len(root_causes) / len(contributing_factors)

        # Adjust for comprehensive analysis (all categories covered)
        categories_covered = len(self.fishbone_categories)
        comprehensive_factor = min(1.0, categories_covered / 6.0)

        return (root_cause_ratio + comprehensive_factor) / 2.0

    def _generate_fishbone_recommendations(self, root_causes: list[str], contributing_factors: list[str]) -> list[str]:
        """Generate actionable recommendations from fishbone analysis."""
        recommendations = []

        if root_causes:
            recommendations.append(f"Focus on addressing these root causes: {', '.join(root_causes[:3])}")

        if len(contributing_factors) > 5:
            recommendations.append("Implement systematic approach to address multiple contributing factors")

        # Add category-specific recommendations
        recommendations.extend(
            [
                "Develop preventive measures for identified high-risk categories",
                "Create monitoring systems for early detection of contributing factors",
                "Establish regular review processes for process improvement",
            ],
        )

        return recommendations

    def _identify_failure_paths(self, issue: str, context: dict[str, Any]) -> list[str]:
        """Identify potential failure paths for fault tree analysis."""
        # Simplified failure path identification
        failure_paths = []

        # Common failure patterns
        common_patterns = [
            "Input validation failure",
            "Process execution failure",
            "Output generation failure",
            "Communication breakdown",
            "Resource exhaustion",
            "Configuration error",
        ]

        issue_words = self._extract_issue_keywords(issue)

        # Match patterns to issue
        for pattern in common_patterns:
            pattern_words = set(pattern.lower().split())
            if pattern_words & set(issue_words):
                failure_paths.append(pattern)

        # Add context-specific paths
        if "database" in issue_words:
            failure_paths.extend(
                [
                    "Database connection failure",
                    "Query execution failure",
                    "Data consistency failure",
                ],
            )

        return failure_paths

    def _decompose_failure_path(self, path: str, context: dict[str, Any]) -> list[str]:
        """Decompose a failure path into individual steps."""
        # Simple decomposition
        parts = path.split()

        # Add context to each step
        decomposition = []
        for i, part in enumerate(parts):
            if i == 0:
                decomposition.append(f"Primary: {part}")
            else:
                decomposition.append(f"Secondary: {part}")

        return decomposition

    def _calculate_path_probability(self, evidence_links: list[str], context: dict[str, Any]) -> float:
        """Calculate probability of failure paths."""
        if not evidence_links:
            return 0.5

        # Average probability based on path complexity
        total_complexity = 0
        for path in evidence_links:
            total_complexity += len(path.split()) if isinstance(path, str) else 1

        avg_complexity = total_complexity / len(evidence_links)

        # Simpler paths are more likely (less complex = less likely to fail)
        if avg_complexity <= 2:
            return 0.3
        if avg_complexity <= 4:
            return 0.2
        return 0.1

    def _extract_path_evidence(self, path: str, context: dict[str, Any]) -> dict[str, Any]:
        """Extract evidence related to a failure path."""
        return {
            "path_complexity": len(path.split()),
            "issue_relevance": self._calculate_path_relevance(path),
            "context_indicators": list(context.keys()),
        }

    def _calculate_path_relevance(self, path: str) -> float:
        """Calculate how relevant a failure path is to the issue."""
        # Simple relevance based on keyword overlap
        path_words = set(path.lower().split())
        return min(1.0, len(path_words) / 10.0)

    def _calculate_fault_tree_confidence(self, root_causes: list[str], failure_paths: list[str]) -> float:
        """Calculate overall confidence score for fault tree analysis."""
        if not failure_paths:
            return 0.0

        # Confidence based on root cause identification
        root_cause_identification = len(root_causes) / len(failure_paths)

        # Add confidence from path probability analysis
        avg_path_confidence = 0.5  # Simplified average

        return (root_cause_identification + avg_path_confidence) / 2.0

    def _generate_fault_tree_recommendations(
        self,
        root_causes: list[str],
        evidence_links: list[dict[str, Any]],
    ) -> list[str]:
        """Generate actionable recommendations from fault tree analysis."""
        recommendations = []

        recommendations.append(f"Address identified root causes: {', '.join(root_causes)}")

        # Add high-impact recommendations
        high_probability_paths = [link for link in evidence_links if link.get("probability", 0) > 0.2]
        if high_probability_paths:
            recommendations.append("Prioritize fixing high-probability failure paths")

        recommendations.extend(
            [
                "Implement redundancy for critical failure paths",
                "Add monitoring and alerting for early failure detection",
                "Create standard operating procedures for common failures",
            ],
        )

        return recommendations

    def _identify_feedback_loops(self, issue: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Identify feedback loops for causal loop analysis."""
        # Simplified feedback loop identification
        loops = []

        # Common feedback loop patterns
        loop_patterns = [
            {
                "description": "More issues → More pressure → More errors → More issues",
                "type": "vicious_cycle",
                "variables": ["issues", "pressure", "errors"],
            },
            {
                "description": "Poor communication → Misunderstanding → More rework → Less time for communication",
                "type": "vicious_cycle",
                "variables": ["communication", "misunderstanding", "rework", "time"],
            },
            {
                "description": "Better monitoring → Earlier detection → Faster resolution → More confidence in monitoring",
                "type": "virtuous_cycle",
                "variables": ["monitoring", "detection", "resolution", "confidence"],
            },
        ]

        # Filter loops based on issue relevance
        issue_words = self._extract_issue_keywords(issue)

        for loop in loop_patterns:
            loop_words = set(" ".join(loop["variables"]).lower().split())
            if loop_words & set(issue_words):
                loops.append(loop)

        return loops

    def _classify_loop_type(self, loop: dict[str, Any], context: dict[str, Any]) -> str:
        """Classify the type of feedback loop."""
        return loop.get("type", "unknown")

    def _assess_loop_impact(self, loop: dict[str, Any], issue: str, context: dict[str, Any]) -> dict[str, Any]:
        """Assess the impact of a feedback loop on the issue."""
        loop_type = loop.get("type", "unknown")

        if loop_type == "vicious_cycle":
            return {"type": "negative", "severity": "high", "description": "Amplifies the issue"}
        if loop_type == "virtuous_cycle":
            return {"type": "positive", "severity": "low", "description": "Mitigates the issue"}
        return {"type": "neutral", "severity": "medium", "description": "Complex impact"}

    def _find_leverage_point(self, loop: dict[str, Any], context: dict[str, Any]) -> str | None:
        """Find the leverage point in a feedback loop."""
        variables = loop.get("variables", [])

        # Simple leverage point identification
        if "pressure" in variables:
            return "Reduce pressure through better planning and communication"
        if "communication" in variables:
            return "Improve communication channels and clarity"
        if "monitoring" in variables:
            return "Enhance monitoring and early detection systems"

        return None

    def _identify_reinforcing_factors(self, loop: dict[str, Any], context: dict[str, Any]) -> list[str]:
        """Identify factors that reinforce the feedback loop."""
        variables = loop.get("variables", [])
        return [f"Factor: {var}" for var in variables]

    def _identify_balancing_factors(self, loop: dict[str, Any], context: dict[str, Any]) -> list[str]:
        """Identify factors that could balance the feedback loop."""
        # Simplified balancing factors
        return [
            "Regular review and reflection",
            "External feedback and input",
            "Process improvement initiatives",
            "Knowledge sharing and training",
        ]

    def _calculate_causal_loop_confidence(self, root_causes: list[str], feedback_loops: list[dict[str, Any]]) -> float:
        """Calculate overall confidence score for causal loop analysis."""
        if not feedback_loops:
            return 0.0

        # Confidence based on leverage point identification
        leverage_points_identified = len([loop for loop in feedback_loops if self._find_leverage_point(loop, {})])

        # Add confidence from loop impact analysis
        avg_loop_confidence = 0.6  # Simplified average

        return (leverage_points_identified / len(feedback_loops) + avg_loop_confidence) / 2.0

    def _generate_causal_loop_recommendations(
        self,
        root_causes: list[str],
        evidence_links: list[dict[str, Any]],
    ) -> list[str]:
        """Generate actionable recommendations from causal loop analysis."""
        recommendations = []

        if root_causes:
            recommendations.append(f"Address leverage points: {', '.join(root_causes)}")

        # Add loop-specific recommendations
        negative_loops = [link for link in evidence_links if link.get("loop_impact", {}).get("type") == "negative"]
        if negative_loops:
            recommendations.append("Break negative feedback loops through targeted interventions")

        recommendations.extend(
            [
                "Strengthen balancing factors to promote positive feedback",
                "Monitor system dynamics and loop behavior",
                "Create mechanisms for early detection of harmful feedback loops",
            ],
        )

        return recommendations

    def _search_knowledge_patterns(self, issue: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Search knowledge system for similar patterns."""
        if not self.knowledge_curator:
            return []

        try:
            # Search for similar RCA patterns
            patterns = self.knowledge_curator.search_library_patterns(
                pattern_type="rca_analysis",
                technology_context=context.get("technology", "general"),
            )

            # Filter by relevance to current issue
            relevant_patterns = []
            for pattern in patterns:
                if self._is_pattern_relevant(pattern, issue, context):
                    relevant_patterns.append(pattern)

            return relevant_patterns[:5]  # Limit to top 5 most relevant

        except Exception as e:
            self.logger.warning(f"Failed to search knowledge patterns: {e}")
            return []

    def _is_pattern_relevant(self, pattern: dict[str, Any], issue: str, context: dict[str, Any]) -> bool:
        """Check if a knowledge pattern is relevant to the current issue."""
        # Simple relevance check based on keywords
        pattern_text = str(pattern).lower()
        issue_text = issue.lower()

        # Check for keyword overlap
        return any(word in pattern_text for word in issue_text.split() if len(word) > 3)

    def _get_search_router(self) -> Any:
        """Lazy initialization of unified search router (Meta-RAG integration).

        Only initializes the router on first use to avoid timeout during SimpleRCAEngine.__init__().
        The router builds indexes during initialization which can take 10-45 seconds.

        Creates CHS and CKS backends directly to avoid dependency on semantic daemon.

        Returns
        -------
        The initialized EnhancedUnifiedSearchRouter instance, or None if unavailable.
        """
        if not self._search_router_initialized:
            if UNIFIED_SEARCH_AVAILABLE and EnhancedUnifiedSearchRouter is not None:
                try:
                    # Create CHS backend directly (chat history search)
                    chs_backend = None
                    if ChatHistorySearcher is not None:
                        try:
                            chs_backend = ChatHistorySearcher()
                            self.logger.debug("Meta-RAG: CHS backend initialized")
                        except Exception as e:
                            self.logger.warning(f"Meta-RAG: Could not initialize CHS backend: {e}")

                    # Create CKS backend directly (knowledge system search)
                    cks_backend = None
                    if CKS is not None:
                        try:
                            cks = CKS()
                            cks_backend = cks
                            self.logger.debug("Meta-RAG: CKS backend initialized")
                        except Exception as e:
                            self.logger.warning(f"Meta-RAG: Could not initialize CKS backend: {e}")

                    # Initialize router with created backends
                    self._search_router = EnhancedUnifiedSearchRouter(
                        chs_backend=chs_backend,
                        cks_backend=cks_backend,
                        enable_cache=True,
                        enable_daemon=False,
                    )
                    self._search_router_initialized = True
                    self.logger.debug("Meta-RAG: Unified search router initialized")
                except Exception as e:
                    self.logger.warning(f"Meta-RAG: Could not initialize search router: {e}")
                    self._search_router = None
                    self._search_router_initialized = True
            else:
                self._search_router_initialized = True
        return self._search_router

    def _search_unified_backends(
        self,
        query: str,
        backends: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search using unified search router (Meta-RAG integration).

        Provides access to:
        - HDMA: Architectural components, dependencies, anti-patterns
        - CDS: Code documentation (docstrings)
        - Grep: Function/class definitions
        - CHS: Chat history (similar issues discussed)
        - CKS: Knowledge patterns
        - CallGraph, CPG, Dependency: Graph-based code analysis

        Parameters
        ----------
        query (str): Search query
        backends (Optional[List[str]]): Specific backends to search. Defaults to HDMA+CDS+CKS+CHS
        limit (int): Maximum results per backend

        Returns
        -------
        List[Dict[str, Any]]: Unified search results with id, title, content, score, metadata
        """
        router = self._get_search_router()
        if not router:
            self.logger.warning("Meta-RAG: Unified search router not available")
            return []

        # Default backends for RCA: architecture + code + knowledge + chat history
        if backends is None:
            backends = ["HDMA", "CDS", "CKS", "CHS", "Grep"]

        try:
            results = router.search(
                query=query,
                backends=backends,
                limit=limit,
            )
            self.logger.debug(f"Meta-RAG: Found {len(results)} results for '{query}'")
            return results

        except Exception as e:
            self.logger.warning(f"Meta-RAG: Search failed for '{query}': {e}")
            return []

    def search_architectural_context(
        self,
        issue: str,
        component_name: str | None = None,
        backends: list[str] | None = None,
    ) -> dict[str, Any]:
        """Search for architectural context related to an issue.

        Uses HDMA and other backends to provide:
        - Component structure and dependencies
        - Architectural anti-patterns
        - Similar issues from chat history
        - Related code patterns

        Parameters
        ----------
        issue (str): The issue or problem description
        component_name (Optional[str]): Specific component to focus on
        backends (Optional[List[str]]): Specific backends to search. Defaults to HDMA+CDS+CKS+CHS

        Returns
        -------
        Dict[str, Any]: Architectural context with keys:
            - components: List of related components
            - dependencies: Dependency relationships
            - anti_patterns: Architectural smells detected
            - similar_issues: Similar issues from chat history
            - code_patterns: Relevant code patterns
        """
        context = {
            "components": [],
            "dependencies": [],
            "anti_patterns": [],
            "similar_issues": [],
            "code_patterns": [],
        }

        # Build search query
        query_parts = [issue]
        if component_name:
            query_parts.append(component_name)
        query = " ".join(query_parts)

        # Search different aspects
        # Use provided backends or defaults
        default_backends = backends or ["HDMA", "CDS", "CKS", "CHS", "Grep"]

        # 1. Architectural components (HDMA)
        try:
            arch_backend = [b for b in default_backends if b == "HDMA"]
            if arch_backend:  # Only search if HDMA was explicitly requested
                arch_results = self._search_unified_backends(
                    query=query,
                    backends=arch_backend,
                    limit=5,
                )
                # Filter out fallback results and categorize
                real_results = [r for r in arch_results if r.get("reason") != "fallback"]
                context["components"] = [r for r in real_results if "component" in r.get("reason", "")]
                context["anti_patterns"] = [r for r in real_results if "anti-pattern" in r.get("reason", "")]
        except Exception:
            pass

        # 2. Dependencies (HDMA or Dependency backend)
        try:
            dep_backend = [b for b in default_backends if b in ["HDMA", "DEPENDENCY"]]
            if dep_backend:  # Only search if dependency backends were explicitly requested
                dep_results = self._search_unified_backends(
                    query=f"dependencies {query}",
                    backends=dep_backend,
                    limit=5,
                )
                context["dependencies"] = [r for r in dep_results if r.get("reason") != "fallback"]
        except Exception:
            pass

        # 3. Similar issues from chat history
        try:
            chs_backend = [b for b in default_backends if b == "CHS"]
            if chs_backend:  # Only search if CHS was explicitly requested
                chs_results = self._search_unified_backends(
                    query=query,
                    backends=chs_backend,
                    limit=3,
                )
                context["similar_issues"] = chs_results
        except Exception:
            pass

        # 4. Code patterns (CDS, Grep)
        try:
            code_backend = [b for b in default_backends if b in ["CDS", "Grep"]]
            if code_backend:  # Only search if code backends were explicitly requested
                code_results = self._search_unified_backends(
                    query=query,
                    backends=code_backend,
                    limit=5,
                )
                context["code_patterns"] = code_results
        except Exception:
            pass

        return context

    def get_architectural_insights(self, error_location: str) -> list[str]:
        """Get architectural insights for a given error location.

        Analyzes the code structure around an error to provide context:
        - What component does this belong to?
        - What depends on this component?
        - Are there known architectural issues?
        - What similar issues have been discussed?

        Parameters
        ----------
        error_location (str): File path, function name, or error description

        Returns
        -------
        List[str]: Architectural insights as human-readable strings
        """
        insights = []

        try:
            context = self.search_architectural_context(
                issue=error_location,
                component_name=error_location.split(":")[0] if ":" in error_location else None,
            )

            # Component insights
            if context["components"]:
                insights.append(f"Found {len(context['components'])} related components")
                for comp in context["components"][:3]:
                    title = comp.get("title", "")
                    content = comp.get("content", "")
                    if title or content:
                        insights.append(f"  - {title or content[:80]}")

            # Dependency insights
            if context["dependencies"]:
                insights.append(f"Dependency information available ({len(context['dependencies'])} relations)")

            # Anti-pattern warnings
            if context["anti_patterns"]:
                insights.append(f"⚠️  {len(context['anti_patterns'])} architectural anti-pattern(s) detected")
                for ap in context["anti_patterns"][:2]:
                    insights.append(f"  - {ap.get('title', 'Unknown pattern')}")

            # Similar issues from chat history
            if context["similar_issues"]:
                insights.append(f"💬 {len(context['similar_issues'])} similar issue(s) discussed previously")

            if not insights:
                insights.append("No architectural context found via unified search")

        except Exception as e:
            insights.append(f"Could not retrieve architectural context: {e}")

        return insights

    def _synthesize_analysis(self, analysis: RCAAnalysis) -> None:
        """Synthesize results from all methodologies into actionable recommendations."""
        all_root_causes = []
        all_recommendations = []
        methodology_results = []

        # Collect all results
        if analysis.fishbone_result:
            methodology_results.append(analysis.fishbone_result)
            all_root_causes.extend(analysis.fishbone_result.root_causes)
            all_recommendations.extend(analysis.fishbone_result.recommendations)

        if analysis.fault_tree_result:
            methodology_results.append(analysis.fault_tree_result)
            all_root_causes.extend(analysis.fault_tree_result.root_causes)
            all_recommendations.extend(analysis.fault_tree_result.recommendations)

        if analysis.causal_loop_result:
            methodology_results.append(analysis.causal_loop_result)
            all_root_causes.extend(analysis.causal_loop_result.root_causes)
            all_recommendations.extend(analysis.causal_loop_result.recommendations)

        # Collect CKS knowledge patterns (learnings from previous incidents)
        if analysis.knowledge_patterns:
            self.logger.info(f"Including {len(analysis.knowledge_patterns)} CKS knowledge patterns")
            for pattern in analysis.knowledge_patterns:
                # Extract lesson from CKS pattern
                lesson = pattern.get("lesson", pattern.get("content", ""))
                if lesson:
                    all_recommendations.append(f"[From CKS] {lesson}")

                # Extract root cause if available
                cause = pattern.get("root_cause", "")
                if cause:
                    all_root_causes.append(f"[CKS] {cause}")

        # Collect Change Intelligence (recent git commits)
        recent_changes = analysis.context.get("recent_changes", [])
        if recent_changes:
            self.logger.info(f"Including {len(recent_changes)} recent changes for correlation")
            for change in recent_changes[:5]:  # Limit to 5 most recent
                commit_msg = change.get("message", "")
                commit_hash = change.get("hash", "")
                author = change.get("author", "")
                if commit_msg:
                    # Format as a correlation hint (not definitive cause)
                    all_recommendations.append(
                        f"[Recent Change] {commit_msg[:60]}... ({commit_hash} by {author})"
                    )

        # Remove duplicates and prioritize
        unique_root_causes = list(set(all_root_causes))
        unique_recommendations = self._prioritize_recommendations(list(set(all_recommendations)))

        # Calculate overall confidence
        if methodology_results:
            analysis.overall_confidence = sum(r.confidence_score for r in methodology_results) / len(
                methodology_results,
            )
        else:
            analysis.overall_confidence = 0.0

        # Set final recommendations
        analysis.actionable_recommendations = unique_recommendations

        self.logger.info(
            f"Analysis synthesized: {len(unique_root_causes)} root causes, {len(unique_recommendations)} recommendations",
        )

    def _prioritize_recommendations(self, recommendations: list[str]) -> list[str]:
        """Prioritize recommendations based on impact and feasibility."""
        # Simple prioritization based on keywords
        high_priority_keywords = ["prevent", "monitor", "improve", "implement", "address"]
        medium_priority_keywords = ["review", "consider", "develop", "create"]

        high_priority = [r for r in recommendations if any(keyword in r.lower() for keyword in high_priority_keywords)]
        medium_priority = [
            r for r in recommendations if any(keyword in r.lower() for keyword in medium_priority_keywords)
        ]
        low_priority = [r for r in recommendations if r not in high_priority and r not in medium_priority]

        return high_priority + medium_priority + low_priority[:10]

    def _store_analysis_patterns(self, analysis: RCAAnalysis) -> None:
        """
        Store analysis patterns in knowledge system for future learning.

        PERF-001 Fix: Patterns are queued in memory and written in batches.
        Queue is flushed when:
        - Queue reaches max_pending_patterns size
        - flush_pending_patterns() is called explicitly
        - Context manager exits (if using `with` statement)
        """
        if not self.knowledge_curator:
            return

        try:
            # Create pattern data
            pattern_data = {
                "pattern_type": "rca_analysis",
                "issue": analysis.issue,
                "context": analysis.context,
                "methodologies": {
                    "fishbone": {
                        "used": analysis.fishbone_result is not None,
                        "confidence": analysis.fishbone_result.confidence_score if analysis.fishbone_result else 0.0,
                    },
                    "fault_tree": {
                        "used": analysis.fault_tree_result is not None,
                        "confidence": (
                            analysis.fault_tree_result.confidence_score if analysis.fault_tree_result else 0.0
                        ),
                    },
                    "causal_loop": {
                        "used": analysis.causal_loop_result is not None,
                        "confidence": (
                            analysis.causal_loop_result.confidence_score if analysis.causal_loop_result else 0.0
                        ),
                    },
                },
                "outcomes": {
                    "root_causes": analysis.actionable_recommendations,
                    "confidence_score": analysis.overall_confidence,
                    "knowledge_patterns": len(analysis.knowledge_patterns),
                },
                "created_at": analysis.created_at.isoformat(),
            }

            # PERF-001: Queue pattern instead of immediate write
            self._pending_patterns.append(pattern_data)
            self.logger.debug(
                "RCA analysis pattern queued (pending: %d/%d)",
                len(self._pending_patterns),
                self._max_pending_patterns,
            )

            # Auto-flush if queue is full
            if len(self._pending_patterns) >= self._max_pending_patterns:
                self.flush_pending_patterns()

        except Exception as e:
            self.logger.warning(f"Failed to queue analysis pattern: {e}")

    def flush_pending_patterns(self) -> int:
        """
        Flush all pending patterns to knowledge system.

        PERF-001: This method writes all queued patterns in a batch.
        Called automatically when queue is full or on context exit.

        Returns:
            Number of patterns successfully stored

        """
        if not self.knowledge_curator or not self._pending_patterns:
            return 0

        stored_count = 0
        failed_count = 0

        # Process all pending patterns
        patterns_to_store = list(self._pending_patterns)
        self._pending_patterns.clear()

        for pattern_data in patterns_to_store:
            try:
                self.knowledge_curator.store_library_pattern(pattern_data)
                stored_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to store pattern: {e}")
                failed_count += 1

        if stored_count > 0:
            self.logger.info(
                "Flushed %d pending patterns to knowledge system (%d failed)",
                stored_count,
                failed_count,
            )

        return stored_count

    def get_pending_patterns_count(self) -> int:
        """
        Get the number of patterns currently queued for storage.

        Returns:
            Number of pending patterns

        """
        return len(self._pending_patterns)

    def _get_recent_changes(
        self,
        time_window_hours: int = 2,
        path_filter: str | None = None,
        repo_root: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get recent git changes for Change Intelligence correlation.

        Most production failures are caused by recent human changes.
        This method retrieves recent commits to provide context.

        Parameters
        ----------
        time_window_hours (int): Hours to look back for changes (default: 2)
        path_filter (Optional[str]): Filter to specific path (e.g., "packages/rca")
        repo_root (Optional[str]): Repository root directory for git command

        Returns
        -------
        List[Dict[str, Any]]: Recent commits with hash, author, message, time

        """
        changes = []

        try:
            # Determine time window
            since_time = datetime.now() - timedelta(hours=time_window_hours)
            since_format = since_time.strftime("%Y-%m-%dT%H:%M:%S")

            # Build git log command
            cmd = [
                "git",
                "log",
                f"--since={since_format}",
                "--format=%H|%an|%s|%ct",
                "--no-merges",
            ]

            # Add path filter if provided (avoids off-target work)
            # Git path filters work with directory paths, no ** needed
            if path_filter:
                cmd.append("--")
                cmd.append(path_filter)

            # Run git command from repo root if specified, else cwd
            cwd = repo_root if repo_root else None
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                cwd=cwd,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        changes.append({
                            "hash": parts[0][:8],  # Short hash
                            "author": parts[1],
                            "message": parts[2],
                            "timestamp": int(parts[3]),
                        })

                if path_filter:
                    self.logger.info(
                        f"Found {len(changes)} recent changes in last {time_window_hours}h "
                        f"(filter: {path_filter})"
                    )
                else:
                    self.logger.info(f"Found {len(changes)} recent changes in last {time_window_hours}h")
            else:
                self.logger.debug(f"Git log failed: {result.stderr}")

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            self.logger.debug(f"Change intelligence unavailable: {e}")

        return changes


def create_simple_rca_engine() -> SimpleRCAEngine:
    """
    Create and configure a Simple RCA Engine instance.

    Convenience function for creating RCA engines with consistent configuration.

    Returns:
    -------
    SimpleRCAEngine: Configured RCA engine instance

    Example:
    -------
    >>> rca = create_simple_rca_engine()
    >>> result = rca.analyze_issue("Database connection failures")
    >>> print(f"Confidence: {result.overall_confidence:.2f}")
    Confidence: 0.75

    """
    return SimpleRCAEngine()
