#!/usr/bin/env python3
"""Performance baseline test for Layer 1 enhancements.

Measures baseline performance BEFORE Agent integration (Layer 2).
This test documents the performance overhead of each Layer 1 enhancement.

Metrics Collected:
- Search execution time (Layer 1A: rule-based filtering)
- Semantic clustering time (Layer 1B)
- Query complexity scoring time (Layer 1C)
- Adaptive limit calculation time (Layer 1D)
- Total Layer 1 time (all sub-layers combined)
- Memory usage for result sets

Performance Targets:
- Layer 1A adds < 200ms overhead
- Layer 1B adds < 500ms overhead
- Layer 1C adds < 100ms overhead
- Layer 1D adds < 50ms overhead
- Total Layer 1 < 1 second
"""

import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

# Add parent directories to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

skills_path = Path(__file__).parent.parent / "skills" / "all"
sys.path.insert(0, str(skills_path))

import adaptive_limits
import query_complexity

# Import Layer 1 enhancement modules
import semantic_cluster

from search_research import UnifiedAsyncRouter
from quality_checker import QualityConfig


class MockSearchResult:
    """Mock search result for testing."""

    def __init__(self, title: str, content: str, score: float, source: str = "WEB"):
        self.title = title
        self.content = content
        self.score = score
        self.source = source
        self.url = None
        self.metadata = {}


async def measure_layer1a_search(
    query: str,
    mode: str = "auto",
    limit: int = 30
) -> tuple[float, list[Any]]:
    """Measure Layer 1A: Search execution with rule-based filtering.

    Args:
        query: Search query
        mode: Search mode
        limit: Result limit

    Returns:
        Tuple of (execution_time_seconds, results)
    """
    start = time.time()

    # Configure quality thresholds
    quality_config = QualityConfig(
        min_score=0.5,
        min_results=3,
        require_content_match=False
    )

    # Initialize unified router
    router = UnifiedAsyncRouter(
        mode=mode,
        enable_jmri=True,
        rrf_k=60,
        quality_config=quality_config
    )

    # Execute search
    results = await router.search_async(query, limit=limit)

    elapsed = time.time() - start

    return elapsed, results


def measure_layer1b_clustering(results: list[Any]) -> float:
    """Measure Layer 1B: Semantic clustering performance.

    Args:
        results: Search results to cluster

    Returns:
        Execution time in seconds
    """
    start = time.time()

    # Apply semantic clustering
    filtered = semantic_cluster.apply_semantic_clustering(
        results,
        similarity_threshold=0.4,
        max_results=25
    )

    elapsed = time.time() - start

    return elapsed


def measure_layer1c_complexity(query: str) -> float:
    """Measure Layer 1C: Query complexity scoring performance.

    Args:
        query: Search query

    Returns:
        Execution time in seconds
    """
    start = time.time()

    # Calculate complexity score
    score = query_complexity.calculate_complexity_score(query)

    elapsed = time.time() - start

    return elapsed


def measure_layer1d_limits(
    complexity_score: int,
    result_count: int
) -> float:
    """Measure Layer 1D: Adaptive limit calculation performance.

    Args:
        complexity_score: Query complexity score
        result_count: Number of results

    Returns:
        Execution time in seconds
    """
    start = time.time()

    # Get adaptive configuration
    config = adaptive_limits.get_adaptive_config(
        complexity_score=complexity_score,
        result_count=result_count
    )

    elapsed = time.time() - start

    return elapsed


