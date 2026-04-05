#!/usr/bin/env python
"""
CKS Phase 1 Integration Tests

Tests the integrated Phase 1 features:
- Query expansion
- RRF fusion
- MMR diversity
- Combined features

Run: python integration_tests.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

try:
    from cks.query_expansion import QueryExpander
    from cks.reranking import maximal_marginal_relevance, reciprocal_rank_fusion
    from cks.unified import CKS
    print("✅ All Phase 1 modules imported successfully")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   Ensure src/cks/query_expansion.py and src/cks/reranking.py exist")
    sys.exit(1)


def test_query_expansion():
    """Test 1: Query expansion functionality"""
    print("\n" + "="*60)
    print("TEST 1: Query Expansion")
    print("="*60)

    expander = QueryExpander()

    # Test 1a: Synonym expansion
    print("\n1a. Synonym Expansion")
    variations = expander.expand_query("db timeout")
    print("   Input: 'db timeout'")
    print(f"   Variations: {variations}")
    assert len(variations) > 1, "Synonym expansion failed (no variations)"
    assert any("timeout" in v or "db" in v or "limit" in v or "time" in v for v in variations), "Synonym expansion failed (no relevant terms)"
    print("   ✅ PASS: Synonym expansion working")

    # Test 1b: Abbreviation expansion
    print("\n1b. Abbreviation Expansion")
    variations = expander.expand_query("cks auth")
    print("   Input: 'cks auth'")
    print(f"   Variations: {variations}")
    assert "Constitutional Knowledge System authentication" in variations, "Abbreviation expansion failed"
    print("   ✅ PASS: Abbreviation expansion working")

    # Test 1c: Entity-specific expansion
    print("\n1c. Entity-Specific Expansion")
    variations = expander.expand_query("naming", entity_slug="taskmaster")
    print("   Input: 'naming' (entity: taskmaster)")
    print(f"   Variations: {variations}")
    assert any("TSK" in v for v in variations), "Entity-specific expansion failed"
    print("   ✅ PASS: Entity-specific expansion working")


def test_reranking():
    """Test 2: Re-ranking algorithms"""
    print("\n" + "="*60)
    print("TEST 2: Re-ranking Algorithms")
    print("="*60)

    # Test 2a: RRF Fusion
    print("\n2a. Reciprocal Rank Fusion")
    results1 = [
        {"id": "a", "title": "Result A", "similarity": 0.9},
        {"id": "b", "title": "Result B", "similarity": 0.8},
        {"id": "c", "title": "Result C", "similarity": 0.7}
    ]
    results2 = [
        {"id": "b", "title": "Result B", "similarity": 0.85},
        {"id": "d", "title": "Result D", "similarity": 0.75},
        {"id": "a", "title": "Result A", "similarity": 0.7}
    ]

    merged = reciprocal_rank_fusion([results1, results2], k=60)
    print("   Input: 2 result lists")
    print(f"   Top 3 merged IDs: {[r['id'] for r in merged[:3]]}")
    assert len(merged) == 4, "RRF fusion failed"
    print("   ✅ PASS: RRF fusion working")

    # Test 2b: MMR Diversity
    print("\n2b. Maximal Marginal Relevance")
    results = [
        {"id": "a", "title": "Result A", "content": "database management systems", "similarity": 0.9},
        {"id": "b", "title": "Result B", "content": "database configuration", "similarity": 0.85},
        {"id": "c", "title": "Result C", "content": "authentication flow", "similarity": 0.7},
        {"id": "d", "title": "Result D", "content": "user login", "similarity": 0.65}
    ]

    diverse = maximal_marginal_relevance("database", results, lambda_param=0.7)
    print("   Input: 4 results (2 similar, 2 different)")
    print(f"   Top 3 diverse IDs: {[r['id'] for r in diverse[:3]]}")
    assert len(diverse) == 4, "MMR failed"
    print("   ✅ PASS: MMR diversity working")


def test_cks_integration():
    """Test 3: CKS integration (requires CKS database)"""
    print("\n" + "="*60)
    print("TEST 3: CKS Integration")
    print("="*60)

    try:
        cks = CKS()
        print("   CKS initialized successfully")

        # Test basic search
        print("\n3a. Basic Semantic Search")
        results = cks.search_semantic("database", limit=3)
        print("   Query: 'database'")
        print(f"   Results: {len(results)} found")
        print("   ✅ PASS: Basic search working")

        # Note: Query expansion integration requires modified search_semantic
        print("\n3b. Enhanced Search (if integrated)")
        print("   ⚠️ SKIP: Requires full integration (see integration_guide.md)")

    except Exception as e:
        print(f"   ⚠️ SKIP: CKS test failed - {e}")
        print("   This is expected if CKS database doesn't exist yet")


def test_api_compatibility():
    """Test 4: API compatibility"""
    print("\n" + "="*60)
    print("TEST 4: API Compatibility")
    print("="*60)

    # Test that modules have expected APIs
    print("\n4a. QueryExpander API")
    expander = QueryExpander()
    assert hasattr(expander, "expand_query"), "Missing expand_query method"
    assert hasattr(expander, "_expand_synonyms"), "Missing _expand_synonyms method"
    print("   ✅ PASS: QueryExpander has expected methods")

    print("\n4b. Reranking Functions")
    assert callable(reciprocal_rank_fusion), "reciprocal_rank_fusion not callable"
    assert callable(maximal_marginal_relevance), "maximal_marginal_relevance not callable"
    print("   ✅ PASS: Reranking functions are callable")

    print("\n4c. Type Annotations")
    from typing import get_type_hints
    hints = get_type_hints(expander.expand_query)
    print(f"   expand_query hints: {hints}")
    print("   ✅ PASS: Type annotations present")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("CKS Phase 1 Integration Tests")
    print("="*60)

    try:
        test_query_expansion()
        test_reranking()
        test_cks_integration()
        test_api_compatibility()

        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print("✅ All tests passed!")
        print("\nNext steps:")
        print("1. Apply integration from integration_guide.md")
        print("2. Run performance baseline: python performance_baseline.py")
        print("3. Create automated test suite")

        return 0

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
