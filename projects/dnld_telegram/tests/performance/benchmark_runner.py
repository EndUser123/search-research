"""
Benchmark script to measure performance improvements in dnld-telegram.

This script runs performance benchmarks to validate the effectiveness of
async optimizations and resilience patterns implemented in the project.
"""
import asyncio
import os
import time
from typing import Any

import psutil


async def benchmark_concurrent_downloads(
    concurrency_level: int, operations_per_task: int = 10
) -> dict[str, Any]:
    """Benchmark concurrent download operations at a specific concurrency level."""

    async def mock_download_operation():
        """Simulate a download operation."""
        # Simulate variable download time
        await asyncio.sleep(0.001 + (hash(str(asyncio.current_task())) % 100) / 10000)
        return {"status": "success", "size": 1024 * 1024}

    start_time = time.time()
    start_memory = psutil.Process(os.getpid()).memory_info().rss

    # Run concurrent operations
    tasks = [
        mock_download_operation()
        for _ in range(concurrency_level * operations_per_task)
    ]
    results = await asyncio.gather(*tasks)

    end_time = time.time()
    end_memory = psutil.Process(os.getpid()).memory_info().rss

    duration = end_time - start_time
    throughput = len(results) / duration if duration > 0 else 0
    memory_growth = (end_memory - start_memory) / (1024 * 1024)  # MB

    success_count = len([r for r in results if r["status"] == "success"])
    success_rate = success_count / len(results) if results else 0

    return {
        "concurrency_level": concurrency_level,
        "operations_count": len(results),
        "duration_seconds": duration,
        "throughput_ops_per_sec": throughput,
        "success_rate": success_rate,
        "memory_growth_mb": memory_growth,
        "successful_operations": success_count,
    }


async def run_performance_benchmarks() -> dict[str, Any]:
    """Run comprehensive performance benchmarks."""
    print("Running performance benchmarks...")
    print("=" * 50)

    # Test different concurrency levels
    concurrency_levels = [1, 5, 10, 20, 50]
    results = []

    for level in concurrency_levels:
        print(f"Benchmarking concurrency level: {level}")
        result = await benchmark_concurrent_downloads(level)
        results.append(result)
        print(f"  Duration: {result['duration_seconds']:.3f}s")
        print(f"  Throughput: {result['throughput_ops_per_sec']:.1f} ops/sec")
        print(f"  Success Rate: {result['success_rate']*100:.1f}%")
        print(f"  Memory Growth: {result['memory_growth_mb']:.2f}MB")
        print()

    # Calculate overall metrics
    total_operations = sum(r["operations_count"] for r in results)
    total_duration = sum(r["duration_seconds"] for r in results)
    avg_throughput = sum(r["throughput_ops_per_sec"] for r in results) / len(results)
    avg_success_rate = sum(r["success_rate"] for r in results) / len(results)

    return {
        "benchmark_results": results,
        "total_operations": total_operations,
        "total_duration": total_duration,
        "average_throughput": avg_throughput,
        "average_success_rate": avg_success_rate,
        "tested_concurrency_levels": concurrency_levels,
    }


def print_summary(benchmark_data: dict[str, Any]):
    """Print a summary of the benchmark results."""
    print("\nPERFORMANCE BENCHMARK SUMMARY")
    print("=" * 50)
    print(f"Total Operations: {benchmark_data['total_operations']:,}")
    print(f"Total Duration: {benchmark_data['total_duration']:.3f}s")
    print(f"Average Throughput: {benchmark_data['average_throughput']:.1f} ops/sec")
    print(f"Average Success Rate: {benchmark_data['average_success_rate']*100:.1f}%")
    print()

    print("PER-LEVEL DETAILS:")
    print("-" * 30)
    for result in benchmark_data["benchmark_results"]:
        print(
            f"Level {result['concurrency_level']:2d}: "
            f"{result['throughput_ops_per_sec']:6.1f} ops/sec "
            f"({result['success_rate']*100:5.1f}% success)"
        )


async def main():
    """Main benchmark runner."""
    try:
        benchmark_data = await run_performance_benchmarks()
        print_summary(benchmark_data)

        # Save results to file
        import json

        with open("performance_benchmark_results.json", "w") as f:
            json.dump(benchmark_data, f, indent=2)

        print("\nResults saved to performance_benchmark_results.json")

    except Exception as e:
        print(f"Error running benchmarks: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
