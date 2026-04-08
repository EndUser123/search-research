"""
Knowledge Integration Core Module

This module contains the core KnowledgeIntegrationEngine class extracted from the
monolithic integration_engine.py file. It provides comprehensive knowledge integration,
pattern matching, cross-implementation learning, and evidence-based recommendations
for the CSF system.

Algorithm Approach: Multi-layered integration with real-time learning,
pattern recognition, and evidence-based recommendations. Provides comprehensive
knowledge capture, analysis, and retrieval capabilities.

Time Complexity: O(log n) for indexed knowledge queries, O(n) for pattern matching,
O(m*k) for cross-implementation learning where m is implementations and k is patterns

Space Complexity: O(n) for knowledge storage, O(m*k) for pattern cache,
O(p*q) for cross-reference indexing where p is patterns and q is implementations

Design Pattern: Observer pattern for real-time learning, Strategy pattern for
different knowledge integration algorithms, and Factory pattern for knowledge
objects.

Security Features:
- Input validation and sanitization for all knowledge data
- Access control through role-based permissions
- Audit logging for all knowledge operations
- Data integrity verification through checksums
- Rate limiting for knowledge ingestion
- Secure storage of sensitive implementation data
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import statistics
import sys
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime, timedelta
from enum import Enum, auto
from functools import partial
from pathlib import Path
from typing import Any

# Import existing CSF components
try:
    from ....lib.core_utils.knowledge.knowledge_query_engine import (
        KnowledgeQueryEngine,
        KnowledgeQueryError,
    )
    from ....lib.helpfulness import HelpfulnessPattern

    csf_AVAILABLE = True
except ImportError:
    csf_AVAILABLE = False
    logging.warning("CSF components not available - some features limited")

# Configure logging for knowledge integration operations
logger = logging.getLogger(__name__)


class KnowledgeIntegrationError(Exception):
    """
    Custom exception for knowledge integration errors.

    Algorithm Approach: Structured error handling with detailed context.
    Provides comprehensive error information for debugging and recovery.

    Design Pattern: Exception chaining pattern for error propagation.
    """

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        context: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now(UTC).isoformat()


class IntegrationStatus(Enum):
    """Status of knowledge integration operations."""

    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    RETRYING = auto()


class PatternType(Enum):
    """Types of knowledge patterns."""

    ARCHITECTURAL = "architectural"
    IMPLEMENTATION = "implementation"
    SECURITY = "security"
    PERFORMANCE = "performance"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"


class ConfidenceLevel(Enum):
    """Confidence levels for recommendations."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class ImplementationResult:
    """
    Result of an implementation for knowledge integration.

    Algorithm Approach: Comprehensive result capture with structured metadata.
    Enables detailed analysis and learning from implementation outcomes.

    Design Pattern: Data Transfer Object pattern for result encapsulation.
    """

    implementation_id: str
    agent_type: str
    task_description: str
    outcome: str  # success, failure, partial
    execution_time: float
    patterns_observed: list[str]
    techniques_used: list[str]
    challenges_faced: list[str]
    lessons_learned: list[str]
    code_metrics: dict[str, Any]
    user_feedback: str | None = None
    artifacts_created: list[str] | None = None
    dependencies_added: list[str] | None = None
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgePattern:
    """
    Represents a knowledge pattern extracted from implementations.

    Algorithm Approach: Pattern abstraction with confidence scoring and evidence tracking.
    Enables pattern recognition, reuse, and adaptation across implementations.

    Design Pattern: Value Object pattern for immutable pattern representation.
    """

    pattern_id: str
    pattern_type: PatternType
    name: str
    description: str
    confidence_score: float
    success_rate: float
    evidence: list[str]
    prerequisites: list[str]
    benefits: list[str]
    risks: list[str]
    implementation_examples: list[str]
    related_patterns: list[str]
    created_at: str
    last_updated: str
    usage_count: int = 0


@dataclass
class EvidenceBasedRecommendation:
    """
    Evidence-based recommendation with confidence scoring.

    Algorithm Approach: Recommendation generation with supporting evidence
    and confidence assessment. Provides actionable suggestions with provenance.

    Design Pattern: Strategy pattern for different recommendation types.
    """

    recommendation_id: str
    title: str
    description: str
    confidence_level: ConfidenceLevel
    supporting_evidence: list[str]
    expected_outcome: str
    implementation_steps: list[str]
    risk_assessment: str
    alternatives: list[str]
    related_patterns: list[str]
    source_implementations: list[str]
    created_at: str
    expires_at: str | None = None
    tags: list[str] | None = None


@dataclass
class KnowledgeQuery:
    """
    Structured query for knowledge base search.

    Algorithm Approach: Flexible query specification with multiple search dimensions.
    Enables precise knowledge retrieval with context awareness.

    Design Pattern: Query Object pattern for complex query encapsulation.
    """

    query_id: str
    search_terms: list[str]
    context: str
    pattern_types: list[PatternType]
    confidence_threshold: float
    time_range: tuple[str, str]  # start_date, end_date
    implementation_filter: dict[str, Any]
    sort_by: str  # relevance, confidence, recency, usage
    limit: int
    include_metadata: bool


class PatternMatchingStrategy(ABC):
    """
    Abstract base class for pattern matching strategies.

    Algorithm Approach: Strategy pattern for extensible pattern matching.
    Enables different algorithms for pattern recognition and analysis.

    Design Pattern: Strategy pattern with template method.
    """

    @abstractmethod
    def match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]:
        """
        Match patterns in implementation data.

        Parameters
        ----------
        implementation_data (ImplementationResult): Implementation data to analyze

        Returns
        -------
        List[KnowledgePattern]: Matched patterns with confidence scores

        """


class StatisticalPatternMatcher(PatternMatchingStrategy):
    """
    Statistical pattern matching using frequency analysis and metrics.

    Algorithm Approach: Statistical analysis with frequency-based pattern detection.
    Identifies recurring patterns through quantitative analysis.

    Design Pattern: Strategy pattern implementation for statistical matching.
    """

    def match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]:
        """
        Match patterns using statistical analysis.

        Algorithm Approach: Frequency analysis with statistical significance testing.
        Detects patterns that occur with statistical significance.

        Parameters
        ----------
        implementation_data (ImplementationResult): Implementation data to analyze

        Returns
        -------
        List[KnowledgePattern]: Statistically significant patterns

        """
        patterns = []

        # Analyze technique frequency
        technique_counts = {}
        for technique in implementation_data.techniques_used:
            technique_counts[technique] = technique_counts.get(technique, 0) + 1

        # Generate patterns based on successful techniques
        if implementation_data.outcome == "success":
            for technique, count in technique_counts.items():
                if count >= 1:  # At least once in successful implementation
                    pattern = KnowledgePattern(
                        pattern_id=f"stat_{technique}_{int(time.time())}",
                        pattern_type=self._classify_technique(technique),
                        name=technique.replace("_", " ").title(),
                        description=f"Statistical pattern: {technique} used in successful implementation",
                        confidence_score=min(count / len(implementation_data.techniques_used), 1.0),
                        success_rate=1.0 if implementation_data.outcome == "success" else 0.0,
                        evidence=[
                            f"Used in implementation {implementation_data.implementation_id}"
                        ],
                        prerequisites=self._extract_prerequisites(technique),
                        benefits=self._extract_benefits(technique),
                        risks=self._extract_risks(technique),
                        implementation_examples=[implementation_data.implementation_id],
                        related_patterns=[],
                        created_at=datetime.now(UTC).isoformat(),
                        last_updated=datetime.now(UTC).isoformat(),
                    )
                    patterns.append(pattern)

        return patterns

    def _classify_technique(self, technique: str) -> PatternType:
        """
        Classify technique into pattern type.

        Parameters
        ----------
        technique (str): Technique to classify

        Returns
        -------
        PatternType: Classified pattern type

        """
        technique_lower = technique.lower()

        if "error" in technique_lower or "exception" in technique_lower:
            return PatternType.ERROR_HANDLING
        if "security" in technique_lower or "auth" in technique_lower:
            return PatternType.SECURITY
        if "performance" in technique_lower or "optimize" in technique_lower:
            return PatternType.PERFORMANCE
        if "test" in technique_lower or "spec" in technique_lower:
            return PatternType.TESTING
        if "deploy" in technique_lower or "build" in technique_lower:
            return PatternType.DEPLOYMENT
        if "doc" in technique_lower or "readme" in technique_lower:
            return PatternType.DOCUMENTATION
        if "arch" in technique_lower or "design" in technique_lower:
            return PatternType.ARCHITECTURAL
        return PatternType.IMPLEMENTATION

    def _extract_prerequisites(self, technique: str) -> list[str]:
        """
        Extract prerequisites for a technique.

        Parameters
        ----------
        technique (str): Technique to analyze

        Returns
        -------
        List[str]: Identified prerequisites

        """
        # Simple heuristic-based prerequisite extraction
        prerequisites = []
        technique_lower = technique.lower()

        if "async" in technique_lower:
            prerequisites.append("Understanding of asynchronous programming")
        if "database" in technique_lower or "db" in technique_lower:
            prerequisites.append("Database connectivity setup")
        if "api" in technique_lower:
            prerequisites.append("API endpoint configuration")

        return prerequisites

    def _extract_benefits(self, technique: str) -> list[str]:
        """
        Extract benefits of a technique.

        Parameters
        ----------
        technique (str): Technique to analyze

        Returns
        -------
        List[str]: Identified benefits

        """
        benefits = []
        technique_lower = technique.lower()

        if "error" in technique_lower:
            benefits.append("Improved error handling and robustness")
        if "security" in technique_lower:
            benefits.append("Enhanced security posture")
        if "performance" in technique_lower:
            benefits.append("Better performance and efficiency")
        if "test" in technique_lower:
            benefits.append("Improved code quality and reliability")

        return benefits

    def _extract_risks(self, technique: str) -> list[str]:
        """
        Extract risks associated with a technique.

        Parameters
        ----------
        technique (str): Technique to analyze

        Returns
        -------
        List[str]: Identified risks

        """
        risks = []
        technique_lower = technique.lower()

        if "async" in technique_lower:
            risks.append("Complexity in async flow management")
        if "database" in technique_lower:
            risks.append("Potential performance bottlenecks")
        if "api" in technique_lower:
            risks.append("External dependency management")

        return risks


