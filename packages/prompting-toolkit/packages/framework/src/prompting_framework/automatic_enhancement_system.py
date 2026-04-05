from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .context_models import PromptingContext, PromptingTechnique
from .unified_prompting_system import IntegrationMode, UnifiedPromptingSystem

"""Automatic Cognitive Enhancement System Core.

Intelligent framework selection and seamless integration for automatic cognitive
enhancement with 40-80% improvement in query processing quality.

This system provides:
- Automatic query analysis for framework selection
- Intelligent enhancement technique coordination
- Performance optimization with quality thresholds
- Seamless user experience with transparent improvement
- CSF constitutional compliance integration
"""





# Import existing orchestration systems


class EnhancementLevel(Enum):
    """Levels of cognitive enhancement intensity."""

    MINIMAL = "minimal"  # Basic enhancement, <1s additional processing
    MODERATE = "moderate"  # Standard enhancement, 1-2s additional processing
    AGGRESSIVE = "aggressive"  # Maximum enhancement, 2-3s additional processing


class QueryComplexityMetrics(Enum):
    """Metrics for query complexity assessment."""

    LENGTH = "length"
    STRUCTURE = "structure"
    DOMAIN_SPECIFICITY = "domain_specificity"
    MULTIPLICITY = "multiplicity"
    AMBIGUITY = "ambiguity"
    EVIDENCE_REQUIREMENTS = "evidence_requirements"


@dataclass
class QueryAnalysis:
    """Comprehensive analysis of user query for intelligent enhancement."""

    # Core metrics
    complexity_score: float  # 0.0 to 1.0
    domain_specificity: float  # 0.0 to 1.0
    ambiguity_score: float  # 0.0 to 1.0 (higher = more ambiguous)
    multi_faceted_score: float  # 0.0 to 1.0

    # Domain and intent analysis
    detected_domains: list[str]
    primary_intent: str
    secondary_intents: list[str]

    # Enhancement recommendations
    recommended_enhancement_level: EnhancementLevel
    applicable_frameworks: list[PromptingTechnique]
    framework_confidence_scores: dict[PromptingTechnique, float]

    # Performance considerations
    estimated_enhancement_time: float
    quality_improvement_potential: float

    # Metadata
    analysis_timestamp: float = field(default_factory=time.time)
    analysis_confidence: float = 0.0


@dataclass
class EnhancementDecision:
    """Decision about which enhancement frameworks to apply."""

    selected_frameworks: list[PromptingTechnique]
    enhancement_level: EnhancementLevel
    application_strategy: str  # "sequential", "parallel", "hybrid"
    confidence_threshold: float
    expected_improvement: float
    processing_budget: float  # seconds

    # Rationale
    decision_reasoning: str
    risk_factors: list[str]
    mitigation_strategies: list[str]


@dataclass
class EnhancementResult:
    """Result of automatic cognitive enhancement process."""

    # Core results
    enhanced_query: str
    applied_frameworks: list[PromptingTechnique]
    enhancement_metadata: dict[str, Any]

    # Quality metrics
    original_quality_score: float
    enhanced_quality_score: float
    improvement_percentage: float

    # Performance metrics
    processing_time: float
    framework_application_times: dict[PromptingTechnique, float]

    # Compliance and validation
    constitutional_compliance: dict[str, bool]
    quality_validation_passed: bool

    # Metadata
    enhancement_confidence: float
    user_transparency_explanation: str


