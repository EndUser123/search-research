#!/usr/bin/env python3
"""
Cognitive Mode Selector for RCA Enhancement (Phase 4)

Provides intelligent thinking mode selection for root cause analysis
by integrating with the existing cognitive stack.

This module enables:
- Automatic problem classification
- Thinking mode selection based on problem characteristics
- Mental model recommendation for rca-specialist

Author: CSF Development Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ProblemType(Enum):
    """Categories of problems for RCA"""

    ERROR = "error"  # Runtime errors, exceptions
    CRASH = "crash"  # Application crashes
    PERFORMANCE = "performance"  # Slowness, resource issues
    BEHAVIOR = "behavior"  # Unexpected behavior, logic bugs
    SECURITY = "security"  # Vulnerabilities, auth issues
    INTEGRATION = "integration"  # Cross-component issues
    DATA = "data"  # Data integrity, corruption
    CONFIG = "config"  # Configuration issues


class ProblemDepth(Enum):
    """Depth of problem analysis"""

    SYMPTOM = "symptom"  # Visible manifestation only
    INTERMEDIATE = "intermediate"  # Partial understanding
    ROOT_CAUSE = "root_cause"  # Fundamental cause identified


@dataclass
class ProblemClassification:
    """Result of problem classification"""

    problem_type: ProblemType
    depth: ProblemDepth
    confidence: float  # 0.0 to 1.0
    characteristics: list[str] = field(default_factory=list)
    suggested_thinking_modes: list[str] = field(default_factory=list)
    rationale: str = ""


class CognitiveModeSelector:
    """
    Selects appropriate cognitive thinking modes for RCA based on
    problem characteristics and context.

    Integrates with the existing cognitive stack ThinkingModesLibrary.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        # Lazy import to avoid circular dependencies
        self._thinking_library = None

    @property
    def thinking_library(self):
        """Lazy load the thinking modes library"""
        if self._thinking_library is None:
            try:
                from ...cognitive.reasoning.thinking_modes import (
                    ThinkingModesLibrary,
                )

                self._thinking_library = ThinkingModesLibrary()
                self.logger.info(
                    "Loaded ThinkingModesLibrary for cognitive mode selection"
                )
            except ImportError as e:
                self.logger.warning(f"Could not import ThinkingModesLibrary: {e}")
                self._thinking_library = None
        return self._thinking_library

    def classify_problem(
        self, problem_description: str, context: dict[str, Any] | None = None
    ) -> ProblemClassification:
        """
        Classify a problem by type and suggest appropriate thinking modes.

        Args:
            problem_description: The problem statement or error message
            context: Additional context (file names, error types, etc.)

        Returns:
            ProblemClassification with type, depth, and suggested thinking modes

        """
        context = context or {}
        problem_lower = problem_description.lower()

        # Analyze characteristics
        characteristics = self._extract_characteristics(problem_lower, context)

        # Determine problem type
        problem_type = self._determine_problem_type(
            problem_lower, context, characteristics
        )

        # Estimate depth based on information available
        depth = self._estimate_depth(problem_lower, context, characteristics)

        # Select thinking modes based on problem characteristics
        suggested_modes = self._select_thinking_modes(
            problem_type, depth, characteristics, context
        )

        # Build rationale
        rationale = self._build_rationale(problem_type, depth, suggested_modes)

        # Calculate confidence
        confidence = self._calculate_confidence(characteristics, context)

        return ProblemClassification(
            problem_type=problem_type,
            depth=depth,
            confidence=confidence,
            characteristics=characteristics,
            suggested_thinking_modes=suggested_modes,
            rationale=rationale,
        )

    def _extract_characteristics(
        self, problem_lower: str, context: dict[str, Any]
    ) -> list[str]:
        """Extract key characteristics from problem description"""
        characteristics = []

        # Error type patterns
        error_patterns = {
            "attribute_error": "attributeerror",
            "import_error": "importerror",
            "type_error": "typeerror",
            "key_error": "keyerror",
            "value_error": "valueerror",
            "name_error": "nameerror",
            "index_error": "indexerror",
            "syntax_error": "syntaxerror",
            "indentation_error": "indentationerror",
            "memory_error": "memoryerror",
            "overflow_error": "overflowerror",
            "runtime_error": "runtimeerror",
        }

        for name, pattern in error_patterns.items():
            if pattern in problem_lower:
                characteristics.append(name)

        # Behavioral patterns
        behavioral_patterns = {
            "intermittent": ["intermittent", "flaky", "sometimes", "occasional"],
            "timing_related": ["timeout", "race", "timing", "async", "concurrent"],
            "performance": ["slow", "timeout", "latency", "performance", "fast"],
            "recurrent": ["again", "recurs", "repeat", "keeps happening"],
            "new_issue": ["never", "first time", "suddenly", "just started"],
            "after_change": ["after", "following", "since", "recently changed"],
        }

        for name, patterns in behavioral_patterns.items():
            if any(p in problem_lower for p in patterns):
                characteristics.append(name)

        # Context-based characteristics
        if "file_path" in context:
            characteristics.append("file_specific")
        if "stack_trace" in context:
            characteristics.append("has_stack_trace")
        if "recent_changes" in context:
            characteristics.append("recent_changes_detected")

        return characteristics

    def _determine_problem_type(
        self, problem_lower: str, context: dict[str, Any], characteristics: list[str]
    ) -> ProblemType:
        """Determine the primary problem type"""
        # Security issues
        security_keywords = [
            "auth",
            "permission",
            "vulnerability",
            "security",
            "injection",
            "xss",
            "csrf",
        ]
        if any(kw in problem_lower for kw in security_keywords):
            return ProblemType.SECURITY

        # Performance issues
        if "performance" in characteristics or "timing_related" in characteristics:
            return ProblemType.PERFORMANCE

        # Crashes
        crash_keywords = [
            "crash",
            "segfault",
            "exception",
            "traceback",
            "aborted",
            "terminated",
        ]
        if any(kw in problem_lower for kw in crash_keywords):
            return ProblemType.CRASH

        # Integration issues
        integration_keywords = [
            "between",
            "integration",
            "interface",
            "api",
            "cross-component",
        ]
        if any(kw in problem_lower for kw in integration_keywords):
            return ProblemType.INTEGRATION

        # Data issues
        data_keywords = ["data", "corrupt", "missing data", "null", "none", "empty"]
        if any(kw in problem_lower for kw in data_keywords):
            return ProblemType.DATA

        # Configuration issues
        config_keywords = ["config", "setting", "environment", "env var"]
        if any(kw in problem_lower for kw in config_keywords):
            return ProblemType.CONFIG

        # Default to ERROR for exception-related issues
        if any(err in problem_lower for err in ["error", "exception", "fail"]):
            return ProblemType.ERROR

        # Default to BEHAVIOR for unexpected behavior
        return ProblemType.BEHAVIOR

    def _estimate_depth(
        self, problem_lower: str, context: dict[str, Any], characteristics: list[str]
    ) -> ProblemDepth:
        """Estimate the current depth of understanding"""
        # If we have stack trace and context, likely deeper
        if "has_stack_trace" in characteristics:
            return ProblemDepth.INTERMEDIATE

        # If problem mentions root cause explicitly
        if any(
            kw in problem_lower for kw in ["root cause", "underlying", "fundamental"]
        ):
            return ProblemDepth.ROOT_CAUSE

        # If intermittent or complex, likely just symptom
        if "intermittent" in characteristics:
            return ProblemDepth.SYMPTOM

        # Default to symptom level for initial classification
        return ProblemDepth.SYMPTOM

    def _select_thinking_modes(
        self,
        problem_type: ProblemType,
        depth: ProblemDepth,
        characteristics: list[str],
        context: dict[str, Any],
    ) -> list[str]:
        """
        Select appropriate thinking modes based on problem analysis.

        Returns a prioritized list of thinking mode IDs.
        """
        modes = []

        # Default mode for all problems
        modes.append("five_whys")  # Good for drilling down

        # Performance issues → Systems Thinking
        if problem_type == ProblemType.PERFORMANCE:
            modes.insert(0, "systems_thinking")
            modes.insert(1, "first_principles")

        # Intermittent/timing issues → Inversion, Systems Thinking
        if "intermittent" in characteristics or "timing_related" in characteristics:
            if "systems_thinking" not in modes:
                modes.insert(0, "systems_thinking")
            modes.append("scientific_method")  # For hypothesis testing

        # New/unknown issues → First Principles
        if "new_issue" in characteristics:
            modes.insert(0, "first_principles")
            if "tree_thinking" not in modes:
                modes.append("tree_thinking")

        # Integration/cross-component → Systems Thinking
        if problem_type == ProblemType.INTEGRATION:
            modes.insert(0, "systems_thinking")
            if "collaborative_reasoning" not in modes:
                modes.append("collaborative_reasoning")

        # Security → Risk Assessment
        if problem_type == ProblemType.SECURITY:
            modes.insert(0, "risk_assessment")
            if "tree_thinking" not in modes:
                modes.append("tree_thinking")

        # Multiple possible causes → Scientific Method
        if depth == ProblemDepth.SYMPTOM:
            if "scientific_method" not in modes:
                modes.append("scientific_method")

        # After recent changes → Linear Thinking (trace the change)
        if (
            "after_change" in characteristics
            or "recent_changes_detected" in characteristics
        ):
            modes.insert(1, "linear_thinking")

        # Complex issues → Tree Thinking for exploring possibilities
        if len(characteristics) > 3:
            if "tree_thinking" not in modes:
                modes.append("tree_thinking")

        # Ensure unique modes while preserving order
        seen = set()
        unique_modes = []
        for mode in modes:
            if mode not in seen:
                seen.add(mode)
                unique_modes.append(mode)

        return unique_modes[:5]  # Top 5 most relevant modes

    def _build_rationale(
        self, problem_type: ProblemType, depth: ProblemDepth, suggested_modes: list[str]
    ) -> str:
        """Build explanation for mode selection"""
        rationale_parts = [
            f"Problem type: {problem_type.value}",
            f"Depth: {depth.value}",
        ]

        if suggested_modes:
            rationale_parts.append(f"Suggested modes: {', '.join(suggested_modes[:3])}")

        return ". ".join(rationale_parts) + "."

    def _calculate_confidence(
        self, characteristics: list[str], context: dict[str, Any]
    ) -> float:
        """Calculate confidence in the classification"""
        base_confidence = 0.5

        # More characteristics = higher confidence
        characteristic_bonus = min(len(characteristics) * 0.05, 0.25)

        # Context richness
        context_bonus = min(len(context) * 0.03, 0.15)

        return min(base_confidence + characteristic_bonus + context_bonus, 1.0)

    def get_thinking_mode_description(self, mode_id: str) -> dict[str, Any]:
        """
        Get description of a thinking mode from the cognitive stack.

        Args:
            mode_id: ID of the thinking mode

        Returns:
            Dictionary with mode information

        """
        library = self.thinking_library
        if library is None:
            # Return basic info if library not available
            basic_modes = {
                "systems_thinking": {
                    "name": "Systems Thinking",
                    "description": "Holistic analysis of interconnections and feedback loops",
                    "best_for": "Performance issues, cross-component problems",
                },
                "first_principles": {
                    "name": "First Principles",
                    "description": "Break down to fundamental truths and build up",
                    "best_for": "Novel problems, edge cases",
                },
                "five_whys": {
                    "name": "5 Whys",
                    "description": "Iterative questioning to find root cause",
                    "best_for": "Linear cause chains, straightforward issues",
                },
                "scientific_method": {
                    "name": "Scientific Method",
                    "description": "Hypothesis-driven investigation",
                    "best_for": "Multiple plausible causes",
                },
                "tree_thinking": {
                    "name": "Tree Thinking",
                    "description": "Branching exploration of possibilities",
                    "best_for": "Multiple potential solutions, complex decisions",
                },
            }
            return basic_modes.get(
                mode_id, {"name": mode_id, "description": "Unknown mode"}
            )

        return library.get_mode_summary(mode_id)

    def get_all_available_modes(self) -> list[dict[str, Any]]:
        """Get list of all available thinking modes"""
        library = self.thinking_library
        if library is None:
            return []

        return library.list_all_modes()


