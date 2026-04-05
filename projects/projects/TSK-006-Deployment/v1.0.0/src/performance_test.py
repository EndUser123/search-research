#!/usr/bin/env python3
"""
Performance Test for TSK-006 Persistent Learning Agent Ecosystem
Step 12: Performance Analytics - Benchmark Collection
"""

import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from agent_factory.agent_factory import AgentFactory
    from agent_factory.cks_integration import cks_stats, query_cks, store_to_cks
    from agent_factory.critic import create_critic
    from agent_factory.evaluation import EvaluationConfig, create_evaluation_pipeline
    from agent_factory.routing import AgentProfile, AgentStatus, PerformanceBasedRouter
except ImportError as e:
    print(f"Import error: {e}")
    print("Running limited performance test without full imports...")
    AgentFactory = None

class PerformanceBenchmark:
    """Comprehensive performance benchmark for TSK-006 system."""

    def __init__(self):
        self.results = {}
        self.test_start_time = time.time()

    def measure_agent_creation_performance(self) -> dict[str, Any]:
        """Measure agent creation performance."""
        print("=== Agent Creation Performance Test ===")

        if not AgentFactory:
            return {"error": "AgentFactory not available"}

        try:
            factory = AgentFactory()
            creation_times = []

            # Test agent creation speed (target: <10ms)
            print("Testing agent creation speed...")
            for i in range(20):  # Test with 20 agents
                start_time = time.perf_counter()
                session_id = factory.create_agent(
                    'development_agent',
                    context={'task': f'performance_test_{i}', 'priority': 'test'}
                )
                end_time = time.perf_counter()

                if session_id:
                    creation_times.append(end_time - start_time)
                    print(f"  Agent {i+1}: {(end_time - start_time) * 1000:.2f}ms")

            if creation_times:
                avg_time = statistics.mean(creation_times)
                min_time = min(creation_times)
                max_time = max(creation_times)
                std_dev = statistics.stdev(creation_times) if len(creation_times) > 1 else 0

                results = {
                    "average_creation_time_ms": avg_time * 1000,
                    "min_creation_time_ms": min_time * 1000,
                    "max_creation_time_ms": max_time * 1000,
                    "std_deviation_ms": std_dev * 1000,
                    "target_ms": 10.0,
                    "success_rate": len(creation_times) / 20 * 100,
                    "status": "PASS" if avg_time < 0.01 else "FAIL"
                }

                print("\nAgent Creation Results:")
                print(f"  Average: {results['average_creation_time_ms']:.2f}ms")
                print(f"  Min: {results['min_creation_time_ms']:.2f}ms")
                print(f"  Max: {results['max_creation_time_ms']:.2f}ms")
                print(f"  Std Dev: {results['std_deviation_ms']:.2f}ms")
                print(f"  Target: <{results['target_ms']}ms")
                print(f"  Status: {results['status']}")

                return results

        except Exception as e:
            return {"error": str(e)}

    def measure_session_management_performance(self) -> dict[str, Any]:
        """Measure session management performance."""
        print("\n=== Session Management Performance Test ===")

        if not AgentFactory:
            return {"error": "AgentFactory not available"}

        try:
            factory = AgentFactory()

            # Test session creation and retrieval (target: <500ms session prep)
            session_times = []

            print("Testing session management speed...")
            for i in range(10):
                start_time = time.perf_counter()

                # Create session
                session_id = factory.create_agent('testing_agent', context={'test': i})

                # Retrieve session
                if session_id:
                    session = factory.get_agent(session_id)
                    # Update context
                    factory.update_agent_context(session_id, {'update': f'test_{i}'})

                end_time = time.perf_counter()
                session_times.append(end_time - start_time)

            if session_times:
                avg_time = statistics.mean(session_times)
                active_sessions = len(factory.get_active_agents())

                results = {
                    "average_session_time_ms": avg_time * 1000,
                    "target_ms": 500.0,
                    "active_sessions": active_sessions,
                    "status": "PASS" if avg_time < 0.5 else "FAIL"
                }

                print("Session Management Results:")
                print(f"  Average Time: {results['average_session_time_ms']:.2f}ms")
                print(f"  Target: <{results['target_ms']}ms")
                print(f"  Active Sessions: {results['active_sessions']}")
                print(f"  Status: {results['status']}")

                return results

        except Exception as e:
            return {"error": str(e)}

    def measure_cks_integration_performance(self) -> dict[str, Any]:
        """Measure CKS integration performance."""
        print("\n=== CKS Integration Performance Test ===")

        try:
            query_times = []
            store_times = []

            # Test CKS query performance (target: <200ms)
            print("Testing CKS query speed...")
            for i in range(10):
                start_time = time.perf_counter()
                results = query_cks(f"test query {i}", top_n=5, threshold=0.5)
                end_time = time.perf_counter()
                query_times.append(end_time - start_time)

            # Test CKS store performance (target: <1s)
            print("Testing CKS store speed...")
            for i in range(5):
                start_time = time.perf_counter()
                success = store_to_cks(
                    f"test question {i}",
                    f"test answer {i}",
                    metadata={"source": "performance_test", "test_id": i}
                )
                end_time = time.perf_counter()
                if success:
                    store_times.append(end_time - start_time)

            # Get CKS stats
            stats = cks_stats()

            query_avg = statistics.mean(query_times) if query_times else 0
            store_avg = statistics.mean(store_times) if store_times else 0

            results = {
                "query_performance": {
                    "average_time_ms": query_avg * 1000,
                    "target_ms": 200.0,
                    "status": "PASS" if query_avg < 0.2 else "FAIL"
                },
                "store_performance": {
                    "average_time_ms": store_avg * 1000,
                    "target_ms": 1000.0,
                    "status": "PASS" if store_avg < 1.0 else "FAIL"
                },
                "cks_stats": stats
            }

            print("CKS Query Results:")
            print(f"  Average Time: {results['query_performance']['average_time_ms']:.2f}ms")
            print(f"  Target: <{results['query_performance']['target_ms']}ms")
            print(f"  Status: {results['query_performance']['status']}")

            print("CKS Store Results:")
            print(f"  Average Time: {results['store_performance']['average_time_ms']:.2f}ms")
            print(f"  Target: <{results['store_performance']['target_ms']}ms")
            print(f"  Status: {results['store_performance']['status']}")

            return results

        except Exception as e:
            return {"error": str(e)}

    def measure_critic_performance(self) -> dict[str, Any]:
        """Measure critic system performance."""
        print("\n=== Critic System Performance Test ===")

        try:
            critic = create_critic()

            # Test code evaluation performance (target: <2s)
            sample_code = '''
def complex_function(a, b, c, d, e):
    """A function for testing critic performance."""
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return a + b + c + d + e
                    else:
                        return a + b + c + d
                else:
                    return a + b + c
            else:
                return a + b
        else:
            return a
    else:
        return 0

class EmptyClass:
    pass

def another_function():
    pass
'''

            evaluation_times = []
            print("Testing code evaluation speed...")

            for i in range(5):
                start_time = time.perf_counter()
                result = critic.evaluate_code(sample_code, f"test_file_{i}.py")
                end_time = time.perf_counter()
                evaluation_times.append(end_time - start_time)

            if evaluation_times:
                avg_time = statistics.mean(evaluation_times)
                quality_scores = [result.quality_score.overall for result in [critic.evaluate_code(sample_code)]]

                results = {
                    "average_evaluation_time_s": avg_time,
                    "target_s": 2.0,
                    "average_quality_score": statistics.mean(quality_scores) if quality_scores else 0,
                    "status": "PASS" if avg_time < 2.0 else "FAIL"
                }

                print("Critic System Results:")
                print(f"  Average Time: {results['average_evaluation_time_s']:.3f}s")
                print(f"  Target: <{results['target_s']}s")
                print(f"  Quality Score: {results['average_quality_score']:.1f}")
                print(f"  Status: {results['status']}")

                return results

        except Exception as e:
            return {"error": str(e)}

    def measure_resource_utilization(self) -> dict[str, Any]:
        """Measure system resource utilization."""
        print("\n=== Resource Utilization Test ===")

        try:
            process = psutil.Process(os.getpid())

            # Get current resource usage
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=1)

            # Get system info
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=1)

            results = {
                "process_memory_rss_mb": memory_info.rss / 1024 / 1024,
                "process_memory_vms_mb": memory_info.vms / 1024 / 1024,
                "process_cpu_percent": cpu_percent,
                "system_memory_usage_percent": system_memory.percent,
                "system_cpu_percent": system_cpu,
                "system_memory_available_gb": system_memory.available / 1024 / 1024 / 1024
            }

            print("Resource Utilization Results:")
            print(f"  Process Memory (RSS): {results['process_memory_rss_mb']:.2f} MB")
            print(f"  Process Memory (VMS): {results['process_memory_vms_mb']:.2f} MB")
            print(f"  Process CPU: {results['process_cpu_percent']:.1f}%")
            print(f"  System Memory Usage: {results['system_memory_usage_percent']:.1f}%")
            print(f"  System CPU: {results['system_cpu_percent']:.1f}%")
            print(f"  Available Memory: {results['system_memory_available_gb']:.2f} GB")

            return results

        except Exception as e:
            return {"error": str(e)}

    def run_comprehensive_benchmark(self) -> dict[str, Any]:
        """Run comprehensive performance benchmark."""
        print("=" * 60)
        print("TSK-006 PERSISTENT LEARNING AGENT ECOSYSTEM")
        print("STEP 12: PERFORMANCE ANALYTICS - BENCHMARK COLLECTION")
        print("=" * 60)

        # Run all performance tests
        self.results["agent_creation"] = self.measure_agent_creation_performance()
        self.results["session_management"] = self.measure_session_management_performance()
        self.results["cks_integration"] = self.measure_cks_integration_performance()
        self.results["critic_system"] = self.measure_critic_performance()
        self.results["resource_utilization"] = self.measure_resource_utilization()

        # Add metadata
        self.results["benchmark_metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "total_duration_s": time.time() - self.test_start_time,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "cpu_count": psutil.cpu_count()
            }
        }

        # Calculate overall performance score
        passed_tests = sum(1 for result in self.results.values()
                          if isinstance(result, dict) and result.get("status") == "PASS")
        total_tests = len([r for r in self.results.values()
                          if isinstance(r, dict) and "status" in r])

        self.results["overall_performance"] = {
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "quality_score": min(100, (passed_tests / total_tests * 100) if total_tests > 0 else 0)
        }

        return self.results

    def save_results(self, output_path: str = None) -> str:
        """Save benchmark results to file."""
        if not output_path:
            output_path = Path(__file__).parent / f"performance_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nBenchmark results saved to: {output_path}")
        return str(output_path)


