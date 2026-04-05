from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base_prompting_technique import BasePromptingTechnique
from .context_models import PromptingContext, PromptingTechnique

"""Enhanced Base Prompting Technique with New Cognitive Capabilities.

Extended base class implementing advanced cognitive techniques for automatic
enhancement system with intelligent framework selection and CSF compliance.

This module provides:
- Enhanced base technique class with automatic cognitive capabilities
- QueryFanout, SocraticMethod, SelfRefine, ChainOfVerification techniques
- Performance monitoring and optimization integration
- Constitutional compliance validation and enforcement
- Advanced caching and learning mechanisms
"""





class EnhancementType(Enum):
    """Types of cognitive enhancement available."""

    STRUCTURAL = "structural"  # Enhanced structure and organization
    CRITICAL_THINKING = "critical_thinking"  # Deep analysis and questioning
    ITERATIVE_REFINEMENT = "iterative_refinement"  # Self-improvement cycles
    EVIDENCE_VERIFICATION = "evidence_verification"  # Fact-checking and validation
    MULTI_PERSPECTIVE = "multi_perspective"  # Multiple viewpoints exploration
    STEP_BY_STEP = "step_by_step"  # Sequential reasoning


@dataclass
class EnhancementMetrics:
    """Metrics for tracking enhancement effectiveness."""

    # Quality metrics
    original_quality_score: float
    enhanced_quality_score: float
    improvement_percentage: float

    # Performance metrics
    processing_time: float
    memory_usage: float
    cpu_usage: float

    # Technique-specific metrics
    technique_success_rate: float
    user_satisfaction_score: float | None = None

    # Metadata
    enhancement_timestamp: float = field(default_factory=time.time)
    context_hash: str = ""


@dataclass
class CognitiveEnhancementResult:
    """Result of applying cognitive enhancement techniques."""

    # Core results
    enhanced_prompt: str
    enhancement_type: EnhancementType
    technique_name: str

    # Quality assessment
    quality_metrics: EnhancementMetrics
    confidence_score: float

    # Processing metadata
    processing_steps: list[str]
    optimization_applied: list[str]

    # Validation results
    constitutional_compliance: dict[str, bool]
    quality_validation_passed: bool

    # User experience
    transparency_explanation: str
    user_guidance: str | None = None


