#!/usr/bin/env python3
"""
Performance benchmarking script for log_chunker.
Tests processing speed, memory usage, and scalability.

Usage:
    python scripts/benchmark.py --log-file sample.log --iterations 5
    python scripts/benchmark.py --generate-test-data --size large
"""

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import psutil

sys.path.insert(0, "src")

from log_chunker.config import ChunkingConfig
from log_chunker.log_chunker import LogChunker


class PerformanceBenchmark:
    """Performance benchmarking for log_chunker."""

    def __init__(self):
        self.results = {}
        self.process = psutil.Process(os.getpid())

    def generate_test_log(self, size: str) -> Path:
        """Generate test log file of specified size."""
        sizes = {
            "small": 100,  # 100 lines
            "medium": 10000,  # 10K lines
            "large": 100000,  # 100K lines
            "xlarge": 1000000,  # 1M lines
        }

        line_count = sizes.get(size, 1000)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            for i in range(line_count):
                timestamp = f"2025-07-14 {(i // 3600):02d}:{(i % 3600 // 60):02d}:{(i % 60):02d},000"
                level = ["INFO", "DEBUG", "WARNING", "ERROR"][i % 4]
                service = f"service{i % 10}"
                message = f"Processing request {i} with data payload {i * 123}"

                if i % 100 == 0:  # Add some errors
                    level = "ERROR"
                    message = f"Failed to process request {i}: Connection timeout"

                f.write(f"{timestamp} - {level} - {service} - {message}\n")

            return Path(f.name)

    def measure_memory_usage(self) -> dict[str, float]:
        """Get current memory usage metrics."""
        memory_info = self.process.memory_info()
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": self.process.memory_percent(),
        }

    def benchmark_processing_speed(
        self, log_file: Path, iterations: int = 3
    ) -> dict[str, Any]:
        """Benchmark log processing speed."""
        print(f"Benchmarking processing speed with {iterations} iterations...")

        times = []
        memory_usage = []

        for i in range(iterations):
            print(f"  Iteration {i + 1}/{iterations}")

            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir)

                # Measure initial memory
                initial_memory = self.measure_memory_usage()

                # Time the processing
                start_time = time.time()

                chunker = LogChunker()
                result = chunker.process_log_file(log_file, output_dir)

                end_time = time.time()

                # Measure final memory
                final_memory = self.measure_memory_usage()

                processing_time = end_time - start_time
                times.append(processing_time)

                memory_delta = final_memory["rss_mb"] - initial_memory["rss_mb"]
                memory_usage.append(
                    {
                        "initial_mb": initial_memory["rss_mb"],
                        "final_mb": final_memory["rss_mb"],
                        "delta_mb": memory_delta,
                        "lines_processed": result.intelligence_report.total_lines_processed,
                    }
                )

        return {
            "iterations": iterations,
            "times_seconds": times,
            "avg_time_seconds": sum(times) / len(times),
            "min_time_seconds": min(times),
            "max_time_seconds": max(times),
            "memory_usage": memory_usage,
            "avg_memory_delta_mb": sum(m["delta_mb"] for m in memory_usage)
            / len(memory_usage),
        }

    def benchmark_scalability(self) -> dict[str, Any]:
        """Benchmark scalability across different log sizes."""
        print("Benchmarking scalability across log sizes...")

        scalability_results = {}

        for size in ["small", "medium", "large"]:
            print(f"  Testing {size} log size...")

            test_log = self.generate_test_log(size)

            try:
                result = self.benchmark_processing_speed(test_log, iterations=2)

                # Calculate lines per second
                avg_time = result["avg_time_seconds"]
                lines_processed = result["memory_usage"][0]["lines_processed"]
                lines_per_second = lines_processed / avg_time if avg_time > 0 else 0

                scalability_results[size] = {
                    "lines_processed": lines_processed,
                    "avg_processing_time": avg_time,
                    "lines_per_second": lines_per_second,
                    "avg_memory_usage_mb": result["avg_memory_delta_mb"],
                }

            finally:
                if test_log.exists():
                    test_log.unlink()

        return scalability_results

    def benchmark_feature_performance(self, log_file: Path) -> dict[str, Any]:
        """Benchmark performance of individual features."""
        print("Benchmarking individual feature performance...")

        feature_results = {}

        # Test with different feature combinations
        configs = {
            "minimal": ChunkingConfig(
                enable_semantic_analysis=False,
                enable_error_deduplication=False,
                enable_anomaly_detection=False,
            ),
            "semantic_only": ChunkingConfig(
                enable_semantic_analysis=True,
                enable_error_deduplication=False,
                enable_anomaly_detection=False,
            ),
            "full_features": ChunkingConfig(
                enable_semantic_analysis=True,
                enable_error_deduplication=True,
                enable_anomaly_detection=True,
            ),
        }

        for config_name, config in configs.items():
            print(f"  Testing {config_name} configuration...")

            with tempfile.TemporaryDirectory() as temp_dir:
                output_dir = Path(temp_dir)

                start_time = time.time()
                initial_memory = self.measure_memory_usage()

                chunker = LogChunker(config)
                result = chunker.process_log_file(log_file, output_dir)

                end_time = time.time()
                final_memory = self.measure_memory_usage()

                feature_results[config_name] = {
                    "processing_time": end_time - start_time,
                    "memory_delta_mb": final_memory["rss_mb"]
                    - initial_memory["rss_mb"],
                    "lines_processed": result.intelligence_report.total_lines_processed,
                    "error_patterns_found": len(
                        result.intelligence_report.error_patterns
                    ),
                    "semantic_clusters_found": len(
                        result.intelligence_report.semantic_clusters
                    ),
                }

        return feature_results

    def run_comprehensive_benchmark(
        self, log_file: Path, iterations: int = 3
    ) -> dict[str, Any]:
        """Run comprehensive performance benchmark."""
        print(f"Running comprehensive benchmark on {log_file}")
        print(f"Log file size: {log_file.stat().st_size / 1024 / 1024:.2f} MB")

        results = {
            "log_file": str(log_file),
            "log_size_mb": log_file.stat().st_size / 1024 / 1024,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
                "python_version": sys.version,
            },
        }

        # Processing speed benchmark
        results["processing_speed"] = self.benchmark_processing_speed(
            log_file, iterations
        )

        # Feature performance benchmark
        results["feature_performance"] = self.benchmark_feature_performance(log_file)

        # Scalability benchmark (if using generated data)
        if "generated" in str(log_file):
            results["scalability"] = self.benchmark_scalability()

        return results

    def save_results(self, results: dict[str, Any], output_file: Path):
        """Save benchmark results to file."""
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nBenchmark results saved to: {output_file}")

    def print_summary(self, results: dict[str, Any]):
        """Print benchmark summary."""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)

        # Processing speed summary
        speed = results["processing_speed"]
        print(f"Processing Speed (avg): {speed['avg_time_seconds']:.2f} seconds")
        print(f"Memory Usage (avg): {speed['avg_memory_delta_mb']:.2f} MB")

        if "memory_usage" in speed and speed["memory_usage"]:
            lines = speed["memory_usage"][0]["lines_processed"]
            lines_per_sec = lines / speed["avg_time_seconds"]
            print(f"Throughput: {lines_per_sec:.0f} lines/second")

        # Feature performance summary
        if "feature_performance" in results:
            print("\nFeature Performance:")
            for feature, data in results["feature_performance"].items():
                print(
                    f"  {feature:15s}: {data['processing_time']:.2f}s, {data['memory_delta_mb']:.1f}MB"
                )

        # Scalability summary
        if "scalability" in results:
            print("\nScalability:")
            for size, data in results["scalability"].items():
                print(f"  {size:10s}: {data['lines_per_second']:.0f} lines/sec")


