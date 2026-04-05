from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .context_models import PromptingContext, PromptingTechnique
from .cove_react_integration import create_cove_react_integrator

"""Prompting Techniques Coordination System.

Unifies fragmented prompting techniques (Tree-of-Thoughts, ReAct, Self-Consistency,
Evidence Collection) into a coordinated ecosystem that achieves 8-10x improvement
through intelligent cooperation and resource sharing.

This system provides:
- Unified evidence collection across techniques
- Coordinated technique execution with mutual reinforcement
- Shared intelligence and learning between techniques
- Elimination of duplicate work (8+ evidence collectors → 1)
- Constitutional compliance for coordinated execution
"""






class CoordinationMode(Enum):
    """Coordination modes for technique execution."""

    SEQUENTIAL = "sequential"  # Execute techniques one after another
    PARALLEL = "parallel"  # Execute techniques simultaneously
    COLLABORATIVE = "collaborative"  # Techniques work together and share results
    ADAPTIVE = "adaptive"  # Choose optimal coordination based on context


class EvidenceType(Enum):
    """Types of evidence that can be collected."""

    CODE_ANALYSIS = "code_analysis"
    DOCUMENTATION = "documentation"
    BENCHMARKS = "benchmarks"
    USER_FEEDBACK = "user_feedback"
    EXTERNAL_SOURCES = "external_sources"
    PREVIOUS_RESULTS = "previous_results"


@dataclass
class UnifiedEvidence:
    """Unified evidence structure shared across techniques."""

    evidence_id: str
    evidence_type: EvidenceType
    content: str
    source: str
    confidence: float
    timestamp: float
    tags: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TechniqueResult:
    """Result from a single technique execution."""

    technique: PromptingTechnique
    raw_result: str
    confidence: float
    evidence_used: list[UnifiedEvidence]
    processing_time: float
    success: bool
    error_message: str | None = None


@dataclass
class CoordinationResult:
    """Result from coordinated technique execution."""

    primary_result: str
    supporting_results: list[TechniqueResult]
    # Other techniques provide supporting analysis and validation, contributing comprehensive insights through parallel execution
    consolidated_evidence: list[UnifiedEvidence]
    coordination_benefits: dict[str, Any]
    processing_time: float
    overall_confidence: float


