#!/usr/bin/env python3
"""
Cache Performance Analyzer and Optimizer
Analyzes cache performance, identifies bottlenecks, and provides optimization recommendations.
"""
from __future__ import annotations

import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add hooks directory to path
hooks_dir = Path("P:/").resolve() / ".claude" / "hooks"
sys.path.insert(0, str(hooks_dir))

from guidance_cache import GuidanceCache, get_guidance_cache


class CachePerformanceAnalyzer:
    """
    Comprehensive cache performance analysis and optimization tool.

    Analyzes:
    - Hit rates across all cache levels
    - Response time distributions (P50, P85, P95, P99)
    - Cache efficiency by workload pattern
    - Memory usage patterns
    - Optimal cache sizing
    """

    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": []
        }

    def analyze_l1_cache_performance(self, cache: GuidanceCache, num_operations: int = 1000) -> dict[str, Any]:
        """
        Analyze L1 cache performance with realistic workload.

        Returns comprehensive performance metrics including:
        - Hit rate by access pattern
        - Response time distribution
        - Memory efficiency
        - Optimal size recommendations
        """
        print(f"\n{'=' * 70}")
        print("L1 Cache Performance Analysis")
        print(f"{'=' * 70}")

        # Test scenarios
        scenarios = [
            ("Sequential Access", self._test_sequential_access, cache, num_operations),
            ("Random Access", self._test_random_access, cache, num_operations),
            ("Repeated Access (80/20)", self._test_repeated_access, cache, num_operations),
            ("Burst Access", self._test_burst_access, cache, num_operations),
        ]

        scenario_results = {}

        for scenario_name, test_func, *args in scenarios:
            print(f"\nScenario: {scenario_name}")
            print("-" * 50)

            result = test_func(*args)
            scenario_results[scenario_name] = result

            # Print results
            print(f"  Operations: {result['operations']}")
            print(f"  L1 Hit Rate: {result['l1_hit_rate']:.2f}%")
            print(f"  L2 Hit Rate: {result['l2_hit_rate']:.2f}%")
            print(f"  Overall Hit Rate: {result['overall_hit_rate']:.2f}%")
            print(f"  Mean Response: {result['mean_response_ms']:.3f}ms")
            print(f"  P85 Response: {result['p85_response_ms']:.3f}ms")
            print(f"  P95 Response: {result['p95_response_ms']:.3f}ms")

        # Aggregate analysis
        print(f"\n{'=' * 70}")
        print("L1 Cache Performance Summary")
        print(f"{'=' * 70}")

        avg_hit_rate = statistics.mean([r["overall_hit_rate"] for r in scenario_results.values()])
        avg_p85 = statistics.mean([r["p85_response_ms"] for r in scenario_results.values()])

        print(f"  Average Hit Rate: {avg_hit_rate:.2f}%")
        print(f"  Average P85 Response: {avg_p85:.3f}ms")

        # Performance targets
        target_hit_rate = 85.0
        target_p85 = 100.0  # 100ms

        hit_rate_met = avg_hit_rate >= target_hit_rate
        p85_met = avg_p85 < target_p85

        print(f"\n  Target Hit Rate (85%): {'✅ MET' if hit_rate_met else '❌ NOT MET'}")
        print(f"  Target P85 (100ms): {'✅ MET' if p85_met else '❌ NOT MET'}")

        # Recommendations
        recommendations = self._generate_l1_recommendations(scenario_results, cache)
        print("\n  Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"    {i}. {rec}")

        return {
            "scenario_results": scenario_results,
            "average_hit_rate": avg_hit_rate,
            "average_p85_ms": avg_p85,
            "targets_met": {
                "hit_rate": hit_rate_met,
                "p85_response": p85_met
            },
            "recommendations": recommendations
        }

    def _test_sequential_access(self, cache: GuidanceCache, num_operations: int) -> dict[str, Any]:
        """Test sequential access pattern (worst case for LRU)."""
        cache.reset_metrics()

        keys = [f"seq_key_{i}" for i in range(min(num_operations, 200))]
        response_times = []

        for i in range(num_operations):
            key = keys[i % len(keys)]
            start = time.time()
            cache.get(key, lambda: {"data": f"value_{i}"})
            response_times.append((time.time() - start) * 1000)

        metrics = cache.get_metrics()
        return self._calculate_metrics(metrics, response_times)

    def _test_random_access(self, cache: GuidanceCache, num_operations: int) -> dict[str, Any]:
        """Test random access pattern."""
        import random
        cache.reset_metrics()

        keys = [f"rand_key_{i}" for i in range(200)]
        response_times = []

        for _ in range(num_operations):
            key = random.choice(keys)
            start = time.time()
            cache.get(key, lambda: {"data": "random_value"})
            response_times.append((time.time() - start) * 1000)

        metrics = cache.get_metrics()
        return self._calculate_metrics(metrics, response_times)

    def _test_repeated_access(self, cache: GuidanceCache, num_operations: int) -> dict[str, Any]:
        """Test 80/20 access pattern (80% of accesses to 20% of keys)."""
        import random
        cache.reset_metrics()

        hot_keys = [f"hot_key_{i}" for i in range(20)]
        cold_keys = [f"cold_key_{i}" for i in range(180)]
        response_times = []

        for _ in range(num_operations):
            # 80% chance of accessing hot keys
            if random.random() < 0.8:
                key = random.choice(hot_keys)
            else:
                key = random.choice(cold_keys)

            start = time.time()
            cache.get(key, lambda: {"data": "value"})
            response_times.append((time.time() - start) * 1000)

        metrics = cache.get_metrics()
        return self._calculate_metrics(metrics, response_times)

    def _test_burst_access(self, cache: GuidanceCache, num_operations: int) -> dict[str, Any]:
        """Test burst access pattern (repeated accesses to same key)."""
        cache.reset_metrics()

        response_times = []
        burst_size = 10
        num_bursts = num_operations // burst_size

        for i in range(num_bursts):
            key = f"burst_key_{i % 100}"

            # Burst of accesses to same key
            for _ in range(burst_size):
                start = time.time()
                cache.get(key, lambda: {"data": "burst_value"})
                response_times.append((time.time() - start) * 1000)

        metrics = cache.get_metrics()
        return self._calculate_metrics(metrics, response_times)

    def _calculate_metrics(self, cache_metrics: dict, response_times: list[float]) -> dict[str, Any]:
        """Calculate performance metrics from cache data."""
        total_requests = cache_metrics["total_requests"]
        l1_hits = cache_metrics["l1_hits"]
        l2_hits = cache_metrics["l2_hits"]
        total_hits = l1_hits + l2_hits + cache_metrics["l3_hits"]

        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0.0
        l1_hit_rate = (l1_hits / total_requests * 100) if total_requests > 0 else 0.0
        l2_hit_rate = (l2_hits / total_requests * 100) if total_requests > 0 else 0.0

        sorted_times = sorted(response_times)
        p50 = sorted_times[len(sorted_times) // 2]
        p85 = sorted_times[int(len(sorted_times) * 0.85)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 100 else p95

        return {
            "operations": total_requests,
            "l1_hit_rate": l1_hit_rate,
            "l2_hit_rate": l2_hit_rate,
            "overall_hit_rate": hit_rate,
            "mean_response_ms": statistics.mean(response_times),
            "median_response_ms": statistics.median(response_times),
            "p50_response_ms": p50,
            "p85_response_ms": p85,
            "p95_response_ms": p95,
            "p99_response_ms": p99,
            "min_response_ms": min(response_times),
            "max_response_ms": max(response_times),
            "stddev_response_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0.0
        }

    def _generate_l1_recommendations(self, scenario_results: dict, cache: GuidanceCache) -> list[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []

        # Analyze hit rates
        avg_hit_rate = statistics.mean([r["overall_hit_rate"] for r in scenario_results.values()])

        if avg_hit_rate < 85.0:
            recommendations.append(
                f"Increase L1 cache size from {cache.l1_max_size} to {cache.l1_max_size + 50} "
                f"to improve hit rate (current: {avg_hit_rate:.1f}%, target: 85%)"
            )

        # Analyze response times
        avg_p85 = statistics.mean([r["p85_response_ms"] for r in scenario_results.values()])

        if avg_p85 > 100.0:
            recommendations.append(
                f"Optimize cache warming to reduce cold starts (P85: {avg_p85:.1f}ms, target: <100ms)"
            )

        # Analyze patterns
        sequential = scenario_results.get("Sequential Access", {})
        repeated = scenario_results.get("Repeated Access (80/20)", {})

        if sequential["overall_hit_rate"] < 50.0:
            recommendations.append(
                "Consider implementing 2Q or ARC cache replacement policy for better sequential access performance"
            )

        if repeated["overall_hit_rate"] > 90.0:
            recommendations.append(
                "Excellent performance on repeated access patterns - current LRU policy is well-suited for workload"
            )

        # Check L1 size utilization
        current_size = len(cache.l1_cache)
        if current_size < cache.l1_max_size * 0.7:
            recommendations.append(
                f"L1 cache underutilized ({current_size}/{cache.l1_max_size} entries). "
                "Consider reducing size or implementing adaptive sizing"
            )

        if not recommendations:
            recommendations.append("Cache performance is optimal - no immediate changes needed")

        return recommendations

    def analyze_cache_sizing(self, cache: GuidanceCache) -> dict[str, Any]:
        """
        Analyze optimal cache sizes through empirical testing.

        Tests different L1/L2 size combinations to find optimal configuration.
        """
        print(f"\n{'=' * 70}")
        print("Cache Sizing Analysis")
        print(f"{'=' * 70}")

        # Test different L1 sizes
        l1_sizes = [50, 75, 100, 150, 200]
        test_results = {}

        for l1_size in l1_sizes:
            # Create test cache with specific size
            test_cache = GuidanceCache(f"sizing_test_l1_{l1_size}")
            test_cache.l1_max_size = l1_size

            # Run workload
            test_cache.reset_metrics()

            # Mixed workload (70% repeated, 30% new)
            import random
            hot_keys = [f"hot_{i}" for i in range(50)]
            cold_keys = [f"cold_{i}" for i in range(500)]

            for _ in range(1000):
                if random.random() < 0.7:
                    key = random.choice(hot_keys)
                else:
                    key = random.choice(cold_keys)

                test_cache.get(key, lambda: {"data": "value"})

            metrics = test_cache.get_metrics()
            hit_rate = (metrics["l1_hits"] + metrics["l2_hits"]) / metrics["total_requests"] * 100

            test_results[l1_size] = {
                "hit_rate": hit_rate,
                "l1_hits": metrics["l1_hits"],
                "l2_hits": metrics["l2_hits"],
                "l1_size": len(test_cache.l1_cache)
            }

            print(f"  L1 Size {l1_size:3d}: Hit Rate {hit_rate:5.2f}%, "
                  f"L1 Hits {metrics['l1_hits']:4d}, L2 Size {len(test_cache.l1_cache):3d}")

        # Find optimal size (diminishing returns)
        optimal_size = self._find_optimal_size(test_results)

        print(f"\n  Optimal L1 Size: {optimal_size} entries")
        print(f"  Current L1 Size: {cache.l1_max_size} entries")

        if optimal_size != cache.l1_max_size:
            print(f"  Recommendation: Adjust L1 size to {optimal_size}")
        else:
            print("  ✅ Current L1 size is optimal")

        return {
            "test_results": test_results,
            "optimal_size": optimal_size,
            "current_size": cache.l1_max_size,
            "adjustment_needed": optimal_size != cache.l1_max_size
        }

    def _find_optimal_size(self, test_results: dict[int, dict]) -> int:
        """Find optimal cache size using diminishing returns analysis."""
        sizes = sorted(test_results.keys())
        hit_rates = [test_results[s]["hit_rate"] for s in sizes]

        # Find point where additional size gives <2% improvement
        for i in range(1, len(sizes)):
            improvement = hit_rates[i] - hit_rates[i-1]
            if improvement < 2.0:
                return sizes[i-1]

        return sizes[-1]

    def analyze_cache_warming(self, cache: GuidanceCache) -> dict[str, Any]:
        """
        Analyze cache warming effectiveness.

        Tests different warming strategies to optimize cold start performance.
        """
        print(f"\n{'=' * 70}")
        print("Cache Warming Analysis")
        print(f"{'=' * 70}")

        # Test warming strategies
        strategies = [
            ("No Warming", []),
            ("Default Warming", ["worktree risk", "explore codebase", "understand architecture"]),
            ("Extended Warming", [
                "worktree risk", "explore codebase", "understand architecture",
                "find patterns", "system structure", "error handling", "authentication"
            ]),
        ]

        results = {}

        for strategy_name, queries in strategies:
            # Create fresh cache for each test
            test_cache = GuidanceCache(f"warming_test_{strategy_name.replace(' ', '_')}")

            # Warm cache
            start = time.time()
            if queries:
                test_cache.warm_cache(queries)
            warm_time = (time.time() - start) * 1000

            # Test with realistic queries (some from warm set, some new)
            import random
            all_queries = [
                "worktree risk", "explore codebase", "understand architecture",
                "find patterns", "authentication system", "database schema"
            ]

            test_cache.reset_metrics()
            response_times = []

            for _ in range(100):
                query = random.choice(all_queries)
                start = time.time()
                test_cache.get(query, lambda: {"data": "result"})
                response_times.append((time.time() - start) * 1000)

            metrics = test_cache.get_metrics()
            avg_response = statistics.mean(response_times)
            hit_rate = (metrics["l1_hits"] + metrics["l2_hits"]) / metrics["total_requests"] * 100

            results[strategy_name] = {
                "warm_time_ms": warm_time,
                "hit_rate": hit_rate,
                "avg_response_ms": avg_response,
                "queries_count": len(queries)
            }

            print(f"\n  Strategy: {strategy_name}")
            print(f"    Warm Time: {warm_time:.2f}ms")
            print(f"    Hit Rate: {hit_rate:.2f}%")
            print(f"    Avg Response: {avg_response:.3f}ms")

        # Find best strategy
        best_strategy = max(results.keys(), key=lambda k: results[k]["hit_rate"])

        print(f"\n  Best Strategy: {best_strategy}")
        print("  Current Strategy: Default Warming")

        return {
            "strategy_results": results,
            "best_strategy": best_strategy,
            "recommendation": results[best_strategy]
        }

    def generate_optimization_report(self, cache: GuidanceCache) -> str:
        """Generate comprehensive optimization report."""
        report_lines = []

        report_lines.append("=" * 70)
        report_lines.append("Cache Performance Optimization Report")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated: {datetime.utcnow().isoformat()}")
        report_lines.append("")

        # Run all analyses
        l1_analysis = self.analyze_l1_cache_performance(cache)
        sizing_analysis = self.analyze_cache_sizing(cache)
        warming_analysis = self.analyze_cache_warming(cache)

        # Summary
        report_lines.append("\n" + "=" * 70)
        report_lines.append("Executive Summary")
        report_lines.append("=" * 70)
        report_lines.append("")

        # Overall assessment
        targets_met = (
            l1_analysis["targets_met"]["hit_rate"] and
            l1_analysis["targets_met"]["p85_response"]
        )

        if targets_met:
            report_lines.append("✅ OVERALL: All performance targets met")
        else:
            report_lines.append("⚠️  OVERALL: Some targets not met - optimization recommended")

        report_lines.append("")
        report_lines.append(f"  Average Hit Rate: {l1_analysis['average_hit_rate']:.2f}% (target: 85%)")
        report_lines.append(f"  Average P85 Response: {l1_analysis['average_p85_ms']:.3f}ms (target: <100ms)")

        # Recommendations
        report_lines.append("\n" + "=" * 70)
        report_lines.append("Optimization Recommendations")
        report_lines.append("=" * 70)
        report_lines.append("")

        all_recommendations = []
        all_recommendations.extend(l1_analysis["recommendations"])

        if sizing_analysis["adjustment_needed"]:
            all_recommendations.append(
                f"Adjust L1 cache size from {sizing_analysis['current_size']} "
                f"to {sizing_analysis['optimal_size']}"
            )

        best_warming = warming_analysis["best_strategy"]
        if best_warming != "Default Warming":
            all_recommendations.append(f"Use '{best_warming}' strategy for cache warming")

        for i, rec in enumerate(all_recommendations, 1):
            report_lines.append(f"{i}. {rec}")

        report_lines.append("")

        return "\n".join(report_lines)


def run_comprehensive_analysis():
    """Run comprehensive cache performance analysis."""
    print("=" * 70)
    print("Cache Performance Analyzer")
    print("=" * 70)
    print()

    analyzer = CachePerformanceAnalyzer()

    # Get cache instance
    cache = get_guidance_cache()

    # Generate report
    report = analyzer.generate_optimization_report(cache)

    # Print report
    print(report)

    # Save report
    report_dir = Path("P:/__csf/.speckit/memory/TSK-251222-GitWorktree-1745")
    report_file = report_dir / f"cache_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    with open(report_file, "w") as f:
        f.write(report)

    print(f"\nReport saved to: {report_file}")

    return 0


if __name__ == "__main__":
    sys.exit(run_comprehensive_analysis())