def main():
    parser = argparse.ArgumentParser(description="Benchmark log_chunker performance")
    parser.add_argument("--log-file", type=Path, help="Log file to benchmark")
    parser.add_argument(
        "--generate-test-data", action="store_true", help="Generate test data"
    )
    parser.add_argument(
        "--size",
        choices=["small", "medium", "large", "xlarge"],
        default="medium",
        help="Size of generated test data",
    )
    parser.add_argument(
        "--iterations", type=int, default=3, help="Number of benchmark iterations"
    )
    parser.add_argument("--output", type=Path, help="Output file for results")

    args = parser.parse_args()

    benchmark = PerformanceBenchmark()

    # Determine log file to use
    if args.generate_test_data:
        print(f"Generating {args.size} test log...")
        log_file = benchmark.generate_test_log(args.size)
        cleanup_log = True
    elif args.log_file:
        log_file = args.log_file
        cleanup_log = False
    else:
        # Use sample.log if available
        log_file = Path("sample.log")
        if not log_file.exists():
            print("Error: No log file specified and sample.log not found")
            print("Use --log-file or --generate-test-data")
            sys.exit(1)
        cleanup_log = False

    try:
        # Run benchmark
        results = benchmark.run_comprehensive_benchmark(log_file, args.iterations)

        # Print summary
        benchmark.print_summary(results)

        # Save results
        if args.output:
            benchmark.save_results(results, args.output)
        else:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = Path(f"benchmark_results_{timestamp}.json")
            benchmark.save_results(results, output_file)

    finally:
        # Cleanup generated test file
        if cleanup_log and log_file.exists():
            log_file.unlink()


if __name__ == "__main__":
    main()
