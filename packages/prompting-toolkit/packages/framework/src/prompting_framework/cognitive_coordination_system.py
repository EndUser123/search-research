from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .base_prompting_technique import BasePromptingTechnique
from .context_models import PromptingTechnique

"""Cognitive Coordination System for Advanced Technique Integration

Provides intelligent coordination between QueryFanoutTechnique and other cognitive
enhancement techniques including SocraticMethod, Chain-of-Verification, and Self-Refine.

Key Features:
- Intelligent technique selection and coordination
- Conflict resolution between techniques
- Performance optimization for multi-technique applications
- Constitutional compliance validation across techniques
- Integration with existing CSF prompting framework
"""





class CoordinationMode(Enum):
    """Coordination modes for technique combination."""

    SEQUENTIAL = "sequential"  # Apply techniques one after another
    PARALLEL = "parallel"  # Apply techniques in parallel
    HIERARCHICAL = "hierarchical"  # Layered application with priority
    ADAPTIVE = "adaptive"  # Dynamic selection based on context


class ConflictResolutionStrategy(Enum):
    """Strategies for resolving conflicts between techniques."""

    PRIORITY_BASED = "priority_based"  # Use technique with higher priority
    MERGE = "merge"  # Merge conflicting instructions
    VETO = "veto"  # Allow techniques to veto each other
    COMPROMISE = "compromise"  # Find middle ground


@dataclass
class TechniqueCoordinationRequest:
    """Request for coordinating multiple techniques."""

    primary_technique: PromptingTechnique
    secondary_techniques: list[PromptingTechnique]
    coordination_mode: CoordinationMode
    conflict_resolution: ConflictResolutionStrategy
    performance_budget: dict[str, float]
    constitutional_requirements: dict[str, Any]


@dataclass
class TechniqueCoordinationResult:
    """Result from technique coordination process."""

    coordinated_techniques: list[PromptingTechnique]
    application_order: list[PromptingTechnique]
    conflict_resolutions: dict[str, Any]
    performance_estimate: dict[str, float]
    constitutional_compliance: dict[str, bool]
    coordination_metadata: dict[str, Any]


@dataclass
class TechniqueInteraction:
    """Represents interaction between two techniques."""

    technique1: PromptingTechnique
    technique2: PromptingTechnique
    interaction_type: str  # "complementary", "conflicting", "redundant", "enhancing"
    strength: float  # -1.0 (high conflict) to 1.0 (high enhancement)
    description: str
    resolution_strategy: ConflictResolutionStrategy | None


