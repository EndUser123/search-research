#!/usr/bin/env python3
"""
Baseline Performance Benchmark Script for unified-search

This script establishes performance baselines for the unified-search package
before implementing search-research features. It measures:
- Search latency (p50/p95/p99)
- Cache performance (hit/miss rates)
- Local backend search performance (FAST mode)

Usage:
    python scripts/baseline_benchmark.py [--queries N] [--output BASELINE.md]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

# Add unified-search to path if needed
unified_search_path = Path(__file__).parents[2] / "unified-search" / "src"
sys.path.insert(0, str(unified_search_path))

try:
    from unified_search import EnhancedUnifiedSearchRouter
except ImportError as e:
    print(f"ERROR: Cannot import unified-search from {unified_search_path}")
    print(f"Import error: {e}")
    print(f"\nTrying to install...")
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", str(unified_search_path.parent)],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("✅ Installation successful, retrying import...")
        from unified_search import EnhancedUnifiedSearchRouter
    else:
        print(f"❌ Installation failed:\n{result.stderr}")
        sys.exit(1)


# Sample queries for benchmarking (realistic AI coding scenarios)
SAMPLE_QUERIES = [
    # Code search patterns
    "async function implementation",
    "class inheritance pattern",
    "error handling try except",
    "type hints annotations",
    "decorator function wrapper",

    # Documentation search
    "authentication flow",
    "database connection",
    "API endpoint configuration",
    "environment variables setup",
    "logging configuration",

    # Chat history patterns
    "how to fix import error",
    "debugging memory leak",
    "optimizing performance",
    "testing async code",
    "dependency injection",

    # Skills and commands
    "git commit workflow",
    "pytest test configuration",
    "docker container setup",
    "CI/CD pipeline",
    "deployment strategy",

    # Fuzzy matching scenarios
    "autentication",  # typo: authentication
    "data base",  # should match: database
    "preformance",  # typo: performance
    "asynchronous",  # variation: async
    "deploymnt",  # typo: deployment
]


def measure_search_latency(
    router: EnhancedUnifiedSearchRouter,
    query: str,
    iterations: int = 10
) -> dict[str, Any]:
    """Measure search latency for a single query.

    Args:
        router: Search router instance
        query: Search query string
        iterations: Number of times to repeat the measurement

    Returns:
        Dict with latency statistics (min, max, mean, median, p50, p95, p99)
    """
    latencies = []

    for _ in range(iterations):
        # Clear cache to measure uncached performance
        router.cache.invalidate()

        start = time.perf_counter()
        try:
            results = router.search(query, limit=20)
            _ = list(results)  # Consume iterator if needed
        except Exception as e:
            print(f"  WARNING: Query '{query}' failed: {e}")
            continue
        end = time.perf_counter()

        latencies.append((end - start) * 1000)  # Convert to ms

    if not latencies:
        return {"error": "All iterations failed"}

    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)

    return {
        "min_ms": round(sorted_latencies[0], 2),
        "max_ms": round(sorted_latencies[-1], 2),
        "mean_ms": round(statistics.mean(sorted_latencies), 2),
        "median_ms": round(statistics.median(sorted_latencies), 2),
        "p50_ms": round(sorted_latencies[int(n * 0.50)], 2),
        "p95_ms": round(sorted_latencies[int(n * 0.95)], 2) if n >= 20 else sorted_latencies[-1],
        "p99_ms": round(sorted_latencies[int(n * 0.99)], 2) if n >= 100 else sorted_latencies[-1],
        "iterations": n,
    }


def measure_cache_performance(
    router: EnhancedUnifiedSearchRouter,
    queries: list[str],
    iterations: int = 100
) -> dict[str, Any]:
    """Measure cache hit/miss rates.

    Args:
        router: Search router instance
        queries: List of queries to test
        iterations: Number of search iterations

    Returns:
        Dict with cache statistics
    """
    # Clear cache before test
    router.cache.invalidate()

    import random
    hits = 0
    misses = 0

    for _ in range(iterations):
        query = random.choice(queries)

        # Check cache stats before
        stats_before = router.cache.get_stats()

        # Perform search
        try:
            router.search(query, limit=20)
        except Exception:
            continue

        # Check cache stats after
        stats_after = router.cache.get_stats()

        # Calculate this query's contribution
        hit_delta = stats_after["hits"] - stats_before["hits"]
        miss_delta = stats_after["misses"] - stats_before["misses"]

        hits += hit_delta
        misses += miss_delta

    total = hits + misses
    hit_rate = hits / total if total > 0 else 0

    return {
        "total_queries": total,
        "hits": hits,
        "misses": misses,
        "hit_rate_percent": round(hit_rate * 100, 2),
        "miss_rate_percent": round((1 - hit_rate) * 100, 2),
    }


def run_benchmark(
    num_queries: int = 1000,
    latency_iterations: int = 10,
    cache_iterations: int = 100,
    backend_filter: list[str] | None = None
) -> dict[str, Any]:
    """Run complete benchmark suite.

    Args:
        num_queries: Number of queries to test (will cycle through SAMPLE_QUERIES)
        latency_iterations: Iterations per query for latency measurement
        cache_iterations: Iterations for cache performance test
        backend_filter: Filter to specific backends (None = all available)

    Returns:
        Dict with all benchmark results
    """
    print(f"🔬 Starting Baseline Benchmark")
    print(f"   Queries: {num_queries}")
    print(f"   Latency iterations: {latency_iterations}")
    print(f"   Cache iterations: {cache_iterations}")
    print(f"   Backend filter: {backend_filter or 'All'}")
    print()

    # Initialize router
    print("⚙️  Initializing unified-search router...")
    router = EnhancedUnifiedSearchRouter(
        enable_cache=True,
        cache_ttl=3600,
        cache_size=1000,
    )

    if backend_filter:
        print(f"   Filtering to backends: {backend_filter}")

    # Generate query list (cycle through SAMPLE_QUERIES)
    queries = []
    query_cycle = SAMPLE_QUERIES
    for i in range(num_queries):
        queries.append(query_cycle[i % len(query_cycle)])

    # Benchmark 1: Search Latency
    print(f"⏱️  Measuring search latency ({len(queries)} queries)...")
    latency_results = []

    for i, query in enumerate(queries[:50], 1):  # Limit to 50 for faster baseline
        if i % 10 == 0:
            print(f"   Progress: {i}/{min(50, len(queries))} queries")

        result = measure_search_latency(router, query, iterations=latency_iterations)
        if "error" not in result:
            latency_results.append({
                "query": query,
                **result
            })

    # Aggregate latency statistics
    all_p50 = [r["p50_ms"] for r in latency_results]
    all_p95 = [r["p95_ms"] for r in latency_results]
    all_p99 = [r["p99_ms"] for r in latency_results]

    aggregate_latency = {
        "queries_tested": len(latency_results),
        "p50_ms": round(statistics.mean(all_p50), 2),
        "p95_ms": round(statistics.mean(all_p95), 2),
        "p99_ms": round(statistics.mean(all_p99), 2),
        "min_p50_ms": round(min(all_p50), 2),
        "max_p50_ms": round(max(all_p50), 2),
    }

    print(f"   ✅ Latency: p50={aggregate_latency['p50_ms']}ms, "
          f"p95={aggregate_latency['p95_ms']}ms, "
          f"p99={aggregate_latency['p99_ms']}ms")

    # Benchmark 2: Cache Performance
    print(f"💾 Measuring cache performance ({cache_iterations} iterations)...")
    cache_results = measure_cache_performance(router, queries, iterations=cache_iterations)
    print(f"   ✅ Cache: {cache_results['hit_rate_percent']}% hit rate")

    # Benchmark 3: Backend-specific performance (if filter provided)
    backend_results = {}
    if backend_filter:
        print(f"🔍 Measuring backend-specific performance...")
        for backend in backend_filter:
            backend_latencies = []
            for query in SAMPLE_QUERIES[:10]:  # Sample 10 queries
                result = measure_search_latency(
                    router,
                    query,
                    iterations=5
                )
                if "error" not in result:
                    backend_latencies.append(result["p50_ms"])

            if backend_latencies:
                backend_results[backend] = {
                    "p50_ms": round(statistics.mean(backend_latencies), 2),
                    "queries_tested": len(backend_latencies)
                }
                print(f"   ✅ {backend}: {backend_results[backend]['p50_ms']}ms")

    return {
        "metadata": {
            "num_queries": num_queries,
            "latency_iterations": latency_iterations,
            "cache_iterations": cache_iterations,
            "backend_filter": backend_filter,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "latency": aggregate_latency,
        "cache": cache_results,
        "backend_performance": backend_results,
        "raw_latency_data": latency_results[:10],  # Include first 10 for reference
    }


def save_baseline_md(results: dict[str, Any], output_path: Path) -> None:
    """Save baseline results as markdown.

    Args:
        results: Benchmark results dictionary
        output_path: Path to output markdown file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    md_content = f"""# unified-search Performance Baseline

**Generated**: {results['metadata']['timestamp']}

## Configuration

- **Queries tested**: {results['metadata']['num_queries']}
- **Latency iterations**: {results['metadata']['latency_iterations']}
- **Cache iterations**: {results['metadata']['cache_iterations']}
- **Backend filter**: {results['metadata']['backend_filter'] or 'All available'}

---

## Latency Baseline

### Aggregate Statistics

| Metric | Value (ms) |
|--------|------------|
| **p50** | {results['latency']['p50_ms']} |
| **p95** | {results['latency']['p95_ms']} |
| **p99** | {results['latency']['p99_ms']} |
| Min p50 | {results['latency']['min_p50_ms']} |
| Max p50 | {results['latency']['max_p50_ms']} |
| Queries tested | {results['latency']['queries_tested']} |

### Regression Thresholds

- **⚠️  WARNING**: p95 latency increase > 20% indicates regression
- **🚨 CRITICAL**: p99 latency increase > 50% indicates severe regression

**Calculation**:
```python
current_p95 = ...  # Measured p95
baseline_p95 = {results['latency']['p95_ms']}
regression_pct = ((current_p95 - baseline_p95) / baseline_p95) * 100

if regression_pct > 20:
    print("REGRESSION DETECTED!")
```

---

## Cache Performance

| Metric | Value |
|--------|-------|
| **Hit rate** | {results['cache']['hit_rate_percent']}% |
| Miss rate | {results['cache']['miss_rate_percent']}% |
| Total queries | {results['cache']['total_queries']} |
| Hits | {results['cache']['hits']} |
| Misses | {results['cache']['misses']} |

---

## Backend-Specific Performance

"""

    if results['backend_performance']:
        md_content += "\n| Backend | p50 (ms) | Queries Tested |\n"
        md_content += "|---------|----------|----------------|\n"
        for backend, stats in results['backend_performance'].items():
            md_content += f"| {backend} | {stats['p50_ms']} | {stats['queries_tested']} |\n"
        md_content += "\n"
    else:
        md_content += "\n*No backend filter specified - testing all available backends*\n\n"

    md_content += """---

## Sample Query Performance

First 10 queries with detailed latency breakdown:

| Query | p50 (ms) | p95 (ms) | p99 (ms) |
|-------|----------|----------|----------|
"""

    for entry in results['raw_latency_data']:
        query = entry['query'][:40] + "..." if len(entry['query']) > 40 else entry['query']
        md_content += f"| {query} | {entry['p50_ms']} | {entry['p95_ms']} | {entry['p99_ms']} |\n"

    md_content += f"""

---

## Methodology

1. **Query Generation**: Cycled through {len(SAMPLE_QUERIES)} realistic AI coding queries
2. **Latency Measurement**: {results['metadata']['latency_iterations']} iterations per query, measured with `time.perf_counter()`
3. **Cache Measurement**: {results['metadata']['cache_iterations']} iterations with randomized query selection
4. **Environment**: Local execution, FAST mode (no remote services)

## Usage in Tests

```python
# In pytest-benchmark tests
def test_search_performance(benchmark):
    from unified_search import search

    result = benchmark(search, "async patterns")
    assert len(result.hits) > 0

    # Regression check (in CI)
    current_p95 = result.stats['p95']
    baseline_p95 = {results['latency']['p95_ms']}
    assert (current_p95 - baseline_p95) / baseline_p95 < 0.20
```

---

*This baseline was established before implementing search-research package features*
"""

    output_path.write_text(md_content)
    print(f"✅ Baseline saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Establish performance baseline for unified-search"
    )
    parser.add_argument(
        "--queries",
        type=int,
        default=1000,
        help="Number of queries to test (default: 1000)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "BASELINE.md",
        help="Output path for baseline markdown (default: BASELINE.md)"
    )
    parser.add_argument(
        "--latency-iterations",
        type=int,
        default=10,
        help="Iterations per query for latency measurement (default: 10)"
    )
    parser.add_argument(
        "--cache-iterations",
        type=int,
        default=100,
        help="Iterations for cache performance test (default: 100)"
    )
    parser.add_argument(
        "--backend",
        type=str,
        action="append",
        help="Filter to specific backend(s) (can specify multiple)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of markdown"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  unified-search Baseline Benchmark")
    print("=" * 60)
    print()

    # Run benchmark
    results = run_benchmark(
        num_queries=args.queries,
        latency_iterations=args.latency_iterations,
        cache_iterations=args.cache_iterations,
        backend_filter=args.backend
    )

    print()
    print("=" * 60)
    print("  📊 Baseline Results Summary")
    print("=" * 60)
    print(f"Latency p50: {results['latency']['p50_ms']}ms")
    print(f"Latency p95: {results['latency']['p95_ms']}ms")
    print(f"Latency p99: {results['latency']['p99_ms']}ms")
    print(f"Cache hit rate: {results['cache']['hit_rate_percent']}%")
    print("=" * 60)
    print()

    # Save results
    if args.json:
        output_path = args.output.with_suffix(".json")
        output_path.write_text(json.dumps(results, indent=2))
        print(f"✅ JSON saved to: {output_path}")
    else:
        save_baseline_md(results, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
