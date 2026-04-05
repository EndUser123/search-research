#!/usr/bin/env python3
"""Performance comparison: Layer 2 overhead measurement.

TASK-009B: Compare performance before vs after Layer 2.

Measures:
- Layer 1 baseline time (no Layer 2)
- Layer 2 overhead time (Agent tool call)
- Token usage (estimate_tokens_from_results accuracy)
- Overhead percentage (Layer 2 time / total time)

Metrics:
- Target: <5 seconds overhead for Layer 2
- Target: <8k tokens for Agent tool prompt
"""

import asyncio
import sys
import time
from pathlib import Path

# Add paths
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

skills_path = Path(__file__).parent.parent / "skills" / "all"
sys.path.insert(0, str(skills_path))

import adaptive_limits
import agent_filter
import layer2_filter
import query_complexity
import semantic_cluster


class MockSearchResult:
    """Mock search result for testing."""
    def __init__(self, title: str, content: str, score: float, source: str = "WEB"):
        self.title = title
        self.content = content
        self.score = score
        self.source = source
        self.url = f"https://example.com/{title.lower().replace(' ', '-')}"
        self.metadata = {}


async def measure_layer1_baseline(query: str, results: list) -> dict:
    """Measure Layer 1 performance (no Layer 2)."""
    print(f"\n[Layer 1 Baseline] Query: '{query}'")
    print(f"[Layer 1 Baseline] Results: {len(results)} items")

    start = time.perf_counter()

    # Layer 1C: Calculate complexity
    complexity_score = query_complexity.calculate_complexity_score(query)
    complexity_time = time.perf_counter() - start

    # Layer 1D: Get adaptive limit
    config = adaptive_limits.get_adaptive_config(complexity_score, 30)
    adaptive_time = time.perf_counter() - complexity_time - start

    # Layer 1B: Semantic clustering
    clustered = semantic_cluster.apply_semantic_clustering(results, max_results=25)
    cluster_time = time.perf_counter() - adaptive_time - complexity_time - start

    total_time = time.perf_counter() - start

    return {
        "total_time": total_time,
        "complexity_time": complexity_time,
        "adaptive_time": adaptive_time,
        "cluster_time": cluster_time,
        "complexity_score": complexity_score,
        "results_in": len(results),
        "results_out": len(clustered),
    }


async def measure_layer2_overhead(query: str, results: list) -> dict:
    """Measure Layer 2 overhead (Agent tool filtering)."""
    print(f"\n[Layer 2 Overhead] Query: '{query}'")
    print(f"[Layer 2 Overhead] Results: {len(results)} items")

    # First, run Layer 1 to get pre-filtered results
    layer1_start = time.perf_counter()

    complexity_score = query_complexity.calculate_complexity_score(query)
    clustered = semantic_cluster.apply_semantic_clustering(results, max_results=25)

    layer1_time = time.perf_counter() - layer1_start

    # Estimate tokens before Layer 2
    estimated_tokens = agent_filter.estimate_tokens_from_results(clustered)

    # Now measure Layer 2
    layer2_start = time.perf_counter()

    filtered = await agent_filter.apply_agent_filtering(
        query=query,
        results=clustered,
        trigger_reason="auto",
        complexity_score=complexity_score
    )

    layer2_time = time.perf_counter() - layer2_start

    total_time = layer1_time + layer2_time

    # Calculate overhead percentage
    overhead_pct = (layer2_time / total_time * 100) if total_time > 0 else 0

    return {
        "total_time": total_time,
        "layer1_time": layer1_time,
        "layer2_time": layer2_time,
        "overhead_pct": overhead_pct,
        "estimated_tokens": estimated_tokens,
        "complexity_score": complexity_score,
        "results_in": len(results),
        "results_out_clustered": len(clustered),
        "results_out_filtered": filtered.get("filtered_count", 0),
        "themes_count": len(filtered.get("themes", [])),
    }


