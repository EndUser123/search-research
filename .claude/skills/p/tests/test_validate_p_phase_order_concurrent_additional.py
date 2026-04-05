#!/usr/bin/env python3
"""
Additional concurrent marker access tests for validate_p_phase_order.py

These tests ADD to the existing TestMultiTerminalSafety class to cover:
1. Concurrent marker CREATION (multiple threads creating same marker)
2. Concurrent marker DELETION (if applicable)
3. Concurrent marker READ during WRITE
4. Concurrent marker WRITE during READ
5. Stress test with more threads (currently 10, test with 50+)

Run with: pytest tests/test_validate_p_phase_order_concurrent_additional.py -v
"""

import tempfile
import threading
import time
from pathlib import Path

import pytest

# Add lib directory to path
LIB_DIR = Path(__file__).parent.parent / "hooks"
import sys

sys.path.insert(0, str(LIB_DIR))

from validate_p_phase_order import marker_exists


class TestMultiTerminalSafetyAdditional:
    """
    Additional tests for multi-terminal safety of marker operations.

    These tests should be added to the existing TestMultiTerminalSafety class
    in test_validate_p_phase_order.py to enhance concurrent access coverage.
    """

    def test_concurrent_marker_creation_same_marker(self):
        """
        Test concurrent marker CREATION - multiple threads creating same marker.

        Multiple terminals might try to create the same phase completion marker
        simultaneously (e.g., multiple P1 completions trying to write p1-complete.marker).

        Expected behavior: All writes should succeed, final marker should be valid.
        File system write_text() should be atomic at the filesystem level.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            creation_count = [0]
            errors = []
            successful_writes = []

            def create_marker(thread_id: int):
                """Thread that attempts to create the marker."""
                try:
                    for i in range(10):
                        timestamp = f"2026-03-09T12:00:{thread_id:02d}{i:02d}"
                        content = f"Phase 1 completed at {timestamp}\n"
                        marker.write_text(content)
                        creation_count[0] += 1
                        successful_writes.append((thread_id, content))
                        time.sleep(0.0001)  # Small delay to increase collision chance
                except Exception as e:
                    errors.append((thread_id, type(e).__name__, str(e)))

            # Start many threads trying to create same marker
            threads = []
            num_threads = 20
            for i in range(num_threads):
                t = threading.Thread(target=create_marker, args=(i,))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred during concurrent creation: {errors}"

            # All writes should have completed (200 total: 20 threads * 10 writes)
            assert creation_count[0] == num_threads * 10, \
                f"Expected {num_threads * 10} writes, got {creation_count[0]}"

            # Final marker should exist and be valid
            assert marker.exists(), "Marker should exist after concurrent creation"
            assert marker_exists(marker, expected_phase=1) is True, \
                "Final marker should be valid after concurrent creation"

            # Marker should have one of the written contents
            content = marker.read_text()
            assert content.startswith("Phase 1 completed at"), \
                f"Marker should have valid content, got: {content}"

    def test_concurrent_marker_deletion_during_read(self):
        """
        Test concurrent marker DELETION during read operations.

        One thread deletes while others read - should handle gracefully.
        Marker operations should be safe even if marker is deleted mid-operation.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            # Create initial marker
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            read_results = []
            delete_complete = threading.Event()
            errors = []

            def read_marker():
                """Thread that reads the marker multiple times."""
                try:
                    for i in range(20):
                        exists = marker.exists()
                        if exists:
                            valid = marker_exists(marker, expected_phase=1)
                            read_results.append((i, exists, valid))
                        else:
                            read_results.append((i, False, False))
                        time.sleep(0.002)
                except Exception as e:
                    errors.append(("reader", type(e).__name__, str(e)))

            def delete_marker():
                """Thread that deletes the marker mid-operation."""
                try:
                    # Wait a bit to let reads start
                    time.sleep(0.02)
                    marker.unlink()
                    delete_complete.set()
                    # Recreate marker to test read-after-delete
                    time.sleep(0.03)
                    marker.write_text("Phase 1 completed at 2026-03-09T12:00:01\n")
                except Exception as e:
                    errors.append(("deleter", type(e).__name__, str(e)))

            # Start both threads
            reader = threading.Thread(target=read_marker)
            deleter = threading.Thread(target=delete_marker)
            reader.start()
            deleter.start()

            # Wait for completion
            reader.join()
            deleter.join()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # Should have read results both before and after deletion
            assert len(read_results) == 20, f"Expected 20 reads, got {len(read_results)}"

            # Some reads should have found the marker (before deletion or after recreation)
            found_marker = any(exists for _, exists, _ in read_results)
            assert found_marker, "Should have found marker at least once"

            # Some reads should have not found the marker (during deletion window)
            missing_marker = any(not exists for _, exists, _ in read_results)
            assert missing_marker, "Should have missed marker at least once during deletion"

            # Final marker should be valid (recreated after deletion)
            assert marker_exists(marker, expected_phase=1) is True

    def test_concurrent_read_during_write_stress(self):
        """
        Test concurrent marker READ during WRITE with high contention.

        Stress test: 50 reader threads + 5 writer threads all accessing same marker.
        This simulates heavy multi-terminal usage.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            # Create initial marker
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            read_count = [0]
            write_count = [0]
            read_results = []
            errors = []

            def read_marker(thread_id: int):
                """Thread that reads the marker multiple times."""
                try:
                    for _ in range(50):
                        result = marker_exists(marker, expected_phase=1)
                        read_results.append((thread_id, result))
                        read_count[0] += 1
                        time.sleep(0.0001)
                except Exception as e:
                    errors.append((f"reader-{thread_id}", type(e).__name__, str(e)))

            def write_marker(thread_id: int):
                """Thread that writes to the marker multiple times."""
                try:
                    for i in range(10):
                        timestamp = f"2026-03-09T12:{thread_id:02d}:{i:02d}"
                        marker.write_text(f"Phase 1 completed at {timestamp}\n")
                        write_count[0] += 1
                        time.sleep(0.001)
                except Exception as e:
                    errors.append((f"writer-{thread_id}", type(e).__name__, str(e)))

            # Start 50 reader threads
            reader_threads = []
            for i in range(50):
                t = threading.Thread(target=read_marker, args=(i,))
                reader_threads.append(t)
                t.start()

            # Start 5 writer threads
            writer_threads = []
            for i in range(5):
                t = threading.Thread(target=write_marker, args=(i,))
                writer_threads.append(t)
                t.start()

            # Wait for all threads
            for t in reader_threads:
                t.join()
            for t in writer_threads:
                t.join()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # All operations should have completed
            expected_reads = 50 * 50  # 50 threads * 50 reads
            expected_writes = 5 * 10   # 5 threads * 10 writes
            assert read_count[0] == expected_reads, \
                f"Expected {expected_reads} reads, got {read_count[0]}"
            assert write_count[0] == expected_writes, \
                f"Expected {expected_writes} writes, got {write_count[0]}"

            # Most reads should have returned True, but some may return False
            # during write operations (reading empty file mid-write)
            # This is expected behavior - the TOCTOU fix ensures we handle this gracefully
            true_count = sum(1 for _, result in read_results if result is True)
            false_count = sum(1 for _, result in read_results if result is False)
            success_rate = (true_count / len(read_results)) * 100

            # We expect at least 90% success rate (reads returning True)
            # Some False results are OK - they represent transient reads during writes
            assert success_rate >= 90.0, \
                f"Expected at least 90% success rate, got {success_rate:.1f}% " \
                f"({true_count} True, {false_count} False)"

            # Final marker should be valid
            assert marker_exists(marker, expected_phase=1) is True

    def test_concurrent_write_during_read_stress(self):
        """
        Test concurrent marker WRITE during READ with high contention.

        Stress test: 5 reader threads + 50 writer threads (write-heavy).
        Tests that marker validation doesn't break under heavy write load.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            # Create initial marker
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            read_count = [0]
            write_count = [0]
            read_results = []
            errors = []

            def read_marker(thread_id: int):
                """Thread that reads and validates the marker."""
                try:
                    for _ in range(100):
                        # Full validation check (what the hook actually does)
                        exists = marker.exists()
                        if exists:
                            valid = marker_exists(marker, expected_phase=1)
                            read_results.append((thread_id, valid))
                        else:
                            read_results.append((thread_id, False))
                        read_count[0] += 1
                        time.sleep(0.0001)
                except Exception as e:
                    errors.append((f"reader-{thread_id}", type(e).__name__, str(e)))

            def write_marker(thread_id: int):
                """Thread that writes to the marker."""
                try:
                    for i in range(5):
                        timestamp = f"2026-03-09T13:{thread_id:02d}:{i:02d}"
                        marker.write_text(f"Phase 1 completed at {timestamp}\n")
                        write_count[0] += 1
                        time.sleep(0.0002)
                except Exception as e:
                    errors.append((f"writer-{thread_id}", type(e).__name__, str(e)))

            # Start 5 reader threads
            reader_threads = []
            for i in range(5):
                t = threading.Thread(target=read_marker, args=(i,))
                reader_threads.append(t)
                t.start()

            # Start 50 writer threads
            writer_threads = []
            for i in range(50):
                t = threading.Thread(target=write_marker, args=(i,))
                writer_threads.append(t)
                t.start()

            # Wait for all threads
            for t in reader_threads:
                t.join()
            for t in writer_threads:
                t.join()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # All operations should have completed
            expected_reads = 5 * 100   # 5 threads * 100 reads
            expected_writes = 50 * 5   # 50 threads * 5 writes
            assert read_count[0] == expected_reads, \
                f"Expected {expected_reads} reads, got {read_count[0]}"
            assert write_count[0] == expected_writes, \
                f"Expected {expected_writes} writes, got {write_count[0]}"

            # Most reads should have found marker valid, but some may return False
            # during heavy write load (reading empty file mid-write)
            # This is expected behavior - the TOCTOU fix ensures we handle this gracefully
            true_count = sum(1 for _, result in read_results if result is True)
            false_count = sum(1 for _, result in read_results if result is False)
            success_rate = (true_count / len(read_results)) * 100

            # We expect at least 90% success rate (reads returning True)
            # Some False results are OK - they represent transient reads during writes
            assert success_rate >= 90.0, \
                f"Expected at least 90% success rate, got {success_rate:.1f}% " \
                f"({true_count} True, {false_count} False)"

            # Final marker should be valid
            assert marker_exists(marker, expected_phase=1) is True

    def test_concurrent_marker_creation_different_phases(self):
        """
        Test concurrent marker CREATION for different phase markers.

        Multiple terminals completing different phases simultaneously
        (e.g., one creates p1-complete.marker, another creates p2-complete.marker).
        Should not interfere with each other.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)

            # Create multiple phase markers
            phase_markers = {
                1: state_dir / "p1-complete.marker",
                2: state_dir / "p2-complete.marker",
                3: state_dir / "p3-complete.marker",
            }

            creation_count = {1: 0, 2: 0, 3: 0}
            errors = []

            def create_marker(phase: int, thread_id: int):
                """Thread that creates a specific phase marker."""
                try:
                    marker = phase_markers[phase]
                    for i in range(20):
                        timestamp = f"2026-03-09T14:{phase}:{thread_id:02d}{i:02d}"
                        marker.write_text(f"Phase {phase} completed at {timestamp}\n")
                        creation_count[phase] += 1
                        time.sleep(0.0001)
                except Exception as e:
                    errors.append((f"phase{phase}-thread{thread_id}", type(e).__name__, str(e)))

            # Create 10 threads per phase (30 total)
            threads = []
            for phase in [1, 2, 3]:
                for i in range(10):
                    t = threading.Thread(target=create_marker, args=(phase, i))
                    threads.append(t)
                    t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # All writes should have completed per phase
            for phase in [1, 2, 3]:
                expected_writes = 10 * 20  # 10 threads * 20 writes
                assert creation_count[phase] == expected_writes, \
                    f"Phase {phase}: Expected {expected_writes} writes, got {creation_count[phase]}"

            # All markers should exist and be valid
            for phase in [1, 2, 3]:
                marker = phase_markers[phase]
                assert marker.exists(), f"Phase {phase} marker should exist"
                assert marker_exists(marker, expected_phase=phase) is True, \
                    f"Phase {phase} marker should be valid"

    def test_concurrent_access_high_stress_100_threads(self):
        """
        High stress test: 100 threads doing mixed operations.

        Simulates extreme multi-terminal scenario with many concurrent users.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            # Create initial marker
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            operation_count = {"read": 0, "write": 0, "validate": 0}
            errors = []
            validate_results = []

            def read_operation(thread_id: int):
                """Simple read operation."""
                try:
                    for _ in range(20):
                        _ = marker.read_text()
                        operation_count["read"] += 1
                        time.sleep(0.0001)
                except Exception as e:
                    errors.append((f"read-{thread_id}", type(e).__name__, str(e)))

            def write_operation(thread_id: int):
                """Write operation."""
                try:
                    for _ in range(5):
                        timestamp = f"2026-03-09T15:{thread_id:02d}:00"
                        marker.write_text(f"Phase 1 completed at {timestamp}\n")
                        operation_count["write"] += 1
                        time.sleep(0.0002)
                except Exception as e:
                    errors.append((f"write-{thread_id}", type(e).__name__, str(e)))

            def validate_operation(thread_id: int):
                """Validate operation (what the hook does)."""
                try:
                    for _ in range(30):
                        result = marker_exists(marker, expected_phase=1)
                        validate_results.append(result)
                        operation_count["validate"] += 1
                        time.sleep(0.0001)
                except Exception as e:
                    errors.append((f"validate-{thread_id}", type(e).__name__, str(e)))

            # Start 100 threads: 70 readers, 20 writers, 10 validators
            threads = []
            for i in range(70):
                t = threading.Thread(target=read_operation, args=(i,))
                threads.append(t)
                t.start()

            for i in range(20):
                t = threading.Thread(target=write_operation, args=(i,))
                threads.append(t)
                t.start()

            for i in range(10):
                t = threading.Thread(target=validate_operation, args=(i,))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # All operations should have completed
            assert operation_count["read"] == 70 * 20, \
                f"Reads: Expected {70 * 20}, got {operation_count['read']}"
            assert operation_count["write"] == 20 * 5, \
                f"Writes: Expected {20 * 5}, got {operation_count['write']}"
            assert operation_count["validate"] == 10 * 30, \
                f"Validates: Expected {10 * 30}, got {operation_count['validate']}"

            # Most validations should have succeeded, but some may return False
            # during heavy concurrent access (reading empty file mid-write)
            # This is expected behavior - the TOCTOU fix ensures we handle this gracefully
            assert len(validate_results) == 10 * 30, \
                f"Expected {10 * 30} validation results, got {len(validate_results)}"

            true_count = sum(1 for result in validate_results if result is True)
            false_count = sum(1 for result in validate_results if result is False)
            success_rate = (true_count / len(validate_results)) * 100

            # We expect at least 90% success rate (validations returning True)
            # Some False results are OK - they represent transient reads during writes
            assert success_rate >= 90.0, \
                f"Expected at least 90% success rate, got {success_rate:.1f}% " \
                f"({true_count} True, {false_count} False)"

            # Final marker should be valid
            assert marker_exists(marker, expected_phase=1) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