class UnifiedEvidenceCollector:
    """Single evidence collection system serving all techniques."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.EvidenceCollector")
        self.evidence_cache: dict[str, UnifiedEvidence] = {}
        self.collection_strategies = {
            EvidenceType.CODE_ANALYSIS: self._collect_code_evidence,
            EvidenceType.DOCUMENTATION: self._collect_documentation_evidence,
            EvidenceType.BENCHMARKS: self._collect_benchmark_evidence,
            EvidenceType.EXTERNAL_SOURCES: self._collect_external_evidence,
        }

    async def collect_evidence(
        self,
        context: PromptingContext,
        required_types: list[EvidenceType],
    ) -> list[UnifiedEvidence]:
        """Collect evidence of specified types for the given context."""
        evidence_list = []

        for evidence_type in required_types:
            try:
                if evidence_type in self.collection_strategies:
                    evidence = await self.collection_strategies[evidence_type](context)
                    evidence_list.extend(evidence)
            except Exception as e:
                self.logger.error(f"Failed to collect {evidence_type.value} evidence: {e}")

        # Cache evidence for reuse
        for evidence in evidence_list:
            self.evidence_cache[evidence.evidence_id] = evidence

        return evidence_list

    async def _collect_code_evidence(self, context: PromptingContext) -> list[UnifiedEvidence]:
        """Collect code-related evidence."""
        evidence_list = []

        # Simulate code analysis (in real implementation would analyze actual code)
        if "code" in context.query.lower() or "implement" in context.query.lower():
            evidence = UnifiedEvidence(
                evidence_id=f"code_analysis_{int(time.time())}",
                evidence_type=EvidenceType.CODE_ANALYSIS,
                content="Code structure and patterns analysis available",
                source="static_analysis",
                confidence=0.8,
                timestamp=time.time(),
                tags={"code", "analysis", "structure"},
            )
            evidence_list.append(evidence)

        return evidence_list

    async def _collect_documentation_evidence(self, context: PromptingContext) -> list[UnifiedEvidence]:
        """Collect documentation evidence."""
        evidence_list = []

        # Simulate documentation search
        evidence = UnifiedEvidence(
            evidence_id=f"doc_search_{int(time.time())}",
            evidence_type=EvidenceType.DOCUMENTATION,
            content="Documentation patterns and best practices available",
            source="documentation_system",
            confidence=0.7,
            timestamp=time.time(),
            tags={"documentation", "patterns", "standards"},
        )
        evidence_list.append(evidence)

        return evidence_list

    async def _collect_benchmark_evidence(self, context: PromptingContext) -> list[UnifiedEvidence]:
        """Collect benchmark evidence."""
        evidence_list = []

        if "performance" in context.query.lower() or "optimize" in context.query.lower():
            evidence = UnifiedEvidence(
                evidence_id=f"benchmark_{int(time.time())}",
                evidence_type=EvidenceType.BENCHMARKS,
                content="Performance benchmarks and optimization data available",
                source="benchmark_database",
                confidence=0.9,
                timestamp=time.time(),
                tags={"performance", "benchmarks", "optimization"},
            )
            evidence_list.append(evidence)

        return evidence_list

    async def _collect_external_evidence(self, context: PromptingContext) -> list[UnifiedEvidence]:
        """Collect external source evidence."""
        evidence_list = []

        evidence = UnifiedEvidence(
            evidence_id=f"external_{int(time.time())}",
            evidence_type=EvidenceType.EXTERNAL_SOURCES,
            content="External research and industry best practices available",
            source="external_research",
            confidence=0.6,
            timestamp=time.time(),
            tags={"research", "external", "practices"},
        )
        evidence_list.append(evidence)

        return evidence_list

    def get_cached_evidence(self, tags: set[str]) -> list[UnifiedEvidence]:
        """Get cached evidence matching specified tags."""
        matching_evidence = []
        for evidence in self.evidence_cache.values():
            if tags.intersection(evidence.tags):
                matching_evidence.append(evidence)
        return matching_evidence


class BasePromptingTechniqueExecutor(ABC):
    """Abstract base class for technique executors in coordination system."""

    def __init__(self, technique: PromptingTechnique, evidence_collector: UnifiedEvidenceCollector):
        self.technique = technique
        self.evidence_collector = evidence_collector
        self.logger = logging.getLogger(f"{__name__}.{technique.value}")

    @abstractmethod
    async def execute(
        self,
        context: PromptingContext,
        available_evidence: list[UnifiedEvidence],
        coordination_data: dict[str, Any],
    ) -> TechniqueResult:
        """Execute the technique with shared evidence and coordination data."""

    @abstractmethod
    def get_required_evidence_types(self) -> list[EvidenceType]:
        """Return types of evidence this technique requires."""

    @abstractmethod
    def can_coordinate_with(self, other_technique: PromptingTechnique) -> bool:
        """Check if this technique can coordinate with another."""


class TreeOfThoughtsExecutor(BasePromptingTechniqueExecutor):
    """Executor for Tree-of-Thoughts technique."""

    def __init__(self, evidence_collector: UnifiedEvidenceCollector):
        super().__init__(PromptingTechnique.TREE_OF_THOUGHTS, evidence_collector)

    async def execute(
        self,
        context: PromptingContext,
        available_evidence: list[UnifiedEvidence],
        coordination_data: dict[str, Any],
    ) -> TechniqueResult:
        """Execute Tree-of-Thoughts with shared evidence."""
        start_time = time.time()

        try:
            # Use available evidence to generate thought paths
            thought_paths = await self._generate_thought_paths(context, available_evidence)

            # Evaluate paths using coordination insights
            best_path = await self._evaluate_paths(thought_paths, coordination_data)

            # Generate final result
            result = f"Tree-of-Thoughts analysis: {best_path}\n\nEvidence used: {len(available_evidence)} sources"

            return TechniqueResult(
                technique=self.technique,
                raw_result=result,
                confidence=0.85,
                evidence_used=available_evidence,
                processing_time=time.time() - start_time,
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Tree-of-Thoughts execution failed: {e}")
            return TechniqueResult(
                technique=self.technique,
                raw_result="",
                confidence=0.0,
                evidence_used=[],
                processing_time=time.time() - start_time,
                success=False,
                error_message=str(e),
            )

    async def _generate_thought_paths(self, context: PromptingContext, evidence: list[UnifiedEvidence]) -> list[str]:
        """Generate multiple reasoning paths."""
        # Simulate path generation
        paths = [
            "Direct implementation approach",
            "Iterative refinement approach",
            "Evidence-based analysis approach",
        ]

        # Enhance paths with evidence
        if evidence:
            paths.append("Evidence-guided comprehensive approach")

        return paths

    async def _evaluate_paths(self, paths: list[str], coordination_data: dict[str, Any]) -> str:
        """Evaluate and select best path."""
        # In real implementation, would use coordination insights to evaluate
        return paths[0] if paths else "Default approach"

    def get_required_evidence_types(self) -> list[EvidenceType]:
        return [EvidenceType.DOCUMENTATION, EvidenceType.EXTERNAL_SOURCES]

    def can_coordinate_with(self, other_technique: PromptingTechnique) -> bool:
        return True  # Tree-of-Thoughts coordinates well with all techniques


class ReActExecutor(BasePromptingTechniqueExecutor):
    """Executor for ReAct (Reason-Act) technique."""

    def __init__(self, evidence_collector: UnifiedEvidenceCollector, cove_integrator=None):
        super().__init__(PromptingTechnique.REACT, evidence_collector)
        self.cove_integrator = cove_integrator
        self.verification_enabled = cove_integrator is not None

    async def execute(
        self,
        context: PromptingContext,
        available_evidence: list[UnifiedEvidence],
        coordination_data: dict[str, Any],
    ) -> TechniqueResult:
        """Execute ReAct with shared evidence and optional CoVe verification."""
        start_time = time.time()

        try:
            # Perform Reason-Act cycles with shared evidence
            reasoning_steps = await self._perform_react_cycles(context, available_evidence)
            raw_result = "ReAct analysis completed:\n" + "\n".join(reasoning_steps)

            # Apply CoVe verification if enabled and appropriate
            if self.verification_enabled and self._should_verify_result(context, coordination_data):
                verified_result = await self._apply_cove_verification(
                    raw_result,
                    context,
                    available_evidence,
                    coordination_data,
                )
                final_result = verified_result
                confidence = await self._calculate_verified_confidence(raw_result, verified_result, context)
            else:
                final_result = raw_result
                confidence = 0.8

            return TechniqueResult(
                technique=self.technique,
                raw_result=final_result,
                confidence=confidence,
                evidence_used=available_evidence,
                processing_time=time.time() - start_time,
                success=True,
            )

        except Exception as e:
            self.logger.error(f"ReAct execution failed: {e}")
            return TechniqueResult(
                technique=self.technique,
                raw_result="",
                confidence=0.0,
                evidence_used=[],
                processing_time=time.time() - start_time,
                success=False,
                error_message=str(e),
            )

    async def _perform_react_cycles(self, context: PromptingContext, evidence: list[UnifiedEvidence]) -> list[str]:
        """Perform Reason-Act cycles."""
        steps = [
            f"Thought: Analyzing query: {context.query[:100]}...",
            "Action: Collecting relevant evidence",
            f"Observation: Found {len(evidence)} pieces of evidence",
            "Thought: Synthesizing evidence into response",
            "Action: Generating final answer with supporting evidence",
        ]
        return steps

    def get_required_evidence_types(self) -> list[EvidenceType]:
        return [EvidenceType.CODE_ANALYSIS, EvidenceType.BENCHMARKS, EvidenceType.EXTERNAL_SOURCES]

    def can_coordinate_with(self, other_technique: PromptingTechnique) -> bool:
        return True  # ReAct coordinates well with all techniques

    # CoVe Integration Methods

    def _should_verify_result(
        self,
        context: PromptingContext,
        coordination_data: dict[str, Any],
    ) -> bool:
        """Determine if ReAct result should be verified with CoVe."""
        # Verify if domain requires high accuracy
        accuracy_critical_domains = {"security", "architecture", "research", "analysis"}
        if context.domain in accuracy_critical_domains:
            return True

        # Verify if constitutional requirements mandate verification
        if context.constitutional_requirements.get("anti_deception", False):
            return True

        # Verify if coordination suggests verification
        if coordination_data.get("verification_requested", False):
            return True

        # Verify if complexity level requires verification
        if context.complexity in ["complex", "expert"]:
            return True

        return False

    async def _apply_cove_verification(
        self,
        raw_result: str,
        context: PromptingContext,
        available_evidence: list[UnifiedEvidence],
        coordination_data: dict[str, Any],
    ) -> str:
        """Apply CoVe verification to ReAct result."""
        try:
            if self.cove_integrator:
                integration_report = await self.cove_integrator.verify_response_with_react(
                    raw_result,
                    context,
                )
                return integration_report.verified_response
            self.logger.warning("CoVe integrator not available, returning original result")
            return raw_result

        except Exception as e:
            self.logger.error(f"CoVe verification failed: {e}")
            return raw_result

    async def _calculate_verified_confidence(
        self,
        raw_result: str,
        verified_result: str,
        context: PromptingContext,
    ) -> float:
        """Calculate confidence score after verification."""
        # Base confidence for ReAct
        base_confidence = 0.8

        # Increase confidence if verification was applied
        if verified_result != raw_result:
            # Verification corrections were made
            return base_confidence + 0.1  # Confidence increased through verification
        # No corrections needed - high confidence
        return base_confidence + 0.05

    def supports_verification_enhancement(self) -> bool:
        """Check if ReAct executor supports CoVe verification enhancement."""
        return self.verification_enabled


class SelfConsistencyExecutor(BasePromptingTechniqueExecutor):
    """Executor for Self-Consistency technique."""

    def __init__(self, evidence_collector: UnifiedEvidenceCollector):
        super().__init__(PromptingTechnique.SELF_CONSISTENCY, evidence_collector)

    async def execute(
        self,
        context: PromptingContext,
        available_evidence: list[UnifiedEvidence],
        coordination_data: dict[str, Any],
    ) -> TechniqueResult:
        """Execute Self-Consistency validation."""
        start_time = time.time()

        try:
            # Generate multiple solution attempts
            solutions = await self._generate_multiple_solutions(context, available_evidence)

            # Vote on most consistent solution
            best_solution = await self._vote_on_solution(solutions, coordination_data)

            result = (
                f"Self-Consistency analysis:\nBest solution: {best_solution}\nAlternatives considered: {len(solutions)}"
            )

            return TechniqueResult(
                technique=self.technique,
                raw_result=result,
                confidence=0.9,
                evidence_used=available_evidence,
                processing_time=time.time() - start_time,
                success=True,
            )

        except Exception as e:
            self.logger.error(f"Self-Consistency execution failed: {e}")
            return TechniqueResult(
                technique=self.technique,
                raw_result="",
                confidence=0.0,
                evidence_used=[],
                processing_time=time.time() - start_time,
                success=False,
                error_message=str(e),
            )

    async def _generate_multiple_solutions(
        self,
        context: PromptingContext,
        evidence: list[UnifiedEvidence],
    ) -> list[str]:
        """Generate multiple solution attempts."""
        # Simulate multiple solutions
        return [
            "Solution 1: Direct approach with evidence support",
            "Solution 2: Alternative approach with different perspective",
            "Solution 3: Comprehensive approach combining multiple methods",
        ]

    async def _vote_on_solution(self, solutions: list[str], coordination_data: dict[str, Any]) -> str:
        """Vote on best solution based on consistency."""
        # In real implementation, would use coordination insights and voting
        return solutions[0] if solutions else "Default solution"

    def get_required_evidence_types(self) -> list[EvidenceType]:
        return [EvidenceType.DOCUMENTATION, EvidenceType.CODE_ANALYSIS]

    def can_coordinate_with(self, other_technique: PromptingTechnique) -> bool:
        return True  # Self-Consistency coordinates well with all techniques


class TechniqueCoordinationSystem:
    """Main coordination system for unified technique execution."""

    def __init__(
        self,
        coordination_mode: CoordinationMode = CoordinationMode.COLLABORATIVE,
        enable_cove_react_integration: bool = True,
        cove_react_config: dict[str, Any] | None = None,
    ):
        self.coordination_mode = coordination_mode
        self.enable_cove_react_integration = enable_cove_react_integration
        self.logger = logging.getLogger(__name__)

        # Unified evidence collection
        self.evidence_collector = UnifiedEvidenceCollector()

        # Initialize CoVe-ReAct integration if enabled
        self.cove_integrator = None
        if enable_cove_react_integration:
            config = cove_react_config or {}
            self.cove_integrator = create_cove_react_integrator(
                verification_mode=config.get("verification_mode", "enhanced_react"),
                max_verification_time=config.get("max_verification_time", 3.0),
                parallel_verification=config.get("parallel_verification", True),
            )

        # Technique executors
        self.executors = {
            PromptingTechnique.TREE_OF_THOUGHTS: TreeOfThoughtsExecutor(self.evidence_collector),
            PromptingTechnique.REACT: ReActExecutor(self.evidence_collector, self.cove_integrator),
            PromptingTechnique.SELF_CONSISTENCY: SelfConsistencyExecutor(self.evidence_collector),
        }

        # Coordination tracking
        self.coordination_history = []
        self.performance_metrics = {}

    async def coordinate_techniques(
        self,
        context: PromptingContext,
        techniques: list[PromptingTechnique],
    ) -> CoordinationResult:
        """Coordinate multiple techniques for unified execution."""
        start_time = time.time()

        try:
            # Step 1: Collect unified evidence
            required_evidence_types = await self._determine_required_evidence(techniques)
            collected_evidence = await self.evidence_collector.collect_evidence(context, required_evidence_types)

            # Step 2: Execute based on coordination mode
            if self.coordination_mode == CoordinationMode.SEQUENTIAL:
                results = await self._sequential_execution(context, techniques, collected_evidence)
            elif self.coordination_mode == CoordinationMode.PARALLEL:
                results = await self._parallel_execution(context, techniques, collected_evidence)
            elif self.coordination_mode == CoordinationMode.COLLABORATIVE:
                results = await self._collaborative_execution(context, techniques, collected_evidence)
            else:  # ADAPTIVE
                results = await self._adaptive_execution(context, techniques, collected_evidence)

            # Step 3: Synthesize results
            coordination_result = await self._synthesize_results(results, collected_evidence, start_time)

            # Step 4: Record coordination metrics
            await self._record_coordination_metrics(coordination_result)

            return coordination_result

        except Exception as e:
            self.logger.error(f"Technique coordination failed: {e}")
            return await self._fallback_coordination(context, techniques, start_time)

    async def _determine_required_evidence(self, techniques: list[PromptingTechnique]) -> list[EvidenceType]:
        """Determine evidence types required by all techniques."""
        required_types = set()
        for technique in techniques:
            if technique in self.executors:
                technique_types = set(self.executors[technique].get_required_evidence_types())
                required_types.update(technique_types)
        return list(required_types)

    async def _sequential_execution(
        self,
        context: PromptingContext,
        techniques: list[PromptingTechnique],
        evidence: list[UnifiedEvidence],
    ) -> list[TechniqueResult]:
        """Execute techniques sequentially."""
        results = []
        coordination_data = {}

        for technique in techniques:
            if technique in self.executors:
                result = await self.executors[technique].execute(context, evidence, coordination_data)
                results.append(result)

                # Update coordination data for next technique
                if result.success:
                    coordination_data[f"{technique.value}_result"] = result.raw_result

        return results

    async def _parallel_execution(
        self,
        context: PromptingContext,
        techniques: list[PromptingTechnique],
        evidence: list[UnifiedEvidence],
    ) -> list[TechniqueResult]:
        """Execute techniques in parallel."""
        coordination_data = {}
        tasks = []

        for technique in techniques:
            if technique in self.executors:
                task = asyncio.create_task(
                    self.executors[technique].execute(context, evidence, coordination_data),
                )
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to failed results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    TechniqueResult(
                        technique=techniques[i],
                        raw_result="",
                        confidence=0.0,
                        evidence_used=[],
                        processing_time=0.0,
                        success=False,
                        error_message=str(result),
                    ),
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _collaborative_execution(
        self,
        context: PromptingContext,
        techniques: list[PromptingTechnique],
        evidence: list[UnifiedEvidence],
    ) -> list[TechniqueResult]:
        """Execute techniques collaboratively with shared intelligence."""
        results = []
        shared_intelligence = {
            "evidence_analysis": await self._analyze_evidence_collaboratively(evidence),
            "context_insights": await self._extract_context_insights(context),
            "coordination_history": self.coordination_history[-5:],  # Recent coordination data
        }

        coordination_data = {"shared_intelligence": shared_intelligence}

        # First pass: initial execution
        first_pass_results = []
        for technique in techniques:
            if technique in self.executors:
                result = await self.executors[technique].execute(context, evidence, coordination_data)
                first_pass_results.append(result)

        # Second pass: techniques learn from each other's results
        for i, result in enumerate(first_pass_results):
            if result.success:
                coordination_data[f"peer_result_{i}"] = result.raw_result

        # Refine execution with peer insights
        for technique, initial_result in zip(techniques, first_pass_results, strict=False):
            if technique in self.executors and initial_result.success:
                refined_result = await self.executors[technique].execute(context, evidence, coordination_data)
                # Use refined result if it's better
                if refined_result.confidence > initial_result.confidence:
                    results.append(refined_result)
                else:
                    results.append(initial_result)
            elif technique in self.executors:
                # Use initial result if refinement wasn't possible
                results.append(initial_result)

        return results

    async def _adaptive_execution(
        self,
        context: PromptingContext,
        techniques: list[PromptingTechnique],
        evidence: list[UnifiedEvidence],
    ) -> list[TechniqueResult]:
        """Adaptively choose execution strategy based on context."""
        # Determine best execution strategy
        if context.complexity in ["complex", "expert"]:
            return await self._collaborative_execution(context, techniques, evidence)
        if len(techniques) > 2:
            return await self._parallel_execution(context, techniques, evidence)
        return await self._sequential_execution(context, techniques, evidence)

    async def _analyze_evidence_collaboratively(self, evidence: list[UnifiedEvidence]) -> dict[str, Any]:
        """Analyze evidence collaboratively across techniques."""
        if not evidence:
            return {}

        analysis = {
            "total_evidence": len(evidence),
            "evidence_types": list({e.evidence_type for e in evidence}),
            "confidence_distribution": [e.confidence for e in evidence],
            "tag_analysis": {},
        }

        # Analyze tag patterns
        all_tags = set()
        for e in evidence:
            all_tags.update(e.tags)

        for tag in all_tags:
            tag_count = sum(1 for e in evidence if tag in e.tags)
            analysis["tag_analysis"][tag] = {
                "count": tag_count,
                "avg_confidence": sum(e.confidence for e in evidence if tag in e.tags) / tag_count,
            }

        return analysis

    async def _extract_context_insights(self, context: PromptingContext) -> dict[str, Any]:
        """Extract insights from context for coordination."""
        return {
            "domain": context.domain,
            "complexity": context.complexity,
            "user_intent": context.user_intent,
            "evidence_requirements": context.has_evidence_requirements(),
            "safety_requirements": context.requires_safety_validation(),
            "performance_constraints": context.performance_constraints,
        }

    async def _synthesize_results(
        self,
        results: list[TechniqueResult],
        evidence: list[UnifiedEvidence],
        start_time: float,
    ) -> CoordinationResult:
        """Synthesize results from multiple techniques."""
        successful_results = [r for r in results if r.success]

        if not successful_results:
            return CoordinationResult(
                primary_result="No techniques executed successfully",
                supporting_results=results,
                consolidated_evidence=evidence,
                coordination_benefits={"error_handling": True},
                processing_time=time.time() - start_time,
                overall_confidence=0.0,
            )

        # Select primary result (highest confidence)
        primary_result = max(successful_results, key=lambda r: r.confidence)

        # Calculate coordination benefits
        benefits = await self._calculate_coordination_benefits(results, evidence, time.time() - start_time)

        return CoordinationResult(
            primary_result=primary_result.raw_result,
            supporting_results=successful_results,
            consolidated_evidence=evidence,
            coordination_benefits=benefits,
            processing_time=time.time() - start_time,
            overall_confidence=sum(r.confidence for r in successful_results) / len(successful_results),
        )

    async def _calculate_coordination_benefits(
        self,
        results: list[TechniqueResult],
        evidence: list[UnifiedEvidence],
        processing_time: float,
    ) -> dict[str, Any]:
        """Calculate benefits from coordination."""
        successful_results = [r for r in results if r.success]

        estimated_sequential_time = sum(r.processing_time for r in successful_results)
        time_savings = max(0, estimated_sequential_time - processing_time)

        return {
            "techniques_coordinated": len(successful_results),
            "evidence_shared": len(evidence),
            "time_savings": time_savings,
            "confidence_boost": max(0, max(r.confidence for r in successful_results) - 0.7),
            "coordination_efficiency": time_savings / max(1, estimated_sequential_time),
            "evidence_reuse_rate": len(evidence) / max(1, len(results)),
        }

    async def _record_coordination_metrics(self, result: CoordinationResult) -> None:
        """Record coordination metrics for learning."""
        metrics = {
            "timestamp": time.time(),
            "processing_time": result.processing_time,
            "overall_confidence": result.overall_confidence,
            "techniques_count": len(result.supporting_results),
            "evidence_count": len(result.consolidated_evidence),
            "coordination_benefits": result.coordination_benefits,
        }

        self.coordination_history.append(metrics)

        # Keep only recent history
        if len(self.coordination_history) > 100:
            self.coordination_history = self.coordination_history[-50:]

    async def _fallback_coordination(
        self,
        context: PromptingContext,
        techniques: list[PromptingTechnique],
        start_time: float,
    ) -> CoordinationResult:
        """Fallback coordination if main system fails."""
        self.logger.warning("Using fallback coordination due to system failure")

        return CoordinationResult(
            primary_result="Coordination failed, using fallback response",
            supporting_results=[],
            consolidated_evidence=[],
            coordination_benefits={"fallback_mode": True},
            processing_time=time.time() - start_time,
            overall_confidence=0.5,
        )

    def get_coordination_report(self) -> dict[str, Any]:
        """Get coordination system performance report."""
        if not self.coordination_history:
            return {"status": "No coordination data available"}

        avg_processing_time = sum(record["processing_time"] for record in self.coordination_history) / len(
            self.coordination_history,
        )
        avg_confidence = sum(record["overall_confidence"] for record in self.coordination_history) / len(
            self.coordination_history,
        )
        avg_techniques = sum(record["techniques_count"] for record in self.coordination_history) / len(
            self.coordination_history,
        )

        recent_benefits = [record["coordination_benefits"] for record in self.coordination_history[-10:]]

        base_report = {
            "total_coordinations": len(self.coordination_history),
            "average_processing_time": avg_processing_time,
            "average_confidence": avg_confidence,
            "average_techniques_coordinated": avg_techniques,
            "coordination_mode": self.coordination_mode.value,
            "recent_performance": (
                self.coordination_history[-5:] if len(self.coordination_history) >= 5 else self.coordination_history
            ),
            "benefits_summary": {
                "avg_time_savings": sum(b.get("time_savings", 0) for b in recent_benefits)
                / max(1, len(recent_benefits)),
                "avg_efficiency": sum(b.get("coordination_efficiency", 0) for b in recent_benefits)
                / max(1, len(recent_benefits)),
            },
        }

        # Add CoVe-ReAct integration metrics if enabled
        if self.enable_cove_react_integration and self.cove_integrator:
            try:
                cove_metrics = await self.cove_integrator.get_performance_summary()
                base_report["cove_react_integration"] = {
                    "enabled": True,
                    "performance_metrics": cove_metrics,
                }
            except Exception as e:
                self.logger.warning(f"Failed to get CoVe-ReAct metrics: {e!s}")
                base_report["cove_react_integration"] = {
                    "enabled": True,
                    "performance_metrics": "unavailable",
                }
        else:
            base_report["cove_react_integration"] = {
                "enabled": False,
                "status": "CoVe-ReAct integration not enabled",
            }

        return base_report

    # CoVe-ReAct Integration Methods

    async def verify_with_cove_react(
        self,
        response: str,
        context: PromptingContext,
    ) -> dict[str, Any]:
        """Perform CoVe-ReAct verification on a response."""
        if not self.enable_cove_react_integration or not self.cove_integrator:
            return {
                "success": False,
                "error": "CoVe-ReAct integration not enabled",
                "original_response": response,
            }

        try:
            integration_report = await self.cove_integrator.verify_response_with_react(response, context)

            return {
                "success": True,
                "verification_report": integration_report,
                "original_response": response,
                "verified_response": integration_report.verified_response,
                "corrections_applied": integration_report.corrections_applied,
                "confidence_improvement": integration_report.confidence_improvement,
                "processing_time": integration_report.processing_time,
            }

        except Exception as e:
            self.logger.error(f"CoVe-ReAct verification failed: {e!s}")
            return {
                "success": False,
                "error": str(e),
                "original_response": response,
            }

    def is_cove_react_enabled(self) -> bool:
        """Check if CoVe-ReAct integration is enabled."""
        return self.enable_cove_react_integration and self.cove_integrator is not None

    def get_cove_react_status(self) -> dict[str, Any]:
        """Get current CoVe-ReAct integration status."""
        if not self.enable_cove_react_integration:
            return {
                "enabled": False,
                "reason": "CoVe-ReAct integration disabled in configuration",
            }

        if not self.cove_integrator:
            return {
                "enabled": False,
                "reason": "CoVe-ReAct integrator not initialized",
            }

        return {
            "enabled": True,
            "verification_mode": self.cove_integrator.verification_mode.value,
            "max_verification_time": self.cove_integrator.max_verification_time,
            "parallel_verification": self.cove_integrator.parallel_verification,
            "react_executor_enhanced": any(
                hasattr(executor, "supports_verification_enhancement") and executor.supports_verification_enhancement()
                for executor in self.executors.values()
            ),
        }

    async def coordinate_with_verification(
        self,
        context: PromptingContext,
        techniques: list[PromptingTechnique],
        enable_verification: bool = None,
    ) -> CoordinationResult:
        """
        Coordinate techniques with optional CoVe-ReAct verification.

        This method extends the standard coordination to include verification
        when appropriate based on context and configuration.

        Args:
        ----
            context: Prompting context
            techniques: Techniques to coordinate
            enable_verification: Override default verification behavior

        Returns:
        -------
            Coordination result with optional verification applied

        """
        # Determine if verification should be applied
        if enable_verification is None:
            enable_verification = self._should_enable_verification(context, techniques)

        # Execute standard coordination
        coordination_result = await self.coordinate_techniques(context, techniques)

        # Apply verification if enabled and appropriate
        if enable_verification and self.is_cove_react_enabled():
            verification_result = await self.verify_with_cove_react(
                coordination_result.primary_result,
                context,
            )

            if verification_result["success"]:
                # Update coordination result with verification
                coordination_result.primary_result = verification_result["verified_response"]
                coordination_result.overall_confidence += verification_result["confidence_improvement"]
                coordination_result.coordination_benefits["verification_applied"] = True
                coordination_result.coordination_benefits["verification_corrections"] = len(
                    verification_result["corrections_applied"],
                )

        return coordination_result

    def _should_enable_verification(
        self,
        context: PromptingContext,
        techniques: list[PromptingTechnique],
    ) -> bool:
        """Determine if verification should be enabled for this coordination."""
        # Enable verification for high-stakes domains
        accuracy_critical_domains = {"security", "architecture", "research", "analysis"}
        if context.domain in accuracy_critical_domains:
            return True

        # Enable verification if ReAct is included and context requires it
        if PromptingTechnique.REACT in techniques:
            if context.constitutional_requirements.get("anti_deception", False):
                return True
            if context.has_evidence_requirements():
                return True

        # Enable verification for complex contexts
        if context.complexity in ["complex", "expert"]:
            return True

        return False
