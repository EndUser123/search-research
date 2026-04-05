"""
Performance Benchmark Tests for Phase 2 Infrastructure.

This module defines comprehensive performance benchmarks for all Phase 2 components
including parallel processing, batch operations, and resource utilization.

Benchmark Categories:
- Throughput Benchmarks
- Latency Measurements
- Resource Utilization
- Scalability Tests
- Stress Tests
"""

import json
import shutil
import tempfile
import threading
import time
import unittest
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import psutil

# Performance target definitions
PERFORMANCE_BENCHMARKS = {
    'parallel_processing': {
        'files_per_second_per_worker': 50,
        'max_workers': 8,
        'optimal_batch_size': 50,
        'worker_efficiency_threshold': 80,  # percentage
    },
    'memory_management': {
        'base_memory_mb': 50,
        'per_batch_memory_mb': 100,
        'peak_memory_mb': 500,
        'memory_leak_threshold': 5,  # MB increase over time
    },
    'disk_io': {
        'backup_speed_mb_per_sec': 50,
        'file_processing_speed_mb_per_sec': 100,
        'max_file_size_mb': 10,
    },
    'cpu_utilization': {
        'normal_operation_percent': 70,
        'peak_operation_percent': 90,
        'efficiency_threshold': 80,  # percentage of time doing useful work
    },
    'scalability': {
        'linear_scaling_workers': 4,  # Up to this many workers
        'scalability_efficiency': 80,  # percentage of theoretical maximum
    },
}


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    test_name: str
    metric_value: float
    target_value: float
    unit: str
    passed: bool
    details: dict[str, Any] = None