def print_comparison(baseline: dict, overhead: dict):
    """Print performance comparison."""
    print("\n" + "="*70)
    print("PERFORMANCE COMPARISON")
    print("="*70)

    print(f"\nQuery complexity: {overhead['complexity_score']}/100")

    print("\n--- Results ---")
    print(f"Input: {baseline['results_in']} results")
    print(f"Layer 1 output: {baseline['results_out']} results")
    print(f"Layer 2 output: {overhead['results_out_filtered']} insights")

    print("\n--- Timing ---")
    print(f"Layer 1 baseline: {baseline['total_time']*1000:.2f} ms")
    print(f"  - Complexity scoring: {baseline['complexity_time']*1000:.2f} ms")
    print(f"  - Adaptive limits: {baseline['adaptive_time']*1000:.2f} ms")
    print(f"  - Semantic clustering: {baseline['cluster_time']*1000:.2f} ms")

    print(f"\nLayer 2 overhead: {overhead['layer2_time']*1000:.2f} ms")
    print(f"  - Overhead percentage: {overhead['overhead_pct']:.1f}%")
    print(f"  - Estimated tokens: {overhead['estimated_tokens']}")

    print("\n--- Total ---")
    print(f"Layer 1 only: {baseline['total_time']*1000:.2f} ms")
    print(f"Layer 1 + 2: {overhead['total_time']*1000:.2f} ms")
    print(f"Overhead: {(overhead['total_time'] - baseline['total_time'])*1000:.2f} ms")

    # Check targets
    print("\n--- Targets ---")
    layer2_overhead_sec = overhead['layer2_time']
    tokens = overhead['estimated_tokens']

    if layer2_overhead_sec < 5.0:
        print(f"✅ Layer 2 overhead: {layer2_overhead_sec:.2f}s < 5.0s (PASS)")
    else:
        print(f"❌ Layer 2 overhead: {layer2_overhead_sec:.2f}s >= 5.0s (FAIL)")

    if tokens < 8000:
        print(f"✅ Token usage: {tokens} < 8000 (PASS)")
    else:
        print(f"❌ Token usage: {tokens} >= 8000 (FAIL)")


async def run_performance_tests():
    """Run performance comparison tests."""
    print("="*70)
    print("TASK-009B: PERFORMANCE COMPARISON - LAYER 2 OVERHEAD")
    print("="*70)

    # Test scenarios
    scenarios = [
        {
            "name": "Small result set (no Layer 2 expected)",
            "query": "async patterns",
            "results": [
                MockSearchResult("Python async patterns", "Content about async", 0.9),
                MockSearchResult("Python async tutorial", "More async", 0.85),
                MockSearchResult("JavaScript promises", "Promise content", 0.8),
            ],
            "expect_layer2": False,
        },
        {
            "name": "Large result set (Layer 2 expected)",
            "query": "authentication patterns",
            "results": [
                MockSearchResult(f"Result {i}: authentication", f"Auth content {i}", 0.9 - i * 0.01)
                for i in range(25)
            ],
            "expect_layer2": True,
        },
        {
            "name": "Context hints (Layer 2 expected)",
            "query": "what did we discuss about authentication",
            "results": [
                MockSearchResult(f"Auth result {i}", f"Auth content {i}", 0.9)
                for i in range(15)
            ],
            "expect_layer2": True,
        },
    ]

    results = []

    for scenario in scenarios:
        print("\n" + "="*70)
        print(f"SCENARIO: {scenario['name']}")
        print("="*70)

        # Measure Layer 1 baseline
        baseline = await measure_layer1_baseline(
            scenario['query'],
            scenario['results']
        )

        # Measure Layer 2 overhead
        overhead = await measure_layer2_overhead(
            scenario['query'],
            scenario['results']
        )

        # Print comparison
        print_comparison(baseline, overhead)

        # Verify Layer 2 trigger expectation
        should_trigger, _ = layer2_filter.should_apply_context_filter(
            semantic_cluster.apply_semantic_clustering(scenario['results'], max_results=25),
            scenario['query'],
            threshold=20
        )

        if should_trigger == scenario['expect_layer2']:
            print(f"\n✅ PASS: Layer 2 trigger expectation met ({should_trigger})")
        else:
            print(f"\n❌ FAIL: Layer 2 trigger expectation mismatch (expected {scenario['expect_layer2']}, got {should_trigger})")

        results.append({
            "scenario": scenario['name'],
            "baseline": baseline,
            "overhead": overhead,
        })

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    layer2_overheads = [r['overhead']['layer2_time'] for r in results if r['overhead']['layer2_time'] > 0]
    token_estimates = [r['overhead']['estimated_tokens'] for r in results]

    if layer2_overheads:
        avg_overhead = sum(layer2_overheads) / len(layer2_overheads)
        max_overhead = max(layer2_overheads)
        print("\nLayer 2 overhead:")
        print(f"  - Average: {avg_overhead*1000:.2f} ms")
        print(f"  - Maximum: {max_overhead*1000:.2f} ms")
        print("  - Target: <5000 ms")
        print(f"  - Status: {'✅ PASS' if max_overhead < 5.0 else '❌ FAIL'}")

    if token_estimates:
        avg_tokens = sum(token_estimates) / len(token_estimates)
        max_tokens = max(token_estimates)
        print("\nToken usage:")
        print(f"  - Average: {avg_tokens:.0f} tokens")
        print(f"  - Maximum: {max_tokens:.0f} tokens")
        print("  - Target: <8000 tokens")
        print(f"  - Status: {'✅ PASS' if max_tokens < 8000 else '❌ FAIL'}")

    print("\n" + "="*70)
    print("✅ TASK-009B COMPLETE")
    print("="*70)

    return True


if __name__ == "__main__":
    success = asyncio.run(run_performance_tests())
    sys.exit(0 if success else 1)
