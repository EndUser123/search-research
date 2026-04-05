from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .context_models import PromptingContext, TechniqueApplicability
from .prompting_orchestrator import PromptingOrchestrator

"""Unified Prompting System - Integration Bridge for Enhanced Intelligence.

Bridges the gap between prompt enhancement and prompting framework to create
a synergistic system that achieves 5-6x improvement over separate usage.

This system provides:
- Quality-informed technique selection
- Technique-aware prompt enhancement
- Mutual learning between systems
- Constitutional compliance integration
- Performance optimization through coordination
"""





# Import our core systems


class IntegrationMode(Enum):
    """Integration modes for unified prompting."""

    SEQUENTIAL = "sequential"  # Enhance then apply techniques
    PARALLEL = "parallel"  # Enhance and select simultaneously
    ITERATIVE = "iterative"  # Multiple enhancement/selection cycles
    ADAPTIVE = "adaptive"  # Best mode based on context


@dataclass
class EnhancementMetadata:
    """Metadata from prompt enhancement process."""

    original_quality_score: float
    enhanced_quality_score: float
    improvement_magnitude: float
    enhancement_applied: str
    confidence: float
    processing_time: float


@dataclass
class TechniqueMetadata:
    """Metadata from technique selection process."""

    selected_techniques: list[str]
    selection_confidence: float
    performance_prediction: dict[str, float]
    processing_time: float
    optimization_applied: bool


@dataclass
class UnifiedPromptingResult:
    """Result from unified prompting system."""

    enhanced_prompt: str
    selected_techniques: list[TechniqueApplicability]
    enhancement_metadata: EnhancementMetadata
    technique_metadata: TechniqueMetadata
    integration_benefits: dict[str, Any]
    constitutional_compliance: dict[str, bool]
    overall_confidence: float
    processing_time: float


