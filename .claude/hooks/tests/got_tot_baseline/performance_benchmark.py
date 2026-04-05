"""
Performance benchmarks for GoT/ToT baseline regression tests.

This module establishes performance baselines for all 9 target skills
before Graph-of-Thought and Tree-of-Thought integration.

Measurements:
- Execution time (mean, median, min, max)
- Memory usage (peak, allocated)
- CPU usage
- Test throughput (tests/second)

Usage:
    python performance_benchmark.py                    # Run all benchmarks
    python performance_benchmark.py --skill trace      # Benchmark single skill
    python performance_benchmark.py --compare          # Compare against baseline
"""

import json
import subprocess
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class PerformanceBenchmark:
    """Run performance benchmarks on baseline regression tests."""

    def __init__(self, baseline_dir: Path):
        self.baseline_dir = baseline_dir
        self.results = {}

    def run_pytest_with_timing(self, test_file: Path) -> Dict[str, Any]:
        """Run pytest test file and collect timing metrics."""
        start_time = time.perf_counter()
        tracemalloc.start()

        try:
            # Run pytest with verbose output
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(test_file), "-v"],
                capture_output=True,
                text=True,
                cwd=self.baseline_dir
            )

            elapsed = time.perf_counter() - start_time
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Parse output for test count
            test_count = 0
            for line in result.stdout.split("\n"):
                # Look for "collected X items"
                if "collected" in line and "items" in line:
                    # Extract number from "collected 13 items"
                    import re
                    match = re.search(r'collected (\d+) items', line)
                    if match:
                        test_count = int(match.group(1))
                        break  # Found collection count, no need to continue

                # Also look for final summary "X passed in Y.YYs"
                elif " passed" in line and "==" not in line and "seconds" not in line:
                    # Extract from "13 passed in 0.32s"
                    import re
                    match = re.search(r'(\d+) passed', line)
                    if match and test_count == 0:  # Only use if collection didn't work
                        test_count = int(match.group(1))

            return {
                "success": result.returncode == 0,
                "exit_code": result.returncode,
                "elapsed_seconds": round(elapsed, 3),
                "memory_peak_mb": round(peak / 1024 / 1024, 2),
                "memory_current_mb": round(current / 1024 / 1024, 2),
                "test_count": test_count,
                "tests_per_second": round(test_count / elapsed, 2) if elapsed > 0 else 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            tracemalloc.stop()
            return {
                "success": False,
                "error": str(e),
                "elapsed_seconds": round(time.perf_counter() - start_time, 3)
            }

    def benchmark_all_skills(self) -> Dict[str, Any]:
        """Benchmark all 9 target skills."""
        skills = [
            "test_trace_baseline.py",
            "test_t_baseline.py",
            "test_debugrca_baseline.py",
            "test_arch_baseline.py",
            "test_plan_workflow_baseline.py",
            "test_p_baseline.py",
            "test_q_baseline.py",
            "test_r_baseline.py",
            "test_s_baseline.py"
        ]

        print("=" * 70)
        print("PERFORMANCE BENCHMARK: GoT/ToT Baseline Regression Tests")
        print("=" * 70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Baseline directory: {self.baseline_dir}")
        print()

        results = {}
        total_time = 0
        total_tests = 0

        for skill_file in skills:
            skill_name = skill_file.replace("test_", "").replace("_baseline.py", "")
            test_path = self.baseline_dir / skill_file

            print(f"Benchmarking /{skill_name}...")

            if not test_path.exists():
                print(f"  ⚠️  SKIP: Test file not found: {test_path}")
                continue

            result = self.run_pytest_with_timing(test_path)
            results[skill_name] = result

            if result.get("success"):
                print(f"  ✅ {result['test_count']} tests in {result['elapsed_seconds']}s")
                print(f"     Memory: {result['memory_peak_mb']} MB peak")
                print(f"     Throughput: {result['tests_per_second']} tests/sec")
                total_time += result['elapsed_seconds']
                total_tests += result['test_count']
            else:
                print(f"  ❌ FAILED: {result.get('error', 'Unknown error')}")

            print()

        # Summary
        print("=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        print(f"Total skills tested: {len(results)}")
        print(f"Total tests run: {total_tests}")
        print(f"Total time: {round(total_time, 2)}s")
        print(f"Overall throughput: {round(total_tests / total_time, 2)} tests/sec")
        print()

        # Per-skill breakdown table
        print("PER-SKILL BREAKDOWN:")
        print("-" * 70)
        print(f"{'Skill':<20} {'Tests':<8} {'Time (s)':<10} {'Memory (MB)':<12} {'Tests/s':<10}")
        print("-" * 70)

        for skill_name, result in sorted(results.items()):
            if result.get("success"):
                print(
                    f"/{skill_name:<19} "
                    f"{result['test_count']:<8} "
                    f"{result['elapsed_seconds']:<10.3f} "
                    f"{result['memory_peak_mb']:<12.2f} "
                    f"{result['tests_per_second']:<10.2f}"
                )

        print("-" * 70)

        return {
            "timestamp": datetime.now().isoformat(),
            "baseline_dir": str(self.baseline_dir),
            "results": results,
            "summary": {
                "total_skills": len(results),
                "total_tests": total_tests,
                "total_time": round(total_time, 2),
                "overall_throughput": round(total_tests / total_time, 2) if total_time > 0 else 0
            }
        }

    def save_baseline(self, results: Dict[str, Any]) -> Path:
        """Save benchmark results to baseline file."""
        baseline_path = self.baseline_dir / "performance_baseline.json"

        with open(baseline_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✅ Baseline saved: {baseline_path}")
        return baseline_path

    def compare_to_baseline(self, current_results: Dict[str, Any]) -> None:
        """Compare current results to saved baseline."""
        baseline_path = self.baseline_dir / "performance_baseline.json"

        if not baseline_path.exists():
            print(f"⚠️  No baseline found for comparison: {baseline_path}")
            return

        with open(baseline_path) as f:
            baseline = json.load(f)

        print("\n" + "=" * 70)
        print("PERFORMANCE COMPARISON: Current vs Baseline")
        print("=" * 70)
        print(f"Baseline timestamp: {baseline.get('timestamp', 'Unknown')}")
        print(f"Current timestamp: {current_results.get('timestamp', 'Unknown')}")
        print()

        # Compare per-skill metrics
        baseline_results = baseline.get("results", {})
        current_results_dict = current_results.get("results", {})

        print(f"{'Skill':<20} {'Metric':<15} {'Baseline':<12} {'Current':<12} {'Delta':<10}")
        print("-" * 70)

        for skill_name in sorted(set(list(baseline_results.keys()) + list(current_results_dict.keys()))):
            baseline_skill = baseline_results.get(skill_name, {})
            current_skill = current_results_dict.get(skill_name, {})

            # Compare execution time
            if baseline_skill.get("success") and current_skill.get("success"):
                baseline_time = baseline_skill.get("elapsed_seconds", 0)
                current_time = current_skill.get("elapsed_seconds", 0)
                delta = current_time - baseline_time
                delta_pct = (delta / baseline_time * 100) if baseline_time > 0 else 0

                delta_str = f"{delta:+.3f}s ({delta_pct:+.1f}%)"

                # Color coding (text-based)
                indicator = "✅" if abs(delta_pct) < 10 else ("⚠️" if abs(delta_pct) < 25 else "❌")

                print(
                    f"/{skill_name:<19} "
                    f"{'Time':<15} "
                    f"{baseline_time:<12.3f} "
                    f"{current_time:<12.3f} "
                    f"{delta_str:<10} {indicator}"
                )

                # Compare memory
                baseline_mem = baseline_skill.get("memory_peak_mb", 0)
                current_mem = current_skill.get("memory_peak_mb", 0)
                mem_delta = current_mem - baseline_mem
                mem_delta_pct = (mem_delta / baseline_mem * 100) if baseline_mem > 0 else 0

                mem_delta_str = f"{mem_delta:+.2f} MB ({mem_delta_pct:+.1f}%)"
                mem_indicator = "✅" if abs(mem_delta_pct) < 10 else ("⚠️" if abs(mem_delta_pct) < 25 else "❌")

                print(
                    f"{'':<20} "
                    f"{'Memory':<15} "
                    f"{baseline_mem:<12.2f} "
                    f"{current_mem:<12.2f} "
                    f"{mem_delta_str:<10} {mem_indicator}"
                )

        print("-" * 70)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Performance benchmarks for GoT/ToT baseline tests"
    )
    parser.add_argument(
        "--skill",
        type=str,
        help="Benchmark specific skill (e.g., trace, t, debugrca)"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare results against saved baseline"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        default=True,
        help="Save results as baseline (default: True)"
    )

    args = parser.parse_args()

    # Determine baseline directory
    script_dir = Path(__file__).resolve().parent
    baseline_dir = script_dir

    # Run benchmarks
    benchmark = PerformanceBenchmark(baseline_dir)

    if args.skill:
        # Single skill benchmark (not implemented yet, would need filtering)
        print("Single skill benchmarking not yet implemented. Running all skills.")
        results = benchmark.benchmark_all_skills()
    else:
        results = benchmark.benchmark_all_skills()

    # Save baseline
    if args.save:
        baseline_path = benchmark.save_baseline(results)

    # Compare if requested
    if args.compare:
        benchmark.compare_to_baseline(results)


if __name__ == "__main__":
    main()
