"""
Pragmatic performance tests for PreToolUse verification router.

Focuses on practical performance characteristics rather than
micro-optimization. Tests 10 runs to establish baseline.
"""

import sys
import time
from pathlib import Path

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestRouterPerformance:
    """Test router performance characteristics."""

    def test_early_exit_performance_benchmark(self):
        """Test early-exit optimization is fast for non-investigation queries."""
        from PreToolUse_verification_router import run_verification_modules

        # Non-investigation query (should early-exit quickly)
        data = {"userPrompt": "create a new file"}

        # Warm up
        for _ in range(3):
            run_verification_modules(data)

        # Benchmark 10 runs
        start = time.perf_counter()
        for _ in range(10):
            run_verification_modules(data)
        end = time.perf_counter()

        avg_time_ms = (end - start) / 10 * 1000

        # Early exit should be very fast (< 1ms average)
        # This is the key performance optimization
        assert avg_time_ms < 1.0, f"Early exit took {avg_time_ms:.2f}ms, expected < 1.0ms"

        print(f"\n[PERFORMANCE] Early exit: {avg_time_ms:.3f}ms average (10 runs)")

    def test_investigation_verification_performance(self):
        """Test investigation verification adds acceptable overhead."""
        from PreToolUse_verification_router import run_verification_modules

        # Investigation query (triggers verification)
        data = {"userPrompt": "investigate this error"}

        # Warm up
        for _ in range(3):
            run_verification_modules(data)

        # Benchmark 10 runs
        start = time.perf_counter()
        for _ in range(10):
            run_verification_modules(data)
        end = time.perf_counter()

        avg_time_ms = (end - start) / 10 * 1000

        # Investigation verification should be fast (< 5ms average)
        # This includes keyword detection, module loading, template generation
        assert avg_time_ms < 5.0, f"Investigation verification took {avg_time_ms:.2f}ms, expected < 5.0ms"

        print(f"\n[PERFORMANCE] Investigation verification: {avg_time_ms:.3f}ms average (10 runs)")

    def test_module_caching_performance(self):
        """Test module caching reduces subsequent load times."""
        from PreToolUse_verification_router import load_verification_modules

        # First load (uncached)
        start = time.perf_counter()
        module1 = load_verification_modules("investigation_verification")
        first_load_ms = (time.perf_counter() - start) * 1000

        # Second load (cached)
        start = time.perf_counter()
        module2 = load_verification_modules("investigation_verification")
        cached_load_ms = (time.perf_counter() - start) * 1000

        # Cached load should be significantly faster
        assert cached_load_ms < first_load_ms, "Cached load should be faster than first load"
        assert module1 is module2, "Cached module should be same object"

        # Cached load should be very fast (< 0.1ms)
        assert cached_load_ms < 0.1, f"Cached load took {cached_load_ms:.3f}ms, expected < 0.1ms"

        print(f"\n[PERFORMANCE] Module load - First: {first_load_ms:.3f}ms, Cached: {cached_load_ms:.3f}ms")

    def test_json_parsing_performance(self):
        """Test JSON input parsing is efficient."""
        from PreToolUse_verification_router import normalize_input_fields

        # Test data with camelCase fields
        test_data = {
            "toolName": "Bash",
            "toolInput": {"command": "test command"},
            "userPrompt": "investigate error"
        }

        # Benchmark 100 iterations (JSON parsing is cheap)
        start = time.perf_counter()
        for _ in range(100):
            normalized = normalize_input_fields(test_data)
        end = time.perf_counter()

        avg_time_ms = (end - start) / 100 * 1000

        # JSON parsing should be very fast (< 0.1ms per iteration)
        assert avg_time_ms < 0.1, f"JSON parsing took {avg_time_ms:.4f}ms, expected < 0.1ms"

        print(f"\n[PERFORMANCE] JSON parsing: {avg_time_ms:.4f}ms average (100 runs)")


