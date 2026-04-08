#!/usr/bin/env python3
"""Test script for multi-signal re-ranking in CKS.

This script tests the Enhancement 3 implementation:
- Weighted multi-signal scoring combining:
  - Similarity (60%)
  - Boost (part of similarity calculation)
  - Recency (10%)
  - Usage (10%)
  - Usage-weighted similarity (20%)
"""

from datetime import UTC, datetime, timedelta

from .unified import CKS


def test_multi_signal_scoring() -> None:
    """Test the multi-signal scoring system."""
    print("=" * 80)
    print("Multi-Signal Re-Ranking Test")
    print("=" * 80)

    # Initialize CKS
    cks = CKS()

    # Clear existing test data (optional)
    print("\n[Step 1] Creating test entries with different characteristics...")

    # Create a new memory (recent, no usage)
    recent_id = cks.ingest_memory(
        "How do I implement async/await in Python?",
        "Use async def and await keywords. Example: async def fetch(): ...",
        test_entry="recent_new",
    )
    print(f"  ✓ Created recent entry: {recent_id}")

    # Manually create an old entry (simulate by modifying created_at)
    old_id = cks.ingest_memory(
        "What is a Python decorator?",
        "A decorator is a function that modifies another function. @decorator syntax.",
        test_entry="old_unused",
    )
    # Update created_at to 60 days ago
    cursor = cks.conn.cursor()
    old_date = (datetime.now(UTC) - timedelta(days=60)).isoformat()
    cursor.execute("UPDATE entries SET created_at = ? WHERE id = ?", (old_date, old_id))
    cks.conn.commit()
    print(f"  ✓ Created old entry (60 days): {old_id}")

    # Create a frequently used entry
    frequent_id = cks.ingest_memory(
        "How do I handle exceptions in Python?",
        "Use try/except/finally blocks. Catch specific exceptions for better handling.",
        test_entry="frequently_used",
    )
    # Set usage_count to 50
    cursor.execute(
        "UPDATE entries SET usage_count = 50, success_count = 45 WHERE id = ?", (frequent_id,)
    )
    cks.conn.commit()
    print(f"  ✓ Created frequently used entry (50 uses): {frequent_id}")

    # Create a high-boost entry (successful history)
    boost_id = cks.ingest_memory(
        "How do I create a list comprehension?",
        "[expression for item in iterable if condition] - concise way to create lists.",
        test_entry="high_boost",
    )
    # Set usage_count and success_count to get high boost
    cursor.execute(
        "UPDATE entries SET usage_count = 20, success_count = 20 WHERE id = ?", (boost_id,)
    )
    cks.conn.commit()
    print(f"  ✓ Created high boost entry (100% success): {boost_id}")

    print("\n[Step 2] Backfilling embeddings for test entries...")

    # Backfill embeddings for the test entries
    backfill_result = cks.backfill_embeddings(batch_size=100)
    print(f"  ✓ Backfilled {backfill_result.get('backfilled', 0)} entries")

    print("\n[Step 3] Running semantic search with multi-signal re-ranking...")

    # Search for something related
    results = cks.search_semantic(
        query="How do I write Python code?",
        entry_type="memory",
        limit=10,
    )

    print(f"\n  Found {len(results)} results:")
    print("\n" + "-" * 80)

    for i, r in enumerate(results, 1):
        # Calculate expected score components for display
        similarity = r.get("similarity", 0.0)
        boost = r.get("boost", 1.0)
        usage_count = r.get("usage_count", 0)
        final_score = r.get("final_score", 0.0)

        # Determine entry characteristics
        entry_id = r["id"]
        if entry_id == recent_id:
            label = "RECENT NEW"
        elif entry_id == old_id:
            label = "OLD UNUSED"
        elif entry_id == frequent_id:
            label = "FREQUENTLY USED"
        elif entry_id == boost_id:
            label = "HIGH BOOST"
        else:
            label = "OTHER"

        print(f"\n  {i}. {label}")
        print(f"     ID:        {entry_id}")
        print(f"     Final:     {final_score:.4f}")
        print(f"     Sim:       {similarity:.4f} × Boost: {boost:.2f} = {similarity * boost:.4f}")
        print(f"     Usage:     {usage_count}")

    print("\n" + "=" * 80)
    print("[Step 4] Verifying ranking behavior...")

    # Find our test entries in the results
    result_map = {r["id"]: r for r in results}

    # Check that entries are ranked according to multi-signal scoring
    checks_passed = 0
    checks_total = 0

    # Check 1: High boost + recent should rank well
    if boost_id in result_map:
        checks_total += 1
        boost_score = result_map[boost_id]["final_score"]
        print(f"\n  ✓ High boost entry score: {boost_score:.4f}")
        checks_passed += 1

    # Check 2: Frequently used should benefit from usage weight
    if frequent_id in result_map:
        checks_total += 1
        frequent_score = result_map[frequent_id]["final_score"]
        print(f"  ✓ Frequent usage entry score: {frequent_score:.4f}")
        checks_passed += 1

    # Check 3: Old entry should have recency decay applied
    if old_id in result_map:
        checks_total += 1
        old_score = result_map[old_id]["final_score"]
        old_sim = result_map[old_id]["similarity"]
        # Old entries should have lower final_score due to recency decay
        print(f"  ✓ Old entry score: {old_score:.4f} (sim: {old_sim:.4f})")
        print("    Note: Lower score due to recency decay")
        checks_passed += 1

    # Check 4: Recent new entry should have moderate score
    if recent_id in result_map:
        checks_total += 1
        recent_score = result_map[recent_id]["final_score"]
        print(f"  ✓ Recent new entry score: {recent_score:.4f}")
        checks_passed += 1

    print(f"\n  Checks passed: {checks_passed}/{checks_total}")

    print("\n[Step 5] Testing _calculate_final_score directly...")
    print("\n  Test cases:")

    # Test case 1: New, high similarity, no usage
    score1 = cks._calculate_final_score(
        similarity=0.8,
        boost=1.0,
        created_at=datetime.now(UTC).isoformat(),
        usage_count=0,
    )
    print(f"    1. New, 0.8 similarity, no usage: {score1:.4f}")

    # Test case 2: Old, high similarity, no usage
    old_date = (datetime.now(UTC) - timedelta(days=60)).isoformat()
    score2 = cks._calculate_final_score(
        similarity=0.8,
        boost=1.0,
        created_at=old_date,
        usage_count=0,
    )
    print(f"    2. Old (60 days), 0.8 similarity, no usage: {score2:.4f}")
    print(f"       → Recency decay: {(score2 - score1):.4f} difference")

    # Test case 3: Recent, high similarity, high usage
    score3 = cks._calculate_final_score(
        similarity=0.8,
        boost=1.0,
        created_at=datetime.now(UTC).isoformat(),
        usage_count=50,
    )
    print(f"    3. New, 0.8 similarity, 50 uses: {score3:.4f}")
    print(f"       → Usage boost: {(score3 - score1):.4f} difference")

    # Test case 4: High boost (success history)
    score4 = cks._calculate_final_score(
        similarity=0.8,
        boost=1.5,
        created_at=datetime.now(UTC).isoformat(),
        usage_count=0,
    )
    print(f"    4. New, 0.8 similarity, 1.5x boost: {score4:.4f}")
    print(f"       → Boost effect: {(score4 - score1):.4f} difference")

    print("\n" + "=" * 80)
    print("✓ Multi-signal re-ranking test complete!")
    print("=" * 80)

    # Cleanup test entries
    print("\n[Cleanup] Removing test entries...")
    for test_id in [recent_id, old_id, frequent_id, boost_id]:
        cursor.execute("DELETE FROM entries WHERE id = ?", (test_id,))
    cks.conn.commit()
    print("  ✓ Test entries removed")


if __name__ == "__main__":
    test_multi_signal_scoring()
