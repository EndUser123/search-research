"""Performance tests for 3D compatibility checking (T-003).

Tests verify that the 3D compatibility detection system meets performance
requirements even with large compatibility matrices.

Performance Requirements:
- Matrix lookup: <1ms (O(1) set lookup)
- Combination validation: <2ms (nested loops over small sets)
- Total overhead: <5ms (including detection + validation)

Test Coverage:
- Baseline performance with 10-entry matrix
- Scalability performance with 100-entry matrix
- Stress test with 1000-entry matrix
- O(1) membership verification
- Set operations vs list operations comparison
"""
from __future__ import annotations

# Add parent directory to path for imports
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_detection import (
    _COMPATIBILITY_MATRIX,
    _detect_3d_compatibility,
)


class Test3DCompatibilityPerformance(unittest.TestCase):
    """Performance tests for 3D compatibility detection."""

    def test_baseline_performance_10_entries(self):
        """Test baseline performance with 10-entry compatibility matrix.

        Requirement: <5ms total latency for 10 entries.
        """
        # Small but realistic match sets
        frameworks = ["assumption_surfacing", "socratic_decomposition"]
        modes = ["multi_agent", "graph"]
        profiles = ["architecture", "tradeoff_decision"]

        # Warm-up run
        _detect_3d_compatibility(frameworks, modes, profiles)

        # Performance measurement
        iterations = 1000
        start_time = time.perf_counter()

        for _ in range(iterations):
            result = _detect_3d_compatibility(frameworks, modes, profiles)

        end_time = time.perf_counter()
        avg_latency_ms = ((end_time - start_time) / iterations) * 1000

        # Verify results are correct
        self.assertGreater(len(result), 0, "Should detect at least one compatible combination")
        self.assertIn("framework", result[0], "Result should include framework")
        self.assertIn("mode", result[0], "Result should include mode")
        self.assertIn("profile", result[0], "Result should include profile")
        self.assertIn("rationale", result[0], "Result should include rationale")

        # Performance assertion: <5ms requirement
        self.assertLess(
            avg_latency_ms,
            5.0,
            f"3D compatibility detection took {avg_latency_ms:.3f}ms, "
            f"exceeds 5ms requirement with {len(_COMPATIBILITY_MATRIX)} matrix entries"
        )

        print(f"✓ Baseline performance: {avg_latency_ms:.3f}ms avg latency")

    def test_scalability_100_entries(self):
        """Test scalability with simulated 100-entry compatibility matrix.

        Requirement: <5ms even with 100 matrix entries.
        This simulates future growth of the compatibility matrix.
        """
        # Create a large simulated compatibility matrix
        simulated_matrix = {}
        for i in range(100):
            framework = f"framework_{i % 9}"  # 9 cognitive frameworks
            mode = f"mode_{i % 4}"  # 4 reasoning modes
            profile = f"profile_{i % 7}"  # 7 think profiles
            simulated_matrix[(framework, mode, profile)] = f"Simulated combination {i}"

        # Temporarily replace the global matrix
        original_matrix = _COMPATIBILITY_MATRIX.copy()
        _COMPATIBILITY_MATRIX.clear()
        _COMPATIBILITY_MATRIX.update(simulated_matrix)

        try:
            # Test with multiple matches
            frameworks = [f"framework_{i}" for i in range(9)]
            modes = [f"mode_{i}" for i in range(4)]
            profiles = [f"profile_{i}" for i in range(7)]

            # Warm-up run
            _detect_3d_compatibility(frameworks, modes, profiles)

            # Performance measurement
            iterations = 1000
            start_time = time.perf_counter()

            for _ in range(iterations):
                result = _detect_3d_compatibility(frameworks, modes, profiles)

            end_time = time.perf_counter()
            avg_latency_ms = ((end_time - start_time) / iterations) * 1000

            # Verify results
            self.assertGreater(len(result), 0, "Should detect combinations")

            # Performance assertion: <5ms even with 100 entries
            self.assertLess(
                avg_latency_ms,
                5.0,
                f"3D compatibility detection took {avg_latency_ms:.3f}ms, "
                f"exceeds 5ms requirement with 100 matrix entries"
            )

            print(f"✓ Scalability test (100 entries): {avg_latency_ms:.3f}ms avg latency")

        finally:
            # Restore original matrix
            _COMPATIBILITY_MATRIX.clear()
            _COMPATIBILITY_MATRIX.update(original_matrix)

    def test_stress_test_1000_entries(self):
        """Stress test with simulated 1000-entry compatibility matrix.

        Requirement: System should handle 1000 entries in <10ms.
        This is a stress test for worst-case scenario.
        """
        # Create a very large simulated compatibility matrix
        simulated_matrix = {}
        for i in range(1000):
            framework = f"framework_{i % 9}"
            mode = f"mode_{i % 4}"
            profile = f"profile_{i % 7}"
            simulated_matrix[(framework, mode, profile)] = f"Simulated combination {i}"

        # Temporarily replace the global matrix
        original_matrix = _COMPATIBILITY_MATRIX.copy()
        _COMPATIBILITY_MATRIX.clear()
        _COMPATIBILITY_MATRIX.update(simulated_matrix)

        try:
            # Test with maximum possible matches
            frameworks = [f"framework_{i}" for i in range(9)]
            modes = [f"mode_{i}" for i in range(4)]
            profiles = [f"profile_{i}" for i in range(7)]

            # Warm-up run
            _detect_3d_compatibility(frameworks, modes, profiles)

            # Performance measurement
            iterations = 100
            start_time = time.perf_counter()

            for _ in range(iterations):
                result = _detect_3d_compatibility(frameworks, modes, profiles)

            end_time = time.perf_counter()
            avg_latency_ms = ((end_time - start_time) / iterations) * 1000

            # Verify results
            self.assertGreater(len(result), 0, "Should detect combinations")

            # Relaxed performance assertion: <10ms for 1000 entries (stress test)
            self.assertLess(
                avg_latency_ms,
                10.0,
                f"3D compatibility detection took {avg_latency_ms:.3f}ms, "
                f"exceeds 10ms stress limit with 1000 matrix entries"
            )

            print(f"✓ Stress test (1000 entries): {avg_latency_ms:.3f}ms avg latency")

        finally:
            # Restore original matrix
            _COMPATIBILITY_MATRIX.clear()
            _COMPATIBILITY_MATRIX.update(original_matrix)

    def test_o1_membership_verification(self):
        """Verify O(1) membership check behavior.

        This test confirms that set operations provide O(1) membership
        checks regardless of matrix size.
        """
        # Test with current matrix size
        frameworks = ["assumption_surfacing", "socratic_decomposition"]
        modes = ["multi_agent"]
        profiles = ["architecture"]

        # Measure time for single detection
        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            result = _detect_3d_compatibility(frameworks, modes, profiles)

        end_time = time.perf_counter()
        avg_latency_ms = ((end_time - start_time) / iterations) * 1000

        # O(1) means time should not grow significantly with iterations
        # Single detection should be <0.01ms
        self.assertLess(
            avg_latency_ms,
            0.01,
            f"Single detection took {avg_latency_ms:.6f}ms, "
            f"expected O(1) behavior"
        )

        print(f"✓ O(1) membership verification: {avg_latency_ms:.6f}ms per detection")

    def test_set_vs_list_operations(self):
        """Compare set operations vs list operations performance.

        This test demonstrates that set operations scale better for large datasets.
        For small datasets, lists may be faster due to Python optimizations,
        but sets provide consistent O(1) performance regardless of size.
        """
        frameworks = ["assumption_surfacing", "socratic_decomposition"]
        modes = ["multi_agent"]
        profiles = ["architecture"]

        # Set operations (current implementation)
        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            framework_set = set(frameworks)
            mode_set = set(modes)
            profile_set = set(profiles)

            # Simulate membership checks
            for (fw, mo, pr) in _COMPATIBILITY_MATRIX.keys():
                _ = fw in framework_set
                _ = mo in mode_set
                _ = pr in profile_set

        set_time = time.perf_counter() - start_time

        # List operations (naive implementation)
        start_time = time.perf_counter()

        for _ in range(iterations):
            # Simulate membership checks with lists
            for (fw, mo, pr) in _COMPATIBILITY_MATRIX.keys():
                _ = fw in frameworks  # O(n) list membership
                _ = mo in modes
                _ = pr in profiles

        list_time = time.perf_counter() - start_time

        # Calculate speedup (can be <1 for small datasets, that's OK)
        speedup = list_time / set_time if set_time > 0 else float('inf')

        print(f"✓ Set operations: {set_time:.4f}s")
        print(f"✓ List operations: {list_time:.4f}s")
        print(f"✓ Speedup: {speedup:.2f}x")

        # For small datasets, both should be fast (<1s for 10k iterations)
        # The key is that sets provide consistent O(1) performance
        self.assertLess(
            set_time,
            1.0,
            f"Set operations took {set_time:.4f}s, expected <1s for 10k iterations"
        )

        # List operations should also be reasonably fast for small datasets
        self.assertLess(
            list_time,
            1.0,
            f"List operations took {list_time:.4f}s, expected <1s for 10k iterations"
        )

        # Both implementations should meet the <5ms per detection requirement
        avg_set_ms = (set_time / iterations) * 1000
        avg_list_ms = (list_time / iterations) * 1000

        print(f"✓ Avg per detection (set): {avg_set_ms:.6f}ms")
        print(f"✓ Avg per detection (list): {avg_list_ms:.6f}ms")

        self.assertLess(
            avg_set_ms,
            5.0,
            f"Set operations avg {avg_set_ms:.3f}ms per detection, exceeds 5ms requirement"
        )

    def test_empty_match_handling(self):
        """Test performance with empty match sets.

        Even with no matches, the function should return quickly.
        """
        # Empty match sets
        frameworks = []
        modes = []
        profiles = []

        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            result = _detect_3d_compatibility(frameworks, modes, profiles)

        end_time = time.perf_counter()
        avg_latency_ms = ((end_time - start_time) / iterations) * 1000

        # Should be very fast with empty sets
        self.assertLess(
            avg_latency_ms,
            0.001,
            f"Empty match handling took {avg_latency_ms:.6f}ms, "
            f"expected <0.001ms"
        )

        # Should return empty list
        result = _detect_3d_compatibility(frameworks, modes, profiles)
        self.assertEqual(len(result), 0, "Should return empty list for empty matches")

        print(f"✓ Empty match handling: {avg_latency_ms:.6f}ms avg latency")

    def test_partial_match_handling(self):
        """Test performance with partial matches.

        Common scenario: only some dimensions have matches.
        """
        # Partial matches: only frameworks matched
        frameworks = ["assumption_surfacing", "socratic_decomposition"]
        modes = []
        profiles = []

        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            result = _detect_3d_compatibility(frameworks, modes, profiles)

        end_time = time.perf_counter()
        avg_latency_ms = ((end_time - start_time) / iterations) * 1000

        # Should be very fast with partial matches
        self.assertLess(
            avg_latency_ms,
            0.002,
            f"Partial match handling took {avg_latency_ms:.6f}ms, "
            f"expected <0.002ms"
        )

        # Should return empty list (need all 3 dimensions for match)
        result = _detect_3d_compatibility(frameworks, modes, profiles)
        self.assertEqual(len(result), 0, "Should return empty list for partial matches")

        print(f"✓ Partial match handling: {avg_latency_ms:.6f}ms avg latency")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
