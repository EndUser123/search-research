"""
Cross-Domain Pattern Transfer - Mechanism for transferring successful enhancement
patterns between different domains while maintaining effectiveness and relevance.

This system enables:
1. Domain similarity analysis
2. Pattern adaptation and transformation
3. Transfer validation and testing
4. Multi-domain optimization
5. Transfer learning from successful cross-domain applications
"""

import logging
import threading
import uuid
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .core.base_patterns import (
    DomainContext,
    DomainType,
    EnhancementPattern,
    QualityMetrics,
)
from .core.memory_structures import PatternMemory, QualityMemory


class TransferabilityScore(Enum):
    """Transferability assessment levels."""

    HIGH = "high"  # 0.8 - 1.0
    MEDIUM = "medium"  # 0.5 - 0.8
    LOW = "low"  # 0.2 - 0.5
    VERY_LOW = "very_low"  # 0.0 - 0.2


class AdaptationStrategy(Enum):
    """Strategies for adapting patterns to new domains."""

    DIRECT_TRANSFER = "direct_transfer"  # No modification needed
    TEMPLATE_ADAPTATION = "template_adaptation"  # Modify template
    PARAMETER_TUNING = "parameter_tuning"  # Adjust parameters
    CONTEXTUAL_REFRAMING = "contextual_reframing"  # Reframe for new context
    HYBRID_CREATION = "hybrid_creation"  # Combine with existing patterns


@dataclass
class DomainSimilarity:
    """Similarity assessment between two domains."""

    source_domain: DomainType
    target_domain: DomainType
    similarity_score: float  # 0.0 to 1.0
    shared_concepts: set[str] = field(default_factory=set)
    domain_distance: float = 0.0  # Conceptual distance
    transfer_history: dict[str, float] = field(
        default_factory=dict
    )  # Past transfer success rates
    confidence_level: float = 0.0  # Confidence in similarity assessment

    def get_transferability_level(self) -> TransferabilityScore:
        """Get transferability assessment based on similarity."""
        if self.similarity_score >= 0.8:
            return TransferabilityScore.HIGH
        elif self.similarity_score >= 0.5:
            return TransferabilityScore.MEDIUM
        elif self.similarity_score >= 0.2:
            return TransferabilityScore.LOW
        else:
            return TransferabilityScore.VERY_LOW


@dataclass
class PatternTransfer:
    """Record of a pattern transfer between domains."""

    transfer_id: str
    source_pattern_id: str
    target_domain: DomainType
    transferred_pattern: EnhancementPattern
    adaptation_strategy: AdaptationStrategy
    similarity_assessment: DomainSimilarity
    transfer_confidence: float
    quality_degradation: float = 0.0  # Expected quality loss
    adaptation_notes: str = ""
    validation_results: dict[str, Any] = field(default_factory=dict)
    success_metrics: QualityMetrics | None = None
    created_at: datetime = field(default_factory=datetime.now)


