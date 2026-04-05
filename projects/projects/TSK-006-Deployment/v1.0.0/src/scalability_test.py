#!/usr/bin/env python3
"""
Scalability Analysis for TSK-006 Persistent Learning Agent Ecosystem
Step 12: Performance Analytics - Scalability Testing and Bottleneck Identification
"""

import concurrent.futures
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from agent_factory.agent_factory import AgentFactory
    from agent_factory.cks_integration import query_cks, store_to_cks
    from agent_factory.critic import create_critic
    from agent_factory.routing import AgentProfile, AgentStatus, PerformanceBasedRouter
except ImportError as e:
    print(f"Import error: {e}")
    AgentFactory = None

class ScalabilityAnalyzer:
    """Comprehensive scalability analysis for TSK-006 system."""

    def __init__(self):
        self.results = {}
        self.test_start_time = time.time()

    def test_concurrent_agent_creation(self, max_concurrent: int = 50) -> dict[str, Any]:
        """Test concurrent agent creation scalability."""
        print("=== Concurrent Agent Creation Scalability Test ===")

        if not AgentFactory:
            return {"error": "AgentFactory not available"}

        results = {
            "concurrency_levels": [],
            "creation_times": [],
            "memory_usage": [],
            "success_rates": []
        }

        concurrency_levels = [1, 5, 10, 20, 30, 40, 50]

        for concurrency in concurrency_levels:
            print(f"Testing with {concurrency} concurrent agents...")

            # Monitor memory before test
            process = psutil.Process(os.getpid())
            memory_before = process.memory_info().rss / 1024 / 1024

            creation_times = []
            successful_creations = 0

            def create_agent_worker(agent_id: int) -> dict[str, Any]:
                """Worker function for concurrent agent creation."""
                try:
                    start_time = time.perf_counter()
                    factory = AgentFactory()
                    session_id = factory.create_agent(
                        'development_agent',
                        context={'test_id': agent_id, 'concurrency_test': True}
                    )
                    end_time = time.perf_counter()

                    return {
                        "agent_id": agent_id,
                        "success": session_id is not None,
                        "creation_time": end_time - start_time,
                        "session_id": session_id
                    }
                except Exception as e:
                    return {
                        "agent_id": agent_id,
                        "success": False,
                        "creation_time": 0,
                        "error": str(e)
                    }

            # Run concurrent agent creation
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(create_agent_worker, i) for i in range(concurrency)]
                agent_results = [future.result() for future in concurrent.futures.as_completed(futures)]

            # Analyze results
            for result in agent_results:
                if result["success"]:
                    successful_creations += 1
                    creation_times.append(result["creation_time"])

            # Monitor memory after test
            memory_after = process.memory_info().rss / 1024 / 1024

            if creation_times:
                avg_time = statistics.mean(creation_times)
                std_dev = statistics.stdev(creation_times) if len(creation_times) > 1 else 0
            else:
                avg_time = 0
                std_dev = 0

            level_results = {
                "concurrency": concurrency,
                "successful_creations": successful_creations,
                "total_attempts": concurrency,
                "success_rate": (successful_creations / concurrency) * 100,
                "avg_creation_time_ms": avg_time * 1000,
                "std_deviation_ms": std_dev * 1000,
                "memory_increase_mb": memory_after - memory_before,
                "throughput_agents_per_second": successful_creations / (sum(creation_times) if creation_times else 1)
            }

            results["concurrency_levels"].append(level_results)
            results["creation_times"].append(avg_time * 1000)
            results["memory_usage"].append(memory_after - memory_before)
            results["success_rates"].append(level_results["success_rate"])

            print(f"  Success Rate: {level_results['success_rate']:.1f}%")
            print(f"  Avg Creation Time: {level_results['avg_creation_time_ms']:.2f}ms")
            print(f"  Memory Increase: {level_results['memory_increase_mb']:.2f} MB")
            print(f"  Throughput: {level_results['throughput_agents_per_second']:.2f} agents/sec")

        return results

    def test_memory_scaling(self, agent_count: int = 100) -> dict[str, Any]:
        """Test memory usage scaling with agent count."""
        print(f"\n=== Memory Scaling Test ({agent_count} agents) ===")

        if not AgentFactory:
            return {"error": "AgentFactory not available"}

        process = psutil.Process(os.getpid())
        memory_samples = []
        agent_counts = []
        session_ids = []

        factory = AgentFactory()
        initial_memory = process.memory_info().rss / 1024 / 1024

        print(f"Initial Memory: {initial_memory:.2f} MB")

        # Create agents incrementally and measure memory
        batch_size = 10
        for i in range(0, agent_count, batch_size):
            batch_start = i
            batch_end = min(i + batch_size, agent_count)

            # Create a batch of agents
            for j in range(batch_start, batch_end):
                start_time = time.perf_counter()
                session_id = factory.create_agent(
                    'development_agent',
                    context={'memory_test': True, 'agent_index': j}
                )
                end_time = time.perf_counter()

                if session_id:
                    session_ids.append(session_id)

            # Measure memory after batch
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            agent_counts.append(len(session_ids))

            memory_per_agent = (current_memory - initial_memory) / max(1, len(session_ids))
            print(f"  Agents {len(session_ids):3d}: {current_memory:6.2f} MB ({memory_per_agent:.2f} MB/agent)")

        results = {
            "total_agents_created": len(session_ids),
            "initial_memory_mb": initial_memory,
            "final_memory_mb": memory_samples[-1] if memory_samples else initial_memory,
            "memory_increase_mb": (memory_samples[-1] if memory_samples else initial_memory) - initial_memory,
            "memory_per_agent_mb": ((memory_samples[-1] if memory_samples else initial_memory) - initial_memory) / max(1, len(session_ids)),
            "memory_samples": memory_samples,
            "agent_counts": agent_counts,
            "memory_efficiency_score": 100 - min(100, ((memory_samples[-1] if memory_samples else initial_memory) - initial_memory) / max(1, len(session_ids)) * 10)
        }

        print("\nMemory Scaling Results:")
        print(f"  Total Agents: {results['total_agents_created']}")
        print(f"  Memory Increase: {results['memory_increase_mb']:.2f} MB")
        print(f"  Memory per Agent: {results['memory_per_agent_mb']:.2f} MB")
        print(f"  Memory Efficiency Score: {results['memory_efficiency_score']:.1f}/100")

        return results

    def test_cks_load_scaling(self, query_count: int = 1000) -> dict[str, Any]:
        """Test CKS performance under load."""
        print(f"\n=== CKS Load Scaling Test ({query_count} queries) ===")

        query_times = []
        store_times = []
        errors = 0

        print("Running CKS queries...")
        for i in range(query_count):
            try:
                start_time = time.perf_counter()
                results = query_cks(f"load test query {i}", top_n=5, threshold=0.5)
                end_time = time.perf_counter()
                query_times.append(end_time - start_time)
            except Exception:
                errors += 1

        print("Running CKS stores...")
        for i in range(100):  # Fewer stores as they're more expensive
            try:
                start_time = time.perf_counter()
                success = store_to_cks(
                    f"load test question {i}",
                    f"load test answer {i}",
                    metadata={"load_test": True, "query_id": i}
                )
                end_time = time.perf_counter()
                if success:
                    store_times.append(end_time - start_time)
            except Exception:
                errors += 1

        if query_times:
            query_avg = statistics.mean(query_times)
            query_p95 = np.percentile(query_times, 95)
            query_p99 = np.percentile(query_times, 99)
        else:
            query_avg = query_p95 = query_p99 = 0

        if store_times:
            store_avg = statistics.mean(store_times)
            store_p95 = np.percentile(store_times, 95)
            store_p99 = np.percentile(store_times, 99)
        else:
            store_avg = store_p95 = store_p99 = 0

        results = {
            "query_count": query_count,
            "store_count": len(store_times),
            "error_count": errors,
            "query_performance": {
                "average_time_ms": query_avg * 1000,
                "p95_time_ms": query_p95 * 1000,
                "p99_time_ms": query_p99 * 1000,
                "queries_per_second": query_count / (sum(query_times) if query_times else 1)
            },
            "store_performance": {
                "average_time_ms": store_avg * 1000,
                "p95_time_ms": store_p95 * 1000,
                "p99_time_ms": store_p99 * 1000,
                "stores_per_second": len(store_times) / (sum(store_times) if store_times else 1)
            },
            "error_rate": (errors / (query_count + 100)) * 100
        }

        print("CKS Load Results:")
        print(f"  Query Avg: {results['query_performance']['average_time_ms']:.2f}ms")
        print(f"  Query P95: {results['query_performance']['p95_time_ms']:.2f}ms")
        print(f"  Query Throughput: {results['query_performance']['queries_per_second']:.1f} qps")
        print(f"  Store Avg: {results['store_performance']['average_time_ms']:.2f}ms")
        print(f"  Error Rate: {results['error_rate']:.2f}%")

        return results

    def test_critic_load_scaling(self, evaluation_count: int = 100) -> dict[str, Any]:
        """Test critic system performance under load."""
        print(f"\n=== Critic Load Scaling Test ({evaluation_count} evaluations) ===")

        try:
            critic = create_critic()
        except Exception as e:
            return {"error": f"Failed to create critic: {e}"}

        sample_code = '''
def complex_function(a, b, c, d, e):
    """A function for testing critic performance under load."""
    result = 0
    for i in range(a):
        if b > 0:
            for j in range(b):
                if c > 0:
                    for k in range(c):
                        if d > 0:
                            result += i * j * k
    return result if e > 0 else 0

class TestClass:
    def __init__(self):
        self.value = 0

    def method_with_issues(self):
        # Empty method
        pass

    def another_method(self):
        return self.value

def another_function():
    pass
'''

        evaluation_times = []
        quality_scores = []
        issue_counts = []

        print("Running critic evaluations...")
        for i in range(evaluation_count):
            try:
                start_time = time.perf_counter()
                result = critic.evaluate_code(sample_code, f"load_test_file_{i}.py")
                end_time = time.perf_counter()

                evaluation_times.append(end_time - start_time)
                quality_scores.append(result.quality_score.overall)
                issue_counts.append(len(result.issues))

            except Exception as e:
                print(f"  Error in evaluation {i}: {e}")

        if evaluation_times:
            avg_time = statistics.mean(evaluation_times)
            p95_time = np.percentile(evaluation_times, 95)
            p99_time = np.percentile(evaluation_times, 99)
            avg_quality = statistics.mean(quality_scores) if quality_scores else 0
            avg_issues = statistics.mean(issue_counts) if issue_counts else 0
        else:
            avg_time = p95_time = p99_time = avg_quality = avg_issues = 0

        results = {
            "evaluation_count": evaluation_count,
            "successful_evaluations": len(evaluation_times),
            "performance_metrics": {
                "average_time_ms": avg_time * 1000,
                "p95_time_ms": p95_time * 1000,
                "p99_time_ms": p99_time * 1000,
                "evaluations_per_second": len(evaluation_times) / (sum(evaluation_times) if evaluation_times else 1)
            },
            "quality_metrics": {
                "average_quality_score": avg_quality,
                "average_issues_found": avg_issues,
                "quality_consistency": 100 - (statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0) * 10
            }
        }

        print("Critic Load Results:")
        print(f"  Evaluations: {results['successful_evaluations']}/{results['evaluation_count']}")
        print(f"  Avg Time: {results['performance_metrics']['average_time_ms']:.2f}ms")
        print(f"  P95 Time: {results['performance_metrics']['p95_time_ms']:.2f}ms")
        print(f"  Throughput: {results['performance_metrics']['evaluations_per_second']:.1f} eps")
        print(f"  Avg Quality Score: {results['quality_metrics']['average_quality_score']:.1f}")
        print(f"  Quality Consistency: {results['quality_metrics']['quality_consistency']:.1f}%")

        return results

    def identify_bottlenecks(self) -> dict[str, Any]:
        """Identify system bottlenecks based on test results."""
        print("\n=== Bottleneck Analysis ===")

        bottlenecks = []
        recommendations = []

        # Analyze agent creation performance
        if "concurrent_creation" in self.results:
            creation_results = self.results["concurrent_creation"]
            if creation_results["creation_times"]:
                max_time = max(creation_results["creation_times"])
                if max_time > 100:  # > 100ms is problematic
                    bottlenecks.append({
                        "component": "Agent Creation",
                        "issue": f"Slow agent creation under load (max: {max_time:.2f}ms)",
                        "severity": "HIGH" if max_time > 200 else "MEDIUM",
                        "impact": "System responsiveness and scalability"
                    })
                    recommendations.append("Optimize agent factory initialization and session management")

        # Analyze memory scaling
        if "memory_scaling" in self.results:
            memory_results = self.results["memory_scaling"]
            memory_per_agent = memory_results.get("memory_per_agent_mb", 0)
            if memory_per_agent > 5:  # > 5MB per agent is high
                bottlenecks.append({
                    "component": "Memory Management",
                    "issue": f"High memory usage per agent ({memory_per_agent:.2f} MB)",
                    "severity": "HIGH" if memory_per_agent > 10 else "MEDIUM",
                    "impact": "Limited scalability and potential memory exhaustion"
                })
                recommendations.append("Implement agent pooling and memory optimization")

        # Analyze CKS performance
        if "cks_load" in self.results:
            cks_results = self.results["cks_load"]
            query_avg = cks_results.get("query_performance", {}).get("average_time_ms", 0)
            if query_avg > 50:  # > 50ms for CKS queries is concerning
                bottlenecks.append({
                    "component": "CKS Integration",
                    "issue": f"Slow CKS queries under load (avg: {query_avg:.2f}ms)",
                    "severity": "MEDIUM",
                    "impact": "Knowledge retrieval performance degradation"
                })
                recommendations.append("Implement CKS query caching and indexing optimization")

        # System-level bottlenecks
        process = psutil.Process(os.getpid())
        cpu_count = psutil.cpu_count()
        current_memory_mb = process.memory_info().rss / 1024 / 1024

        if current_memory_mb > 500:  # > 500MB is significant
            bottlenecks.append({
                "component": "System Resources",
                "issue": f"High memory usage ({current_memory_mb:.2f} MB)",
                "severity": "MEDIUM",
                "impact": "System performance and stability"
            })

        analysis = {
            "identified_bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "system_assessment": {
                "current_memory_mb": current_memory_mb,
                "cpu_cores_available": cpu_count,
                "overall_health": "GOOD" if len(bottlenecks) == 0 else "NEEDS_ATTENTION" if len(bottlenecks) <= 2 else "CRITICAL"
            }
        }

        print("Bottleneck Analysis Results:")
        print(f"  Bottlenecks Found: {len(bottlenecks)}")
        print(f"  Recommendations: {len(recommendations)}")
        print(f"  Overall Health: {analysis['system_assessment']['overall_health']}")

        for bottleneck in bottlenecks:
            print(f"\n  {bottleneck['severity']}: {bottleneck['component']}")
            print(f"    Issue: {bottleneck['issue']}")
            print(f"    Impact: {bottleneck['impact']}")

        return analysis

    def run_scalability_analysis(self) -> dict[str, Any]:
        """Run comprehensive scalability analysis."""
        print("=" * 60)
        print("TSK-006 PERSISTENT LEARNING AGENT ECOSYSTEM")
        print("STEP 12: PERFORMANCE ANALYTICS - SCALABILITY ANALYSIS")
        print("=" * 60)

        # Run all scalability tests
        self.results["concurrent_creation"] = self.test_concurrent_agent_creation()
        self.results["memory_scaling"] = self.test_memory_scaling()
        self.results["cks_load"] = self.test_cks_load_scaling()
        self.results["critic_load"] = self.test_critic_load_scaling()
        self.results["bottleneck_analysis"] = self.identify_bottlenecks()

        # Add metadata
        self.results["analysis_metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "total_duration_s": time.time() - self.test_start_time,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count(),
                "total_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024
            }
        }

        # Calculate overall scalability score
        scores = []

        # Agent creation scalability score
        if "concurrent_creation" in self.results and self.results["concurrent_creation"].get("success_rates"):
            avg_success_rate = statistics.mean(self.results["concurrent_creation"]["success_rates"])
            scores.append(avg_success_rate)

        # Memory efficiency score
        if "memory_scaling" in self.results:
            memory_score = self.results["memory_scaling"].get("memory_efficiency_score", 0)
            scores.append(memory_score)

        # CKS performance score
        if "cks_load" in self.results:
            cks_score = 100 - min(100, self.results["cks_load"].get("error_rate", 0) * 10)
            scores.append(cks_score)

        # Critic performance score
        if "critic_load" in self.results:
            critic_score = self.results["critic_load"].get("quality_metrics", {}).get("quality_consistency", 0)
            scores.append(critic_score)

        overall_score = statistics.mean(scores) if scores else 0

        self.results["overall_scalability"] = {
            "scalability_score": overall_score,
            "component_scores": len(scores),
            "grade": "A" if overall_score >= 90 else "B" if overall_score >= 80 else "C" if overall_score >= 70 else "D" if overall_score >= 60 else "F",
            "ready_for_production": overall_score >= 75
        }

        return self.results

    def save_results(self, output_path: str = None) -> str:
        """Save scalability analysis results to file."""
        if not output_path:
            output_path = Path(__file__).parent / f"scalability_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nScalability analysis results saved to: {output_path}")
        return str(output_path)


