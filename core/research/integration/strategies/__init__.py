"""
Pattern Matching Strategies

Contains different pattern matching algorithms for knowledge discovery.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import UTC, datetime

from ..models import (
    ImplementationResult,
    KnowledgePattern,
    PatternType,
)


class PatternMatchingStrategy(ABC):
    """
    Abstract base class for pattern matching strategies.

    Algorithm Approach: Strategy pattern for extensible pattern matching.
    Allows different algorithms for pattern discovery and validation.
    """

    @abstractmethod
    def match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]:
        """
        Match patterns in implementation data.

        Parameters
        ----------
        implementation_data (ImplementationResult): Implementation result to analyze

        Returns
        -------
        List[KnowledgePattern]: Matched patterns with confidence scores

        """


class StatisticalPatternMatcher(PatternMatchingStrategy):
    """
    Statistical pattern matching using frequency analysis and correlation.

    Algorithm Approach: Statistical analysis with confidence intervals.
    Identifies patterns based on frequency and success rate correlation.
    """

    def __init__(self):
        """Initialize statistical pattern matcher."""
        self.pattern_frequencies = defaultdict(int)
        self.success_rates = defaultdict(list)
        self.min_confidence_threshold = 0.3

    def match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]:
        """
        Match patterns using statistical analysis.

        Algorithm Approach: Frequency analysis with success rate correlation.
        Identifies statistically significant patterns.

        Parameters
        ----------
        implementation_data (ImplementationResult): Implementation result to analyze

        Returns
        -------
        List[KnowledgePattern]: Statistically significant patterns

        """
        patterns = []

        # Analyze observed patterns
        for pattern_name in implementation_data.patterns_observed:
            # Update frequency
            self.pattern_frequencies[pattern_name] += 1

            # Update success rate tracking
            success = implementation_data.outcome == "success"
            self.success_rates[pattern_name].append(success)

            # Calculate confidence based on frequency and success rate
            frequency = self.pattern_frequencies[pattern_name]
            success_rate = sum(self.success_rates[pattern_name]) / len(
                self.success_rates[pattern_name]
            )
            confidence = min((frequency / 10) * success_rate, 1.0)  # Normalize to 0-1

            if confidence >= self.min_confidence_threshold:
                pattern = KnowledgePattern(
                    pattern_id=f"stat_{pattern_name}_{frequency}",
                    pattern_type=self._classify_pattern_type(pattern_name),
                    name=pattern_name,
                    description=f"Statistically significant pattern: {pattern_name}",
                    confidence_score=confidence,
                    success_rate=success_rate,
                    evidence=[f"Observed in {frequency} implementations"],
                    prerequisites=[],
                    benefits=[f"Success rate: {success_rate:.2%}"],
                    risks=[],
                    implementation_examples=[implementation_data.implementation_id],
                    related_patterns=[],
                    created_at=datetime.now(UTC).isoformat(),
                    last_updated=datetime.now(UTC).isoformat(),
                    usage_count=frequency,
                )
                patterns.append(pattern)

        return patterns

    def _classify_pattern_type(self, pattern_name: str) -> PatternType:
        """
        Classify pattern type based on name analysis.

        Algorithm Approach: Keyword-based classification with fallback.
        Provides basic pattern type categorization.

        Parameters
        ----------
        pattern_name (str): Pattern name to classify

        Returns
        -------
        PatternType: Classified pattern type

        """
        pattern_lower = pattern_name.lower()

        if any(keyword in pattern_lower for keyword in ["error", "exception", "try", "catch"]):
            return PatternType.ERROR_HANDLING
        if any(keyword in pattern_lower for keyword in ["test", "spec", "assert"]):
            return PatternType.TESTING
        if any(keyword in pattern_lower for keyword in ["deploy", "release", "production"]):
            return PatternType.DEPLOYMENT
        if any(keyword in pattern_lower for keyword in ["security", "auth", "encrypt"]):
            return PatternType.SECURITY
        if any(keyword in pattern_lower for keyword in ["performance", "optimize", "cache"]):
            return PatternType.PERFORMANCE
        if any(keyword in pattern_lower for keyword in ["workflow", "pipeline", "process"]):
            return PatternType.WORKFLOW
        if any(keyword in pattern_lower for keyword in ["architecture", "design", "structure"]):
            return PatternType.ARCHITECTURAL
        return PatternType.IMPLEMENTATION


class SemanticPatternMatcher(PatternMatchingStrategy):
    """
    Semantic pattern matching using natural language processing.

    Algorithm Approach: Semantic similarity analysis with concept mapping.
    Identifies patterns based on conceptual similarity and context.
    """

    def __init__(self):
        """Initialize semantic pattern matcher."""
        self.semantic_mappings = {
            # Error handling concepts
            "error_management": [
                "error",
                "exception",
                "try",
                "catch",
                "handle",
                "recover",
            ],
            "validation": ["validate", "check", "verify", "ensure", "guard"],
            # Performance concepts
            "optimization": ["optimize", "improve", "enhance", "boost", "speed"],
            "caching": ["cache", "store", "memoize", "remember", "buffer"],
            # Security concepts
            "authentication": ["auth", "login", "credentials", "verify", "identify"],
            "authorization": ["authorize", "permission", "access", "role", "privilege"],
            # Architecture concepts
            "modularization": [
                "module",
                "component",
                "separate",
                "isolate",
                "encapsulate",
            ],
            "scalability": ["scale", "grow", "expand", "handle_load", "distributed"],
        }

    def match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]:
        """
        Match patterns using semantic analysis.

        Algorithm Approach: Concept mapping with similarity scoring.
        Identifies semantically related patterns.

        Parameters
        ----------
        implementation_data (ImplementationResult): Implementation result to analyze

        Returns
        -------
        List[KnowledgePattern]: Semantically matched patterns

        """
        patterns = []

        # Extract text from implementation data
        text_content = " ".join(
            [
                implementation_data.task_description,
                " ".join(implementation_data.patterns_observed),
                " ".join(implementation_data.techniques_used),
                " ".join(implementation_data.lessons_learned),
                implementation_data.user_feedback,
            ],
        ).lower()

        # Match semantic concepts
        for concept, keywords in self.semantic_mappings.items():
            matches = sum(1 for keyword in keywords if keyword in text_content)
            if matches >= 2:  # Need at least 2 keyword matches
                confidence = min(matches / len(keywords), 1.0)

                pattern = KnowledgePattern(
                    pattern_id=f"semantic_{concept}_{int(time.time())}",
                    pattern_type=self._classify_concept_type(concept),
                    name=f"Semantic Pattern: {concept}",
                    description=f"Semantically identified pattern based on: {', '.join(keywords)}",
                    confidence_score=confidence,
                    success_rate=0.0,  # Unknown for semantic patterns
                    evidence=[f"Found {matches} matching keywords in implementation"],
                    prerequisites=[],
                    benefits=["Conceptually similar to successful implementations"],
                    risks=["Requires validation for specific context"],
                    implementation_examples=[implementation_data.implementation_id],
                    related_patterns=[],
                    created_at=datetime.now(UTC).isoformat(),
                    last_updated=datetime.now(UTC).isoformat(),
                    usage_count=1,
                )
                patterns.append(pattern)

        return patterns

    def _classify_concept_type(self, concept: str) -> PatternType:
        """
        Classify semantic concept to pattern type.

        Parameters
        ----------
        concept (str): Semantic concept to classify

        Returns
        -------
        PatternType: Corresponding pattern type

        """
        if concept in ["error_management", "validation"]:
            return PatternType.ERROR_HANDLING
        if concept in ["optimization", "caching"]:
            return PatternType.PERFORMANCE
        if concept in ["authentication", "authorization"]:
            return PatternType.SECURITY
        if concept in ["modularization", "scalability"]:
            return PatternType.ARCHITECTURAL
        return PatternType.IMPLEMENTATION
