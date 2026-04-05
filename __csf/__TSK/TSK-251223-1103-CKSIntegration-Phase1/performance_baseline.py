#!/usr/bin/env python
"""
CKS Phase 1 Performance Baseline

Measures search quality improvements from Phase 1 integration.

Run: python performance_baseline.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

try:
    from cks.unified import CKS
    print("✅ CKS imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)


# Test queries covering different scenarios
TEST_QUERIES = [
    ("db timeout", "Abbreviated query"),
    ("cks auth", "Multiple abbreviations"),
    ("api error", "Technical term"),
    ("fix bug", "Common terms"),
    ("database connection", "Full terms"),
    ("test pattern", "General query"),
]


def measure_search_performance(cks: CKS, query: str, use_expansion: bool = False) -> dict:
    """Measure search performance for a single query"""
    start = time.time()

    if use_expansion:
        try:
            results = cks.search_semantic(query, expand_query=True, limit=10)
        except TypeError:
            # Fallback if expand_query not yet integrated
            print("   ⚠️ expand_query not integrated yet, using standard search")
            results = cks.search_semantic(query, limit=10)
    else:
        results = cks.search_semantic(query, limit=10)

    elapsed = time.time() - start

    # Calculate metrics
    avg_score = sum(r.get("final_score", r.get("similarity", 0)) for r in results) / len(results) if results else 0

    return {
        "count": len(results),
        "elapsed": elapsed,
        "avg_score": avg_score,
        "top_score": results[0].get("final_score", results[0].get("similarity", 0)) if results else 0,
    }


def run_baseline():
    """Run performance baseline comparison"""
    print("\n" + "="*70)
    print("CKS Phase 1 Performance Baseline")
    print("="*70)

    cks = CKS()

    print("\nTest Queries:")
    for query, description in TEST_QUERIES:
        print(f"  - '{query}' ({description})")

    print("\n" + "="*70)
    print("BEFORE Phase 1 (Standard Search)")
    print("="*70)

    baseline_results = {}
    for query, description in TEST_QUERIES:
        print(f"\nQuery: '{query}' ({description})")
        metrics = measure_search_performance(cks, query, use_expansion=False)
        baseline_results[query] = metrics

        print(f"  Results:  {metrics['count']}")
        print(f"  Latency:  {metrics['elapsed']*1000:.1f}ms")
        print(f"  Avg Score: {metrics['avg_score']:.3f}")
        print(f"  Top Score: {metrics['top_score']:.3f}")

    print("\n" + "="*70)
    print("AFTER Phase 1 (With Query Expansion)")
    print("="*70)

    enhanced_results = {}
    for query, description in TEST_QUERIES:
        print(f"\nQuery: '{query}' ({description})")
        metrics = measure_search_performance(cks, query, use_expansion=True)
        enhanced_results[query] = metrics

        print(f"  Results:  {metrics['count']}")
        print(f"  Latency:  {metrics['elapsed']*1000:.1f}ms")
        print(f"  Avg Score: {metrics['avg_score']:.3f}")
        print(f"  Top Score: {metrics['top_score']:.3f}")

    # Calculate improvements
    print("\n" + "="*70)
    print("IMPROVEMENT SUMMARY")
    print("="*70)

    print(f"\n{'Query':<20} {'Results':<10} {'Latency':<10} {'Avg Score':<10}")
    print("-"*70)

    total_result_improvement = 0
    total_latency_increase = 0
    total_score_improvement = 0
    count = 0

    for query, _ in TEST_QUERIES:
        base = baseline_results[query]
        enhanced = enhanced_results[query]

        result_change = enhanced["count"] - base["count"]
        latency_change = enhanced["elapsed"] - base["elapsed"]
        score_change = enhanced["avg_score"] - base["avg_score"]

        result_pct = (result_change / base["count"] * 100) if base["count"] > 0 else 0
        latency_pct = (latency_change / base["elapsed"] * 100) if base["elapsed"] > 0 else 0

        print(f"{query[:20]:<20} {result_change:+d} ({result_pct:+.0f}%)  {latency_change*1000:+.1f}ms ({latency_pct:+.0f}%)  {score_change:+.3f}")

        total_result_improvement += result_pct
        total_latency_increase += latency_pct
        total_score_improvement += score_change
        count += 1

    print("-"*70)
    avg_result_improvement = total_result_improvement / count
    avg_latency_increase = total_latency_increase / count
    avg_score_improvement = total_score_improvement / count

    print(f"{'AVERAGE':<20} {avg_result_improvement:+.1f}%  {avg_latency_increase:+.1f}%  {avg_score_improvement:+.3f}")

    # Assessment
    print("\n" + "="*70)
    print("ASSESSMENT")
    print("="*70)

    if avg_result_improvement > 10:
        print(f"✅ EXCELLENT: {avg_result_improvement:+.1f}% result improvement")
    elif avg_result_improvement > 0:
        print(f"✅ GOOD: {avg_result_improvement:+.1f}% result improvement")
    else:
        print(f"⚠️ NO IMPROVEMENT: {avg_result_improvement:+.1f}% result change")

    if avg_latency_increase < 100:
        print(f"✅ ACCEPTABLE: {avg_latency_increase:+.1f}% latency increase")
    else:
        print(f"⚠️ HIGH LATENCY: {avg_latency_increase:+.1f}% latency increase")

    print("\nExpected improvements from Phase 1:")
    print("  - Recall: +20-30% (query expansion)")
    print("  - Precision: +15-25% (re-ranking)")
    print("  - Combined: +35-55% (both features)")

    return {
        "avg_result_improvement": avg_result_improvement,
        "avg_latency_increase": avg_latency_increase,
        "avg_score_improvement": avg_score_improvement,
    }


def save_baseline_results(results: dict):
    """Save baseline results to file"""
    import json
    from datetime import datetime

    output_file = Path(__file__).parent / "baseline_results.json"

    results["timestamp"] = datetime.now().isoformat()
    results["test_queries"] = [q for q, _ in TEST_QUERIES]

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Baseline results saved to: {output_file}")


def main():
    """Run performance baseline"""
    try:
        results = run_baseline()
        save_baseline_results(results)

        print("\n" + "="*70)
        print("✅ Performance baseline complete")
        print("="*70)

        return 0

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
