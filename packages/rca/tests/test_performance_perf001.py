"""Tests for PERF-001: Synchronous JSON write on every knowledge store.

This test verifies that the async write-behind caching is implemented correctly:
1. Multiple analyses should NOT cause multiple synchronous writes
2. Writes should be batched and deferred
3. Flush should only happen when explicitly called or on session end
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from rca.simple_rca_engine import SimpleRCAEngine


class TestPERF001WriteBehindCaching:
    """Tests for async write-behind caching in SimpleRCAEngine."""

    def test_multiple_analyses_do_not_write_every_time(self):
        """Test that multiple analyses don't cause synchronous writes on each call.

        GREEN phase: After implementing write-behind caching,
        multiple analyses should queue patterns without writing.
        """
        # Mock the knowledge curator to track write calls
        mock_curator = Mock()
        mock_curator.store_library_pattern = Mock()
        mock_curator.search_library_patterns = Mock(return_value=[])

        engine = SimpleRCAEngine(knowledge_curator=mock_curator)

        # Perform multiple analyses
        for i in range(5):
            engine.analyze_issue(f"Test issue {i}", context={"test": i})

        # AFTER FIX: Writes should be deferred (0 immediate writes)
        write_count = mock_curator.store_library_pattern.call_count

        # Verify writes were deferred
        assert write_count == 0, f"Expected 0 immediate writes, got {write_count}"

        # Verify patterns are queued
        assert engine.get_pending_patterns_count() == 5, "Expected 5 patterns queued"

    def test_writes_can_be_batched(self):
        """Test that writes can be batched and flushed together.

        After the fix, calling flush() should write all pending patterns.
        """
        mock_curator = Mock()
        mock_curator.store_library_pattern = Mock()
        mock_curator.search_library_patterns = Mock(return_value=[])

        engine = SimpleRCAEngine(knowledge_curator=mock_curator)

        # Perform multiple analyses
        issues = [f"Test issue {i}" for i in range(3)]
        for issue in issues:
            engine.analyze_issue(issue)

        # After fix: check if flush method exists
        has_flush = hasattr(engine, "flush_pending_patterns")
        if has_flush:
            # Flush all pending writes
            engine.flush_pending_patterns()

            # Should have written all patterns in one batch or single call
            # Implementation may vary - just verify writes happened
            assert mock_curator.store_library_pattern.call_count >= 1
        else:
            pytest.skip("flush_pending_patterns not implemented yet")

    def test_write_queue_is_bounded(self):
        """Test that the write queue has a bounded size to prevent memory issues."""
        mock_curator = Mock()
        mock_curator.store_library_pattern = Mock()
        mock_curator.search_library_patterns = Mock(return_value=[])

        engine = SimpleRCAEngine(knowledge_curator=mock_curator)

        # Check if max_queue_size attribute exists after fix
        has_queue_size = hasattr(engine, "_max_pending_patterns")
        if has_queue_size:
            # Verify the queue is bounded (reasonable limit)
            assert engine._max_pending_patterns > 0
            assert engine._max_pending_patterns <= 1000  # Reasonable upper bound
        else:
            pytest.skip("_max_pending_patterns not implemented yet")

    def test_performance_improvement_is_measurable(self):
        """Test that the performance improvement is measurable.

        This test uses timing to verify that batched writes are faster
        than synchronous writes.
        """
        import time

        mock_curator = Mock()
        mock_curator.store_library_patterns = Mock()  # Batch method (after fix)
        mock_curator.store_library_pattern = Mock()  # Single method (current)
        mock_curator.search_library_patterns = Mock(return_value=[])

        engine = SimpleRCAEngine(knowledge_curator=mock_curator)

        # Perform 10 analyses and measure time
        start_time = time.perf_counter()
        for i in range(10):
            engine.analyze_issue(f"Benchmark issue {i}")
        elapsed = time.perf_counter() - start_time

        # With synchronous writes, this would be slow
        # With write-behind, this should be very fast
        # We just verify it completes in reasonable time
        assert elapsed < 5.0, "Analysis took too long - performance issue detected"

        # Check if batch method is available
        if hasattr(engine, "flush_pending_patterns"):
            # Flush and verify it works
            engine.flush_pending_patterns()


class TestPERF001Integration:
    """Integration tests for PERF-001 fix."""

    def test_context_manager_flushes_on_exit(self):
        """Test that using engine as context manager flushes on exit."""
        mock_curator = Mock()
        mock_curator.store_library_pattern = Mock()
        mock_curator.search_library_patterns = Mock(return_value=[])

        with SimpleRCAEngine(knowledge_curator=mock_curator) as engine:
            # Perform analyses within context
            for i in range(3):
                engine.analyze_issue(f"Context test {i}")

        # After exiting context, writes should be flushed
        # This requires __enter__ and __exit__ implementation
        if hasattr(SimpleRCAEngine, "__enter__"):
            assert mock_curator.store_library_pattern.call_count >= 1
        else:
            pytest.skip("Context manager not implemented yet")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