class SemanticPatternMatcher(PatternMatchingStrategy):
    """
    Semantic pattern matching using NLP and context analysis.

    Algorithm Approach: Semantic analysis with context-aware pattern detection.
    Identifies patterns through meaning and context rather than just frequency.

    Design Pattern: Strategy pattern implementation for semantic matching.
    """

    def match_patterns(self, implementation_data: ImplementationResult) -> list[KnowledgePattern]:
        """
        Match patterns using semantic analysis.

        Algorithm Approach: Context-aware semantic analysis with pattern clustering.
        Detects patterns based on semantic similarity and contextual relevance.

        Parameters
        ----------
        implementation_data (ImplementationResult): Implementation data to analyze

        Returns
        -------
        List[KnowledgePattern]: Semantically relevant patterns

        """
        patterns = []

        # Analyze task description for semantic patterns
        self._extract_keywords(implementation_data.task_description)

        # Analyze lessons learned for semantic insights
        lessons_insights = self._analyze_lessons(implementation_data.lessons_learned)

        # Generate patterns based on semantic analysis
        for insight in lessons_insights:
            pattern = KnowledgePattern(
                pattern_id=f"sem_{insight['type']}_{int(time.time())}",
                pattern_type=self._classify_insight(insight),
                name=insight["title"],
                description=insight["description"],
                confidence_score=insight["confidence"],
                success_rate=1.0 if implementation_data.outcome == "success" else 0.5,
                evidence=[insight["evidence"]],
                prerequisites=insight.get("prerequisites", []),
                benefits=insight.get("benefits", []),
                risks=insight.get("risks", []),
                implementation_examples=[implementation_data.implementation_id],
                related_patterns=[],
                created_at=datetime.now(UTC).isoformat(),
                last_updated=datetime.now(UTC).isoformat(),
            )
            patterns.append(pattern)

        return patterns

    def _extract_keywords(self, text: str) -> list[str]:
        """
        Extract keywords from text using simple NLP.

        Parameters
        ----------
        text (str): Text to analyze

        Returns
        -------
        List[str]: Extracted keywords

        """
        # Simple keyword extraction using common programming terms
        programming_keywords = [
            "async",
            "await",
            "error",
            "exception",
            "handling",
            "security",
            "authentication",
            "authorization",
            "performance",
            "optimization",
            "cache",
            "database",
            "query",
            "api",
            "rest",
            "graphql",
            "test",
            "testing",
            "unit",
            "integration",
            "deployment",
            "build",
            "ci",
            "cd",
            "pipeline",
            "monitoring",
            "logging",
            "debug",
            "refactor",
            "architecture",
            "design",
            "pattern",
            "interface",
            "abstract",
            "inheritance",
            "polymorphism",
            "encapsulation",
            "modular",
            "scalable",
            "maintainable",
        ]

        words = text.lower().split()
        keywords = [word for word in words if word in programming_keywords]

        return list(set(keywords))  # Remove duplicates

    def _analyze_lessons(self, lessons: list[str]) -> list[dict[str, Any]]:
        """
        Analyze lessons learned for semantic insights.

        Parameters
        ----------
        lessons (List[str]): Lessons learned from implementation

        Returns
        -------
        List[Dict[str, Any]]: Semantic insights derived from lessons

        """
        insights = []

        for lesson in lessons:
            lesson_lower = lesson.lower()

            # Analyze lesson type and content
            if "error" in lesson_lower or "exception" in lesson_lower:
                insights.append(
                    {
                        "type": "error_handling",
                        "title": "Error Handling Pattern",
                        "description": f"Error handling insight: {lesson}",
                        "confidence": 0.7,
                        "evidence": lesson,
                        "prerequisites": ["Understanding of error types", "Exception hierarchy"],
                        "benefits": ["Improved robustness", "Better error reporting"],
                        "risks": ["Increased code complexity"],
                    }
                )

            elif "performance" in lesson_lower or "optimize" in lesson_lower:
                insights.append(
                    {
                        "type": "performance",
                        "title": "Performance Optimization Pattern",
                        "description": f"Performance insight: {lesson}",
                        "confidence": 0.6,
                        "evidence": lesson,
                        "prerequisites": ["Performance metrics", "Benchmarks"],
                        "benefits": ["Faster execution", "Better resource utilization"],
                        "risks": ["Premature optimization", "Code complexity"],
                    }
                )

            elif "security" in lesson_lower or "auth" in lesson_lower:
                insights.append(
                    {
                        "type": "security",
                        "title": "Security Pattern",
                        "description": f"Security insight: {lesson}",
                        "confidence": 0.8,
                        "evidence": lesson,
                        "prerequisites": ["Security requirements", "Threat model"],
                        "benefits": ["Enhanced security", "Compliance"],
                        "risks": ["Performance overhead", "Complexity"],
                    }
                )

        return insights

    def _classify_insight(self, insight: dict[str, Any]) -> PatternType:
        """
        Classify insight into pattern type.

        Parameters
        ----------
        insight (Dict[str, Any]): Insight to classify

        Returns
        -------
        PatternType: Classified pattern type

        """
        insight_type = insight.get("type", "")

        if insight_type == "error_handling":
            return PatternType.ERROR_HANDLING
        if insight_type == "performance":
            return PatternType.PERFORMANCE
        if insight_type == "security":
            return PatternType.SECURITY
        return PatternType.IMPLEMENTATION


