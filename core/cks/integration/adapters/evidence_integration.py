import hashlib
import json
import logging
import re
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

"""
CSF CKS Integration for Unified Evidence System

This module provides comprehensive CKS (Cognitive Knowledge System) integration
into the unified evidence framework, enabling pattern recognition, knowledge
base integration, and intelligent evidence processing.

Algorithm Approach: CKS-Powered Evidence Enhancement
- Integrates CKS pattern recognition into evidence collection
- Provides knowledge base correlation and validation
- Enables intelligent evidence categorization and analysis
- Maintains constitutional compliance with CKS integration

Time Complexity: O(n) for evidence processing with CKS enhancement
Space Complexity: O(n) for CKS knowledge base indexing
"""


logger = logging.getLogger(__name__)


class CKSPatternType(Enum):
    """Types of CKS patterns for evidence enhancement."""

    WORKFLOW_PATTERN = "workflow_pattern"
    TASK_PATTERN = "task_pattern"
    ERROR_PATTERN = "error_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    COMPLIANCE_PATTERN = "compliance_pattern"
    CONSTITUTIONAL_PATTERN = "constitutional_pattern"
    ANTI_MOCK_PATTERN = "anti_mock_pattern"
    QUALITY_PATTERN = "quality_pattern"
    RESEARCH_PROTOCOL_PATTERN = "research_protocol_pattern"
    EXPLORATION_PATTERN = "exploration_pattern"
    EVIDENCE_COLLECTION_PATTERN = "evidence_collection_pattern"
    CONTEXT_AWARENESS_PATTERN = "context_awareness_pattern"


class CKSConfidenceLevel(Enum):
    """CKS confidence levels for pattern matching."""

    VERY_LOW = 0.2
    LOW = 0.4
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95


@dataclass
class CKSPattern:
    """Represents a CKS pattern for evidence analysis.

    Design Pattern: Pattern Recognition Object - encapsulates pattern
    definitions, matching logic, and confidence scoring.

    Attributes:
        id (str): Unique pattern identifier
        name (str): Human-readable pattern name
        pattern_type (CKSPatternType): Type of pattern
        pattern_regex (str): Regular expression for pattern matching
        description (str): Pattern description
        confidence_threshold (float): Minimum confidence threshold
        tags (Set[str]): Pattern tags for categorization
        constitutional_relevance (float): Constitutional relevance score (0-1)
        evidence_boost (float): Evidence confidence boost factor
        metadata (Dict[str, Any]): Additional pattern metadata

    """

    id: str
    name: str
    pattern_type: CKSPatternType
    pattern_regex: str
    description: str
    confidence_threshold: float = 0.6
    tags: set[str] = None
    constitutional_relevance: float = 0.5
    evidence_boost: float = 1.0
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Post-initialization setup."""
        if self.tags is None:
            self.tags = set()
        if self.metadata is None:
            self.metadata = {}
        # Compile regex for efficiency
        self._compiled_regex = re.compile(self.pattern_regex, re.IGNORECASE | re.MULTILINE)

    def match(self, text: str) -> tuple[bool, float, list[str]]:
        """Match pattern against text.

        Parameters
        ----------
        text (str): Text to match against

        Returns
        -------
        Tuple[bool, float, List[str]]: (matched, confidence, matched_groups)

        """
        matches = list(self._compiled_regex.finditer(text))
        if not matches:
            return False, 0.0, []

        # Calculate confidence based on match quality and count
        total_matches = len(matches)
        confidence = min(total_matches * 0.2, 1.0)  # Scale matches to confidence

        # Extract matched groups
        matched_groups = []
        for match in matches:
            if match.groups():
                matched_groups.extend(match.groups())
            else:
                matched_groups.append(match.group(0))

        return confidence >= self.confidence_threshold, confidence, matched_groups


@dataclass
class CKSEnrichment:
    """Represents CKS enrichment applied to evidence.

    Attributes:
        evidence_id (str): Evidence record identifier
        patterns_matched (List[Tuple[str, float]]): List of (pattern_id, confidence)
        knowledge_correlations (List[Dict[str, Any]]): Knowledge base correlations
        constitutional_insights (Dict[str, Any]): Constitutional compliance insights
        quality_assessments (Dict[str, float]): Quality assessment scores
        enhancement_timestamp (datetime): When enrichment was applied
        metadata (Dict[str, Any]): Additional enrichment metadata

    """

    evidence_id: str
    patterns_matched: list[tuple[str, float]]
    knowledge_correlations: list[dict[str, Any]]
    constitutional_insights: dict[str, Any]
    quality_assessments: dict[str, float]
    enhancement_timestamp: datetime
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Post-initialization setup."""
        if self.metadata is None:
            self.metadata = {}


