#!/usr/bin/env python3
"""
Benchmark script to measure hook execution latency.

Compares subprocess vs in-process execution for all hook events.
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys
import time
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from __lib.hook_importer import HookImporter


def measure_subprocess_latency(
    hook_file: Path,
    timeout: float = 15.0,
    iterations: int = 10
) -> dict[str, float]:
    """Measure subprocess hook execution latency."""

    latencies = []

    for _ in range(iterations):
        # Prepare minimal stdin data
        input_data = json.dumps({"test": "data"})

        start = time.perf_counter()

        result = subprocess.run(
            [
                sys.executable,
                HOOKS_DIR / "__lib" / "hook_runner.py",
                str(hook_file),
                "--timeout", str(timeout)
            ],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )

        end = time.perf_counter()

        latencies.append((end - start) * 1000)  # Convert to ms

    return {
        "mean_ms": statistics.mean(latencies),
        "median_ms": statistics.median(latencies),
        "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "iterations": iterations
    }


def measure_in_process_latency(
    hook_name: str,
    iterations: int = 10
) -> dict[str, float]:
    """Measure in-process hook execution latency."""

    importer = HookImporter(HOOKS_DIR)
    latencies = []

    # Prepare stdin data
    old_stdin = sys.stdin
    input_data = json.dumps({"test": "data"})

    try:
        for _ in range(iterations):
            sys.stdin = __import__("io").StringIO(input_data)

            start = time.perf_counter()

            result = importer.execute_hook(hook_name, timeout=15.0)

            end = time.perf_counter()

            latencies.append((end - start) * 1000)  # Convert to ms

    finally:
        sys.stdin = old_stdin

    return {
        "mean_ms": statistics.mean(latencies),
        "median_ms": statistics.median(latencies),
        "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
        "min_ms": min(latencies),
        "max_ms": max(latencies),
        "iterations": iterations
    }


def benchmark_hook(hook_name: str, iterations: int = 10) -> dict:
    """Benchmark both subprocess and in-process execution for a hook."""

    hook_file = HOOKS_DIR / f"{hook_name}.py"

    print(f"\n{'='*60}")
    print(f"Benchmarking: {hook_name}")
    print(f"{'='*60}")

    results = {
        "hook": hook_name,
        "iterations": iterations
    }

    # Measure subprocess latency
    print(f"\n📊 Measuring subprocess latency ({iterations} iterations)...")
    subprocess_results = measure_subprocess_latency(hook_file, iterations=iterations)
    results["subprocess"] = subprocess_results

    print(f"   Mean:   {subprocess_results['mean_ms']:.2f} ms")
    print(f"   Median: {subprocess_results['median_ms']:.2f} ms")
    print(f"   Min:    {subprocess_results['min_ms']:.2f} ms")
    print(f"   Max:    {subprocess_results['max_ms']:.2f} ms")
    print(f"   Stdev:  {subprocess_results['stdev_ms']:.2f} ms")

    # Measure in-process latency
    print(f"\n📊 Measuring in-process latency ({iterations} iterations)...")

    try:
        in_process_results = measure_in_process_latency(hook_name, iterations=iterations)
        results["in_process"] = in_process_results

        print(f"   Mean:   {in_process_results['mean_ms']:.2f} ms")
        print(f"   Median: {in_process_results['median_ms']:.2f} ms")
        print(f"   Min:    {in_process_results['min_ms']:.2f} ms")
        print(f"   Max:    {in_process_results['max_ms']:.2f} ms")
        print(f"   Stdev:  {in_process_results['stdev_ms']:.2f} ms")

        # Calculate improvement
        improvement = (
            (subprocess_results['mean_ms'] - in_process_results['mean_ms'])
            / subprocess_results['mean_ms'] * 100
        )
        results["improvement_percent"] = improvement

        print(f"\n✅ Improvement: {improvement:.1f}% latency reduction")

    except Exception as e:
        print(f"\n❌ In-process execution failed: {e}")
        results["in_process"] = None
        results["improvement_percent"] = 0.0

    return results


def main():
    """Run benchmark suite."""

    print("\n" + "="*60)
    print("Hook Execution Latency Benchmark")
    print("="*60)

    # Hooks to benchmark
    hooks = [
        "PreToolUse",
        "Stop",
        "SessionStart",
        # "UserPromptSubmit",  # Skip - known limitation with relative imports
    ]

    iterations = 10
    all_results = []

    for hook_name in hooks:
        try:
            results = benchmark_hook(hook_name, iterations=iterations)
            all_results.append(results)
        except Exception as e:
            print(f"\n❌ Failed to benchmark {hook_name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    for results in all_results:
        hook = results["hook"]
        subprocess_ms = results["subprocess"]["mean_ms"]
        in_process = results.get("in_process")

        if in_process:
            in_process_ms = in_process["mean_ms"]
            improvement = results["improvement_percent"]
            print(f"\n{hook}:")
            print(f"  Subprocess:  {subprocess_ms:.2f} ms")
            print(f"  In-process:  {in_process_ms:.2f} ms")
            print(f"  Improvement: {improvement:.1f}%")
        else:
            print(f"\n{hook}:")
            print(f"  Subprocess:  {subprocess_ms:.2f} ms")
            print("  In-process:  FAILED")

    # Save results to JSON
    results_file = HOOKS_DIR / "benchmarks" / "latency_results.json"
    results_file.parent.mkdir(exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")

    # Calculate overall improvement
    improvements = [
        r["improvement_percent"]
        for r in all_results
        if r.get("improvement_percent", 0) > 0
    ]

    if improvements:
        avg_improvement = statistics.mean(improvements)
        print(f"\n📈 Average latency reduction: {avg_improvement:.1f}%")


if __name__ == "__main__":
    main()