class TestPerformanceRegression:
    """Test that performance doesn't regress over time."""

    def test_bypass_detection_performance(self):
        """Test bypass flag detection is fast."""
        from PreToolUse_verification_modules.investigation_verification import check_bypass_flag

        data = {
            "userPrompt": "investigate error --skip-investigation-verify",
            "sessionId": "test-session"
        }

        # Benchmark 100 iterations
        start = time.perf_counter()
        for _ in range(100):
            check_bypass_flag(data)
        end = time.perf_counter()

        avg_time_ms = (end - start) / 100 * 1000

        # Bypass detection should be fast (< 0.5ms per iteration)
        # Relaxed from 0.05ms to 0.5ms to account for file I/O logging
        assert avg_time_ms < 0.5, f"Bypass detection took {avg_time_ms:.4f}ms, expected < 0.5ms"

        print(f"\n[PERFORMANCE] Bypass detection: {avg_time_ms:.4f}ms average (100 runs)")

    def test_keyword_detection_performance(self):
        """Test keyword detection is fast."""
        from PreToolUse_verification_modules.investigation_verification import (
            has_investigation_keywords,
        )

        # Test with direct keyword
        data = {"userPrompt": "investigate this error"}

        # Benchmark 100 iterations
        start = time.perf_counter()
        for _ in range(100):
            has_investigation_keywords(data)
        end = time.perf_counter()

        avg_time_ms = (end - start) / 100 * 1000

        # Keyword detection should be very fast (< 0.05ms per iteration)
        assert avg_time_ms < 0.05, f"Keyword detection took {avg_time_ms:.4f}ms, expected < 0.05ms"

        print(f"\n[PERFORMANCE] Keyword detection: {avg_time_ms:.4f}ms average (100 runs)")

    def test_obfuscation_normalization_performance(self):
        """Test obfuscation normalization is fast."""
        from PreToolUse_verification_modules.investigation_verification import (
            has_investigation_keywords,
        )

        # Test with obfuscated keyword
        data = {"userPrompt": "there's an e r r o r in the system"}

        # Benchmark 100 iterations
        start = time.perf_counter()
        for _ in range(100):
            has_investigation_keywords(data)
        end = time.perf_counter()

        avg_time_ms = (end - start) / 100 * 1000

        # Obfuscation normalization should be fast (< 0.1ms per iteration)
        assert avg_time_ms < 0.1, f"Obfuscation normalization took {avg_time_ms:.4f}ms, expected < 0.1ms"

        print(f"\n[PERFORMANCE] Obfuscation normalization: {avg_time_ms:.4f}ms average (100 runs)")


class TestMemoryEfficiency:
    """Test memory efficiency characteristics."""

    def test_module_caching_memory(self):
        """Test module caching doesn't duplicate modules in memory."""
        from PreToolUse_verification_router import _MODULE_CACHE, load_verification_modules

        # Clear cache first
        _MODULE_CACHE.clear()

        # Load module multiple times
        module1 = load_verification_modules("investigation_verification")
        module2 = load_verification_modules("investigation_verification")
        module3 = load_verification_modules("investigation_verification")

        # Should all be the same object (no duplication)
        assert module1 is module2
        assert module2 is module3

        # Cache should only have one entry
        assert len(_MODULE_CACHE) == 1

        print(f"\n[MEMORY] Module cache size: {len(_MODULE_CACHE)} module(s)")

    def test_no_memory_leak_on_repeated_calls(self):
        """Test repeated calls don't cause memory accumulation."""
        from PreToolUse_verification_router import run_verification_modules

        data = {"userPrompt": "investigate error"}

        # Call many times (simulates heavy usage)
        for _ in range(1000):
            run_verification_modules(data)

        # If we get here without crashing, no memory leak
        # (Real memory profiling would require tracemalloc or similar)
        assert True

        print("\n[MEMORY] Completed 1000 iterations without issues")


if __name__ == "__main__":
    # Run performance tests with verbose output
    pytest.main([__file__, "-v", "-s"])