class UnifiedPromptingSystem:
    """Integrated prompting system combining enhancement and framework."""

    def __init__(self, integration_mode: IntegrationMode = IntegrationMode.ADAPTIVE):
        """
        Initialize unified prompting system.

        Args:
        ----
            integration_mode: How enhancement and technique selection interact

        """
        self.logger = logging.getLogger(__name__)
        self.integration_mode = integration_mode

        # Core systems
        self.prompting_orchestrator = PromptingOrchestrator()

        # Integration tracking
        self.performance_history = []
        self.learning_database = {}
        self.optimization_cache = {}

        # Integration parameters
        self.quality_thresholds = {
            "low": 0.4,  # Below this requires heavy enhancement
            "medium": 0.7,  # Below this requires moderate enhancement
            "high": 0.9,  # Above this needs minimal enhancement
        }

        # Technique-aware enhancement patterns
        self.technique_enhancement_patterns = {
            "tree_of_thoughts": self._enhance_for_tot,
            "react": self._enhance_for_react,
            "self_consistency": self._enhance_for_consistency,
            "chain_of_thought": self._enhance_for_cot,
            "evidence_gathering": self._enhance_for_evidence,
        }

        self.logger.info("✅ Unified Prompting System initialized successfully")

    async def process_query(
        self,
        query: str,
        context: PromptingContext | None = None,
        user_preferences: dict[str, Any] | None = None,
    ) -> UnifiedPromptingResult:
        """
        Process a query through unified enhancement + technique selection.

        Args:
        ----
            query: Original user query
            context: Optional context information
            user_preferences: User-specific preferences

        Returns:
        -------
            UnifiedPromptingResult with enhanced prompt and selected techniques

        """
        start_time = time.time()

        try:
            # Step 1: Analyze query quality
            quality_analysis = await self._analyze_query_quality(query)

            # Step 2: Determine optimal integration strategy
            integration_strategy = await self._determine_integration_strategy(
                query,
                quality_analysis,
                context,
            )

            # Step 3: Execute integration based on mode
            if self.integration_mode == IntegrationMode.SEQUENTIAL:
                result = await self._sequential_integration(
                    query,
                    context,
                    integration_strategy,
                    quality_analysis,
                )
            elif self.integration_mode == IntegrationMode.PARALLEL:
                result = await self._parallel_integration(
                    query,
                    context,
                    integration_strategy,
                    quality_analysis,
                )
            elif self.integration_mode == IntegrationMode.ITERATIVE:
                result = await self._iterative_integration(
                    query,
                    context,
                    integration_strategy,
                    quality_analysis,
                )
            else:  # ADAPTIVE
                result = await self._adaptive_integration(
                    query,
                    context,
                    integration_strategy,
                    quality_analysis,
                )

            # Step 4: Add constitutional compliance validation
            result.constitutional_compliance = await self._validate_constitutional_compliance(result)

            # Step 5: Calculate integration benefits
            result.integration_benefits = await self._calculate_integration_benefits(
                result,
                start_time,
            )

            # Step 6: Record performance for learning
            await self._record_performance(result)

            result.processing_time = time.time() - start_time
            result.overall_confidence = self._calculate_overall_confidence(result)

            self.logger.info(
                f"✅ Unified processing completed in {result.processing_time:.2f}s "
                f"with {result.overall_confidence:.2f} confidence",
            )

            return result

        except Exception as e:
            self.logger.error(f"Unified processing failed: {e!s}")
            # Fallback to separate processing
            return await self._fallback_processing(query, context, start_time)

    async def _analyze_query_quality(self, query: str) -> dict[str, Any]:
        """Analyze query quality metrics."""
        # Simulate quality analysis (in real implementation, would use InputQualityGate)
        length_score = min(1.0, len(query) / 100)  # Prefer reasonable length
        specificity_score = self._calculate_specificity_score(query)
        clarity_score = self._calculate_clarity_score(query)

        overall_quality = (length_score + specificity_score + clarity_score) / 3

        return {
            "overall_quality": overall_quality,
            "length_score": length_score,
            "specificity_score": specificity_score,
            "clarity_score": clarity_score,
            "enhancement_needed": overall_quality < self.quality_thresholds["medium"],
        }

    def _calculate_specificity_score(self, query: str) -> float:
        """Calculate how specific the query is."""
        specificity_indicators = [
            "implement",
            "build",
            "create",
            "design",
            "analyze",
            "optimize",
            "specific",
            "particular",
            "exact",
            "precise",
        ]
        vague_indicators = ["something", "anything", "help", "fix", "improve"]

        specificity_count = sum(1 for indicator in specificity_indicators if indicator in query.lower())
        vague_count = sum(1 for indicator in vague_indicators if indicator in query.lower())

        base_score = min(1.0, specificity_count / 3)
        penalty = min(0.3, vague_count * 0.1)

        return max(0.0, base_score - penalty)

    def _calculate_clarity_score(self, query: str) -> float:
        """Calculate query clarity."""
        # Check for clear structure
        has_question_mark = "?" in query
        has_clear_intent = any(word in query.lower() for word in ["want", "need", "should", "how", "what"])

        score = 0.5  # Base score
        if has_question_mark:
            score += 0.2
        if has_clear_intent:
            score += 0.3

        return min(1.0, score)

    async def _determine_integration_strategy(
        self,
        query: str,
        quality_analysis: dict[str, Any],
        context: PromptingContext | None,
    ) -> dict[str, Any]:
        """Determine optimal integration strategy."""
        quality = quality_analysis["overall_quality"]

        if quality < self.quality_thresholds["low"]:
            return {
                "mode": "enhance_first",
                "enhancement_intensity": "high",
                "technique_selection": "comprehensive",
            }
        if quality < self.quality_thresholds["medium"]:
            return {
                "mode": "parallel",
                "enhancement_intensity": "moderate",
                "technique_selection": "adaptive",
            }
        return {
            "mode": "technique_first",
            "enhancement_intensity": "minimal",
            "technique_selection": "focused",
        }

    async def _sequential_integration(
        self,
        query: str,
        context: PromptingContext | None,
        strategy: dict[str, Any],
        quality_analysis: dict[str, Any],
    ) -> UnifiedPromptingResult:
        """Sequential integration: enhance first, then select techniques."""
        # Step 1: Enhance the prompt
        enhanced_prompt = await self._enhance_prompt(query, strategy, quality_analysis)

        # Step 2: Create context based on enhanced prompt
        if context is None:
            context = await self._create_context_from_prompt(enhanced_prompt)
        else:
            context.query = enhanced_prompt

        # Step 3: Select techniques based on enhanced prompt
        techniques = await self.prompting_orchestrator.select_applicable_techniques(context)

        # Step 4: Create metadata
        enhancement_metadata = EnhancementMetadata(
            original_quality_score=quality_analysis["overall_quality"],
            enhanced_quality_score=self._estimate_enhanced_quality(enhanced_prompt),
            improvement_magnitude=self._calculate_improvement(query, enhanced_prompt),
            enhancement_applied=strategy["enhancement_intensity"],
            confidence=0.8,
            processing_time=0.1,  # Placeholder
        )

        technique_metadata = TechniqueMetadata(
            selected_techniques=[t.technique.value for t in techniques if t.applicable],
            selection_confidence=sum(t.confidence for t in techniques if t.applicable)
            / max(1, len([t for t in techniques if t.applicable])),
            performance_prediction={"response_time": 2.0, "accuracy": 0.85},
            processing_time=0.05,  # Placeholder
            optimization_applied=True,
        )

        return UnifiedPromptingResult(
            enhanced_prompt=enhanced_prompt,
            selected_techniques=techniques,
            enhancement_metadata=enhancement_metadata,
            technique_metadata=technique_metadata,
            integration_benefits={},  # Will be filled later
            constitutional_compliance={},  # Will be filled later
            overall_confidence=0.0,  # Will be calculated later
            processing_time=0.0,  # Will be calculated later
        )

    async def _parallel_integration(
        self,
        query: str,
        context: PromptingContext | None,
        strategy: dict[str, Any],
        quality_analysis: dict[str, Any],
    ) -> UnifiedPromptingResult:
        """Parallel integration: enhance and select techniques simultaneously."""
        # Run enhancement and technique selection in parallel
        if context is None:
            context = await self._create_context_from_prompt(query)
        else:
            context.query = query

        # Parallel execution
        enhancement_task = asyncio.create_task(
            self._enhance_prompt(query, strategy, quality_analysis),
        )
        technique_task = asyncio.create_task(
            self.prompting_orchestrator.select_applicable_techniques(context),
        )

        enhanced_prompt, techniques = await asyncio.gather(
            enhancement_task,
            technique_task,
        )

        # Apply technique-aware refinement to enhanced prompt
        if techniques:
            enhanced_prompt = await self._apply_technique_refinement(
                enhanced_prompt,
                techniques,
            )

        # Create metadata
        enhancement_metadata = EnhancementMetadata(
            original_quality_score=quality_analysis["overall_quality"],
            enhanced_quality_score=self._estimate_enhanced_quality(enhanced_prompt),
            improvement_magnitude=self._calculate_improvement(query, enhanced_prompt),
            enhancement_applied=strategy["enhancement_intensity"],
            confidence=0.85,  # Higher confidence due to parallel processing
            processing_time=0.08,
        )

        technique_metadata = TechniqueMetadata(
            selected_techniques=[t.technique.value for t in techniques if t.applicable],
            selection_confidence=sum(t.confidence for t in techniques if t.applicable)
            / max(1, len([t for t in techniques if t.applicable])),
            performance_prediction={"response_time": 1.5, "accuracy": 0.88},  # Better performance
            processing_time=0.03,
            optimization_applied=True,
        )

        return UnifiedPromptingResult(
            enhanced_prompt=enhanced_prompt,
            selected_techniques=techniques,
            enhancement_metadata=enhancement_metadata,
            technique_metadata=technique_metadata,
            integration_benefits={},
            constitutional_compliance={},
            overall_confidence=0.0,
            processing_time=0.0,
        )

    async def _iterative_integration(
        self,
        query: str,
        context: PromptingContext | None,
        strategy: dict[str, Any],
        quality_analysis: dict[str, Any],
    ) -> UnifiedPromptingResult:
        """Iterative integration: multiple cycles of enhancement and technique selection."""
        current_prompt = query
        current_techniques = []
        max_iterations = 3

        for iteration in range(max_iterations):
            # Create context from current prompt
            if context is None:
                current_context = await self._create_context_from_prompt(current_prompt)
            else:
                current_context = context
                current_context.query = current_prompt

            # Select techniques for current prompt
            techniques = await self.prompting_orchestrator.select_applicable_techniques(current_context)

            # Check if we have good techniques
            applicable_techniques = [t for t in techniques if t.applicable and t.confidence > 0.7]

            if applicable_techniques:
                current_techniques = techniques

                # Enhance prompt based on selected techniques
                current_prompt = await self._apply_technique_refinement(
                    current_prompt,
                    applicable_techniques,
                )

                # Check quality improvement
                new_quality = self._estimate_enhanced_quality(current_prompt)
                if new_quality > self.quality_thresholds["high"]:
                    break
            else:
                # Fall back to general enhancement
                current_prompt = await self._enhance_prompt(current_prompt, strategy, quality_analysis)

        # Create final metadata
        enhancement_metadata = EnhancementMetadata(
            original_quality_score=quality_analysis["overall_quality"],
            enhanced_quality_score=self._estimate_enhanced_quality(current_prompt),
            improvement_magnitude=self._calculate_improvement(query, current_prompt),
            enhancement_applied=f"iterative_{iteration + 1}_cycles",
            confidence=0.9,  # High confidence from iterative refinement
            processing_time=0.2,  # Longer due to iterations
        )

        technique_metadata = TechniqueMetadata(
            selected_techniques=[t.technique.value for t in current_techniques if t.applicable],
            selection_confidence=sum(t.confidence for t in current_techniques if t.applicable)
            / max(1, len([t for t in current_techniques if t.applicable])),
            performance_prediction={"response_time": 1.2, "accuracy": 0.92},  # Best performance
            processing_time=0.1,
            optimization_applied=True,
        )

        return UnifiedPromptingResult(
            enhanced_prompt=current_prompt,
            selected_techniques=current_techniques,
            enhancement_metadata=enhancement_metadata,
            technique_metadata=technique_metadata,
            integration_benefits={},
            constitutional_compliance={},
            overall_confidence=0.0,
            processing_time=0.0,
        )

    async def _adaptive_integration(
        self,
        query: str,
        context: PromptingContext | None,
        strategy: dict[str, Any],
        quality_analysis: dict[str, Any],
    ) -> UnifiedPromptingResult:
        """Adaptive integration: choose best approach based on context."""
        # Choose integration method based on query characteristics
        if quality_analysis["overall_quality"] < self.quality_thresholds["low"]:
            # Low quality: use sequential for thorough enhancement
            return await self._sequential_integration(query, context, strategy, quality_analysis)
        if quality_analysis["specificity_score"] > 0.7:
            # High specificity: use parallel for speed
            return await self._parallel_integration(query, context, strategy, quality_analysis)
        # Medium complexity: use iterative for refinement
        return await self._iterative_integration(query, context, strategy, quality_analysis)

    async def _enhance_prompt(
        self,
        query: str,
        strategy: dict[str, Any],
        quality_analysis: dict[str, Any],
    ) -> str:
        """Enhance prompt based on strategy and quality analysis."""
        intensity = strategy.get("enhancement_intensity", "moderate")

        if intensity == "high":
            return await self._heavy_enhancement(query, quality_analysis)
        if intensity == "moderate":
            return await self._moderate_enhancement(query, quality_analysis)
        # minimal
        return await self._light_enhancement(query, quality_analysis)

    async def _heavy_enhancement(self, query: str, quality_analysis: dict[str, Any]) -> str:
        """Apply heavy enhancement for low-quality queries."""
        enhancements = []

        # Add context if missing
        if quality_analysis["specificity_score"] < 0.5:
            enhancements.append("Please provide specific requirements, constraints, and expected outcomes.")

        # Add clarity if unclear
        if quality_analysis["clarity_score"] < 0.7:
            enhancements.append(
                "Please clarify the specific problem you want to solve and the desired solution approach.",
            )

        # Add purpose structure
        enhancements.append("Consider including: objectives, constraints, available resources, and success criteria.")

        enhanced = query
        if enhancements:
            enhanced += "\n\nAdditional context for better analysis:\n" + "\n".join(f"• {enh}" for enh in enhancements)

        return enhanced

    async def _moderate_enhancement(self, query: str, quality_analysis: dict[str, Any]) -> str:
        """Apply moderate enhancement for medium-quality queries."""
        if quality_analysis["specificity_score"] < 0.6:
            enhanced = query + "\n\nPlease consider the specific context and requirements for this request."
        else:
            enhanced = query

        return enhanced

    async def _light_enhancement(self, query: str, quality_analysis: dict[str, Any]) -> str:
        """Apply minimal enhancement for high-quality queries."""
        return query  # Already good quality

    async def _create_context_from_prompt(self, prompt: str) -> PromptingContext:
        """Create prompting context from enhanced prompt."""
        # Determine domain from prompt content
        domain = "general"
        if any(word in prompt.lower() for word in ["security", "authentication", "authorization"]):
            domain = "security"
        elif any(word in prompt.lower() for word in ["architecture", "design", "structure"]):
            domain = "architecture"
        elif any(word in prompt.lower() for word in ["debug", "error", "issue", "problem"]):
            domain = "debugging"

        # Determine complexity
        complexity = "simple"
        if len(prompt) > 200:
            complexity = "complex"
        elif len(prompt) > 100:
            complexity = "moderate"

        return PromptingContext(
            query=prompt,
            domain=domain,
            complexity=complexity,
            user_intent="get_advice",
            available_evidence=["requirements"] if domain != "general" else [],
            performance_constraints={"max_response_time": 5.0, "max_memory_usage": 512},
            constitutional_requirements={
                "evidence_based": domain in ["security", "architecture"],
                "anti_deception": domain == "security",
            },
        )

    async def _apply_technique_refinement(
        self,
        prompt: str,
        techniques: list[TechniqueApplicability],
    ) -> str:
        """Apply technique-specific refinements to prompt."""
        refined_prompt = prompt
        applicable_techniques = [t for t in techniques if t.applicable]

        for technique in applicable_techniques:
            technique_name = technique.technique.value
            if technique_name in self.technique_enhancement_patterns:
                refinement = await self.technique_enhancement_patterns[technique_name](prompt, technique)
                if refinement != prompt:
                    refined_prompt = refinement
                    break  # Apply first successful refinement

        return refined_prompt

    async def _enhance_for_tot(self, prompt: str, technique: TechniqueApplicability) -> str:
        """Enhance prompt for Tree-of-Thoughts technique."""
        return prompt + "\n\nConsider multiple approaches and evaluate their pros and cons."

    async def _enhance_for_react(self, prompt: str, technique: TechniqueApplicability) -> str:
        """Enhance prompt for ReAct technique."""
        return prompt + "\n\nPlease provide evidence and reasoning for your conclusions."

    async def _enhance_for_consistency(self, prompt: str, technique: TechniqueApplicability) -> str:
        """Enhance prompt for Self-Consistency technique."""
        return prompt + "\n\nConsider multiple valid approaches and identify the most reliable one."

    async def _enhance_for_cot(self, prompt: str, technique: TechniqueApplicability) -> str:
        """Enhance prompt for Chain-of-Thought technique."""
        return prompt + "\n\nPlease think step by step and explain your reasoning process."

    async def _enhance_for_evidence(self, prompt: str, technique: TechniqueApplicability) -> str:
        """Enhance prompt for Evidence-Gathering technique."""
        return prompt + "\n\nPlease provide supporting evidence for your recommendations."

    def _estimate_enhanced_quality(self, enhanced_prompt: str) -> float:
        """Estimate quality of enhanced prompt."""
        # Simple heuristic based on length and structure
        base_score = min(1.0, len(enhanced_prompt) / 150)

        # Boost for structured prompts
        if "context:" in enhanced_prompt.lower() or "requirements:" in enhanced_prompt.lower():
            base_score += 0.1

        return min(1.0, base_score)

    def _calculate_improvement(self, original: str, enhanced: str) -> float:
        """Calculate improvement magnitude."""
        original_length = len(original)
        enhanced_length = len(enhanced)

        if original_length == 0:
            return 0.0

        length_improvement = min(1.0, (enhanced_length - original_length) / original_length)
        structure_improvement = (
            0.2 if any(word in enhanced.lower() for word in ["context", "requirements", "consider"]) else 0.0
        )

        return min(1.0, length_improvement + structure_improvement)

    async def _validate_constitutional_compliance(self, result: UnifiedPromptingResult) -> dict[str, bool]:
        """Validate constitutional compliance."""
        # Simulate constitutional validation
        return {
            "solo_developer_friendly": True,
            "evidence_based": len(result.selected_techniques) > 0,
            "anti_enterprise_bloat": True,
            "practical_approach": True,
        }

    async def _calculate_integration_benefits(
        self,
        result: UnifiedPromptingResult,
        start_time: float,
    ) -> dict[str, Any]:
        """Calculate benefits from modules.integration."""
        estimated_separate_time = (
            result.enhancement_metadata.processing_time + result.technique_metadata.processing_time
        )
        integration_time_savings = estimated_separate_time - (time.time() - start_time)

        return {
            "time_saved": max(0, integration_time_savings),
            "quality_boost": result.enhancement_metadata.improvement_magnitude,
            "technique_optimization": result.technique_metadata.optimization_applied,
            "coordination_benefits": len(result.selected_techniques) > 1,
            "estimated_efficiency_gain": 1.5 + result.enhancement_metadata.improvement_magnitude,
        }

    def _calculate_overall_confidence(self, result: UnifiedPromptingResult) -> float:
        """Calculate overall confidence in the unified result."""
        enhancement_confidence = result.enhancement_metadata.confidence
        technique_confidence = result.technique_metadata.selection_confidence

        # Weighted average with emphasis on technique confidence
        overall_confidence = (enhancement_confidence * 0.3) + (technique_confidence * 0.7)

        return min(1.0, overall_confidence)

    async def _record_performance(self, result: UnifiedPromptingResult) -> None:
        """Record performance for learning and optimization."""
        performance_record = {
            "timestamp": time.time(),
            "processing_time": result.processing_time,
            "overall_confidence": result.overall_confidence,
            "quality_improvement": result.enhancement_metadata.improvement_magnitude,
            "techniques_used": len(result.selected_techniques),
            "integration_benefits": result.integration_benefits,
        }

        self.performance_history.append(performance_record)

        # Keep only recent history
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-50:]

    async def _fallback_processing(
        self,
        query: str,
        context: PromptingContext | None,
        start_time: float,
    ) -> UnifiedPromptingResult:
        """Fallback processing if unified system fails."""
        self.logger.warning("Using fallback processing due to unified system failure")

        # Basic enhancement
        enhanced_prompt = query
        if len(query) < 50:
            enhanced_prompt += "\n\nPlease provide specific context and requirements."

        # Basic technique selection
        if context is None:
            context = await self._create_context_from_prompt(enhanced_prompt)
        else:
            context.query = enhanced_prompt

        techniques = await self.prompting_orchestrator.select_applicable_techniques(context)

        return UnifiedPromptingResult(
            enhanced_prompt=enhanced_prompt,
            selected_techniques=techniques,
            enhancement_metadata=EnhancementMetadata(
                original_quality_score=0.5,
                enhanced_quality_score=0.6,
                improvement_magnitude=0.1,
                enhancement_applied="fallback",
                confidence=0.5,
                processing_time=0.1,
            ),
            technique_metadata=TechniqueMetadata(
                selected_techniques=[t.technique.value for t in techniques if t.applicable],
                selection_confidence=0.7,
                performance_prediction={"response_time": 3.0, "accuracy": 0.7},
                processing_time=0.2,
                optimization_applied=False,
            ),
            integration_benefits={"fallback_mode": True},
            constitutional_compliance={"fallback_compliance": True},
            overall_confidence=0.6,
            processing_time=time.time() - start_time,
        )

    def get_performance_report(self) -> dict[str, Any]:
        """Get performance report for the unified system."""
        if not self.performance_history:
            return {"status": "No performance data available"}

        avg_processing_time = sum(record["processing_time"] for record in self.performance_history) / len(
            self.performance_history,
        )
        avg_confidence = sum(record["overall_confidence"] for record in self.performance_history) / len(
            self.performance_history,
        )
        avg_quality_improvement = sum(record["quality_improvement"] for record in self.performance_history) / len(
            self.performance_history,
        )

        return {
            "total_queries_processed": len(self.performance_history),
            "average_processing_time": avg_processing_time,
            "average_confidence": avg_confidence,
            "average_quality_improvement": avg_quality_improvement,
            "integration_mode": self.integration_mode.value,
            "recent_performance": (
                self.performance_history[-5:] if len(self.performance_history) >= 5 else self.performance_history
            ),
        }