async def run_performance_baseline() -> dict[str, Any]:
    """Run comprehensive performance baseline for all Layer 1 enhancements.

    Returns:
        Dict with baseline metrics for each layer
    """
    print("=" * 70)
    print("LAYER 1 PERFORMANCE BASELINE TEST")
    print("=" * 70)

    # Test queries with varying complexity
    test_queries = [
        ("async patterns", "Simple technical query"),
        ("python async await patterns", "Medium technical query"),
        ("how to implement authentication", "Complex ambiguous query"),
    ]

    results_summary = {
        "queries": [],
        "layer1a_time": [],
        "layer1b_time": [],
        "layer1c_time": [],
        "layer1d_time": [],
        "total_time": [],
    }

    for query, description in test_queries:
        print(f"\n{'=' * 70}")
        print(f"Testing: {description}")
        print(f"Query: '{query}'")
        print(f"{'=' * 70}")

        # Start memory tracking
        tracemalloc.start()

        # Layer 1A: Search execution
        print("\n[Layer 1A] Search execution...")
        layer1a_time, results = await measure_layer1a_search(query, limit=30)
        print(f"  → {layer1a_time * 1000:.2f}ms")
        print(f"  → {len(results)} results")

        # Layer 1B: Semantic clustering
        print("\n[Layer 1B] Semantic clustering...")
        layer1b_time = measure_layer1b_clustering(results)
        print(f"  → {layer1b_time * 1000:.2f}ms")

        # Layer 1C: Query complexity scoring
        print("\n[Layer 1C] Query complexity scoring...")
        layer1c_time = measure_layer1c_complexity(query)
        complexity_score = query_complexity.calculate_complexity_score(query)
        print(f"  → {layer1c_time * 1000:.2f}ms")
        print(f"  → Complexity score: {complexity_score}")

        # Layer 1D: Adaptive limits
        print("\n[Layer 1D] Adaptive limit calculation...")
        layer1d_time = measure_layer1d_limits(complexity_score, len(results))
        print(f"  → {layer1d_time * 1000:.2f}ms")

        # Calculate total time
        total_time = layer1a_time + layer1b_time + layer1c_time + layer1d_time

        # Get memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"\n[Total] {total_time * 1000:.2f}ms")
        print(f"[Memory] Peak: {peak / 1024:.2f} KB")

        # Store results
        results_summary["queries"].append({
            "query": query,
            "description": description,
            "layer1a_ms": layer1a_time * 1000,
            "layer1b_ms": layer1b_time * 1000,
            "layer1c_ms": layer1c_time * 1000,
            "layer1d_ms": layer1d_time * 1000,
            "total_ms": total_time * 1000,
            "memory_kb": peak / 1024,
        })

        results_summary["layer1a_time"].append(layer1a_time)
        results_summary["layer1b_time"].append(layer1b_time)
        results_summary["layer1c_time"].append(layer1c_time)
        results_summary["layer1d_time"].append(layer1d_time)
        results_summary["total_time"].append(total_time)

    # Calculate averages
    print(f"\n{'=' * 70}")
    print("AVERAGE PERFORMANCE METRICS")
    print(f"{'=' * 70}")

    avg_layer1a = sum(results_summary["layer1a_time"]) / len(results_summary["layer1a_time"]) * 1000
    avg_layer1b = sum(results_summary["layer1b_time"]) / len(results_summary["layer1b_time"]) * 1000
    avg_layer1c = sum(results_summary["layer1c_time"]) / len(results_summary["layer1c_time"]) * 1000
    avg_layer1d = sum(results_summary["layer1d_time"]) / len(results_summary["layer1d_time"]) * 1000
    avg_total = sum(results_summary["total_time"]) / len(results_summary["total_time"]) * 1000

    print(f"Layer 1A (Search):          {avg_layer1a:.2f}ms  (target: < 200ms)")
    print(f"Layer 1B (Clustering):       {avg_layer1b:.2f}ms  (target: < 500ms)")
    print(f"Layer 1C (Complexity):       {avg_layer1c:.2f}ms  (target: < 100ms)")
    print(f"Layer 1D (Adaptive Limits):  {avg_layer1d:.2f}ms  (target: < 50ms)")
    print(f"{'─' * 40}")
    print(f"TOTAL LAYER 1:              {avg_total:.2f}ms  (target: < 1000ms)")

    # Verify performance targets
    print(f"\n{'=' * 70}")
    print("PERFORMANCE TARGET VERIFICATION")
    print(f"{'=' * 70}")

    targets = {
        "Layer 1A (Search)": (avg_layer1a, 200),
        "Layer 1B (Clustering)": (avg_layer1b, 500),
        "Layer 1C (Complexity)": (avg_layer1c, 100),
        "Layer 1D (Adaptive Limits)": (avg_layer1d, 50),
        "TOTAL LAYER 1": (avg_total, 1000),
    }

    all_pass = True
    for name, (actual, target) in targets.items():
        status = "✅ PASS" if actual < target else "❌ FAIL"
        print(f"{name:25} {actual:.2f}ms / {target}ms  {status}")
        if actual >= target:
            all_pass = False

    print(f"\n{'=' * 70}")
    if all_pass:
        print("✅ ALL PERFORMANCE TARGETS MET")
    else:
        print("❌ SOME PERFORMANCE TARGETS NOT MET")
    print(f"{'=' * 70}")

    return results_summary


if __name__ == "__main__":
    import asyncio
    baseline = asyncio.run(run_performance_baseline())
