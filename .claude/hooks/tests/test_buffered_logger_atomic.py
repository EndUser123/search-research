"""
Tests for atomic log writes in buffered_logger.py.

This test file verifies that BufferedLogger performs atomic writes
that are safe for concurrent access from multiple PROCESSES (not just threads).

The key distinction: threading.Lock() works within a process but fails
across processes. FileLock from portalocker works across both.

Run with: pytest .claude/hooks/tests/test_buffered_logger_atomic.py -v
"""

from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path as PathLib

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(PathLib(__file__).parent.parent))

# Try to import - will fail in RED phase
try:
    from buffered_logger import BufferedLogger
except (ImportError, ModuleNotFoundError):
    BufferedLogger = None
    pytestmark = pytest.mark.skip("BufferedLogger not available")


@pytest.mark.skipif(BufferedLogger is None, reason="BufferedLogger not implemented")
def test_concurrent_log_writes_no_corruption(tmp_path):
    """
    Test that concurrent log writes don't corrupt the file (within process).

    This test verifies thread safety using the existing threading.Lock().
    Note: This validates thread-safety, not cross-process safety.
    Cross-process safety requires FileLock and is validated separately.

    Given: A BufferedLogger with buffer_size=1 and flush_interval=0.1
    When: 5 threads each write 100 log entries concurrently
    Then: All 500 entries should be valid JSON with no data loss
    """
    log_file = tmp_path / "test.jsonl"
    logger = BufferedLogger(
        log_file,
        buffer_size=1,
        flush_interval=0.1
    )
    logger.start()

    def write_logs(thread_id):
        for i in range(100):
            logger.log({"thread": thread_id, "seq": i})
            time.sleep(0.001)

    threads = [threading.Thread(target=write_logs, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    logger.shutdown()

    # Verify all entries are valid JSON
    entries = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))  # Should not raise

    # Should have exactly 500 entries (5 threads * 100 entries)
    assert len(entries) == 500, f"Expected 500 entries, got {len(entries)}"


@pytest.mark.skipif(BufferedLogger is None, reason="BufferedLogger not implemented")
def test_concurrent_writes_maintain_sequence_per_thread(tmp_path):
    """
    Test that each thread's writes maintain sequence order.

    This verifies that within each thread, sequence numbers are monotonic.
    Inter-thread ordering is not guaranteed, but intra-thread ordering must be preserved.

    Given: Multiple threads writing with sequence numbers
    When: Threads write concurrently
    Then: Each thread's sequence numbers should be 0-99 in order
    """
    log_file = tmp_path / "test_sequence.jsonl"
    logger = BufferedLogger(
        log_file,
        buffer_size=1,
        flush_interval=0.1
    )
    logger.start()

    def write_logs(thread_id):
        for i in range(100):
            logger.log({"thread": thread_id, "seq": i})
            time.sleep(0.001)

    threads = [threading.Thread(target=write_logs, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    logger.shutdown()

    # Collect entries by thread
    entries_by_thread: dict[int, list[int]] = {i: [] for i in range(5)}
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                thread_id = entry.get("thread")
                seq = entry.get("seq")
                if thread_id is not None and seq is not None:
                    entries_by_thread[thread_id].append(seq)

    # Verify each thread has exactly 100 entries in sequence
    for thread_id, sequences in entries_by_thread.items():
        assert len(sequences) == 100, f"Thread {thread_id} has {len(sequences)} entries, expected 100"
        assert sequences == list(range(100)), f"Thread {thread_id} sequence is not 0-99 in order"


@pytest.mark.skipif(BufferedLogger is None, reason="BufferedLogger not implemented")
def test_buffered_logger_has_atomic_write_method(tmp_path):
    """
    Verify that BufferedLogger uses FileLock for atomic writes.

    This test checks for the presence of FileLock-based atomic write behavior
    by examining the _write_to_disk method implementation.
    """
    import inspect

    from buffered_logger import BufferedLogger

    # Check that _write_to_disk exists
    assert hasattr(BufferedLogger, '_write_to_disk'), "BufferedLogger must have _write_to_disk method"

    # Get source code of _write_to_disk
    source = inspect.getsource(BufferedLogger._write_to_disk)

    # Check if it uses FileLock (the GREEN phase implementation will have this)
    uses_file_lock = 'FileLock' in source or 'file_lock' in source or 'portalocker' in source

    if not uses_file_lock:
        pytest.fail(
            "BufferedLogger._write_to_disk does not use FileLock for atomic writes. "
            "Current implementation is only thread-safe, not process-safe. "
            "Add 'from __lib.file_lock import FileLock' and wrap the write in 'with FileLock(...):'"
        )


@pytest.mark.skipif(BufferedLogger is None, reason="BufferedLogger not implemented")
def test_buffered_logger_imports():
    """
    Characterization test: Verify BufferedLogger module can be imported.
    """
    from buffered_logger import BufferedLogger

    assert BufferedLogger is not None
    assert hasattr(BufferedLogger, 'log')
    assert hasattr(BufferedLogger, '_write_to_disk')