class EnhancedBasePromptingTechnique(BasePromptingTechnique):
    """
    Enhanced base class with automatic cognitive enhancement capabilities.

    Extends the base technique class to provide intelligent framework selection,
    performance optimization, and constitutional compliance integration.
    """

    def __init__(self, technique: PromptingTechnique, enhancement_type: EnhancementType):
        """Initialize enhanced prompting technique."""
        super().__init__(technique)
        self.enhancement_type = enhancement_type

        # Performance tracking
        self.performance_history: list[EnhancementMetrics] = []
        self.success_patterns: dict[str, float] = {}

        # Enhancement configuration
        self.enable_auto_optimization = True
        self.compliance_strictness = "strict"
        self.max_enhancement_time = 2.0

        # Learning and adaptation
        self.context_patterns: dict[str, dict[str, Any]] = {}
        self.user_preferences: dict[str, Any] = {}

        self.logger.info(f"Enhanced technique initialized: {technique.value} ({enhancement_type.value})")

    async def apply_cognitive_enhancement(
        self,
        prompt: str,
        context: PromptingContext | None = None,
    ) -> CognitiveEnhancementResult:
        """
        Apply cognitive enhancement with intelligent framework selection.

        Args:
        ----
            prompt: Original prompt to enhance
            context: Optional context for enhancement

        Returns:
        -------
            Comprehensive enhancement result with metrics and validation

        """
        start_time = time.time()
        original_quality = await self._calculate_prompt_quality(prompt, context)

        try:
            self.logger.debug(f"Applying {self.enhancement_type.value} enhancement to: {prompt[:50]}...")

            # Step 1: Analyze enhancement requirements
            enhancement_requirements = await self._analyze_enhancement_requirements(
                prompt,
                context,
            )

            # Step 2: Select optimal enhancement strategy
            enhancement_strategy = await self._select_enhancement_strategy(
                enhancement_requirements,
                context,
            )

            # Step 3: Apply the enhancement
            enhanced_prompt, processing_steps = await self._execute_enhancement_strategy(
                prompt,
                enhancement_strategy,
                context,
            )

            # Step 4: Calculate quality metrics
            enhanced_quality = await self._calculate_prompt_quality(enhanced_prompt, context)
            processing_time = time.time() - start_time

            # Step 5: Validate results
            quality_validation = await self._validate_enhancement_quality(
                original_quality,
                enhanced_quality,
                enhancement_strategy,
            )

            constitutional_compliance = await self._validate_constitutional_compliance(
                enhanced_prompt,
                context,
            )

            # Step 6: Create comprehensive result
            quality_metrics = EnhancementMetrics(
                original_quality_score=original_quality,
                enhanced_quality_score=enhanced_quality,
                improvement_percentage=((enhanced_quality - original_quality) / max(original_quality, 0.1)) * 100,
                processing_time=processing_time,
                memory_usage=0.0,  # Would be measured in real implementation
                cpu_usage=0.0,  # Would be measured in real implementation
                technique_success_rate=1.0 if quality_validation else 0.5,
                context_hash=self._generate_context_hash(context),
            )

            # Step 7: Generate transparency explanation
            transparency_explanation = await self._generate_transparency_explanation(
                enhancement_strategy,
                quality_metrics,
            )

            # Step 8: Update learning systems
            await self._update_learning_systems(
                prompt,
                enhanced_prompt,
                quality_metrics,
                context,
            )

            result = CognitiveEnhancementResult(
                enhanced_prompt=enhanced_prompt,
                enhancement_type=self.enhancement_type,
                technique_name=self.technique.value,
                quality_metrics=quality_metrics,
                confidence_score=min(1.0, quality_validation + 0.2),
                processing_steps=processing_steps,
                optimization_applied=enhancement_strategy.get("optimizations", []),
                constitutional_compliance=constitutional_compliance,
                quality_validation_passed=quality_validation,
                transparency_explanation=transparency_explanation,
                user_guidance=await self._generate_user_guidance(enhancement_strategy),
            )

            # Record performance
            self.performance_history.append(quality_metrics)
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-50:]

            self.logger.info(
                f"Enhancement completed: {quality_metrics.improvement_percentage:.1f}% "
                f"improvement in {processing_time:.2f}s",
            )

            return result

        except Exception as e:
            self.logger.error(f"Cognitive enhancement failed: {e!s}")
            return await self._create_fallback_result(prompt, original_quality, start_time, str(e))

    async def _analyze_enhancement_requirements(
        self,
        prompt: str,
        context: PromptingContext | None,
    ) -> dict[str, Any]:
        """Analyze requirements for cognitive enhancement."""
        requirements = {
            "current_quality": await self._calculate_prompt_quality(prompt, context),
            "complexity_score": await self._calculate_complexity_score(prompt),
            "ambiguity_score": await self._calculate_ambiguity_score(prompt),
            "domain_requirements": await self._analyze_domain_requirements(prompt, context),
            "performance_constraints": context.performance_constraints if context else {},
            "constitutional_requirements": context.constitutional_requirements if context else {},
        }

        # Determine enhancement intensity based on requirements
        if requirements["complexity_score"] > 0.7 or requirements["ambiguity_score"] > 0.6:
            requirements["intensity"] = "high"
        elif requirements["complexity_score"] > 0.4 or requirements["ambiguity_score"] > 0.3:
            requirements["intensity"] = "moderate"
        else:
            requirements["intensity"] = "minimal"

        return requirements

    async def _select_enhancement_strategy(
        self,
        requirements: dict[str, Any],
        context: PromptingContext | None,
    ) -> dict[str, Any]:
        """Select optimal enhancement strategy based on requirements."""
        strategy = {
            "primary_approach": self._get_primary_approach(requirements),
            "intensity_level": requirements["intensity"],
            "optimizations": [],
            "validation_steps": [],
        }

        # Add optimization strategies based on requirements
        if requirements["complexity_score"] > 0.6:
            strategy["optimizations"].append("structured_decomposition")

        if requirements["ambiguity_score"] > 0.4:
            strategy["optimizations"].append("clarification_enhancement")

        if self.enhancement_type == EnhancementType.EVIDENCE_VERIFICATION:
            strategy["optimizations"].append("evidence_gathering")

        # Add domain-specific optimizations
        domain_optimizations = await self._get_domain_optimizations(
            requirements["domain_requirements"],
        )
        strategy["optimizations"].extend(domain_optimizations)

        return strategy

    async def _execute_enhancement_strategy(
        self,
        prompt: str,
        strategy: dict[str, Any],
        context: PromptingContext | None,
    ) -> tuple[str, list[str]]:
        """Execute the selected enhancement strategy."""
        enhanced_prompt = prompt
        processing_steps = []

        processing_steps.append(f"Applying {strategy['primary_approach']} enhancement")

        # Apply the primary enhancement based on technique type
        if self.enhancement_type == EnhancementType.QUERY_FANOUT:
            enhanced_prompt = await self._apply_query_fanout_enhancement(prompt, strategy)
            processing_steps.append("Multi-perspective analysis applied")
        elif self.enhancement_type == EnhancementType.CRITICAL_THINKING:
            enhanced_prompt = await self._apply_socratic_enhancement(prompt, strategy)
            processing_steps.append("Socratic questioning framework applied")
        elif self.enhancement_type == EnhancementType.ITERATIVE_REFINEMENT:
            enhanced_prompt = await self._apply_refinement_enhancement(prompt, strategy)
            processing_steps.append("Self-refinement cycle initiated")
        elif self.enhancement_type == EnhancementType.EVIDENCE_VERIFICATION:
            enhanced_prompt = await self._apply_verification_enhancement(prompt, strategy)
            processing_steps.append("Evidence verification process applied")
        elif self.enhancement_type == EnhancementType.MULTI_PERSPECTIVE:
            enhanced_prompt = await self._apply_perspective_enhancement(prompt, strategy)
            processing_steps.append("Multi-perspective analysis completed")
        elif self.enhancement_type == EnhancementType.STEP_BY_STEP:
            enhanced_prompt = await self._apply_sequential_enhancement(prompt, strategy)
            processing_steps.append("Step-by-step reasoning structure added")

        # Apply additional optimizations
        for optimization in strategy.get("optimizations", []):
            enhanced_prompt = await self._apply_optimization(enhanced_prompt, optimization, context)
            processing_steps.append(f"Applied optimization: {optimization}")

        return enhanced_prompt, processing_steps

    # Technique-specific enhancement methods

    async def _apply_query_fanout_enhancement(self, prompt: str, strategy: dict[str, Any]) -> str:
        """Apply QueryFanout enhancement for multi-faceted analysis."""
        intensity = strategy.get("intensity_level", "moderate")

        if intensity == "high":
            enhancement = (
                f"{prompt}\n\n"
                "COMPREHENSIVE MULTI-PERSPECTIVE ANALYSIS REQUIRED:\n\n"
                "Please address this query from the following perspectives:\n"
                "1. TECHNICAL IMPLEMENTATION: Detailed technical considerations, implementation approaches, and technical constraints\n"
                "2. PRACTICAL APPLICATION: Real-world implications, usability considerations, and practical challenges\n"
                "3. ALTERNATIVE APPROACHES: Different methodologies, comparative analysis, and trade-offs\n"
                "4. RISK ASSESSMENT: Potential risks, mitigation strategies, and contingency planning\n"
                "5. BEST PRACTICES: Industry standards, proven methodologies, and optimization opportunities\n"
                "6. LONG-TERM CONSIDERATIONS: Scalability, maintainability, and future evolution\n\n"
                "Provide a comprehensive analysis that integrates all perspectives and presents a unified recommendation."
            )
        elif intensity == "moderate":
            enhancement = (
                f"{prompt}\n\n"
                "Please analyze this from multiple perspectives:\n"
                "• Technical implementation and feasibility\n"
                "• Practical implications and constraints\n"
                "• Alternative approaches and trade-offs\n"
                "• Best practices and recommendations"
            )
        else:  # minimal
            enhancement = f"{query}\n\nConsider multiple approaches and perspectives in your analysis."

        return enhancement

    async def _apply_socratic_enhancement(self, prompt: str, strategy: dict[str, Any]) -> str:
        """Apply Socratic method enhancement for critical thinking."""
        intensity = strategy.get("intensity_level", "moderate")

        if intensity == "high":
            enhancement = (
                f"{prompt}\n\n"
                "CRITICAL THINKING ANALYSIS USING SOCRATIC METHOD:\n\n"
                "Please approach this query through systematic Socratic inquiry:\n\n"
                "FOUNDATIONAL QUESTIONS:\n"
                "• What are the fundamental assumptions underlying this query?\n"
                "• What definitions and concepts need clarification?\n"
                "• What is the scope and context of this problem?\n\n"
                "EVIDENCE AND REASONING:\n"
                "• What evidence supports or challenges the premises?\n"
                "• What logical relationships exist between the components?\n"
                "• What are the potential biases or limitations?\n\n"
                "ALTERNATIVE PERSPECTIVES:\n"
                "• How might different stakeholders view this issue?\n"
                "• What alternative interpretations or solutions exist?\n"
                "• What are the strengths and weaknesses of each approach?\n\n"
                "IMPLICATIONS AND CONSEQUENCES:\n"
                "• What are the short-term and long-term implications?\n"
                "• What unintended consequences might arise?\n"
                "• How does this connect to broader principles or patterns?\n\n"
                "SYNTHESIS AND CONCLUSION:\n"
                "• What conclusions can be drawn with reasonable confidence?\n"
                "• What remaining questions or uncertainties exist?\n"
                "• What recommendations emerge from this analysis?"
            )
        elif intensity == "moderate":
            enhancement = (
                f"{prompt}\n\n"
                "Please use critical thinking and Socratic inquiry:\n"
                "• Question underlying assumptions\n"
                "• Examine evidence and reasoning\n"
                "• Consider alternative perspectives\n"
                "• Analyze implications and consequences"
            )
        else:  # minimal
            enhancement = (
                f"{prompt}\n\nPlease think critically about assumptions, evidence, and alternative perspectives."
            )

        return enhancement

    async def _apply_refinement_enhancement(self, prompt: str, strategy: dict[str, Any]) -> str:
        """Apply Self-Refine enhancement for iterative improvement."""
        intensity = strategy.get("intensity_level", "moderate")

        if intensity == "high":
            enhancement = (
                f"{prompt}\n\n"
                "ITERATIVE SELF-REFINEMENT PROCESS:\n\n"
                "Please provide a response through multiple refinement cycles:\n\n"
                "CYCLE 1 - INITIAL RESPONSE:\n"
                "Provide your initial comprehensive answer to the query.\n\n"
                "CYCLE 2 - SELF-CRITIQUE:\n"
                "Analyze your initial response and identify:\n"
                "• Areas that could be more precise or complete\n"
                "• Assumptions that may need verification\n"
                "• Alternative approaches that should be considered\n"
                "• Structural or logical improvements needed\n\n"
                "CYCLE 3 - REFINEMENT:\n"
                "Based on your critique, provide an improved response that addresses identified issues.\n\n"
                "CYCLE 4 - FINAL VALIDATION:\n"
                "Review your refined response and ensure:\n"
                "• Completeness and accuracy\n"
                "• Logical consistency and coherence\n"
                "• Practical applicability and clarity\n\n"
                "Provide both your refined final answer and brief insights into how the refinement process improved the response."
            )
        elif intensity == "moderate":
            enhancement = (
                f"{prompt}\n\n"
                "Please provide a response and then refine it:\n"
                "1. Initial response based on the query\n"
                "2. Self-critique identifying improvement areas\n"
                "3. Refined response addressing identified issues\n"
                "4. Brief explanation of improvements made"
            )
        else:  # minimal
            enhancement = f"{prompt}\n\nPlease provide a response, then self-critique and refine it for improvement."

        return enhancement

    async def _apply_verification_enhancement(self, prompt: str, strategy: dict[str, Any]) -> str:
        """Apply Chain-of-Verification enhancement for evidence-based reasoning."""
        intensity = strategy.get("intensity_level", "moderate")

        if intensity == "high":
            enhancement = (
                f"{prompt}\n\n"
                "CHAIN OF VERIFICATION METHODOLOGY:\n\n"
                "Please respond using a systematic verification approach:\n\n"
                "STEP 1 - INITIAL RESPONSE:\n"
                "Provide your initial answer to the query.\n\n"
                "STEP 2 - CLAIM IDENTIFICATION:\n"
                "Extract and list all key claims, facts, and assertions made in your response.\n\n"
                "STEP 3 - EVIDENCE VERIFICATION:\n"
                "For each claim, provide:\n"
                "• Supporting evidence or reasoning\n"
                "• Sources or basis for the claim\n"
                "• Confidence level (High/Medium/Low)\n"
                "• Potential counter-evidence or limitations\n\n"
                "STEP 4 - CONSISTENCY CHECK:\n"
                "Verify that:\n"
                "• All claims are internally consistent\n"
                "• Claims don't contradict each other\n"
                "• Reasoning follows logical patterns\n\n"
                "STEP 5 - EXTERNAL VALIDATION:\n"
                "Cross-check critical claims against:\n"
                "• Established principles or best practices\n"
                "• Common knowledge or expert consensus\n"
                "• Potential edge cases or exceptions\n\n"
                "STEP 6 - FINAL VERIFIED RESPONSE:\n"
                "Provide your final answer with:\n"
                "• Confidence indicators for key points\n"
                "• Acknowledgment of uncertainties or limitations\n"
                "• Clear distinction between verified claims and speculation"
            )
        elif intensity == "moderate":
            enhancement = (
                f"{prompt}\n\n"
                "Please use Chain-of-Verification:\n"
                "1. Provide initial answer\n"
                "2. Identify key claims and verify with evidence\n"
                "3. Check consistency and accuracy\n"
                "4. Provide final verified response with confidence levels"
            )
        else:  # minimal
            enhancement = f"{query}\n\nPlease provide evidence-based claims and verify key assertions."

        return enhancement

    async def _apply_perspective_enhancement(self, prompt: str, strategy: dict[str, Any]) -> str:
        """Apply multi-perspective enhancement."""
        return (
            f"{prompt}\n\n"
            "Please analyze this from multiple viewpoints:\n"
            "• Technical perspective\n"
            "• User experience perspective\n"
            "• Business/organizational perspective\n"
            "• Long-term maintenance perspective\n"
            "Synthesize insights from all perspectives."
        )

    async def _apply_sequential_enhancement(self, prompt: str, strategy: dict[str, Any]) -> str:
        """Apply step-by-step reasoning enhancement."""
        return (
            f"{prompt}\n\n"
            "Please think step-by-step:\n"
            "1. Break down the problem into clear components\n"
            "2. Analyze each component systematically\n"
            "3. Identify relationships and dependencies\n"
            "4. Synthesize findings into a coherent solution\n"
            "5. Validate the solution against requirements"
        )

    # Helper methods for enhancement process

    async def _get_primary_approach(self, requirements: dict[str, Any]) -> str:
        """Get primary enhancement approach based on technique type."""
        approach_mapping = {
            EnhancementType.QUERY_FANOUT: "multi_perspective_analysis",
            EnhancementType.CRITICAL_THINKING: "socratic_inquiry",
            EnhancementType.ITERATIVE_REFINEMENT: "self_improvement_cycle",
            EnhancementType.EVIDENCE_VERIFICATION: "evidence_validation",
            EnhancementType.MULTI_PERSPECTIVE: "viewpoint_integration",
            EnhancementType.STEP_BY_STEP: "sequential_reasoning",
        }

        return approach_mapping.get(self.enhancement_type, "general_enhancement")

    async def _get_domain_optimizations(self, domain_requirements: dict[str, Any]) -> list[str]:
        """Get domain-specific optimization strategies."""
        optimizations = []

        if domain_requirements.get("security_focus", False):
            optimizations.append("security_validation")

        if domain_requirements.get("performance_focus", False):
            optimizations.append("performance_optimization")

        if domain_requirements.get("architecture_focus", False):
            optimizations.append("system_design_analysis")

        return optimizations

    async def _apply_optimization(
        self,
        prompt: str,
        optimization: str,
        context: PromptingContext | None,
    ) -> str:
        """Apply specific optimization to enhanced prompt."""
        optimization_strategies = {
            "structured_decomposition": "\n\nPlease structure your response with clear sections and logical flow.",
            "clarification_enhancement": "\n\nPlease clarify any ambiguities and provide specific examples.",
            "evidence_gathering": "\n\nPlease support claims with specific evidence and examples.",
            "security_validation": "\n\nPlease address security implications and validation requirements.",
            "performance_optimization": "\n\nPlease consider performance implications and optimization opportunities.",
            "system_design_analysis": "\n\nPlease analyze system design implications and architectural considerations.",
        }

        enhancement = optimization_strategies.get(optimization, "")
        return prompt + enhancement

    async def _calculate_prompt_quality(self, prompt: str, context: PromptingContext | None) -> float:
        """Calculate quality score for a prompt (0.0 to 1.0)."""
        # Length quality
        length_score = 0.0
        if 50 <= len(prompt) <= 1000:
            length_score = 1.0
        elif len(prompt) < 50:
            length_score = len(prompt) / 50
        else:
            length_score = max(0.0, 1.0 - (len(prompt) - 1000) / 1000)

        # Structure quality
        structure_indicators = ["1.", "2.", "•", ":", "\n\n"]
        structure_score = min(1.0, sum(1 for indicator in structure_indicators if indicator in prompt) / 3)

        # Content specificity
        specific_indicators = ["implement", "design", "analyze", "create", "optimize", "solve"]
        specificity_score = min(1.0, sum(1 for indicator in specific_indicators if indicator in prompt.lower()) / 2)

        # Overall quality
        overall_quality = length_score * 0.3 + structure_score * 0.4 + specificity_score * 0.3

        return min(1.0, max(0.0, overall_quality))

    async def _calculate_complexity_score(self, prompt: str) -> float:
        """Calculate complexity score for the prompt."""
        complexity_indicators = [
            "complex",
            "multiple",
            "various",
            "integrate",
            "coordinate",
            "system",
            "architecture",
            "comprehensive",
            "detailed",
            "thorough",
        ]

        complexity_count = sum(1 for indicator in complexity_indicators if indicator in prompt.lower())
        structural_complexity = min(1.0, prompt.count(".") / 5)
        length_complexity = min(1.0, len(prompt) / 500)

        return min(1.0, (complexity_count / 3 + structural_complexity + length_complexity) / 3)

    async def _calculate_ambiguity_score(self, prompt: str) -> float:
        """Calculate ambiguity score for the prompt."""
        ambiguity_indicators = [
            "something",
            "anything",
            "help",
            "improve",
            "better",
            "some",
            "maybe",
            "perhaps",
            "could",
            "should",
            "generally",
            "usually",
        ]

        ambiguity_count = sum(1 for indicator in ambiguity_indicators if indicator in prompt.lower())
        specificity_indicators = [
            "specific",
            "exact",
            "precise",
            "implement",
            "design",
            "create",
        ]
        specificity_count = sum(1 for indicator in specificity_indicators if indicator in prompt.lower())

        raw_ambiguity = min(1.0, ambiguity_count / 3)
        specificity_reduction = min(0.5, specificity_count * 0.1)

        return max(0.0, raw_ambiguity - specificity_reduction)

    async def _analyze_domain_requirements(self, prompt: str, context: PromptingContext | None) -> dict[str, Any]:
        """Analyze domain-specific requirements."""
        domain_requirements = {
            "security_focus": any(
                word in prompt.lower() for word in ["security", "auth", "encryption", "vulnerability"]
            ),
            "performance_focus": any(
                word in prompt.lower() for word in ["performance", "optimize", "speed", "efficiency"]
            ),
            "architecture_focus": any(
                word in prompt.lower() for word in ["architecture", "design", "structure", "system"]
            ),
            "development_focus": any(
                word in prompt.lower() for word in ["code", "implement", "develop", "programming"]
            ),
        }

        if context:
            domain_requirements["context_domain"] = context.domain
            domain_requirements["context_complexity"] = context.complexity

        return domain_requirements

    async def _validate_enhancement_quality(
        self,
        original_quality: float,
        enhanced_quality: float,
        strategy: dict[str, Any],
    ) -> bool:
        """Validate that enhancement meets quality requirements."""
        improvement = enhanced_quality - original_quality

        # Minimum improvement threshold
        min_improvement = 0.1 if strategy.get("intensity_level") == "minimal" else 0.15

        return improvement >= min_improvement

    async def _validate_constitutional_compliance(
        self,
        enhanced_prompt: str,
        context: PromptingContext | None,
    ) -> dict[str, bool]:
        """Validate constitutional compliance for enhanced prompt."""
        compliance = {
            "solo_developer_friendly": len(enhanced_prompt) < 2000,  # Reasonable length
            "evidence_based": "evidence" in enhanced_prompt.lower() or "verify" in enhanced_prompt.lower(),
            "anti_deception": "claim" in enhanced_prompt.lower() or "confidence" in enhanced_prompt.lower(),
            "transparency": "step" in enhanced_prompt.lower() or "process" in enhanced_prompt.lower(),
            "practical_approach": not (
                "theoretical" in enhanced_prompt.lower() and "practical" not in enhanced_prompt.lower()
            ),
        }

        return compliance

    async def _generate_transparency_explanation(
        self,
        strategy: dict[str, Any],
        metrics: EnhancementMetrics,
    ) -> str:
        """Generate transparency explanation for the enhancement."""
        explanation_parts = [
            f"Applied {self.enhancement_type.value.replace('_', ' ').title()} enhancement",
            f"Strategy: {strategy.get('primary_approach', 'general_enhancement').replace('_', ' ').title()}",
            f"Intensity: {strategy.get('intensity_level', 'moderate').title()}",
            f"Quality improvement: {metrics.improvement_percentage:.1f}%",
            f"Processing time: {metrics.processing_time:.2f}s",
        ]

        if strategy.get("optimizations"):
            explanation_parts.append(f"Optimizations applied: {', '.join(strategy['optimizations'])}")

        return "\n".join(explanation_parts)

    async def _generate_user_guidance(self, strategy: dict[str, Any]) -> str | None:
        """Generate user guidance for understanding the enhancement."""
        if strategy.get("intensity_level") == "high":
            return (
                "This enhancement provides a comprehensive framework for analysis. "
                "Follow the structured approach to ensure thorough coverage of the topic."
            )
        if strategy.get("intensity_level") == "moderate":
            return (
                "This enhancement adds structure and guidance to improve response quality. "
                "Use the provided framework to organize your thinking."
            )

        return None

    async def _update_learning_systems(
        self,
        original_prompt: str,
        enhanced_prompt: str,
        metrics: EnhancementMetrics,
        context: PromptingContext | None,
    ) -> None:
        """Update learning systems with enhancement data."""
        # Update context patterns
        context_hash = self._generate_context_hash(context)
        if context_hash not in self.context_patterns:
            self.context_patterns[context_hash] = {
                "count": 0,
                "total_improvement": 0.0,
                "technique_effectiveness": 0.0,
            }

        pattern = self.context_patterns[context_hash]
        pattern["count"] += 1
        pattern["total_improvement"] += metrics.improvement_percentage
        pattern["technique_effectiveness"] = pattern["total_improvement"] / pattern["count"]

    def _generate_context_hash(self, context: PromptingContext | None) -> str:
        """Generate hash for context identification."""
        if not context:
            return "no_context"

        context_string = f"{context.domain}:{context.complexity}:{context.user_intent}"
        return str(hash(context_string))

    async def _create_fallback_result(
        self,
        prompt: str,
        original_quality: float,
        start_time: float,
        error_message: str,
    ) -> CognitiveEnhancementResult:
        """Create fallback result when enhancement fails."""
        processing_time = time.time() - start_time

        return CognitiveEnhancementResult(
            enhanced_prompt=prompt,
            enhancement_type=self.enhancement_type,
            technique_name=self.technique.value,
            quality_metrics=EnhancementMetrics(
                original_quality_score=original_quality,
                enhanced_quality_score=original_quality,
                improvement_percentage=0.0,
                processing_time=processing_time,
                memory_usage=0.0,
                cpu_usage=0.0,
                technique_success_rate=0.0,
            ),
            confidence_score=0.2,
            processing_steps=[f"Enhancement failed: {error_message}"],
            optimization_applied=[],
            constitutional_compliance={"error_fallback": True},
            quality_validation_passed=False,
            transparency_explanation=f"Enhancement failed due to error: {error_message}",
            user_guidance="Please try again or rephrase your query.",
        )

    # Abstract method implementations (required by base class)

    async def is_applicable(self, context: PromptingContext) -> bool:
        """Determine if this enhanced technique is applicable."""
        # Enhanced techniques are generally more broadly applicable
        base_applicable = await super().is_applicable(context)

        # Consider enhancement-specific factors
        if self.enhancement_type == EnhancementType.EVIDENCE_VERIFICATION:
            return base_applicable or context.has_evidence_requirements()
        if self.enhancement_type == EnhancementType.CRITICAL_THINKING:
            return base_applicable or context.complexity in ["complex", "expert"]
        if self.enhancement_type == EnhancementType.QUERY_FANOUT:
            return base_applicable or len(context.query) > 100

        return base_applicable

    async def get_applicability_confidence(self, context: PromptingContext) -> float:
        """Get confidence score for enhanced technique applicability."""
        base_confidence = await super().get_applicability_confidence(context)

        # Boost confidence based on enhancement capabilities
        if self.enhancement_type == EnhancementType.ITERATIVE_REFINEMENT:
            return min(1.0, base_confidence + 0.1)  # Self-refinement is broadly useful
        if self.enhancement_type == EnhancementType.EVIDENCE_VERIFICATION and context.has_evidence_requirements():
            return min(1.0, base_confidence + 0.2)  # High value for evidence-based domains

        return base_confidence

    async def apply_technique(self, prompt: str, context: PromptingContext) -> str:
        """Apply the enhanced technique to the prompt."""
        # Use the cognitive enhancement system
        enhancement_result = await self.apply_cognitive_enhancement(prompt, context)

        return enhancement_result.enhanced_prompt

    # Performance and optimization methods

    def get_performance_statistics(self) -> dict[str, Any]:
        """Get performance statistics for the enhanced technique."""
        if not self.performance_history:
            return {"status": "No performance data available"}

        avg_improvement = sum(m.improvement_percentage for m in self.performance_history) / len(
            self.performance_history,
        )
        avg_processing_time = sum(m.processing_time for m in self.performance_history) / len(self.performance_history)
        avg_success_rate = sum(m.technique_success_rate for m in self.performance_history) / len(
            self.performance_history,
        )

        return {
            "technique": self.technique.value,
            "enhancement_type": self.enhancement_type.value,
            "total_applications": len(self.performance_history),
            "average_improvement_percentage": avg_improvement,
            "average_processing_time": avg_processing_time,
            "average_success_rate": avg_success_rate,
            "context_patterns_learned": len(self.context_patterns),
            "recent_performance": [
                {
                    "improvement": m.improvement_percentage,
                    "processing_time": m.processing_time,
                    "success_rate": m.technique_success_rate,
                }
                for m in self.performance_history[-5:]
            ],
        }

    def clear_performance_history(self) -> None:
        """Clear performance history and reset learning systems."""
        self.performance_history.clear()
        self.context_patterns.clear()
        self.success_patterns.clear()
        self.logger.info("Performance history and learning systems cleared")

    async def optimize_performance(self) -> dict[str, Any]:
        """Optimize technique performance based on historical data."""
        if not self.performance_history:
            return {"optimization_applied": False, "reason": "No performance data available"}

        optimizations = []

        # Analyze recent performance trends
        recent_performance = self.performance_history[-10:]
        avg_recent_improvement = sum(m.improvement_percentage for m in recent_performance) / len(recent_performance)

        if avg_recent_improvement < 15:  # Below threshold
            # Increase enhancement intensity
            self.max_enhancement_time = min(3.0, self.max_enhancement_time * 1.1)
            optimizations.append("increased_enhancement_time")

        # Analyze processing time patterns
        avg_processing_time = sum(m.processing_time for m in recent_performance) / len(recent_performance)
        if avg_processing_time > 1.5:  # Too slow
            optimizations.append("performance_optimization_needed")

        return {
            "optimization_applied": len(optimizations) > 0,
            "optimizations": optimizations,
            "performance_analysis": {
                "recent_avg_improvement": avg_recent_improvement,
                "recent_avg_processing_time": avg_processing_time,
                "total_applications_analyzed": len(recent_performance),
            },
        }


