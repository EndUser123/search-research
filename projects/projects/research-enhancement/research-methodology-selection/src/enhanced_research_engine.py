"""
Enhanced Research Engine with Intelligent Methodology Selection
Integrates all components for coordinated multi-mode research
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any

from .components.enhanced_dependency_analyzer import (
    QueryDependencies,
    SimplifiedDependencyAnalyzer,
)
from .components.learning_system import LearningSystem
from .components.mode_relationship_mapper import ModeCombination, ModeRelationshipMapper
from .components.multi_mode_orchestrator import (
    MultiModeOrchestrator,
    OrchestratedResult,
)
from .components.quality_optimizer import (
    CostBenefitOptimizer,
    OptimizationResult,
    QualityPredictor,
)


class EnhancedResearchEngine:
    """
    Enhanced research engine that intelligently selects and orchestrates
    multiple research methodologies based on query analysis and learned patterns
    """

    def __init__(self, config: dict[str, Any] = None):
        """
        Initialize the enhanced research engine

        Args:
            config: Configuration dictionary with optional settings:
                - budget_limit: Maximum cost factor for research (default: 5.0)
                - timeout_per_mode: Timeout in seconds per mode (default: 60)
                - max_parallel_modes: Maximum parallel modes (default: 4)
                - enable_learning: Enable learning system (default: True)
                - feedback_file: Path to feedback storage file
        """
        self.config = config or {}

        # Initialize core components
        self.dependency_analyzer = SimplifiedDependencyAnalyzer()
        self.mode_mapper = ModeRelationshipMapper()
        self.quality_predictor = QualityPredictor()
        self.cost_optimizer = CostBenefitOptimizer()
        self.orchestrator = MultiModeOrchestrator(
            timeout_per_mode=self.config.get("timeout_per_mode", 60),
            max_parallel_modes=self.config.get("max_parallel_modes", 4)
        )

        # Initialize learning system if enabled
        if self.config.get("enable_learning", True):
            feedback_file = self.config.get("feedback_file", "research_feedback.json")
            self.learning_system = LearningSystem(feedback_file)
        else:
            self.learning_system = None

        # Configuration
        self.default_budget = self.config.get("budget_limit", 5.0)

        # Statistics
        self.engine_stats = {
            "total_research_sessions": 0,
            "intelligent_selections": 0,
            "user_specified_modes": 0,
            "average_quality": 0.0,
            "learning_enabled": self.learning_system is not None
        }

    async def research(self, query: str, mode: str = "auto",
                      budget_limit: float = None, tsk_context: dict = None,
                      domain: str = None, expertise_level: str = "intermediate") -> dict[str, Any]:
        """
        Perform intelligent research with methodology selection

        Args:
            query: Research query
            mode: Research mode ("auto", "octocode", "web", "multi-model", "cognitive-enhanced")
            budget_limit: Maximum budget for research (default from config)
            tsk_context: TSK context information
            domain: Research domain for pattern matching
            expertise_level: User expertise level for personalization

        Returns:
            Dict containing research results and metadata
        """
        research_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            if mode == "auto":
                return await self._intelligent_research(
                    research_id, query, budget_limit, tsk_context, domain, expertise_level
                )
            else:
                return await self._single_mode_research(
                    research_id, query, mode, tsk_context, domain, expertise_level
                )
        except Exception as e:
            # Return error result
            return {
                "research_id": research_id,
                "query": query,
                "error": str(e),
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "status": "failed"
            }

    async def _intelligent_research(self, research_id: str, query: str,
                                  budget_limit: float, tsk_context: dict,
                                  domain: str, expertise_level: str) -> dict[str, Any]:
        """Intelligent research with automatic methodology selection"""

        # Step 1: Analyze query dependencies
        dependencies = self.dependency_analyzer.analyze_dependencies(query, tsk_context)

        # Step 2: Get candidate modes based on dependencies
        candidate_modes = self.mode_mapper._get_candidate_modes(dependencies)

        # Step 3: Get pattern-based recommendation if available
        pattern_recommendation = None
        if self.learning_system:
            pattern_recommendation = self.learning_system.get_pattern_based_recommendation(
                query, [mode.value for mode in candidate_modes], domain, expertise_level
            )

        # Step 4: Generate and evaluate combinations
        combinations = self.mode_mapper._generate_combinations(candidate_modes, dependencies)
        scored_combinations = self.mode_mapper._score_combinations(combinations, dependencies)

        # Step 5: Apply learning system recommendation
        if pattern_recommendation:
            # Boost recommended combination's score
            rec_combo_str = pattern_recommendation["recommended_combination"]
            rec_modes = [self._parse_mode_string(m) for m in rec_combo_str.split('+')]

            for combination in scored_combinations:
                if set(combination.modes) == set(rec_modes):
                    combination.predicted_quality += 0.1  # Boost for learning recommendation
                    break

        # Step 6: Optimize for budget
        budget = budget_limit or self.default_budget
        optimization_result = self.cost_optimizer.optimize_for_budget(
            scored_combinations, dependencies, budget, domain
        )

        # Step 7: Execute research with orchestrated coordination
        orchestrated_result = await self.orchestrator.execute_research(
            query, optimization_result.recommended_combination, tsk_context
        )

        # Step 8: Enhance results with methodology metadata
        enhanced_results = self._enhance_with_metadata(
            orchestrated_result, dependencies, optimization_result,
            pattern_recommendation, domain, expertise_level
        )

        # Step 9: Update statistics
        self.engine_stats["total_research_sessions"] += 1
        self.engine_stats["intelligent_selections"] += 1
        self._update_quality_stats(orchestrated_result.synthesized_results.get("quality_metrics", {}))

        return enhanced_results

    async def _single_mode_research(self, research_id: str, query: str,
                                  mode: str, tsk_context: dict,
                                  domain: str, expertise_level: str) -> dict[str, Any]:
        """Single mode research execution with minimal overhead"""

        from .components.mode_relationship_mapper import ResearchMode

        try:
            research_mode = ResearchMode(mode)
        except ValueError:
            return {
                "research_id": research_id,
                "query": query,
                "error": f"Invalid research mode: {mode}",
                "status": "failed"
            }

        # Create simple combination for single mode
        single_combination = ModeCombination(
            modes=[research_mode],
            predicted_quality=0.8,  # Default assumption
            estimated_cost=self.cost_optimizer.cost_factors[research_mode],
            redundancy_score=0.0,
            coverage_score=0.7
        )

        # Execute single mode
        orchestrated_result = await self.orchestrator.execute_research(
            query, single_combination, tsk_context
        )

        # Create minimal metadata
        enhanced_results = {
            "research_id": research_id,
            "query": query,
            "mode": mode,
            "individual_results": {
                mode.value: result.__dict__ for mode, result in orchestrated_result.individual_results.items()
            },
            "synthesized_results": orchestrated_result.synthesized_results,
            "execution_summary": orchestrated_result.execution_summary,
            "methodology_metadata": {
                "selection_type": "user_specified",
                "mode_selected": mode,
                "pattern_recommendation": None,
                "dependencies_analyzed": False
            },
            "status": "completed"
        }

        # Update statistics
        self.engine_stats["total_research_sessions"] += 1
        self.engine_stats["user_specified_modes"] += 1
        self._update_quality_stats(orchestrated_result.synthesized_results.get("quality_metrics", {}))

        return enhanced_results

    def _parse_mode_string(self, mode_str: str):
        """Parse mode string to ResearchMode enum"""
        from .components.mode_relationship_mapper import ResearchMode
        for mode in ResearchMode:
            if mode.value == mode_str:
                return mode
        raise ValueError(f"Unknown mode: {mode_str}")

    def _enhance_with_metadata(self, orchestrated_result: OrchestratedResult,
                             dependencies: QueryDependencies,
                             optimization_result: OptimizationResult,
                             pattern_recommendation: dict | None,
                             domain: str, expertise_level: str) -> dict[str, Any]:
        """Enhance results with methodology selection metadata"""

        # Convert individual results to serializable format
        individual_results_serializable = {}
        for mode, result in orchestrated_result.individual_results.items():
            result_dict = {
                "mode": result.mode.value,
                "status": result.status.value,
                "execution_time": result.execution_time,
                "sources_found": result.sources_found,
                "confidence": result.confidence,
                "error_message": result.error_message,
                "metadata": result.metadata or {}
            }
            individual_results_serializable[mode] = result_dict

        return {
            "research_id": orchestrated_result.orchestration_metadata.get("research_id", str(uuid.uuid4())),
            "query": orchestrated_result.query,
            "modes_executed": [mode.value for mode in orchestrated_result.modes_executed],
            "individual_results": individual_results_serializable,
            "synthesized_results": orchestrated_result.synthesized_results,
            "execution_summary": orchestrated_result.execution_summary,
            "methodology_metadata": {
                "selection_type": "intelligent",
                "dependencies_analyzed": True,
                "dependencies": {
                    "requires_code": dependencies.requires_code,
                    "requires_github": dependencies.requires_github,
                    "requires_academic": dependencies.requires_academic,
                    "requires_ai_perspectives": dependencies.requires_ai_perspectives,
                    "complexity_score": dependencies.complexity_score,
                    "research_depth": dependencies.research_depth.value,
                    "confidence": dependencies.confidence
                },
                "optimization": {
                    "recommended_combination": [m.value for m in optimization_result.recommended_combination.modes],
                    "predicted_quality": optimization_result.recommended_combination.predicted_quality,
                    "estimated_cost": optimization_result.recommended_combination.estimated_cost,
                    "budget_usage": optimization_result.budget_usage,
                    "reasoning": optimization_result.optimization_reasoning,
                    "alternatives": [
                        {
                            "modes": [m.value for m in alt.modes],
                            "quality": alt.predicted_quality,
                            "cost": alt.estimated_cost
                        }
                        for alt in optimization_result.alternatives
                    ]
                },
                "pattern_recommendation": pattern_recommendation,
                "domain_context": domain,
                "expertise_level": expertise_level,
                "orchestration": orchestrated_result.orchestration_metadata
            },
            "status": "completed"
        }

    def _update_quality_stats(self, quality_metrics: dict[str, Any]):
        """Update engine statistics with quality information"""
        overall_confidence = quality_metrics.get("overall_confidence", 0.0)
        current_avg = self.engine_stats["average_quality"]
        total_sessions = self.engine_stats["total_research_sessions"]

        # Update running average
        if total_sessions > 0:
            self.engine_stats["average_quality"] = (
                (current_avg * (total_sessions - 1) + overall_confidence) / total_sessions
            )
        else:
            self.engine_stats["average_quality"] = overall_confidence

    def provide_feedback(self, research_id: str, query: str, modes_used: list[str],
                        predicted_quality: float, actual_quality_rating: float,
                        helpful_aspects: list[str] = None,
                        improvement_suggestions: list[str] = None,
                        sources_helpful: list[str] = None,
                        sources_missing: list[str] = None,
                        session_duration: float = 0.0,
                        user_expertise_level: str = "intermediate",
                        research_domain: str = "general") -> bool:
        """
        Provide feedback for learning system improvement

        Args:
            research_id: Unique identifier for the research session
            query: Original research query
            modes_used: List of modes that were used
            predicted_quality: Quality predicted by the system
            actual_quality_rating: Actual quality rating from user (1-5 scale)
            helpful_aspects: List of aspects that were helpful
            improvement_suggestions: List of improvement suggestions
            sources_helpful: List of helpful source types
            sources_missing: List of missing source types
            session_duration: Duration of the research session
            user_expertise_level: User's expertise level
            research_domain: Domain of research

        Returns:
            bool: True if feedback was successfully collected
        """
        if not self.learning_system:
            return False

        try:
            self.learning_system.collect_feedback(
                research_id=research_id,
                query=query,
                modes_used=modes_used,
                predicted_quality=predicted_quality,
                actual_quality_rating=actual_quality_rating,
                helpful_aspects=helpful_aspects,
                improvement_suggestions=improvement_suggestions,
                sources_helpful=sources_helpful,
                sources_missing=sources_missing,
                session_duration=session_duration,
                user_expertise_level=user_expertise_level,
                research_domain=research_domain
            )
            return True
        except Exception as e:
            print(f"Error collecting feedback: {e}")
            return False

    def get_engine_statistics(self) -> dict[str, Any]:
        """Get comprehensive engine statistics"""
        stats = self.engine_stats.copy()

        # Add learning system stats if available
        if self.learning_system:
            stats["learning_system"] = self.learning_system.get_learning_summary()
            stats["mode_performance"] = self.learning_system.get_mode_performance_stats()

        # Add orchestrator stats
        stats["orchestrator"] = self.orchestrator.get_execution_statistics()

        return stats

    def export_learning_data(self, filename: str = None) -> str | None:
        """Export learning data for analysis"""
        if not self.learning_system:
            return None

        return self.learning_system.export_patterns(filename)

# Example usage and testing
async def main():
    """Main function demonstrating the enhanced research engine"""
    print("=== Enhanced Research Engine Demo ===")

    # Initialize the engine
    config = {
        "budget_limit": 4.0,
        "timeout_per_mode": 30,
        "enable_learning": True,
        "feedback_file": "demo_feedback.json"
    }

    engine = EnhancedResearchEngine(config)

    # Test intelligent research
    test_queries = [
        {
            "query": "react hooks implementation example",
            "domain": "technical",
            "expertise": "intermediate"
        },
        {
            "query": "enterprise microservices security patterns comparison",
            "domain": "technical",
            "expertise": "expert"
        },
        {
            "query": "academic papers on machine learning ethics",
            "domain": "academic",
            "expertise": "expert"
        },
        {
            "query": "docker tutorial for beginners",
            "domain": "technical",
            "expertise": "beginner"
        }
    ]

    for test_case in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {test_case['query']}")
        print(f"Domain: {test_case['domain']}, Expertise: {test_case['expertise']}")

        # Perform intelligent research
        result = await engine.research(
            query=test_case["query"],
            mode="auto",
            domain=test_case["domain"],
            expertise_level=test_case["expertise"]
        )

        if result.get("status") == "completed":
            # Display methodology metadata
            metadata = result["methodology_metadata"]
            print("\nMethodology Selection:")
            print(f"  Selection Type: {metadata['selection_type']}")
            print(f"  Modes Executed: {', '.join(result['modes_executed'])}")
            print(f"  Dependencies Found: {sum(metadata['dependencies'].values())}")

            if metadata.get("optimization"):
                opt = metadata["optimization"]
                print(f"  Predicted Quality: {opt['predicted_quality']:.2f}")
                print(f"  Budget Usage: {opt['budget_usage']:.1%}")
                print(f"  Reasoning: {opt['reasoning']}")

            if metadata.get("pattern_recommendation"):
                pattern = metadata["pattern_recommendation"]
                print(f"  Pattern-based Recommendation: {pattern['recommended_combination']}")
                print(f"  Pattern Confidence: {pattern['confidence']:.2f}")

            # Display results summary
            synthesized = result["synthesized_results"]
            print("\nResults Summary:")
            print(f"  Total Sources: {synthesized.get('total_sources', 0)}")
            print(f"  Overall Confidence: {synthesized.get('quality_metrics', {}).get('overall_confidence', 0):.2f}")

            # Display execution summary
            exec_summary = result["execution_summary"]
            print(f"  Execution Time: {exec_summary.get('total_execution_time', 0):.2f}s")
            print(f"  Success Rate: {exec_summary.get('success_rate', 0):.1%}")

            # Simulate user feedback for learning
            if metadata["selection_type"] == "intelligent":
                actual_quality = 4.2 if synthesized.get('total_sources', 0) > 10 else 3.8
                engine.provide_feedback(
                    research_id=result["research_id"],
                    query=test_case["query"],
                    modes_used=result["modes_executed"],
                    predicted_quality=metadata.get("optimization", {}).get("predicted_quality", 0.8),
                    actual_quality_rating=actual_quality,
                    helpful_aspects=["comprehensive coverage", "multiple perspectives"],
                    user_expertise_level=test_case["expertise"],
                    research_domain=test_case["domain"],
                    session_duration=exec_summary.get('total_execution_time', 0)
                )
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")

    # Show final statistics
    print(f"\n{'='*60}")
    print("Final Engine Statistics:")
    stats = engine.get_engine_statistics()
    print(f"  Total Research Sessions: {stats['total_research_sessions']}")
    print(f"  Intelligent Selections: {stats['intelligent_selections']}")
    print(f"  User Specified Modes: {stats['user_specified_modes']}")
    print(f"  Average Quality: {stats['average_quality']:.2f}")
    print(f"  Learning Enabled: {stats['learning_enabled']}")

    if stats.get("learning_system"):
        learning_stats = stats["learning_system"]
        print(f"  Learning Sessions: {learning_stats['total_feedback_sessions']}")
        print(f"  Patterns Identified: {learning_stats['patterns_identified']}")

    # Export learning data
    if stats["learning_enabled"]:
        export_file = engine.export_learning_data("demo_learning_export.json")
        if export_file:
            print(f"  Learning Data Exported: {export_file}")

if __name__ == "__main__":
    asyncio.run(main())
