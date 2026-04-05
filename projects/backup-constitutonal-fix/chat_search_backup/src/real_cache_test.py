#!/usr/bin/env python3
"""
Real Chat History Cache Performance Test
Tests CHS caching system with actual user chat history
"""

import json
import statistics
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from chat_history_search import ChatHistorySearcher


def load_real_queries():
    """Load realistic search queries based on common user patterns"""
    return [
        # Error-related queries (high frequency)
        "error",
        "fix error",
        "debug error",
        "permission denied",
        "file not found",

        # Implementation queries
        "implement feature",
        "add function",
        "create new",
        "how to",
        "help with",

        # Code review queries
        "review code",
        "optimize performance",
        "refactor",
        "improve code",

        # Configuration queries
        "config",
        "setup",
        "install",
        "configure",

        # Debugging queries
        "debug",
        "troubleshoot",
        "issue",
        "problem",

        # Git/Version control
        "git commit",
        "git push",
        "merge conflict",
        "branch",

        # Testing queries
        "test",
        "unit test",
        "integration test",
        "run tests",

        # Documentation queries
        "documentation",
        "readme",
        "comment",
        "explain",

        # Performance queries
        "performance",
        "optimize",
        "slow",
        "memory usage",

        # General queries
        "update",
        "delete",
        "modify",
        "change"
    ]

def measure_search_performance(searcher, query, iterations=3):
    """Measure search performance for a specific query"""
    times = []
    cache_hits = 0

    for i in range(iterations):
        start_time = time.time()
        results = searcher.search(query, limit=10)
        duration = time.time() - start_time
        times.append(duration)

        if results and results[0].get('cached', False):
            if i > 0:  # First search might be a miss
                cache_hits += 1

    return {
        'query': query,
        'times': times,
        'avg_time': statistics.mean(times),
        'min_time': min(times),
        'max_time': max(times),
        'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
        'cache_hits': cache_hits,
        'result_count': len(results) if results else 0
    }

