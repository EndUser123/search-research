#!/usr/bin/env python3
"""Demonstration of cache hit performance"""

import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from chat_history_search import ChatHistorySearcher


def main():
    print("🚀 CHS Multi-Level Cache Performance Demo")
    print("=" * 50)

    # Initialize searcher with caching enabled
    searcher = ChatHistorySearcher(enable_rag=False)

    if not searcher.enable_caching:
        print("❌ Cache system not available")
        return

    print("✅ Cache system initialized")
    print(f"📊 Cache directory: {searcher.cache.cache_dir}")
    print(f"🆔 Session ID: {searcher.cache.session_id}")
    print()

    # Test query
    test_query = "error"
    filters = {
        "session_filter": "all",
        "context_filter": "all",
        "rank_by": "relevance",
        "limit": 5
    }

    print(f"🔍 Testing search for: '{test_query}'")
    print()

    # First search (cache miss)
    print("📈 Search #1 (Expected cache miss)")
    start_time = time.time()
    results1 = searcher.search(test_query, **filters)
    first_duration = time.time() - start_time
    print(f"⏱️  Duration: {first_duration:.3f}s")
    print(f"📋 Results: {len(results1)} items")
    print(f"💾 Cached: {results1[0].get('cached', False) if results1 else 'N/A'}")
    print()

    # Check cache stats
    stats = searcher.get_cache_stats()
    perf_stats = stats.get("performance_stats", {})
    hit_rates = stats.get("hit_rates", {})

    print("📊 Cache Statistics After Search #1:")
    print(f"   Total Requests: {perf_stats.get('total_requests', 0)}")
    print(f"   Cache Misses: {perf_stats.get('total_misses', 0)}")
    print(f"   Overall Hit Rate: {hit_rates.get('overall', 0):.1%}")
    print(f"   L1 (Memory) Hits: {perf_stats.get('l1_hits', 0)}")
    print(f"   L2 (Session) Hits: {perf_stats.get('l2_hits', 0)}")
    print(f"   L3 (Persistent) Hits: {perf_stats.get('l3_hits', 0)}")
    print()

    # Second search (cache hit)
    print("🎯 Search #2 (Expected cache hit)")
    start_time = time.time()
    results2 = searcher.search(test_query, **filters)
    second_duration = time.time() - start_time
    print(f"⏱️  Duration: {second_duration:.3f}s")
    print(f"📋 Results: {len(results2)} items")
    print(f"💾 Cached: {results2[0].get('cached', False) if results2 else 'N/A'}")
    print()

    # Check final cache stats
    stats = searcher.get_cache_stats()
    perf_stats = stats.get("performance_stats", {})
    hit_rates = stats.get("hit_rates", {})

    print("📊 Final Cache Statistics:")
    print(f"   Total Requests: {perf_stats.get('total_requests', 0)}")
    print(f"   Cache Misses: {perf_stats.get('total_misses', 0)}")
    print(f"   Overall Hit Rate: {hit_rates.get('overall', 0):.1%}")
    print(f"   L1 (Memory) Hits: {perf_stats.get('l1_hits', 0)}")
    print(f"   L2 (Session) Hits: {perf_stats.get('l2_hits', 0)}")
    print(f"   L3 (Persistent) Hits: {perf_stats.get('l3_hits', 0)}")
    print()

    # Performance improvement
    if first_duration > 0:
        improvement = ((first_duration - second_duration) / first_duration) * 100
        speedup = first_duration / second_duration if second_duration > 0 else float('inf')

        print("🚀 Performance Improvement:")
        print(f"   Time Reduction: {improvement:.1f}%")
        print(f"   Speedup Factor: {speedup:.1f}x")
        print()

    # Cache level details
    levels = stats.get("levels", {})
    print("🏗️ Cache Level Details:")
    for level_name, level_stats in levels.items():
        if isinstance(level_stats, dict):
            print(f"   {level_name}:")
            print(f"     Type: {level_stats.get('type', 'Unknown')}")
            print(f"     Size: {level_stats.get('size', 0)}/{level_stats.get('max_size', 0)}")
            print(f"     Utilization: {level_stats.get('utilization', 0):.1%}")
            print(f"     Total Hits: {level_stats.get('total_hits', 0)}")
    print()

    print("✅ Cache demonstration completed successfully!")

if __name__ == "__main__":
    main()