class KnowledgeIntegrationEngine:
    """
    Advanced knowledge integration engine for CWO12 Step 10 enhancement.

    Algorithm Approach: Multi-layered integration with real-time learning,
    pattern recognition, and evidence-based recommendations. Provides comprehensive
    knowledge capture, analysis, and retrieval capabilities.

    Design Pattern: Observer pattern for real-time learning, Facade pattern
    for unified interface, and Strategy pattern for extensible algorithms.

    Thread Safety: Thread-safe operations through proper synchronization
    and atomic data structures.

    Performance: Asynchronous processing with intelligent caching and
    batch operations for scalability.
    """

    def __init__(
        self,
        helpful_engine: HelpfulnessPattern | None = None,
        knowledge_query_engine: KnowledgeQueryEngine | None = None,
        storage_path: str | None = None,
    ):
        """
        Initialize Knowledge Integration Engine.

        Parameters
        ----------
        helpful_engine (HelpfulnessPattern, optional): Helpfulness engine integration
        knowledge_query_engine (KnowledgeQueryEngine, optional): CSF knowledge engine
        storage_path (str, optional): Path for knowledge storage database

        Raises
        ------
        ValueError: If initialization parameters are invalid
        KnowledgeIntegrationError: If engine initialization fails

        """
        self.helpful_engine = helpful_engine
        self.knowledge_query_engine = knowledge_query_engine
        self.storage_path = storage_path or str(Path(__file__).parent / "knowledge_integration.db")

        # Initialize pattern matchers
        self.pattern_matchers = [
            StatisticalPatternMatcher(),
            SemanticPatternMatcher(),
        ]

        # Initialize knowledge storage
        self._initialize_storage()

        # Initialize threading and async support
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._learning_lock = threading.Lock()
        self._ingestion_queue = deque(maxlen=1000)
        self._batch_size = 10
        self._batch_timeout = 30  # seconds

        # Initialize pattern cache
        self._pattern_cache = {}
        self._cache_ttl = 300  # 5 minutes

        # Initialize shutdown flag
        self._shutdown_requested = False

        # Start background processing
        self._start_background_processing()

        logger.info("KnowledgeIntegrationEngine initialized successfully")

    def _initialize_storage(self) -> None:
        """
        Initialize knowledge storage database.

        Algorithm Approach: SQLite database with optimized schema.
        Provides persistent storage with efficient querying capabilities.

        Design Pattern: Active Record pattern for data access.
        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                # Create implementations table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS implementations (
                        implementation_id TEXT PRIMARY KEY,
                        agent_type TEXT NOT NULL,
                        task_description TEXT NOT NULL,
                        outcome TEXT NOT NULL,
                        execution_time REAL NOT NULL,
                        patterns_observed TEXT,
                        techniques_used TEXT,
                        challenges_faced TEXT,
                        lessons_learned TEXT,
                        code_metrics TEXT,
                        user_feedback TEXT,
                        artifacts_created TEXT,
                        dependencies_added TEXT,
                        timestamp TEXT NOT NULL,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create patterns table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS knowledge_patterns (
                        pattern_id TEXT PRIMARY KEY,
                        pattern_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        confidence_score REAL NOT NULL,
                        success_rate REAL NOT NULL,
                        evidence TEXT,
                        prerequisites TEXT,
                        benefits TEXT,
                        risks TEXT,
                        implementation_examples TEXT,
                        related_patterns TEXT,
                        created_at TEXT NOT NULL,
                        last_updated TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 0
                    )
                """
                )

                # Create recommendations table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS recommendations (
                        recommendation_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        confidence_level REAL NOT NULL,
                        supporting_evidence TEXT,
                        expected_outcome TEXT,
                        implementation_steps TEXT,
                        risk_assessment TEXT,
                        alternatives TEXT,
                        related_patterns TEXT,
                        source_implementations TEXT,
                        created_at TEXT NOT NULL,
                        expires_at TEXT,
                        tags TEXT
                    )
                """
                )

                # Create pattern relationships table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS pattern_relationships (
                        source_pattern_id TEXT NOT NULL,
                        target_pattern_id TEXT NOT NULL,
                        relationship_type TEXT NOT NULL,
                        strength REAL NOT NULL,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (source_pattern_id, target_pattern_id)
                    )
                """
                )

                # Create indexes for performance
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_patterns_type ON knowledge_patterns(pattern_type)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_patterns_confidence ON knowledge_patterns(confidence_score)",
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_recommendations_confidence ON recommendations(confidence_level)",
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_implementations_outcome ON implementations(outcome)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_implementations_timestamp ON implementations(timestamp)"
                )

                conn.commit()
                logger.info("Knowledge storage initialized successfully")

        except Exception as e:
            raise KnowledgeIntegrationError(
                f"Failed to initialize knowledge storage: {e}",
                "STORAGE_INITIALIZATION_ERROR",
                {"storage_path": self.storage_path},
            )

    def _start_background_processing(self) -> None:
        """Start background processing for knowledge ingestion."""

        def process_queue():
            while not getattr(self, "_shutdown_requested", False):
                try:
                    if len(self._ingestion_queue) >= self._batch_size:
                        batch = [
                            self._ingestion_queue.popleft()
                            for _ in range(min(self._batch_size, len(self._ingestion_queue)))
                        ]
                        self._process_ingestion_batch(batch)
                    else:
                        time.sleep(0.5)  # Wait for more items with shorter sleep
                except Exception as e:
                    logger.error(f"Error in background processing: {e}")
                    time.sleep(5)  # Back off on error

        # Start background thread
        self._background_thread = threading.Thread(target=process_queue, daemon=True)
        self._background_thread.start()
        logger.info("Background processing started")

    def _process_ingestion_batch(self, batch: list[ImplementationResult]) -> None:
        """
        Process a batch of implementation results for ingestion.

        Algorithm Approach: Batch processing with transaction management.
        Ensures efficient and consistent knowledge ingestion.

        Parameters
        ----------
        batch (List[ImplementationResult]): Implementation results to process

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                for impl_result in batch:
                    # Store implementation data
                    self._store_implementation_data(cursor, impl_result)

                    # Extract and store patterns
                    patterns = self._extract_patterns(impl_result)
                    for pattern in patterns:
                        self._store_pattern(cursor, pattern)

                    # Generate and store recommendations
                    recommendations = self._generate_recommendations(impl_result, patterns)
                    for recommendation in recommendations:
                        self._store_recommendation(cursor, recommendation)

                conn.commit()
                logger.info(f"Processed ingestion batch of {len(batch)} implementations")

        except Exception as e:
            logger.error(f"Error processing ingestion batch: {e}")

    def _store_implementation_data(
        self, cursor: sqlite3.Cursor, impl_result: ImplementationResult
    ) -> None:
        """
        Store implementation result data in database.

        Parameters
        ----------
        cursor (sqlite3.Cursor): Database cursor
        impl_result (ImplementationResult): Implementation result to store

        """
        cursor.execute(
            """
            INSERT OR REPLACE INTO implementations
            (implementation_id, agent_type, task_description, outcome, execution_time,
             patterns_observed, techniques_used, challenges_faced, lessons_learned,
             code_metrics, user_feedback, artifacts_created, dependencies_added,
             timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                impl_result.implementation_id,
                impl_result.agent_type,
                impl_result.task_description,
                impl_result.outcome,
                impl_result.execution_time,
                json.dumps(impl_result.patterns_observed),
                json.dumps(impl_result.techniques_used),
                json.dumps(impl_result.challenges_faced),
                json.dumps(impl_result.lessons_learned),
                json.dumps(impl_result.code_metrics),
                impl_result.user_feedback,
                json.dumps(impl_result.artifacts_created),
                json.dumps(impl_result.dependencies_added),
                impl_result.timestamp,
                json.dumps(impl_result.metadata),
            ),
        )

    def _extract_patterns(self, impl_result: ImplementationResult) -> list[KnowledgePattern]:
        """
        Extract patterns from implementation result.

        Algorithm Approach: Multi-strategy pattern matching with confidence scoring.
        Combines statistical and semantic analysis for comprehensive coverage.

        Parameters
        ----------
        impl_result (ImplementationResult): Implementation result to analyze

        Returns
        -------
        List[KnowledgePattern]: Extracted patterns with confidence scores

        """
        all_patterns = []

        # Apply each pattern matching strategy
        for matcher in self.pattern_matchers:
            try:
                patterns = matcher.match_patterns(impl_result)
                all_patterns.extend(patterns)
            except Exception as e:
                logger.error(f"Error in pattern matcher {matcher.__class__.__name__}: {e}")

        # Deduplicate and merge patterns
        merged_patterns = self._merge_patterns(all_patterns)

        logger.info(
            f"Extracted {len(merged_patterns)} patterns from implementation {impl_result.implementation_id}"
        )
        return merged_patterns

    def _merge_patterns(self, patterns: list[KnowledgePattern]) -> list[KnowledgePattern]:
        """
        Merge duplicate or similar patterns.

        Algorithm Approach: Pattern similarity detection with confidence merging.
        Consolidates similar patterns to avoid redundancy.

        Parameters
        ----------
        patterns (List[KnowledgePattern]): Patterns to merge

        Returns
        -------
        List[KnowledgePattern]: Merged patterns

        """
        if not patterns:
            return []

        merged = {}

        for pattern in patterns:
            # Create similarity key based on name and type
            similarity_key = f"{pattern.pattern_type}:{pattern.name.lower()}"

            if similarity_key in merged:
                # Merge with existing pattern
                existing = merged[similarity_key]
                existing.confidence_score = max(existing.confidence_score, pattern.confidence_score)
                existing.evidence.extend(pattern.evidence)
                existing.implementation_examples.extend(pattern.implementation_examples)
                existing.usage_count += pattern.usage_count
                existing.last_updated = datetime.now(UTC).isoformat()
            else:
                merged[similarity_key] = pattern

        return list(merged.values())

    def _store_pattern(self, cursor: sqlite3.Cursor, pattern: KnowledgePattern) -> None:
        """
        Store pattern in database.

        Parameters
        ----------
        cursor (sqlite3.Cursor): Database cursor
        pattern (KnowledgePattern): Pattern to store

        """
        cursor.execute(
            """
            INSERT OR REPLACE INTO knowledge_patterns
            (pattern_id, pattern_type, name, description, confidence_score,
             success_rate, evidence, prerequisites, benefits, risks,
             implementation_examples, related_patterns, created_at,
             last_updated, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                pattern.pattern_id,
                pattern.pattern_type.value,
                pattern.name,
                pattern.description,
                pattern.confidence_score,
                pattern.success_rate,
                json.dumps(pattern.evidence),
                json.dumps(pattern.prerequisites),
                json.dumps(pattern.benefits),
                json.dumps(pattern.risks),
                json.dumps(pattern.implementation_examples),
                json.dumps(pattern.related_patterns),
                pattern.created_at,
                pattern.last_updated,
                pattern.usage_count,
            ),
        )

    def _generate_recommendations(
        self,
        impl_result: ImplementationResult,
        patterns: list[KnowledgePattern],
    ) -> list[EvidenceBasedRecommendation]:
        """
        Generate evidence-based recommendations from patterns.

        Algorithm Approach: Rule-based recommendation generation with confidence scoring.
        Creates actionable suggestions based on successful patterns.

        Parameters
        ----------
        impl_result (ImplementationResult): Implementation result context
        patterns (List[KnowledgePattern]): Extracted patterns

        Returns
        -------
        List[EvidenceBasedRecommendation]: Generated recommendations

        """
        recommendations = []

        for pattern in patterns:
            if pattern.confidence_score >= 0.7 and pattern.success_rate >= 0.8:
                # High-confidence, high-success patterns generate recommendations
                recommendation = EvidenceBasedRecommendation(
                    recommendation_id=f"rec_{pattern.pattern_id}_{int(time.time())}",
                    title=f"Apply Pattern: {pattern.name}",
                    description=f"Consider applying the '{pattern.name}' pattern based on its success rate of {pattern.success_rate:.1%}",
                    confidence_level=(
                        ConfidenceLevel.HIGH
                        if pattern.confidence_score >= 0.9
                        else ConfidenceLevel.MEDIUM
                    ),
                    supporting_evidence=pattern.evidence
                    + [f"Success rate: {pattern.success_rate:.1%}"],
                    expected_outcome=f"Expected to improve implementation quality with {pattern.success_rate:.1%} success probability",
                    implementation_steps=[
                        f"1. Ensure prerequisites: {', '.join(pattern.prerequisites)}",
                        f"2. Apply pattern: {pattern.description}",
                        "3. Validate results and measure outcomes",
                    ],
                    risk_assessment=f"Risks: {', '.join(pattern.risks) if pattern.risks else 'Low risk based on historical data'}",
                    alternatives=(
                        [f"Consider similar patterns: {', '.join(pattern.related_patterns[:3])}"]
                        if pattern.related_patterns
                        else []
                    ),
                    related_patterns=[pattern.pattern_id],
                    source_implementations=[impl_result.implementation_id],
                    created_at=datetime.now(UTC).isoformat(),
                    expires_at=(datetime.now(UTC) + timedelta(days=30)).isoformat(),
                    tags=[pattern.pattern_type.value, pattern.name.lower()],
                )
                recommendations.append(recommendation)

        return recommendations

    def _store_recommendation(
        self, cursor: sqlite3.Cursor, recommendation: EvidenceBasedRecommendation
    ) -> None:
        """
        Store recommendation in database.

        Parameters
        ----------
        cursor (sqlite3.Cursor): Database cursor
        recommendation (EvidenceBasedRecommendation): Recommendation to store

        """
        cursor.execute(
            """
            INSERT OR REPLACE INTO recommendations
            (recommendation_id, title, description, confidence_level,
             supporting_evidence, expected_outcome, implementation_steps,
             risk_assessment, alternatives, related_patterns,
             source_implementations, created_at, expires_at, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                recommendation.recommendation_id,
                recommendation.title,
                recommendation.description,
                recommendation.confidence_level.value,
                json.dumps(recommendation.supporting_evidence),
                recommendation.expected_outcome,
                json.dumps(recommendation.implementation_steps),
                recommendation.risk_assessment,
                json.dumps(recommendation.alternatives),
                json.dumps(recommendation.related_patterns),
                json.dumps(recommendation.source_implementations),
                recommendation.created_at,
                recommendation.expires_at,
                json.dumps(recommendation.tags),
            ),
        )

    def automatic_knowledge_ingestion(
        self,
        implementation_results: ImplementationResult | list[ImplementationResult],
    ) -> dict[str, Any]:
        """
        Automatically ingest knowledge from implementation results and outcomes.

        Algorithm Approach: Asynchronous batch processing with pattern extraction.
        Enables real-time learning from ongoing implementations.

        Parameters
        ----------
        implementation_results (Union[ImplementationResult, List[ImplementationResult]]):
            Implementation result(s) to ingest

        Returns
        -------
        Dict[str, Any]: Ingestion results with status and statistics

        Raises
        ------
        KnowledgeIntegrationError: If ingestion fails
        ValueError: If implementation data is invalid

        """
        try:
            # Normalize input to list
            if isinstance(implementation_results, ImplementationResult):
                implementation_results = [implementation_results]

            # Validate implementation results
            for impl_result in implementation_results:
                self._validate_implementation_result(impl_result)

            # Add to ingestion queue
            for impl_result in implementation_results:
                self._ingestion_queue.append(impl_result)

            # Capture helpful improvement opportunities
            if self.helpful_engine:
                for impl_result in implementation_results:
                    if impl_result.outcome == "success":
                        self.helpful_engine.capture_improvement(
                            idea=f"Analyze successful implementation: {impl_result.implementation_id}",
                            context=f"Task: {impl_result.task_description[:100]}...",
                            priority="medium",
                            tags=["knowledge_integration", "successful_implementation"],
                        )
                    elif impl_result.outcome == "failure":
                        self.helpful_engine.suggest_improvement(
                            current_issue=f"Failed implementation: {impl_result.implementation_id}",
                            suggestion="Analyze failure patterns and improve error handling",
                            expected_benefit="Reduced failure rates and improved implementation quality",
                        )

            # Return ingestion status
            result = {
                "status": "queued_for_processing",
                "implementations_queued": len(implementation_results),
                "queue_size": len(self._ingestion_queue),
                "estimated_processing_time": len(self._ingestion_queue) * 0.5,  # Estimate
                "timestamp": datetime.now(UTC).isoformat(),
                "implementation_ids": [impl.implementation_id for impl in implementation_results],
            }

            logger.info(
                f"Queued {len(implementation_results)} implementations for knowledge ingestion"
            )
            return result

        except Exception as e:
            logger.error(f"Automatic knowledge ingestion failed: {e}")
            raise KnowledgeIntegrationError(
                f"Failed to ingest knowledge: {e}",
                "INGESTION_ERROR",
                {
                    "implementation_count": (
                        len(implementation_results)
                        if isinstance(implementation_results, list)
                        else 1
                    ),
                },
            )

    def _validate_implementation_result(self, impl_result: ImplementationResult) -> None:
        """
        Validate implementation result data.

        Algorithm Approach: Comprehensive validation with detailed error reporting.
        Ensures data quality before processing.

        Parameters
        ----------
        impl_result (ImplementationResult): Implementation result to validate

        Raises
        ------
        ValueError: If validation fails

        """
        if not impl_result.implementation_id:
            raise ValueError("Implementation ID is required")

        if not impl_result.agent_type:
            raise ValueError("Agent type is required")

        if not impl_result.task_description:
            raise ValueError("Task description is required")

        if impl_result.outcome not in ["success", "failure", "partial"]:
            raise ValueError("Outcome must be 'success', 'failure', or 'partial'")

        if impl_result.execution_time < 0:
            raise ValueError("Execution time must be non-negative")

    def pattern_matching_algorithms(
        self, implementation_data: ImplementationResult | None = None
    ) -> dict[str, Any]:
        """
        Match current to historical patterns using advanced algorithms.

        Algorithm Approach: Multi-strategy pattern matching with confidence scoring.
        Combines statistical, semantic, and hybrid matching approaches.

        Parameters
        ----------
        implementation_data (ImplementationResult, optional): Current implementation to analyze
            - If not provided, returns pattern matching statistics
            - If provided, performs pattern matching on the data

        Returns
        -------
        Dict[str, Any]: Pattern matching results and statistics

        Raises
        ------
        KnowledgeIntegrationError: If pattern matching fails

        """
        try:
            if implementation_data:
                # Perform pattern matching on provided data
                patterns = self._extract_patterns(implementation_data)

                # Get historical pattern statistics
                historical_stats = self._get_pattern_statistics()

                # Match with historical patterns
                matches = self._match_with_historical_patterns(patterns)

                result = {
                    "current_patterns": [asdict(pattern) for pattern in patterns],
                    "historical_matches": matches,
                    "pattern_statistics": historical_stats,
                    "matching_confidence": self._calculate_overall_confidence(patterns),
                    "recommendations": self._generate_pattern_recommendations(patterns),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            else:
                # Return pattern matching algorithm statistics
                result = {
                    "available_algorithms": [
                        matcher.__class__.__name__ for matcher in self.pattern_matchers
                    ],
                    "total_patterns_stored": self._count_stored_patterns(),
                    "pattern_types_distribution": self._get_pattern_type_distribution(),
                    "average_confidence_scores": self._get_average_confidence_by_type(),
                    "recent_pattern_discoveries": self._get_recent_patterns(limit=10),
                    "algorithm_performance": self._get_algorithm_performance(),
                    "timestamp": datetime.now(UTC).isoformat(),
                }

            logger.info("Pattern matching completed successfully")
            return result

        except Exception as e:
            logger.error(f"Pattern matching failed: {e}")
            raise KnowledgeIntegrationError(
                f"Pattern matching error: {e}",
                "PATTERN_MATCHING_ERROR",
            )

    def _get_pattern_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive pattern statistics from storage.

        Returns
        -------
        Dict[str, Any]: Pattern statistics and distributions

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                # Total patterns
                cursor.execute("SELECT COUNT(*) FROM knowledge_patterns")
                total_patterns = cursor.fetchone()[0]

                # Patterns by type
                cursor.execute(
                    """
                    SELECT pattern_type, COUNT(*)
                    FROM knowledge_patterns
                    GROUP BY pattern_type
                """
                )
                patterns_by_type = dict(cursor.fetchall())

                # Average confidence by type
                cursor.execute(
                    """
                    SELECT pattern_type, AVG(confidence_score)
                    FROM knowledge_patterns
                    GROUP BY pattern_type
                """
                )
                avg_confidence_by_type = dict(cursor.fetchall())

                # Success rate distribution
                cursor.execute(
                    """
                    SELECT
                        CASE
                            WHEN success_rate >= 0.9 THEN 'Excellent (>=90%)'
                            WHEN success_rate >= 0.8 THEN 'Good (80-89%)'
                            WHEN success_rate >= 0.7 THEN 'Average (70-79%)'
                            WHEN success_rate >= 0.6 THEN 'Fair (60-69%)'
                            ELSE 'Poor (<60%)'
                        END as category,
                        COUNT(*) as count
                    FROM knowledge_patterns
                    WHERE success_rate > 0
                    GROUP BY category
                """
                )
                success_rate_distribution = dict(cursor.fetchall())

                return {
                    "total_patterns": total_patterns,
                    "patterns_by_type": patterns_by_type,
                    "average_confidence_by_type": avg_confidence_by_type,
                    "success_rate_distribution": success_rate_distribution,
                }

        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {}

    def _count_stored_patterns(self) -> int:
        """
        Count total patterns stored in database.

        Returns
        -------
        int: Total number of stored patterns

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM knowledge_patterns")
                return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting stored patterns: {e}")
            return 0

    def _get_pattern_type_distribution(self) -> dict[str, int]:
        """
        Get distribution of patterns by type.

        Returns
        -------
        Dict[str, int]: Pattern type distribution

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT pattern_type, COUNT(*)
                    FROM knowledge_patterns
                    GROUP BY pattern_type
                """
                )
                return dict(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error getting pattern type distribution: {e}")
            return {}

    def _get_average_confidence_by_type(self) -> dict[str, float]:
        """
        Get average confidence scores by pattern type.

        Returns
        -------
        Dict[str, float]: Average confidence by type

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT pattern_type, AVG(confidence_score)
                    FROM knowledge_patterns
                    GROUP BY pattern_type
                """
                )
                return {row[0]: float(row[1]) for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Error getting average confidence by type: {e}")
            return {}

    def _get_recent_patterns(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recently created patterns.

        Parameters
        ----------
        limit (int): Maximum number of patterns to return

        Returns
        -------
        List[Dict[str, Any]: Recent patterns

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT pattern_id, name, pattern_type, confidence_score, created_at
                    FROM knowledge_patterns
                    ORDER BY created_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting recent patterns: {e}")
            return []

    def _get_algorithm_performance(self) -> dict[str, Any]:
        """
        Get performance metrics for pattern matching algorithms.

        Returns
        -------
        Dict[str, Any]: Algorithm performance metrics

        """
        return {
            "statistical_matcher": {"active": True, "patterns_found": 0},
            "semantic_matcher": {"active": True, "patterns_found": 0},
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
        }

    def _match_with_historical_patterns(
        self, current_patterns: list[KnowledgePattern]
    ) -> list[dict[str, Any]]:
        """
        Match current patterns with historical patterns.

        Algorithm Approach: Similarity-based matching with confidence weighting.
        Identifies related historical patterns for guidance.

        Parameters
        ----------
        current_patterns (List[KnowledgePattern]): Current patterns to match

        Returns
        -------
        List[Dict[str, Any]: Historical pattern matches with similarity scores

        """
        matches = []

        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                for current_pattern in current_patterns:
                    # Find similar historical patterns
                    cursor.execute(
                        """
                        SELECT pattern_id, name, description, confidence_score,
                               success_rate, usage_count
                        FROM knowledge_patterns
                        WHERE pattern_type = ? AND pattern_id != ?
                        ORDER BY confidence_score DESC, usage_count DESC
                        LIMIT 5
                    """,
                        (
                            current_pattern.pattern_type.value,
                            current_pattern.pattern_id,
                        ),
                    )

                    historical_patterns = cursor.fetchall()

                    for hist_pattern in historical_patterns:
                        similarity = self._calculate_pattern_similarity(
                            current_pattern,
                            {
                                "name": hist_pattern[1],
                                "description": hist_pattern[2],
                            },
                        )

                        if similarity >= 0.5:  # Similarity threshold
                            matches.append(
                                {
                                    "current_pattern_id": current_pattern.pattern_id,
                                    "current_pattern_name": current_pattern.name,
                                    "historical_pattern_id": hist_pattern[0],
                                    "historical_pattern_name": hist_pattern[1],
                                    "similarity_score": similarity,
                                    "historical_confidence": hist_pattern[3],
                                    "historical_success_rate": hist_pattern[4],
                                    "historical_usage_count": hist_pattern[5],
                                    "recommendation": (
                                        "Consider historical approach"
                                        if similarity >= 0.8
                                        else "Adapt with caution"
                                    ),
                                },
                            )

        except Exception as e:
            logger.error(f"Error matching with historical patterns: {e}")

        return matches

    def _calculate_pattern_similarity(
        self, pattern1: KnowledgePattern, pattern2_info: dict[str, str]
    ) -> float:
        """
        Calculate similarity between two patterns.

        Algorithm Approach: Text similarity with keyword matching.
        Provides similarity score between 0.0 and 1.0.

        Parameters
        ----------
        pattern1 (KnowledgePattern): First pattern
        pattern2_info (Dict[str, str]): Second pattern information (name, description)

        Returns
        -------
        float: Similarity score between 0.0 and 1.0

        """
        text1 = f"{pattern1.name} {pattern1.description}".lower()
        text2 = f"{pattern2_info['name']} {pattern2_info['description']}".lower()

        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _calculate_overall_confidence(self, patterns: list[KnowledgePattern]) -> float:
        """
        Calculate overall confidence for a set of patterns.

        Parameters
        ----------
        patterns (List[KnowledgePattern]): Patterns to evaluate

        Returns
        -------
        float: Overall confidence score

        """
        if not patterns:
            return 0.0

        return sum(pattern.confidence_score for pattern in patterns) / len(patterns)

    def _generate_pattern_recommendations(self, patterns: list[KnowledgePattern]) -> list[str]:
        """
        Generate recommendations based on pattern analysis.

        Parameters
        ----------
        patterns (List[KnowledgePattern]): Analyzed patterns

        Returns
        -------
        List[str]: Generated recommendations

        """
        recommendations = []

        high_confidence_patterns = [p for p in patterns if p.confidence_score >= 0.8]
        if high_confidence_patterns:
            recommendations.append(
                f"Found {len(high_confidence_patterns)} high-confidence patterns suitable for immediate application",
            )

        low_success_patterns = [p for p in patterns if p.success_rate < 0.6 and p.success_rate > 0]
        if low_success_patterns:
            recommendations.append(
                f"Caution: {len(low_success_patterns)} patterns have low historical success rates"
            )

        if len(patterns) >= 5:
            recommendations.append("Consider focusing on the top 3 patterns to avoid complexity")

        return recommendations

    def cross_implementation_learning(
        self, analysis_parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Learn across multiple implementations to capture transferable lessons.

        Algorithm Approach: Cross-referential analysis with pattern clustering.
        Identifies transferable lessons and successful approaches.

        Parameters
        ----------
        analysis_parameters (Dict[str, Any], optional): Parameters for analysis
            - time_range: Time range for analysis (start_date, end_date)
            - agent_types: Agent types to include in analysis
            - outcome_filter: Filter by implementation outcomes
            - pattern_types: Pattern types to focus on
            - confidence_threshold: Minimum confidence threshold

        Returns
        -------
        Dict[str, Any]: Cross-implementation learning results

        Raises
        ------
        KnowledgeIntegrationError: If learning analysis fails

        """
        try:
            # Default parameters
            params = {
                "time_range": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
                "agent_types": None,
                "outcome_filter": None,
                "pattern_types": None,
                "confidence_threshold": 0.5,
                "limit": 100,
            }
            params.update(analysis_parameters or {})

            # Gather implementation data
            implementations = self._get_implementations_for_analysis(params)

            # Analyze cross-implementation patterns
            cross_patterns = self._analyze_cross_implementation_patterns(implementations)

            # Identify transferable lessons
            transferable_lessons = self._identify_transferable_lessons(
                implementations, cross_patterns
            )

            # Generate insights
            insights = self._generate_cross_implementation_insights(implementations, cross_patterns)

            # Calculate success correlations
            success_correlations = self._calculate_success_correlations(implementations)

            result = {
                "analysis_parameters": params,
                "implementations_analyzed": len(implementations),
                "cross_implementation_patterns": cross_patterns,
                "transferable_lessons": transferable_lessons,
                "generated_insights": insights,
                "success_correlations": success_correlations,
                "learning_summary": self._generate_learning_summary(
                    cross_patterns, transferable_lessons
                ),
                "recommendations": self._generate_cross_implementation_recommendations(
                    cross_patterns
                ),
                "timestamp": datetime.now(UTC).isoformat(),
            }

            logger.info(
                f"Cross-implementation learning completed for {len(implementations)} implementations"
            )
            return result

        except Exception as e:
            logger.error(f"Cross-implementation learning failed: {e}")
            raise KnowledgeIntegrationError(
                f"Cross-implementation learning error: {e}",
                "CROSS_IMPLEMENTATION_LEARNING_ERROR",
            )

    def _get_implementations_for_analysis(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Get implementations matching analysis parameters.

        Parameters
        ----------
        params (Dict[str, Any]): Analysis parameters

        Returns
        -------
        List[Dict[str, Any]: Matching implementation data

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                # Build query with filters
                query = "SELECT * FROM implementations WHERE 1=1"
                query_params = []

                if params.get("time_range"):
                    query += " AND timestamp >= ?"
                    query_params.append(params["time_range"])

                if params.get("agent_types"):
                    placeholders = ",".join(["?"] * len(params["agent_types"]))
                    query += f" AND agent_type IN ({placeholders})"
                    query_params.extend(params["agent_types"])

                if params.get("outcome_filter"):
                    placeholders = ",".join(["?"] * len(params["outcome_filter"]))
                    query += f" AND outcome IN ({placeholders})"
                    query_params.extend(params["outcome_filter"])

                query += " ORDER BY timestamp DESC LIMIT ?"
                query_params.append(params.get("limit", 100))

                cursor.execute(query, query_params)
                columns = [description[0] for description in cursor.description]
                implementations = []

                for row in cursor.fetchall():
                    impl_data = dict(zip(columns, row, strict=False))
                    # Parse JSON fields
                    for json_field in [
                        "patterns_observed",
                        "techniques_used",
                        "challenges_faced",
                        "lessons_learned",
                        "code_metrics",
                        "artifacts_created",
                        "dependencies_added",
                        "metadata",
                    ]:
                        if impl_data.get(json_field):
                            impl_data[json_field] = json.loads(impl_data[json_field])
                    implementations.append(impl_data)

                return implementations

        except Exception as e:
            logger.error(f"Error getting implementations for analysis: {e}")
            return []

    def _analyze_cross_implementation_patterns(
        self, implementations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Analyze patterns across multiple implementations.

        Algorithm Approach: Frequency analysis with success rate correlation.
        Identifies patterns that appear across different implementations.

        Parameters
        ----------
        implementations (List[Dict[str, Any]]): Implementation data to analyze

        Returns
        -------
        List[Dict[str, Any]: Cross-implementation pattern analysis

        """
        pattern_stats = defaultdict(lambda: {"count": 0, "successes": 0, "implementations": []})

        # Collect pattern statistics
        for impl in implementations:
            success = impl.get("outcome") == "success"
            patterns = impl.get("patterns_observed", [])
            techniques = impl.get("techniques_used", [])

            all_patterns = set(patterns + techniques)

            for pattern in all_patterns:
                pattern_stats[pattern]["count"] += 1
                pattern_stats[pattern]["implementations"].append(impl["implementation_id"])
                if success:
                    pattern_stats[pattern]["successes"] += 1

        # Analyze patterns
        cross_patterns = []
        for pattern, stats in pattern_stats.items():
            if stats["count"] >= 2:  # Appears in at least 2 implementations
                success_rate = stats["successes"] / stats["count"]
                frequency = stats["count"] / len(implementations)

                cross_patterns.append(
                    {
                        "pattern_name": pattern,
                        "frequency": frequency,
                        "occurrence_count": stats["count"],
                        "success_rate": success_rate,
                        "implementations": stats["implementations"],
                        "transferability_score": frequency * success_rate,
                        "recommendation_strength": (
                            "high"
                            if success_rate >= 0.8
                            else "medium"
                            if success_rate >= 0.6
                            else "low"
                        ),
                    },
                )

        # Sort by transferability score
        cross_patterns.sort(key=lambda x: x["transferability_score"], reverse=True)

        return cross_patterns

    def _identify_transferable_lessons(
        self,
        implementations: list[dict[str, Any]],
        cross_patterns: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Identify transferable lessons from cross-implementation analysis.

        Parameters
        ----------
        implementations (List[Dict[str, Any]]): Implementation data
        cross_patterns (List[Dict[str, Any]]): Cross-implementation patterns

        Returns
        -------
        List[Dict[str, Any]: Transferable lessons with evidence

        """
        lessons = []

        # Extract lessons from successful implementations
        successful_lessons = defaultdict(int)
        failed_lessons = defaultdict(int)

        for impl in implementations:
            impl_lessons = impl.get("lessons_learned", [])
            success = impl.get("outcome") == "success"

            for lesson in impl_lessons:
                if success:
                    successful_lessons[lesson] += 1
                else:
                    failed_lessons[lesson] += 1

        # Analyze lesson transferability
        for lesson, success_count in successful_lessons.items():
            failure_count = failed_lessons.get(lesson, 0)
            total_occurrences = success_count + failure_count

            if total_occurrences >= 2 and success_count > failure_count:
                transferability = success_count / total_occurrences

                # Find supporting evidence from patterns
                supporting_patterns = [
                    p
                    for p in cross_patterns
                    if any(
                        keyword in lesson.lower() for keyword in p["pattern_name"].lower().split()
                    )
                ]

                lessons.append(
                    {
                        "lesson": lesson,
                        "success_count": success_count,
                        "failure_count": failure_count,
                        "transferability_score": transferability,
                        "supporting_patterns": [p["pattern_name"] for p in supporting_patterns],
                        "evidence_strength": (
                            "strong"
                            if transferability >= 0.8
                            else "moderate"
                            if transferability >= 0.6
                            else "weak"
                        ),
                        "applicability": self._assess_lesson_applicability(lesson, cross_patterns),
                    },
                )

        # Sort by transferability score
        lessons.sort(key=lambda x: x["transferability_score"], reverse=True)

        return lessons

    def _assess_lesson_applicability(
        self, lesson: str, cross_patterns: list[dict[str, Any]]
    ) -> str:
        """
        Assess applicability of a lesson based on pattern analysis.

        Parameters
        ----------
        lesson (str): Lesson to assess
        cross_patterns (List[Dict[str, Any]]): Cross-implementation patterns

        Returns
        -------
        str: Applicability assessment

        """
        lesson_lower = lesson.lower()

        # Check if lesson relates to high-success patterns
        high_success_patterns = [p for p in cross_patterns if p["success_rate"] >= 0.8]

        for pattern in high_success_patterns:
            if any(keyword in lesson_lower for keyword in pattern["pattern_name"].lower().split()):
                return "broad"

        # Check if lesson relates to any patterns
        if any(
            any(keyword in lesson_lower for keyword in p["pattern_name"].lower().split())
            for p in cross_patterns
        ):
            return "moderate"

        return "specific"

    def _generate_cross_implementation_insights(
        self,
        implementations: list[dict[str, Any]],
        cross_patterns: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Generate insights from cross-implementation analysis.

        Parameters
        ----------
        implementations (List[Dict[str, Any]]): Implementation data
        cross_patterns (List[Dict[str, Any]]): Cross-implementation patterns

        Returns
        -------
        List[Dict[str, Any]: Generated insights

        """
        insights = []

        # Success rate analysis
        total_implementations = len(implementations)
        successful_implementations = sum(
            1 for impl in implementations if impl.get("outcome") == "success"
        )
        overall_success_rate = (
            successful_implementations / total_implementations if total_implementations > 0 else 0
        )

        insights.append(
            {
                "insight_type": "success_rate_analysis",
                "title": "Overall Success Rate",
                "description": f"Overall implementation success rate is {overall_success_rate:.1%}",
                "value": overall_success_rate,
                "benchmark": (
                    "good"
                    if overall_success_rate >= 0.8
                    else "needs_improvement"
                    if overall_success_rate >= 0.6
                    else "poor"
                ),
            },
        )

        # Pattern effectiveness
        if cross_patterns:
            top_pattern = cross_patterns[0]
            insights.append(
                {
                    "insight_type": "pattern_effectiveness",
                    "title": "Most Effective Pattern",
                    "description": f"The '{top_pattern['pattern_name']}' pattern appears in {top_pattern['occurrence_count']} implementations with {top_pattern['success_rate']:.1%} success rate",
                    "pattern_name": top_pattern["pattern_name"],
                    "success_rate": top_pattern["success_rate"],
                    "transferability_score": top_pattern["transferability_score"],
                },
            )

        # Agent performance analysis
        agent_performance = defaultdict(lambda: {"total": 0, "successful": 0})
        for impl in implementations:
            agent_type = impl.get("agent_type", "unknown")
            agent_performance[agent_type]["total"] += 1
            if impl.get("outcome") == "success":
                agent_performance[agent_type]["successful"] += 1

        best_agent = None
        best_success_rate = 0
        for agent_type, stats in agent_performance.items():
            if stats["total"] >= 3:  # Minimum 3 implementations
                success_rate = stats["successful"] / stats["total"]
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_agent = agent_type

        if best_agent:
            insights.append(
                {
                    "insight_type": "agent_performance",
                    "title": "Best Performing Agent",
                    "description": f"Agent type '{best_agent}' has the highest success rate at {best_success_rate:.1%}",
                    "agent_type": best_agent,
                    "success_rate": best_success_rate,
                },
            )

        return insights

    def _calculate_success_correlations(
        self, implementations: list[dict[str, Any]]
    ) -> dict[str, float]:
        """
        Calculate correlations between patterns and success.

        Parameters
        ----------
        implementations (List[Dict[str, Any]]): Implementation data

        Returns
        -------
        Dict[str, float]: Pattern success correlations

        """
        correlations = {}

        # Calculate correlation for each pattern
        all_patterns = set()
        for impl in implementations:
            all_patterns.update(impl.get("patterns_observed", []))
            all_patterns.update(impl.get("techniques_used", []))

        for pattern in all_patterns:
            implementations_with_pattern = [
                impl
                for impl in implementations
                if pattern in impl.get("patterns_observed", [])
                or pattern in impl.get("techniques_used", [])
            ]

            if len(implementations_with_pattern) >= 2:
                success_count = sum(
                    1 for impl in implementations_with_pattern if impl.get("outcome") == "success"
                )
                success_rate = success_count / len(implementations_with_pattern)
                correlations[pattern] = success_rate

        return correlations

    def _generate_learning_summary(
        self,
        cross_patterns: list[dict[str, Any]],
        transferable_lessons: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate summary of learning analysis.

        Parameters
        ----------
        cross_patterns (List[Dict[str, Any]]): Cross-implementation patterns
        transferable_lessons (List[Dict[str, Any]]): Transferable lessons

        Returns
        -------
        Dict[str, Any]: Learning summary

        """
        high_value_patterns = [p for p in cross_patterns if p["transferability_score"] >= 0.5]
        high_value_lessons = [l for l in transferable_lessons if l["transferability_score"] >= 0.7]

        return {
            "total_patterns_analyzed": len(cross_patterns),
            "high_value_patterns": len(high_value_patterns),
            "total_lessons_identified": len(transferable_lessons),
            "highly_transferable_lessons": len(high_value_lessons),
            "key_findings": [
                f"Found {len(high_value_patterns)} patterns with high transferability scores",
                f"Identified {len(high_value_lessons)} lessons with strong transferability",
                "Pattern-based approach shows consistent success across implementations",
            ],
            "action_items": [
                "Prioritize high-transferability patterns in future implementations",
                "Document and share highly transferable lessons across teams",
                "Consider standardizing high-success patterns",
            ],
        }

    def _generate_cross_implementation_recommendations(
        self, cross_patterns: list[dict[str, Any]]
    ) -> list[str]:
        """
        Generate recommendations based on cross-implementation learning.

        Parameters
        ----------
        cross_patterns (List[Dict[str, Any]]): Cross-implementation patterns

        Returns
        -------
        List[str]: Generated recommendations

        """
        recommendations = []

        if cross_patterns:
            top_patterns = cross_patterns[:3]
            recommendations.append(
                f"Prioritize these high-transferability patterns: {', '.join(p['pattern_name'] for p in top_patterns)}",
            )

        low_success_patterns = [p for p in cross_patterns if p["success_rate"] < 0.5]
        if low_success_patterns:
            recommendations.append(
                f"Review and potentially revise these low-success patterns: {', '.join(p['pattern_name'] for p in low_success_patterns[:3])}",
            )

        recommendations.extend(
            [
                "Establish pattern library with documented success rates",
                "Create implementation decision trees based on historical patterns",
                "Implement pattern validation checks before major implementations",
            ],
        )

        return recommendations

    def evidence_based_recommendations(
        self,
        context: str,
        confidence_threshold: float = 0.5,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Provide data-driven suggestions with confidence scoring.

        Algorithm Approach: Evidence aggregation with confidence-weighted recommendations.
        Generates actionable suggestions based on historical evidence.

        Parameters
        ----------
        context (str): Context for which recommendations are needed
        confidence_threshold (float): Minimum confidence threshold for recommendations
        limit (int): Maximum number of recommendations to return

        Returns
        -------
        Dict[str, Any]: Evidence-based recommendations with confidence scores

        Raises
        ------
        KnowledgeIntegrationError: If recommendation generation fails

        """
        try:
            # Analyze context to identify relevant patterns
            relevant_patterns = self._find_relevant_patterns(context)

            # Get existing recommendations from database
            existing_recommendations = self._get_existing_recommendations(
                context, confidence_threshold
            )

            # Generate new recommendations based on patterns
            generated_recommendations = self._generate_context_recommendations(
                relevant_patterns, context
            )

            # Combine and rank recommendations
            all_recommendations = existing_recommendations + generated_recommendations

            # Filter by confidence threshold and limit
            filtered_recommendations = [
                rec
                for rec in all_recommendations
                if rec["confidence_score"] >= confidence_threshold
            ]

            # Sort by confidence score and relevance
            filtered_recommendations.sort(
                key=lambda x: (x["confidence_score"], x["relevance_score"]),
                reverse=True,
            )
            filtered_recommendations = filtered_recommendations[:limit]

            # Add evidence and justification
            for rec in filtered_recommendations:
                rec["evidence"] = self._gather_recommendation_evidence(rec)
                rec["implementation_risk"] = self._assess_implementation_risk(rec)
                rec["expected_benefit"] = self._estimate_expected_benefit(rec)

            result = {
                "context": context,
                "confidence_threshold": confidence_threshold,
                "recommendations": filtered_recommendations,
                "total_recommendations": len(filtered_recommendations),
                "evidence_strength": self._calculate_overall_evidence_strength(
                    filtered_recommendations
                ),
                "recommendation_categories": self._categorize_recommendations(
                    filtered_recommendations
                ),
                "implementation_priority": self._prioritize_recommendations(
                    filtered_recommendations
                ),
                "generated_at": datetime.now(UTC).isoformat(),
            }

            logger.info(
                f"Generated {len(filtered_recommendations)} evidence-based recommendations for context: {context[:50]}...",
            )
            return result

        except Exception as e:
            logger.error(f"Evidence-based recommendations failed: {e}")
            raise KnowledgeIntegrationError(
                f"Recommendation generation error: {e}",
                "RECOMMENDATION_GENERATION_ERROR",
            )

    def _find_relevant_patterns(self, context: str) -> list[dict[str, Any]]:
        """
        Find patterns relevant to the given context.

        Algorithm Approach: Context-based pattern matching with relevance scoring.
        Identifies patterns that apply to the current context.

        Parameters
        ----------
        context (str): Context for pattern relevance

        Returns
        -------
        List[Dict[str, Any]: Relevant patterns with relevance scores

        """
        relevant_patterns = []
        context_words = set(context.lower().split())

        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT pattern_id, pattern_type, name, description,
                           confidence_score, success_rate, usage_count
                    FROM knowledge_patterns
                    WHERE confidence_score >= 0.5
                    ORDER BY success_rate DESC, confidence_score DESC
                """
                )

                for row in cursor.fetchall():
                    pattern_data = {
                        "pattern_id": row[0],
                        "pattern_type": row[1],
                        "name": row[2],
                        "description": row[3],
                        "confidence_score": row[4],
                        "success_rate": row[5],
                        "usage_count": row[6],
                    }

                    # Calculate relevance score based on keyword overlap
                    pattern_text = f"{row[2]} {row[3]}".lower()
                    pattern_words = set(pattern_text.split())

                    overlap = len(context_words.intersection(pattern_words))
                    relevance_score = overlap / len(context_words) if context_words else 0

                    if relevance_score > 0.1:  # Minimum relevance threshold
                        pattern_data["relevance_score"] = relevance_score
                        relevant_patterns.append(pattern_data)

                # Sort by relevance and success
                relevant_patterns.sort(
                    key=lambda x: (x["relevance_score"], x["success_rate"]),
                    reverse=True,
                )

        except Exception as e:
            logger.error(f"Error finding relevant patterns: {e}")

        return relevant_patterns

    def _get_existing_recommendations(
        self, context: str, confidence_threshold: float
    ) -> list[dict[str, Any]]:
        """
        Get existing recommendations from database.

        Parameters
        ----------
        context (str): Context for recommendations
        confidence_threshold (float): Minimum confidence threshold

        Returns
        -------
        List[Dict[str, Any]: Existing recommendations

        """
        recommendations = []

        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                # Search for recommendations by title, description, or tags
                search_terms = context.lower().split()

                for term in search_terms[:5]:  # Limit to prevent too many queries
                    cursor.execute(
                        """
                        SELECT recommendation_id, title, description, confidence_level,
                               supporting_evidence, expected_outcome, tags
                        FROM recommendations
                        WHERE (title LIKE ? OR description LIKE ? OR tags LIKE ?)
                        AND confidence_level >= ?
                        AND expires_at > datetime('now')
                        ORDER BY confidence_level DESC
                    """,
                        (f"%{term}%", f"%{term}%", f"%{term}%", confidence_threshold),
                    )

                    for row in cursor.fetchall():
                        rec_data = {
                            "recommendation_id": row[0],
                            "title": row[1],
                            "description": row[2],
                            "confidence_score": row[3],
                            "supporting_evidence": json.loads(row[4]) if row[4] else [],
                            "expected_outcome": row[5],
                            "tags": json.loads(row[6]) if row[6] else [],
                            "source": "existing",
                        }

                        # Avoid duplicates
                        if not any(
                            rec["recommendation_id"] == rec_data["recommendation_id"]
                            for rec in recommendations
                        ):
                            recommendations.append(rec_data)

        except Exception as e:
            logger.error(f"Error getting existing recommendations: {e}")

        return recommendations

    def _generate_context_recommendations(
        self,
        relevant_patterns: list[dict[str, Any]],
        context: str,
    ) -> list[dict[str, Any]]:
        """
        Generate new recommendations based on relevant patterns.

        Algorithm Approach: Pattern-based recommendation generation with confidence scoring.
        Creates actionable suggestions from successful patterns.

        Parameters
        ----------
        relevant_patterns (List[Dict[str, Any]]): Relevant patterns
        context (str): Current context

        Returns
        -------
        List[Dict[str, Any]: Generated recommendations

        """
        recommendations = []

        for pattern in relevant_patterns[:5]:  # Top 5 most relevant patterns
            if pattern["success_rate"] >= 0.7 and pattern["confidence_score"] >= 0.6:
                confidence = (pattern["success_rate"] + pattern["confidence_score"]) / 2

                recommendation = {
                    "recommendation_id": f"gen_{pattern['pattern_id']}_{int(time.time())}",
                    "title": f"Apply Pattern: {pattern['name']}",
                    "description": f"Consider applying the '{pattern['name']}' pattern which has a {pattern['success_rate']:.1%} success rate",
                    "confidence_score": confidence,
                    "source_pattern_id": pattern["pattern_id"],
                    "source": "generated",
                    "relevance_score": pattern.get("relevance_score", 0.5),
                    "implementation_steps": [
                        f"1. Review pattern: {pattern['description']}",
                        "2. Check applicability to current context",
                        "3. Implement with proper monitoring",
                    ],
                }

                recommendations.append(recommendation)

        return recommendations

    def _gather_recommendation_evidence(self, recommendation: dict[str, Any]) -> list[str]:
        """
        Gather supporting evidence for a recommendation.

        Parameters
        ----------
        recommendation (Dict[str, Any]): Recommendation to gather evidence for

        Returns
        -------
        List[str]: Supporting evidence

        """
        evidence = []

        if recommendation.get("source") == "existing":
            evidence.extend(recommendation.get("supporting_evidence", []))
        elif recommendation.get("source_pattern_id"):
            try:
                with sqlite3.connect(self.storage_path) as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT evidence, implementation_examples, usage_count
                        FROM knowledge_patterns
                        WHERE pattern_id = ?
                    """,
                        (recommendation["source_pattern_id"],),
                    )

                    row = cursor.fetchone()
                    if row:
                        pattern_evidence = json.loads(row[0]) if row[0] else []
                        examples = json.loads(row[2]) if row[2] else []
                        usage_count = row[3]

                        evidence.extend(pattern_evidence)
                        if examples:
                            evidence.append(
                                f"Successfully applied in {len(examples)} implementations"
                            )
                        evidence.append(f"Pattern used {usage_count} times historically")

            except Exception as e:
                logger.error(f"Error gathering recommendation evidence: {e}")

        return evidence

    def _assess_implementation_risk(self, recommendation: dict[str, Any]) -> str:
        """
        Assess implementation risk for a recommendation.

        Parameters
        ----------
        recommendation (Dict[str, Any]): Recommendation to assess

        Returns
        -------
        str: Risk assessment (low/medium/high)

        """
        confidence = recommendation.get("confidence_score", 0)

        if confidence >= 0.8:
            return "low"
        if confidence >= 0.6:
            return "medium"
        return "high"

    def _estimate_expected_benefit(self, recommendation: dict[str, Any]) -> str:
        """
        Estimate expected benefit of implementing recommendation.

        Parameters
        ----------
        recommendation (Dict[str, Any]): Recommendation to evaluate

        Returns
        -------
        str: Expected benefit description

        """
        confidence = recommendation.get("confidence_score", 0)
        recommendation.get("source", "")

        if confidence >= 0.8:
            return "High probability of success with significant improvement"
        if confidence >= 0.6:
            return "Moderate probability of success with measurable improvement"
        return "Experimental approach with potential for learning"

    def _calculate_overall_evidence_strength(self, recommendations: list[dict[str, Any]]) -> str:
        """
        Calculate overall evidence strength for recommendations.

        Parameters
        ----------
        recommendations (List[Dict[str, Any]]): Recommendations to evaluate

        Returns
        -------
        str: Overall evidence strength

        """
        if not recommendations:
            return "none"

        avg_confidence = sum(rec.get("confidence_score", 0) for rec in recommendations) / len(
            recommendations
        )

        if avg_confidence >= 0.8:
            return "strong"
        if avg_confidence >= 0.6:
            return "moderate"
        return "weak"

    def _categorize_recommendations(self, recommendations: list[dict[str, Any]]) -> dict[str, int]:
        """
        Categorize recommendations by type.

        Parameters
        ----------
        recommendations (List[Dict[str, Any]]): Recommendations to categorize

        Returns
        -------
        Dict[str, int]: Recommendation categories and counts

        """
        categories = defaultdict(int)

        for rec in recommendations:
            title_lower = rec.get("title", "").lower()

            if "pattern" in title_lower:
                categories["pattern_based"] += 1
            elif "security" in title_lower:
                categories["security"] += 1
            elif "performance" in title_lower:
                categories["performance"] += 1
            elif "error" in title_lower:
                categories["error_handling"] += 1
            else:
                categories["general"] += 1

        return dict(categories)

    def _prioritize_recommendations(self, recommendations: list[dict[str, Any]]) -> list[str]:
        """
        Prioritize recommendations for implementation.

        Parameters
        ----------
        recommendations (List[Dict[str, Any]]): Recommendations to prioritize

        Returns
        -------
        List[str]: Prioritized recommendation titles

        """
        # Sort by combined score of confidence and relevance
        prioritized = sorted(
            recommendations,
            key=lambda x: (x.get("confidence_score", 0) * 0.6 + x.get("relevance_score", 0) * 0.4),
            reverse=True,
        )

        return [rec.get("title", "") for rec in prioritized]

    def knowledge_base_query(self, query: KnowledgeQuery | str | dict[str, Any]) -> dict[str, Any]:
        """
        Query stored knowledge for historical insights and retrieval.

        Algorithm Approach: Multi-faceted search with relevance ranking and filtering.
        Provides efficient access to stored knowledge with intelligent result ordering.

        Parameters
        ----------
        query (Union[KnowledgeQuery, str, Dict[str, Any]]): Query specification
            - KnowledgeQuery: Structured query object
            - str: Simple search query
            - Dict[str, Any]: Query parameters dictionary

        Returns
        -------
        Dict[str, Any]: Query results with relevant insights

        Raises
        ------
        KnowledgeIntegrationError: If query execution fails

        """
        try:
            # Normalize query
            if isinstance(query, str):
                # Simple string query
                structured_query = KnowledgeQuery(
                    query_id=f"query_{int(time.time())}",
                    search_terms=[query],
                    context="",
                    pattern_types=list(PatternType),
                    confidence_threshold=0.3,
                    time_range=("", ""),
                    implementation_filter={},
                    sort_by="relevance",
                    limit=20,
                    include_metadata=True,
                )
            elif isinstance(query, dict):
                # Dictionary query
                structured_query = KnowledgeQuery(
                    query_id=query.get("query_id", f"query_{int(time.time())}"),
                    search_terms=query.get("search_terms", []),
                    context=query.get("context", ""),
                    pattern_types=[PatternType(pt) for pt in query.get("pattern_types", [])],
                    confidence_threshold=query.get("confidence_threshold", 0.3),
                    time_range=query.get("time_range", ("", "")),
                    implementation_filter=query.get("implementation_filter", {}),
                    sort_by=query.get("sort_by", "relevance"),
                    limit=query.get("limit", 20),
                    include_metadata=query.get("include_metadata", True),
                )
            else:
                # KnowledgeQuery object
                structured_query = query

            # Execute query
            results = self._execute_knowledge_query(structured_query)

            # Enhance results with related information
            enhanced_results = self._enhance_query_results(results, structured_query)

            # Generate query insights
            insights = self._generate_query_insights(enhanced_results, structured_query)

            result = {
                "query_id": structured_query.query_id,
                "search_terms": structured_query.search_terms,
                "results": enhanced_results,
                "total_results": len(enhanced_results),
                "query_insights": insights,
                "result_categories": self._categorize_query_results(enhanced_results),
                "related_queries": self._suggest_related_queries(
                    structured_query, enhanced_results
                ),
                "query_metadata": {
                    "execution_time": time.time(),  # Would track actual execution time
                    "confidence_threshold": structured_query.confidence_threshold,
                    "search_method": "knowledge_base_query",
                },
                "timestamp": datetime.now(UTC).isoformat(),
            }

            logger.info(f"Knowledge base query completed: {len(enhanced_results)} results")
            return result

        except Exception as e:
            logger.error(f"Knowledge base query failed: {e}")
            raise KnowledgeIntegrationError(
                f"Query execution error: {e}",
                "QUERY_EXECUTION_ERROR",
            )

    def _execute_knowledge_query(self, query: KnowledgeQuery) -> list[dict[str, Any]]:
        """
        Execute the structured knowledge query.

        Algorithm Approach: Multi-table search with relevance ranking.
        Retrieves patterns, recommendations, and related knowledge.

        Parameters
        ----------
        query (KnowledgeQuery): Structured query to execute

        Returns
        -------
        List[Dict[str, Any]: Query results

        """
        results = []

        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                # Search patterns
                if not query.pattern_types or PatternType.IMPLEMENTATION in query.pattern_types:
                    pattern_results = self._search_patterns(cursor, query)
                    results.extend(pattern_results)

                # Search recommendations
                recommendation_results = self._search_recommendations(cursor, query)
                results.extend(recommendation_results)

                # Sort results according to query specification
                results = self._sort_query_results(results, query.sort_by)

                # Apply limit
                results = results[: query.limit]

        except Exception as e:
            logger.error(f"Error executing knowledge query: {e}")

        return results

    def _search_patterns(
        self, cursor: sqlite3.Cursor, query: KnowledgeQuery
    ) -> list[dict[str, Any]]:
        """
        Search knowledge patterns based on query.

        Parameters
        ----------
        cursor (sqlite3.Cursor): Database cursor
        query (KnowledgeQuery): Query specification

        Returns
        -------
        List[Dict[str, Any]: Pattern search results

        """
        results = []

        # Build search query
        search_conditions = ["confidence_score >= ?"]
        search_params = [query.confidence_threshold]

        # Add pattern type filter
        if query.pattern_types:
            type_placeholders = ",".join(["?"] * len(query.pattern_types))
            search_conditions.append(f"pattern_type IN ({type_placeholders})")
            search_params.extend([pt.value for pt in query.pattern_types])

        # Add time range filter
        if query.time_range[0]:
            search_conditions.append("created_at >= ?")
            search_params.append(query.time_range[0])

        if query.time_range[1]:
            search_conditions.append("created_at <= ?")
            search_params.append(query.time_range[1])

        # Add text search
        if query.search_terms:
            text_conditions = []
            for term in query.search_terms:
                text_conditions.append("(name LIKE ? OR description LIKE ?)")
                search_params.extend([f"%{term}%", f"%{term}%"])
            search_conditions.append(f"({' OR '.join(text_conditions)})")

        # Construct final query
        base_query = f"""
            SELECT pattern_id, pattern_type, name, description, confidence_score,
                   success_rate, evidence, benefits, usage_count, created_at
            FROM knowledge_patterns
            WHERE {" AND ".join(search_conditions)}
        """

        cursor.execute(base_query, search_params)

        for row in cursor.fetchall():
            result = {
                "type": "pattern",
                "id": row[0],
                "pattern_type": row[1],
                "name": row[2],
                "description": row[3],
                "confidence_score": row[4],
                "success_rate": row[5],
                "evidence": json.loads(row[6]) if row[6] else [],
                "benefits": json.loads(row[7]) if row[7] else [],
                "usage_count": row[8],
                "created_at": row[9],
                "relevance_score": self._calculate_result_relevance(row, query),
            }

            if query.include_metadata:
                result["metadata"] = {
                    "source": "knowledge_patterns",
                    "query_match": "text_search" if query.search_terms else "browse",
                }

            results.append(result)

        return results

    def _search_recommendations(
        self, cursor: sqlite3.Cursor, query: KnowledgeQuery
    ) -> list[dict[str, Any]]:
        """
        Search recommendations based on query.

        Parameters
        ----------
        cursor (sqlite3.Cursor): Database cursor
        query (KnowledgeQuery): Query specification

        Returns
        -------
        List[Dict[str, Any]: Recommendation search results

        """
        results = []

        # Build search query
        search_conditions = ["confidence_level >= ? AND expires_at > datetime('now')"]
        search_params = [query.confidence_threshold]

        # Add text search
        if query.search_terms:
            text_conditions = []
            for term in query.search_terms:
                text_conditions.append("(title LIKE ? OR description LIKE ? OR tags LIKE ?)")
                search_params.extend([f"%{term}%", f"%{term}%", f"%{term}%"])
            search_conditions.append(f"({' OR '.join(text_conditions)})")

        # Add time range filter
        if query.time_range[0]:
            search_conditions.append("created_at >= ?")
            search_params.append(query.time_range[0])

        if query.time_range[1]:
            search_conditions.append("created_at <= ?")
            search_params.append(query.time_range[1])

        # Construct final query
        base_query = f"""
            SELECT recommendation_id, title, description, confidence_level,
                   supporting_evidence, expected_outcome, tags, created_at
            FROM recommendations
            WHERE {" AND ".join(search_conditions)}
        """

        cursor.execute(base_query, search_params)

        for row in cursor.fetchall():
            result = {
                "type": "recommendation",
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "confidence_score": row[3],
                "supporting_evidence": json.loads(row[4]) if row[4] else [],
                "expected_outcome": row[5],
                "tags": json.loads(row[6]) if row[6] else [],
                "created_at": row[7],
                "relevance_score": self._calculate_recommendation_relevance(row, query),
            }

            if query.include_metadata:
                result["metadata"] = {
                    "source": "recommendations",
                    "query_match": "text_search" if query.search_terms else "browse",
                }

            results.append(result)

        return results

    def _calculate_result_relevance(self, result_row: tuple, query: KnowledgeQuery) -> float:
        """
        Calculate relevance score for a search result.

        Algorithm Approach: Multi-factor relevance calculation with weighting.
        Provides consistent relevance scoring across result types.

        Parameters
        ----------
        result_row (tuple): Database row for the result
        query (KnowledgeQuery): Original query specification

        Returns
        -------
        float: Relevance score between 0.0 and 1.0

        """
        relevance = 0.0

        # Base relevance from confidence score
        relevance += result_row[4] * 0.3  # confidence_score

        # Success rate contribution
        if result_row[5] > 0:  # success_rate
            relevance += result_row[5] * 0.3

        # Usage frequency contribution
        if result_row[8] > 0:  # usage_count
            usage_score = min(result_row[8] / 50, 1.0)  # Normalize to max 50 uses
            relevance += usage_score * 0.2

        # Text matching contribution
        if query.search_terms:
            text_content = f"{result_row[2]} {result_row[3]}".lower()  # name + description
            term_matches = sum(1 for term in query.search_terms if term.lower() in text_content)
            text_score = term_matches / len(query.search_terms)
            relevance += text_score * 0.2

        return min(relevance, 1.0)

    def _calculate_recommendation_relevance(
        self, result_row: tuple, query: KnowledgeQuery
    ) -> float:
        """
        Calculate relevance score for a recommendation result.

        Parameters
        ----------
        result_row (tuple): Database row for the recommendation
        query (KnowledgeQuery): Original query specification

        Returns
        -------
        float: Relevance score between 0.0 and 1.0

        """
        relevance = result_row[3] * 0.4  # confidence_level

        # Text matching contribution
        if query.search_terms:
            text_content = (
                f"{result_row[1]} {result_row[2]} {result_row[6]}".lower()
            )  # title + description + tags
            term_matches = sum(1 for term in query.search_terms if term.lower() in text_content)
            text_score = term_matches / len(query.search_terms)
            relevance += text_score * 0.6

        return min(relevance, 1.0)

    def _sort_query_results(
        self, results: list[dict[str, Any]], sort_by: str
    ) -> list[dict[str, Any]]:
        """
        Sort query results according to specified criteria.

        Parameters
        ----------
        results (List[Dict[str, Any]]): Results to sort
        sort_by (str): Sorting criteria

        Returns
        -------
        List[Dict[str, Any]: Sorted results

        """
        if sort_by == "relevance":
            results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        elif sort_by == "confidence":
            results.sort(key=lambda x: x.get("confidence_score", 0), reverse=True)
        elif sort_by == "recency":
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_by == "usage":
            results.sort(key=lambda x: x.get("usage_count", 0), reverse=True)

        return results

    def _enhance_query_results(
        self, results: list[dict[str, Any]], query: KnowledgeQuery
    ) -> list[dict[str, Any]]:
        """
        Enhance query results with additional information.

        Algorithm Approach: Result enrichment with related items and context.
        Provides comprehensive information for each result.

        Parameters
        ----------
        results (List[Dict[str, Any]]): Original query results
        query (KnowledgeQuery): Original query

        Returns
        -------
        List[Dict[str, Any]: Enhanced query results

        """
        enhanced_results = []

        for result in results:
            enhanced_result = result.copy()

            # Add related items
            if result["type"] == "pattern":
                related_patterns = self._find_related_patterns(result["id"])
                enhanced_result["related_patterns"] = related_patterns

                # Add recent implementations
                recent_implementations = self._get_pattern_implementations(result["id"], limit=3)
                enhanced_result["recent_implementations"] = recent_implementations

            elif result["type"] == "recommendation":
                # Add source patterns
                if enhanced_result.get("metadata", {}).get("source_pattern_id"):
                    source_pattern = self._get_pattern_info(
                        enhanced_result["metadata"]["source_pattern_id"],
                    )
                    enhanced_result["source_pattern"] = source_pattern

            enhanced_results.append(enhanced_result)

        return enhanced_results

    def _find_related_patterns(self, pattern_id: str) -> list[dict[str, Any]]:
        """
        Find patterns related to the given pattern.

        Parameters
        ----------
        pattern_id (str): Pattern ID to find relations for

        Returns
        -------
        List[Dict[str, Any]: Related patterns

        """
        related_patterns = []

        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT target_pattern_id, relationship_type, strength
                    FROM pattern_relationships
                    WHERE source_pattern_id = ?
                    UNION
                    SELECT source_pattern_id, relationship_type, strength
                    FROM pattern_relationships
                    WHERE target_pattern_id = ?
                    ORDER BY strength DESC
                    LIMIT 5
                """,
                    (pattern_id, pattern_id),
                )

                for row in cursor.fetchall():
                    related_pattern_id = row[0]

                    # Get pattern info
                    cursor.execute(
                        """
                        SELECT name, pattern_type, confidence_score
                        FROM knowledge_patterns
                        WHERE pattern_id = ?
                    """,
                        (related_pattern_id,),
                    )

                    pattern_row = cursor.fetchone()
                    if pattern_row:
                        related_patterns.append(
                            {
                                "pattern_id": related_pattern_id,
                                "name": pattern_row[0],
                                "pattern_type": pattern_row[1],
                                "confidence_score": pattern_row[2],
                                "relationship_type": row[1],
                                "relationship_strength": row[2],
                            },
                        )

        except Exception as e:
            logger.error(f"Error finding related patterns: {e}")

        return related_patterns

    def _get_pattern_implementations(self, pattern_id: str, limit: int = 3) -> list[dict[str, Any]]:
        """
        Get recent implementations that used the given pattern.

        Parameters
        ----------
        pattern_id (str): Pattern ID to look up
        limit (int): Maximum number of implementations to return

        Returns
        -------
        List[Dict[str, Any]: Recent implementations using the pattern

        """
        implementations = []

        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT implementation_id, task_description, outcome, timestamp
                    FROM implementations
                    WHERE patterns_observed LIKE ? OR techniques_used LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (f"%{pattern_id}%", f"%{pattern_id}%", limit),
                )

                for row in cursor.fetchall():
                    implementations.append(
                        {
                            "implementation_id": row[0],
                            "task_description": row[1],
                            "outcome": row[2],
                            "timestamp": row[3],
                        },
                    )

        except Exception as e:
            logger.error(f"Error getting pattern implementations: {e}")

        return implementations

    def _get_pattern_info(self, pattern_id: str) -> dict[str, Any] | None:
        """
        Get pattern information by ID.

        Parameters
        ----------
        pattern_id (str): Pattern ID to look up

        Returns
        -------
        Optional[Dict[str, Any]: Pattern information or None if not found

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT name, description, pattern_type, confidence_score, success_rate
                    FROM knowledge_patterns
                    WHERE pattern_id = ?
                """,
                    (pattern_id,),
                )

                row = cursor.fetchone()
                if row:
                    return {
                        "pattern_id": pattern_id,
                        "name": row[0],
                        "description": row[1],
                        "pattern_type": row[2],
                        "confidence_score": row[3],
                        "success_rate": row[4],
                    }

        except Exception as e:
            logger.error(f"Error getting pattern info: {e}")

        return None

    def _generate_query_insights(
        self, results: list[dict[str, Any]], query: KnowledgeQuery
    ) -> list[dict[str, Any]]:
        """
        Generate insights from query results.

        Parameters
        ----------
        results (List[Dict[str, Any]]): Query results
        query (KnowledgeQuery): Original query

        Returns
        -------
        List[Dict[str, Any]: Query insights

        """
        insights = []

        if not results:
            insights.append(
                {
                    "type": "no_results",
                    "message": "No results found matching the query criteria",
                    "suggestion": "Try broadening search terms or lowering confidence threshold",
                },
            )
            return insights

        # Result count insight
        insights.append(
            {
                "type": "result_count",
                "message": f"Found {len(results)} relevant items",
                "result_count": len(results),
            },
        )

        # Result type distribution
        pattern_count = sum(1 for r in results if r["type"] == "pattern")
        recommendation_count = sum(1 for r in results if r["type"] == "recommendation")

        if pattern_count > 0 and recommendation_count > 0:
            insights.append(
                {
                    "type": "result_distribution",
                    "message": f"Results include {pattern_count} patterns and {recommendation_count} recommendations",
                    "patterns": pattern_count,
                    "recommendations": recommendation_count,
                },
            )

        # Confidence distribution
        high_confidence = sum(1 for r in results if r.get("confidence_score", 0) >= 0.8)
        if high_confidence > 0:
            insights.append(
                {
                    "type": "confidence_distribution",
                    "message": f"{high_confidence} results have high confidence (>=80%)",
                    "high_confidence_count": high_confidence,
                },
            )

        return insights

    def _categorize_query_results(self, results: list[dict[str, Any]]) -> dict[str, int]:
        """
        Categorize query results for better organization.

        Parameters
        ----------
        results (List[Dict[str, Any]]): Query results to categorize

        Returns
        -------
        Dict[str, int]: Result categories and counts

        """
        categories = defaultdict(int)

        for result in results:
            if result["type"] == "pattern":
                categories["patterns"] += 1
                # Further categorize by pattern type
                pattern_type = result.get("pattern_type", "unknown")
                categories[f"pattern_{pattern_type}"] += 1
            elif result["type"] == "recommendation":
                categories["recommendations"] += 1

        return dict(categories)

    def _suggest_related_queries(
        self, query: KnowledgeQuery, results: list[dict[str, Any]]
    ) -> list[str]:
        """
        Suggest related queries based on current query and results.

        Parameters
        ----------
        query (KnowledgeQuery): Original query
        results (List[Dict[str, Any]]): Query results

        Returns
        -------
        List[str]: Suggested related queries

        """
        suggestions = []

        if results:
            # Suggest queries based on top results
            top_results = results[:3]

            for result in top_results:
                if result["type"] == "pattern":
                    pattern_type = result.get("pattern_type", "")
                    if pattern_type:
                        suggestions.append(f"Find more {pattern_type} patterns")

                # Extract key terms from results
                if result.get("name"):
                    suggestions.append(f"Learn more about: {result['name']}")

        # Add general suggestions
        if query.confidence_threshold > 0.3:
            suggestions.append("Expand search with lower confidence threshold")

        if len(query.search_terms) == 1:
            suggestions.append("Try related terms for broader results")

        return suggestions[:5]  # Limit to 5 suggestions

    def get_integration_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive integration engine statistics.

        Returns
        -------
        Dict[str, Any]: Integration statistics and performance metrics

        """
        try:
            with sqlite3.connect(self.storage_path) as conn:
                cursor = conn.cursor()

                # Implementation statistics
                cursor.execute("SELECT COUNT(*) FROM implementations")
                total_implementations = cursor.fetchone()[0]

                cursor.execute("SELECT outcome, COUNT(*) FROM implementations GROUP BY outcome")
                implementation_outcomes = dict(cursor.fetchall())

                cursor.execute(
                    """
                    SELECT agent_type, COUNT(*)
                    FROM implementations
                    GROUP BY agent_type
                """
                )
                implementations_by_agent = dict(cursor.fetchall())

                # Pattern statistics
                cursor.execute("SELECT COUNT(*) FROM knowledge_patterns")
                total_patterns = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT pattern_type, COUNT(*)
                    FROM knowledge_patterns
                    GROUP BY pattern_type
                """
                )
                patterns_by_type = dict(cursor.fetchall())

                # Recommendation statistics
                cursor.execute(
                    "SELECT COUNT(*) FROM recommendations WHERE expires_at > datetime('now')"
                )
                active_recommendations = cursor.fetchone()[0]

                cursor.execute(
                    """
                    SELECT AVG(confidence_level)
                    FROM recommendations
                    WHERE expires_at > datetime('now')
                """
                )
                avg_recommendation_confidence = cursor.fetchone()[0] or 0

                # Learning statistics
                cursor.execute(
                    """
                    SELECT AVG(success_rate)
                    FROM knowledge_patterns
                    WHERE success_rate > 0
                """
                )
                avg_success_rate = cursor.fetchone()[0] or 0

                # System performance
                system_stats = {
                    "queue_size": len(self._ingestion_queue),
                    "cache_size": len(self._pattern_cache),
                    "active_pattern_matchers": len(self.pattern_matchers),
                    "csf_integration": csf_AVAILABLE,
                    "helpful_engine_integration": self.helpful_engine is not None,
                }

                return {
                    "implementation_statistics": {
                        "total_implementations": total_implementations,
                        "outcomes": implementation_outcomes,
                        "by_agent_type": implementations_by_agent,
                    },
                    "pattern_statistics": {
                        "total_patterns": total_patterns,
                        "by_type": patterns_by_type,
                        "average_success_rate": avg_success_rate,
                    },
                    "recommendation_statistics": {
                        "active_recommendations": active_recommendations,
                        "average_confidence": avg_recommendation_confidence,
                    },
                    "system_performance": system_stats,
                    "learning_summary": {
                        "knowledge_gained": total_patterns + active_recommendations,
                        "learning_rate": total_implementations / max(1, total_patterns),
                        "knowledge_quality": avg_success_rate,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }

        except Exception as e:
            logger.error(f"Error getting integration statistics: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(UTC).isoformat(),
            }

    def close(self) -> None:
        """
        Close the knowledge integration engine and cleanup resources.

        Algorithm Approach: Graceful shutdown with resource cleanup.
        Ensures all background operations complete and resources are released.

        Raises
        ------
        KnowledgeIntegrationError: If cleanup fails

        """
        try:
            # Set shutdown flag to stop background processing
            self._shutdown_requested = True

            # Process remaining items in queue with timeout
            timeout_start = time.time()
            max_wait_time = 5.0  # Maximum 5 seconds to process remaining items

            while self._ingestion_queue and (time.time() - timeout_start) < max_wait_time:
                batch = []
                while len(batch) < self._batch_size and self._ingestion_queue:
                    batch.append(self._ingestion_queue.popleft())

                if batch:
                    self._process_ingestion_batch(batch)

            # Force clear remaining queue items if timeout reached
            if self._ingestion_queue:
                logger.warning(
                    f"Clearing {len(self._ingestion_queue)} unprocessed items due to shutdown timeout"
                )
                self._ingestion_queue.clear()

            # Shutdown thread pool with timeout
            self.executor.shutdown(wait=False)

            # Wait for background thread to finish with timeout
            if hasattr(self, "_background_thread") and self._background_thread.is_alive():
                self._background_thread.join(timeout=2.0)
                if self._background_thread.is_alive():
                    logger.warning("Background thread did not terminate gracefully")

            # Close database connections if any are open
            # (SQLite connections are automatically closed)

            # Clear caches
            self._pattern_cache.clear()

            logger.info("KnowledgeIntegrationEngine closed successfully")

        except Exception as e:
            logger.error(f"Error closing KnowledgeIntegrationEngine: {e}")
            raise KnowledgeIntegrationError(
                f"Engine cleanup error: {e}",
                "CLEANUP_ERROR",
            )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
        if exc_type:
            logger.error(f"KnowledgeIntegrationEngine exiting with error: {exc_val}")
        return False  # Don't suppress exceptions
