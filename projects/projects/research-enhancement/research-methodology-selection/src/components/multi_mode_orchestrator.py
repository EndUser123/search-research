"""
Multi-Mode Orchestrator for Research Methodology Selection
Coordinates parallel execution across multiple research engines with result synthesis
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from .mode_relationship_mapper import ModeCombination, ResearchMode


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class ModeExecutionResult:
    """Result of executing a single research mode"""
    mode: ResearchMode
    status: ExecutionStatus
    execution_time: float
    sources_found: int
    results: list[dict[str, Any]]
    confidence: float
    error_message: str | None = None
    metadata: dict[str, Any] = None

@dataclass
class OrchestratedResult:
    """Complete result from multi-mode orchestration"""
    query: str
    modes_executed: list[ResearchMode]
    individual_results: dict[str, ModeExecutionResult]
    synthesized_results: dict[str, Any]
    execution_summary: dict[str, Any]
    orchestration_metadata: dict[str, Any]

class MultiModeOrchestrator:
    """Coordinates execution across multiple research modes"""

    def __init__(self, timeout_per_mode: int = 60, max_parallel_modes: int = 4):
        self.timeout_per_mode = timeout_per_mode
        self.max_parallel_modes = max_parallel_modes

        # Mode executors (placeholder implementations)
        self.mode_executors = {
            ResearchMode.OCTOCODE: self._execute_octocode,
            ResearchMode.WEB: self._execute_web,
            ResearchMode.MULTI_MODEL: self._execute_multi_model,
            ResearchMode.COGNITIVE: self._execute_cognitive,
        }

        # Execution statistics
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time": 0.0,
            "mode_success_rates": {mode.value: 0.0 for mode in ResearchMode}
        }

    async def execute_research(self, query: str, combination: ModeCombination,
                             tsk_context: dict = None) -> OrchestratedResult:
        """Execute research across multiple modes with coordination"""

        if not combination.modes:
            raise ValueError("No research modes specified in combination")

        # Create execution plan (all modes can run in parallel for now)
        execution_plan = self._create_execution_plan(combination.modes)

        # Execute modes in parallel according to plan
        individual_results = {}
        start_time = datetime.now()

        for stage, stage_modes in execution_plan.items():
            stage_tasks = []

            # Create tasks for all modes in this stage
            for mode in stage_modes:
                task = asyncio.create_task(
                    self._execute_mode_with_timeout(mode, query, tsk_context)
                )
                stage_tasks.append((mode, task))

            # Wait for all modes in this stage to complete
            for mode, task in stage_tasks:
                try:
                    result = await task
                    individual_results[mode.value] = result
                except TimeoutError:
                    individual_results[mode.value] = ModeExecutionResult(
                        mode=mode,
                        status=ExecutionStatus.TIMEOUT,
                        execution_time=self.timeout_per_mode,
                        sources_found=0,
                        results=[],
                        confidence=0.0,
                        error_message=f"Execution timed out after {self.timeout_per_mode}s"
                    )
                except Exception as e:
                    individual_results[mode.value] = ModeExecutionResult(
                        mode=mode,
                        status=ExecutionStatus.FAILED,
                        execution_time=0.0,
                        sources_found=0,
                        results=[],
                        confidence=0.0,
                        error_message=str(e)
                    )

        total_execution_time = (datetime.now() - start_time).total_seconds()

        # Synthesize results from all modes
        synthesized_results = self._synthesize_results(individual_results, query, combination)

        # Create execution summary
        execution_summary = self._create_execution_summary(
            individual_results, total_execution_time, combination
        )

        # Update execution statistics
        self._update_execution_stats(individual_results, total_execution_time)

        # Create orchestrated result
        orchestrated_result = OrchestratedResult(
            query=query,
            modes_executed=combination.modes,
            individual_results=individual_results,
            synthesized_results=synthesized_results,
            execution_summary=execution_summary,
            orchestration_metadata={
                "execution_plan": {str(k): [m.value for m in v] for k, v in execution_plan.items()},
                "total_execution_time": total_execution_time,
                "timeout_per_mode": self.timeout_per_mode,
                "max_parallel_modes": self.max_parallel_modes
            }
        )

        return orchestrated_result

    def _create_execution_plan(self, modes: list[ResearchMode]) -> dict[int, list[ResearchMode]]:
        """Create execution plan considering dependencies"""
        # For current implementation, all modes can execute in parallel
        # Future versions could implement more sophisticated dependency resolution
        return {0: modes}

    async def _execute_mode_with_timeout(self, mode: ResearchMode, query: str,
                                       tsk_context: dict = None) -> ModeExecutionResult:
        """Execute a single mode with timeout protection"""
        start_time = datetime.now()

        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                self._execute_mode(mode, query, tsk_context),
                timeout=self.timeout_per_mode
            )

            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time

            return result

        except TimeoutError:
            execution_time = (datetime.now() - start_time).total_seconds()
            raise

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            # Return failure result instead of raising
            return ModeExecutionResult(
                mode=mode,
                status=ExecutionStatus.FAILED,
                execution_time=execution_time,
                sources_found=0,
                results=[],
                confidence=0.0,
                error_message=str(e)
            )

    async def _execute_mode(self, mode: ResearchMode, query: str,
                          tsk_context: dict = None) -> ModeExecutionResult:
        """Execute a single research mode"""
        executor = self.mode_executors.get(mode)
        if not executor:
            raise ValueError(f"No executor implemented for mode: {mode}")

        try:
            result = await executor(query, tsk_context)
            return result
        except Exception as e:
            # Convert any exception to a ModeExecutionResult
            return ModeExecutionResult(
                mode=mode,
                status=ExecutionStatus.FAILED,
                execution_time=0.0,
                sources_found=0,
                results=[],
                confidence=0.0,
                error_message=str(e)
            )

    # Placeholder implementations for mode executors
    # These would be replaced with actual implementations that call the real research engines

    async def _execute_octocode(self, query: str, tsk_context: dict = None) -> ModeExecutionResult:
        """Execute octocode research (GitHub + Web)"""
        # Simulate execution time
        await asyncio.sleep(2.0)

        # Simulate results
        return ModeExecutionResult(
            mode=ResearchMode.OCTOCODE,
            status=ExecutionStatus.COMPLETED,
            execution_time=2.0,
            sources_found=15,
            results=[
                {
                    "source": "github",
                    "title": "React Hooks Implementation Example",
                    "url": "https://github.com/example/react-hooks",
                    "type": "repository",
                    "relevance_score": 0.92
                },
                {
                    "source": "web",
                    "title": "Complete Guide to React Hooks",
                    "url": "https://reactjs.org/docs/hooks-intro.html",
                    "type": "documentation",
                    "relevance_score": 0.95
                }
            ],
            confidence=0.88,
            metadata={
                "github_repos_found": 8,
                "web_sources_found": 7,
                "api_calls_made": 3
            }
        )

    async def _execute_web(self, query: str, tsk_context: dict = None) -> ModeExecutionResult:
        """Execute web search research"""
        # Simulate execution time
        await asyncio.sleep(1.5)

        return ModeExecutionResult(
            mode=ResearchMode.WEB,
            status=ExecutionStatus.COMPLETED,
            execution_time=1.5,
            sources_found=12,
            results=[
                {
                    "source": "web",
                    "title": "Understanding React Hooks",
                    "url": "https://example.com/react-hooks-tutorial",
                    "type": "tutorial",
                    "relevance_score": 0.87
                },
                {
                    "source": "web",
                    "title": "React Hooks Best Practices",
                    "url": "https://example.com/react-hooks-best-practices",
                    "type": "article",
                    "relevance_score": 0.91
                }
            ],
            confidence=0.82,
            metadata={
                "search_queries_used": 2,
                "domains_crawled": 5
            }
        )

    async def _execute_multi_model(self, query: str, tsk_context: dict = None) -> ModeExecutionResult:
        """Execute multi-model AI research"""
        # Simulate execution time (multiple API calls)
        await asyncio.sleep(3.0)

        return ModeExecutionResult(
            mode=ResearchMode.MULTI_MODEL,
            status=ExecutionStatus.COMPLETED,
            execution_time=3.0,
            sources_found=3,
            results=[
                {
                    "source": "ai_model_1",
                    "title": "AI Analysis: React Hooks Patterns",
                    "content": "Analysis of common patterns...",
                    "type": "ai_analysis",
                    "relevance_score": 0.85
                },
                {
                    "source": "ai_model_2",
                    "title": "AI Perspective: React Hooks Best Practices",
                    "content": "Alternative approach to hooks...",
                    "type": "ai_perspective",
                    "relevance_score": 0.80
                }
            ],
            confidence=0.75,
            metadata={
                "models_used": 2,
                "total_tokens": 1500
            }
        )

    async def _execute_cognitive(self, query: str, tsk_context: dict = None) -> ModeExecutionResult:
        """Execute cognitive-enhanced research"""
        # Simulate execution time (sequential processing)
        await asyncio.sleep(4.0)

        return ModeExecutionResult(
            mode=ResearchMode.COGNITIVE,
            status=ExecutionStatus.COMPLETED,
            execution_time=4.0,
            sources_found=1,
            results=[
                {
                    "source": "cognitive_analysis",
                    "title": "Comprehensive Analysis: React Hooks Implementation Strategies",
                    "content": "Deep analysis covering multiple aspects...",
                    "type": "cognitive_synthesis",
                    "relevance_score": 0.94
                }
            ],
            confidence=0.92,
            metadata={
                "analysis_stages": 3,
                "fact_checking_performed": True,
                "synthesis_quality": "high"
            }
        )

    def _synthesize_results(self, individual_results: dict[str, ModeExecutionResult],
                          query: str, combination: ModeCombination) -> dict[str, Any]:
        """Synthesize results from multiple modes with intelligent merging"""

        successful_results = {
            mode: result for mode, result in individual_results.items()
            if result.status == ExecutionStatus.COMPLETED
        }

        if not successful_results:
            return {
                "error": "No modes completed successfully",
                "query": query,
                "recommendations": ["Try with simpler query or different modes"]
            }

        # Gather all results
        all_results = []
        for mode, result in successful_results.items():
            for item in result.results:
                item["source_mode"] = mode
                all_results.append(item)

        # Sort by relevance score
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # Deduplicate similar results
        deduplicated_results = self._deduplicate_results(all_results)

        # Identify consensus points
        consensus_points = self._identify_consensus_points(successful_results)

        # Extract unique insights
        unique_insights = self._extract_unique_insights(successful_results)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            successful_results, query, combination
        )

        # Calculate overall metrics
        total_sources = sum(result.sources_found for result in successful_results.values())
        avg_confidence = sum(result.confidence for result in successful_results.values()) / len(successful_results)

        return {
            "query": query,
            "total_sources": total_sources,
            "successful_modes": list(successful_results.keys()),
            "results": deduplicated_results[:20],  # Top 20 results
            "consensus_points": consensus_points,
            "unique_insights": unique_insights,
            "recommendations": recommendations,
            "quality_metrics": {
                "overall_confidence": avg_confidence,
                "source_diversity": len(set(r.get("source", "") for r in deduplicated_results)),
                "coverage_completeness": len(successful_results) / len(combination.modes)
            }
        }

    def _deduplicate_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate or very similar results"""
        if not results:
            return results

        deduplicated = []
        seen_titles = set()
        seen_urls = set()

        for result in results:
            title = result.get("title", "").lower()
            url = result.get("url", "")

            # Check for duplicates based on title and URL
            if title not in seen_titles and url not in seen_urls:
                deduplicated.append(result)
                seen_titles.add(title)
                seen_urls.add(url)

        return deduplicated

    def _identify_consensus_points(self, results: dict[str, ModeExecutionResult]) -> list[str]:
        """Identify points where multiple modes agree"""
        consensus = []

        # Simple consensus detection based on common themes in results
        all_titles = []
        for result in results.values():
            for item in result.results:
                all_titles.append(item.get("title", "").lower())

        # Look for common keywords
        common_keywords = {}
        for title in all_titles:
            words = title.split()
            for word in words:
                if len(word) > 4:  # Only consider meaningful words
                    common_keywords[word] = common_keywords.get(word, 0) + 1

        # Find keywords that appear in multiple results
        consensus_keywords = [word for word, count in common_keywords.items() if count >= 2]

        if consensus_keywords:
            consensus.append(f"Common themes: {', '.join(consensus_keywords[:3])}")

        return consensus

    def _extract_unique_insights(self, results: dict[str, ModeExecutionResult]) -> list[str]:
        """Extract unique insights from different modes"""
        insights = []

        for mode, result in results.items():
            if result.sources_found > 0:
                if mode == "octocode":
                    insights.append("GitHub repositories provide practical implementation examples")
                elif mode == "web":
                    insights.append("Web sources offer comprehensive documentation and tutorials")
                elif mode == "multi-model":
                    insights.append("AI models provide diverse analytical perspectives")
                elif mode == "cognitive-enhanced":
                    insights.append("Cognitive analysis offers deep, synthesized insights")

        return insights

    def _generate_recommendations(self, results: dict[str, ModeExecutionResult],
                                query: str, combination: ModeCombination) -> list[str]:
        """Generate recommendations based on results"""
        recommendations = []

        successful_modes = list(results.keys())

        if len(successful_modes) == 1:
            mode = successful_modes[0]
            if mode == "octocode":
                recommendations.append("Consider adding web search for more comprehensive documentation")
            elif mode == "web":
                recommendations.append("Consider octocode mode for practical code examples")
        elif len(successful_modes) >= 3:
            recommendations.append("Comprehensive coverage achieved across multiple source types")
        else:
            recommendations.append("Good balance of sources for this query type")

        return recommendations

    def _create_execution_summary(self, individual_results: dict[str, ModeExecutionResult],
                                total_execution_time: float,
                                combination: ModeCombination) -> dict[str, Any]:
        """Create summary of execution results"""
        successful_count = sum(
            1 for result in individual_results.values()
            if result.status == ExecutionStatus.COMPLETED
        )
        failed_count = len(individual_results) - successful_count

        total_sources = sum(
            result.sources_found for result in individual_results.values()
            if result.status == ExecutionStatus.COMPLETED
        )

        avg_confidence = sum(
            result.confidence for result in individual_results.values()
            if result.status == ExecutionStatus.COMPLETED
        ) / max(successful_count, 1)

        return {
            "modes_attempted": len(individual_results),
            "modes_successful": successful_count,
            "modes_failed": failed_count,
            "success_rate": successful_count / len(individual_results),
            "total_execution_time": total_execution_time,
            "total_sources_found": total_sources,
            "average_confidence": avg_confidence,
            "efficiency_score": total_sources / max(total_execution_time, 1),
            "mode_details": {
                mode: {
                    "status": result.status.value,
                    "execution_time": result.execution_time,
                    "sources_found": result.sources_found,
                    "confidence": result.confidence
                }
                for mode, result in individual_results.items()
            }
        }

    def _update_execution_stats(self, individual_results: dict[str, ModeExecutionResult],
                              total_execution_time: float):
        """Update internal execution statistics"""
        self.execution_stats["total_executions"] += 1

        successful = sum(
            1 for result in individual_results.values()
            if result.status == ExecutionStatus.COMPLETED
        )

        if successful > 0:
            self.execution_stats["successful_executions"] += 1
        else:
            self.execution_stats["failed_executions"] += 1

        # Update average execution time
        total_executions = self.execution_stats["total_executions"]
        current_avg = self.execution_stats["average_execution_time"]
        self.execution_stats["average_execution_time"] = (
            (current_avg * (total_executions - 1) + total_execution_time) / total_executions
        )

        # Update mode-specific success rates
        for mode, result in individual_results.items():
            if result.status == ExecutionStatus.COMPLETED:
                current_rate = self.execution_stats["mode_success_rates"][mode]
                self.execution_stats["mode_success_rates"][mode] = (
                    (current_rate * (total_executions - 1) + 1.0) / total_executions
                )

    def get_execution_statistics(self) -> dict[str, Any]:
        """Get current execution statistics"""
        return self.execution_stats.copy()