class PerformanceBenchmarkSuite:
    """Comprehensive performance benchmark suite."""

    def __init__(self):
        self.results: list[BenchmarkResult] = []
        self.test_data_dir = None

    def setup_test_data(self, num_files: int = 1000, file_size_kb: int = 10):
        """Create test data for benchmarking."""
        self.test_data_dir = tempfile.mkdtemp(prefix="phase2_bench_")

        # Create test Python files
        test_content = '''
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Union
import json
import logging

class TestComponent:
    """Test component for benchmarking."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.data: List[str] = []

    def process_data(self, input_data: List[str]) -> Dict[str, Any]:
        """Process input data and return results."""
        self.data.extend(input_data)
        return {
            "processed_count": len(input_data),
            "total_count": len(self.data),
            "status": "success"
        }

    def validate_input(self, data: str) -> bool:
        """Validate input data."""
        return isinstance(data, str) and len(data) > 0

def utility_function(param: str, count: int = 1) -> List[str]:
    """Utility function for testing."""
    return [param] * count

# Additional imports for testing
try:
    import numpy as np
    import pandas as pd
except ImportError:
    pass
''' * (file_size_kb // 2)  # Approximate file size

        for i in range(num_files):
            file_path = Path(self.test_data_dir) / f"test_file_{i:05d}.py"
            with open(file_path, 'w') as f:
                f.write(test_content)

        return self.test_data_dir

    def cleanup_test_data(self):
        """Clean up test data directory."""
        if self.test_data_dir and Path(self.test_data_dir).exists():
            shutil.rmtree(self.test_data_dir)

    def benchmark_parallel_processing_throughput(self) -> BenchmarkResult:
        """Benchmark parallel processing throughput."""
        if not self.test_data_dir:
            self.setup_test_data()

        test_files = list(Path(self.test_data_dir).glob("*.py"))
        target = PERFORMANCE_BENCHMARKS['parallel_processing']['files_per_second_per_worker']

        # Test with different worker counts
        best_throughput = 0
        best_workers = 1

        for workers in [1, 2, 4, 6, 8]:
            start_time = time.time()

            with ThreadPoolExecutor(max_workers=workers) as executor:
                # Process files in parallel
                def process_file(file_path):
                    with open(file_path) as f:
                        return ast.parse(f.read())

                list(executor.map(process_file, test_files))

            end_time = time.time()
            elapsed = end_time - start_time
            throughput = len(test_files) / elapsed if elapsed > 0 else 0

            if throughput > best_throughput:
                best_throughput = throughput
                best_workers = workers

        passed = best_throughput >= target
        result = BenchmarkResult(
            test_name="parallel_processing_throughput",
            metric_value=best_throughput,
            target_value=target,
            unit="files/sec",
            passed=passed,
            details={
                "optimal_workers": best_workers,
                "files_processed": len(test_files),
            }
        )

        self.results.append(result)
        return result

    def benchmark_memory_usage(self) -> BenchmarkResult:
        """Benchmark memory usage during processing."""
        if not self.test_data_dir:
            self.setup_test_data(num_files=500)

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        test_files = list(Path(self.test_data_dir).glob("*"))

        # Process files and monitor memory
        peak_memory = initial_memory

        def memory_monitor():
            nonlocal peak_memory
            while True:
                current_memory = process.memory_info().rss / 1024 / 1024
                peak_memory = max(peak_memory, current_memory)
                time.sleep(0.1)

        monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
        monitor_thread.start()

        # Process files
        for file_path in test_files:
            with open(file_path, 'rb') as f:
                data = f.read()
                # Simulate processing
                processed_data = data.upper()

        # Let monitor catch final memory
        time.sleep(0.5)

        memory_increase = peak_memory - initial_memory
        target = PERFORMANCE_BENCHMARKS['memory_management']['per_batch_memory_mb']
        passed = memory_increase <= target

        result = BenchmarkResult(
            test_name="memory_usage",
            metric_value=memory_increase,
            target_value=target,
            unit="MB",
            passed=passed,
            details={
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": peak_memory,
                "files_processed": len(test_files),
            }
        )

        self.results.append(result)
        return result

    def benchmark_disk_io_performance(self) -> BenchmarkResult:
        """Benchmark disk I/O performance."""
        if not self.test_data_dir:
            self.setup_test_data(num_files=200, file_size_kb=50)

        test_files = list(Path(self.test_data_dir).glob("*.py"))
        total_size = sum(f.stat().st_size for f in test_files) / 1024 / 1024  # MB

        # Test read performance
        start_time = time.time()
        for file_path in test_files:
            with open(file_path, 'rb') as f:
                f.read()
        read_time = time.time() - start_time

        # Test write performance (backup simulation)
        backup_dir = tempfile.mkdtemp(prefix="backup_test_")
        start_time = time.time()
        for file_path in test_files:
            backup_path = Path(backup_dir) / file_path.name
            shutil.copy2(file_path, backup_path)
        write_time = time.time() - start_time

        # Calculate throughput
        read_throughput = total_size / read_time if read_time > 0 else 0
        write_throughput = total_size / write_time if write_time > 0 else 0

        target = PERFORMANCE_BENCHMARKS['disk_io']['file_processing_speed_mb_per_sec']
        avg_throughput = (read_throughput + write_throughput) / 2
        passed = avg_throughput >= target

        # Cleanup backup
        shutil.rmtree(backup_dir)

        result = BenchmarkResult(
            test_name="disk_io_performance",
            metric_value=avg_throughput,
            target_value=target,
            unit="MB/sec",
            passed=passed,
            details={
                "read_throughput_mb_per_sec": read_throughput,
                "write_throughput_mb_per_sec": write_throughput,
                "total_size_mb": total_size,
                "files_processed": len(test_files),
            }
        )

        self.results.append(result)
        return result

    def benchmark_scalability(self) -> BenchmarkResult:
        """Benchmark scalability across worker counts."""
        if not self.test_data_dir:
            self.setup_test_data(num_files=800)

        test_files = list(Path(self.test_data_dir).glob("*.py"))
        worker_counts = [1, 2, 4, 6, 8]
        throughputs = []

        for workers in worker_counts:
            start_time = time.time()

            with ProcessPoolExecutor(max_workers=workers) as executor:
                def simple_process(file_path):
                    # Simple processing task
                    return file_path.stat().st_size

                list(executor.map(simple_process, test_files))

            end_time = time.time()
            throughput = len(test_files) / (end_time - start_time)
            throughputs.append(throughput)

        # Calculate scalability efficiency
        # Compare to theoretical maximum (linear scaling)
        baseline_throughput = throughputs[0] if throughputs else 1
        theoretical_max = baseline_throughput * worker_counts[-1]
        actual_max = throughputs[-1] if throughputs else baseline_throughput

        efficiency = (actual_max / theoretical_max * 100) if theoretical_max > 0 else 0
        target = PERFORMANCE_BENCHMARKS['scalability']['scalability_efficiency']
        passed = efficiency >= target

        result = BenchmarkResult(
            test_name="scalability",
            metric_value=efficiency,
            target_value=target,
            unit="%",
            passed=passed,
            details={
                "worker_counts": worker_counts,
                "throughputs": throughputs,
                "baseline_throughput": baseline_throughput,
                "actual_max_throughput": actual_max,
                "theoretical_max_throughput": theoretical_max,
            }
        )

        self.results.append(result)
        return result

    def benchmark_cpu_efficiency(self) -> BenchmarkResult:
        """Benchmark CPU utilization efficiency."""
        if not self.test_data_dir:
            self.setup_test_data(num_files=300)

        process = psutil.Process()
        test_files = list(Path(self.test_data_dir).glob("*.py"))

        # Monitor CPU usage during processing
        cpu_samples = []
        monitoring = True

        def cpu_monitor():
            while monitoring:
                cpu_percent = process.cpu_percent()
                cpu_samples.append(cpu_percent)
                time.sleep(0.1)

        monitor_thread = threading.Thread(target=cpu_monitor, daemon=True)
        monitor_thread.start()

        # Perform CPU-intensive work
        start_time = time.time()
        for file_path in test_files:
            # Simulate processing work
            with open(file_path) as f:
                content = f.read()
                # Some CPU work
                words = content.split()
                word_count = len(words)

        end_time = time.time()
        monitoring = False
        time.sleep(0.2)  # Let monitor finish

        # Calculate efficiency
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        target = PERFORMANCE_BENCHMARKS['cpu_utilization']['efficiency_threshold']

        # Efficiency is how much of the CPU time was productive
        # Simplified: compare to normal operation threshold
        efficiency = min(avg_cpu / target * 100, 100) if target > 0 else 0
        passed = avg_cpu <= PERFORMANCE_BENCHMARKS['cpu_utilization']['normal_operation_percent']

        result = BenchmarkResult(
            test_name="cpu_efficiency",
            metric_value=efficiency,
            target_value=target,
            unit="%",
            passed=passed,
            details={
                "avg_cpu_percent": avg_cpu,
                "peak_cpu_percent": max(cpu_samples) if cpu_samples else 0,
                "processing_time_sec": end_time - start_time,
                "cpu_samples_count": len(cpu_samples),
            }
        )

        self.results.append(result)
        return result

    def run_all_benchmarks(self) -> dict[str, Any]:
        """Run all performance benchmarks."""
        print("Running Phase 2 Performance Benchmarks...")
        print("=" * 60)

        # Setup test data
        self.setup_test_data()

        try:
            # Run all benchmarks
            benchmarks = [
                self.benchmark_parallel_processing_throughput,
                self.benchmark_memory_usage,
                self.benchmark_disk_io_performance,
                self.benchmark_scalability,
                self.benchmark_cpu_efficiency,
            ]

            for benchmark in benchmarks:
                try:
                    result = benchmark()
                    status = "✓ PASS" if result.passed else "✗ FAIL"
                    print(f"{result.test_name:<30}: {status} ({result.metric_value:.1f}/{result.target_value} {result.unit})")
                except Exception as e:
                    print(f"Error running {benchmark.__name__}: {e}")

            # Generate summary
            passed_count = sum(1 for r in self.results if r.passed)
            total_count = len(self.results)
            overall_pass = passed_count == total_count

            print("\n" + "=" * 60)
            print("BENCHMARK SUMMARY")
            print("=" * 60)
            print(f"Total Benchmarks: {total_count}")
            print(f"Passed: {passed_count}")
            print(f"Failed: {total_count - passed_count}")
            print(f"Success Rate: {passed_count/total_count*100:.1f}%")
            print(f"Overall Status: {'PASS' if overall_pass else 'FAIL'}")

            return {
                'overall_pass': overall_pass,
                'passed_count': passed_count,
                'total_count': total_count,
                'success_rate': passed_count/total_count*100,
                'results': [
                    {
                        'test_name': r.test_name,
                        'metric_value': r.metric_value,
                        'target_value': r.target_value,
                        'unit': r.unit,
                        'passed': r.passed,
                        'details': r.details,
                    }
                    for r in self.results
                ]
            }

        finally:
            # Cleanup
            self.cleanup_test_data()


class TestPerformanceBenchmarks(unittest.TestCase):
    """Unit tests for performance benchmarks."""

    def setUp(self):
        """Set up benchmark suite."""
        self.benchmark_suite = PerformanceBenchmarkSuite()

    def test_parallel_processing_throughput(self):
        """Test parallel processing throughput benchmark."""
        result = self.benchmark_suite.benchmark_parallel_processing_throughput()
        self.assertIsInstance(result, BenchmarkResult)
        self.assertIsNotNone(result.metric_value)
        self.assertIsNotNone(result.target_value)

    def test_memory_usage_benchmark(self):
        """Test memory usage benchmark."""
        result = self.benchmark_suite.benchmark_memory_usage()
        self.assertIsInstance(result, BenchmarkResult)
        self.assertGreaterEqual(result.metric_value, 0)

    def test_disk_io_benchmark(self):
        """Test disk I/O benchmark."""
        result = self.benchmark_suite.benchmark_disk_io_performance()
        self.assertIsInstance(result, BenchmarkResult)
        self.assertGreater(result.metric_value, 0)

    def test_scalability_benchmark(self):
        """Test scalability benchmark."""
        result = self.benchmark_suite.benchmark_scalability()
        self.assertIsInstance(result, BenchmarkResult)
        self.assertIn('worker_counts', result.details)
        self.assertIn('throughputs', result.details)

    def test_cpu_efficiency_benchmark(self):
        """Test CPU efficiency benchmark."""
        result = self.benchmark_suite.benchmark_cpu_efficiency()
        self.assertIsInstance(result, BenchmarkResult)
        self.assertGreaterEqual(result.metric_value, 0)
        self.assertLessEqual(result.metric_value, 100)


def main():
    """Run performance benchmarks and save results."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Phase 2 Performance Benchmarks")
    parser.add_argument("--output", "-o", help="Output file for results (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Run benchmarks
    suite = PerformanceBenchmarkSuite()
    results = suite.run_all_benchmarks()

    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")

    # Exit with appropriate code
    return 0 if results['overall_pass'] else 1


if __name__ == '__main__':
    import ast
    import sys
    sys.exit(main())
