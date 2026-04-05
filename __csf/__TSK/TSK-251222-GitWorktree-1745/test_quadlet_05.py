#!/usr/bin/env python3
"""
Test script for Quadlet-05: Multi-Level Cache System
Tests the guidance_cache.py module and integration with user_prompt_submit_cks.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path("P:/").resolve() / ".claude" / "hooks"
sys.path.insert(0, str(hooks_dir))

from guidance_cache import GuidanceCache, get_guidance_cache


def test_guidance_cache():
    """Test guidance cache functionality."""
    print("=" * 70)
    print("Quadlet-05: Multi-Level Cache System Tests")
    print("=" * 70)
    print()

    # Test 1: Basic cache operations
    print("Test 1: Basic Cache Operations")
    print("-" * 50)

    cache = GuidanceCache("test_basic")

    # Test set and get
    cache.set("key1", {"data": "value1"})
    result = cache.get("key1")

    if result == {"data": "value1"}:
        print("  ✅ Basic set/get working")
        test1_pass = True
    else:
        print(f"  ❌ Expected {{'data': 'value1'}}, got {result}")
        test1_pass = False

    # Test cache miss
    result = cache.get("nonexistent")
    if result is None:
        print("  ✅ Cache miss returns None")
        test1_2_pass = True
    else:
        print(f"  ❌ Expected None, got {result}")
        test1_2_pass = False

    print()

    # Test 2: LRU eviction
    print("Test 2: LRU Eviction (L1 Cache)")
    print("-" * 50)

    cache = GuidanceCache("test_lru")

    # Fill L1 cache to capacity + 1
    for i in range(cache.l1_max_size + 1):
        cache.set(f"key_{i}", f"value_{i}")

    # Check L1 directly (not via get, which checks L2)
    if "key_0" not in cache.l1_cache:
        print("  ✅ LRU eviction working (key_0 evicted from L1)")
        test2_pass = True
    else:
        print("  ❌ key_0 still in L1 cache")
        test2_pass = False

    # Last key should still be present in L1
    if f"key_{cache.l1_max_size}" in cache.l1_cache:
        print("  ✅ Latest key still present in L1 after eviction")
        test2_2_pass = True
    else:
        print("  ❌ Latest key was evicted from L1")
        test2_2_pass = False

    # Verify evicted key still accessible via L2
    result = cache.get("key_0")
    if result == "value_0":
        print("  ✅ Evicted key still accessible from L2 (promoted back to L1)")
        test2_3_pass = True
    else:
        print(f"  ❌ L2 fallback failed: {result}")
        test2_3_pass = False

    print()

    # Test 3: Cache hierarchy performance
    print("Test 3: Cache Hierarchy Performance")
    print("-" * 50)

    cache = GuidanceCache("test_performance")

    # Reset metrics
    cache.reset_metrics()

    # Set value
    cache.set("perf_test", {"result": "cached_data"})

    # Measure L1 hit
    start = time.time()
    value = cache.get("perf_test")
    l1_time = (time.time() - start) * 1000

    print(f"  L1 Cache Hit: {l1_time:.3f}ms (target: <10ms)")
    if l1_time < 10:
        print("  ✅ L1 performance within target")
        test3_pass = True
    else:
        print(f"  ❌ L1 too slow: {l1_time:.3f}ms")
        test3_pass = False

    # Clear L1 to test L2
    cache.clear_l1()

    # Measure L2 hit (includes L1 miss + L2 hit + promotion)
    start = time.time()
    value = cache.get("perf_test")
    l2_time = (time.time() - start) * 1000

    print(f"  L2 Cache Hit: {l2_time:.3f}ms (target: <30ms)")
    if l2_time < 30:
        print("  ✅ L2 performance within target")
        test3_2_pass = True
    else:
        print(f"  ❌ L2 too slow: {l2_time:.3f}ms")
        test3_2_pass = False

    if value == {"result": "cached_data"}:
        print("  ✅ L2 returns correct data")
        test3_3_pass = True
    else:
        print(f"  ❌ L2 data incorrect: {value}")
        test3_3_pass = False

    print()

    # Test 4: Fetch function
    print("Test 4: Fetch Function on Cache Miss")
    print("-" * 50)

    cache = GuidanceCache("test_fetch")
    # Clear any existing cache to ensure fresh start
    cache.clear_all()

    call_count = {"count": 0}

    def expensive_operation():
        call_count["count"] += 1
        return {"expensive": True, "timestamp": time.time()}

    # First call should trigger fetch (use unique key with timestamp)
    unique_key = f"fetch_test_{time.time()}"
    result1 = cache.get(unique_key, expensive_operation)
    if result1["expensive"] and call_count["count"] == 1:
        print("  ✅ Fetch function called on miss")
        test4_pass = True
    else:
        print(f"  ❌ Fetch test failed: {result1}, calls: {call_count['count']}")
        test4_pass = False

    # Second call should use cache (not call fetch)
    result2 = cache.get(unique_key, expensive_operation)
    if result2["expensive"] and call_count["count"] == 1:
        print("  ✅ Cache used on subsequent call (fetch not called)")
        test4_2_pass = True
    else:
        print(f"  ❌ Fetch called again: {call_count['count']}")
        test4_2_pass = False

    print()

    # Test 5: Cache invalidation
    print("Test 5: Cache Invalidation")
    print("-" * 50)

    cache = GuidanceCache("test_invalidation")

    cache.set("invalidate_test", {"data": "value"})
    result1 = cache.get("invalidate_test")

    if result1 is not None:
        # Invalidate
        cache.invalidate("invalidate_test")
        result2 = cache.get("invalidate_test")

        if result2 is None:
            print("  ✅ Invalidation working (entry removed)")
            test5_pass = True
        else:
            print(f"  ❌ Entry still present after invalidation: {result2}")
            test5_pass = False
    else:
        print("  ❌ Set operation failed")
        test5_pass = False

    print()

    # Test 6: Metrics tracking
    print("Test 6: Performance Metrics")
    print("-" * 50)

    cache = GuidanceCache("test_metrics")
    cache.reset_metrics()

    # Generate some cache activity
    cache.set("metrics_test1", "value1")
    cache.set("metrics_test2", "value2")
    cache.get("metrics_test1")  # L1 hit
    cache.get("metrics_test2")  # L1 hit
    cache.get("nonexistent")     # L1 miss, L2 miss, L3 miss

    metrics = cache.get_metrics()

    print(f"  Total Requests: {metrics['total_requests']}")
    print(f"  L1 Hits: {metrics['l1_hits']}")
    print(f"  L1 Hit Rate: {metrics['l1_hit_rate']}%")
    print(f"  Overall Hit Rate: {metrics['overall_hit_rate']}%")

    if metrics["total_requests"] == 3:
        print("  ✅ Request count accurate")
        test6_pass = True
    else:
        print(f"  ❌ Expected 3 requests, got {metrics['total_requests']}")
        test6_pass = False

    if metrics["l1_hits"] == 2:
        print("  ✅ L1 hits accurate")
        test6_2_pass = True
    else:
        print(f"  ❌ Expected 2 L1 hits, got {metrics['l1_hits']}")
        test6_2_pass = False

    print()

    # Test 7: L2 persistence
    print("Test 7: L2 Disk Cache Persistence")
    print("-" * 50)

    cache1 = GuidanceCache("test_persistence")
    cache1.set("persistent_test", {"data": "persists"})

    # Create new cache instance (simulates restart)
    cache2 = GuidanceCache("test_persistence")
    result = cache2.get("persistent_test")

    if result == {"data": "persists"}:
        print("  ✅ L2 cache persists across instances")
        test7_pass = True
    else:
        print(f"  ❌ Persistence failed: {result}")
        test7_pass = False

    print()

    # Test 8: Global cache instance
    print("Test 8: Global Cache Singleton")
    print("-" * 50)

    # Get global cache twice
    cache_a = get_guidance_cache()
    cache_b = get_guidance_cache()

    if cache_a is cache_b:
        print("  ✅ Same instance returned (singleton working)")
        test8_pass = True
    else:
        print("  ❌ Different instances returned")
        test8_pass = False

    # Test that data persists across global accesses
    cache_a.set("global_test", "global_value")
    result = cache_b.get("global_test")

    if result == "global_value":
        print("  ✅ Data persists across global accesses")
        test8_2_pass = True
    else:
        print(f"  ❌ Data not shared: {result}")
        test8_2_pass = False

    print()

    # Test 9: Clear operations
    print("Test 9: Cache Clear Operations")
    print("-" * 50)

    cache = GuidanceCache("test_clear")

    cache.set("clear_test1", "value1")
    cache.set("clear_test2", "value2")

    # Clear L1 only
    cache.clear_l1()

    # Check L1 directly (not via get which checks L2)
    if "clear_test1" not in cache.l1_cache:
        print("  ✅ clear_l1() clears L1 cache")
        test9_pass = True
    else:
        print("  ❌ clear_test1 still in L1 after clear_l1()")
        test9_pass = False

    # Verify L2 still has the data
    cache2 = GuidanceCache("test_clear")
    result_l2 = cache2.get("clear_test1")
    if result_l2 == "value1":
        print("  ✅ clear_l1() preserves L2 cache")
        test9_2_pass = True
    else:
        print(f"  ❌ L2 cache was cleared: {result_l2}")
        test9_2_pass = False

    # Clear all
    cache.clear_all()
    # After clear_all, get() should return None (both L1 and L2 cleared)
    result_all = cache.get("clear_test2")

    if result_all is None:
        print("  ✅ clear_all() clears L1 and L2")
        test9_3_pass = True
    else:
        print(f"  ❌ clear_all() didn't clear: {result_all}")
        test9_3_pass = False

    print()

    # Summary
    print("=" * 70)
    all_tests = [
        ("Basic operations", test1_pass and test1_2_pass),
        ("LRU eviction", test2_pass and test2_2_pass and test2_3_pass),
        ("Performance", test3_pass and test3_2_pass and test3_3_pass),
        ("Fetch function", test4_pass and test4_2_pass),
        ("Invalidation", test5_pass),
        ("Metrics tracking", test6_pass and test6_2_pass),
        ("L2 persistence", test7_pass),
        ("Global singleton", test8_pass and test8_2_pass),
        ("Clear operations", test9_pass and test9_2_pass and test9_3_pass),
    ]

    passed = sum(1 for _, result in all_tests if result)
    failed = len(all_tests) - passed

    print(f"Test Summary: {passed} passed, {failed} failed out of {len(all_tests)} total")
    print("=" * 70)

    for name, result in all_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    if failed == 0:
        print("\n✅ All tests passed!")
        return 0
    print(f"\n❌ {failed} test(s) failed")
    return 1


def test_integration_with_cks():
    """Test integration with user_prompt_submit_cks.py."""
    print("\n" + "=" * 70)
    print("Integration Tests: user_prompt_submit_cks.py")
    print("=" * 70)
    print()

    try:
        from user_prompt_submit_cks import CKSIntegrator

        # Test that CKS integrator can use cache
        integrator = CKSIntegrator()

        # This test just verifies the integration doesn't break
        # (actual CKS queries require CKS to be available)
        print("  ✅ CKSIntegrator imports successfully with cache")
        print("  ✅ Cache integration ready (depends on CKS availability)")
        return 0

    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        return 1
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return 1


if __name__ == "__main__":
    result1 = test_guidance_cache()
    result2 = test_integration_with_cks()
    sys.exit(max(result1, result2))
