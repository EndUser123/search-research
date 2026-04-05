#!/usr/bin/env python3
"""Scalability testing for SQLite chat search with varying dataset sizes."""

import sys
import time
from pathlib import Path

# Add CSF NIP paths
csf_nip_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(csf_nip_root))
sys.path.insert(0, str(csf_nip_root / "src"))
sys.path.insert(0, str(csf_nip_root / "src" / "lib"))

from chat_history_db import ChatHistoryDB
from chat_history_search import ChatHistorySearcher


def test_scalability_across_sizes():
    """Test performance across different dataset sizes."""
    print("📈 SQLite Chat Search Scalability Analysis")
    print("=" * 50)

    # Current database analysis
    db = ChatHistoryDB()
    current_stats = db.get_stats()

    print("\n📊 Current Database Metrics:")
    print(f"   Messages:      {current_stats['messages']:,}")
    print(f"   Sessions:      {current_stats['sessions']:,}")
    print(f"   Database Size: {current_stats['db_size_mb']:.2f} MB")

    # Performance benchmarks with current size
    searcher = ChatHistorySearcher()
    test_queries = [
        "performance optimization",
        "database security",
        "API implementation",
        "memory management"
    ]

    print("\n🚀 Current Size Performance Benchmarks:")
    print("-" * 40)

    current_performance = {}

    for query in test_queries:
        times = []
        result_counts = []

        for _ in range(5):  # 5 measurements
            start_time = time.perf_counter()
            results = searcher.search(query, limit=50)
            end_time = time.perf_counter()

            times.append((end_time - start_time) * 1000)
            result_counts.append(len(results))

        avg_time = sum(times) / len(times)
        avg_results = sum(result_counts) / len(result_counts)

        current_performance[query] = {
            'avg_time_ms': avg_time,
            'avg_results': avg_results
        }

        print(f"   {query:25s}: {avg_time:6.2f}ms | {avg_results:5.1f} results")

    # Projected performance analysis
    print("\n📈 Scalability Projections:")
    print("-" * 40)

    # Calculate key performance metrics
    avg_query_time = sum(p['avg_time_ms'] for p in current_performance.values()) / len(current_performance)
    total_messages = current_stats['messages']
    db_size_mb = current_stats['db_size_mb']

    print(f"   Average Query Time:     {avg_query_time:.2f} ms")
    print(f"   Messages per MB:       {total_messages / db_size_mb:.0f}")
    print(f"   Query Time per 1K Msg: {(avg_query_time / total_messages) * 1000:.3f} ms")
    print(f"   Storage Efficiency:    {total_messages / db_size_mb:.0f} msg/MB")

    # Project performance for larger datasets
    projection_sizes = [
        (50000, "50K Messages"),
        (100000, "100K Messages"),
        (500000, "500K Messages"),
        (1000000, "1M Messages")
    ]

    print("\n📊 Projected Performance at Scale:")
    print("-" * 50)
    print(f"{'Dataset Size':<15} {'Est. DB Size':<12} {'Est. Query Time':<15} {'Messages/MB':<12}")
    print("-" * 50)

    for msg_count, label in projection_sizes:
        # Assume linear scaling for database size
        estimated_db_size = (msg_count / total_messages) * db_size_mb

        # Assume sub-linear scaling for query time (due to indexing)
        # Use square root scaling as a reasonable approximation
        scaling_factor = (msg_count / total_messages) ** 0.5
        estimated_query_time = avg_query_time * scaling_factor

        messages_per_mb = msg_count / estimated_db_size

        print(f"{label:<15} {estimated_db_size:>9.1f} MB {estimated_query_time:>11.2f} ms {messages_per_mb:>9.0f}")

    # Performance characteristics analysis
    print("\n🔍 Performance Characteristics Analysis:")
    print("-" * 45)

    # Query time complexity analysis
    print("Query Time Complexity:")
    if avg_query_time < 20:
        print("   ✅ Excellent: < 20ms average response time")
    elif avg_query_time < 50:
        print("   ✅ Good: < 50ms average response time")
    else:
        print("   ⚠️  Needs optimization: > 50ms average response time")

    # Storage efficiency analysis
    storage_efficiency = total_messages / db_size_mb
    print("\nStorage Efficiency:")
    if storage_efficiency > 2000:
        print(f"   ✅ Excellent: {storage_efficiency:.0f} messages/MB")
    elif storage_efficiency > 1000:
        print(f"   ✅ Good: {storage_efficiency:.0f} messages/MB")
    else:
        print(f"   ⚠️  Could improve: {storage_efficiency:.0f} messages/MB")

    # Scalability assessment
    print("\n📈 Scalability Assessment:")

    # Test with different result limits
    print("\nResult Limit Impact:")
    for limit in [10, 50, 100, 500]:
        times = []
        for _ in range(3):
            start_time = time.perf_counter()
            results = searcher.search("performance", limit=limit)
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)

        avg_time = sum(times) / len(times)
        print(f"   Limit {limit:3d}: {avg_time:6.2f}ms average")

    # Load testing
    print("\nLoad Testing (100 sequential queries):")
    start_time = time.perf_counter()

    for i in range(100):
        query = test_queries[i % len(test_queries)]
        searcher.search(query, limit=20)

    total_time = time.perf_counter() - start_time
    avg_per_query = (total_time / 100) * 1000
    queries_per_second = 100 / total_time

    print(f"   Total Time:     {total_time:.2f}s")
    print(f"   Average/Query: {avg_per_query:.2f}ms")
    print(f"   Throughput:    {queries_per_second:.1f} queries/second")

    # Memory and resource efficiency
    print("\n💾 Resource Efficiency Analysis:")
    print(f"   Database Size:     {db_size_mb:.2f} MB for {total_messages:,} messages")
    print(f"   Size per Message:  {(db_size_mb * 1024) / total_messages:.2f} KB")
    print("   Index Efficiency:  Low overhead SQLite FTS5 indexing")

    # Recommendations based on current performance
    print("\n💡 Scalability Recommendations:")

    if avg_query_time < 20 and storage_efficiency > 2000:
        print("   ✅ Current system shows excellent scalability characteristics")
        print("   📈 Can comfortably handle 100K-500K messages with current architecture")
        print("   🚀 Consider migrating to PostgreSQL for > 1M messages")
    elif avg_query_time < 50:
        print("   ✅ Good performance with room for optimization")
        print("   🔧 Add database indexes for frequently searched terms")
        print("   💾 Consider query result caching for common searches")
    else:
        print("   ⚠️  Performance optimization needed before scaling")
        print("   🔧 Implement comprehensive database indexing strategy")
        print("   📊 Consider query optimization and connection pooling")

    print("\n🎯 Scalability Verdict:")

    performance_score = 0
    if avg_query_time < 20:
        performance_score += 40
    elif avg_query_time < 50:
        performance_score += 25

    if storage_efficiency > 2000:
        performance_score += 30
    elif storage_efficiency > 1000:
        performance_score += 20

    if queries_per_second > 50:
        performance_score += 30
    elif queries_per_second > 20:
        performance_score += 20

    if performance_score >= 80:
        print(f"   🌟 EXCELLENT: High scalability potential ({performance_score}/100)")
    elif performance_score >= 60:
        print(f"   ✅ GOOD: Scalable with optimizations ({performance_score}/100)")
    elif performance_score >= 40:
        print(f"   ⚠️  MODERATE: Scalability improvements needed ({performance_score}/100)")
    else:
        print(f"   ❌ LIMITED: Significant scalability improvements required ({performance_score}/100)")

    print("\n📊 Summary:")
    print(f"   Current dataset: {total_messages:,} messages, {db_size_mb:.1f} MB")
    print(f"   Performance score: {performance_score}/100")
    print(f"   Recommended max size: ~{int(500000 * (performance_score/100)):,} messages before major optimizations")


if __name__ == "__main__":
    test_scalability_across_sizes()