def main():
    """Main execution function."""
    benchmark = PerformanceBenchmark()
    results = benchmark.run_comprehensive_benchmark()

    # Print summary
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("=" * 60)

    if "overall_performance" in results:
        overall = results["overall_performance"]
        print(f"Overall Success Rate: {overall['success_rate']:.1f}%")
        print(f"Tests Passed: {overall['passed_tests']}/{overall['total_tests']}")
        print(f"Quality Score: {overall['quality_score']:.1f}/100")

    print("\nComponent Status:")
    for component, result in results.items():
        if isinstance(result, dict) and "status" in result:
            status_symbol = "✓" if result["status"] == "PASS" else "✗"
            print(f"  {status_symbol} {component.replace('_', ' ').title()}: {result['status']}")
        elif isinstance(result, dict) and "error" in result:
            print(f"  ✗ {component.replace('_', ' ').title()}: ERROR - {result['error']}")

    # Validate performance targets
    targets_met = 0
    total_targets = 0

    target_validations = [
        ("Agent Creation", results.get("agent_creation", {}).get("average_creation_time_ms", 0), 10),
        ("Session Management", results.get("session_management", {}).get("average_session_time_ms", 0), 500),
        ("CKS Query", results.get("cks_integration", {}).get("query_performance", {}).get("average_time_ms", 0), 200),
        ("CKS Store", results.get("cks_integration", {}).get("store_performance", {}).get("average_time_ms", 0), 1000),
        ("Critic Evaluation", results.get("critic_system", {}).get("average_evaluation_time_s", 0) * 1000, 2000)
    ]

    print("\nPerformance Target Validation:")
    for name, actual, target in target_validations:
        if actual > 0:
            total_targets += 1
            status = "✓ PASS" if actual < target else "✗ FAIL"
            print(f"  {status} {name}: {actual:.2f}ms (target: <{target}ms)")
            if actual < target:
                targets_met += 1

    target_success_rate = (targets_met / total_targets * 100) if total_targets > 0 else 0
    print(f"\nTarget Achievement Rate: {target_success_rate:.1f}%")

    # Save results
    output_file = benchmark.save_results()

    return results


if __name__ == "__main__":
    main()