def main():
    """Main execution function."""
    analyzer = ScalabilityAnalyzer()
    results = analyzer.run_scalability_analysis()

    # Print summary
    print("\n" + "=" * 60)
    print("SCALABILITY ANALYSIS SUMMARY")
    print("=" * 60)

    if "overall_scalability" in results:
        overall = results["overall_scalability"]
        print(f"Scalability Score: {overall['scalability_score']:.1f}/100")
        print(f"Grade: {overall['grade']}")
        print(f"Production Ready: {overall['ready_for_production']}")

    print("\nComponent Performance:")
    components = [
        ("Concurrent Agent Creation", "concurrent_creation"),
        ("Memory Scaling", "memory_scaling"),
        ("CKS Load Performance", "cks_load"),
        ("Critic Load Performance", "critic_load")
    ]

    for name, key in components:
        if key in results and isinstance(results[key], dict) and "error" not in results[key]:
            print(f"  ✓ {name}: COMPLETED")
        elif key in results and isinstance(results[key], dict) and "error" in results[key]:
            print(f"  ✗ {name}: ERROR - {results[key]['error']}")

    if "bottleneck_analysis" in results:
        analysis = results["bottleneck_analysis"]
        print(f"\nSystem Health: {analysis['system_assessment']['overall_health']}")
        print(f"Bottlenecks Identified: {len(analysis['identified_bottlenecks'])}")
        print(f"Recommendations: {len(analysis['recommendations'])}")

    # Save results
    output_file = analyzer.save_results()

    return results


if __name__ == "__main__":
    main()
