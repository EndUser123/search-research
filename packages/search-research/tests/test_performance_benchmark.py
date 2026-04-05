#!/usr/bin/env python3
"""Performance benchmark for async backend detection.

This test measures the overhead of inspect.iscoroutinefunction() detection
to ensure the fix doesn't degrade /all skill performance.
"""

import asyncio
import statistics
import time

from search_research import AsyncSearchRouter


async def benchmark_async_detection_overhead():
    """Measure performance overhead of async backend detection."""

    # Create router
    router = AsyncSearchRouter()

    # Check available backends
    if not router._backends:
        print("⚠ No backends available - skipping benchmark")
        return

    print(f"Backends: {list(router._backends.keys())}")

    # Warmup
    for _ in range(5):
        await router.search_async("test query", limit=5)

    # Benchmark: Measure search latency
    iterations = 50
    latencies = []

    print(f"\nRunning {iterations} search iterations...")

    for i in range(iterations):
        start = time.perf_counter()
        await router.search_async("test query", limit=5)
        end = time.perf_counter()
        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{iterations} iterations")

    # Calculate statistics
    mean_latency = statistics.mean(latencies)
    median_latency = statistics.median(latencies)
    stdev_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
    min_latency = min(latencies)
    max_latency = max(latencies)
    p95_latency = statistics.quantiles(latencies, n=20)[18]  # 95th percentile

    print(f"\n{'=' * 60}")
    print("PERFORMANCE BENCHMARK RESULTS")
    print(f"{'=' * 60}")
    print(f"Iterations:      {iterations}")
    print(f"Mean latency:   {mean_latency:.2f} ms")
    print(f"Median latency: {median_latency:.2f} ms")
    print(f"Std deviation:  {stdev_latency:.2f} ms")
    print(f"Min latency:    {min_latency:.2f} ms")
    print(f"Max latency:    {max_latency:.2f} ms")
    print(f"95th percentile: {p95_latency:.2f} ms")
    print(f"{'=' * 60}")

    # Performance threshold check
    # Threshold: 100ms overhead is too much for interactive search
    OVERHEAD_THRESHOLD_MS = 100

    if mean_latency > OVERHEAD_THRESHOLD_MS:
        print(f"\n❌ FAILED: Mean latency ({mean_latency:.2f} ms) exceeds threshold ({OVERHEAD_THRESHOLD_MS} ms)")
        print("   Impact: /all skill will feel slow to users")
        return False
    else:
        print(f"\n✅ PASSED: Mean latency ({mean_latency:.2f} ms) within acceptable threshold ({OVERHEAD_THRESHOLD_MS} ms)")
        return True


async def main():
    """Run performance benchmark."""
    print("Performance Benchmark: Async Backend Detection Overhead")
    print("=" * 60)

    success = await benchmark_async_detection_overhead()

    if success:
        print("\n✅ Performance benchmark PASSED")
        return 0
    else:
        print("\n❌ Performance benchmark FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
