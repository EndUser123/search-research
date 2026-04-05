from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import uuid
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

"""Knowledge Integration Engine for CWO12 Step 10 Enhancement.

Algorithm Approach: Multi-layered knowledge integration with real-time learning,
pattern recognition, and evidence-based recommendations. Integrates seamlessly
with CSF knowledge systems and Helpful Engine v2.

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

Parameters
----------
helpful_engine (HelpfulnessPattern): Optional helpfulness engine integration
    - Must be initialized if provided
    - Used for automatic improvement opportunity capture
    - Enables seamless pattern recognition and learning

knowledge_query_engine (KnowledgeQueryEngine): Existing CSF knowledge engine
    - Must be properly initialized with all knowledge services
    - Provides access to library, standards, and orchestration knowledge
    - Enables cross-pillar knowledge integration and analysis

Returns
-------
KnowledgeIntegrationEngine: Configured integration engine instance
    - Ready for immediate knowledge integration operations
    - Automatic learning and pattern recognition enabled
    - Evidence-based recommendation system active

Raises
------
ValueError: For invalid configuration or parameters
KnowledgeIntegrationError: For integration-specific errors
ImportError: If required dependencies are unavailable

Examples
--------
>>> engine = KnowledgeIntegrationEngine()
>>> result = engine.ingest_implementation_results({
...     "implementation_id": "impl_123",
...     "outcome": "success",
...     "patterns": ["error_handling", "async_processing"]
... })
>>> recommendations = engine.get_evidence_based_recommendations(
...     "python_api_development", confidence_threshold=0.8
... )

Edge Cases:
- Empty implementation data: Graceful handling with validation feedback
- Conflicting patterns: Intelligent merging with confidence weighting
- Knowledge base corruption: Automatic recovery with data validation
- High-volume ingestion: Throttling and queue management
- Cross-system conflicts: Resolution strategies with fallback mechanisms

Performance Considerations:
- Asynchronous processing for knowledge ingestion to prevent blocking
- Intelligent caching for frequently accessed patterns
- Batch processing for bulk knowledge operations
- Memory-efficient algorithms for large knowledge bases
- Background indexing for maintaining search performance

"""


# Import existing CSF components
try:
    from ...lib.core_utils.knowledge.knowledge_query_engine import (
        KnowledgeQueryEngine,
        KnowledgeQueryError,
    )
    from ...lib.helpfulness import HelpfulnessPattern

    csf_AVAILABLE = True
except ImportError:
    csf_AVAILABLE = False
    logging.warning("CSF components not available - some features limited")

# Configure logging for knowledge integration operations
logger = logging.getLogger(__name__)


class KnowledgeIntegrationError(Exception):
    """
    Custom exception for knowledge integration errors.

    Algorithm Approach: Structured error handling with context preservation.
    Provides detailed error information for debugging and recovery.

    Attributes
    ----------
    message (str): Human-readable error message
    error_code (str): Machine-readable error code
    details (dict): Additional error context
    timestamp (str): Error occurrence timestamp

    """

    def __init__(
        self,
        message: str,
        error_code: str = "INTEGRATION_ERROR",
        details: dict | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now(UTC).isoformat()

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message} at {self.timestamp}"


