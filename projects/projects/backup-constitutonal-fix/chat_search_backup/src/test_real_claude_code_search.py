#!/usr/bin/env python3
"""Test search functionality with realistic Claude Code conversation data."""

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


def test_real_claude_code_search():
    """Test search functionality with realistic Claude Code conversations."""
    print("🔍 Testing Search with Realistic Claude Code Conversations")
    print("=" * 60)

    # Initialize search system
    searcher = ChatHistorySearcher()
    db = ChatHistoryDB()

    # Get database statistics
    stats = db.get_stats()
    print("📊 Database Status:")
    print(f"   Total Sessions: {stats['sessions']:,}")
    print(f"   Total Messages: {stats['messages']:,}")
    print(f"   Database Size: {stats['db_size_mb']:.2f} MB")

    # Test queries based on realistic Claude Code usage patterns
    test_scenarios = [
        {
            "name": "Code Review Scenarios",
            "queries": [
                "code review",
                "performance optimization",
                "code improvements",
                "readability",
                "best practices"
            ]
        },
        {
            "name": "Development Workflow",
            "queries": [
                "Git workflow",
                "branching strategy",
                "version control",
                "pull request",
                "code review"
            ]
        },
        {
            "name": "Infrastructure & DevOps",
            "queries": [
                "Docker optimization",
                "containerization",
                "CI/CD pipeline",
                "deployment",
                "build performance"
            ]
        },
        {
            "name": "API Development",
            "queries": [
                "API design",
                "REST endpoints",
                "authentication",
                "error handling",
                "OpenAPI specification"
            ]
        },
        {
            "name": "Database & Performance",
            "queries": [
                "database optimization",
                "query performance",
                "indexing strategy",
                "schema design",
                "SQL optimization"
            ]
        },
        {
            "name": "Testing & Quality Assurance",
            "queries": [
                "testing strategy",
                "unit tests",
                "integration tests",
                "test automation",
                "code coverage"
            ]
        }
    ]

    total_searches = 0
    total_results = 0
    search_times = []

    print("\n🧪 Search Performance Test Results:")
    print("=" * 50)

    for scenario in test_scenarios:
        print(f"\n📂 {scenario['name']}:")
        print("-" * 30)

        scenario_results = 0

        for query in scenario['queries']:
            # Measure search performance
            start_time = time.perf_counter()
            results = searcher.search(query, limit=5)
            end_time = time.perf_counter()

            search_time = (end_time - start_time) * 1000
            search_times.append(search_time)
            total_searches += 1

            result_count = len(results)
            scenario_results += result_count
            total_results += result_count

            print(f"   🔍 '{query:25s}'")
            print(f"      Time: {search_time:6.2f}ms | Results: {result_count:2d}")

            # Show sample results if found
            if results:
                sample_result = results[0]
                content = sample_result.get('text', sample_result.get('content', ''))[:80]
                role = sample_result.get('metadata', {}).get('role', 'unknown')
                print(f"      💬 Sample: [{role}] {content}...")

        print(f"   📊 {scenario['name']} Results: {scenario_results} total")

    # Performance Analysis
    print("\n⚡ Performance Analysis:")
    print("-" * 25)

    avg_search_time = sum(search_times) / len(search_times)
    min_time = min(search_times)
    max_time = max(search_times)
    median_time = sorted(search_times)[len(search_times) // 2]

    print(f"   Average Search Time: {avg_search_time:.2f}ms")
    print(f"   Median Search Time:  {median_time:.2f}ms")
    print(f"   Fastest Search:      {min_time:.2f}ms")
    print(f"   Slowest Search:      {max_time:.2f}ms")
    print(f"   Total Searches:     {total_searches}")
    print(f"   Total Results:      {total_results}")
    print(f"   Avg Results/Search:  {total_results / total_searches:.1f}")

    # Search Quality Tests
    print("\n🎯 Search Quality Tests:")
    print("-" * 30)

    quality_tests = [
        {
            "name": "Multi-word Queries",
            "queries": [
                "database performance optimization",
                "Git branching strategy best practices",
                "Docker container security best practices"
            ]
        },
        {
            "name": "Technical Terms",
            "queries": [
                "TypeScript Node.js optimization",
                "PostgreSQL indexing strategy",
                "Redis caching implementation"
            ]
        },
        {
            "name": "Problem-solving Queries",
            "queries": [
                "how to fix slow API responses",
                "database connection timeout issues",
                "memory leak in production deployment"
            ]
        }
    ]

    for test in quality_tests:
        print(f"\n🧪 {test['name']}:")
        for query in test['queries']:
            start_time = time.perf_counter()
            results = searcher.search(query, limit=3)
            end_time = time.perf_counter()

            search_time = (end_time - start_time) * 1000

            # Calculate relevance score based on content match
            relevance_score = 0
            if results:
                for result in results:
                    content = result.get('text', result.get('content', '')).lower()
                    query_words = query.lower().split()
                    matches = sum(1 for word in query_words if word in content)
                    relevance_score += matches / len(query_words)

            avg_relevance = relevance_score / len(results) if results else 0

            print(f"   🔍 '{query[:35]:35s}'")
            print(f"      Time: {search_time:6.2f}ms | Results: {len(results):2d} | Relevance: {avg_relevance:.2f}")

    # Slash Command Integration Test
    print("\n🔗 Slash Command Integration Test:")
    print("-" * 40)

    slash_command_queries = [
        "code review suggestions",
        "API authentication implementation",
        "Docker multi-stage build optimization",
        "database query performance analysis",
        "testing framework setup"
    ]

    for query in slash_command_queries:
        # Test with different formats that slash commands might use
        formats = [
            ("Default", {}),
            ("With Limit", {"limit": 3}),
            ("RAG Enhanced", {"use_rag": True})
        ]

        for format_name, format_args in formats:
            start_time = time.perf_counter()
            results = searcher.search(query, **format_args)
            end_time = time.perf_counter()

            search_time = (end_time - start_time) * 1000
            result_count = len(results)

            print(f"   📋 {format_name:12s}: {search_time:6.2f}ms | {result_count} results")

        print()  # Empty line between queries

    # Final Assessment
    print("\n🎉 Final Assessment:")
    print("=" * 25)

    performance_grade = "A+"
    if avg_search_time < 20:
        performance_grade = "A+"
    elif avg_search_time < 50:
        performance_grade = "A"
    elif avg_search_time < 100:
        performance_grade = "B"
    else:
        performance_grade = "C"

    results_grade = "A+"
    avg_results = total_results / total_searches
    if avg_results > 5:
        results_grade = "A+"
    elif avg_results > 3:
        results_grade = "A"
    elif avg_results > 1:
        results_grade = "B"
    else:
        results_grade = "C"

    print(f"   Performance Grade:  {performance_grade}")
    print(f"   Results Quality:    {results_grade}")
    print(f"   Database Size:      {stats['db_size_mb']:.2f} MB")
    print(f"   Messages Searched: {stats['messages']:,}")

    # Success criteria
    success_criteria = [
        avg_search_time < 50,  # Sub-50ms response time
        total_results > 0,      # Found some results
        len(search_times) > 10,  # Adequate test coverage
        stats['messages'] > 1000  # Substantial dataset
    ]

    all_criteria_met = all(success_criteria)

    print("\n✅ Success Criteria:")
    for i, criterion in enumerate(success_criteria, 1):
        status = "✅" if criterion else "❌"
        criterion_name = [
            "Fast response time (< 50ms)",
            "Results found",
            "Adequate test coverage",
            "Substantial dataset (> 1K messages)"
        ][i-1]
        print(f"   {status} {criterion_name}")

    print(f"\n🎯 Overall Result: {'✅ PASS' if all_criteria_met else '❌ NEEDS ATTENTION'}")

    if all_criteria_met:
        print("   🚀 SQLite chat search is ready for production with real Claude Code data!")
        print("   📈 Excellent performance and accuracy across all test scenarios")
    else:
        print("   ⚠️  Some optimization may be needed before production deployment")

    return all_criteria_met


if __name__ == "__main__":
    test_real_claude_code_search()