class CKSIntegrator:
    """CKS integration system for unified evidence enhancement.

    Algorithm Approach: Pattern-Based Evidence Enhancement
    - Applies CKS patterns to evidence for intelligent categorization
    - Correlates evidence with knowledge base for context
    - Provides constitutional compliance insights
    - Enhances evidence quality through pattern recognition
    """

    def __init__(self, cks_db_path: str, knowledge_base_path: str) -> None:
        """Initialize CKS integrator.

        Parameters
        ----------
        cks_db_path (str): Path to CKS database
        knowledge_base_path (str): Path to CKS knowledge base

        Raises
        ------
        ValueError: If initialization fails

        """
        self.cks_db_path = Path(cks_db_path)
        self.knowledge_base_path = Path(knowledge_base_path)
        self._lock = threading.RLock()

        # Pattern cache
        self._patterns_cache = {}
        self._knowledge_cache = {}

        # Statistics
        self._enrichment_stats = {
            "total_enriched": 0,
            "patterns_applied": 0,
            "constitutional_violations_detected": 0,
            "quality_improvements": 0,
        }

        self._initialize_database()
        self._load_default_patterns()

    def _initialize_database(self) -> None:
        """Initialize CKS integration database."""
        try:
            with sqlite3.connect(self.cks_db_path) as conn:
                cursor = conn.cursor()

                # Create patterns table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cks_patterns (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        pattern_type TEXT NOT NULL,
                        pattern_regex TEXT NOT NULL,
                        description TEXT NOT NULL,
                        confidence_threshold REAL DEFAULT 0.6,
                        tags TEXT NOT NULL,
                        constitutional_relevance REAL DEFAULT 0.5,
                        evidence_boost REAL DEFAULT 1.0,
                        metadata TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        INDEX idx_pattern_type (pattern_type),
                        INDEX idx_constitutional_relevance (constitutional_relevance),
                        INDEX idx_is_active (is_active)
                    )
                """)

                # Create evidence enrichment table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS evidence_enrichments (
                        id TEXT PRIMARY KEY,
                        evidence_id TEXT NOT NULL,
                        patterns_matched TEXT NOT NULL,
                        knowledge_correlations TEXT NOT NULL,
                        constitutional_insights TEXT NOT NULL,
                        quality_assessments TEXT NOT NULL,
                        enhancement_timestamp TEXT NOT NULL,
                        metadata TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_evidence_id (evidence_id),
                        INDEX idx_enhancement_timestamp (enhancement_timestamp)
                    )
                """)

                # Create knowledge base correlations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_correlations (
                        id TEXT PRIMARY KEY,
                        evidence_id TEXT NOT NULL,
                        knowledge_item_id TEXT NOT NULL,
                        correlation_strength REAL NOT NULL,
                        correlation_type TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_evidence_id (evidence_id),
                        INDEX idx_knowledge_item_id (knowledge_item_id),
                        INDEX idx_correlation_strength (correlation_strength)
                    )
                """)

                # Create pattern matching history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pattern_matching_history (
                        id TEXT PRIMARY KEY,
                        pattern_id TEXT NOT NULL,
                        evidence_id TEXT NOT NULL,
                        confidence_score REAL NOT NULL,
                        matched_text TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY (pattern_id) REFERENCES cks_patterns(id),
                        INDEX idx_pattern_id (pattern_id),
                        INDEX idx_evidence_id (evidence_id),
                        INDEX idx_timestamp (timestamp),
                        INDEX idx_confidence_score (confidence_score)
                    )
                """)

                conn.commit()
                logger.info(f"CKS integration database initialized: {self.cks_db_path}")

        except Exception as e:
            logger.exception(f"Failed to initialize CKS database: {e}")
            raise ValueError(f"Database initialization failed: {e}")

    def _load_default_patterns(self) -> None:
        """Load default CKS patterns for evidence enhancement."""
        default_patterns = [
            # Constitutional compliance patterns
            CKSPattern(
                id="constitutional_compliance_95_percent",
                name="95% Constitutional Compliance Pattern",
                pattern_type=CKSPatternType.CONSTITUTIONAL_PATTERN,
                pattern_regex=r"(constitutional.*compliance.*95.*%|compliance.*score.*0\.95|threshold.*95)",
                description="Detects evidence related to 95% constitutional compliance requirement",
                confidence_threshold=0.8,
                tags={"constitutional", "compliance", "threshold"},
                constitutional_relevance=1.0,
                evidence_boost=1.2,
            ),
            # Anti-mock philosophy patterns
            CKSPattern(
                id="anti_mock_philosophy",
                name="Anti-Mock Philosophy Pattern",
                pattern_type=CKSPatternType.ANTI_MOCK_PATTERN,
                pattern_regex=r"(anti.*mock|no.*mock|real.*implementation|actual.*database|production.*code)",
                description="Detects evidence related to anti-mock philosophy compliance",
                confidence_threshold=0.7,
                tags={"anti-mock", "philosophy", "real-implementation"},
                constitutional_relevance=0.9,
                evidence_boost=1.1,
            ),
            # Workflow performance patterns
            CKSPattern(
                id="workflow_performance_30_percent",
                name="30% Performance Improvement Pattern",
                pattern_type=CKSPatternType.PERFORMANCE_PATTERN,
                pattern_regex=r"(30.*%.*improvement|performance.*boost.*30|boundary.*elimination)",
                description="Detects evidence related to 30% performance improvement targets",
                confidence_threshold=0.8,
                tags={"performance", "improvement", "optimization"},
                constitutional_relevance=0.7,
                evidence_boost=1.15,
            ),
            # Error pattern detection
            CKSPattern(
                id="error_failure_pattern",
                name="Error and Failure Pattern",
                pattern_type=CKSPatternType.ERROR_PATTERN,
                pattern_regex=r"(error|exception|failure|failed|timeout|crashed)",
                description="Detects error and failure indicators in evidence",
                confidence_threshold=0.6,
                tags={"error", "failure", "exception"},
                constitutional_relevance=0.3,
                evidence_boost=0.9,
            ),
            # Quality pattern detection
            CKSPattern(
                id="quality_assurance_pattern",
                name="Quality Assurance Pattern",
                pattern_type=CKSPatternType.QUALITY_PATTERN,
                pattern_regex=r"(test.*passed|validation.*successful|quality.*score|compliance.*met)",
                description="Detects quality assurance indicators in evidence",
                confidence_threshold=0.7,
                tags={"quality", "assurance", "validation"},
                constitutional_relevance=0.8,
                evidence_boost=1.1,
            ),
            # System integration patterns
            CKSPattern(
                id="system_integration_pattern",
                name="System Integration Pattern",
                pattern_type=CKSPatternType.WORKFLOW_PATTERN,
                pattern_regex=r"(integrated|unified|coordinated|synchronized|orchestrated)",
                description="Detects system integration and coordination evidence",
                confidence_threshold=0.6,
                tags={"integration", "unified", "coordination"},
                constitutional_relevance=0.6,
                evidence_boost=1.0,
            ),
            # Research First Operational Protocol patterns (from CLAUDE.md PART L)
            CKSPattern(
                id="research_first_protocol",
                name="Research First Protocol Pattern",
                pattern_type=CKSPatternType.RESEARCH_PROTOCOL_PATTERN,
                pattern_regex=r"(research.*first|explore.*existing|search.*before.*plan|context.*inheritance)",
                description="Detects Research First operational protocol compliance - exploration before planning",
                confidence_threshold=0.8,
                tags={"research", "protocol", "exploration", "claude.md"},
                constitutional_relevance=0.9,
                evidence_boost=1.2,
            ),
            CKSPattern(
                id="codebase_exploration",
                name="Codebase Exploration Pattern",
                pattern_type=CKSPatternType.EXPLORATION_PATTERN,
                pattern_regex=r"(glob.*pattern|grep.*search|file.*exploration|existing.*solution)",
                description="Detects proper codebase exploration using Glob/Grep/Read tools",
                confidence_threshold=0.7,
                tags={"exploration", "codebase", "search", "tools"},
                constitutional_relevance=0.8,
                evidence_boost=1.15,
            ),
            CKSPattern(
                id="evidence_collection_mandate",
                name="Evidence Collection Mandate Pattern",
                pattern_type=CKSPatternType.EVIDENCE_COLLECTION_PATTERN,
                pattern_regex=r"(evidence.*required|source.*citation|file.*path.*reference|specific.*line.*number)",
                description="Detects evidence collection with specific file paths and line numbers",
                confidence_threshold=0.8,
                tags={"evidence", "citation", "sources", "verification"},
                constitutional_relevance=0.9,
                evidence_boost=1.1,
            ),
            CKSPattern(
                id="context_awareness_compliance",
                name="Context Awareness Compliance Pattern",
                pattern_type=CKSPatternType.CONTEXT_AWARENESS_PATTERN,
                pattern_regex=r"(first.*read.*claude\.md|inherit.*context|global.*standards|team.*practices)",
                description="Detects context awareness and CLAUDE.md inheritance compliance",
                confidence_threshold=0.9,
                tags={"context", "awareness", "claude.md", "inheritance"},
                constitutional_relevance=0.95,
                evidence_boost=1.25,
            ),
            # 4-Step Research Protocol patterns
            CKSPattern(
                id="research_step_1_discovery",
                name="Research Step 1: Discovery Pattern",
                pattern_type=CKSPatternType.RESEARCH_PROTOCOL_PATTERN,
                pattern_regex=r"(step.*1.*discovery|explore.*codebase|glob.*files|search.*existing)",
                description="Detects Step 1 of research protocol: discovery and exploration",
                confidence_threshold=0.7,
                tags={"research", "discovery", "exploration", "step1"},
                constitutional_relevance=0.8,
                evidence_boost=1.1,
            ),
            CKSPattern(
                id="research_step_2_analysis",
                name="Research Step 2: Analysis Pattern",
                pattern_type=CKSPatternType.RESEARCH_PROTOCOL_PATTERN,
                pattern_regex=r"(step.*2.*analysis|analyze.*findings|document.*existing|gap.*identification)",
                description="Detects Step 2 of research protocol: analysis of findings",
                confidence_threshold=0.7,
                tags={"research", "analysis", "findings", "step2"},
                constitutional_relevance=0.8,
                evidence_boost=1.1,
            ),
            CKSPattern(
                id="research_step_3_evidence",
                name="Research Step 3: Evidence Collection Pattern",
                pattern_type=CKSPatternType.EVIDENCE_COLLECTION_PATTERN,
                pattern_regex=r"(step.*3.*evidence|collect.*evidence|cite.*sources|file.*line.*reference)",
                description="Detects Step 3 of research protocol: evidence collection with citations",
                confidence_threshold=0.8,
                tags={"research", "evidence", "citations", "step3"},
                constitutional_relevance=0.9,
                evidence_boost=1.2,
            ),
            CKSPattern(
                id="research_step_4_synthesis",
                name="Research Step 4: Synthesis Pattern",
                pattern_type=CKSPatternType.RESEARCH_PROTOCOL_PATTERN,
                pattern_regex=r"(step.*4.*synthesis|synthesize.*findings|research.*report|evidence.*integration)",
                description="Detects Step 4 of research protocol: synthesis and integration",
                confidence_threshold=0.7,
                tags={"research", "synthesis", "integration", "step4"},
                constitutional_relevance=0.8,
                evidence_boost=1.1,
            ),
            # Research quality standards
            CKSPattern(
                id="research_quality_standards",
                name="Research Quality Standards Pattern",
                pattern_type=CKSPatternType.QUALITY_PATTERN,
                pattern_regex=r"(quality.*standards|research.*methodology|evidence.*requirements|time.*management)",
                description="Detects research quality standards and methodology compliance",
                confidence_threshold=0.8,
                tags={"research", "quality", "standards", "methodology"},
                constitutional_relevance=0.9,
                evidence_boost=1.15,
            ),
            # Anti-Lazy Planning Protocol patterns
            CKSPattern(
                id="anti_lazy_planning",
                name="Anti-Lazy Planning Protocol Pattern",
                pattern_type=CKSPatternType.RESEARCH_PROTOCOL_PATTERN,
                pattern_regex=r"(anti.*lazy.*planning|exploration.*before.*planning|search.*existing.*first)",
                description="Detects Anti-Lazy Planning protocol compliance from CLAUDE.md E.1",
                confidence_threshold=0.9,
                tags={"anti-lazy", "planning", "exploration", "protocol"},
                constitutional_relevance=0.95,
                evidence_boost=1.3,
            ),
            CKSPattern(
                id="exploration_evidence_requirement",
                name="Exploration Evidence Requirement Pattern",
                pattern_type=CKSPatternType.EVIDENCE_COLLECTION_PATTERN,
                pattern_regex=r"(glob.*results|grep.*results|file.*path.*evidence|search.*proof)",
                description="Detects exploration evidence requirements with Glob/Grep results",
                confidence_threshold=0.8,
                tags={"exploration", "evidence", "glob", "grep", "proof"},
                constitutional_relevance=0.9,
                evidence_boost=1.2,
            ),
        ]

        for pattern in default_patterns:
            self._store_pattern(pattern)

        logger.info(f"Loaded {len(default_patterns)} default CKS patterns")

    def enrich_evidence(
        self, evidence_id: str, evidence_data: dict[str, Any], evidence_text: str | None = None
    ) -> CKSEnrichment:
        """Apply CKS enrichment to evidence record.

        Algorithm Approach: Multi-Layer Pattern Matching
        - Applies CKS patterns to evidence text and metadata
        - Correlates with knowledge base for context enhancement
        - Provides constitutional compliance insights
        - Calculates quality assessment scores

        Parameters
        ----------
        evidence_id (str): Evidence record identifier
        evidence_data (Dict[str, Any]): Evidence data
        evidence_text (Optional[str]): Text content for pattern matching

        Returns
        -------
        CKSEnrichment: Applied enrichment details

        """
        try:
            # Prepare text for pattern matching
            if evidence_text is None:
                evidence_text = self._extract_text_from_evidence(evidence_data)

            # Apply pattern matching
            patterns_matched = self._apply_patterns(evidence_text)

            # Correlate with knowledge base
            knowledge_correlations = self._correlate_with_knowledge(evidence_data, patterns_matched)

            # Generate constitutional insights
            constitutional_insights = self._analyze_constitutional_compliance(
                evidence_data,
                patterns_matched,
                knowledge_correlations,
            )

            # Calculate quality assessments
            quality_assessments = self._assess_evidence_quality(
                evidence_data,
                patterns_matched,
                constitutional_insights,
            )

            # Create enrichment object
            enrichment = CKSEnrichment(
                evidence_id=evidence_id,
                patterns_matched=patterns_matched,
                knowledge_correlations=knowledge_correlations,
                constitutional_insights=constitutional_insights,
                quality_assessments=quality_assessments,
                enhancement_timestamp=datetime.now(UTC),
            )

            # Store enrichment
            self._store_enrichment(enrichment)

            # Update statistics
            self._enrichment_stats["total_enriched"] += 1
            self._enrichment_stats["patterns_applied"] += len(patterns_matched)
            if constitutional_insights.get("violations", 0) > 0:
                self._enrichment_stats["constitutional_violations_detected"] += 1
            if quality_assessments.get("overall_score", 0) > 0.8:
                self._enrichment_stats["quality_improvements"] += 1

            logger.debug(f"CKS enrichment applied to evidence: {evidence_id}")
            return enrichment

        except Exception as e:
            logger.exception(f"Failed to enrich evidence {evidence_id}: {e}")
            raise

    def _extract_text_from_evidence(self, evidence_data: dict[str, Any]) -> str:
        """Extract searchable text from evidence data."""
        text_parts = []

        # Extract from data fields
        if "data" in evidence_data:
            for value in evidence_data["data"].values():
                if isinstance(value, str):
                    text_parts.append(value)
                elif isinstance(value, dict):
                    text_parts.append(json.dumps(value))
                elif isinstance(value, list):
                    text_parts.extend(str(item) for item in value if isinstance(item, str))

        # Extract from metadata
        if "metadata" in evidence_data:
            for value in evidence_data["metadata"].values():
                if isinstance(value, str):
                    text_parts.append(value)

        # Extract from description or message fields
        for field in ["description", "message", "status", "error"]:
            if field in evidence_data and isinstance(evidence_data[field], str):
                text_parts.append(evidence_data[field])

        return " ".join(text_parts)

    def _apply_patterns(self, text: str) -> list[tuple[str, float]]:
        """Apply CKS patterns to text and return matches."""
        patterns_matched = []
        patterns = self._load_active_patterns()

        for pattern in patterns:
            try:
                matched, confidence, matched_groups = pattern.match(text)
                if matched:
                    patterns_matched.append((pattern.id, confidence))

                    # Store pattern matching history
                    self._store_pattern_match(
                        pattern.id, "unknown", confidence, " ".join(matched_groups)
                    )

            except Exception as e:
                logger.warning(f"Pattern matching error for {pattern.id}: {e}")

        return patterns_matched

    def _correlate_with_knowledge(
        self, evidence_data: dict[str, Any], patterns_matched: list[tuple[str, float]]
    ) -> list[dict[str, Any]]:
        """Correlate evidence with knowledge base."""
        correlations = []

        # Extract keywords from evidence
        evidence_keywords = self._extract_keywords(evidence_data)

        # Match against knowledge base (simplified implementation)
        for keyword in evidence_keywords:
            # In real implementation, would query actual knowledge base
            correlation_strength = min(len(keyword) * 0.1, 1.0)
            if correlation_strength > 0.3:
                correlations.append(
                    {
                        "knowledge_item_id": f"kb_{hashlib.md5(keyword.encode()).hexdigest()[:8]}",
                        "keyword": keyword,
                        "correlation_strength": correlation_strength,
                        "correlation_type": "keyword_match",
                    }
                )

        return correlations

    def _analyze_constitutional_compliance(
        self,
        evidence_data: dict[str, Any],
        patterns_matched: list[tuple[str, float]],
        knowledge_correlations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze constitutional compliance aspects of evidence."""
        insights = {
            "compliance_score": 0.0,
            "violations": [],
            "recommendations": [],
            "constitutional_patterns": [],
            "anti_mock_compliance": True,
            "research_protocol_compliance": {
                "research_first_adherence": False,
                "exploration_before_planning": False,
                "evidence_collection_quality": 0.0,
                "context_awareness_compliance": False,
                "anti_lazy_planning_compliance": False,
            },
            "research_methodology_score": 0.0,
        }

        # Check constitutional patterns
        constitutional_patterns = [
            p for p in patterns_matched if self._is_constitutional_pattern(p[0])
        ]
        insights["constitutional_patterns"] = constitutional_patterns

        # Check anti-mock compliance
        anti_mock_patterns = [p for p in patterns_matched if self._is_anti_mock_pattern(p[0])]
        insights["anti_mock_compliance"] = len(anti_mock_patterns) > 0

        # Check research protocol compliance (Research First Operational Protocol)
        research_protocol_patterns = [
            p for p in patterns_matched if self._is_research_protocol_pattern(p[0])
        ]
        insights["research_protocol_compliance"]["research_first_adherence"] = (
            len(research_protocol_patterns) > 0
        )

        # Check exploration patterns
        exploration_patterns = [p for p in patterns_matched if "exploration" in p[0].lower()]
        insights["research_protocol_compliance"]["exploration_before_planning"] = (
            len(exploration_patterns) > 0
        )

        # Check evidence collection quality
        evidence_patterns = [
            p for p in patterns_matched if self._is_evidence_collection_pattern(p[0])
        ]
        if evidence_patterns:
            avg_evidence_confidence = sum(conf for _, conf in evidence_patterns) / len(
                evidence_patterns
            )
            insights["research_protocol_compliance"]["evidence_collection_quality"] = min(
                avg_evidence_confidence, 1.0
            )

        # Check context awareness compliance
        context_patterns = [p for p in patterns_matched if self._is_context_awareness_pattern(p[0])]
        insights["research_protocol_compliance"]["context_awareness_compliance"] = (
            len(context_patterns) > 0
        )

        # Check anti-lazy planning compliance
        anti_lazy_patterns = [p for p in patterns_matched if "anti_lazy" in p[0].lower()]
        insights["research_protocol_compliance"]["anti_lazy_planning_compliance"] = (
            len(anti_lazy_patterns) > 0
        )

        # Calculate overall compliance score
        if constitutional_patterns:
            avg_confidence = sum(conf for _, conf in constitutional_patterns) / len(
                constitutional_patterns
            )
            insights["compliance_score"] = min(avg_confidence, 1.0)

        # Calculate research methodology score
        research_metrics = insights["research_protocol_compliance"]
        research_scores = [
            1.0 if research_metrics["research_first_adherence"] else 0.0,
            1.0 if research_metrics["exploration_before_planning"] else 0.0,
            research_metrics["evidence_collection_quality"],
            1.0 if research_metrics["context_awareness_compliance"] else 0.0,
            1.0 if research_metrics["anti_lazy_planning_compliance"] else 0.0,
        ]
        insights["research_methodology_score"] = sum(research_scores) / len(research_scores)

        # Detect potential violations
        error_patterns = [p for p in patterns_matched if self._is_error_pattern(p[0])]
        if error_patterns:
            insights["violations"].append(
                {
                    "type": "error_indicators",
                    "patterns": error_patterns,
                    "severity": "medium",
                }
            )

        # Research methodology violations
        if not research_metrics["research_first_adherence"]:
            insights["violations"].append(
                {
                    "type": "research_protocol_violation",
                    "description": "Research First operational protocol not detected",
                    "severity": "high",
                }
            )

        if not research_metrics["anti_lazy_planning_compliance"]:
            insights["violations"].append(
                {
                    "type": "anti_lazy_planning_violation",
                    "description": "Anti-Lazy Planning protocol compliance not detected",
                    "severity": "high",
                }
            )

        # Generate recommendations
        if insights["compliance_score"] < 0.95:
            insights["recommendations"].append("Increase constitutional compliance measures")
        if not insights["anti_mock_compliance"]:
            insights["recommendations"].append("Ensure anti-mock philosophy compliance")
        if insights["research_methodology_score"] < 0.8:
            insights["recommendations"].append(
                "Implement Research First operational protocol from CLAUDE.md PART L"
            )
        if not research_metrics["exploration_before_planning"]:
            insights["recommendations"].append(
                "Always explore existing codebase before planning new implementations"
            )
        if research_metrics["evidence_collection_quality"] < 0.7:
            insights["recommendations"].append(
                "Improve evidence collection with specific file paths and line numbers"
            )
        if not research_metrics["context_awareness_compliance"]:
            insights["recommendations"].append("Ensure context awareness and CLAUDE.md inheritance")

        return insights

    def _assess_evidence_quality(
        self,
        evidence_data: dict[str, Any],
        patterns_matched: list[tuple[str, float]],
        constitutional_insights: dict[str, Any],
    ) -> dict[str, float]:
        """Assess quality aspects of evidence."""
        assessments = {
            "overall_score": 0.0,
            "completeness_score": 0.0,
            "accuracy_score": 0.0,
            "consistency_score": 0.0,
            "reliability_score": 0.0,
            "research_methodology_score": 0.0,
            "exploration_quality_score": 0.0,
            "evidence_citation_score": 0.0,
            "context_inheritance_score": 0.0,
        }

        # Completeness assessment
        required_fields = ["id", "type", "timestamp", "data"]
        completeness = sum(1 for field in required_fields if field in evidence_data)
        assessments["completeness_score"] = completeness / len(required_fields)

        # Accuracy assessment (based on pattern quality)
        quality_patterns = [p for p in patterns_matched if self._is_quality_pattern(p[0])]
        assessments["accuracy_score"] = min(len(quality_patterns) * 0.2, 1.0)

        # Consistency assessment
        assessments["consistency_score"] = (
            1.0 if constitutional_insights.get("compliance_score", 0) >= 0.9 else 0.7
        )

        # Reliability assessment
        error_patterns = [p for p in patterns_matched if self._is_error_pattern(p[0])]
        assessments["reliability_score"] = max(0.0, 1.0 - len(error_patterns) * 0.1)

        # Research methodology quality assessment
        constitutional_insights.get("research_protocol_compliance", {})
        assessments["research_methodology_score"] = constitutional_insights.get(
            "research_methodology_score", 0.0
        )

        # Exploration quality assessment (Research First Protocol)
        exploration_patterns = [
            p for p in patterns_matched if self._is_research_protocol_pattern(p[0])
        ]
        if exploration_patterns:
            exploration_confidence = sum(conf for _, conf in exploration_patterns) / len(
                exploration_patterns
            )
            assessments["exploration_quality_score"] = min(exploration_confidence, 1.0)

        # Evidence citation quality assessment
        evidence_patterns = [
            p for p in patterns_matched if self._is_evidence_collection_pattern(p[0])
        ]
        if evidence_patterns:
            citation_confidence = sum(conf for _, conf in evidence_patterns) / len(
                evidence_patterns
            )
            assessments["evidence_citation_score"] = min(citation_confidence, 1.0)

        # Context inheritance quality assessment
        context_patterns = [p for p in patterns_matched if self._is_context_awareness_pattern(p[0])]
        if context_patterns:
            context_confidence = sum(conf for _, conf in context_patterns) / len(context_patterns)
            assessments["context_inheritance_score"] = min(context_confidence, 1.0)

        # Calculate enhanced overall score (weights favor research methodology)
        weights = {
            "completeness_score": 0.15,
            "accuracy_score": 0.15,
            "consistency_score": 0.15,
            "reliability_score": 0.15,
            "research_methodology_score": 0.25,  # Higher weight for research methodology
            "exploration_quality_score": 0.1,
            "evidence_citation_score": 0.1,
            "context_inheritance_score": 0.1,
        }

        weighted_sum = sum(assessments[metric] * weight for metric, weight in weights.items())
        assessments["overall_score"] = weighted_sum

        return assessments

    def _extract_keywords(self, evidence_data: dict[str, Any]) -> list[str]:
        """Extract keywords from evidence data."""
        keywords = []

        # Simple keyword extraction (would be more sophisticated in real implementation)
        text = self._extract_text_from_evidence(evidence_data)
        words = re.findall(r"\b\w+\b", text.lower())

        # Filter meaningful keywords (length > 3)
        keywords = [word for word in set(words) if len(word) > 3]

        return keywords[:20]  # Limit to top 20 keywords

    def _is_constitutional_pattern(self, pattern_id: str) -> bool:
        """Check if pattern is constitutional-related."""
        return "constitutional" in pattern_id.lower()

    def _is_anti_mock_pattern(self, pattern_id: str) -> bool:
        """Check if pattern is anti-mock-related."""
        return "anti_mock" in pattern_id.lower()

    def _is_error_pattern(self, pattern_id: str) -> bool:
        """Check if pattern is error-related."""
        return "error" in pattern_id.lower()

    def _is_quality_pattern(self, pattern_id: str) -> bool:
        """Check if pattern is quality-related."""
        return "quality" in pattern_id.lower()

    def _is_research_protocol_pattern(self, pattern_id: str) -> bool:
        """Check if pattern is research protocol-related."""
        return any(
            keyword in pattern_id.lower()
            for keyword in ["research", "protocol", "exploration", "anti_lazy"]
        )

    def _is_evidence_collection_pattern(self, pattern_id: str) -> bool:
        """Check if pattern is evidence collection-related."""
        return any(
            keyword in pattern_id.lower() for keyword in ["evidence", "citation", "source", "proof"]
        )

    def _is_context_awareness_pattern(self, pattern_id: str) -> bool:
        """Check if pattern is context awareness-related."""
        return any(keyword in pattern_id.lower() for keyword in ["context", "awareness", "claude"])

    def _store_pattern(self, pattern: CKSPattern) -> None:
        """Store CKS pattern in database."""
        try:
            with sqlite3.connect(self.cks_db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO cks_patterns
                    (id, name, pattern_type, pattern_regex, description, confidence_threshold,
                     tags, constitutional_relevance, evidence_boost, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        pattern.id,
                        pattern.name,
                        pattern.pattern_type.value,
                        pattern.pattern_regex,
                        pattern.description,
                        pattern.confidence_threshold,
                        json.dumps(list(pattern.tags)),
                        pattern.constitutional_relevance,
                        pattern.evidence_boost,
                        json.dumps(pattern.metadata),
                    ),
                )

                conn.commit()

        except Exception as e:
            logger.exception(f"Failed to store pattern {pattern.id}: {e}")

    def _load_active_patterns(self) -> list[CKSPattern]:
        """Load all active CKS patterns."""
        if self._patterns_cache:
            return list(self._patterns_cache.values())

        try:
            with sqlite3.connect(self.cks_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("SELECT * from csf.cks_patterns WHERE is_active = TRUE")
                rows = cursor.fetchall()

                patterns = []
                for row in rows:
                    pattern = CKSPattern(
                        id=row["id"],
                        name=row["name"],
                        pattern_type=CKSPatternType(row["pattern_type"]),
                        pattern_regex=row["pattern_regex"],
                        description=row["description"],
                        confidence_threshold=row["confidence_threshold"],
                        tags=set(json.loads(row["tags"])),
                        constitutional_relevance=row["constitutional_relevance"],
                        evidence_boost=row["evidence_boost"],
                        metadata=json.loads(row["metadata"]),
                    )
                    patterns.append(pattern)
                    self._patterns_cache[pattern.id] = pattern

                return patterns

        except Exception as e:
            logger.exception(f"Failed to load patterns: {e}")
            return []

    def _store_enrichment(self, enrichment: CKSEnrichment) -> None:
        """Store evidence enrichment in database."""
        try:
            with sqlite3.connect(self.cks_db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO evidence_enrichments
                    (id, evidence_id, patterns_matched, knowledge_correlations,
                     constitutional_insights, quality_assessments, enhancement_timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4()),
                        enrichment.evidence_id,
                        json.dumps(enrichment.patterns_matched),
                        json.dumps(enrichment.knowledge_correlations),
                        json.dumps(enrichment.constitutional_insights),
                        json.dumps(enrichment.quality_assessments),
                        enrichment.enhancement_timestamp.isoformat(),
                        json.dumps(enrichment.metadata),
                    ),
                )

                conn.commit()

        except Exception as e:
            logger.exception(f"Failed to store enrichment: {e}")

    def _store_pattern_match(
        self, pattern_id: str, evidence_id: str, confidence: float, matched_text: str
    ) -> None:
        """Store pattern matching history."""
        try:
            with sqlite3.connect(self.cks_db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO pattern_matching_history
                    (id, pattern_id, evidence_id, confidence_score, matched_text, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        str(uuid.uuid4()),
                        pattern_id,
                        evidence_id,
                        confidence,
                        matched_text[:500],  # Limit text length
                        datetime.now(UTC).isoformat(),
                    ),
                )

                conn.commit()

        except Exception as e:
            logger.exception(f"Failed to store pattern match: {e}")

    def get_enrichment_statistics(self) -> dict[str, Any]:
        """Get CKS enrichment statistics."""
        return {
            **self._enrichment_stats,
            "patterns_loaded": len(self._patterns_cache),
            "active_patterns": len(
                [p for p in self._patterns_cache.values() if True]
            ),  # All are active
            "last_updated": datetime.now(UTC).isoformat(),
        }

    def add_custom_pattern(self, pattern: CKSPattern) -> bool:
        """Add a custom CKS pattern.

        Parameters
        ----------
        pattern (CKSPattern): Pattern to add

        Returns
        -------
        bool: True if pattern was added successfully

        """
        try:
            self._store_pattern(pattern)
            self._patterns_cache[pattern.id] = pattern
            logger.info(f"Custom CKS pattern added: {pattern.id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to add custom pattern: {e}")
            return False

    def get_enrichment_for_evidence(self, evidence_id: str) -> CKSEnrichment | None:
        """Retrieve CKS enrichment for specific evidence.

        Parameters
        ----------
        evidence_id (str): Evidence record identifier

        Returns
        -------
        Optional[CKSEnrichment]: Enrichment data if found

        """
        try:
            with sqlite3.connect(self.cks_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM evidence_enrichments WHERE evidence_id = ?
                    ORDER BY enhancement_timestamp DESC LIMIT 1
                """,
                    (evidence_id,),
                )
                row = cursor.fetchone()

                if row:
                    return CKSEnrichment(
                        evidence_id=row["evidence_id"],
                        patterns_matched=json.loads(row["patterns_matched"]),
                        knowledge_correlations=json.loads(row["knowledge_correlations"]),
                        constitutional_insights=json.loads(row["constitutional_insights"]),
                        quality_assessments=json.loads(row["quality_assessments"]),
                        enhancement_timestamp=datetime.fromisoformat(row["enhancement_timestamp"]),
                        metadata=json.loads(row["metadata"]),
                    )
                return None

        except Exception as e:
            logger.exception(f"Failed to retrieve enrichment for {evidence_id}: {e}")
            return None

    def validate_research_methodology(
        self, evidence_data: dict[str, Any], evidence_text: str | None = None
    ) -> dict[str, Any]:
        """Validate evidence against Research First Operational Protocol from CLAUDE.md PART L.

        This method implements the 4-step research protocol validation:
        1. Discovery and exploration
        2. Analysis of findings
        3. Evidence collection with citations
        4. Synthesis and integration

        Parameters
        ----------
        evidence_data (Dict[str, Any]): Evidence data to validate
        evidence_text (Optional[str]): Text content for analysis

        Returns
        -------
        Dict[str, Any]: Research methodology validation results

        """
        validation_results = {
            "protocol_compliance": {
                "step_1_discovery": {"compliant": False, "evidence": [], "score": 0.0},
                "step_2_analysis": {"compliant": False, "evidence": [], "score": 0.0},
                "step_3_evidence": {"compliant": False, "evidence": [], "score": 0.0},
                "step_4_synthesis": {"compliant": False, "evidence": [], "score": 0.0},
            },
            "overall_compliance_score": 0.0,
            "violations": [],
            "recommendations": [],
            "anti_lazy_compliance": False,
            "context_inheritance_compliance": False,
        }

        try:
            # Prepare text for analysis
            if evidence_text is None:
                evidence_text = self._extract_text_from_evidence(evidence_data)

            # Apply patterns
            patterns_matched = self._apply_patterns(evidence_text)

            # Validate Step 1: Discovery and Exploration
            step_1_patterns = [
                p
                for p in patterns_matched
                if any(
                    keyword in p[0].lower()
                    for keyword in ["discovery", "exploration", "glob", "search"]
                )
            ]
            if step_1_patterns:
                validation_results["protocol_compliance"]["step_1_discovery"]["compliant"] = True
                validation_results["protocol_compliance"]["step_1_discovery"]["evidence"] = (
                    step_1_patterns
                )
                validation_results["protocol_compliance"]["step_1_discovery"]["score"] = max(
                    conf for _, conf in step_1_patterns
                )

            # Validate Step 2: Analysis
            step_2_patterns = [
                p
                for p in patterns_matched
                if any(
                    keyword in p[0].lower()
                    for keyword in ["analysis", "findings", "existing", "gap"]
                )
            ]
            if step_2_patterns:
                validation_results["protocol_compliance"]["step_2_analysis"]["compliant"] = True
                validation_results["protocol_compliance"]["step_2_analysis"]["evidence"] = (
                    step_2_patterns
                )
                validation_results["protocol_compliance"]["step_2_analysis"]["score"] = max(
                    conf for _, conf in step_2_patterns
                )

            # Validate Step 3: Evidence Collection
            step_3_patterns = [
                p
                for p in patterns_matched
                if any(
                    keyword in p[0].lower()
                    for keyword in ["evidence", "citation", "source", "file"]
                )
            ]
            if step_3_patterns:
                validation_results["protocol_compliance"]["step_3_evidence"]["compliant"] = True
                validation_results["protocol_compliance"]["step_3_evidence"]["evidence"] = (
                    step_3_patterns
                )
                validation_results["protocol_compliance"]["step_3_evidence"]["score"] = max(
                    conf for _, conf in step_3_patterns
                )

            # Validate Step 4: Synthesis
            step_4_patterns = [
                p
                for p in patterns_matched
                if any(
                    keyword in p[0].lower() for keyword in ["synthesis", "integration", "report"]
                )
            ]
            if step_4_patterns:
                validation_results["protocol_compliance"]["step_4_synthesis"]["compliant"] = True
                validation_results["protocol_compliance"]["step_4_synthesis"]["evidence"] = (
                    step_4_patterns
                )
                validation_results["protocol_compliance"]["step_4_synthesis"]["score"] = max(
                    conf for _, conf in step_4_patterns
                )

            # Validate Anti-Lazy Planning compliance
            anti_lazy_patterns = [p for p in patterns_matched if "anti_lazy" in p[0].lower()]
            validation_results["anti_lazy_compliance"] = len(anti_lazy_patterns) > 0

            # Validate Context Inheritance compliance
            context_patterns = [
                p for p in patterns_matched if "context" in p[0].lower() or "claude" in p[0].lower()
            ]
            validation_results["context_inheritance_compliance"] = len(context_patterns) > 0

            # Calculate overall compliance score
            step_scores = [
                validation_results["protocol_compliance"]["step_1_discovery"]["score"],
                validation_results["protocol_compliance"]["step_2_analysis"]["score"],
                validation_results["protocol_compliance"]["step_3_evidence"]["score"],
                validation_results["protocol_compliance"]["step_4_synthesis"]["score"],
            ]
            validation_results["overall_compliance_score"] = sum(step_scores) / len(step_scores)

            # Identify violations
            for step_name, step_data in validation_results["protocol_compliance"].items():
                if not step_data["compliant"]:
                    validation_results["violations"].append(
                        {
                            "type": f"{step_name}_violation",
                            "description": f"Research protocol step {step_name} not detected",
                            "severity": "high"
                            if step_name in ["step_1_discovery", "step_3_evidence"]
                            else "medium",
                        }
                    )

            if not validation_results["anti_lazy_compliance"]:
                validation_results["violations"].append(
                    {
                        "type": "anti_lazy_violation",
                        "description": "Anti-Lazy Planning protocol not detected",
                        "severity": "high",
                    }
                )

            if not validation_results["context_inheritance_compliance"]:
                validation_results["violations"].append(
                    {
                        "type": "context_inheritance_violation",
                        "description": "Context inheritance/CLAUDE.md compliance not detected",
                        "severity": "high",
                    }
                )

            # Generate recommendations
            if validation_results["overall_compliance_score"] < 0.8:
                validation_results["recommendations"].append(
                    "Implement complete 4-step research protocol from CLAUDE.md PART L"
                )

            if not validation_results["protocol_compliance"]["step_1_discovery"]["compliant"]:
                validation_results["recommendations"].append(
                    "Always start with discovery and exploration using Glob/Grep/Read tools"
                )

            if not validation_results["protocol_compliance"]["step_3_evidence"]["compliant"]:
                validation_results["recommendations"].append(
                    "Ensure evidence collection with specific file paths and line numbers"
                )

            if not validation_results["anti_lazy_compliance"]:
                validation_results["recommendations"].append(
                    "Follow Anti-Lazy Planning protocol: explore existing code before planning"
                )

            if not validation_results["context_inheritance_compliance"]:
                validation_results["recommendations"].append(
                    "Always read CLAUDE.md first to inherit context and standards"
                )

            logger.debug(
                f"Research methodology validation completed: {validation_results['overall_compliance_score']:.2f}"
            )
            return validation_results

        except Exception as e:
            logger.exception(f"Research methodology validation failed: {e}")
            validation_results["error"] = str(e)
            return validation_results

    def get_pattern_effectiveness(self) -> dict[str, dict[str, Any]]:
        """Analyze pattern effectiveness across all enrichments.

        Returns:
        Dict[str, Dict[str, Any]]: Pattern effectiveness metrics

        """
        try:
            with sqlite3.connect(self.cks_db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT pattern_id, COUNT(*) as match_count, AVG(confidence_score) as avg_confidence
                    FROM pattern_matching_history
                    GROUP BY pattern_id
                    ORDER BY match_count DESC
                """)

                pattern_stats = {}
                for row in cursor.fetchall():
                    pattern_id, match_count, avg_confidence = row
                    pattern_stats[pattern_id] = {
                        "match_count": match_count,
                        "average_confidence": avg_confidence,
                        "effectiveness_score": match_count * avg_confidence,
                    }

                return pattern_stats

        except Exception as e:
            logger.exception(f"Failed to analyze pattern effectiveness: {e}")
            return {}