# Convenience functions for quick usage
def classify_rca_problem(
    problem_description: str, context: dict[str, Any] | None = None
) -> ProblemClassification:
    """
    Quick function to classify an RCA problem.

    Called by rca-specialist or /debug command.
    """
    selector = CognitiveModeSelector()
    return selector.classify_problem(problem_description, context)


def suggest_thinking_modes(
    problem_description: str, context: dict[str, Any] | None = None
) -> list[str]:
    """
    Quick function to get suggested thinking modes for an RCA problem.

    Returns prioritized list of thinking mode IDs.
    """
    classification = classify_rca_problem(problem_description, context)
    return classification.suggested_thinking_modes


def get_mode_info(mode_id: str) -> dict[str, Any]:
    """Get information about a specific thinking mode"""
    selector = CognitiveModeSelector()
    return selector.get_thinking_mode_description(mode_id)


# CLI interface for testing
if __name__ == "__main__":
    # Test examples
    test_problems = [
        "AttributeError: 'Module' object has no attribute 'load'",
        "Application is slow when processing large files",
        "Intermittent timeout when connecting to database",
        "Security: User can access admin endpoints without authentication",
    ]

    selector = CognitiveModeSelector()

    print("Cognitive Mode Selector Test")
    print("=" * 60)

    for problem in test_problems:
        print(f"\nProblem: {problem}")
        classification = selector.classify_problem(problem)
        print(f"  Type: {classification.problem_type.value}")
        print(f"  Depth: {classification.depth.value}")
        print(f"  Confidence: {classification.confidence:.2f}")
        print(f"  Modes: {', '.join(classification.suggested_thinking_modes)}")
        print(f"  Rationale: {classification.rationale}")