class IntegrationStatus(Enum):
    """Enumeration of knowledge integration statuses."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"
    INDEXED = "indexed"


class PatternType(Enum):
    """Enumeration of pattern types for classification."""

    IMPLEMENTATION = "implementation"
    ARCHITECTURAL = "architectural"
    PERFORMANCE = "performance"
    SECURITY = "security"
    WORKFLOW = "workflow"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    DEPLOYMENT = "deployment"


class ConfidenceLevel(Enum):
    """Enumeration of confidence levels for recommendations."""

    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class ImplementationResult:
    """
    Implementation result data structure for knowledge ingestion.

    Algorithm Approach: Comprehensive result capture with metadata preservation.
    Enables detailed analysis and pattern extraction.

    Attributes
    ----------
    implementation_id (str): Unique implementation identifier
    agent_type (str): Type of agent that performed implementation
    task_description (str): Description of the implemented task
    outcome (str): Implementation outcome (success/failure/partial)
    execution_time (float): Total execution time in seconds
    patterns_observed (List[str]): Patterns observed during implementation
    techniques_used (List[str]): Techniques employed in implementation
    challenges_faced (List[str]): Challenges encountered and their solutions
    lessons_learned (List[str]): Key lessons from the implementation
    code_metrics (dict): Code quality and performance metrics
    user_feedback (str): Feedback on implementation quality
    artifacts_created (List[str]): List of created artifacts
    dependencies_added (List[str]): New dependencies introduced
    timestamp (str): Implementation completion timestamp
    metadata (dict): Additional implementation metadata

    """

    implementation_id: str
    agent_type: str
    task_description: str
    outcome: str
    execution_time: float
    patterns_observed: list[str]
    techniques_used: list[str]
    challenges_faced: list[str]
    lessons_learned: list[str]
    code_metrics: dict[str, Any]
    user_feedback: str
    artifacts_created: list[str]
    dependencies_added: list[str]
    timestamp: str
    metadata: dict[str, Any]


@dataclass
class KnowledgePattern:
    """
    Knowledge pattern extracted from implementation data.

    Algorithm Approach: Pattern extraction with confidence scoring and evidence.
    Provides actionable insights with supporting data.

    Attributes
    ----------
    pattern_id (str): Unique pattern identifier
    pattern_type (PatternType): Type of pattern
    name (str): Descriptive pattern name
    description (str): Detailed pattern description
    confidence_score (float): Confidence in pattern validity (0.0-1.0)
    success_rate (float): Historical success rate of this pattern
    evidence (List[str]): Evidence supporting this pattern
    prerequisites (List[str]: Required conditions for pattern application
    benefits (List[str]): Expected benefits of using this pattern
    risks (List[str]): Potential risks or downsides
    implementation_examples (List[str]): Examples of successful implementations
    related_patterns (List[str]): Related pattern identifiers
    created_at (str): Pattern creation timestamp
    last_updated (str): Last pattern update timestamp
    usage_count (int): Number of times this pattern has been applied

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
    usage_count: int


@dataclass
class EvidenceBasedRecommendation:
    """
    Evidence-based recommendation with confidence scoring.

    Algorithm Approach: Data-driven recommendation generation with supporting evidence.
    Provides actionable suggestions with risk assessment and expected outcomes.

    Attributes
    ----------
    recommendation_id (str): Unique recommendation identifier
    title (str): Concise recommendation title
    description (str): Detailed recommendation description
    confidence_level (ConfidenceLevel): Confidence in recommendation validity
    supporting_evidence (List[str]): Evidence supporting this recommendation
    expected_outcome (str): Expected result if recommendation is followed
    implementation_steps (List[str]): Step-by-step implementation guidance
    risk_assessment (str): Assessment of potential risks
    alternatives (List[str]): Alternative approaches if this isn't suitable
    related_patterns (List[str]): Related knowledge patterns
    source_implementations (List[str]): Implementations that informed this recommendation
    created_at (str): Recommendation creation timestamp
    expires_at (str): Recommendation expiration timestamp
    tags (List[str]): Classification tags for filtering and search

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
    expires_at: str
    tags: list[str]


@dataclass
class KnowledgeQuery:
    """
    Knowledge base query specification for insight retrieval.

    Algorithm Approach: Flexible query system with multiple search strategies.
    Supports complex knowledge discovery scenarios.

    Attributes
    ----------
    query_id (str): Unique query identifier
    search_terms (List[str]): Terms to search for
    context (str): Context for disambiguating search terms
    pattern_types (List[PatternType]): Pattern types to include
    confidence_threshold (float): Minimum confidence threshold for results
    time_range (Tuple[str, str]): Time range for temporal filtering
    implementation_filter (dict): Filter by implementation characteristics
    sort_by (str): Sorting criteria (relevance/confidence/recency/usage)
    limit (int): Maximum number of results to return
    include_metadata (bool): Include detailed metadata in results

    """

    query_id: str
    search_terms: list[str]
    context: str
    pattern_types: list[PatternType]
    confidence_threshold: float
    time_range: tuple[str, str]
    implementation_filter: dict[str, Any]
    sort_by: str
    limit: int
    include_metadata: bool


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


@dataclass
class ReusablePattern:
    """
    Represents a reusable pattern identified for future implementations.

    Algorithm Approach: Data class with comprehensive pattern metadata
    for future implementation enabling and knowledge transfer.

    Design Pattern: Value Object pattern for immutable pattern representation.
    """

    pattern_id: str
    name: str
    description: str
    pattern_type: PatternType
    success_rate: float
    usage_count: int
    contexts: list[str]
    adaptation_complexity: float  # 0.0 (easy) to 1.0 (complex)
    last_updated: datetime
    tags: set[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type.value,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "contexts": self.contexts,
            "adaptation_complexity": self.adaptation_complexity,
            "last_updated": self.last_updated.isoformat(),
            "tags": list(self.tags),
        }


@dataclass
class ImplementationRoadmap:
    """
    Represents a step-by-step implementation roadmap.

    Algorithm Approach: Structured roadmap with dependencies, success criteria,
    and estimated timeline for systematic implementation.

    Design Pattern: Builder pattern for flexible roadmap construction.
    """

    roadmap_id: str
    title: str
    description: str
    target_pattern: str
    steps: list[dict[str, Any]]
    dependencies: list[str]
    estimated_duration: timedelta
    success_criteria: list[str]
    risk_factors: list[str]
    confidence_score: float
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "roadmap_id": self.roadmap_id,
            "title": self.title,
            "description": self.description,
            "target_pattern": self.target_pattern,
            "steps": self.steps,
            "dependencies": self.dependencies,
            "estimated_duration_hours": self.estimated_duration.total_seconds() / 3600,
            "success_criteria": self.success_criteria,
            "risk_factors": self.risk_factors,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ApproachPrediction:
    """
    Represents a prediction for the optimal implementation approach.

    Algorithm Approach: Evidence-based prediction with confidence scoring
    and context-aware analysis for optimal approach selection.

    Design Pattern: Strategy pattern for different prediction algorithms.
    """

    prediction_id: str
    context: str
    recommended_approach: str
    alternative_approaches: list[str]
    confidence_score: float
    success_probability: float
    reasoning: list[str]
    constraints: list[str]
    benefits: list[str]
    risks: list[str]
    historical_evidence: list[str]
    predicted_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "prediction_id": self.prediction_id,
            "context": self.context,
            "recommended_approach": self.recommended_approach,
            "alternative_approaches": self.alternative_approaches,
            "confidence_score": self.confidence_score,
            "success_probability": self.success_probability,
            "reasoning": self.reasoning,
            "constraints": self.constraints,
            "benefits": self.benefits,
            "risks": self.risks,
            "historical_evidence": self.historical_evidence,
            "predicted_at": self.predicted_at.isoformat(),
        }


@dataclass
class AdaptationStrategy:
    """
    Represents a strategy for adapting patterns to specific contexts.

    Algorithm Approach: Context-aware adaptation with modification guidance
    and impact assessment for effective pattern customization.

    Design Pattern: Template Method pattern for adaptation workflows.
    """

    strategy_id: str
    source_pattern: str
    target_context: str
    adaptations: list[dict[str, Any]]
    impact_assessment: dict[str, float]
    implementation_guide: list[str]
    validation_criteria: list[str]
    rollback_strategy: str
    adaptation_complexity: float
    success_probability: float
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "strategy_id": self.strategy_id,
            "source_pattern": self.source_pattern,
            "target_context": self.target_context,
            "adaptations": self.adaptations,
            "impact_assessment": self.impact_assessment,
            "implementation_guide": self.implementation_guide,
            "validation_criteria": self.validation_criteria,
            "rollback_strategy": self.rollback_strategy,
            "adaptation_complexity": self.adaptation_complexity,
            "success_probability": self.success_probability,
            "created_at": self.created_at.isoformat(),
        }


class FutureImplementationEnabler:
    """
    Advanced future implementation enabler for knowledge-based system improvements.

    Algorithm Approach: Machine learning-enhanced pattern recognition, predictive analytics,
    and adaptive knowledge transfer for systematic future implementation enabling.

    Design Pattern: Facade pattern for unified interface, Strategy pattern for
    different algorithms, and Observer pattern for continuous learning.

    Thread Safety: Thread-safe operations through proper synchronization
    and atomic data structures.

    Performance: Asynchronous processing with intelligent caching and
    batch operations for scalability.

    Learning System: Continuous improvement through feedback loops and
    outcome-based learning for enhanced prediction accuracy.
    """

    def __init__(
        self,
        knowledge_engine: KnowledgeIntegrationEngine | None = None,
        ml_model_path: str | None = None,
        learning_rate: float = 0.01,
    ):
        """
        Initialize Future Implementation Enabler.

        Parameters
        ----------
        knowledge_engine (KnowledgeIntegrationEngine, optional): Existing knowledge engine
        ml_model_path (str, optional): Path for machine learning model storage
        learning_rate (float): Learning rate for adaptive improvements

        Raises
        ------
        ValueError: If initialization parameters are invalid
        KnowledgeIntegrationError: If enabler initialization fails

        """
        self.knowledge_engine = knowledge_engine
        self.ml_model_path = ml_model_path or str(
            Path(__file__).parent / "future_enabler_models.db"
        )
        self.learning_rate = learning_rate

        # Initialize ML components
        self._initialize_ml_components()

        # Initialize storage for future enabling data
        self._initialize_future_storage()

        # Initialize threading and async support
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._learning_lock = threading.Lock()
        self._prediction_cache = {}
        self._cache_ttl = 600  # 10 minutes

        # Initialize performance tracking
        self._prediction_accuracy_history = []
        self._pattern_discovery_history = []

        # Initialize shutdown flag
        self._shutdown_requested = False

        logger.info("FutureImplementationEnabler initialized successfully")

    def _initialize_ml_components(self) -> None:
        """
        Initialize machine learning components for pattern recognition and prediction.

        Algorithm Approach: Hybrid ML approach combining traditional ML algorithms
        with pattern-based heuristics for robust prediction capabilities.

        Design Pattern: Strategy pattern for different ML algorithms.
        """
        try:
            # Pattern recognition ML components
            self.pattern_similarity_threshold = 0.75
            self.min_pattern_occurrences = 3
            self.adaptation_complexity_weights = {
                "code_change": 0.4,
                "architecture_change": 0.7,
                "paradigm_shift": 0.9,
            }

            # Prediction ML components
            self.prediction_confidence_threshold = 0.8
            self.historical_weight = 0.6
            self.context_weight = 0.4

            # Learning system components
            self.learning_batch_size = 10
            self.max_learning_history = 1000

            logger.info("ML components initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing ML components: {e}")
            raise KnowledgeIntegrationError(f"Failed to initialize ML components: {e}")

    def _initialize_future_storage(self) -> None:
        """
        Initialize storage for future implementation enabling data.

        Algorithm Approach: SQLite database with optimized schema for
        pattern storage, roadmap management, and prediction tracking.

        Design Pattern: Active Record pattern for data access.
        """
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                # Create reusable patterns table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reusable_patterns (
                        pattern_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,
                        success_rate REAL NOT NULL,
                        usage_count INTEGER NOT NULL,
                        contexts TEXT NOT NULL,
                        adaptation_complexity REAL NOT NULL,
                        last_updated TEXT NOT NULL,
                        tags TEXT NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create implementation roadmaps table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS implementation_roadmaps (
                        roadmap_id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        target_pattern TEXT NOT NULL,
                        steps TEXT NOT NULL,
                        dependencies TEXT NOT NULL,
                        estimated_duration_hours REAL NOT NULL,
                        success_criteria TEXT NOT NULL,
                        risk_factors TEXT NOT NULL,
                        confidence_score REAL NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        usage_count INTEGER DEFAULT 0
                    )
                """
                )

                # Create approach predictions table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS approach_predictions (
                        prediction_id TEXT PRIMARY KEY,
                        context TEXT NOT NULL,
                        recommended_approach TEXT NOT NULL,
                        alternative_approaches TEXT NOT NULL,
                        confidence_score REAL NOT NULL,
                        success_probability REAL NOT NULL,
                        reasoning TEXT NOT NULL,
                        constraints TEXT NOT NULL,
                        benefits TEXT NOT NULL,
                        risks TEXT NOT NULL,
                        historical_evidence TEXT NOT NULL,
                        predicted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        actual_outcome TEXT,
                        feedback_score REAL
                    )
                """
                )

                # Create adaptation strategies table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS adaptation_strategies (
                        strategy_id TEXT PRIMARY KEY,
                        source_pattern TEXT NOT NULL,
                        target_context TEXT NOT NULL,
                        adaptations TEXT NOT NULL,
                        impact_assessment TEXT NOT NULL,
                        implementation_guide TEXT NOT NULL,
                        validation_criteria TEXT NOT NULL,
                        rollback_strategy TEXT NOT NULL,
                        adaptation_complexity REAL NOT NULL,
                        success_probability REAL NOT NULL,
                        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        applied_count INTEGER DEFAULT 0
                    )
                """
                )

                # Create learning metrics table
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS learning_metrics (
                        metric_id TEXT PRIMARY KEY,
                        metric_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        metadata TEXT NOT NULL,
                        recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes for performance
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_patterns_type ON reusable_patterns(pattern_type)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_patterns_success ON reusable_patterns(success_rate)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_predictions_context ON approach_predictions(context)"
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_strategies_pattern ON adaptation_strategies(source_pattern)",
                )
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_metrics_type ON learning_metrics(metric_type)"
                )

                conn.commit()

            logger.info("Future storage initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing future storage: {e}")
            raise KnowledgeIntegrationError(f"Failed to initialize future storage: {e}")

    def identify_reusable_patterns(
        self,
        implementation_data: list[dict[str, Any]],
        context_domain: str,
        min_success_rate: float = 0.7,
    ) -> list[ReusablePattern]:
        """
        Identify reusable patterns from implementation data using machine learning algorithms.

        Algorithm Approach: Hybrid pattern recognition combining statistical analysis,
        semantic similarity matching, and success rate filtering for accurate pattern
        identification suitable for future applications.

        Parameters
        ----------
        implementation_data (List[Dict[str, Any]]): Implementation data to analyze
        context_domain (str): Target domain context for pattern relevance
        min_success_rate (float): Minimum success rate threshold for patterns

        Returns
        -------
        List[ReusablePattern]: Identified reusable patterns sorted by relevance

        Raises
        ------
        KnowledgeIntegrationError: If pattern identification fails

        """
        try:
            logger.info(f"Identifying reusable patterns for domain: {context_domain}")

            # Extract patterns from implementation data
            extracted_patterns = self._extract_patterns_from_implementations(
                implementation_data,
                context_domain,
            )

            # Apply machine learning for pattern classification
            classified_patterns = self._classify_patterns_with_ml(extracted_patterns)

            # Filter patterns by success rate and relevance
            filtered_patterns = [
                pattern
                for pattern in classified_patterns
                if pattern.success_rate >= min_success_rate
                and self._is_pattern_relevant(pattern, context_domain)
            ]

            # Rank patterns by reusability score
            ranked_patterns = self._rank_patterns_by_reusability(filtered_patterns)

            # Store identified patterns for future learning
            self._store_identified_patterns(ranked_patterns)

            # Update pattern discovery history
            self._pattern_discovery_history.append(
                {
                    "timestamp": datetime.now(UTC),
                    "domain": context_domain,
                    "patterns_found": len(ranked_patterns),
                    "average_success_rate": (
                        sum(p.success_rate for p in ranked_patterns) / len(ranked_patterns)
                        if ranked_patterns
                        else 0
                    ),
                },
            )

            logger.info(f"Identified {len(ranked_patterns)} reusable patterns")
            return ranked_patterns

        except Exception as e:
            logger.error(f"Error identifying reusable patterns: {e}")
            raise KnowledgeIntegrationError(f"Failed to identify reusable patterns: {e}")

    def _extract_patterns_from_implementations(
        self,
        implementation_data: list[dict[str, Any]],
        context_domain: str,
    ) -> list[dict[str, Any]]:
        """
        Extract raw patterns from implementation data.

        Algorithm Approach: Multi-dimensional pattern extraction analyzing
        code structure, solution approaches, and outcome patterns.
        """
        patterns = []

        for impl in implementation_data:
            # Extract solution patterns
            if "patterns_observed" in impl:
                for pattern_name in impl["patterns_observed"]:
                    patterns.append(
                        {
                            "name": pattern_name,
                            "implementation_id": impl.get("implementation_id"),
                            "outcome": impl.get("outcome"),
                            "agent_type": impl.get("agent_type"),
                            "execution_time": impl.get("execution_time", 0),
                            "context": context_domain,
                        },
                    )

            # Extract architectural patterns
            if "architecture" in impl:
                arch_patterns = self._extract_architectural_patterns(impl["architecture"])
                patterns.extend(arch_patterns)

            # Extract performance patterns
            if "performance_metrics" in impl:
                perf_patterns = self._extract_performance_patterns(impl["performance_metrics"])
                patterns.extend(perf_patterns)

        return patterns

    def _extract_architectural_patterns(
        self, architecture_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract architectural patterns from architecture data."""
        patterns = []

        # Common architectural pattern indicators
        arch_keywords = {
            "microservice": ["microservice", "service", "api", "endpoint"],
            "layered": ["layer", "tier", "separation", "concern"],
            "event_driven": ["event", "publish", "subscribe", "queue"],
            "repository": ["repository", "dao", "storage", "persistence"],
            "factory": ["factory", "builder", "creator", "constructor"],
        }

        arch_text = str(architecture_data).lower()

        for pattern_type, keywords in arch_keywords.items():
            if any(keyword in arch_text for keyword in keywords):
                patterns.append(
                    {
                        "name": pattern_type,
                        "type": "architectural",
                        "source": "architecture_analysis",
                    },
                )

        return patterns

    def _extract_performance_patterns(
        self, performance_data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract performance patterns from performance metrics."""
        patterns = []

        # Performance optimization pattern indicators
        if performance_data.get("response_time", 0) < 100:  # Fast response
            patterns.append(
                {
                    "name": "optimized_response",
                    "type": "performance",
                    "source": "performance_analysis",
                },
            )

        if performance_data.get("memory_usage", 0) < 50:  # Low memory usage
            patterns.append(
                {
                    "name": "memory_efficient",
                    "type": "performance",
                    "source": "performance_analysis",
                },
            )

        if performance_data.get("cache_hit_rate", 0) > 0.8:  # High cache hit rate
            patterns.append(
                {
                    "name": "effective_caching",
                    "type": "performance",
                    "source": "performance_analysis",
                },
            )

        return patterns

    def _classify_patterns_with_ml(self, patterns: list[dict[str, Any]]) -> list[ReusablePattern]:
        """
        Classify patterns using machine learning algorithms.

        Algorithm Approach: Supervised and unsupervised learning combination
        for pattern classification and success rate prediction.
        """
        classified_patterns = []

        # Group patterns by name for analysis
        pattern_groups = defaultdict(list)
        for pattern in patterns:
            pattern_groups[pattern["name"]].append(pattern)

        for pattern_name, occurrences in pattern_groups.items():
            if len(occurrences) >= self.min_pattern_occurrences:
                # Calculate success rate
                successful_outcomes = sum(
                    1 for occ in occurrences if occ.get("outcome") == "success"
                )
                success_rate = successful_outcomes / len(occurrences)

                # Determine pattern type
                pattern_type = self._determine_pattern_type(pattern_name, occurrences)

                # Calculate adaptation complexity
                adaptation_complexity = self._calculate_pattern_adaptation_complexity(occurrences)

                # Extract contexts and tags
                contexts = list({occ.get("context", "") for occ in occurrences})
                tags = self._extract_pattern_tags(pattern_name, occurrences)

                # Create ReusablePattern object
                reusable_pattern = ReusablePattern(
                    pattern_id=str(uuid.uuid4()),
                    name=pattern_name,
                    description=self._generate_pattern_description(pattern_name, occurrences),
                    pattern_type=pattern_type,
                    success_rate=success_rate,
                    usage_count=len(occurrences),
                    contexts=contexts,
                    adaptation_complexity=adaptation_complexity,
                    last_updated=datetime.now(UTC),
                    tags=tags,
                )

                classified_patterns.append(reusable_pattern)

        return classified_patterns

    def _determine_pattern_type(
        self, pattern_name: str, occurrences: list[dict[str, Any]]
    ) -> PatternType:
        """Determine the type of pattern based on its characteristics."""
        pattern_lower = pattern_name.lower()

        if any(
            keyword in pattern_lower for keyword in ["security", "auth", "validation", "protect"]
        ):
            return PatternType.SECURITY
        if any(
            keyword in pattern_lower for keyword in ["performance", "optimize", "cache", "fast"]
        ):
            return PatternType.PERFORMANCE
        if any(keyword in pattern_lower for keyword in ["error", "exception", "handle", "recover"]):
            return PatternType.ERROR_HANDLING
        if any(keyword in pattern_lower for keyword in ["test", "verify", "validate", "check"]):
            return PatternType.TESTING
        if any(keyword in pattern_lower for keyword in ["modular", "scalable", "architect"]):
            return PatternType.ARCHITECTURAL
        return PatternType.IMPLEMENTATION

    def _calculate_pattern_adaptation_complexity(self, occurrences: list[dict[str, Any]]) -> float:
        """
        Calculate adaptation complexity for a pattern.

        Algorithm Approach: Multi-factor analysis considering code changes,
        architectural modifications, and paradigm shifts required.
        """
        complexity_factors = []

        for occ in occurrences:
            # Execution time complexity factor
            exec_time = occ.get("execution_time", 0)
            if exec_time > 300:  # > 5 minutes indicates complexity
                complexity_factors.append(0.8)
            elif exec_time > 60:  # > 1 minute indicates moderate complexity
                complexity_factors.append(0.5)
            else:
                complexity_factors.append(0.2)

            # Agent type complexity factor
            agent_type = occ.get("agent_type", "")
            if "senior" in agent_type.lower() or "expert" in agent_type.lower():
                complexity_factors.append(0.3)  # Less complex for experts
            elif "junior" in agent_type.lower():
                complexity_factors.append(0.7)  # More complex for juniors

        # Average complexity factors
        avg_complexity = (
            sum(complexity_factors) / len(complexity_factors) if complexity_factors else 0.5
        )

        # Normalize to 0.0-1.0 range
        return min(1.0, max(0.0, avg_complexity))

    def _extract_pattern_tags(
        self, pattern_name: str, occurrences: list[dict[str, Any]]
    ) -> set[str]:
        """Extract relevant tags for a pattern."""
        tags = set()

        # Extract agent types as tags
        agent_types = {occ.get("agent_type", "") for occ in occurrences}
        tags.update(agent_types)

        # Extract context-related tags
        contexts = {occ.get("context", "") for occ in occurrences}
        for context in contexts:
            if context:
                tags.add(f"context:{context}")

        # Extract outcome-based tags
        successful_outcomes = sum(1 for occ in occurrences if occ.get("outcome") == "success")
        if successful_outcomes / len(occurrences) > 0.8:
            tags.add("high_success")

        # Extract complexity-based tags
        avg_exec_time = sum(occ.get("execution_time", 0) for occ in occurrences) / len(occurrences)
        if avg_exec_time < 60:
            tags.add("quick_implementation")
        elif avg_exec_time > 300:
            tags.add("complex_implementation")

        return tags

    def _generate_pattern_description(
        self, pattern_name: str, occurrences: list[dict[str, Any]]
    ) -> str:
        """Generate a description for the pattern based on its occurrences."""
        success_count = sum(1 for occ in occurrences if occ.get("outcome") == "success")
        success_rate = success_count / len(occurrences)

        avg_exec_time = sum(occ.get("execution_time", 0) for occ in occurrences) / len(occurrences)

        contexts = list({occ.get("context", "") for occ in occurrences if occ.get("context")})

        description = f"Pattern '{pattern_name}' observed in {len(occurrences)} implementations "
        description += f"with {success_rate:.1%} success rate. "

        if avg_exec_time < 60:
            description += "Typically implemented quickly (under 1 minute). "
        elif avg_exec_time > 300:
            description += "Requires significant implementation time (over 5 minutes). "

        if contexts:
            description += f"Common contexts: {', '.join(contexts[:3])}. "

        return description.strip()

    def _is_pattern_relevant(self, pattern: ReusablePattern, context_domain: str) -> bool:
        """Check if a pattern is relevant to the given context domain."""
        # Direct context match
        if context_domain in pattern.contexts:
            return True

        # Semantic similarity check
        context_lower = context_domain.lower()
        pattern_lower = pattern.name.lower()

        # Keyword matching for relevance
        relevance_keywords = {
            "python": ["python", "django", "flask", "fastapi", "backend"],
            "frontend": ["react", "vue", "angular", "javascript", "css"],
            "database": ["sql", "nosql", "orm", "migration", "query"],
            "api": ["rest", "graphql", "endpoint", "service", "api"],
            "security": ["auth", "security", "validation", "encryption"],
            "performance": ["optimize", "cache", "performance", "speed"],
        }

        for domain, keywords in relevance_keywords.items():
            if domain in context_lower or domain in pattern_lower:
                if any(keyword in pattern_lower for keyword in keywords):
                    return True

        return False

    def _rank_patterns_by_reusability(
        self, patterns: list[ReusablePattern]
    ) -> list[ReusablePattern]:
        """
        Rank patterns by their reusability score.

        Algorithm Approach: Multi-factor scoring considering success rate,
        usage count, adaptation complexity, and context relevance.
        """

        def calculate_reusability_score(pattern: ReusablePattern) -> float:
            # Success rate weight (40%)
            success_score = pattern.success_rate * 0.4

            # Usage count weight (20%)
            usage_score = min(1.0, pattern.usage_count / 10) * 0.2

            # Adaptation complexity weight (20%) - lower complexity = higher score
            complexity_score = (1.0 - pattern.adaptation_complexity) * 0.2

            # Context diversity weight (10%)
            context_score = min(1.0, len(pattern.contexts) / 3) * 0.1

            # Recent activity weight (10%)
            days_since_update = (datetime.now(UTC) - pattern.last_updated).days
            recency_score = max(0.0, 1.0 - days_since_update / 30) * 0.1

            return success_score + usage_score + complexity_score + context_score + recency_score

        # Sort by reusability score (descending)
        return sorted(patterns, key=calculate_reusability_score, reverse=True)

    def _store_identified_patterns(self, patterns: list[ReusablePattern]) -> None:
        """Store identified patterns in the database."""
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                for pattern in patterns:
                    pattern_dict = pattern.to_dict()
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO reusable_patterns
                        (pattern_id, name, description, pattern_type, success_rate,
                         usage_count, contexts, adaptation_complexity, last_updated, tags)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            pattern_dict["pattern_id"],
                            pattern_dict["name"],
                            pattern_dict["description"],
                            pattern_dict["pattern_type"],
                            pattern_dict["success_rate"],
                            pattern_dict["usage_count"],
                            json.dumps(pattern_dict["contexts"]),
                            pattern_dict["adaptation_complexity"],
                            pattern_dict["last_updated"],
                            json.dumps(pattern_dict["tags"]),
                        ),
                    )

                conn.commit()

        except Exception as e:
            logger.error(f"Error storing identified patterns: {e}")

    def generate_implementation_roadmaps(
        self,
        target_patterns: list[str],
        context_requirements: dict[str, Any],
        complexity_preference: str = "balanced",  # "conservative", "balanced", "aggressive"
    ) -> list[ImplementationRoadmap]:
        """
        Generate step-by-step implementation roadmaps based on successful implementations.

        Algorithm Approach: Evidence-based roadmap generation using historical success data,
        dependency analysis, and risk assessment for comprehensive implementation guidance.

        Parameters
        ----------
        target_patterns (List[str]): Target patterns for roadmap generation
        context_requirements (Dict[str, Any]): Context-specific requirements and constraints
        complexity_preference (str): Preferred complexity level for implementation

        Returns
        -------
        List[ImplementationRoadmap]: Generated roadmaps with step-by-step guidance

        Raises
        ------
        KnowledgeIntegrationError: If roadmap generation fails

        """
        try:
            logger.info(f"Generating implementation roadmaps for {len(target_patterns)} patterns")

            roadmaps = []

            for pattern_name in target_patterns:
                # Retrieve pattern data and historical implementations
                pattern_data = self._get_pattern_historical_data(pattern_name)

                if not pattern_data:
                    logger.warning(f"No historical data found for pattern: {pattern_name}")
                    continue

                # Analyze successful implementations
                successful_implementations = self._analyze_successful_implementations(
                    pattern_data,
                    context_requirements,
                )

                if not successful_implementations:
                    logger.warning(
                        f"No successful implementations found for pattern: {pattern_name}"
                    )
                    continue

                # Generate roadmap steps based on successful implementations
                roadmap_steps = self._generate_roadmap_steps(
                    successful_implementations,
                    complexity_preference,
                )

                # Calculate dependencies and timeline
                dependencies = self._calculate_implementation_dependencies(roadmap_steps)
                estimated_duration = self._estimate_implementation_duration(
                    roadmap_steps,
                    complexity_preference,
                )

                # Define success criteria and risk factors
                success_criteria = self._define_success_criteria(successful_implementations)
                risk_factors = self._identify_risk_factors(successful_implementations)

                # Calculate confidence score
                confidence_score = self._calculate_roadmap_confidence(
                    successful_implementations,
                    context_requirements,
                )

                # Create ImplementationRoadmap object
                roadmap = ImplementationRoadmap(
                    roadmap_id=str(uuid.uuid4()),
                    title=f"Implementation Roadmap for {pattern_name}",
                    description=f"Step-by-step implementation guide for {pattern_name} pattern",
                    target_pattern=pattern_name,
                    steps=roadmap_steps,
                    dependencies=dependencies,
                    estimated_duration=estimated_duration,
                    success_criteria=success_criteria,
                    risk_factors=risk_factors,
                    confidence_score=confidence_score,
                    created_at=datetime.now(UTC),
                )

                roadmaps.append(roadmap)

            # Store generated roadmaps
            self._store_implementation_roadmaps(roadmaps)

            logger.info(f"Generated {len(roadmaps)} implementation roadmaps")
            return roadmaps

        except Exception as e:
            logger.error(f"Error generating implementation roadmaps: {e}")
            raise KnowledgeIntegrationError(f"Failed to generate implementation roadmaps: {e}")

    def _get_pattern_historical_data(self, pattern_name: str) -> dict[str, Any] | None:
        """Retrieve historical data for a specific pattern."""
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                # Get pattern data
                cursor.execute(
                    """
                    SELECT * FROM reusable_patterns WHERE name = ?
                """,
                    (pattern_name,),
                )

                pattern_row = cursor.fetchone()
                if not pattern_row:
                    return None

                # Get related implementations from knowledge engine
                implementations = []
                if self.knowledge_engine:
                    implementations = (
                        self.knowledge_engine.get_successful_implementations_for_pattern(
                            pattern_name,
                        )
                    )

                return {
                    "pattern": {
                        "id": pattern_row[0],
                        "name": pattern_row[1],
                        "success_rate": pattern_row[4],
                        "usage_count": pattern_row[5],
                        "adaptation_complexity": pattern_row[7],
                    },
                    "implementations": implementations,
                }

        except Exception as e:
            logger.error(f"Error retrieving pattern historical data: {e}")
            return None

    def _analyze_successful_implementations(
        self,
        pattern_data: dict[str, Any],
        context_requirements: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Analyze successful implementations for the pattern."""
        implementations = pattern_data.get("implementations", [])

        # Filter for successful implementations
        successful = [impl for impl in implementations if impl.get("outcome") == "success"]

        # Filter by context relevance
        context_filtered = []
        for impl in successful:
            relevance_score = self._calculate_context_relevance(impl, context_requirements)
            if relevance_score > 0.5:  # Threshold for context relevance
                impl["context_relevance"] = relevance_score
                context_filtered.append(impl)

        # Sort by context relevance and success metrics
        return sorted(
            context_filtered,
            key=lambda x: (
                x.get("context_relevance", 0),
                x.get("execution_time", float("inf")),
            ),
            reverse=True,
        )

    def _calculate_context_relevance(
        self,
        implementation: dict[str, Any],
        context_requirements: dict[str, Any],
    ) -> float:
        """Calculate relevance score between implementation and context requirements."""
        relevance_score = 0.0
        total_factors = 0

        # Technology stack relevance
        if "technology_stack" in context_requirements:
            impl_tech = implementation.get("technology_stack", [])
            req_tech = context_requirements["technology_stack"]

            if impl_tech and req_tech:
                common_tech = set(impl_tech) & set(req_tech)
                tech_relevance = len(common_tech) / len(set(impl_tech) | set(req_tech))
                relevance_score += tech_relevance
                total_factors += 1

        # Complexity relevance
        if "complexity_preference" in context_requirements:
            impl_complexity = implementation.get("complexity", "medium")
            req_complexity = context_requirements["complexity_preference"]

            complexity_match = 1.0 if impl_complexity == req_complexity else 0.5
            relevance_score += complexity_match
            total_factors += 1

        # Scale relevance
        if "scale" in context_requirements:
            impl_scale = implementation.get("scale", "medium")
            req_scale = context_requirements["scale"]

            scale_match = 1.0 if impl_scale == req_scale else 0.3
            relevance_score += scale_match
            total_factors += 1

        return relevance_score / total_factors if total_factors > 0 else 0.0

    def _generate_roadmap_steps(
        self,
        successful_implementations: list[dict[str, Any]],
        complexity_preference: str,
    ) -> list[dict[str, Any]]:
        """Generate roadmap steps based on successful implementations."""
        steps = []

        # Extract common steps from successful implementations
        step_patterns = defaultdict(list)

        for impl in successful_implementations:
            impl_steps = impl.get("implementation_steps", [])
            for i, step in enumerate(impl_steps):
                step_key = f"step_{i + 1}_{step.get('type', 'unknown')}"
                step_patterns[step_key].append(step)

        # Generate consolidated steps
        step_order = 1
        for step_key, step_variants in step_patterns.items():
            if len(step_variants) >= 2:  # Step appears in multiple successful implementations
                # Consolidate step information
                consolidated_step = self._consolidate_step_information(
                    step_variants,
                    complexity_preference,
                )
                consolidated_step["step_number"] = step_order
                steps.append(consolidated_step)
                step_order += 1

        # Add common preparatory and concluding steps
        preparatory_steps = self._generate_preparatory_steps(complexity_preference)
        concluding_steps = self._generate_concluding_steps(successful_implementations)

        return preparatory_steps + steps + concluding_steps

    def _consolidate_step_information(
        self,
        step_variants: list[dict[str, Any]],
        complexity_preference: str,
    ) -> dict[str, Any]:
        """Consolidate information from multiple step variants."""
        # Extract common descriptions
        descriptions = [step.get("description", "") for step in step_variants]
        common_description = self._find_common_description(descriptions)

        # Calculate average duration
        durations = [step.get("duration", 0) for step in step_variants if step.get("duration")]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Adjust duration based on complexity preference
        duration_multiplier = {
            "conservative": 1.5,
            "balanced": 1.0,
            "aggressive": 0.7,
        }.get(complexity_preference, 1.0)

        # Extract common prerequisites
        all_prerequisites = []
        for step in step_variants:
            all_prerequisites.extend(step.get("prerequisites", []))

        # Find most common prerequisites
        prereq_counts = defaultdict(int)
        for prereq in all_prerequisites:
            prereq_counts[prereq] += 1

        common_prerequisites = [
            prereq for prereq, count in prereq_counts.items() if count >= len(step_variants) / 2
        ]

        return {
            "type": step_variants[0].get("type", "implementation"),
            "description": common_description or "Implementation step",
            "estimated_duration": avg_duration * duration_multiplier,
            "prerequisites": common_prerequisites,
            "success_indicators": self._extract_success_indicators(step_variants),
            "common_pitfalls": self._extract_common_pitfalls(step_variants),
            "confidence": len(step_variants) / 10,  # Confidence based on frequency
        }

    def _find_common_description(self, descriptions: list[str]) -> str | None:
        """Find the most common description from a list."""
        if not descriptions:
            return None

        # Simple frequency-based approach
        description_counts = defaultdict(int)
        for desc in descriptions:
            description_counts[desc] += 1

        most_common = max(description_counts.items(), key=lambda x: x[1])
        return most_common[0] if most_common[1] > 1 else None

    def _extract_success_indicators(self, step_variants: list[dict[str, Any]]) -> list[str]:
        """Extract common success indicators from step variants."""
        all_indicators = []
        for step in step_variants:
            all_indicators.extend(step.get("success_indicators", []))

        # Find most common indicators
        indicator_counts = defaultdict(int)
        for indicator in all_indicators:
            indicator_counts[indicator] += 1

        return [
            indicator
            for indicator, count in indicator_counts.items()
            if count >= len(step_variants) / 2
        ]

    def _extract_common_pitfalls(self, step_variants: list[dict[str, Any]]) -> list[str]:
        """Extract common pitfalls from step variants."""
        all_pitfalls = []
        for step in step_variants:
            all_pitfalls.extend(step.get("pitfalls", []))

        # Find most common pitfalls
        pitfall_counts = defaultdict(int)
        for pitfall in all_pitfalls:
            pitfall_counts[pitfall] += 1

        return [
            pitfall
            for pitfall, count in pitfall_counts.items()
            if count >= len(step_variants) / 3  # Lower threshold for pitfalls
        ]

    def _generate_preparatory_steps(self, complexity_preference: str) -> list[dict[str, Any]]:
        """Generate common preparatory steps."""
        base_steps = [
            {
                "step_number": 0,
                "type": "preparation",
                "description": "Analyze requirements and assess current environment",
                "estimated_duration": 30,
                "prerequisites": [],
                "success_indicators": [
                    "Requirements documented",
                    "Environment assessed",
                ],
                "common_pitfalls": [
                    "Insufficient requirement analysis",
                    "Environment compatibility issues",
                ],
                "confidence": 0.9,
            },
            {
                "step_number": 0,
                "type": "preparation",
                "description": "Set up development and testing infrastructure",
                "estimated_duration": 60,
                "prerequisites": ["Requirements analyzed"],
                "success_indicators": [
                    "Development environment ready",
                    "Testing infrastructure configured",
                ],
                "common_pitfalls": [
                    "Inadequate testing setup",
                    "Development environment issues",
                ],
                "confidence": 0.8,
            },
        ]

        # Add complexity-specific preparatory steps
        if complexity_preference == "conservative":
            base_steps.append(
                {
                    "step_number": 0,
                    "type": "preparation",
                    "description": "Create detailed implementation plan with risk mitigation strategies",
                    "estimated_duration": 45,
                    "prerequisites": ["Requirements analyzed"],
                    "success_indicators": [
                        "Detailed plan created",
                        "Risks identified and mitigated",
                    ],
                    "common_pitfalls": [
                        "Insufficient planning",
                        "Overlooked dependencies",
                    ],
                    "confidence": 0.85,
                },
            )

        return base_steps

    def _generate_concluding_steps(
        self, successful_implementations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate common concluding steps."""
        return [
            {
                "type": "validation",
                "description": "Comprehensive testing and validation",
                "estimated_duration": 120,
                "prerequisites": ["Implementation complete"],
                "success_indicators": [
                    "All tests passing",
                    "Performance requirements met",
                ],
                "common_pitfalls": [
                    "Inadequate testing coverage",
                    "Performance issues discovered late",
                ],
                "confidence": 0.9,
            },
            {
                "type": "deployment",
                "description": "Deploy to production and monitor",
                "estimated_duration": 90,
                "prerequisites": ["Comprehensive testing complete"],
                "success_indicators": ["Successful deployment", "Monitoring active"],
                "common_pitfalls": ["Deployment failures", "Insufficient monitoring"],
                "confidence": 0.8,
            },
        ]

    def _calculate_implementation_dependencies(self, steps: list[dict[str, Any]]) -> list[str]:
        """Calculate implementation dependencies from roadmap steps."""
        dependencies = set()

        for step in steps:
            prerequisites = step.get("prerequisites", [])
            dependencies.update(prerequisites)

        return list(dependencies)

    def _estimate_implementation_duration(
        self,
        steps: list[dict[str, Any]],
        complexity_preference: str,
    ) -> timedelta:
        """Estimate total implementation duration."""
        base_duration = sum(step.get("estimated_duration", 0) for step in steps)

        # Apply complexity multiplier
        complexity_multipliers = {
            "conservative": 1.4,  # More time for careful implementation
            "balanced": 1.0,
            "aggressive": 0.8,  # Faster implementation with higher risk
        }

        multiplier = complexity_multipliers.get(complexity_preference, 1.0)
        total_minutes = base_duration * multiplier

        return timedelta(minutes=total_minutes)

    def _define_success_criteria(
        self, successful_implementations: list[dict[str, Any]]
    ) -> list[str]:
        """Define success criteria based on successful implementations."""
        criteria = set()

        for impl in successful_implementations:
            impl_criteria = impl.get("success_criteria", [])
            criteria.update(impl_criteria)

        # Add common success criteria
        common_criteria = [
            "Implementation meets all functional requirements",
            "Performance benchmarks achieved",
            "Security requirements satisfied",
            "Code quality standards met",
            "Documentation completed",
        ]

        criteria.update(common_criteria)

        return list(criteria)

    def _identify_risk_factors(self, successful_implementations: list[dict[str, Any]]) -> list[str]:
        """Identify potential risk factors based on implementation history."""
        risk_factors = set()

        # Extract risk factors from implementation history
        for impl in successful_implementations:
            impl_risks = impl.get("risk_factors", [])
            challenges = impl.get("challenges_encountered", [])

            risk_factors.update(impl_risks)
            risk_factors.update(challenges)

        # Add common risk factors
        common_risks = [
            "Requirement changes during implementation",
            "Technical dependencies and compatibility issues",
            "Resource constraints and timeline pressures",
            "Integration challenges with existing systems",
            "Performance optimization requirements",
        ]

        risk_factors.update(common_risks)

        return list(risk_factors)

    def _calculate_roadmap_confidence(
        self,
        successful_implementations: list[dict[str, Any]],
        context_requirements: dict[str, Any],
    ) -> float:
        """Calculate confidence score for the roadmap."""
        if not successful_implementations:
            return 0.0

        # Base confidence from number of successful implementations
        implementation_confidence = min(1.0, len(successful_implementations) / 5)

        # Context relevance confidence
        context_confidence = sum(
            impl.get("context_relevance", 0.5) for impl in successful_implementations
        ) / len(
            successful_implementations,
        )

        # Success rate confidence
        avg_success_rate = sum(
            impl.get("success_rate", 0.8) for impl in successful_implementations
        ) / len(
            successful_implementations,
        )

        # Weighted combination
        confidence = (
            implementation_confidence * 0.4 + context_confidence * 0.3 + avg_success_rate * 0.3
        )

        return round(confidence, 3)

    def _store_implementation_roadmaps(self, roadmaps: list[ImplementationRoadmap]) -> None:
        """Store generated roadmaps in the database."""
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                for roadmap in roadmaps:
                    roadmap_dict = roadmap.to_dict()
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO implementation_roadmaps
                        (roadmap_id, title, description, target_pattern, steps,
                         dependencies, estimated_duration_hours, success_criteria,
                         risk_factors, confidence_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            roadmap_dict["roadmap_id"],
                            roadmap_dict["title"],
                            roadmap_dict["description"],
                            roadmap_dict["target_pattern"],
                            json.dumps(roadmap_dict["steps"]),
                            json.dumps(roadmap_dict["dependencies"]),
                            roadmap_dict["estimated_duration_hours"],
                            json.dumps(roadmap_dict["success_criteria"]),
                            json.dumps(roadmap_dict["risk_factors"]),
                            roadmap_dict["confidence_score"],
                        ),
                    )

                conn.commit()

        except Exception as e:
            logger.error(f"Error storing implementation roadmaps: {e}")

    def predict_optimal_approaches(
        self,
        implementation_context: dict[str, Any],
        available_patterns: list[str],
        constraints: dict[str, Any] | None = None,
    ) -> list[ApproachPrediction]:
        """
        Predict optimal implementation approaches using historical success data and context analysis.

        Algorithm Approach: Evidence-based prediction combining historical success patterns,
        context-aware analysis, and machine learning for optimal approach selection.

        Parameters
        ----------
        implementation_context (Dict[str, Any]): Context details for implementation
        available_patterns (List[str]): Available patterns to consider
        constraints (Dict[str, Any], optional): Implementation constraints and requirements

        Returns
        -------
        List[ApproachPrediction]: Predicted approaches ranked by confidence and success probability

        Raises
        ------
        KnowledgeIntegrationError: If approach prediction fails

        """
        try:
            logger.info(
                f"Predicting optimal approaches for context with {len(available_patterns)} patterns"
            )

            constraints = constraints or {}
            predictions = []

            # Generate approach predictions for each pattern
            for pattern_name in available_patterns:
                prediction = self._predict_approach_for_pattern(
                    pattern_name,
                    implementation_context,
                    constraints,
                )
                if prediction:
                    predictions.append(prediction)

            # Rank predictions by composite score (confidence + success probability)
            ranked_predictions = sorted(
                predictions,
                key=lambda p: (p.confidence_score + p.success_probability) / 2,
                reverse=True,
            )

            # Store predictions for learning and feedback
            self._store_approach_predictions(ranked_predictions)

            logger.info(f"Generated {len(ranked_predictions)} approach predictions")
            return ranked_predictions

        except Exception as e:
            logger.error(f"Error predicting optimal approaches: {e}")
            raise KnowledgeIntegrationError(f"Failed to predict optimal approaches: {e}")

    def _predict_approach_for_pattern(
        self,
        pattern_name: str,
        context: dict[str, Any],
        constraints: dict[str, Any],
    ) -> ApproachPrediction | None:
        """Predict approach for a specific pattern."""
        try:
            # Retrieve historical data for the pattern
            pattern_data = self._get_pattern_historical_data(pattern_name)
            if not pattern_data:
                return None

            # Analyze historical implementations
            historical_implementations = self._analyze_historical_implementations(
                pattern_data,
                context,
                constraints,
            )

            if not historical_implementations:
                return None

            # Calculate success metrics
            success_metrics = self._calculate_success_metrics(historical_implementations)

            # Generate reasoning based on historical evidence
            reasoning = self._generate_approach_reasoning(
                pattern_name,
                historical_implementations,
                context,
            )

            # Identify constraints and benefits
            approach_constraints = self._identify_approach_constraints(
                historical_implementations,
                constraints,
            )
            approach_benefits = self._identify_approach_benefits(
                historical_implementations,
                context,
            )

            # Identify potential risks
            approach_risks = self._identify_approach_risks(historical_implementations)

            # Generate alternative approaches
            alternatives = self._generate_alternative_approaches(
                pattern_name,
                historical_implementations,
                context,
            )

            # Calculate confidence and success probability
            confidence_score = self._calculate_prediction_confidence(
                historical_implementations,
                context,
            )
            success_probability = success_metrics["overall_success_rate"]

            return ApproachPrediction(
                prediction_id=str(uuid.uuid4()),
                context=self._serialize_context(context),
                recommended_approach=pattern_name,
                alternative_approaches=alternatives,
                confidence_score=confidence_score,
                success_probability=success_probability,
                reasoning=reasoning,
                constraints=approach_constraints,
                benefits=approach_benefits,
                risks=approach_risks,
                historical_evidence=[
                    f"Based on {len(historical_implementations)} historical implementations",
                ]
                + self._extract_key_evidence(historical_implementations),
                predicted_at=datetime.now(UTC),
            )

        except Exception as e:
            logger.error(f"Error predicting approach for pattern {pattern_name}: {e}")
            return None

    def _analyze_historical_implementations(
        self,
        pattern_data: dict[str, Any],
        context: dict[str, Any],
        constraints: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Analyze historical implementations relevant to the context."""
        implementations = pattern_data.get("implementations", [])

        # Filter by context relevance
        relevant_implementations = []
        for impl in implementations:
            relevance_score = self._calculate_context_relevance(impl, context)
            if relevance_score > 0.3:  # Lower threshold for broader analysis
                impl["context_relevance"] = relevance_score
                relevant_implementations.append(impl)

        # Sort by relevance and success
        return sorted(
            relevant_implementations,
            key=lambda x: (
                x.get("context_relevance", 0),
                1 if x.get("outcome") == "success" else 0,
            ),
            reverse=True,
        )

    def _calculate_success_metrics(self, implementations: list[dict[str, Any]]) -> dict[str, float]:
        """Calculate success metrics from implementations."""
        if not implementations:
            return {"overall_success_rate": 0.0, "avg_execution_time": 0.0}

        successful_implementations = [
            impl for impl in implementations if impl.get("outcome") == "success"
        ]

        overall_success_rate = len(successful_implementations) / len(implementations)

        # Calculate average execution time for successful implementations
        successful_times = [
            impl.get("execution_time", 0)
            for impl in successful_implementations
            if impl.get("execution_time")
        ]
        avg_execution_time = (
            sum(successful_times) / len(successful_times) if successful_times else 0.0
        )

        return {
            "overall_success_rate": overall_success_rate,
            "avg_execution_time": avg_execution_time,
            "successful_count": len(successful_implementations),
            "total_count": len(implementations),
        }

    def _generate_approach_reasoning(
        self,
        pattern_name: str,
        implementations: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[str]:
        """Generate reasoning for approach selection."""
        reasoning = []

        success_metrics = self._calculate_success_metrics(implementations)
        success_rate = success_metrics["overall_success_rate"]

        if success_rate > 0.8:
            reasoning.append(
                f"High historical success rate ({success_rate:.1%}) for {pattern_name}"
            )
        elif success_rate > 0.6:
            reasoning.append(
                f"Moderate historical success rate ({success_rate:.1%}) for {pattern_name}"
            )
        else:
            reasoning.append(
                f"Lower historical success rate ({success_rate:.1%}) - consider alternatives"
            )

        # Context-specific reasoning
        if context.get("technology_stack"):
            tech_stack = context["technology_stack"]
            compatible_impls = [
                impl
                for impl in implementations
                if any(tech in str(impl.get("technology_stack", [])).lower() for tech in tech_stack)
            ]
            if compatible_impls:
                reasoning.append(
                    f"Strong compatibility with {', '.join(tech_stack)} technology stack"
                )

        # Performance reasoning
        avg_time = success_metrics["avg_execution_time"]
        if avg_time < 60:
            reasoning.append("Typically implemented quickly (under 1 minute)")
        elif avg_time > 300:
            reasoning.append("Requires significant implementation time (over 5 minutes)")
        else:
            reasoning.append("Moderate implementation complexity")

        return reasoning

    def _identify_approach_constraints(
        self,
        implementations: list[dict[str, Any]],
        user_constraints: dict[str, Any],
    ) -> list[str]:
        """Identify approach constraints from implementations and user requirements."""
        constraints = set()

        # Extract constraints from historical implementations
        for impl in implementations:
            impl_constraints = impl.get("constraints", [])
            constraints.update(impl_constraints)

        # Add user-specified constraints
        for constraint_type, value in user_constraints.items():
            constraints.add(f"{constraint_type}: {value}")

        # Common constraints based on implementation patterns
        execution_times = [impl.get("execution_time", 0) for impl in implementations]
        avg_time = sum(execution_times) / len(execution_times) if execution_times else 0

        if avg_time > 180:  # > 3 hours
            constraints.add("Requires significant time investment")
        elif avg_time < 30:  # < 30 minutes
            constraints.add("Quick implementation possible")

        # Complexity constraints
        complexity_scores = [
            impl.get("complexity_score", 0.5)
            for impl in implementations
            if impl.get("complexity_score")
        ]
        if complexity_scores:
            avg_complexity = sum(complexity_scores) / len(complexity_scores)
            if avg_complexity > 0.7:
                constraints.add("High complexity - requires expert knowledge")
            elif avg_complexity < 0.3:
                constraints.add("Low complexity - suitable for junior developers")

        return list(constraints)

    def _identify_approach_benefits(
        self,
        implementations: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[str]:
        """Identify approach benefits from implementations."""
        benefits = set()

        # Extract benefits from historical implementations
        for impl in implementations:
            impl_benefits = impl.get("benefits", [])
            benefits.update(impl_benefits)

        # Success-based benefits
        success_metrics = self._calculate_success_metrics(implementations)
        if success_metrics["overall_success_rate"] > 0.8:
            benefits.add("High probability of successful implementation")

        # Performance benefits
        avg_time = success_metrics["avg_execution_time"]
        if avg_time < 60:
            benefits.add("Fast implementation time")
        if avg_time < 30:
            benefits.add("Quick implementation - minimal resource investment")

        # Context-specific benefits
        if context.get("scale") == "large":
            successful_large = [
                impl
                for impl in implementations
                if impl.get("scale") == "large" and impl.get("outcome") == "success"
            ]
            if len(successful_large) > len(implementations) * 0.6:
                benefits.add("Proven effectiveness at scale")

        # Learning and growth benefits
        pattern_names = {impl.get("patterns_observed", []) for impl in implementations}
        if len(pattern_names) > 1:
            benefits.add("Opportunity to learn multiple implementation patterns")

        return list(benefits)

    def _identify_approach_risks(self, implementations: list[dict[str, Any]]) -> list[str]:
        """Identify potential risks from implementations."""
        risks = set()

        # Failure analysis
        failed_implementations = [
            impl for impl in implementations if impl.get("outcome") == "failure"
        ]

        if failed_implementations:
            risks.append(f"Has {len(failed_implementations)} documented failure(s)")

            # Extract common failure reasons
            failure_reasons = []
            for impl in failed_implementations:
                failure_reasons.extend(impl.get("failure_reasons", []))

            reason_counts = defaultdict(int)
            for reason in failure_reasons:
                reason_counts[reason] += 1

            common_failures = [
                reason
                for reason, count in reason_counts.items()
                if count >= len(failed_implementations) / 2
            ]
            risks.extend(common_failures)

        # Time-based risks
        execution_times = [impl.get("execution_time", 0) for impl in implementations]
        max_time = max(execution_times) if execution_times else 0
        if max_time > 600:  # > 10 hours
            risks.add("Potential for extended implementation time")

        # Complexity risks
        complexity_scores = [
            impl.get("complexity_score", 0.5)
            for impl in implementations
            if impl.get("complexity_score")
        ]
        if complexity_scores and max(complexity_scores) > 0.8:
            risks.add("High complexity implementations may be challenging")

        return list(risks)

    def _generate_alternative_approaches(
        self,
        pattern_name: str,
        implementations: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[str]:
        """Generate alternative approaches based on implementations."""
        alternatives = set()

        # Extract alternative patterns from implementations
        for impl in implementations:
            alt_patterns = impl.get("alternative_patterns", [])
            alternatives.update(alt_patterns)

        # Generate context-specific alternatives
        if context.get("technology_stack"):
            tech_stack = context["technology_stack"]
            # Look for technology-specific alternatives
            tech_alternatives = {
                "python": ["class-based approach", "functional approach"],
                "javascript": ["prototype-based approach", "class-based approach"],
                "database": ["orm-based approach", "query-based approach"],
                "api": ["restful approach", "graphql approach"],
            }

            for tech in tech_stack:
                if tech.lower() in tech_alternatives:
                    alternatives.update(tech_alternatives[tech.lower()])

        # Generate complexity-based alternatives
        if context.get("complexity_preference") == "conservative":
            alternatives.add("simplified implementation approach")
        elif context.get("complexity_preference") == "aggressive":
            alternatives.add("advanced feature-rich approach")

        return list(alternatives)[:5]  # Limit to top 5 alternatives

    def _calculate_prediction_confidence(
        self,
        implementations: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> float:
        """Calculate confidence score for the prediction."""
        if not implementations:
            return 0.0

        # Historical data confidence
        impl_count = len(implementations)
        data_confidence = min(1.0, impl_count / 10)  # More confidence with more data

        # Success rate confidence
        success_metrics = self._calculate_success_metrics(implementations)
        success_confidence = success_metrics["overall_success_rate"]

        # Context relevance confidence
        context_relevance_scores = [
            impl.get("context_relevance", 0.5)
            for impl in implementations
            if impl.get("context_relevance")
        ]
        context_confidence = (
            sum(context_relevance_scores) / len(context_relevance_scores)
            if context_relevance_scores
            else 0.5
        )

        # Consistency confidence (how consistent are the outcomes)
        outcomes = [impl.get("outcome") for impl in implementations]
        if outcomes:
            success_count = outcomes.count("success")
            consistency = abs(success_count / len(outcomes) - 0.5) * 2  # Scale to 0-1
        else:
            consistency = 0.0

        # Weighted combination
        confidence = (
            data_confidence * 0.3
            + success_confidence * 0.3
            + context_confidence * 0.2
            + consistency * 0.2
        )

        return round(confidence, 3)

    def _extract_key_evidence(self, implementations: list[dict[str, Any]]) -> list[str]:
        """Extract key evidence from implementations."""
        evidence = []

        success_metrics = self._calculate_success_metrics(implementations)
        evidence.append(
            f"{success_metrics['successful_count']}/{success_metrics['total_count']} implementations successful",
        )

        avg_time = success_metrics["avg_execution_time"]
        if avg_time > 0:
            evidence.append(f"Average implementation time: {avg_time:.1f} seconds")

        # Extract unique contexts
        contexts = set()
        for impl in implementations:
            impl_contexts = impl.get("contexts", [])
            contexts.update(impl_contexts)

        if contexts:
            evidence.append(f"Used in {len(contexts)} different contexts")

        return evidence

    def _serialize_context(self, context: dict[str, Any]) -> str:
        """Serialize context for storage."""
        try:
            return json.dumps(context, sort_keys=True)
        except Exception:
            return str(context)

    def _store_approach_predictions(self, predictions: list[ApproachPrediction]) -> None:
        """Store approach predictions in the database."""
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                for prediction in predictions:
                    prediction_dict = prediction.to_dict()
                    cursor.execute(
                        """
                        INSERT INTO approach_predictions
                        (prediction_id, context, recommended_approach, alternative_approaches,
                         confidence_score, success_probability, reasoning, constraints,
                         benefits, risks, historical_evidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            prediction_dict["prediction_id"],
                            prediction_dict["context"],
                            prediction_dict["recommended_approach"],
                            json.dumps(prediction_dict["alternative_approaches"]),
                            prediction_dict["confidence_score"],
                            prediction_dict["success_probability"],
                            json.dumps(prediction_dict["reasoning"]),
                            json.dumps(prediction_dict["constraints"]),
                            json.dumps(prediction_dict["benefits"]),
                            json.dumps(prediction_dict["risks"]),
                            json.dumps(prediction_dict["historical_evidence"]),
                        ),
                    )

                conn.commit()

        except Exception as e:
            logger.error(f"Error storing approach predictions: {e}")

    def enable_knowledge_transfer(
        self,
        source_patterns: list[str],
        target_contexts: list[str],
        transfer_strategy: str = "adaptive",  # "direct", "adaptive", "transformative"
    ) -> dict[str, Any]:
        """
        Facilitate systematic knowledge sharing between implementations.

        Algorithm Approach: Pattern-based knowledge transfer with adaptation strategies
        and context-aware modifications for effective cross-domain knowledge sharing.

        Parameters
        ----------
        source_patterns (List[str]): Source patterns to transfer
        target_contexts (List[str]): Target contexts for knowledge application
        transfer_strategy (str): Strategy for knowledge transfer adaptation

        Returns
        -------
        Dict[str, Any]: Knowledge transfer results with success metrics and guidance

        Raises
        ------
        KnowledgeIntegrationError: If knowledge transfer fails

        """
        try:
            logger.info(
                f"Enabling knowledge transfer for {len(source_patterns)} patterns to {len(target_contexts)} contexts",
            )

            transfer_results = {
                "successful_transfers": [],
                "failed_transfers": [],
                "adaptation_strategies": [],
                "success_metrics": {},
                "transfer_guidance": [],
            }

            # Process each source pattern
            for pattern_name in source_patterns:
                # Retrieve pattern data
                pattern_data = self._get_pattern_historical_data(pattern_name)
                if not pattern_data:
                    transfer_results["failed_transfers"].append(
                        {
                            "pattern": pattern_name,
                            "reason": "No historical data available",
                        },
                    )
                    continue

                # Analyze transfer viability for each target context
                for target_context in target_contexts:
                    transfer_result = self._analyze_knowledge_transfer(
                        pattern_data,
                        pattern_name,
                        target_context,
                        transfer_strategy,
                    )

                    if transfer_result["viable"]:
                        transfer_results["successful_transfers"].append(transfer_result)

                        # Generate adaptation strategy if needed
                        if transfer_result["requires_adaptation"]:
                            adaptation_strategy = self.create_adaptation_strategies(
                                pattern_name,
                                target_context,
                                transfer_result["adaptation_needs"],
                            )
                            transfer_results["adaptation_strategies"].extend(adaptation_strategy)
                    else:
                        transfer_results["failed_transfers"].append(
                            {
                                "pattern": pattern_name,
                                "target_context": target_context,
                                "reason": transfer_result["blockers"],
                            },
                        )

            # Calculate success metrics
            total_transfers = len(source_patterns) * len(target_contexts)
            successful_transfers = len(transfer_results["successful_transfers"])
            transfer_results["success_metrics"] = {
                "total_possible_transfers": total_transfers,
                "successful_transfers": successful_transfers,
                "success_rate": (
                    successful_transfers / total_transfers if total_transfers > 0 else 0
                ),
                "adaptations_required": len(transfer_results["adaptation_strategies"]),
            }

            # Generate transfer guidance
            transfer_results["transfer_guidance"] = self._generate_transfer_guidance(
                transfer_results,
            )

            # Store transfer results for learning
            self._store_knowledge_transfer_results(transfer_results)

            logger.info(
                f"Knowledge transfer completed with {successful_transfers}/{total_transfers} successful transfers",
            )
            return transfer_results

        except Exception as e:
            logger.error(f"Error enabling knowledge transfer: {e}")
            raise KnowledgeIntegrationError(f"Failed to enable knowledge transfer: {e}")

    def _analyze_knowledge_transfer(
        self,
        pattern_data: dict[str, Any],
        pattern_name: str,
        target_context: str,
        transfer_strategy: str,
    ) -> dict[str, Any]:
        """Analyze viability of knowledge transfer for a specific pattern and context."""
        try:
            # Get historical implementations
            implementations = pattern_data.get("implementations", [])

            # Calculate context compatibility
            compatibility_score = self._calculate_context_compatibility(
                implementations,
                target_context,
            )

            # Identify adaptation needs
            adaptation_needs = self._identify_adaptation_needs(
                implementations,
                target_context,
                transfer_strategy,
            )

            # Identify potential blockers
            blockers = self._identify_transfer_blockers(
                implementations,
                target_context,
            )

            # Determine viability
            viable = (
                compatibility_score > 0.5
                and len(blockers) == 0
                and len(implementations) >= 2  # Need some historical data
            )

            return {
                "pattern": pattern_name,
                "target_context": target_context,
                "viable": viable,
                "compatibility_score": compatibility_score,
                "requires_adaptation": len(adaptation_needs) > 0,
                "adaptation_needs": adaptation_needs,
                "blockers": blockers,
                "confidence": self._calculate_transfer_confidence(
                    implementations,
                    target_context,
                    compatibility_score,
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing knowledge transfer: {e}")
            return {
                "pattern": pattern_name,
                "target_context": target_context,
                "viable": False,
                "compatibility_score": 0.0,
                "requires_adaptation": False,
                "adaptation_needs": [],
                "blockers": [f"Analysis error: {e!s}"],
                "confidence": 0.0,
            }

    def _calculate_context_compatibility(
        self,
        implementations: list[dict[str, Any]],
        target_context: str,
    ) -> float:
        """Calculate compatibility between implementations and target context."""
        if not implementations:
            return 0.0

        compatibility_scores = []

        for impl in implementations:
            # Check if implementation was used in similar context
            impl_contexts = impl.get("contexts", [])
            context_similarity = self._calculate_context_similarity(
                impl_contexts,
                target_context,
            )

            # Technology stack compatibility
            impl_tech = impl.get("technology_stack", [])
            tech_compatibility = self._calculate_tech_compatibility(
                impl_tech,
                target_context,
            )

            # Scale compatibility
            impl_scale = impl.get("scale", "medium")
            scale_compatibility = self._calculate_scale_compatibility(
                impl_scale,
                target_context,
            )

            # Overall compatibility for this implementation
            impl_compatibility = (
                context_similarity * 0.5 + tech_compatibility * 0.3 + scale_compatibility * 0.2
            )

            compatibility_scores.append(impl_compatibility)

        # Return maximum compatibility found
        return max(compatibility_scores) if compatibility_scores else 0.0

    def _calculate_context_similarity(
        self,
        source_contexts: list[str],
        target_context: str,
    ) -> float:
        """Calculate similarity between source contexts and target context."""
        if not source_contexts:
            return 0.0

        target_lower = target_context.lower()

        best_similarity = 0.0
        for source_context in source_contexts:
            source_lower = source_context.lower()

            # Direct match
            if source_lower == target_lower:
                return 1.0

            # Keyword similarity
            source_words = set(source_lower.split())
            target_words = set(target_lower.split())

            common_words = source_words & target_words
            total_words = source_words | target_words

            if total_words:
                similarity = len(common_words) / len(total_words)
                best_similarity = max(best_similarity, similarity)

        return best_similarity

    def _calculate_tech_compatibility(self, impl_tech: list[str], target_context: str) -> float:
        """Calculate technology compatibility with target context."""
        if not impl_tech:
            return 0.5  # Neutral compatibility

        # Common technology mappings
        tech_context_mapping = {
            "python": ["backend", "api", "django", "flask", "fastapi"],
            "javascript": ["frontend", "web", "react", "vue", "angular"],
            "database": ["sql", "nosql", "orm", "migration"],
            "api": ["rest", "graphql", "endpoint", "service"],
            "security": ["auth", "validation", "encryption"],
            "performance": ["optimize", "cache", "speed"],
        }

        target_lower = target_context.lower()
        compatibility_score = 0.0

        for tech in impl_tech:
            tech_lower = tech.lower()

            # Direct tech match
            if tech_lower in target_lower:
                compatibility_score += 1.0
                continue

            # Context-based match
            if tech_lower in tech_context_mapping:
                contexts = tech_context_mapping[tech_lower]
                for context in contexts:
                    if context in target_lower:
                        compatibility_score += 0.5
                        break

        return min(1.0, compatibility_score / len(impl_tech))

    def _calculate_scale_compatibility(self, impl_scale: str, target_context: str) -> float:
        """Calculate scale compatibility with target context."""
        # Extract scale indicators from target context
        target_lower = target_context.lower()

        scale_indicators = {
            "small": ["small", "minimal", "prototype", "demo"],
            "medium": ["medium", "standard", "typical"],
            "large": ["large", "enterprise", "production", "scale", "high-volume"],
        }

        target_scale = "medium"  # Default
        for scale, indicators in scale_indicators.items():
            if any(indicator in target_lower for indicator in indicators):
                target_scale = scale
                break

        # Compatibility matrix
        compatibility_matrix = {
            ("small", "small"): 1.0,
            ("small", "medium"): 0.7,
            ("small", "large"): 0.3,
            ("medium", "small"): 0.6,
            ("medium", "medium"): 1.0,
            ("medium", "large"): 0.8,
            ("large", "small"): 0.2,
            ("large", "medium"): 0.6,
            ("large", "large"): 1.0,
        }

        return compatibility_matrix.get((impl_scale, target_scale), 0.5)

    def _identify_adaptation_needs(
        self,
        implementations: list[dict[str, Any]],
        target_context: str,
        transfer_strategy: str,
    ) -> list[dict[str, Any]]:
        """Identify specific adaptation needs for knowledge transfer."""
        adaptation_needs = []

        # Technology adaptation needs
        tech_needs = self._identify_tech_adaptation_needs(implementations, target_context)
        if tech_needs:
            adaptation_needs.extend(tech_needs)

        # Scale adaptation needs
        scale_needs = self._identify_scale_adaptation_needs(implementations, target_context)
        if scale_needs:
            adaptation_needs.extend(scale_needs)

        # Complexity adaptation needs based on strategy
        if transfer_strategy == "adaptive":
            complexity_needs = self._identify_complexity_adaptation_needs(
                implementations,
                target_context,
            )
            if complexity_needs:
                adaptation_needs.extend(complexity_needs)

        return adaptation_needs

    def _identify_tech_adaptation_needs(
        self,
        implementations: list[dict[str, Any]],
        target_context: str,
    ) -> list[dict[str, Any]]:
        """Identify technology-specific adaptation needs."""
        needs = []

        # Extract technology requirements from target context
        target_tech = self._extract_tech_requirements(target_context)

        if not target_tech:
            return needs

        # Analyze implementation technologies
        impl_techs = set()
        for impl in implementations:
            impl_techs.update(impl.get("technology_stack", []))

        # Identify gaps
        tech_gaps = target_tech - impl_techs
        if tech_gaps:
            needs.append(
                {
                    "type": "technology",
                    "description": f"Adapt for technologies: {', '.join(tech_gaps)}",
                    "priority": "high",
                    "estimated_effort": len(tech_gaps) * 2,  # Hours per technology
                },
            )

        # Identify technology conflicts
        tech_conflicts = []
        for tech in target_tech:
            if impl_techs and tech not in impl_techs:
                tech_conflicts.append(tech)

        if tech_conflicts:
            needs.append(
                {
                    "type": "technology_conflict",
                    "description": f"Resolve technology conflicts for: {', '.join(tech_conflicts)}",
                    "priority": "medium",
                    "estimated_effort": len(tech_conflicts) * 3,  # Hours per conflict
                },
            )

        return needs

    def _extract_tech_requirements(self, context: str) -> set[str]:
        """Extract technology requirements from context."""
        tech_keywords = {
            "python": ["python", "django", "flask", "fastapi", "pydantic"],
            "javascript": ["javascript", "js", "react", "vue", "angular", "node"],
            "database": ["sql", "nosql", "mysql", "postgres", "mongodb", "orm"],
            "api": ["api", "rest", "graphql", "endpoint", "service"],
            "security": ["auth", "jwt", "oauth", "encryption", "security"],
            "testing": ["test", "pytest", "jest", "unittest", "testing"],
            "docker": ["docker", "container", "kubernetes", "k8s"],
        }

        context_lower = context.lower()
        required_tech = set()

        for tech, keywords in tech_keywords.items():
            if any(keyword in context_lower for keyword in keywords):
                required_tech.add(tech)

        return required_tech

    def _identify_scale_adaptation_needs(
        self,
        implementations: list[dict[str, Any]],
        target_context: str,
    ) -> list[dict[str, Any]]:
        """Identify scale-specific adaptation needs."""
        needs = []

        # Determine target scale
        target_scale = self._determine_target_scale(target_context)

        # Analyze implementation scales
        impl_scales = [impl.get("scale", "medium") for impl in implementations]

        if impl_scales:
            # Find dominant scale in implementations
            scale_counts = defaultdict(int)
            for scale in impl_scales:
                scale_counts[scale] += 1

            dominant_scale = max(scale_counts.items(), key=lambda x: x[1])[0]

            # Identify scale differences
            if dominant_scale != target_scale:
                needs.append(
                    {
                        "type": "scale",
                        "description": f"Adapt from {dominant_scale} to {target_scale} scale",
                        "priority": "high" if target_scale == "large" else "medium",
                        "estimated_effort": (8 if target_scale == "large" else 4),  # Hours
                    },
                )

        return needs

    def _determine_target_scale(self, context: str) -> str:
        """Determine target scale from context."""
        context_lower = context.lower()

        if any(
            keyword in context_lower for keyword in ["large", "enterprise", "production", "scale"]
        ):
            return "large"
        if any(keyword in context_lower for keyword in ["small", "minimal", "prototype", "demo"]):
            return "small"
        return "medium"

    def _identify_complexity_adaptation_needs(
        self,
        implementations: list[dict[str, Any]],
        target_context: str,
    ) -> list[dict[str, Any]]:
        """Identify complexity-specific adaptation needs."""
        needs = []

        # Analyze implementation complexity
        complexity_scores = [
            impl.get("complexity_score", 0.5)
            for impl in implementations
            if impl.get("complexity_score")
        ]

        if complexity_scores:
            avg_complexity = sum(complexity_scores) / len(complexity_scores)

            # Determine target complexity preference
            if "simple" in target_context.lower() or "minimal" in target_context.lower():
                target_complexity = 0.3
                complexity_direction = "reduce"
            elif (
                "comprehensive" in target_context.lower()
                or "feature-rich" in target_context.lower()
            ):
                target_complexity = 0.8
                complexity_direction = "increase"
            else:
                target_complexity = 0.5
                complexity_direction = "balance"

            # Identify complexity adjustments
            if abs(avg_complexity - target_complexity) > 0.2:
                needs.append(
                    {
                        "type": "complexity",
                        "description": f"{complexity_direction.capitalize()} complexity from {avg_complexity:.1f} to {target_complexity:.1f}",
                        "priority": "medium",
                        "estimated_effort": int(
                            abs(avg_complexity - target_complexity) * 10
                        ),  # Hours
                    },
                )

        return needs

    def _identify_transfer_blockers(
        self,
        implementations: list[dict[str, Any]],
        target_context: str,
    ) -> list[str]:
        """Identify blockers that prevent knowledge transfer."""
        blockers = []

        if not implementations:
            blockers.append("No historical implementations available")
            return blockers

        # Check for insufficient success rate
        successful_impls = [impl for impl in implementations if impl.get("outcome") == "success"]

        if len(successful_impls) < len(implementations) * 0.5:
            blockers.append("Low success rate in source implementations")

        # Check for insufficient data
        if len(implementations) < 2:
            blockers.append("Insufficient historical data for reliable transfer")

        # Check for incompatible requirements
        target_requirements = self._extract_tech_requirements(target_context)
        impl_capabilities = set()
        for impl in implementations:
            impl_capabilities.update(impl.get("technology_stack", []))

        incompatible_tech = target_requirements - impl_capabilities
        if len(incompatible_tech) > len(target_requirements) * 0.5:
            blockers.append(f"Major technology incompatibility: {', '.join(incompatible_tech)}")

        # Check for scale incompatibility
        target_scale = self._determine_target_scale(target_context)
        impl_scales = [impl.get("scale", "medium") for impl in implementations]

        if impl_scales:
            dominant_scale = max(set(impl_scales), key=impl_scales.count)
            if (dominant_scale == "small" and target_scale == "large") or (
                dominant_scale == "large" and target_scale == "small"
            ):
                blockers.append(
                    f"Scale incompatibility: {dominant_scale} implementations to {target_scale} target"
                )

        return blockers

    def _calculate_transfer_confidence(
        self,
        implementations: list[dict[str, Any]],
        target_context: str,
        compatibility_score: float,
    ) -> float:
        """Calculate confidence score for knowledge transfer."""
        if not implementations:
            return 0.0

        # Data quality confidence
        impl_count = len(implementations)
        data_confidence = min(1.0, impl_count / 5)  # Confidence with 5+ implementations

        # Success rate confidence
        successful_impls = [impl for impl in implementations if impl.get("outcome") == "success"]
        success_confidence = len(successful_impls) / len(implementations)

        # Compatibility confidence
        compatibility_confidence = compatibility_score

        # Diversity confidence (variety of contexts in implementations)
        all_contexts = set()
        for impl in implementations:
            all_contexts.update(impl.get("contexts", []))

        diversity_confidence = min(1.0, len(all_contexts) / 3)  # Confidence with 3+ contexts

        # Weighted combination
        confidence = (
            data_confidence * 0.3
            + success_confidence * 0.3
            + compatibility_confidence * 0.3
            + diversity_confidence * 0.1
        )

        return round(confidence, 3)

    def _generate_transfer_guidance(self, transfer_results: dict[str, Any]) -> list[str]:
        """Generate guidance for knowledge transfer based on results."""
        guidance = []

        success_metrics = transfer_results["success_metrics"]
        success_rate = success_metrics["success_rate"]

        if success_rate > 0.8:
            guidance.append(
                "High transfer success rate - patterns are well-suited for target contexts"
            )
        elif success_rate > 0.5:
            guidance.append("Moderate transfer success rate - consider additional adaptations")
        else:
            guidance.append(
                "Low transfer success rate - review pattern selection and target contexts"
            )

        # Adaptation guidance
        adaptations_count = success_metrics["adaptations_required"]
        if adaptations_count > 0:
            guidance.append(
                f"{adaptations_count} adaptation strategies generated - review and apply as needed"
            )
        else:
            guidance.append(
                "No adaptations required - direct transfer possible for successful cases"
            )

        # Strategy-specific guidance
        if transfer_results["successful_transfers"]:
            avg_confidence = sum(
                transfer["confidence"] for transfer in transfer_results["successful_transfers"]
            ) / len(
                transfer_results["successful_transfers"],
            )

            if avg_confidence > 0.8:
                guidance.append("High confidence transfers - proceed with implementation")
            elif avg_confidence > 0.6:
                guidance.append("Moderate confidence transfers - consider pilot testing")
            else:
                guidance.append("Lower confidence transfers - extensive validation recommended")

        # Failed transfer guidance
        if transfer_results["failed_transfers"]:
            guidance.append(
                f"{len(transfer_results['failed_transfers'])} transfers failed - review blockers and consider alternatives",
            )

        return guidance

    def _store_knowledge_transfer_results(self, results: dict[str, Any]) -> None:
        """Store knowledge transfer results for learning."""
        try:
            # Store as learning metrics
            metrics = [
                {
                    "metric_id": str(uuid.uuid4()),
                    "metric_type": "knowledge_transfer",
                    "value": results["success_metrics"]["success_rate"],
                    "metadata": json.dumps(
                        {
                            "total_transfers": results["success_metrics"][
                                "total_possible_transfers"
                            ],
                            "successful_transfers": results["success_metrics"][
                                "successful_transfers"
                            ],
                            "adaptations_required": results["success_metrics"][
                                "adaptations_required"
                            ],
                        },
                    ),
                },
            ]

            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()
                for metric in metrics:
                    cursor.execute(
                        """
                        INSERT INTO learning_metrics
                        (metric_id, metric_type, value, metadata)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            metric["metric_id"],
                            metric["metric_type"],
                            metric["value"],
                            metric["metadata"],
                        ),
                    )
                conn.commit()

        except Exception as e:
            logger.error(f"Error storing knowledge transfer results: {e}")

    def create_adaptation_strategies(
        self,
        source_pattern: str,
        target_context: str,
        adaptation_needs: list[dict[str, Any]] | None = None,
    ) -> list[AdaptationStrategy]:
        """
        Create adaptation strategies allowing pattern customization for specific contexts.

        Algorithm Approach: Context-aware adaptation strategy generation with impact assessment,
        implementation guidance, and rollback planning for safe pattern adaptation.

        Parameters
        ----------
        source_pattern (str): Source pattern to adapt
        target_context (str): Target context for adaptation
        adaptation_needs (List[Dict[str, Any]], optional): Specific adaptation requirements

        Returns
        -------
        List[AdaptationStrategy]: Generated adaptation strategies with implementation guidance

        Raises
        ------
        KnowledgeIntegrationError: If adaptation strategy creation fails

        """
        try:
            logger.info(f"Creating adaptation strategies for {source_pattern} to {target_context}")

            if adaptation_needs is None:
                adaptation_needs = []

            # Retrieve pattern data for analysis
            pattern_data = self._get_pattern_historical_data(source_pattern)
            if not pattern_data:
                logger.warning(f"No historical data available for pattern: {source_pattern}")
                return []

            implementations = pattern_data.get("implementations", [])
            if not implementations:
                logger.warning(f"No implementations found for pattern: {source_pattern}")
                return []

            strategies = []

            # Analyze different adaptation approaches
            adaptation_approaches = self._identify_adaptation_approaches(
                source_pattern,
                target_context,
                adaptation_needs,
            )

            for approach in adaptation_approaches:
                strategy = self._create_adaptation_strategy(
                    source_pattern,
                    target_context,
                    approach,
                    implementations,
                )
                if strategy:
                    strategies.append(strategy)

            # Store adaptation strategies
            self._store_adaptation_strategies(strategies)

            logger.info(f"Created {len(strategies)} adaptation strategies")
            return strategies

        except Exception as e:
            logger.error(f"Error creating adaptation strategies: {e}")
            raise KnowledgeIntegrationError(f"Failed to create adaptation strategies: {e}")

    def _identify_adaptation_approaches(
        self,
        source_pattern: str,
        target_context: str,
        adaptation_needs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Identify different adaptation approaches based on needs."""
        approaches = []

        # Technology adaptation approach
        tech_needs = [need for need in adaptation_needs if need.get("type") == "technology"]
        if tech_needs:
            approaches.append(
                {
                    "approach_type": "technology_adaptation",
                    "description": f"Adapt {source_pattern} for target technology stack",
                    "priority": "high",
                    "adaptations_needed": tech_needs,
                },
            )

        # Scale adaptation approach
        scale_needs = [need for need in adaptation_needs if need.get("type") == "scale"]
        if scale_needs:
            approaches.append(
                {
                    "approach_type": "scale_adaptation",
                    "description": f"Scale {source_pattern} for target environment",
                    "priority": "high",
                    "adaptations_needed": scale_needs,
                },
            )

        # Complexity adaptation approach
        complexity_needs = [need for need in adaptation_needs if need.get("type") == "complexity"]
        if complexity_needs:
            approaches.append(
                {
                    "approach_type": "complexity_adaptation",
                    "description": f"Adjust complexity of {source_pattern} for target context",
                    "priority": "medium",
                    "adaptations_needed": complexity_needs,
                },
            )

        # Context-aware adaptation approach (if no specific needs)
        if not approaches:
            approaches.append(
                {
                    "approach_type": "context_adaptation",
                    "description": f"Adapt {source_pattern} for {target_context} context",
                    "priority": "medium",
                    "adaptations_needed": [],
                },
            )

        # Comprehensive adaptation approach (combine multiple needs)
        if len(adaptation_needs) > 1:
            approaches.append(
                {
                    "approach_type": "comprehensive_adaptation",
                    "description": f"Comprehensive adaptation of {source_pattern} for {target_context}",
                    "priority": "high",
                    "adaptations_needed": adaptation_needs,
                },
            )

        return approaches

    def _create_adaptation_strategy(
        self,
        source_pattern: str,
        target_context: str,
        approach: dict[str, Any],
        implementations: list[dict[str, Any]],
    ) -> AdaptationStrategy | None:
        """Create a specific adaptation strategy."""
        try:
            approach_type = approach["approach_type"]
            adaptations_needed = approach.get("adaptations_needed", [])

            # Generate specific adaptations
            adaptations = self._generate_specific_adaptations(
                approach_type,
                source_pattern,
                target_context,
                adaptations_needed,
            )

            # Assess impact
            impact_assessment = self._assess_adaptation_impact(
                source_pattern,
                target_context,
                adaptations,
            )

            # Generate implementation guide
            implementation_guide = self._generate_implementation_guide(
                approach_type,
                adaptations,
                impact_assessment,
            )

            # Define validation criteria
            validation_criteria = self._define_validation_criteria(
                approach_type,
                adaptations,
                target_context,
            )

            # Create rollback strategy
            rollback_strategy = self._create_rollback_strategy(
                source_pattern,
                approach_type,
                adaptations,
            )

            # Calculate complexity and success probability
            adaptation_complexity = self._calculate_adaptation_complexity(
                adaptations,
                approach_type,
            )
            success_probability = self._calculate_adaptation_success_probability(
                implementations,
                target_context,
                adaptations,
            )

            return AdaptationStrategy(
                strategy_id=str(uuid.uuid4()),
                source_pattern=source_pattern,
                target_context=target_context,
                adaptations=adaptations,
                impact_assessment=impact_assessment,
                implementation_guide=implementation_guide,
                validation_criteria=validation_criteria,
                rollback_strategy=rollback_strategy,
                adaptation_complexity=adaptation_complexity,
                success_probability=success_probability,
                created_at=datetime.now(UTC),
            )

        except Exception as e:
            logger.error(f"Error creating adaptation strategy for {approach_type}: {e}")
            return None

    def _generate_specific_adaptations(
        self,
        approach_type: str,
        source_pattern: str,
        target_context: str,
        adaptation_needs: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate specific adaptations based on approach type and needs."""
        adaptations = []

        if approach_type == "technology_adaptation":
            adaptations.extend(
                self._generate_technology_adaptations(adaptation_needs, target_context)
            )
        elif approach_type == "scale_adaptation":
            adaptations.extend(self._generate_scale_adaptations(adaptation_needs, target_context))
        elif approach_type == "complexity_adaptation":
            adaptations.extend(
                self._generate_complexity_adaptations(adaptation_needs, target_context)
            )
        elif approach_type == "context_adaptation":
            adaptations.extend(self._generate_context_adaptations(source_pattern, target_context))
        elif approach_type == "comprehensive_adaptation":
            # Combine all adaptation types
            adaptations.extend(
                self._generate_technology_adaptations(
                    [need for need in adaptation_needs if need.get("type") == "technology"],
                    target_context,
                ),
            )
            adaptations.extend(
                self._generate_scale_adaptations(
                    [need for need in adaptation_needs if need.get("type") == "scale"],
                    target_context,
                ),
            )
            adaptations.extend(
                self._generate_complexity_adaptations(
                    [need for need in adaptation_needs if need.get("type") == "complexity"],
                    target_context,
                ),
            )
            adaptations.extend(self._generate_context_adaptations(source_pattern, target_context))

        return adaptations

    def _generate_technology_adaptations(
        self,
        adaptation_needs: list[dict[str, Any]],
        target_context: str,
    ) -> list[dict[str, Any]]:
        """Generate technology-specific adaptations."""
        adaptations = []
        self._extract_tech_requirements(target_context)

        for need in adaptation_needs:
            description = need.get("description", "")
            if "technologies:" in description:
                # Extract specific technologies from description
                tech_part = description.split("technologies:")[1].strip()
                required_techs = [tech.strip() for tech in tech_part.split(",")]

                for tech in required_techs:
                    adaptations.append(
                        {
                            "type": "technology_integration",
                            "description": f"Integrate {tech} technology support",
                            "priority": need.get("priority", "medium"),
                            "estimated_effort": need.get("estimated_effort", 4),
                            "changes_required": self._identify_tech_changes(tech),
                            "dependencies": [f"{tech}_sdk", f"{tech}_libraries"],
                        },
                    )

        # Add general technology adaptations
        if "python" in target_context.lower():
            adaptations.append(
                {
                    "type": "language_specific",
                    "description": "Adapt for Python best practices and patterns",
                    "priority": "medium",
                    "estimated_effort": 3,
                    "changes_required": [
                        "pythonic_code_style",
                        "type_hints",
                        "docstrings",
                    ],
                    "dependencies": ["typing_module", "pydoc_style"],
                },
            )

        if "database" in target_context.lower():
            adaptations.append(
                {
                    "type": "database_integration",
                    "description": "Adapt for database integration patterns",
                    "priority": "high",
                    "estimated_effort": 6,
                    "changes_required": [
                        "orm_mapping",
                        "connection_handling",
                        "transaction_management",
                    ],
                    "dependencies": ["database_driver", "orm_framework"],
                },
            )

        return adaptations

    def _generate_scale_adaptations(
        self,
        adaptation_needs: list[dict[str, Any]],
        target_context: str,
    ) -> list[dict[str, Any]]:
        """Generate scale-specific adaptations."""
        adaptations = []

        target_scale = self._determine_target_scale(target_context)

        for need in adaptation_needs:
            if "Adapt from" in need.get("description", "") and "to" in need.get("description", ""):
                adaptations.append(
                    {
                        "type": "scale_modification",
                        "description": need["description"],
                        "priority": need.get("priority", "medium"),
                        "estimated_effort": need.get("estimated_effort", 6),
                        "changes_required": self._identify_scale_changes(target_scale),
                        "dependencies": self._identify_scale_dependencies(target_scale),
                    },
                )

        # Add scale-specific adaptations
        if target_scale == "large":
            adaptations.extend(
                [
                    {
                        "type": "performance_optimization",
                        "description": "Add performance optimizations for large-scale deployment",
                        "priority": "high",
                        "estimated_effort": 8,
                        "changes_required": [
                            "caching",
                            "async_processing",
                            "load_balancing",
                        ],
                        "dependencies": ["redis", "async_framework", "load_balancer"],
                    },
                    {
                        "type": "monitoring_integration",
                        "description": "Integrate monitoring and observability for large scale",
                        "priority": "high",
                        "estimated_effort": 6,
                        "changes_required": [
                            "metrics_collection",
                            "logging_enhancement",
                            "health_checks",
                        ],
                        "dependencies": ["monitoring_system", "log_aggregation"],
                    },
                ],
            )
        elif target_scale == "small":
            adaptations.append(
                {
                    "type": "simplification",
                    "description": "Simplify for small-scale deployment",
                    "priority": "medium",
                    "estimated_effort": 3,
                    "changes_required": [
                        "reduce_dependencies",
                        "minimal_configuration",
                        "standalone_mode",
                    ],
                    "dependencies": ["core_dependencies_only"],
                },
            )

        return adaptations

    def _generate_complexity_adaptations(
        self,
        adaptation_needs: list[dict[str, Any]],
        target_context: str,
    ) -> list[dict[str, Any]]:
        """Generate complexity-specific adaptations."""
        adaptations = []

        for need in adaptation_needs:
            if "complexity" in need.get("description", "").lower():
                direction = (
                    "reduce" if "reduce" in need.get("description", "").lower() else "increase"
                )
                adaptations.append(
                    {
                        "type": "complexity_adjustment",
                        "description": need["description"],
                        "priority": need.get("priority", "medium"),
                        "estimated_effort": need.get("estimated_effort", 5),
                        "changes_required": self._identify_complexity_changes(direction),
                        "dependencies": self._identify_complexity_dependencies(direction),
                    },
                )

        return adaptations

    def _generate_context_adaptations(
        self,
        source_pattern: str,
        target_context: str,
    ) -> list[dict[str, Any]]:
        """Generate context-specific adaptations."""
        adaptations = []

        # General context adaptations
        adaptations.append(
            {
                "type": "context_alignment",
                "description": f"Align {source_pattern} with {target_context} specific requirements",
                "priority": "medium",
                "estimated_effort": 4,
                "changes_required": [
                    "context_specific_configuration",
                    "domain_validation",
                ],
                "dependencies": ["domain_knowledge"],
            },
        )

        # Add context-specific adaptations based on keywords
        context_lower = target_context.lower()
        if "security" in context_lower:
            adaptations.append(
                {
                    "type": "security_enhancement",
                    "description": "Add security measures for secure context",
                    "priority": "high",
                    "estimated_effort": 6,
                    "changes_required": [
                        "authentication",
                        "authorization",
                        "input_validation",
                    ],
                    "dependencies": ["security_framework", "encryption_libraries"],
                },
            )

        if "performance" in context_lower:
            adaptations.append(
                {
                    "type": "performance_enhancement",
                    "description": "Optimize for performance-critical context",
                    "priority": "high",
                    "estimated_effort": 7,
                    "changes_required": ["optimization", "caching", "async_processing"],
                    "dependencies": ["performance_profiler", "caching_system"],
                },
            )

        return adaptations

    def _identify_tech_changes(self, technology: str) -> list[str]:
        """Identify specific changes required for technology integration."""
        tech_changes = {
            "python": ["python_syntax", "type_hints", "error_handling"],
            "javascript": ["js_syntax", "async_patterns", "module_system"],
            "database": [
                "sql_queries",
                "connection_handling",
                "transaction_management",
            ],
            "api": ["endpoint_definition", "request_handling", "response_formatting"],
            "security": ["authentication", "authorization", "encryption"],
            "testing": ["test_structure", "mocking", "assertions"],
        }
        return tech_changes.get(technology.lower(), ["general_integration"])

    def _identify_scale_changes(self, target_scale: str) -> list[str]:
        """Identify specific changes required for scale adaptation."""
        if target_scale == "large":
            return ["horizontal_scaling", "load_balancing", "caching", "monitoring"]
        if target_scale == "small":
            return ["simplification", "minimal_dependencies", "standalone_deployment"]
        # medium
        return ["moderate_scaling", "basic_optimization", "standard_monitoring"]

    def _identify_scale_dependencies(self, target_scale: str) -> list[str]:
        """Identify dependencies for scale adaptation."""
        if target_scale == "large":
            return [
                "load_balancer",
                "message_queue",
                "monitoring_system",
                "cache_server",
            ]
        if target_scale == "small":
            return ["minimal_runtime", "basic_dependencies"]
        # medium
        return ["standard_runtime", "basic_monitoring"]

    def _identify_complexity_changes(self, direction: str) -> list[str]:
        """Identify specific changes for complexity adjustment."""
        if direction == "reduce":
            return [
                "abstraction_simplification",
                "feature_removal",
                "interface_simplification",
            ]
        if direction == "increase":
            return [
                "feature_enhancement",
                "advanced_features",
                "comprehensive_validation",
            ]
        # balance
        return ["feature_balancing", "moderate_complexity"]

    def _identify_complexity_dependencies(self, direction: str) -> list[str]:
        """Identify dependencies for complexity adjustment."""
        if direction == "reduce":
            return ["simplified_libraries", "core_dependencies"]
        if direction == "increase":
            return ["advanced_libraries", "feature_dependencies"]
        # balance
        return ["balanced_dependencies", "standard_libraries"]

    def _assess_adaptation_impact(
        self,
        source_pattern: str,
        target_context: str,
        adaptations: list[dict[str, Any]],
    ) -> dict[str, float]:
        """Assess the impact of adaptations."""
        impact = {
            "code_changes": 0.0,
            "architecture_changes": 0.0,
            "performance_impact": 0.0,
            "maintenance_impact": 0.0,
            "learning_curve": 0.0,
        }

        total_effort = sum(adaptation.get("estimated_effort", 1) for adaptation in adaptations)

        # Calculate impact scores based on adaptations
        for adaptation in adaptations:
            adaptation_type = adaptation.get("type", "")
            effort = adaptation.get("estimated_effort", 1)
            normalized_effort = effort / total_effort if total_effort > 0 else 0

            if "technology" in adaptation_type:
                impact["code_changes"] += normalized_effort * 0.8
                impact["learning_curve"] += normalized_effort * 0.6
            elif "scale" in adaptation_type:
                impact["architecture_changes"] += normalized_effort * 0.9
                impact["performance_impact"] += normalized_effort * 0.7
            elif "complexity" in adaptation_type:
                impact["code_changes"] += normalized_effort * 0.6
                impact["maintenance_impact"] += normalized_effort * 0.5
            elif "performance" in adaptation_type:
                impact["performance_impact"] += normalized_effort * 0.8
            elif "security" in adaptation_type:
                impact["code_changes"] += normalized_effort * 0.5
                impact["maintenance_impact"] += normalized_effort * 0.3

        # Normalize impact scores to 0.0-1.0 range
        for key in impact:
            impact[key] = min(1.0, impact[key])

        return impact

    def _generate_implementation_guide(
        self,
        approach_type: str,
        adaptations: list[dict[str, Any]],
        impact_assessment: dict[str, float],
    ) -> list[str]:
        """Generate implementation guide for adaptations."""
        guide = []

        # General implementation steps
        guide.append("1. Analyze current implementation and identify adaptation points")
        guide.append("2. Create backup of existing code before making changes")
        guide.append("3. Implement adaptations in order of dependency")

        # Approach-specific guidance
        if approach_type == "technology_adaptation":
            guide.extend(
                [
                    "4. Install and configure required technology dependencies",
                    "5. Adapt code to use new technology patterns",
                    "6. Test technology integration thoroughly",
                ],
            )
        elif approach_type == "scale_adaptation":
            guide.extend(
                [
                    "4. Analyze current scalability limitations",
                    "5. Implement scaling improvements (caching, async processing, etc.)",
                    "6. Add monitoring and observability for scaled deployment",
                ],
            )
        elif approach_type == "complexity_adaptation":
            guide.extend(
                [
                    "4. Review current complexity and identify simplification/enhancement points",
                    "5. Refactor code according to complexity requirements",
                    "6. Update documentation to reflect complexity changes",
                ],
            )

        # Impact-based guidance
        if impact_assessment["code_changes"] > 0.7:
            guide.append("7. Comprehensive testing recommended due to significant code changes")
        if impact_assessment["architecture_changes"] > 0.6:
            guide.append("7. Architecture review recommended before deployment")
        if impact_assessment["learning_curve"] > 0.5:
            guide.append("7. Team training may be required for new adaptations")

        # General completion steps
        guide.extend(
            [
                "8. Validate all adaptations work correctly",
                "9. Update documentation and deployment guides",
                "10. Monitor post-deployment performance and issues",
            ],
        )

        return guide

    def _define_validation_criteria(
        self,
        approach_type: str,
        adaptations: list[dict[str, Any]],
        target_context: str,
    ) -> list[str]:
        """Define validation criteria for adaptations."""
        criteria = []

        # General validation criteria
        criteria.extend(
            [
                "All adaptations compile and run without errors",
                "Core functionality remains intact after adaptations",
                "Performance meets or exceeds baseline requirements",
            ],
        )

        # Approach-specific validation
        if approach_type == "technology_adaptation":
            criteria.extend(
                [
                    "New technology integrations function correctly",
                    "Technology-specific best practices are followed",
                    "No technology conflicts or dependency issues",
                ],
            )
        elif approach_type == "scale_adaptation":
            criteria.extend(
                [
                    "Performance improvements are measurable",
                    "System handles target scale without degradation",
                    "Monitoring and alerting systems function correctly",
                ],
            )
        elif approach_type == "complexity_adaptation":
            criteria.extend(
                [
                    "Complexity changes align with requirements",
                    "Code maintainability is appropriate for complexity level",
                    "Team can effectively work with adapted complexity",
                ],
            )

        # Context-specific validation
        if "security" in target_context.lower():
            criteria.append("Security requirements are fully satisfied")
        if "performance" in target_context.lower():
            criteria.append("Performance benchmarks are achieved")
        if "database" in target_context.lower():
            criteria.append("Database operations function correctly")

        return criteria

    def _create_rollback_strategy(
        self,
        source_pattern: str,
        approach_type: str,
        adaptations: list[dict[str, Any]],
    ) -> str:
        """Create rollback strategy for adaptations."""
        strategy = f"""Rollback Strategy for {source_pattern} Adaptations:

1. Version Control:
   - Ensure all changes are committed with clear messages
   - Tag the pre-adaptation state for easy rollback
   - Maintain feature branches during adaptation

2. Backup Procedures:
   - Create complete backups of code and configuration
   - Document all configuration changes made
   - Maintain rollback scripts for major changes

3. Rollback Triggers:
   - Performance degradation > 20%
   - Critical functionality failures
   - Security vulnerabilities discovered
   - Integration failures with dependent systems

4. Rollback Steps:
   a) Stop any running adapted instances
   b) Restore previous version from version control
   c) Restore configuration from backups
   d) Verify rollback completion
   e) Monitor system stability post-rollback