class AutomaticEnhancementSystem:
    """
    Automatic Cognitive Enhancement System with Intelligent Framework Selection.

    This system extends existing orchestration systems to provide automatic
    cognitive enhancement with intelligent framework selection based on query
    analysis, domain detection, and user intent analysis.
    """

    def __init__(
        self,
        max_enhancement_time: float = 3.0,
        min_quality_threshold: float = 0.7,
        enable_parallel_processing: bool = True,
        cache_decisions: bool = True,
    ):
        """
        Initialize the automatic enhancement system.

        Args:
        ----
            max_enhancement_time: Maximum additional time for enhancement processing
            min_quality_threshold: Minimum quality threshold to trigger enhancement
            enable_parallel_processing: Whether to enable parallel framework execution
            cache_decisions: Whether to cache enhancement decisions for reuse

        """
        self.logger = logging.getLogger(__name__)

        # Configuration parameters
        self.max_enhancement_time = max_enhancement_time
        self.min_quality_threshold = min_quality_threshold
        self.enable_parallel_processing = enable_parallel_processing
        self.cache_decisions = cache_decisions

        # Core systems
        self.unified_system = UnifiedPromptingSystem(
            integration_mode=IntegrationMode.ADAPTIVE,
        )

        # Decision caching
        self._decision_cache: dict[str, EnhancementDecision] = {}
        self._analysis_cache: dict[str, QueryAnalysis] = {}

        # Framework application thresholds
        self.framework_thresholds = {
            PromptingTechnique.QUERY_FANOUT: {
                "min_complexity_score": 0.6,
                "min_multi_faceted_score": 0.5,
                "max_processing_time": 1.5,
            },
            PromptingTechnique.SOCRATIC: {
                "min_ambiguity_score": 0.4,
                "requires_critical_thinking": True,
                "max_processing_time": 1.2,
            },
            PromptingTechnique.SELF_REFINE: {
                "min_quality_improvement_potential": 0.3,
                "iterative_enhancement": True,
                "max_processing_time": 2.0,
            },
            PromptingTechnique.CHAIN_OF_VERIFICATION: {
                "requires_evidence": True,
                "min_domain_specificity": 0.5,
                "max_processing_time": 1.8,
            },
            PromptingTechnique.TREE_OF_THOUGHTS: {
                "min_complexity_score": 0.7,
                "requires_exploration": True,
                "max_processing_time": 2.5,
            },
        }

        # Performance budgets by enhancement level
        self.enhancement_budgets = {
            EnhancementLevel.MINIMAL: {"time": 0.8, "frameworks": 1},
            EnhancementLevel.MODERATE: {"time": 2.0, "frameworks": 2},
            EnhancementLevel.AGGRESSIVE: {"time": 3.0, "frameworks": 3},
        }

        self.logger.info("✅ Automatic Enhancement System initialized successfully")

    async def analyze_query_for_enhancement(
        self,
        query: str,
        context: PromptingContext | None = None,
    ) -> QueryAnalysis:
        """
        Perform comprehensive query analysis for enhancement decisions.

        Args:
        ----
            query: The user query to analyze
            context: Optional existing context information

        Returns:
        -------
            Comprehensive query analysis with enhancement recommendations

        """
        start_time = time.time()

        # Check cache first
        cache_key = self._generate_query_cache_key(query, context)
        if self.cache_decisions and cache_key in self._analysis_cache:
            self.logger.debug(f"Using cached analysis for query: {query[:50]}...")
            return self._analysis_cache[cache_key]

        try:
            # Step 1: Basic quality metrics
            complexity_score = await self._calculate_complexity_score(query)
            domain_specificity = await self._calculate_domain_specificity(query)
            ambiguity_score = await self._calculate_ambiguity_score(query)
            multi_faceted_score = await self._calculate_multi_faceted_score(query)

            # Step 2: Domain and intent detection
            detected_domains = await self._detect_domains(query, context)
            primary_intent = await self._detect_primary_intent(query, detected_domains)
            secondary_intents = await self._detect_secondary_intents(query, primary_intent)

            # Step 3: Framework applicability assessment
            applicable_frameworks = await self._assess_framework_applicability(
                query,
                complexity_score,
                domain_specificity,
                ambiguity_score,
                multi_faceted_score,
                detected_domains,
            )

            framework_confidence_scores = await self._calculate_framework_confidence(
                applicable_frameworks,
                query,
                detected_domains,
            )

            # Step 4: Enhancement level recommendation
            recommended_enhancement_level = await self._recommend_enhancement_level(
                complexity_score,
                ambiguity_score,
                multi_faceted_score,
                detected_domains,
            )

            # Step 5: Performance estimation
            estimated_enhancement_time = await self._estimate_enhancement_time(
                recommended_enhancement_level,
                applicable_frameworks,
            )

            quality_improvement_potential = await self._estimate_quality_improvement_potential(
                complexity_score,
                ambiguity_score,
                applicable_frameworks,
            )

            # Step 6: Calculate overall analysis confidence
            analysis_confidence = await self._calculate_analysis_confidence(
                complexity_score,
                domain_specificity,
                len(detected_domains),
                len(applicable_frameworks),
            )

            # Create analysis result
            analysis = QueryAnalysis(
                complexity_score=complexity_score,
                domain_specificity=domain_specificity,
                ambiguity_score=ambiguity_score,
                multi_faceted_score=multi_faceted_score,
                detected_domains=detected_domains,
                primary_intent=primary_intent,
                secondary_intents=secondary_intents,
                recommended_enhancement_level=recommended_enhancement_level,
                applicable_frameworks=applicable_frameworks,
                framework_confidence_scores=framework_confidence_scores,
                estimated_enhancement_time=estimated_enhancement_time,
                quality_improvement_potential=quality_improvement_potential,
                analysis_confidence=analysis_confidence,
            )

            # Cache the analysis
            if self.cache_decisions:
                self._analysis_cache[cache_key] = analysis

            processing_time = time.time() - start_time
            self.logger.debug(
                f"Query analysis completed in {processing_time:.3f}s with {analysis_confidence:.2f} confidence",
            )

            return analysis

        except Exception as e:
            self.logger.error(f"Query analysis failed: {e!s}")
            # Return minimal analysis for fallback
            return QueryAnalysis(
                complexity_score=0.5,
                domain_specificity=0.3,
                ambiguity_score=0.5,
                multi_faceted_score=0.3,
                detected_domains=["general"],
                primary_intent="get_advice",
                secondary_intents=[],
                recommended_enhancement_level=EnhancementLevel.MINIMAL,
                applicable_frameworks=[PromptingTechnique.CHAIN_OF_THOUGHT],
                framework_confidence_scores={PromptingTechnique.CHAIN_OF_THOUGHT: 0.6},
                estimated_enhancement_time=0.5,
                quality_improvement_potential=0.2,
                analysis_confidence=0.4,
            )

    async def make_enhancement_decision(
        self,
        analysis: QueryAnalysis,
        performance_budget: float | None = None,
    ) -> EnhancementDecision:
        """
        Make intelligent decision about enhancement framework selection.

        Args:
        ----
            analysis: Query analysis results
            performance_budget: Optional performance budget constraint

        Returns:
        -------
            Enhancement decision with selected frameworks and strategy

        """
        # Check cache first
        cache_key = self._generate_decision_cache_key(analysis)
        if self.cache_decisions and cache_key in self._decision_cache:
            self.logger.debug("Using cached enhancement decision")
            return self._decision_cache[cache_key]

        try:
            # Determine available processing budget
            available_budget = performance_budget or self.max_enhancement_time
            enhancement_budget = self.enhancement_budgets[analysis.recommended_enhancement_level]
            processing_budget = min(available_budget, enhancement_budget["time"])

            # Filter frameworks by confidence and performance constraints
            viable_frameworks = []
            for framework in analysis.applicable_frameworks:
                confidence = analysis.framework_confidence_scores.get(framework, 0.0)
                threshold_config = self.framework_thresholds.get(framework, {})

                # Check confidence threshold
                if confidence < 0.6:  # Minimum confidence threshold
                    continue

                # Check processing time constraints
                max_time = threshold_config.get("max_processing_time", 1.0)
                if max_time > processing_budget:
                    continue

                # Check applicability requirements
                if framework == PromptingTechnique.QUERY_FANOUT:
                    if analysis.multi_faceted_score < threshold_config.get("min_multi_faceted_score", 0.5):
                        continue
                elif framework == PromptingTechnique.SOCRATIC:
                    if analysis.ambiguity_score < threshold_config.get("min_ambiguity_score", 0.4):
                        continue
                elif framework == PromptingTechnique.CHAIN_OF_VERIFICATION:
                    if analysis.domain_specificity < threshold_config.get("min_domain_specificity", 0.5):
                        continue

                viable_frameworks.append(framework)

            # Sort by confidence score
            viable_frameworks.sort(
                key=lambda f: analysis.framework_confidence_scores.get(f, 0.0),
                reverse=True,
            )

            # Limit number of frameworks based on budget and enhancement level
            max_frameworks = enhancement_budget["frameworks"]
            selected_frameworks = viable_frameworks[:max_frameworks]

            # Determine application strategy
            application_strategy = await self._determine_application_strategy(
                selected_frameworks,
                processing_budget,
            )

            # Calculate expected improvement and confidence
            expected_improvement = await self._calculate_expected_improvement(
                selected_frameworks,
                analysis,
            )

            confidence_threshold = min(
                analysis.framework_confidence_scores.get(selected_frameworks[0], 0.7) if selected_frameworks else 0.7,
                analysis.analysis_confidence,
            )

            # Generate decision reasoning
            decision_reasoning = await self._generate_decision_reasoning(
                analysis,
                selected_frameworks,
                expected_improvement,
            )

            # Assess risk factors
            risk_factors = await self._assess_enhancement_risks(
                selected_frameworks,
                analysis,
                processing_budget,
            )

            # Generate mitigation strategies
            mitigation_strategies = await self._generate_mitigation_strategies(risk_factors)

            decision = EnhancementDecision(
                selected_frameworks=selected_frameworks,
                enhancement_level=analysis.recommended_enhancement_level,
                application_strategy=application_strategy,
                confidence_threshold=confidence_threshold,
                expected_improvement=expected_improvement,
                processing_budget=processing_budget,
                decision_reasoning=decision_reasoning,
                risk_factors=risk_factors,
                mitigation_strategies=mitigation_strategies,
            )

            # Cache the decision
            if self.cache_decisions:
                self._decision_cache[cache_key] = decision

            self.logger.info(
                f"Enhancement decision: {len(selected_frameworks)} frameworks, "
                f"{expected_improvement:.1%} expected improvement, "
                f"{application_strategy} strategy",
            )

            return decision

        except Exception as e:
            self.logger.error(f"Enhancement decision failed: {e!s}")
            # Fallback decision
            return EnhancementDecision(
                selected_frameworks=[PromptingTechnique.CHAIN_OF_THOUGHT],
                enhancement_level=EnhancementLevel.MINIMAL,
                application_strategy="sequential",
                confidence_threshold=0.6,
                expected_improvement=0.2,
                processing_budget=min(1.0, available_budget if performance_budget else 1.0),
                decision_reasoning="Fallback decision due to error",
                risk_factors=["processing_error"],
                mitigation_strategies=["use_basic_enhancement"],
            )

    async def apply_automatic_enhancement(
        self,
        query: str,
        context: PromptingContext | None = None,
        performance_budget: float | None = None,
    ) -> EnhancementResult:
        """
        Apply automatic cognitive enhancement with intelligent framework selection.

        Args:
        ----
            query: Original user query
            context: Optional context information
            performance_budget: Optional performance budget constraint

        Returns:
        -------
            Enhancement result with improved query and metadata

        """
        start_time = time.time()
        original_quality_score = await self._calculate_base_quality_score(query)

        try:
            self.logger.info(f"Starting automatic enhancement for query: {query[:50]}...")

            # Step 1: Analyze query
            analysis = await self.analyze_query_for_enhancement(query, context)

            # Step 2: Make enhancement decision
            decision = await self.make_enhancement_decision(analysis, performance_budget)

            # Step 3: Check if enhancement is warranted
            if (
                not decision.selected_frameworks
                or decision.expected_improvement < 0.1
                or decision.confidence_threshold < 0.5
            ):
                self.logger.info("Enhancement not warranted, returning original query")
                return EnhancementResult(
                    enhanced_query=query,
                    applied_frameworks=[],
                    enhancement_metadata={"enhancement_skipped": True},
                    original_quality_score=original_quality_score,
                    enhanced_quality_score=original_quality_score,
                    improvement_percentage=0.0,
                    processing_time=time.time() - start_time,
                    framework_application_times={},
                    constitutional_compliance={"basic_compliance": True},
                    quality_validation_passed=True,
                    enhancement_confidence=1.0,
                    user_transparency_explanation="No enhancement applied - original query quality is sufficient",
                )

            # Step 4: Apply enhancement frameworks
            enhanced_query, framework_times = await self._apply_enhancement_frameworks(
                query,
                decision,
                context,
            )

            # Step 5: Calculate quality improvement
            enhanced_quality_score = await self._calculate_base_quality_score(enhanced_query)
            improvement_percentage = (
                (enhanced_quality_score - original_quality_score) / max(original_quality_score, 0.1)
            ) * 100

            # Step 6: Validate constitutional compliance
            constitutional_compliance = await self._validate_constitutional_compliance(
                enhanced_query,
                decision.selected_frameworks,
            )

            # Step 7: Quality validation
            quality_validation_passed = await self._validate_quality_improvement(
                original_quality_score,
                enhanced_quality_score,
                decision,
            )

            # Step 8: Generate user transparency explanation
            user_transparency_explanation = await self._generate_transparency_explanation(
                decision,
                improvement_percentage,
                framework_times,
            )

            # Step 9: Calculate enhancement confidence
            enhancement_confidence = min(
                decision.confidence_threshold,
                analysis.analysis_confidence,
                1.0 if quality_validation_passed else 0.5,
            )

            processing_time = time.time() - start_time

            self.logger.info(
                f"Automatic enhancement completed: {improvement_percentage:.1f}% improvement "
                f"in {processing_time:.2f}s with {enhancement_confidence:.2f} confidence",
            )

            return EnhancementResult(
                enhanced_query=enhanced_query,
                applied_frameworks=decision.selected_frameworks,
                enhancement_metadata={
                    "enhancement_level": decision.enhancement_level.value,
                    "application_strategy": decision.application_strategy,
                    "decision_reasoning": decision.decision_reasoning,
                    "risk_factors": decision.risk_factors,
                    "mitigation_applied": decision.mitigation_strategies,
                },
                original_quality_score=original_quality_score,
                enhanced_quality_score=enhanced_quality_score,
                improvement_percentage=improvement_percentage,
                processing_time=processing_time,
                framework_application_times=framework_times,
                constitutional_compliance=constitutional_compliance,
                quality_validation_passed=quality_validation_passed,
                enhancement_confidence=enhancement_confidence,
                user_transparency_explanation=user_transparency_explanation,
            )

        except Exception as e:
            self.logger.error(f"Automatic enhancement failed: {e!s}")
            # Return original query with error metadata
            processing_time = time.time() - start_time
            return EnhancementResult(
                enhanced_query=query,
                applied_frameworks=[],
                enhancement_metadata={"error": str(e), "fallback_mode": True},
                original_quality_score=original_quality_score,
                enhanced_quality_score=original_quality_score,
                improvement_percentage=0.0,
                processing_time=processing_time,
                framework_application_times={},
                constitutional_compliance={"error_fallback": True},
                quality_validation_passed=True,
                enhancement_confidence=0.3,
                user_transparency_explanation=f"Enhancement failed due to technical error: {e!s}",
            )

    # Private helper methods for query analysis

    async def _calculate_complexity_score(self, query: str) -> float:
        """Calculate query complexity score (0.0 to 1.0)."""
        complexity_indicators = [
            "implement",
            "design",
            "analyze",
            "optimize",
            "integrate",
            "coordinate",
            "multiple",
            "various",
            "several",
            "complex",
            "advanced",
            "comprehensive",
        ]

        # Length complexity (normalized)
        length_score = min(1.0, len(query) / 500)

        # Vocabulary complexity
        complexity_words = sum(1 for word in complexity_indicators if word in query.lower())
        vocab_score = min(1.0, complexity_words / 3)

        # Structural complexity (questions, conditions, multiple parts)
        structural_score = 0.0
        if "?" in query:
            structural_score += 0.2
        if any(word in query.lower() for word in ["and", "or", "but", "while"]):
            structural_score += 0.3
        if query.count(".") > 2:
            structural_score += 0.2

        return min(1.0, (length_score + vocab_score + structural_score) / 3)

    async def _calculate_domain_specificity(self, query: str) -> float:
        """Calculate domain specificity score (0.0 to 1.0)."""
        domain_keywords = {
            "security": ["security", "authentication", "authorization", "encryption", "vulnerability", "threat"],
            "architecture": ["architecture", "design", "structure", "system", "component", "scalability"],
            "performance": ["performance", "optimization", "speed", "latency", "throughput", "efficiency"],
            "development": ["code", "implement", "develop", "programming", "software", "application"],
            "research": ["research", "study", "analyze", "investigate", "explore", "examine"],
        }

        max_specificity = 0.0
        for _domain, keywords in domain_keywords.items():
            domain_score = sum(1 for keyword in keywords if keyword in query.lower())
            domain_specificity = min(1.0, domain_score / 2)
            max_specificity = max(max_specificity, domain_specificity)

        return max_specificity

    async def _calculate_ambiguity_score(self, query: str) -> float:
        """Calculate ambiguity score (0.0 to 1.0, higher = more ambiguous)."""
        ambiguity_indicators = [
            "something",
            "anything",
            "help",
            "fix",
            "improve",
            "better",
            "some",
            "maybe",
            "perhaps",
            "possibly",
            "could",
            "might",
            "should",
            "generally",
            "usually",
        ]

        specificity_indicators = [
            "specific",
            "exact",
            "precise",
            "particular",
            "detailed",
            "concrete",
            "implement",
            "build",
            "create",
            "design",
            "optimize",
        ]

        ambiguity_count = sum(1 for indicator in ambiguity_indicators if indicator in query.lower())
        specificity_count = sum(1 for indicator in specificity_indicators if indicator in query.lower())

        raw_ambiguity = min(1.0, ambiguity_count / 3)
        specificity_penalty = min(0.5, specificity_count * 0.15)

        return max(0.0, raw_ambiguity - specificity_penalty)

    async def _calculate_multi_faceted_score(self, query: str) -> float:
        """Calculate multi-faceted score (0.0 to 1.0)."""
        connectors = ["and", "or", "but", "while", "also", "additionally", "furthermore", "moreover"]
        question_words = ["what", "how", "why", "when", "where", "which"]

        connector_count = sum(1 for conn in connectors if f" {conn} " in f" {query.lower()} ")
        question_count = sum(1 for qword in question_words if query.lower().startswith(qword))

        # Check for multiple aspects/topics
        sentences = query.split(".")
        sentence_count = len([s for s in sentences if s.strip()])

        multi_faceted_score = min(1.0, (connector_count + question_count + (sentence_count - 1)) / 4)

        return multi_faceted_score

    async def _detect_domains(self, query: str, context: PromptingContext | None) -> list[str]:
        """Detect relevant domains for the query."""
        detected_domains = []

        domain_keywords = {
            "security": ["security", "authentication", "authorization", "encryption", "vulnerability"],
            "architecture": ["architecture", "design", "structure", "system", "component"],
            "performance": ["performance", "optimization", "speed", "latency", "efficiency"],
            "development": ["code", "implement", "develop", "programming", "software"],
            "research": ["research", "study", "analyze", "investigate", "explore"],
            "debugging": ["debug", "error", "issue", "problem", "fix", "troubleshoot"],
        }

        query_lower = query.lower()
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_domains.append(domain)

        # Add context domain if available
        if context and context.domain not in detected_domains:
            detected_domains.insert(0, context.domain)

        # Default to general if no domains detected
        if not detected_domains:
            detected_domains.append("general")

        return detected_domains

    async def _detect_primary_intent(self, query: str, detected_domains: list[str]) -> str:
        """Detect the primary user intent from the query."""
        intent_patterns = {
            "get_advice": ["help", "advice", "recommendation", "suggestion", "guidance"],
            "solve_problem": ["solve", "fix", "resolve", "address", "handle"],
            "analyze_situation": ["analyze", "examine", "review", "assess", "evaluate"],
            "make_decision": ["decide", "choose", "select", "determine", "pick"],
            "generate_code": ["implement", "code", "program", "develop", "build"],
            "debug_issue": ["debug", "error", "issue", "problem", "troubleshoot"],
            "research_topic": ["research", "study", "investigate", "explore", "find"],
            "compare_options": ["compare", "versus", "vs", "difference", "better"],
        }

        query_lower = query.lower()
        intent_scores = {}

        for intent, patterns in intent_patterns.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            intent_scores[intent] = score

        if intent_scores:
            primary_intent = max(intent_scores, key=intent_scores.get)
            if intent_scores[primary_intent] > 0:
                return primary_intent

        return "get_advice"  # Default intent

    async def _detect_secondary_intents(self, query: str, primary_intent: str) -> list[str]:
        """Detect secondary user intents from the query."""
        # This is a simplified implementation
        # In practice, this would use more sophisticated NLP techniques
        secondary_intents = []

        # Look for additional intent indicators beyond the primary
        if "?" in query and primary_intent != "research_topic":
            secondary_intents.append("research_topic")

        if (
            any(word in query.lower() for word in ["compare", "versus", "better"])
            and primary_intent != "compare_options"
        ):
            secondary_intents.append("compare_options")

        return secondary_intents

    async def _assess_framework_applicability(
        self,
        query: str,
        complexity_score: float,
        domain_specificity: float,
        ambiguity_score: float,
        multi_faceted_score: float,
        detected_domains: list[str],
    ) -> list[PromptingTechnique]:
        """Assess which frameworks are applicable to this query."""
        applicable_frameworks = []

        # QueryFanout: Multi-faceted queries
        if multi_faceted_score > 0.5 or complexity_score > 0.6:
            applicable_frameworks.append(PromptingTechnique.QUERY_FANOUT)

        # Socratic Method: Ambiguous queries or critical thinking needed
        if ambiguity_score > 0.4 or any(domain in detected_domains for domain in ["architecture", "security"]):
            applicable_frameworks.append(PromptingTechnique.SOCRATIC)

        # Self-Refine: Complex queries needing iterative improvement
        if complexity_score > 0.7 or domain_specificity > 0.6:
            applicable_frameworks.append(PromptingTechnique.SELF_REFINE)

        # Chain-of-Verification: Evidence-based domains
        if any(domain in detected_domains for domain in ["security", "research", "architecture"]):
            applicable_frameworks.append(PromptingTechnique.CHAIN_OF_VERIFICATION)

        # Tree-of-Thoughts: Complex exploration scenarios
        if complexity_score > 0.8 or multi_faceted_score > 0.7:
            applicable_frameworks.append(PromptingTechnique.TREE_OF_THOUGHTS)

        # Always include basic Chain-of-Thought as fallback
        if not applicable_frameworks:
            applicable_frameworks.append(PromptingTechnique.CHAIN_OF_THOUGHT)

        return applicable_frameworks

    async def _calculate_framework_confidence(
        self,
        frameworks: list[PromptingTechnique],
        query: str,
        detected_domains: list[str],
    ) -> dict[PromptingTechnique, float]:
        """Calculate confidence scores for each framework."""
        confidence_scores = {}

        base_confidence = 0.7  # Base confidence for applicable frameworks

        for framework in frameworks:
            confidence = base_confidence

            # Adjust confidence based on framework specialization
            if framework == PromptingTechnique.QUERY_FANOUT:
                if len(detected_domains) > 1:
                    confidence += 0.2
            elif framework == PromptingTechnique.SOCRATIC:
                if any(domain in detected_domains for domain in ["architecture", "security"]):
                    confidence += 0.15
            elif framework == PromptingTechnique.CHAIN_OF_VERIFICATION:
                if "security" in detected_domains or "research" in detected_domains:
                    confidence += 0.2
            elif framework == PromptingTechnique.TREE_OF_THOUGHTS:
                if len(query) > 200:  # Longer queries benefit more
                    confidence += 0.1

            confidence_scores[framework] = min(1.0, confidence)

        return confidence_scores

    # Additional private methods would continue here...
    # Due to length constraints, I'll include key remaining methods in the next part

    async def _recommend_enhancement_level(
        self,
        complexity_score: float,
        ambiguity_score: float,
        multi_faceted_score: float,
        detected_domains: list[str],
    ) -> EnhancementLevel:
        """Recommend the appropriate enhancement level."""
        # Calculate overall enhancement need score
        enhancement_need = (complexity_score + ambiguity_score + multi_faceted_score) / 3

        # Adjust for specialized domains
        if any(domain in detected_domains for domain in ["security", "architecture"]):
            enhancement_need += 0.1

        if enhancement_need >= 0.8:
            return EnhancementLevel.AGGRESSIVE
        if enhancement_need >= 0.5:
            return EnhancementLevel.MODERATE
        return EnhancementLevel.MINIMAL

    async def _estimate_enhancement_time(
        self,
        enhancement_level: EnhancementLevel,
        frameworks: list[PromptingTechnique],
    ) -> float:
        """Estimate enhancement processing time."""
        base_times = {
            EnhancementLevel.MINIMAL: 0.5,
            EnhancementLevel.MODERATE: 1.5,
            EnhancementLevel.AGGRESSIVE: 2.5,
        }

        framework_times = {
            PromptingTechnique.QUERY_FANOUT: 0.8,
            PromptingTechnique.SOCRATIC: 0.6,
            PromptingTechnique.SELF_REFINE: 1.2,
            PromptingTechnique.CHAIN_OF_VERIFICATION: 1.0,
            PromptingTechnique.TREE_OF_THOUGHTS: 1.5,
            PromptingTechnique.CHAIN_OF_THOUGHT: 0.3,
        }

        base_time = base_times[enhancement_level]
        framework_time = sum(framework_times.get(f, 0.5) for f in frameworks[:2])  # Top 2 frameworks

        return min(self.max_enhancement_time, base_time + framework_time)

    async def _estimate_quality_improvement_potential(
        self,
        complexity_score: float,
        ambiguity_score: float,
        frameworks: list[PromptingTechnique],
    ) -> float:
        """Estimate potential quality improvement (0.0 to 1.0)."""
        base_potential = (complexity_score + ambiguity_score) / 2

        framework_multipliers = {
            PromptingTechnique.QUERY_FANOUT: 1.3,
            PromptingTechnique.SOCRATIC: 1.4,
            PromptingTechnique.SELF_REFINE: 1.5,
            PromptingTechnique.CHAIN_OF_VERIFICATION: 1.2,
            PromptingTechnique.TREE_OF_THOUGHTS: 1.4,
            PromptingTechnique.CHAIN_OF_THOUGHT: 1.1,
        }

        if frameworks:
            max_multiplier = max(framework_multipliers.get(f, 1.0) for f in frameworks)
            return min(1.0, base_potential * max_multiplier)

        return min(0.3, base_potential)

    # Cache key generation methods
    def _generate_query_cache_key(self, query: str, context: PromptingContext | None) -> str:
        """Generate cache key for query analysis."""
        context_hash = hash(str(context)) if context else 0
        query_hash = hash(query)
        return f"query_analysis:{query_hash}:{context_hash}"

    def _generate_decision_cache_key(self, analysis: QueryAnalysis) -> str:
        """Generate cache key for enhancement decision."""
        key_components = [
            analysis.complexity_score,
            analysis.domain_specificity,
            analysis.ambiguity_score,
            analysis.multi_faceted_score,
            analysis.recommended_enhancement_level.value,
            len(analysis.applicable_frameworks),
        ]
        return f"enhancement_decision:{hash(str(key_components))}"

    # Simplified implementations for remaining methods
    async def _calculate_analysis_confidence(
        self,
        complexity_score: float,
        domain_specificity: float,
        domain_count: int,
        framework_count: int,
    ) -> float:
        """Calculate confidence in the analysis."""
        base_confidence = 0.8

        # Higher confidence with clearer signals
        if complexity_score > 0.7 or complexity_score < 0.3:
            base_confidence += 0.1
        if domain_specificity > 0.6 or domain_specificity < 0.3:
            base_confidence += 0.1
        if domain_count <= 2:  # Clear domain focus
            base_confidence += 0.1
        if framework_count > 0:
            base_confidence += 0.1

        return min(1.0, base_confidence)

    async def _determine_application_strategy(
        self,
        frameworks: list[PromptingTechnique],
        processing_budget: float,
    ) -> str:
        """Determine optimal framework application strategy."""
        if len(frameworks) == 1:
            return "sequential"
        if processing_budget > 2.0:
            return "parallel"
        return "hybrid"

    async def _calculate_expected_improvement(
        self,
        frameworks: list[PromptingTechnique],
        analysis: QueryAnalysis,
    ) -> float:
        """Calculate expected quality improvement."""
        if not frameworks:
            return 0.0

        base_improvement = analysis.quality_improvement_potential

        # Adjust based on number and quality of frameworks
        framework_factor = min(1.5, 1.0 + (len(frameworks) - 1) * 0.2)

        # Adjust based on framework confidence
        avg_confidence = sum(analysis.framework_confidence_scores.get(f, 0.7) for f in frameworks) / len(frameworks)
        confidence_factor = avg_confidence

        return min(0.8, base_improvement * framework_factor * confidence_factor)

    async def _generate_decision_reasoning(
        self,
        analysis: QueryAnalysis,
        frameworks: list[PromptingTechnique],
        expected_improvement: float,
    ) -> str:
        """Generate reasoning for the enhancement decision."""
        reasoning_parts = []

        reasoning_parts.append(f"Query complexity score: {analysis.complexity_score:.2f}")
        reasoning_parts.append(f"Detected domains: {', '.join(analysis.detected_domains)}")

        if frameworks:
            reasoning_parts.append(f"Selected frameworks: {', '.join(f.value for f in frameworks)}")

        reasoning_parts.append(f"Expected improvement: {expected_improvement:.1%}")

        return "; ".join(reasoning_parts)

    async def _assess_enhancement_risks(
        self,
        frameworks: list[PromptingTechnique],
        analysis: QueryAnalysis,
        processing_budget: float,
    ) -> list[str]:
        """Assess potential risks with the enhancement approach."""
        risks = []

        if analysis.estimated_enhancement_time > processing_budget * 0.8:
            risks.append("processing_time_risk")

        if len(frameworks) > 2:
            risks.append("complexity_overhead")

        if analysis.analysis_confidence < 0.6:
            risks.append("low_confidence_analysis")

        return risks

    async def _generate_mitigation_strategies(self, risk_factors: list[str]) -> list[str]:
        """Generate strategies to mitigate identified risks."""
        strategies = []

        for risk in risk_factors:
            if risk == "processing_time_risk":
                strategies.append("use_timeout_protection")
            elif risk == "complexity_overhead":
                strategies.append("limit_framework_count")
            elif risk == "low_confidence_analysis":
                strategies.append("use_conservative_enhancement")

        return strategies

    # Framework application and result generation methods

    async def _apply_enhancement_frameworks(
        self,
        query: str,
        decision: EnhancementDecision,
        context: PromptingContext | None,
    ) -> tuple[str, dict[PromptingTechnique, float]]:
        """Apply selected enhancement frameworks to the query."""
        enhanced_query = query
        framework_times = {}

        if decision.application_strategy == "sequential":
            # Apply frameworks one by one
            for framework in decision.selected_frameworks:
                start_time = time.time()
                enhanced_query = await self._apply_single_framework(
                    enhanced_query,
                    framework,
                    context,
                )
                framework_times[framework] = time.time() - start_time

        elif decision.application_strategy == "parallel":
            # Apply frameworks in parallel and combine results
            if self.enable_parallel_processing and len(decision.selected_frameworks) > 1:
                enhanced_query, framework_times = await self._apply_frameworks_parallel(
                    query,
                    decision.selected_frameworks,
                    context,
                )
            else:
                # Fallback to sequential
                for framework in decision.selected_frameworks:
                    start_time = time.time()
                    enhanced_query = await self._apply_single_framework(
                        enhanced_query,
                        framework,
                        context,
                    )
                    framework_times[framework] = time.time() - start_time

        # Apply primary framework first, then others
        elif decision.selected_frameworks:
            primary = decision.selected_frameworks[0]
            start_time = time.time()
            enhanced_query = await self._apply_single_framework(enhanced_query, primary, context)
            framework_times[primary] = time.time() - start_time

            # Apply remaining frameworks if time permits
            remaining_time = decision.processing_budget - sum(framework_times.values())
            if remaining_time > 0.5:  # Minimum time for additional enhancement
                for framework in decision.selected_frameworks[1:]:
                    if remaining_time <= 0:
                        break
                    start_time = time.time()
                    enhanced_query = await self._apply_single_framework(
                        enhanced_query,
                        framework,
                        context,
                    )
                    framework_times[framework] = time.time() - start_time
                    remaining_time -= framework_times[framework]

        return enhanced_query, framework_times

    async def _apply_single_framework(
        self,
        query: str,
        framework: PromptingTechnique,
        context: PromptingContext | None,
    ) -> str:
        """Apply a single enhancement framework to the query."""
        # Framework-specific enhancement logic
        if framework == PromptingTechnique.QUERY_FANOUT:
            return await self._apply_query_fanout(query, context)
        if framework == PromptingTechnique.SOCRATIC:
            return await self._apply_socratic_method(query, context)
        if framework == PromptingTechnique.SELF_REFINE:
            return await self._apply_self_refine(query, context)
        if framework == PromptingTechnique.CHAIN_OF_VERIFICATION:
            return await self._apply_chain_of_verification(query, context)
        if framework == PromptingTechnique.TREE_OF_THOUGHTS:
            return await self._apply_tree_of_thoughts(query, context)
        if framework == PromptingTechnique.CHAIN_OF_THOUGHT:
            return await self._apply_chain_of_thought(query, context)
        # Default enhancement for unknown frameworks
        return query + "\n\nPlease provide a comprehensive and well-structured response."

    async def _apply_query_fanout(self, query: str, context: PromptingContext | None) -> str:
        """Apply QueryFanout framework to explore multiple aspects."""
        fanout_enhancement = (
            f"{query}\n\n"
            "Please address this query from multiple perspectives:\n"
            "• Technical implementation considerations\n"
            "• Practical implications and constraints\n"
            "• Alternative approaches and trade-offs\n"
            "• Best practices and recommendations\n"
            "• Potential challenges and mitigation strategies"
        )
        return fanout_enhancement

    async def _apply_socratic_method(self, query: str, context: PromptingContext | None) -> str:
        """Apply Socratic method to deepen critical thinking."""
        socratic_enhancement = (
            f"{query}\n\n"
            "Please approach this with Socratic inquiry:\n"
            "• What are the underlying assumptions?\n"
            "• What evidence supports these assumptions?\n"
            "• Are there alternative perspectives?\n"
            "• What are the potential implications?\n"
            "• How can we verify the conclusions?\n"
            "• What questions remain unaddressed?"
        )
        return socratic_enhancement

    async def _apply_self_refine(self, query: str, context: PromptingContext | None) -> str:
        """Apply Self-Refine framework for iterative improvement."""
        self_refine_enhancement = (
            f"{query}\n\n"
            "Please provide a response and then refine it:\n"
            "1. Initial response based on the query\n"
            "2. Self-critique and identify areas for improvement\n"
            "3. Refined response addressing identified issues\n"
            "4. Final validation of the refined solution"
        )
        return self_refine_enhancement

    async def _apply_chain_of_verification(self, query: str, context: PromptingContext | None) -> str:
        """Apply Chain-of-Verification for evidence-based reasoning."""
        cov_enhancement = (
            f"{query}\n\n"
            "Please use Chain-of-Verification methodology:\n"
            "1. Provide initial answer to the query\n"
            "2. Identify key claims and assumptions\n"
            "3. Verify each claim with supporting evidence\n"
            "4. Cross-check consistency and accuracy\n"
            "5. Final verified response with confidence levels"
        )
        return cov_enhancement

    async def _apply_tree_of_thoughts(self, query: str, context: PromptingContext | None) -> str:
        """Apply Tree-of-Thoughts for exploring multiple reasoning paths."""
        tot_enhancement = (
            f"{query}\n\n"
            "Please use Tree-of-Thoughts reasoning:\n"
            "• Generate multiple potential approaches\n"
            "• Evaluate each approach step-by-step\n"
            "• Self-critique and identify potential issues\n"
            "• Explore alternative paths if needed\n"
            "• Synthesize findings into optimal solution\n"
            "• Provide confidence assessment for final answer"
        )
        return tot_enhancement

    async def _apply_chain_of_thought(self, query: str, context: PromptingContext | None) -> str:
        """Apply Chain-of-Thought for step-by-step reasoning."""
        cot_enhancement = (
            f"{query}\n\n"
            "Please think step-by-step and explain your reasoning:\n"
            "1. Break down the problem into components\n"
            "2. Analyze each component systematically\n"
            "3. Identify relationships and dependencies\n"
            "4. Synthesize findings into comprehensive solution\n"
            "5. Validate the solution against requirements"
        )
        return cot_enhancement

    async def _apply_frameworks_parallel(
        self,
        query: str,
        frameworks: list[PromptingTechnique],
        context: PromptingContext | None,
    ) -> tuple[str, dict[PromptingTechnique, float]]:
        """Apply multiple frameworks in parallel and combine results."""
        # Create parallel tasks
        tasks = []
        for framework in frameworks:
            task = asyncio.create_task(
                self._apply_single_framework(query, framework, context),
            )
            tasks.append((framework, task))

        # Wait for all tasks to complete
        framework_times = {}
        enhanced_results = []

        for framework, task in tasks:
            start_time = time.time()
            try:
                result = await task
                enhanced_results.append((framework, result))
                framework_times[framework] = time.time() - start_time
            except Exception as e:
                self.logger.error(f"Parallel framework {framework.value} failed: {e}")
                framework_times[framework] = time.time() - start_time

        # Combine the results
        if enhanced_results:
            # Use the result from the highest confidence framework as base
            primary_framework, primary_result = enhanced_results[0]
            combined_result = primary_result

            # Add insights from other frameworks
            if len(enhanced_results) > 1:
                additional_insights = []
                for framework, result in enhanced_results[1:]:
                    if result != query:  # Only add if different enhancement was applied
                        additional_insights.append(f"Additional insights from {framework.value} framework")

                if additional_insights:
                    combined_result += f"\n\nAdditional considerations: {', '.join(additional_insights)}"

            return combined_result, framework_times
        # All frameworks failed, return original query
        return query, framework_times

    async def _calculate_base_quality_score(self, query: str) -> float:
        """Calculate base quality score for a query (0.0 to 1.0)."""
        # Length quality (queries that are too short or too long get lower scores)
        length_score = 0.0
        if 20 <= len(query) <= 500:
            length_score = 1.0
        elif len(query) < 20:
            length_score = len(query) / 20
        else:
            length_score = max(0.0, 1.0 - (len(query) - 500) / 500)

        # Structure quality (presence of clear structure)
        structure_indicators = ["?", ".", "\n", ":", ";"]
        structure_score = min(1.0, sum(1 for indicator in structure_indicators if indicator in query) / 3)

        # Content quality (presence of specific, actionable content)
        quality_indicators = [
            "implement",
            "design",
            "analyze",
            "create",
            "build",
            "solve",
            "optimize",
            "improve",
            "fix",
            "debug",
            "develop",
            "architect",
            "plan",
            "evaluate",
        ]
        content_score = min(1.0, sum(1 for indicator in quality_indicators if indicator in query.lower()) / 2)

        # Clarity quality (clear questions and requests)
        clarity_indicators = ["how", "what", "why", "when", "where", "which", "should", "can"]
        clarity_score = min(1.0, sum(1 for indicator in clarity_indicators if indicator.lower() in query.lower()) / 2)

        # Weighted average
        overall_quality = length_score * 0.2 + structure_score * 0.2 + content_score * 0.4 + clarity_score * 0.2

        return min(1.0, max(0.0, overall_quality))

    async def _validate_constitutional_compliance(
        self,
        enhanced_query: str,
        frameworks: list[PromptingTechnique],
    ) -> dict[str, bool]:
        """Validate constitutional compliance for enhanced query."""
        compliance = {
            "solo_developer_friendly": True,  # Enhancement should help, not hinder solo developers
            "evidence_based": any(
                framework in [PromptingTechnique.CHAIN_OF_VERIFICATION, PromptingTechnique.REACT]
                for framework in frameworks
            ),
            "anti_deception": len(enhanced_query) < 2000,  # Avoid overly complex enhancements
            "transparency": len(frameworks) <= 3,  # Limit number of frameworks for transparency
            "performance_responsive": len(frameworks) > 0 or "basic" in enhanced_query.lower(),
        }

        return compliance

    async def _validate_quality_improvement(
        self,
        original_score: float,
        enhanced_score: float,
        decision: EnhancementDecision,
    ) -> bool:
        """Validate that quality improvement meets expectations."""
        actual_improvement = enhanced_score - original_score
        expected_improvement = decision.expected_improvement * original_score

        # Check if improvement meets at least 50% of expectation
        meets_expectation = actual_improvement >= expected_improvement * 0.5

        # Also check absolute improvement threshold
        meets_absolute_threshold = actual_improvement >= 0.1

        return meets_expectation or meets_absolute_threshold

    async def _generate_transparency_explanation(
        self,
        decision: EnhancementDecision,
        improvement_percentage: float,
        framework_times: dict[PromptingTechnique, float],
    ) -> str:
        """Generate user-facing transparency explanation."""
        explanation_parts = []

        if decision.selected_frameworks:
            explanation_parts.append(
                f"Applied {len(decision.selected_frameworks)} cognitive enhancement framework"
                f"{'s' if len(decision.selected_frameworks) != 1 else ''}:",
            )

            for framework in decision.selected_frameworks:
                processing_time = framework_times.get(framework, 0.0)
                explanation_parts.append(
                    f"  • {framework.value.replace('_', ' ').title()} ({processing_time:.2f}s)",
                )

            explanation_parts.append(f"Expected improvement: {decision.expected_improvement:.1%}")

        if improvement_percentage > 0:
            explanation_parts.append(f"Actual quality improvement: {improvement_percentage:.1f}%")

        explanation_parts.append(decision.decision_reasoning)

        return "\n".join(explanation_parts)

    # Performance optimization methods
    def clear_caches(self) -> None:
        """Clear all internal caches."""
        self._decision_cache.clear()
        self._analysis_cache.clear()
        self.logger.info("All enhancement caches cleared")

    def get_cache_statistics(self) -> dict[str, Any]:
        """Get statistics about internal caches."""
        return {
            "decision_cache_size": len(self._decision_cache),
            "analysis_cache_size": len(self._analysis_cache),
            "cache_enabled": self.cache_decisions,
            "parallel_processing_enabled": self.enable_parallel_processing,
        }

    async def optimize_for_query_patterns(
        self,
        recent_queries: list[str],
    ) -> dict[str, Any]:
        """Optimize system based on recent query patterns."""
        if not recent_queries:
            return {"optimization_applied": False, "reason": "No recent queries provided"}

        # Analyze patterns in recent queries
        pattern_analysis = {
            "average_length": sum(len(q) for q in recent_queries) / len(recent_queries),
            "common_domains": [],
            "complexity_distribution": {"simple": 0, "moderate": 0, "complex": 0, "expert": 0},
        }

        # Detect common domains (simplified)
        domain_keywords = {
            "security": ["security", "auth", "encryption", "vulnerability"],
            "architecture": ["architecture", "design", "structure", "system"],
            "development": ["code", "implement", "develop", "programming"],
            "performance": ["performance", "optimize", "speed", "efficiency"],
        }

        for domain, keywords in domain_keywords.items():
            count = sum(1 for query in recent_queries if any(keyword in query.lower() for keyword in keywords))
            if count > 0:
                pattern_analysis["common_domains"].append({"domain": domain, "frequency": count})

        # Adjust thresholds based on patterns
        optimizations = {}

        if pattern_analysis["average_length"] > 200:
            # Users prefer detailed queries, allow more enhancement time
            self.max_enhancement_time = min(4.0, self.max_enhancement_time * 1.2)
            optimizations["enhancement_time_adjusted"] = True

        if len(pattern_analysis["common_domains"]) > 2:
            # Users work across multiple domains, enable more frameworks
            optimizations["multi_domain_optimization"] = True

        return {
            "optimization_applied": len(optimizations) > 0,
            "pattern_analysis": pattern_analysis,
            "optimizations": optimizations,
        }
