#!/usr/bin/env python3
"""
Test script for Quadlet-06: Performance Optimization and Tuning
Validates cache performance against targets and implements optimizations.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path("P:/").resolve() / ".claude" / "hooks"
sys.path.insert(0, str(hooks_dir))

from explore_opportunity_detector import ExploreOpportunityDetector
from guidance_cache import GuidanceCache, get_guidance_cache


def test_performance_targets():
    """Test that cache meets performance targets."""
    print("=" * 70)
    print("Quadlet-06: Performance Target Validation")
    print("=" * 70)
    print()

    # Performance targets
    TARGET_HIT_RATE = 85.0  # 85%
    TARGET_P85_RESPONSE = 100.0  # 100ms
    TARGET_P95_RESPONSE = 200.0  # 200ms (P95)

    print("Performance Targets:")
    print(f"  Hit Rate: >= {TARGET_HIT_RATE}%")
    print(f"  P85 Response: < {TARGET_P85_RESPONSE}ms")
    print(f"  P95 Response: < {TARGET_P95_RESPONSE}ms")
    print()

    # Test 1: Realistic workload performance
    print("Test 1: Realistic Workload Performance")
    print("-" * 50)

    cache = get_guidance_cache()
    cache.reset_metrics()

    # Simulate realistic workload (mix of patterns)
    import random

    response_times = []
    workload_types = [
        ("Repeated (80/20)", 0.4),  # 40% of operations
        ("Random", 0.3),            # 30% of operations
        ("Sequential", 0.2),        # 20% of operations
        ("Burst", 0.1),             # 10% of operations
    ]

    for _ in range(1000):
        # Choose workload type
        workload_type = random.choices(
            [w[0] for w in workload_types],
            weights=[w[1] for w in workload_types]
        )[0]

        if workload_type == "Repeated (80/20)":
            # 80/20 pattern
            key = random.choice([f"hot_{i}" for i in range(20)]) if random.random() < 0.8 else f"cold_{random.randint(0, 180)}"
        elif workload_type == "Random":
            key = f"rand_{random.randint(0, 200)}"
        elif workload_type == "Sequential":
            key = f"seq_{random.randint(0, 200)}"
        else:  # Burst
            key = f"burst_{random.randint(0, 50)}"

        start = time.time()
        cache.get(key, lambda: {"data": "value"})
        response_times.append((time.time() - start) * 1000)

    # Calculate metrics
    metrics = cache.get_metrics()
    total_hits = metrics["l1_hits"] + metrics["l2_hits"] + metrics["l3_hits"]
    hit_rate = (total_hits / metrics["total_requests"] * 100) if metrics["total_requests"] > 0 else 0.0

    sorted_times = sorted(response_times)
    p50 = sorted_times[len(sorted_times) // 2]
    p85 = sorted_times[int(len(sorted_times) * 0.85)]
    p95 = sorted_times[int(len(sorted_times) * 0.95)]
    p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 100 else p95

    print(f"  Total Operations: {metrics['total_requests']}")
    print(f"  L1 Hits: {metrics['l1_hits']} ({metrics['l1_hit_rate']:.2f}%)")
    print(f"  L2 Hits: {metrics['l2_hits']} ({metrics['l2_hit_rate']:.2f}%)")
    print(f"  Overall Hit Rate: {hit_rate:.2f}%")
    print()
    print("  Response Times:")
    print(f"    P50: {p50:.3f}ms")
    print(f"    P85: {p85:.3f}ms")
    print(f"    P95: {p95:.3f}ms")
    print(f"    P99: {p99:.3f}ms")
    print()

    # Validate targets
    hit_rate_pass = hit_rate >= TARGET_HIT_RATE
    p85_pass = p85 < TARGET_P85_RESPONSE
    p95_pass = p95 < TARGET_P95_RESPONSE

    print(f"  Hit Rate (target: {TARGET_HIT_RATE}%): {'✅ PASS' if hit_rate_pass else '❌ FAIL'} ({hit_rate:.2f}%)")
    print(f"  P85 Response (target: <{TARGET_P85_RESPONSE}ms): {'✅ PASS' if p85_pass else '❌ FAIL'} ({p85:.3f}ms)")
    print(f"  P95 Response (target: <{TARGET_P95_RESPONSE}ms): {'✅ PASS' if p95_pass else '❌ FAIL'} ({p95:.3f}ms)")

    test1_pass = hit_rate_pass and p85_pass and p95_pass
    print()

    # Test 2: Cache efficiency under load
    print("Test 2: Cache Efficiency Under Load")
    print("-" * 50)

    cache2 = GuidanceCache("test_load")
    cache2.reset_metrics()

    # High load test (5000 operations)
    load_start = time.time()
    for i in range(5000):
        key = f"load_key_{i % 500}"  # 500 unique keys
        cache2.get(key, lambda: {"data": f"value_{i}"})
    load_duration = (time.time() - load_start) * 1000

    load_metrics = cache2.get_metrics()
    load_hit_rate = ((load_metrics["l1_hits"] + load_metrics["l2_hits"]) /
                     load_metrics["total_requests"] * 100)
    ops_per_second = 5000 / (load_duration / 1000)

    print("  Operations: 5000")
    print(f"  Duration: {load_duration:.2f}ms")
    print(f"  Throughput: {ops_per_second:.0f} ops/sec")
    print(f"  Hit Rate: {load_hit_rate:.2f}%")
    print()

    # Load targets
    throughput_target = 10000  # 10k ops/sec
    throughput_pass = ops_per_second >= throughput_target
    hit_rate_load_pass = load_hit_rate >= 80.0  # 80% under load

    print(f"  Throughput (target: {throughput_target} ops/sec): {'✅ PASS' if throughput_pass else '❌ FAIL'} ({ops_per_second:.0f} ops/sec)")
    print(f"  Hit Rate Under Load (target: 80%): {'✅ PASS' if hit_rate_load_pass else '❌ FAIL'} ({load_hit_rate:.2f}%)")

    test2_pass = throughput_pass and hit_rate_load_pass
    print()

    # Test 3: Memory efficiency
    print("Test 3: Memory Efficiency")
    print("-" * 50)

    cache3 = GuidanceCache("test_memory")

    # Fill cache to capacity
    for i in range(cache3.l1_max_size + 50):
        cache3.set(f"mem_key_{i}", {"data": f"value_{i}", "metadata": "x" * 100})

    l1_size = len(cache3.l1_cache)
    l2_files = list(cache3.l2_cache_dir.glob("*.json"))
    l2_size = len(l2_files)

    print(f"  L1 Entries: {l1_size} / {cache3.l1_max_size}")
    print(f"  L2 Entries: {l2_size}")
    print(f"  L1 Usage: {l1_size / cache3.l1_max_size * 100:.1f}%")
    print()

    # Memory targets
    l1_efficient = l1_size <= cache3.l1_max_size
    l2_efficient = l2_size <= cache3.l2_max_size

    print(f"  L1 Size Within Limit: {'✅ PASS' if l1_efficient else '❌ FAIL'}")
    print(f"  L2 Size Within Limit: {'✅ PASS' if l2_efficient else '❌ FAIL'}")

    test3_pass = l1_efficient and l2_efficient
    print()

    # Test 4: Explore detector performance
    print("Test 4: Explore Opportunity Detector Performance")
    print("-" * 50)

    detector = ExploreOpportunityDetector()

    # Test detection performance
    detection_times = []

    for prompt in [
        "I want to understand the codebase architecture",
        "Explore the authentication system components",
        "What does path_validator.py do?",
        "Fix the bug in line 42",
        "Analyze the error handling approach",
    ] * 20:  # 100 detections total
        start = time.time()
        detector.detect_opportunity(prompt, {"cwd": "P:/__csf"})
        detection_times.append((time.time() - start) * 1000)

    avg_detection = sum(detection_times) / len(detection_times)
    sorted_detections = sorted(detection_times)
    p85_detection = sorted_detections[int(len(sorted_detections) * 0.85)]

    print(f"  Detections: {len(detection_times)}")
    print(f"  Average: {avg_detection:.3f}ms")
    print(f"  P85: {p85_detection:.3f}ms")
    print()

    # Detector targets
    detector_target = 500.0  # 500ms
    detector_pass = p85_detection < detector_target

    print(f"  P85 Detection Time (target: <{detector_target}ms): {'✅ PASS' if detector_pass else '❌ FAIL'} ({p85_detection:.3f}ms)")

    test4_pass = detector_pass
    print()

    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)

    all_tests = [
        ("Realistic Workload Performance", test1_pass),
        ("Cache Efficiency Under Load", test2_pass),
        ("Memory Efficiency", test3_pass),
        ("Explore Detector Performance", test4_pass),
    ]

    passed = sum(1 for _, result in all_tests if result)
    failed = len(all_tests) - passed

    print(f"Tests: {passed} passed, {failed} failed out of {len(all_tests)} total")
    print()

    for name, result in all_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")

    print()

    if failed == 0:
        print("✅ All performance targets validated!")
        return 0
    print(f"❌ {failed} test(s) failed performance targets")
    return 1


def test_optimization_reliability():
    """Test that optimizations don't break existing functionality."""
    print("\n" + "=" * 70)
    print("Optimization Reliability Tests")
    print("=" * 70)
    print()

    # Import and run basic tests
    try:
        # Run quadlet-05 tests to ensure no regression
        test_file = Path("P:/__csf/.speckit/memory/TSK-251222-GitWorktree-1745/test_quadlet_05.py")
        if test_file.exists():
            import subprocess
            result = subprocess.run(
                [sys.executable, str(test_file)],
                capture_output=True,
                timeout=60, check=False
            )

            if result.returncode == 0:
                print("  ✅ Quadlet-05 tests still passing (no regression)")
                return 0
            print("  ❌ Quadlet-05 tests failing (regression detected)")
            return 1
        print("  ⚠️  Quadlet-05 test file not found")
        return 0

    except Exception as e:
        print(f"  ❌ Reliability test failed: {e}")
        return 1


if __name__ == "__main__":
    result1 = test_performance_targets()
    result2 = test_optimization_reliability()
    sys.exit(max(result1, result2))