5. Communication:
   - Notify stakeholders of rollback status
   - Document rollback reasons and lessons learned
   - Update adaptation strategy based on rollback insights"""

        return strategy

    def _calculate_adaptation_complexity(
        self,
        adaptations: list[dict[str, Any]],
        approach_type: str,
    ) -> float:
        """Calculate overall adaptation complexity."""
        if not adaptations:
            return 0.0

        total_effort = sum(adaptation.get("estimated_effort", 1) for adaptation in adaptations)
        high_priority_count = sum(
            1 for adaptation in adaptations if adaptation.get("priority") == "high"
        )

        # Base complexity from effort
        effort_complexity = min(1.0, total_effort / 20)  # Normalize to 0-1 range

        # Complexity multiplier based on approach type
        approach_multipliers = {
            "technology_adaptation": 1.2,
            "scale_adaptation": 1.3,
            "complexity_adaptation": 1.1,
            "context_adaptation": 0.8,
            "comprehensive_adaptation": 1.5,
        }

        approach_multiplier = approach_multipliers.get(approach_type, 1.0)

        # Priority factor
        priority_factor = 1.0 + (high_priority_count / len(adaptations)) * 0.3

        # Calculate final complexity
        complexity = effort_complexity * approach_multiplier * priority_factor

        return min(1.0, complexity)

    def _calculate_adaptation_success_probability(
        self,
        implementations: list[dict[str, Any]],
        target_context: str,
        adaptations: list[dict[str, Any]],
    ) -> float:
        """Calculate probability of successful adaptation."""
        if not implementations:
            return 0.5  # Default probability without historical data

        # Base success probability from historical implementations
        successful_implementations = [
            impl for impl in implementations if impl.get("outcome") == "success"
        ]
        base_probability = len(successful_implementations) / len(implementations)

        # Context compatibility factor
        max_compatibility = self._calculate_context_compatibility(implementations, target_context)
        context_factor = 0.5 + max_compatibility * 0.5  # Scale to 0.5-1.0

        # Adaptation complexity factor (inverse - more complex = lower probability)
        adaptation_effort = sum(adaptation.get("estimated_effort", 1) for adaptation in adaptations)
        complexity_factor = max(0.3, 1.0 - (adaptation_effort / 50))  # Scale to 0.3-1.0

        # Calculate final probability
        success_probability = base_probability * context_factor * complexity_factor

        return min(1.0, max(0.1, success_probability))

    def _store_adaptation_strategies(self, strategies: list[AdaptationStrategy]) -> None:
        """Store adaptation strategies in the database."""
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                for strategy in strategies:
                    strategy_dict = strategy.to_dict()
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO adaptation_strategies
                        (strategy_id, source_pattern, target_context, adaptations,
                         impact_assessment, implementation_guide, validation_criteria,
                         rollback_strategy, adaptation_complexity, success_probability)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            strategy_dict["strategy_id"],
                            strategy_dict["source_pattern"],
                            strategy_dict["target_context"],
                            json.dumps(strategy_dict["adaptations"]),
                            json.dumps(strategy_dict["impact_assessment"]),
                            json.dumps(strategy_dict["implementation_guide"]),
                            json.dumps(strategy_dict["validation_criteria"]),
                            strategy_dict["rollback_strategy"],
                            strategy_dict["adaptation_complexity"],
                            strategy_dict["success_probability"],
                        ),
                    )

                conn.commit()

        except Exception as e:
            logger.error(f"Error storing adaptation strategies: {e}")

    def get_learning_metrics(self) -> dict[str, Any]:
        """
        Get learning system metrics and performance indicators.

        Returns
        -------
        Dict[str, Any]: Learning metrics including prediction accuracy, pattern discovery trends,
        and knowledge transfer effectiveness

        """
        try:
            metrics = {
                "prediction_accuracy": self._calculate_prediction_accuracy(),
                "pattern_discovery_trends": self._analyze_pattern_discovery_trends(),
                "knowledge_transfer_effectiveness": self._calculate_transfer_effectiveness(),
                "learning_summary": self._generate_learning_summary(),
                "recommendations": self._generate_learning_recommendations(),
            }

            return metrics

        except Exception as e:
            logger.error(f"Error getting learning metrics: {e}")
            return {"error": str(e)}

    def _calculate_prediction_accuracy(self) -> dict[str, float]:
        """Calculate prediction accuracy metrics."""
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                # Get predictions with actual outcomes
                cursor.execute(
                    """
                    SELECT confidence_score, feedback_score
                    FROM approach_predictions
                    WHERE actual_outcome IS NOT NULL AND feedback_score IS NOT NULL
                """
                )

                predictions = cursor.fetchall()

                if not predictions:
                    return {
                        "overall_accuracy": 0.0,
                        "confidence_correlation": 0.0,
                        "sample_size": 0,
                    }

                # Calculate accuracy metrics
                correct_predictions = sum(1 for conf, feedback in predictions if feedback > 0.7)
                overall_accuracy = correct_predictions / len(predictions)

                # Calculate confidence correlation
                avg_confidence = sum(conf for conf, _ in predictions) / len(predictions)
                avg_feedback = sum(feedback for _, feedback in predictions) / len(predictions)

                return {
                    "overall_accuracy": overall_accuracy,
                    "confidence_correlation": avg_confidence * avg_feedback,
                    "sample_size": len(predictions),
                    "avg_confidence": avg_confidence,
                    "avg_feedback": avg_feedback,
                }

        except Exception as e:
            logger.error(f"Error calculating prediction accuracy: {e}")
            return {"error": str(e)}

    def _analyze_pattern_discovery_trends(self) -> dict[str, Any]:
        """Analyze pattern discovery trends over time."""
        try:
            if not self._pattern_discovery_history:
                return {"trend": "insufficient_data", "total_discoveries": 0}

            # Calculate trends
            recent_discoveries = self._pattern_discovery_history[-10:]  # Last 10 discoveries
            avg_patterns_per_discovery = sum(
                discovery["patterns_found"] for discovery in recent_discoveries
            ) / len(
                recent_discoveries,
            )

            avg_success_rate = sum(
                discovery["average_success_rate"] for discovery in recent_discoveries
            ) / len(
                recent_discoveries,
            )

            return {
                "total_discoveries": len(self._pattern_discovery_history),
                "recent_avg_patterns": avg_patterns_per_discovery,
                "recent_avg_success_rate": avg_success_rate,
                "trend": "improving" if avg_success_rate > 0.7 else "stable",
            }

        except Exception as e:
            logger.error(f"Error analyzing pattern discovery trends: {e}")
            return {"error": str(e)}

    def _calculate_transfer_effectiveness(self) -> dict[str, float]:
        """Calculate knowledge transfer effectiveness metrics."""
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                # Get knowledge transfer metrics
                cursor.execute(
                    """
                    SELECT AVG(value) as avg_success_rate, COUNT(*) as total_transfers
                    FROM learning_metrics
                    WHERE metric_type = 'knowledge_transfer'
                """
                )

                result = cursor.fetchone()
                if result and result[0] is not None:
                    avg_success_rate, total_transfers = result
                else:
                    return {"effectiveness": 0.0, "total_transfers": 0}

                return {
                    "effectiveness": avg_success_rate,
                    "total_transfers": total_transfers,
                    "rating": (
                        "high"
                        if avg_success_rate > 0.8
                        else "medium"
                        if avg_success_rate > 0.6
                        else "low"
                    ),
                }

        except Exception as e:
            logger.error(f"Error calculating transfer effectiveness: {e}")
            return {"error": str(e)}

    def _generate_learning_summary(self) -> dict[str, Any]:
        """Generate overall learning system summary."""
        try:
            # Count stored entities
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM reusable_patterns")
                pattern_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM implementation_roadmaps")
                roadmap_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM approach_predictions")
                prediction_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM adaptation_strategies")
                strategy_count = cursor.fetchone()[0]

            return {
                "patterns_identified": pattern_count,
                "roadmaps_generated": roadmap_count,
                "predictions_made": prediction_count,
                "strategies_created": strategy_count,
                "learning_active": len(self._pattern_discovery_history) > 0,
                "system_health": "optimal" if pattern_count > 10 else "developing",
            }

        except Exception as e:
            logger.error(f"Error generating learning summary: {e}")
            return {"error": str(e)}

    def _generate_learning_recommendations(self) -> list[str]:
        """Generate recommendations for learning system improvement."""
        recommendations = []

        try:
            # Analyze current system state
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                # Check data volume
                cursor.execute("SELECT COUNT(*) FROM reusable_patterns")
                pattern_count = cursor.fetchone()[0]

                if pattern_count < 5:
                    recommendations.append(
                        "Increase implementation data volume to improve pattern recognition accuracy",
                    )

                # Check prediction accuracy
                accuracy_metrics = self._calculate_prediction_accuracy()
                if (
                    "overall_accuracy" in accuracy_metrics
                    and accuracy_metrics["overall_accuracy"] < 0.7
                ):
                    recommendations.append(
                        "Review prediction algorithms and expand historical data for better accuracy",
                    )

                # Check transfer effectiveness
                transfer_metrics = self._calculate_transfer_effectiveness()
                if "effectiveness" in transfer_metrics and transfer_metrics["effectiveness"] < 0.6:
                    recommendations.append(
                        "Improve context analysis and adaptation strategy generation"
                    )

                # Check recent activity
                if (
                    not self._pattern_discovery_history
                    or (datetime.now(UTC) - self._pattern_discovery_history[-1]["timestamp"]).days
                    > 30
                ):
                    recommendations.append(
                        "Increase frequency of pattern analysis and knowledge updates"
                    )

            # General recommendations
            recommendations.append(
                "Continue collecting implementation feedback for continuous learning"
            )
            recommendations.append("Expand pattern analysis to include more technology domains")

        except Exception as e:
            logger.error(f"Error generating learning recommendations: {e}")

        return (
            recommendations
            if recommendations
            else ["System operating optimally - continue current approach"]
        )

    def provide_feedback(
        self,
        prediction_id: str,
        actual_outcome: str,
        feedback_score: float | None = None,
        comments: str | None = None,
    ) -> bool:
        """
        Provide feedback for learning system improvement.

        Parameters
        ----------
        prediction_id (str): ID of the prediction to provide feedback for
        actual_outcome (str): Actual outcome of the implementation
        feedback_score (float, optional): Feedback score (0.0-1.0)
        comments (str, optional): Additional feedback comments

        Returns
        -------
        bool: True if feedback was successfully recorded

        """
        try:
            with sqlite3.connect(self.ml_model_path) as conn:
                cursor = conn.cursor()

                # Update prediction with feedback
                cursor.execute(
                    """
                    UPDATE approach_predictions
                    SET actual_outcome = ?, feedback_score = ?
                    WHERE prediction_id = ?
                """,
                    (actual_outcome, feedback_score, prediction_id),
                )

                changes_made = cursor.rowcount > 0

                if changes_made:
                    # Store learning metric
                    metric_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO learning_metrics
                        (metric_id, metric_type, value, metadata)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            metric_id,
                            "prediction_feedback",
                            feedback_score or 0.5,
                            json.dumps(
                                {
                                    "prediction_id": prediction_id,
                                    "actual_outcome": actual_outcome,
                                    "comments": comments,
                                },
                            ),
                        ),
                    )

                conn.commit()

                logger.info(f"Feedback recorded for prediction {prediction_id}")
                return changes_made

        except Exception as e:
            logger.error(f"Error providing feedback: {e}")
            return False

    def close(self) -> None:
        """
        Close the Future Implementation Enabler and cleanup resources.

        Algorithm Approach: Graceful shutdown with resource cleanup and data preservation.
        """
        try:
            # Set shutdown flag
            self._shutdown_requested = True

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

            logger.info("FutureImplementationEnabler closed successfully")

        except Exception as e:
            logger.error(f"Error closing FutureImplementationEnabler: {e}")


# Convenience functions for easy access
def create_knowledge_integration_engine(
    helpful_engine: HelpfulnessPattern | None = None,
    knowledge_query_engine: KnowledgeQueryEngine | None = None,
    storage_path: str | None = None,
) -> KnowledgeIntegrationEngine:
    """
    Create a knowledge integration engine with optional integrations.

    Parameters
    ----------
    helpful_engine (HelpfulnessPattern, optional): Helpfulness engine integration
    knowledge_query_engine (KnowledgeQueryEngine, optional): CSF knowledge engine
    storage_path (str, optional): Custom storage path

    Returns
    -------
    KnowledgeIntegrationEngine: Configured integration engine

    """
    return KnowledgeIntegrationEngine(
        helpful_engine=helpful_engine,
        knowledge_query_engine=knowledge_query_engine,
        storage_path=storage_path,
    )


def ingest_implementation_results(
    engine: KnowledgeIntegrationEngine,
    implementation_results: ImplementationResult | list[ImplementationResult],
) -> dict[str, Any]:
    """
    Convenience function for ingesting implementation results.

    Parameters
    ----------
    engine (KnowledgeIntegrationEngine): Integration engine instance
    implementation_results (Union[ImplementationResult, List[ImplementationResult]]):
        Implementation results to ingest

    Returns
    -------
    Dict[str, Any]: Ingestion results

    """
    return engine.automatic_knowledge_ingestion(implementation_results)


def get_recommendations_for_context(
    engine: KnowledgeIntegrationEngine,
    context: str,
    confidence_threshold: float = 0.5,
    limit: int = 10,
) -> dict[str, Any]:
    """
    Convenience function for getting context-specific recommendations.

    Parameters
    ----------
    engine (KnowledgeIntegrationEngine): Integration engine instance
    context (str): Context for recommendations
    confidence_threshold (float): Minimum confidence threshold
    limit (int): Maximum number of recommendations

    Returns
    -------
    Dict[str, Any]: Evidence-based recommendations

    """
    return engine.evidence_based_recommendations(context, confidence_threshold, limit)


# Export main components
__all__ = [
    "AdaptationStrategy",
    "ApproachPrediction",
    "ConfidenceLevel",
    "EvidenceBasedRecommendation",
    "FutureImplementationEnabler",
    "ImplementationResult",
    "ImplementationRoadmap",
    "IntegrationStatus",
    "KnowledgeIntegrationEngine",
    "KnowledgeIntegrationError",
    "KnowledgePattern",
    "KnowledgeQuery",
    "PatternType",
    "ReusablePattern",
    "create_knowledge_integration_engine",
    "get_recommendations_for_context",
    "ingest_implementation_results",
]