class CognitiveCoordinationSystem:
    """
    Advanced Cognitive Coordination System

    Provides intelligent coordination between QueryFanoutTechnique and other
    cognitive enhancement techniques for optimal prompt enhancement.

    Capabilities:
    - Technique interaction analysis and compatibility assessment
    - Conflict detection and resolution
    - Performance optimization for multi-technique applications
    - Constitutional compliance validation
    - Adaptive coordination based on query complexity and constraints
    """

    def __init__(self):
        """Initialize CognitiveCoordinationSystem."""
        self.logger = logging.getLogger(__name__)

        # Technique compatibility matrix
        self._initialize_technique_interactions()

        # Coordination strategies
        self.coordination_strategies = {
            CoordinationMode.SEQUENTIAL: self._apply_sequential_coordination,
            CoordinationMode.PARALLEL: self._apply_parallel_coordination,
            CoordinationMode.HIERARCHICAL: self._apply_hierarchical_coordination,
            CoordinationMode.ADAPTIVE: self._apply_adaptive_coordination,
        }

        # Performance tracking
        self.coordination_history = []
        self.performance_metrics = {}

    def _initialize_technique_interactions(self) -> None:
        """Initialize technique interaction matrix."""
        self.technique_interactions = [
            # QueryFanout + Socratic (highly complementary)
            TechniqueInteraction(
                technique1=PromptingTechnique.QUERY_FANOUT,
                technique2=PromptingTechnique.SOCRATIC,
                interaction_type="complementary",
                strength=0.9,
                description="QueryFanout provides breadth while Socratic provides depth",
                resolution_strategy=ConflictResolutionStrategy.MERGE,
            ),
            # QueryFanout + Self-Refine (enhancing)
            TechniqueInteraction(
                technique1=PromptingTechnique.QUERY_FANOUT,
                technique2=PromptingTechnique.SELF_REFINE,
                interaction_type="enhancing",
                strength=0.8,
                description="QueryFanout generates questions, Self-Refine iteratively improves answers",
                resolution_strategy=ConflictResolutionStrategy.PRIORITY_BASED,
            ),
            # QueryFanout + Chain-of-Verification (complementary)
            TechniqueInteraction(
                technique1=PromptingTechnique.QUERY_FANOUT,
                technique2=PromptingTechnique.CHAIN_OF_VERIFICATION,
                interaction_type="complementary",
                strength=0.7,
                description="QueryFanout explores aspects, CoV verifies each aspect",
                resolution_strategy=ConflictResolutionStrategy.MERGE,
            ),
            # Socratic + Self-Refine (enhancing)
            TechniqueInteraction(
                technique1=PromptingTechnique.SOCRATIC,
                technique2=PromptingTechnique.SELF_REFINE,
                interaction_type="enhancing",
                strength=0.85,
                description="Socratic questioning followed by iterative refinement",
                resolution_strategy=ConflictResolutionStrategy.PRIORITY_BASED,
            ),
            # Self-Refine + Chain-of-Verification (complementary)
            TechniqueInteraction(
                technique1=PromptingTechnique.SELF_REFINE,
                technique2=PromptingTechnique.CHAIN_OF_VERIFICATION,
                interaction_type="complementary",
                strength=0.75,
                description="Refinement followed by verification of improvements",
                resolution_strategy=ConflictResolutionStrategy.PRIORITY_BASED,
            ),
        ]

    async def coordinate_techniques(
        self,
        request: TechniqueCoordinationRequest,
        available_techniques: dict[PromptingTechnique, BasePromptingTechnique],
    ) -> TechniqueCoordinationResult:
        """
        Coordinate multiple techniques for optimal prompt enhancement.

        Args:
        ----
            request: Coordination request with techniques and preferences
            available_techniques: Dictionary of available technique instances

        Returns:
        -------
            Coordination result with optimized technique application plan

        """
        start_time = time.time()

        try:
            # Analyze technique interactions
            interactions = self._analyze_technique_interactions(request)

            # Detect and resolve conflicts
            resolved_conflicts = await self._resolve_conflicts(
                interactions,
                request.conflict_resolution,
            )

            # Select coordination strategy
            coordination_strategy = self._select_coordination_strategy(request, interactions)

            # Generate coordination plan
            coordination_plan = await coordination_strategy(request, available_techniques, interactions)

            # Validate constitutional compliance
            compliance = await self._validate_constitutional_compliance(
                coordination_plan,
                request.constitutional_requirements,
            )

            # Estimate performance impact
            performance_estimate = self._estimate_performance_impact(coordination_plan, request)

            # Create result
            result = TechniqueCoordinationResult(
                coordinated_techniques=[request.primary_technique] + request.secondary_techniques,
                application_order=coordination_plan,
                conflict_resolutions=resolved_conflicts,
                performance_estimate=performance_estimate,
                constitutional_compliance=compliance,
                coordination_metadata={
                    "coordination_mode": request.coordination_mode.value,
                    "interaction_strength": self._calculate_overall_interaction_strength(interactions),
                    "processing_time": time.time() - start_time,
                },
            )

            # Update coordination history
            self._update_coordination_history(request, result)

            return result

        except Exception as e:
            self.logger.error(f"Technique coordination failed: {e!s}")
            # Return fallback coordination
            return self._create_fallback_coordination(request)

    def _analyze_technique_interactions(
        self,
        request: TechniqueCoordinationRequest,
    ) -> list[TechniqueInteraction]:
        """Analyze interactions between techniques in the request."""
        interactions = []
        all_techniques = [request.primary_technique] + request.secondary_techniques

        # Find interactions between all technique pairs
        for i, tech1 in enumerate(all_techniques):
            for tech2 in all_techniques[i + 1 :]:
                interaction = self._find_technique_interaction(tech1, tech2)
                if interaction:
                    interactions.append(interaction)

        return interactions

    def _find_technique_interaction(
        self,
        tech1: PromptingTechnique,
        tech2: PromptingTechnique,
    ) -> TechniqueInteraction | None:
        """Find interaction between two techniques."""
        for interaction in self.technique_interactions:
            if (interaction.technique1 == tech1 and interaction.technique2 == tech2) or (
                interaction.technique1 == tech2 and interaction.technique2 == tech1
            ):
                return interaction

        # Default interaction for unknown combinations
        return TechniqueInteraction(
            technique1=tech1,
            technique2=tech2,
            interaction_type="neutral",
            strength=0.0,
            description="No predefined interaction",
            resolution_strategy=ConflictResolutionStrategy.PRIORITY_BASED,
        )

    async def _resolve_conflicts(
        self,
        interactions: list[TechniqueInteraction],
        resolution_strategy: ConflictResolutionStrategy,
    ) -> dict[str, Any]:
        """Resolve conflicts between techniques based on strategy."""
        conflicts = [i for i in interactions if i.interaction_type == "conflicting" or i.strength < -0.3]

        if not conflicts:
            return {"conflicts_detected": 0, "resolutions": []}

        resolutions = []
        for conflict in conflicts:
            resolution = await self._resolve_single_conflict(conflict, resolution_strategy)
            resolutions.append(resolution)

        return {
            "conflicts_detected": len(conflicts),
            "resolutions": resolutions,
            "strategy_used": resolution_strategy.value,
        }

    async def _resolve_single_conflict(
        self,
        conflict: TechniqueInteraction,
        strategy: ConflictResolutionStrategy,
    ) -> dict[str, Any]:
        """Resolve a single conflict between techniques."""
        if strategy == ConflictResolutionStrategy.PRIORITY_BASED:
            # Use QueryFanout as priority for conflict with Socratic
            winner = (
                conflict.technique1 if conflict.technique1 == PromptingTechnique.QUERY_FANOUT else conflict.technique2
            )
            return {
                "conflict": f"{conflict.technique1.value} vs {conflict.technique2.value}",
                "resolution": f"Prioritized {winner.value}",
                "winner": winner.value,
                "loser": (conflict.technique1 if winner == conflict.technique2 else conflict.technique2).value,
            }

        if strategy == ConflictResolutionStrategy.MERGE:
            return {
                "conflict": f"{conflict.technique1.value} vs {conflict.technique2.value}",
                "resolution": "Merged conflicting instructions",
                "approach": "Combined complementary aspects",
            }

        if strategy == ConflictResolutionStrategy.COMPROMISE:
            return {
                "conflict": f"{conflict.technique1.value} vs {conflict.technique2.value}",
                "resolution": "Applied both techniques with reduced intensity",
                "approach": "50% intensity each",
            }

        # VETO
        return {
            "conflict": f"{conflict.technique1.value} vs {conflict.technique2.value}",
            "resolution": "Conflicting techniques vetoed each other",
            "result": "Removed conflicting techniques",
        }

    def _select_coordination_strategy(
        self,
        request: TechniqueCoordinationRequest,
        interactions: list[TechniqueInteraction],
    ) -> callable:
        """Select optimal coordination strategy based on request and interactions."""
        if request.coordination_mode != CoordinationMode.ADAPTIVE:
            return self.coordination_strategies[request.coordination_mode]

        # Adaptive strategy selection
        avg_strength = sum(abs(i.strength) for i in interactions) / len(interactions) if interactions else 0

        if avg_strength > 0.7:  # High positive interactions
            return self.coordination_strategies[CoordinationMode.PARALLEL]
        if avg_strength < -0.3:  # High conflicts
            return self.coordination_strategies[CoordinationMode.SEQUENTIAL]
        return self.coordination_strategies[CoordinationMode.HIERARCHICAL]

    async def _apply_sequential_coordination(
        self,
        request: TechniqueCoordinationRequest,
        available_techniques: dict[PromptingTechnique, BasePromptingTechnique],
        interactions: list[TechniqueInteraction],
    ) -> list[PromptingTechnique]:
        """Apply techniques sequentially."""
        # Start with primary technique
        application_order = [request.primary_technique]

        # Add secondary techniques in order of interaction strength
        secondary_with_strength = []
        for tech in request.secondary_techniques:
            strength = self._get_interaction_strength(request.primary_technique, tech, interactions)
            secondary_with_strength.append((tech, strength))

        # Sort by strength (descending)
        secondary_with_strength.sort(key=lambda x: x[1], reverse=True)

        # Add to application order
        for tech, _ in secondary_with_strength:
            application_order.append(tech)

        return application_order

    async def _apply_parallel_coordination(
        self,
        request: TechniqueCoordinationRequest,
        available_techniques: dict[PromptingTechnique, BasePromptingTechnique],
        interactions: list[TechniqueInteraction],
    ) -> list[PromptingTechnique]:
        """Apply techniques in parallel."""
        # All techniques applied simultaneously
        return [request.primary_technique] + request.secondary_techniques

    async def _apply_hierarchical_coordination(
        self,
        request: TechniqueCoordinationRequest,
        available_techniques: dict[PromptingTechnique, BasePromptingTechnique],
        interactions: list[TechniqueInteraction],
    ) -> list[PromptingTechnique]:
        """Apply techniques in hierarchical layers."""
        layers = []

        # Layer 1: Primary technique
        layers.append([request.primary_technique])

        # Layer 2: Complementary techniques (strength > 0.5)
        complementary = []
        for tech in request.secondary_techniques:
            strength = self._get_interaction_strength(request.primary_technique, tech, interactions)
            if strength > 0.5:
                complementary.append(tech)

        if complementary:
            layers.append(complementary)

        # Layer 3: Remaining techniques
        remaining = [tech for tech in request.secondary_techniques if tech not in complementary]
        if remaining:
            layers.append(remaining)

        # Flatten layers into application order
        application_order = []
        for layer in layers:
            application_order.extend(layer)

        return application_order

    async def _apply_adaptive_coordination(
        self,
        request: TechniqueCoordinationRequest,
        available_techniques: dict[PromptingTechnique, BasePromptingTechnique],
        interactions: list[TechniqueInteraction],
    ) -> list[PromptingTechnique]:
        """Apply techniques with adaptive selection."""
        # Delegate to selected adaptive strategy
        selected_strategy = self._select_coordination_strategy(request, interactions)
        return await selected_strategy(request, available_techniques, interactions)

    async def _validate_constitutional_compliance(
        self,
        application_order: list[PromptingTechnique],
        requirements: dict[str, Any],
    ) -> dict[str, bool]:
        """Validate constitutional compliance across all techniques."""
        compliance = {}

        # Evidence-based compliance
        if requirements.get("evidence_based", False):
            evidence_supporting_techniques = {
                PromptingTechnique.QUERY_FANOUT,  # Explores multiple aspects
                PromptingTechnique.CHAIN_OF_VERIFICATION,  # Verifies claims
                PromptingTechnique.SELF_REFINE,  # Iteratively improves evidence quality
            }

            compliance["evidence_based"] = any(tech in evidence_supporting_techniques for tech in application_order)

        # Anti-deception compliance
        if requirements.get("anti_deception", False):
            anti_deception_techniques = {
                PromptingTechnique.SOCRATIC,  # Questions assumptions
                PromptingTechnique.CHAIN_OF_VERIFICATION,  # Verifies claims
                PromptingTechnique.SELF_REFINE,  # Refines accuracy
            }

            compliance["anti_deception"] = any(tech in anti_deception_techniques for tech in application_order)

        # Performance compliance
        max_techniques = requirements.get("max_concurrent_techniques", 4)
        compliance["performance_constraints"] = len(application_order) <= max_techniques

        return compliance

    def _estimate_performance_impact(
        self,
        application_order: list[PromptingTechnique],
        request: TechniqueCoordinationRequest,
    ) -> dict[str, float]:
        """Estimate performance impact of coordinated techniques."""
        # Base impact per technique
        base_impacts = {
            PromptingTechnique.QUERY_FANOUT: {"time": 1.5, "memory": 100, "tokens": 300},
            PromptingTechnique.SOCRATIC: {"time": 1.2, "memory": 80, "tokens": 250},
            PromptingTechnique.SELF_REFINE: {"time": 2.0, "memory": 120, "tokens": 400},
            PromptingTechnique.CHAIN_OF_VERIFICATION: {"time": 1.8, "memory": 110, "tokens": 350},
        }

        # Calculate total impact
        total_time = 0
        total_memory = 0
        total_tokens = 0

        for tech in application_order:
            impact = base_impacts.get(tech, {"time": 1.0, "memory": 50, "tokens": 200})
            total_time += impact["time"]
            total_memory += impact["memory"]
            total_tokens += impact["tokens"]

        # Coordination overhead (10%)
        coordination_overhead = 1.1

        return {
            "estimated_time": total_time * coordination_overhead,
            "estimated_memory": total_memory * coordination_overhead,
            "estimated_tokens": int(total_tokens * coordination_overhead),
            "technique_count": len(application_order),
        }

    def _get_interaction_strength(
        self,
        tech1: PromptingTechnique,
        tech2: PromptingTechnique,
        interactions: list[TechniqueInteraction],
    ) -> float:
        """Get interaction strength between two techniques."""
        for interaction in interactions:
            if (interaction.technique1 == tech1 and interaction.technique2 == tech2) or (
                interaction.technique1 == tech2 and interaction.technique2 == tech1
            ):
                return interaction.strength
        return 0.0

    def _calculate_overall_interaction_strength(
        self,
        interactions: list[TechniqueInteraction],
    ) -> float:
        """Calculate overall interaction strength."""
        if not interactions:
            return 0.0

        return sum(i.strength for i in interactions) / len(interactions)

    def _update_coordination_history(
        self,
        request: TechniqueCoordinationRequest,
        result: TechniqueCoordinationResult,
    ) -> None:
        """Update coordination history for learning and optimization."""
        history_entry = {
            "timestamp": time.time(),
            "request": {
                "primary_technique": request.primary_technique.value,
                "secondary_techniques": [t.value for t in request.secondary_techniques],
                "coordination_mode": request.coordination_mode.value,
            },
            "result": {
                "technique_count": len(result.coordinated_techniques),
                "conflicts_resolved": result.conflict_resolutions.get("conflicts_detected", 0),
                "compliance_score": sum(result.constitutional_compliance.values())
                / len(result.constitutional_compliance),
                "estimated_time": result.performance_estimate.get("estimated_time", 0.0),
            },
        }

        self.coordination_history.append(history_entry)

        # Keep only recent history
        if len(self.coordination_history) > 100:
            self.coordination_history = self.coordination_history[-50:]

    def _create_fallback_coordination(
        self,
        request: TechniqueCoordinationRequest,
    ) -> TechniqueCoordinationResult:
        """Create fallback coordination if main coordination fails."""
        return TechniqueCoordinationResult(
            coordinated_techniques=[request.primary_technique],
            application_order=[request.primary_technique],
            conflict_resolutions={"fallback_mode": True},
            performance_estimate={"estimated_time": 1.0, "estimated_memory": 50, "estimated_tokens": 200},
            constitutional_compliance={"fallback_compliance": True},
            coordination_metadata={"fallback_used": True, "error": "coordination_failed"},
        )

    def get_coordination_statistics(self) -> dict[str, Any]:
        """Get coordination system performance statistics."""
        if not self.coordination_history:
            return {"status": "No coordination history available"}

        recent_history = self.coordination_history[-20:]  # Last 20 coordinations

        avg_techniques = sum(h["result"]["technique_count"] for h in recent_history) / len(recent_history)
        avg_time = sum(h["result"]["estimated_time"] for h in recent_history) / len(recent_history)
        avg_compliance = sum(h["result"]["compliance_score"] for h in recent_history) / len(recent_history)
        total_conflicts = sum(h["result"]["conflicts_resolved"] for h in recent_history)

        coordination_modes = {}
        for h in recent_history:
            mode = h["request"]["coordination_mode"]
            coordination_modes[mode] = coordination_modes.get(mode, 0) + 1

        return {
            "total_coordinations": len(self.coordination_history),
            "recent_coordinations": len(recent_history),
            "average_techniques_per_coordination": avg_techniques,
            "average_estimated_time": avg_time,
            "average_compliance_score": avg_compliance,
            "total_conflicts_resolved": total_conflicts,
            "most_used_coordination_mode": (
                max(coordination_modes, key=coordination_modes.get) if coordination_modes else None
            ),
            "coordination_mode_distribution": coordination_modes,
        }