# Specific enhanced technique implementations


class EnhancedQueryFanoutTechnique(EnhancedBasePromptingTechnique):
    """Enhanced QueryFanout technique with multi-perspective analysis."""

    def __init__(self):
        super().__init__(PromptingTechnique.QUERY_FANOUT, EnhancementType.MULTI_PERSPECTIVE)

    def supports_evidence_based_reasoning(self) -> bool:
        return True

    def supports_system_design(self) -> bool:
        return True

    def supports_scalability_analysis(self) -> bool:
        return True


class EnhancedSocraticTechnique(EnhancedBasePromptingTechnique):
    """Enhanced Socratic technique with critical thinking framework."""

    def __init__(self):
        super().__init__(PromptingTechnique.SOCRATIC, EnhancementType.CRITICAL_THINKING)

    def supports_evidence_based_reasoning(self) -> bool:
        return True

    def supports_threat_modeling(self) -> bool:
        return True


class EnhancedSelfRefineTechnique(EnhancedBasePromptingTechnique):
    """Enhanced Self-Refine technique with iterative improvement."""

    def __init__(self):
        super().__init__(PromptingTechnique.SELF_REFINE, EnhancementType.ITERATIVE_REFINEMENT)

    def supports_optimization(self) -> bool:
        return True

    def supports_system_design(self) -> bool:
        return True


class EnhancedChainOfVerificationTechnique(EnhancedBasePromptingTechnique):
    """Enhanced Chain-of-Verification technique with evidence validation."""

    def __init__(self):
        super().__init__(PromptingTechnique.CHAIN_OF_VERIFICATION, EnhancementType.EVIDENCE_VERIFICATION)

    def supports_evidence_based_reasoning(self) -> bool:
        return True

    def supports_threat_modeling(self) -> bool:
        return True

    def supports_benchmarking(self) -> bool:
        return True