# Test cases
if __name__ == "__main__":
    from .mode_relationship_mapper import ModeCombination

    orchestrator = MultiModeOrchestrator()

    # Test single mode
    single_mode_combo = ModeCombination(
        modes=[ResearchMode.OCTOCODE],
        predicted_quality=0.85,
        estimated_cost=1.5,
        redundancy_score=0.0,
        coverage_score=0.8
    )

    # Test multiple modes
    multi_mode_combo = ModeCombination(
        modes=[ResearchMode.OCTOCODE, ResearchMode.WEB, ResearchMode.MULTI_MODEL],
        predicted_quality=0.92,
        estimated_cost=5.5,
        redundancy_score=0.3,
        coverage_score=0.95
    )

    async def test_orchestration():
        print("=== Multi-Mode Orchestration Test ===")

        print("\n1. Testing single mode execution...")
        result1 = await orchestrator.execute_research("react hooks example", single_mode_combo)
        print(f"Modes: {[m.value for m in result1.modes_executed]}")
        print(f"Total sources: {result1.synthesized_results['total_sources']}")
        print(f"Execution time: {result1.orchestration_metadata['total_execution_time']:.2f}s")

        print("\n2. Testing multi-mode execution...")
        result2 = await orchestrator.execute_research("react hooks best practices", multi_mode_combo)
        print(f"Modes: {[m.value for m in result2.modes_executed]}")
        print(f"Total sources: {result2.synthesized_results['total_sources']}")
        print(f"Execution time: {result2.orchestration_metadata['total_execution_time']:.2f}s")
        print(f"Consensus points: {result2.synthesized_results['consensus_points']}")
        print(f"Unique insights: {result2.synthesized_results['unique_insights']}")

        print("\n3. Execution statistics...")
        stats = orchestrator.get_execution_statistics()
        print(f"Total executions: {stats['total_executions']}")
        print(f"Success rate: {stats['successful_executions'] / max(stats['total_executions'], 1):.1%}")
        print(f"Average execution time: {stats['average_execution_time']:.2f}s")

    # Run the test
    asyncio.run(test_orchestration())