def main():
    print("🔬 CHS Cache Performance Test with Real Chat History")
    print("=" * 60)

    # Initialize searcher with RAG disabled for fair caching comparison
    print("🚀 Initializing CHS with multi-level caching...")
    searcher = ChatHistorySearcher(enable_rag=False)

    if not searcher.enable_caching:
        print("❌ Cache system not available - test aborted")
        return

    print("✅ Cache system initialized successfully")
    print(f"📊 Session ID: {searcher.cache.session_id}")
    print(f"📁 Cache Directory: {searcher.cache.cache_dir}")
    print()

    # Load realistic test queries
    test_queries = load_real_queries()
    print(f"📋 Testing {len(test_queries)} realistic search queries")
    print()

    # Performance tracking
    all_results = []
    total_searches = 0
    total_cache_hits = 0

    print("🏃 Running performance tests...")
    print("-" * 40)

    for i, query in enumerate(test_queries, 1):
        print(f"[{i:2d}/{len(test_queries)}] Testing: '{query}'")

        # Measure performance (3 iterations per query)
        perf_data = measure_search_performance(searcher, query, iterations=3)
        all_results.append(perf_data)

        total_searches += len(perf_data['times'])
        total_cache_hits += perf_data['cache_hits']

        # Show per-query results
        print(f"      Avg: {perf_data['avg_time']*1000:.1f}ms")
        print(f"      Min: {perf_data['min_time']*1000:.1f}ms")
        print(f"      Max: {perf_data['max_time']*1000:.1f}ms")
        print(f"      Cache Hits: {perf_data['cache_hits']}/3")
        print(f"      Results: {perf_data['result_count']}")
        print()

    # Analyze overall performance
    print("📊 OVERALL PERFORMANCE ANALYSIS")
    print("=" * 40)

    # Calculate statistics
    all_times = []
    cache_enabled_times = []
    cache_disabled_times = []

    for result in all_results:
        all_times.extend(result['times'])
        # First search (cache miss) vs subsequent searches (cache hits)
        if len(result['times']) >= 1:
            cache_disabled_times.append(result['times'][0])  # First search
        if len(result['times']) >= 2:
            cache_enabled_times.extend(result['times'][1:])  # Subsequent searches

    # Performance metrics
    overall_avg = statistics.mean(all_times) * 1000
    cache_miss_avg = statistics.mean(cache_disabled_times) * 1000
    cache_hit_avg = statistics.mean(cache_enabled_times) * 1000 if cache_enabled_times else 0

    # Speedup calculation
    speedup = cache_miss_avg / cache_hit_avg if cache_hit_avg > 0 else 0
    improvement = ((cache_miss_avg - cache_hit_avg) / cache_miss_avg * 100) if cache_hit_avg > 0 else 0

    print(f"🔍 Total Searches Performed: {total_searches}")
    print(f"💾 Total Cache Hits: {total_cache_hits}")
    print(f"📈 Overall Hit Rate: {(total_cache_hits/(total_searches-len(test_queries)))*100:.1f}%")
    print()

    print("⏱️ TIMING ANALYSIS:")
    print(f"   Overall Average: {overall_avg:.1f}ms")
    print(f"   Cache Miss (first search): {cache_miss_avg:.1f}ms")
    print(f"   Cache Hit (subsequent): {cache_hit_avg:.1f}ms")
    print()

    print("🚀 PERFORMANCE IMPROVEMENT:")
    if speedup > 0:
        print(f"   Speedup Factor: {speedup:.1f}x faster")
        print(f"   Time Reduction: {improvement:.1f}%")
        print(f"   Time Saved: {cache_miss_avg - cache_hit_avg:.1f}ms per query")
    else:
        print("   No cache hits detected (expected for unique queries)")
    print()

    # Cache statistics
    print("📋 CACHE STATISTICS:")
    cache_stats = searcher.get_cache_stats()
    perf_stats = cache_stats.get('performance_stats', {})
    hit_rates = cache_stats.get('hit_rates', {})

    print(f"   Total Cache Requests: {perf_stats.get('total_requests', 0)}")
    print(f"   L1 (Memory) Hits: {perf_stats.get('l1_hits', 0)}")
    print(f"   L2 (Session) Hits: {perf_stats.get('l2_hits', 0)}")
    print(f"   L3 (Persistent) Hits: {perf_stats.get('l3_hits', 0)}")
    print()

    # Cache level breakdown
    levels = cache_stats.get('levels', {})
    print("🏗️ CACHE LEVEL BREAKDOWN:")
    for level_name, level_stats in levels.items():
        if isinstance(level_stats, dict) and 'size' in level_stats:
            utilization = level_stats.get('utilization', 0) * 100
            total_hits = level_stats.get('total_hits', 0)
            print(f"   {level_name}:")
            print(f"     Size: {level_stats.get('size', 0)}/{level_stats.get('max_size', 0)}")
            print(f"     Utilization: {utilization:.1f}%")
            print(f"     Type: {level_stats.get('type', 'Unknown')}")
            print(f"     Hits: {total_hits}")
    print()

    # Performance classification
    print("🎯 PERFORMANCE CLASSIFICATION:")
    if speedup >= 10:
        print("   🏆 EXCELLENT: >10x speedup achieved")
    elif speedup >= 5:
        print("   🥇 VERY GOOD: 5-10x speedup achieved")
    elif speedup >= 2:
        print("   🥈 GOOD: 2-5x speedup achieved")
    elif speedup >= 1.5:
        print("   🥉 MODERATE: 1.5-2x speedup achieved")
    else:
        print("   📊 MINIMAL: <1.5x speedup (queries may be too diverse)")
    print()

    # Health check
    print("🏥 CACHE HEALTH CHECK:")
    health = searcher.cache_health_check()
    status = health.get('overall_status', 'unknown')
    print(f"   Overall Status: {status.upper()}")

    if health.get('issues'):
        print("   Issues:")
        for issue in health['issues']:
            print(f"     - {issue}")

    if health.get('recommendations'):
        print("   Recommendations:")
        for rec in health['recommendations']:
            print(f"     - {rec}")
    print()

    # Save detailed results
    results_file = Path(__file__).parent / "cache_performance_results.json"
    results_data = {
        'test_timestamp': time.time(),
        'test_queries_count': len(test_queries),
        'total_searches': total_searches,
        'cache_hits': total_cache_hits,
        'hit_rate': (total_cache_hits/(total_searches-len(test_queries)))*100 if total_searches > len(test_queries) else 0,
        'performance': {
            'overall_avg_ms': overall_avg,
            'cache_miss_avg_ms': cache_miss_avg,
            'cache_hit_avg_ms': cache_hit_avg,
            'speedup_factor': speedup,
            'improvement_percentage': improvement
        },
        'cache_stats': cache_stats,
        'health_check': health,
        'query_results': all_results[:5]  # First 5 queries as sample
    }

    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"💾 Detailed results saved to: {results_file}")
    print()
    print("✅ Real chat history cache performance test completed!")

if __name__ == "__main__":
    main()