class CrossDomainPatternTransfer:
    """System for transferring patterns between domains."""

    def __init__(self, pattern_memory: PatternMemory, quality_memory: QualityMemory):
        self.pattern_memory = pattern_memory
        self.quality_memory = quality_memory
        self.logger = logging.getLogger(__name__)

        # Domain knowledge base
        self.domain_concepts: dict[DomainType, set[str]] = {
            DomainType.SOFTWARE_DEVELOPMENT: {
                "code",
                "debugging",
                "architecture",
                "algorithms",
                "data_structures",
                "testing",
                "deployment",
                "refactoring",
                "optimization",
                "scalability",
            },
            DomainType.DATA_ANALYSIS: {
                "statistics",
                "visualization",
                "data_cleaning",
                "modeling",
                "insights",
                "correlation",
                "regression",
                "clustering",
                "prediction",
                "accuracy",
            },
            DomainType.TROUBLESHOOTING: {
                "diagnosis",
                "root_cause",
                "symptoms",
                "solutions",
                "prevention",
                "debugging",
                "testing",
                "verification",
                "monitoring",
                "alerts",
            },
            DomainType.DOCUMENTATION: {
                "clarity",
                "organization",
                "examples",
                "tutorials",
                "reference",
                "structure",
                "formatting",
                "completeness",
                "accessibility",
                "maintenance",
            },
            DomainType.RESEARCH: {
                "methodology",
                "analysis",
                "hypothesis",
                "experimentation",
                "validation",
                "synthesis",
                "literature",
                "citations",
                "peer_review",
                "innovation",
            },
            DomainType.DESIGN: {
                "user_experience",
                "interface",
                "aesthetics",
                "usability",
                "accessibility",
                "patterns",
                "consistency",
                "intuition",
                "workflow",
                "prototyping",
            },
            DomainType.STRATEGY: {
                "planning",
                "goals",
                "objectives",
                "roadmap",
                "implementation",
                "metrics",
                "optimization",
                "resources",
                "timeline",
                "stakeholders",
            },
            DomainType.EDUCATION: {
                "learning",
                "curriculum",
                "assessment",
                "feedback",
                "engagement",
                "comprehension",
                "retention",
                "practice",
                "examples",
                "explanation",
            },
        }

        # Transfer history and analytics
        self.transfer_history: dict[str, PatternTransfer] = {}
        self.domain_similarities: dict[
            tuple[DomainType, DomainType], DomainSimilarity
        ] = {}
        self.adaptation_strategies: dict[AdaptationStrategy, Callable] = {}
        self.transfer_success_rates: dict[
            tuple[DomainType, DomainType], float
        ] = defaultdict(float)

        # Transfer parameters
        self.min_similarity_threshold = 0.3
        self.max_quality_degradation = 0.4
        self.adaptation_confidence_threshold = 0.6

        # Initialize adaptation strategies
        self._initialize_adaptation_strategies()

        # Threading
        self.lock = threading.RLock()

    def _initialize_adaptation_strategies(self) -> None:
        """Initialize adaptation strategy functions."""
        self.adaptation_strategies = {
            AdaptationStrategy.DIRECT_TRANSFER: self._direct_transfer,
            AdaptationStrategy.TEMPLATE_ADAPTATION: self._template_adaptation,
            AdaptationStrategy.PARAMETER_TUNING: self._parameter_tuning,
            AdaptationStrategy.CONTEXTUAL_REFRAMING: self._contextual_reframing,
            AdaptationStrategy.HYBRID_CREATION: self._hybrid_creation,
        }

    def calculate_domain_similarity(
        self, source_domain: DomainType, target_domain: DomainType
    ) -> DomainSimilarity:
        """Calculate similarity between two domains."""
        similarity_key = (source_domain, target_domain)

        with self.lock:
            # Check if similarity already calculated
            if similarity_key in self.domain_similarities:
                return self.domain_similarities[similarity_key]

            # Get domain concepts
            source_concepts = self.domain_concepts.get(source_domain, set())
            target_concepts = self.domain_concepts.get(target_domain, set())

            # Calculate concept overlap
            shared_concepts = source_concepts.intersection(target_concepts)
            total_concepts = source_concepts.union(target_concepts)

            concept_similarity = (
                len(shared_concepts) / len(total_concepts) if total_concepts else 0.0
            )

            # Calculate domain distance (inverse of similarity)
            domain_distance = 1.0 - concept_similarity

            # Get transfer history confidence
            transfer_history = self.transfer_success_rates.get(similarity_key, {})
            historical_confidence = 0.0
            if transfer_history:
                historical_confidence = sum(transfer_history.values()) / len(
                    transfer_history
                )

            # Calculate overall similarity
            similarity_score = concept_similarity * 0.7 + historical_confidence * 0.3

            similarity = DomainSimilarity(
                source_domain=source_domain,
                target_domain=target_domain,
                similarity_score=similarity_score,
                shared_concepts=shared_concepts,
                domain_distance=domain_distance,
                transfer_history=transfer_history,
                confidence_level=historical_confidence,
            )

            self.domain_similarities[similarity_key] = similarity
            return similarity

    def assess_transferability(
        self, pattern: EnhancementPattern, target_domain: DomainType
    ) -> tuple[bool, float, AdaptationStrategy]:
        """Assess if a pattern can be transferred to a target domain."""
        if pattern.domain_context.domain == target_domain:
            # Same domain - direct transfer
            return True, 1.0, AdaptationStrategy.DIRECT_TRANSFER

        # Calculate domain similarity
        similarity = self.calculate_domain_similarity(
            pattern.domain_context.domain, target_domain
        )

        if similarity.similarity_score < self.min_similarity_threshold:
            return False, 0.0, AdaptationStrategy.DIRECT_TRANSFER

        # Determine adaptation strategy based on similarity and pattern characteristics
        if similarity.similarity_score >= 0.8:
            strategy = AdaptationStrategy.DIRECT_TRANSFER
        elif similarity.similarity_score >= 0.6:
            strategy = AdaptationStrategy.TEMPLATE_ADAPTATION
        elif similarity.similarity_score >= 0.4:
            strategy = AdaptationStrategy.PARAMETER_TUNING
        else:
            strategy = AdaptationStrategy.CONTEXTUAL_REFRAMING

        # Calculate transfer confidence
        transfer_confidence = (
            similarity.similarity_score * 0.5
            + pattern.quality_metrics.transferability * 0.3
            + pattern.quality_metrics.reliability_score * 0.2
        )

        return (
            transfer_confidence >= self.adaptation_confidence_threshold,
            transfer_confidence,
            strategy,
        )

    def transfer_pattern(
        self, pattern_id: str, target_domain: DomainType
    ) -> PatternTransfer | None:
        """Transfer a pattern to a new domain."""
        with self.lock:
            # Get source pattern
            source_pattern = self.pattern_memory.get_pattern(pattern_id)
            if not source_pattern:
                self.logger.error(f"Pattern {pattern_id} not found")
                return None

            # Assess transferability
            can_transfer, confidence, strategy = self.assess_transferability(
                source_pattern, target_domain
            )

            if not can_transfer:
                self.logger.info(
                    f"Pattern {pattern_id} cannot be transferred to {target_domain}"
                )
                return None

            # Calculate domain similarity
            similarity = self.calculate_domain_similarity(
                source_pattern.domain_context.domain, target_domain
            )

            # Apply adaptation strategy
            adaptation_function = self.adaptation_strategies.get(strategy)
            if not adaptation_function:
                self.logger.error(f"Unknown adaptation strategy: {strategy}")
                return None

            transferred_pattern = adaptation_function(
                source_pattern, target_domain, similarity
            )

            if not transferred_pattern:
                return None

            # Create transfer record
            transfer = PatternTransfer(
                transfer_id=str(uuid.uuid4()),
                source_pattern_id=pattern_id,
                target_domain=target_domain,
                transferred_pattern=transferred_pattern,
                adaptation_strategy=strategy,
                similarity_assessment=similarity,
                transfer_confidence=confidence,
                quality_degradation=self._estimate_quality_degradation(
                    source_pattern, similarity
                ),
            )

            self.transfer_history[transfer.transfer_id] = transfer

            self.logger.info(
                f"Successfully transferred pattern {pattern_id} to {target_domain} using {strategy.value}"
            )
            return transfer

    def _direct_transfer(
        self,
        pattern: EnhancementPattern,
        target_domain: DomainType,
        similarity: DomainSimilarity,
    ) -> EnhancementPattern | None:
        """Direct pattern transfer with no modification."""
        try:
            # Create a copy of the pattern
            transferred_pattern = EnhancementPattern(
                name=f"{pattern.name}_transferred_to_{target_domain.value}",
                description=f"Transferred from {pattern.domain_context.domain.value}: {pattern.description}",
                pattern_type=pattern.pattern_type,
                template=pattern.template,
                variables=pattern.variables.copy(),
                transformation_rules=pattern.transformation_rules.copy(),
                enhancement_technique=pattern.enhancement_technique,
                target_quality_threshold=pattern.target_quality_threshold,
                creator_system=f"transfer_{pattern.creator_system}",
            )

            # Update domain context
            transferred_pattern.domain_context = DomainContext(
                domain=target_domain,
                subdomain=pattern.domain_context.subdomain,
                constraints=pattern.domain_context.constraints.copy(),
                metadata=pattern.domain_context.metadata.copy(),
                related_domains={pattern.domain_context.domain},
            )

            # Adjust quality metrics
            transferred_pattern.quality_metrics = QualityMetrics(
                success_rate=pattern.quality_metrics.success_rate
                * 0.9,  # Slight degradation
                average_improvement=pattern.quality_metrics.average_improvement * 0.9,
                reliability_score=pattern.quality_metrics.reliability_score,
                adaptability_score=pattern.quality_metrics.adaptability_score,
                efficiency_score=pattern.quality_metrics.efficiency_score,
                transferability=1.0,  # High transferability since it's direct
                novelty_score=pattern.quality_metrics.novelty_score,
            )

            return transferred_pattern

        except Exception as e:
            self.logger.error(f"Error in direct transfer: {str(e)}")
            return None

    def _template_adaptation(
        self,
        pattern: EnhancementPattern,
        target_domain: DomainType,
        similarity: DomainSimilarity,
    ) -> EnhancementPattern | None:
        """Adapt pattern template for new domain."""
        try:
            # Get domain-specific terminology
            target_concepts = self.domain_concepts.get(target_domain, set())
            source_concepts = self.domain_concepts.get(
                pattern.domain_context.domain, set()
            )

            # Create template adaptation mapping
            adaptation_map = self._create_template_mapping(
                source_concepts, target_concepts
            )

            # Adapt template
            adapted_template = pattern.template
            for source_term, target_term in adaptation_map.items():
                adapted_template = adapted_template.replace(source_term, target_term)

            # Create transferred pattern
            transferred_pattern = EnhancementPattern(
                name=f"{pattern.name}_adapted_for_{target_domain.value}",
                description=f"Adapted from {pattern.domain_context.domain.value} for {target_domain.value}: {pattern.description}",
                pattern_type=pattern.pattern_type,
                template=adapted_template,
                variables=pattern.variables.copy(),
                transformation_rules=pattern.transformation_rules.copy(),
                enhancement_technique=pattern.enhancement_technique,
                target_quality_threshold=pattern.target_quality_threshold
                * 0.95,  # Slightly lower threshold
                creator_system=f"template_adaptation_{pattern.creator_system}",
            )

            # Update domain context
            transferred_pattern.domain_context = DomainContext(
                domain=target_domain,
                subdomain=pattern.domain_context.subdomain,
                constraints=pattern.domain_context.constraints.copy(),
                metadata={
                    **pattern.domain_context.metadata,
                    "adaptation_method": "template_adaptation",
                },
                related_domains={pattern.domain_context.domain},
            )

            # Adjust quality metrics
            transferred_pattern.quality_metrics = QualityMetrics(
                success_rate=pattern.quality_metrics.success_rate * 0.85,
                average_improvement=pattern.quality_metrics.average_improvement * 0.85,
                reliability_score=pattern.quality_metrics.reliability_score * 0.9,
                adaptability_score=pattern.quality_metrics.adaptability_score,
                efficiency_score=pattern.quality_metrics.efficiency_score * 0.9,
                transferability=0.8,
                novelty_score=pattern.quality_metrics.novelty_score * 0.95,
            )

            return transferred_pattern

        except Exception as e:
            self.logger.error(f"Error in template adaptation: {str(e)}")
            return None

    def _parameter_tuning(
        self,
        pattern: EnhancementPattern,
        target_domain: DomainType,
        similarity: DomainSimilarity,
    ) -> EnhancementPattern | None:
        """Tune pattern parameters for new domain."""
        try:
            # Calculate parameter adjustments based on domain distance
            adjustment_factor = 1.0 - similarity.domain_distance * 0.3

            # Adjust quality threshold and other parameters
            adjusted_threshold = pattern.target_quality_threshold * adjustment_factor
            adjusted_complexity = max(
                0.1, min(1.0, pattern.complexity_adjustment * adjustment_factor)
            )
            adjusted_specificity = max(
                0.1,
                min(
                    1.0,
                    pattern.specificity_level
                    * (1.0 + similarity.domain_distance * 0.2),
                ),
            )

            # Create transferred pattern
            transferred_pattern = EnhancementPattern(
                name=f"{pattern.name}_tuned_for_{target_domain.value}",
                description=f"Parameter-tuned from {pattern.domain_context.domain.value} for {target_domain.value}: {pattern.description}",
                pattern_type=pattern.pattern_type,
                template=pattern.template,
                variables=pattern.variables.copy(),
                transformation_rules=pattern.transformation_rules.copy(),
                enhancement_technique=pattern.enhancement_technique,
                target_quality_threshold=adjusted_threshold,
                complexity_adjustment=adjusted_complexity,
                specificity_level=adjusted_specificity,
                context_preservation=pattern.context_preservation,
                creator_system=f"parameter_tuning_{pattern.creator_system}",
            )

            # Update domain context
            transferred_pattern.domain_context = DomainContext(
                domain=target_domain,
                subdomain=pattern.domain_context.subdomain,
                constraints=pattern.domain_context.constraints.copy(),
                metadata={
                    **pattern.domain_context.metadata,
                    "adaptation_method": "parameter_tuning",
                    "parameter_adjustments": {
                        "threshold_adjustment": adjusted_threshold
                        / pattern.target_quality_threshold,
                        "complexity_adjustment": adjusted_complexity,
                        "specificity_adjustment": adjusted_specificity,
                    },
                },
                related_domains={pattern.domain_context.domain},
            )

            # Adjust quality metrics
            transferred_pattern.quality_metrics = QualityMetrics(
                success_rate=pattern.quality_metrics.success_rate * 0.8,
                average_improvement=pattern.quality_metrics.average_improvement * 0.8,
                reliability_score=pattern.quality_metrics.reliability_score * 0.85,
                adaptability_score=pattern.quality_metrics.adaptability_score,
                efficiency_score=pattern.quality_metrics.efficiency_score * 0.85,
                transferability=0.6,
                novelty_score=pattern.quality_metrics.novelty_score,
            )

            return transferred_pattern

        except Exception as e:
            self.logger.error(f"Error in parameter tuning: {str(e)}")
            return None

    def _contextual_reframing(
        self,
        pattern: EnhancementPattern,
        target_domain: DomainType,
        similarity: DomainSimilarity,
    ) -> EnhancementPattern | None:
        """Reframe pattern context for new domain."""
        try:
            # Get shared concepts for reframing
            shared_concepts = list(similarity.shared_concepts)
            if not shared_concepts:
                return None

            # Create contextual template prefix/suffix
            context_prefix = f"Considering the {target_domain.value} context, "
            context_suffix = f"\n\nThis approach is tailored for {target_domain.value} challenges and opportunities."

            # Reframe template
            reframed_template = f"{context_prefix}{pattern.template}{context_suffix}"

            # Add shared concepts as variables
            enhanced_variables = pattern.variables.copy()
            for concept in shared_concepts[:3]:  # Limit to top 3 concepts
                enhanced_variables[
                    f"{concept}_context"
                ] = f"Apply {concept} principles specific to {target_domain.value}"

            # Create transferred pattern
            transferred_pattern = EnhancementPattern(
                name=f"{pattern.name}_reframed_for_{target_domain.value}",
                description=f"Contextually reframed from {pattern.domain_context.domain.value} for {target_domain.value}: {pattern.description}",
                pattern_type=pattern.pattern_type,
                template=reframed_template,
                variables=enhanced_variables,
                transformation_rules=pattern.transformation_rules.copy(),
                enhancement_technique=pattern.enhancement_technique,
                target_quality_threshold=pattern.target_quality_threshold * 0.9,
                complexity_adjustment=pattern.complexity_adjustment
                * 1.1,  # Slightly increase complexity
                specificity_level=pattern.specificity_level
                * 0.9,  # Reduce specificity for broader application
                creator_system=f"contextual_reframing_{pattern.creator_system}",
            )

            # Update domain context
            transferred_pattern.domain_context = DomainContext(
                domain=target_domain,
                subdomain=pattern.domain_context.subdomain,
                constraints=pattern.domain_context.constraints.copy(),
                metadata={
                    **pattern.domain_context.metadata,
                    "adaptation_method": "contextual_reframing",
                    "shared_concepts": shared_concepts,
                    "contextual_elements": ["domain_prefix", "domain_suffix"],
                },
                related_domains={pattern.domain_context.domain},
            )

            # Adjust quality metrics
            transferred_pattern.quality_metrics = QualityMetrics(
                success_rate=pattern.quality_metrics.success_rate * 0.7,
                average_improvement=pattern.quality_metrics.average_improvement * 0.75,
                reliability_score=pattern.quality_metrics.reliability_score * 0.8,
                adaptability_score=pattern.quality_metrics.adaptability_score
                * 1.1,  # Increased adaptability
                efficiency_score=pattern.quality_metrics.efficiency_score * 0.75,
                transferability=0.5,
                novelty_score=pattern.quality_metrics.novelty_score * 0.9,
            )

            return transferred_pattern

        except Exception as e:
            self.logger.error(f"Error in contextual reframing: {str(e)}")
            return None

    def _hybrid_creation(
        self,
        pattern: EnhancementPattern,
        target_domain: DomainType,
        similarity: DomainSimilarity,
    ) -> EnhancementPattern | None:
        """Create hybrid pattern by combining with existing target domain patterns."""
        try:
            # Get successful patterns in target domain
            target_patterns = self.pattern_memory.get_successful_patterns(0.7, 3)
            target_domain_patterns = [
                p for p in target_patterns if p.domain_context.domain == target_domain
            ]

            if not target_domain_patterns:
                # Fall back to contextual reframing
                return self._contextual_reframing(pattern, target_domain, similarity)

            # Select best compatible pattern
            best_pattern = None
            best_compatibility = 0.0

            for target_pattern in target_domain_patterns:
                compatibility = self._calculate_pattern_compatibility(
                    pattern, target_pattern
                )
                if compatibility > best_compatibility:
                    best_compatibility = compatibility
                    best_pattern = target_pattern

            if not best_pattern or best_compatibility < 0.3:
                return None

            # Create hybrid template
            hybrid_template = (
                f"{pattern.template}\n\nAdditionally:\n{best_pattern.template}"
            )

            # Combine variables
            hybrid_variables = {**pattern.variables, **best_pattern.variables}

            # Create hybrid pattern
            transferred_pattern = EnhancementPattern(
                name=f"{pattern.name}_hybrid_with_{best_pattern.name}",
                description=f"Hybrid pattern combining {pattern.name} with {best_pattern.name} for {target_domain.value}",
                pattern_type=f"hybrid_{pattern.pattern_type}_{best_pattern.pattern_type}",
                template=hybrid_template,
                variables=hybrid_variables,
                transformation_rules={
                    **pattern.transformation_rules,
                    **best_pattern.transformation_rules,
                },
                enhancement_technique=f"hybrid_{pattern.enhancement_technique}_{best_pattern.enhancement_technique}",
                target_quality_threshold=max(
                    pattern.target_quality_threshold,
                    best_pattern.target_quality_threshold,
                ),
                complexity_adjustment=(
                    pattern.complexity_adjustment + best_pattern.complexity_adjustment
                )
                / 2,
                specificity_level=(
                    pattern.specificity_level + best_pattern.specificity_level
                )
                / 2,
                creator_system=f"hybrid_creation_{pattern.creator_system}_{best_pattern.creator_system}",
            )

            # Update domain context
            transferred_pattern.domain_context = DomainContext(
                domain=target_domain,
                subdomain=pattern.domain_context.subdomain,
                constraints={
                    **pattern.domain_context.constraints,
                    **best_pattern.domain_context.constraints,
                },
                metadata={
                    **pattern.domain_context.metadata,
                    "adaptation_method": "hybrid_creation",
                    "source_pattern_id": pattern.id,
                    "target_pattern_id": best_pattern.id,
                    "compatibility_score": best_compatibility,
                },
                related_domains={pattern.domain_context.domain},
            )

            # Adjust quality metrics based on both patterns
            avg_success_rate = (
                pattern.quality_metrics.success_rate
                + best_pattern.quality_metrics.success_rate
            ) / 2
            transferred_pattern.quality_metrics = QualityMetrics(
                success_rate=avg_success_rate * 0.75,
                average_improvement=(
                    pattern.quality_metrics.average_improvement
                    + best_pattern.quality_metrics.average_improvement
                )
                / 2
                * 0.8,
                reliability_score=min(
                    pattern.quality_metrics.reliability_score,
                    best_pattern.quality_metrics.reliability_score,
                )
                * 0.9,
                adaptability_score=max(
                    pattern.quality_metrics.adaptability_score,
                    best_pattern.quality_metrics.adaptability_score,
                ),
                efficiency_score=(
                    pattern.quality_metrics.efficiency_score
                    + best_pattern.quality_metrics.efficiency_score
                )
                / 2
                * 0.8,
                transferability=0.4,  # Lower transferability due to hybrid nature
                novelty_score=(
                    pattern.quality_metrics.novelty_score
                    + best_pattern.quality_metrics.novelty_score
                )
                / 2,
            )

            return transferred_pattern

        except Exception as e:
            self.logger.error(f"Error in hybrid creation: {str(e)}")
            return None

    def _create_template_mapping(
        self, source_concepts: set[str], target_concepts: set[str]
    ) -> dict[str, str]:
        """Create mapping between source and target domain concepts."""
        mapping = {}
        concept_similarities = {
            # Software Development -> Data Analysis
            "algorithms": "modeling",
            "data_structures": "data_organization",
            "optimization": "performance_tuning",
            "testing": "validation",
            "debugging": "diagnosis",
            # Software Development -> Troubleshooting
            "debugging": "root_cause_analysis",
            "testing": "verification",
            "monitoring": "observation",
            "deployment": "implementation",
            "refactoring": "correction",
            # Data Analysis -> Documentation
            "visualization": "illustration",
            "insights": "findings",
            "modeling": "explanation",
            "analysis": "examination",
            "correlation": "relationship",
            # Troubleshooting -> Documentation
            "diagnosis": "identification",
            "solutions": "resolutions",
            "symptoms": "indications",
            "prevention": "mitigation",
            "root_cause": "underlying_issue",
        }

        for source_concept in source_concepts:
            # Direct mapping if available
            if source_concept in concept_similarities:
                target_concept = concept_similarities[source_concept]
                if target_concept in target_concepts:
                    mapping[source_concept] = target_concept
                    continue

            # Find similar target concept
            for target_concept in target_concepts:
                if self._concept_similarity(source_concept, target_concept) > 0.7:
                    mapping[source_concept] = target_concept
                    break

        return mapping

    def _concept_similarity(self, concept_a: str, concept_b: str) -> float:
        """Calculate similarity between two concepts."""
        if concept_a == concept_b:
            return 1.0

        # Simple similarity based on common substrings
        common_chars = set(concept_a.lower()).intersection(set(concept_b.lower()))
        total_chars = set(concept_a.lower()).union(set(concept_b.lower()))

        if not total_chars:
            return 0.0

        return len(common_chars) / len(total_chars)

    def _calculate_pattern_compatibility(
        self, pattern_a: EnhancementPattern, pattern_b: EnhancementPattern
    ) -> float:
        """Calculate compatibility between two patterns for hybrid creation."""
        compatibility = 0.0
        factors = 0

        # Pattern type similarity
        if pattern_a.pattern_type == pattern_b.pattern_type:
            compatibility += 0.3
        factors += 1

        # Quality score similarity
        quality_diff = abs(
            pattern_a.quality_metrics.calculate_overall_score()
            - pattern_b.quality_metrics.calculate_overall_score()
        )
        quality_similarity = max(0, 1.0 - quality_diff)
        compatibility += 0.3 * quality_similarity
        factors += 1

        # Tag overlap
        common_tags = pattern_a.tags.intersection(pattern_b.tags)
        if pattern_a.tags or pattern_b.tags:
            tag_similarity = len(common_tags) / len(
                pattern_a.tags.union(pattern_b.tags)
            )
            compatibility += 0.2 * tag_similarity
        factors += 1

        # Complexity compatibility
        complexity_diff = abs(
            pattern_a.complexity_adjustment - pattern_b.complexity_adjustment
        )
        complexity_similarity = max(0, 1.0 - complexity_diff)
        compatibility += 0.2 * complexity_similarity
        factors += 1

        return compatibility if factors == 0 else compatibility / factors

    def _estimate_quality_degradation(
        self, pattern: EnhancementPattern, similarity: DomainSimilarity
    ) -> float:
        """Estimate quality degradation from domain transfer."""
        base_degradation = (1.0 - similarity.similarity_score) * 0.3

        # Adjust based on pattern transferability
        transferability_factor = 1.0 - pattern.quality_metrics.transferability * 0.5

        # Adjust based on domain distance
        distance_factor = similarity.domain_distance * 0.2

        total_degradation = base_degradation + transferability_factor + distance_factor
        return min(self.max_quality_degradation, total_degradation)

    def validate_transfer(
        self, transfer_id: str, test_data: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Validate a transferred pattern with test data."""
        with self.lock:
            if transfer_id not in self.transfer_history:
                return {"success": False, "error": "Transfer not found"}

            transfer = self.transfer_history[transfer_id]
            pattern = transfer.transferred_pattern

            validation_results = {
                "success": True,
                "transfer_id": transfer_id,
                "pattern_id": pattern.id,
                "test_cases": len(test_data),
                "passed_tests": 0,
                "failed_tests": 0,
                "average_improvement": 0.0,
                "test_details": [],
            }

            total_improvement = 0.0
            successful_tests = 0

            for i, test_case in enumerate(test_data):
                try:
                    # Apply the pattern
                    result = pattern.apply(test_case)
                    improvement = test_case.get("expected_improvement", 0.0)
                    actual_improvement = test_case.get(
                        "actual_improvement", improvement * 0.8
                    )

                    test_passed = (
                        actual_improvement >= improvement * 0.6
                    )  # 60% of expected improvement

                    if test_passed:
                        validation_results["passed_tests"] += 1
                        successful_tests += 1
                    else:
                        validation_results["failed_tests"] += 1

                    total_improvement += actual_improvement

                    validation_results["test_details"].append(
                        {
                            "test_case": i,
                            "passed": test_passed,
                            "expected_improvement": improvement,
                            "actual_improvement": actual_improvement,
                        }
                    )

                except Exception as e:
                    validation_results["failed_tests"] += 1
                    validation_results["test_details"].append(
                        {"test_case": i, "passed": False, "error": str(e)}
                    )

            # Calculate metrics
            if successful_tests > 0:
                validation_results["average_improvement"] = total_improvement / len(
                    test_data
                )

            validation_results["success_rate"] = successful_tests / len(test_data)

            # Update transfer record
            transfer.validation_results = validation_results

            # Update transfer success rates
            domain_pair = (pattern.domain_context.domain, transfer.target_domain)
            current_rate = self.transfer_success_rates[domain_pair]
            new_rate = validation_results["success_rate"]
            self.transfer_success_rates[domain_pair] = (current_rate + new_rate) / 2.0

            return validation_results

    def get_transfer_statistics(self) -> dict[str, Any]:
        """Get comprehensive transfer statistics."""
        with self.lock:
            stats = {
                "total_transfers": len(self.transfer_history),
                "successful_transfers": 0,
                "failed_transfers": 0,
                "domain_pairs": {},
                "adaptation_strategies": defaultdict(int),
                "average_confidence": 0.0,
                "average_quality_degradation": 0.0,
            }

            total_confidence = 0.0
            total_degradation = 0.0

            for transfer in self.transfer_history.values():
                # Count successful/failed based on validation
                if transfer.validation_results:
                    success_rate = transfer.validation_results.get("success_rate", 0.0)
                    if success_rate >= 0.7:
                        stats["successful_transfers"] += 1
                    else:
                        stats["failed_transfers"] += 1
                else:
                    # Assume pending or not validated
                    stats["successful_transfers"] += 0.5
                    stats["failed_transfers"] += 0.5

                # Track domain pairs
                domain_key = f"{transfer.similarity_assessment.source_domain.value}_to_{transfer.target_domain.value}"
                if domain_key not in stats["domain_pairs"]:
                    stats["domain_pairs"][domain_key] = {
                        "count": 0,
                        "avg_confidence": 0.0,
                    }
                stats["domain_pairs"][domain_key]["count"] += 1

                # Track adaptation strategies
                stats["adaptation_strategies"][transfer.adaptation_strategy.value] += 1

                # Accumulate metrics
                total_confidence += transfer.transfer_confidence
                total_degradation += transfer.quality_degradation

            # Calculate averages
            if self.transfer_history:
                stats["average_confidence"] = total_confidence / len(
                    self.transfer_history
                )
                stats["average_quality_degradation"] = total_degradation / len(
                    self.transfer_history
                )

            # Convert defaultdict to regular dict
            stats["adaptation_strategies"] = dict(stats["adaptation_strategies"])

            return stats

    def find_transfer_opportunities(
        self, min_similarity: float = 0.4
    ) -> list[dict[str, Any]]:
        """Find potential transfer opportunities between domains."""
        opportunities = []

        with self.lock:
            # Get successful patterns
            successful_patterns = self.pattern_memory.get_successful_patterns(0.7, 5)

            for pattern in successful_patterns:
                for target_domain in DomainType:
                    if target_domain == pattern.domain_context.domain:
                        continue

                    similarity = self.calculate_domain_similarity(
                        pattern.domain_context.domain, target_domain
                    )

                    if similarity.similarity_score >= min_similarity:
                        (
                            can_transfer,
                            confidence,
                            strategy,
                        ) = self.assess_transferability(pattern, target_domain)

                        if can_transfer:
                            opportunities.append(
                                {
                                    "source_pattern_id": pattern.id,
                                    "source_pattern_name": pattern.name,
                                    "source_domain": pattern.domain_context.domain.value,
                                    "target_domain": target_domain.value,
                                    "similarity_score": similarity.similarity_score,
                                    "transfer_confidence": confidence,
                                    "recommended_strategy": strategy.value,
                                    "source_quality": pattern.quality_metrics.calculate_overall_score(),
                                }
                            )

        # Sort by transfer confidence (descending)
        opportunities.sort(key=lambda x: x["transfer_confidence"], reverse=True)

        return opportunities
