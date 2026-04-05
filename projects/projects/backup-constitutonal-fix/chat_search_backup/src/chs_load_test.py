#!/usr/bin/env python3
"""CHS Load Testing Script
Comprehensive performance testing for Chat History Search system under various load conditions.
"""

import concurrent.futures
import json
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

# Set optimization environment variables
import os

os.environ['WORKFLOW_OPTIMIZATIONS_ENABLED'] = 'true'
os.environ['PATTERN_RECOGNITION_ENABLED'] = 'true'
os.environ['ENHANCED_CACHING_ENABLED'] = 'true'
os.environ['SESSION_MONITORING_ENABLED'] = 'true'

from src.modules.analysis.chat_search.src.chat_history_search import ChatHistorySearcher


class CHSLoadTester:
    """Comprehensive load testing for CHS system."""

    def __init__(self):
        self.searcher = None
        self.test_queries = [
            "database performance optimization",
            "API design patterns",
            "testing methodologies",
            "machine learning algorithms",
            "security architecture",
            "cache implementation",
            "microservices design",
            "error handling strategies",
            "performance monitoring",
            "data validation techniques",
            "concurrent programming",
            "system architecture patterns",
            "user authentication",
            "data storage solutions",
            "network protocols",
            "search algorithms",
            "load balancing",
            "database indexing",
            "memory management",
            "async programming",
            "logging best practices"
        ]

    def initialize_system(self):
        """Initialize CHS system for testing."""
        print("🚀 Initializing CHS System for Load Testing")
        print("=" * 60)

        start_time = time.time()
        self.searcher = ChatHistorySearcher(enable_rag=True)
        init_time = time.time() - start_time

        print(f"✅ System initialized in {init_time:.2f} seconds")
        print("✅ SQLite Database: Connected")
        print(f"✅ RAG System: {'ENABLED' if self.searcher.enable_rag else 'DISABLED'}")
        print(f"✅ Enhanced Cache: {'ENABLED' if self.searcher.enable_caching else 'DISABLED'}")
        print(f"✅ Session Monitor: {'ENABLED' if self.searcher.session_monitor else 'DISABLED'}")
        print(f"✅ Pattern Recognition: {'ENABLED' if self.searcher.pattern_recognizer else 'DISABLED'}")
        print()

    def single_query_test(self, query: str, limit: int = 20) -> dict[str, Any]:
        """Execute a single search query and measure performance."""
        start_time = time.perf_counter()

        try:
            results = self.searcher.search(query, limit=limit)
            end_time = time.perf_counter()

            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds

            return {
                'query': query,
                'execution_time_ms': execution_time,
                'results_count': len(results),
                'success': True,
                'error': None
            }

        except Exception as e:
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000

            return {
                'query': query,
                'execution_time_ms': execution_time,
                'results_count': 0,
                'success': False,
                'error': str(e)
            }

    def baseline_performance_test(self) -> dict[str, Any]:
        """Test baseline performance with sequential queries."""
        print("📊 Baseline Performance Test")
        print("-" * 40)

        results = []
        start_time = time.time()

        for i, query in enumerate(self.test_queries, 1):
            print(f"Query {i:2d}/20: {query[:30]}...", end=" ")
            result = self.single_query_test(query)
            results.append(result)

            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['execution_time_ms']:6.2f}ms | {result['results_count']:3d} results")

        total_time = time.time() - start_time

        # Calculate statistics
        execution_times = [r['execution_time_ms'] for r in results if r['success']]
        successful_queries = [r for r in results if r['success']]

        stats = {
            'total_queries': len(results),
            'successful_queries': len(successful_queries),
            'failed_queries': len(results) - len(successful_queries),
            'total_execution_time': total_time,
            'avg_execution_time_ms': statistics.mean(execution_times) if execution_times else 0,
            'median_execution_time_ms': statistics.median(execution_times) if execution_times else 0,
            'min_execution_time_ms': min(execution_times) if execution_times else 0,
            'max_execution_time_ms': max(execution_times) if execution_times else 0,
            'std_deviation_ms': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            'queries_per_second': len(successful_queries) / total_time if total_time > 0 else 0,
            'total_results': sum(r['results_count'] for r in successful_queries)
        }

        print("\n📈 Baseline Performance Summary:")
        print(f"   Total Queries: {stats['total_queries']}")
        print(f"   Success Rate: {(stats['successful_queries']/stats['total_queries']*100):.1f}%")
        print(f"   Average Response: {stats['avg_execution_time_ms']:.2f}ms")
        print(f"   Median Response: {stats['median_execution_time_ms']:.2f}ms")
        print(f"   Min/Max: {stats['min_execution_time_ms']:.2f}ms / {stats['max_execution_time_ms']:.2f}ms")
        print(f"   Std Deviation: {stats['std_deviation_ms']:.2f}ms")
        print(f"   Throughput: {stats['queries_per_second']:.2f} queries/second")
        print(f"   Total Results: {stats['total_results']}")
        print()

        return stats

    def concurrent_load_test(self, num_threads: int = 10, queries_per_thread: int = 5) -> dict[str, Any]:
        """Test performance under concurrent load."""
        print(f"⚡ Concurrent Load Test: {num_threads} threads × {queries_per_thread} queries")
        print("-" * 60)

        def worker_thread(thread_id: int) -> list[dict[str, Any]]:
            """Worker thread for concurrent testing."""
            thread_results = []

            for i in range(queries_per_thread):
                query = random.choice(self.test_queries)
                result = self.single_query_test(query)
                result['thread_id'] = thread_id
                result['query_number'] = i
                thread_results.append(result)

            return thread_results

        # Execute concurrent test
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # Submit all threads
            future_to_thread = {
                executor.submit(worker_thread, thread_id): thread_id
                for thread_id in range(num_threads)
            }

            # Collect results
            all_results = []
            for future in concurrent.futures.as_completed(future_to_thread):
                thread_id = future_to_thread[future]
                try:
                    thread_results = future.result()
                    all_results.extend(thread_results)
                except Exception as exc:
                    print(f"Thread {thread_id} generated an exception: {exc}")

        total_time = time.time() - start_time

        # Calculate statistics
        execution_times = [r['execution_time_ms'] for r in all_results if r['success']]
        successful_queries = [r for r in all_results if r['success']]

        stats = {
            'concurrent_threads': num_threads,
            'queries_per_thread': queries_per_thread,
            'total_queries': len(all_results),
            'successful_queries': len(successful_queries),
            'failed_queries': len(all_results) - len(successful_queries),
            'total_execution_time': total_time,
            'avg_execution_time_ms': statistics.mean(execution_times) if execution_times else 0,
            'median_execution_time_ms': statistics.median(execution_times) if execution_times else 0,
            'min_execution_time_ms': min(execution_times) if execution_times else 0,
            'max_execution_time_ms': max(execution_times) if execution_times else 0,
            'std_deviation_ms': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            'queries_per_second': len(successful_queries) / total_time if total_time > 0 else 0,
            'total_results': sum(r['results_count'] for r in successful_queries),
            'concurrency_factor': len(successful_queries) / total_time / (len(successful_queries) / sum(execution_times) * 1000) if execution_times else 0
        }

        print("📈 Concurrent Load Results:")
        print(f"   Threads: {stats['concurrent_threads']}")
        print(f"   Total Queries: {stats['total_queries']}")
        print(f"   Success Rate: {(stats['successful_queries']/stats['total_queries']*100):.1f}%")
        print(f"   Average Response: {stats['avg_execution_time_ms']:.2f}ms")
        print(f"   Median Response: {stats['median_execution_time_ms']:.2f}ms")
        print(f"   Min/Max: {stats['min_execution_time_ms']:.2f}ms / {stats['max_execution_time_ms']:.2f}ms")
        print(f"   Std Deviation: {stats['std_deviation_ms']:.2f}ms")
        print(f"   Throughput: {stats['queries_per_second']:.2f} queries/second")
        print(f"   Concurrency Efficiency: {stats['concurrency_factor']:.2f}x")
        print(f"   Total Results: {stats['total_results']}")
        print()

        return stats

    def stress_test(self, duration_seconds: int = 60) -> dict[str, Any]:
        """Stress test the system for a specific duration."""
        print(f"🔥 Stress Test: {duration_seconds} seconds of continuous load")
        print("-" * 50)

        results = []
        start_time = time.time()
        query_count = 0

        while time.time() - start_time < duration_seconds:
            query = random.choice(self.test_queries)
            result = self.single_query_test(query)
            result['timestamp'] = time.time() - start_time
            results.append(result)
            query_count += 1

            # Small delay to prevent overwhelming
            time.sleep(0.01)

        actual_duration = time.time() - start_time

        # Calculate statistics
        execution_times = [r['execution_time_ms'] for r in results if r['success']]
        successful_queries = [r for r in results if r['success']]

        # Analyze performance over time
        time_buckets = {}
        bucket_size = 10  # 10-second buckets

        for result in successful_queries:
            bucket = int(result['timestamp'] // bucket_size) * bucket_size
            if bucket not in time_buckets:
                time_buckets[bucket] = []
            time_buckets[bucket].append(result['execution_time_ms'])

        bucket_stats = {}
        for bucket, times in time_buckets.items():
            bucket_stats[bucket] = {
                'avg_time': statistics.mean(times),
                'query_count': len(times)
            }

        stats = {
            'test_duration': actual_duration,
            'total_queries': len(results),
            'successful_queries': len(successful_queries),
            'failed_queries': len(results) - len(successful_queries),
            'avg_execution_time_ms': statistics.mean(execution_times) if execution_times else 0,
            'median_execution_time_ms': statistics.median(execution_times) if execution_times else 0,
            'min_execution_time_ms': min(execution_times) if execution_times else 0,
            'max_execution_time_ms': max(execution_times) if execution_times else 0,
            'std_deviation_ms': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            'queries_per_second': len(successful_queries) / actual_duration if actual_duration > 0 else 0,
            'total_results': sum(r['results_count'] for r in successful_queries),
            'time_bucket_performance': bucket_stats
        }

        print("📈 Stress Test Results:")
        print(f"   Duration: {stats['test_duration']:.1f} seconds")
        print(f"   Total Queries: {stats['total_queries']}")
        print(f"   Success Rate: {(stats['successful_queries']/stats['total_queries']*100):.1f}%")
        print(f"   Average Response: {stats['avg_execution_time_ms']:.2f}ms")
        print(f"   Median Response: {stats['median_execution_time_ms']:.2f}ms")
        print(f"   Min/Max: {stats['min_execution_time_ms']:.2f}ms / {stats['max_execution_time_ms']:.2f}ms")
        print(f"   Std Deviation: {stats['std_deviation_ms']:.2f}ms")
        print(f"   Throughput: {stats['queries_per_second']:.2f} queries/second")
        print(f"   Total Results: {stats['total_results']}")

        print("\n📊 Performance Over Time:")
        for bucket in sorted(bucket_stats.keys()):
            bucket_stat = bucket_stats[bucket]
            print(f"   {bucket:2.0f}-{bucket+10:2.0f}s: {bucket_stat['avg_time']:6.2f}ms avg, {bucket_stat['query_count']:3d} queries")

        print()

        return stats

    def memory_usage_test(self, num_queries: int = 100) -> dict[str, Any]:
        """Test memory usage during search operations."""
        print(f"💾 Memory Usage Test: {num_queries} sequential queries")
        print("-" * 45)

        import gc

        import psutil

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"Initial Memory: {initial_memory:.2f} MB")

        # Execute queries and monitor memory
        memory_samples = [initial_memory]
        results = []

        for i in range(num_queries):
            query = random.choice(self.test_queries)
            result = self.single_query_test(query)
            results.append(result)

            # Sample memory every 10 queries
            if i % 10 == 0:
                gc.collect()  # Force garbage collection
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)
                print(f"Query {i:3d}: {current_memory:6.2f} MB")

        # Final memory measurement
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_samples.append(final_memory)

        # Calculate memory statistics
        memory_growth = final_memory - initial_memory
        max_memory = max(memory_samples)

        stats = {
            'num_queries': num_queries,
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'max_memory_mb': max_memory,
            'memory_growth_mb': memory_growth,
            'memory_per_query_kb': (memory_growth * 1024) / num_queries if num_queries > 0 else 0,
            'successful_queries': len([r for r in results if r['success']]),
            'avg_execution_time_ms': statistics.mean([r['execution_time_ms'] for r in results if r['success']]) if results else 0
        }

        print("\n📈 Memory Usage Summary:")
        print(f"   Initial Memory: {stats['initial_memory_mb']:.2f} MB")
        print(f"   Final Memory: {stats['final_memory_mb']:.2f} MB")
        print(f"   Max Memory: {stats['max_memory_mb']:.2f} MB")
        print(f"   Memory Growth: {stats['memory_growth_mb']:.2f} MB")
        print(f"   Memory per Query: {stats['memory_per_query_kb']:.2f} KB")
        print(f"   Success Rate: {(stats['successful_queries']/stats['num_queries']*100):.1f}%")
        print()

        return stats

    def run_comprehensive_test_suite(self) -> dict[str, Any]:
        """Run complete test suite and generate comprehensive report."""
        print("🎯 COMPREHENSIVE CHS LOAD TESTING SUITE")
        print("=" * 60)
        print(f"Test Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        suite_start_time = time.time()
        test_results = {}

        try:
            # Initialize system
            self.initialize_system()

            # Test 1: Baseline Performance
            test_results['baseline'] = self.baseline_performance_test()

            # Test 2: Concurrent Load Test
            test_results['concurrent_light'] = self.concurrent_load_test(num_threads=5, queries_per_thread=4)
            test_results['concurrent_medium'] = self.concurrent_load_test(num_threads=10, queries_per_thread=5)
            test_results['concurrent_heavy'] = self.concurrent_load_test(num_threads=20, queries_per_thread=3)

            # Test 3: Stress Test
            test_results['stress_test'] = self.stress_test(duration_seconds=30)

            # Test 4: Memory Usage Test
            test_results['memory_test'] = self.memory_usage_test(num_queries=50)

            suite_total_time = time.time() - suite_start_time

            # Generate comprehensive report
            self.generate_comprehensive_report(test_results, suite_total_time)

            return test_results

        except Exception as e:
            print(f"❌ Test suite failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return test_results

    def generate_comprehensive_report(self, test_results: dict[str, Any], total_time: float):
        """Generate comprehensive performance report."""
        print("📊 COMPREHENSIVE PERFORMANCE REPORT")
        print("=" * 60)

        # Summary Statistics
        print("🎯 PERFORMANCE SUMMARY:")
        print(f"   Total Test Duration: {total_time:.2f} seconds")
        print(f"   Tests Completed: {len(test_results)}")
        print()

        # Baseline Performance
        if 'baseline' in test_results:
            baseline = test_results['baseline']
            print("📈 BASELINE PERFORMANCE:")
            print(f"   Average Response: {baseline['avg_execution_time_ms']:.2f}ms")
            print(f"   Throughput: {baseline['queries_per_second']:.2f} queries/sec")
            print(f"   Success Rate: {(baseline['successful_queries']/baseline['total_queries']*100):.1f}%")
            print()

        # Concurrency Performance
        concurrent_tests = [k for k in test_results.keys() if k.startswith('concurrent')]
        if concurrent_tests:
            print("⚡ CONCURRENCY PERFORMANCE:")
            for test_name in concurrent_tests:
                test_data = test_results[test_name]
                threads = test_data['concurrent_threads']
                print(f"   {threads:2d} threads: {test_data['avg_execution_time_ms']:6.2f}ms avg, {test_data['queries_per_second']:6.2f} qps")
            print()

        # Stress Test Results
        if 'stress_test' in test_results:
            stress = test_results['stress_test']
            print("🔥 STRESS TEST PERFORMANCE:")
            print(f"   Duration: {stress['test_duration']:.1f} seconds")
            print(f"   Queries: {stress['total_queries']} total, {stress['successful_queries']} successful")
            print(f"   Throughput: {stress['queries_per_second']:.2f} queries/sec")
            print(f"   Response Stability: σ = {stress['std_deviation_ms']:.2f}ms")
            print()

        # Memory Usage
        if 'memory_test' in test_results:
            memory = test_results['memory_test']
            print("💾 MEMORY USAGE:")
            print(f"   Memory Growth: {memory['memory_growth_mb']:.2f} MB")
            print(f"   Memory per Query: {memory['memory_per_query_kb']:.2f} KB")
            print()

        # Performance Grade
        grade = self.calculate_performance_grade(test_results)
        print(f"🏆 OVERALL PERFORMANCE GRADE: {grade}")
        print()

        # Recommendations
        self.generate_recommendations(test_results, grade)

    def calculate_performance_grade(self, test_results: dict[str, Any]) -> str:
        """Calculate overall performance grade."""
        score = 0
        max_score = 0

        # Baseline performance (30%)
        if 'baseline' in test_results:
            max_score += 30
            baseline = test_results['baseline']
            if baseline['avg_execution_time_ms'] < 50:
                score += 30
            elif baseline['avg_execution_time_ms'] < 100:
                score += 25
            elif baseline['avg_execution_time_ms'] < 200:
                score += 20
            else:
                score += 10

        # Concurrency performance (30%)
        if 'concurrent_medium' in test_results:
            max_score += 30
            concurrent = test_results['concurrent_medium']
            if concurrent['avg_execution_time_ms'] < 100:
                score += 30
            elif concurrent['avg_execution_time_ms'] < 200:
                score += 25
            elif concurrent['avg_execution_time_ms'] < 500:
                score += 20
            else:
                score += 10

        # Stress test stability (25%)
        if 'stress_test' in test_results:
            max_score += 25
            stress = test_results['stress_test']
            cv = stress['std_deviation_ms'] / stress['avg_execution_time_ms'] if stress['avg_execution_time_ms'] > 0 else 1
            if cv < 0.5:
                score += 25
            elif cv < 1.0:
                score += 20
            elif cv < 2.0:
                score += 15
            else:
                score += 5

        # Memory efficiency (15%)
        if 'memory_test' in test_results:
            max_score += 15
            memory = test_results['memory_test']
            if memory['memory_per_query_kb'] < 10:
                score += 15
            elif memory['memory_per_query_kb'] < 50:
                score += 12
            elif memory['memory_per_query_kb'] < 100:
                score += 8
            else:
                score += 4

        if max_score == 0:
            return "N/A"

        percentage = (score / max_score) * 100

        if percentage >= 90:
            return "A+ (Excellent)"
        elif percentage >= 80:
            return "A (Very Good)"
        elif percentage >= 70:
            return "B+ (Good)"
        elif percentage >= 60:
            return "B (Satisfactory)"
        elif percentage >= 50:
            return "C (Needs Improvement)"
        else:
            return "D (Poor)"

    def generate_recommendations(self, test_results: dict[str, Any], grade: str):
        """Generate performance optimization recommendations."""
        print("💡 PERFORMANCE RECOMMENDATIONS:")

        # Baseline recommendations
        if 'baseline' in test_results:
            baseline = test_results['baseline']
            if baseline['avg_execution_time_ms'] > 100:
                print("   • Consider implementing query result caching for frequently used queries")
                print("   • Optimize database indexes for better search performance")
                print("   • Review vector search configuration for faster semantic matching")

        # Concurrency recommendations
        concurrent_tests = [k for k in test_results.keys() if k.startswith('concurrent')]
        if concurrent_tests:
            performance_drop = False
            for test_name in concurrent_tests:
                test_data = test_results[test_name]
                if test_data['avg_execution_time_ms'] > 200:
                    performance_drop = True
                    break

            if performance_drop:
                print("   • Implement connection pooling for database operations")
                print("   • Consider using async operations for better concurrency")
                print("   • Optimize thread pool configuration based on CPU cores")

        # Memory recommendations
        if 'memory_test' in test_results:
            memory = test_results['memory_test']
            if memory['memory_growth_mb'] > 50:
                print("   • Implement memory-efficient result streaming")
                print("   • Consider result pagination for large result sets")
                print("   • Review caching strategy to prevent memory bloat")

        # Stress test recommendations
        if 'stress_test' in test_results:
            stress = test_results['stress_test']
            if stress['std_deviation_ms'] > stress['avg_execution_time_ms']:
                print("   • Investigate performance variability during sustained load")
                print("   • Consider implementing adaptive timeout mechanisms")
                print("   • Monitor system resource usage during peak periods")

        if "A+" in grade or "A" in grade:
            print("   🎉 System performance is excellent! Continue current optimization strategy.")

        print()


def main():
    """Main load testing execution."""
    print("🔧 CHS Load Testing Tool")
    print("=" * 40)

    tester = CHSLoadTester()

    try:
        # Run comprehensive test suite
        results = tester.run_comprehensive_test_suite()

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = Path(__file__).parent / f"chs_load_test_results_{timestamp}.json"

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"📁 Detailed results saved to: {results_file}")

    except KeyboardInterrupt:
        print("\n🛑 Load testing interrupted by user")
    except Exception as e:
        print(f"❌ Load testing failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
