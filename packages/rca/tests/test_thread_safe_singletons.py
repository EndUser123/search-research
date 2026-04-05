"""Tests for thread-safe singleton initialization (RCA-001-001 fix)."""

import concurrent.futures
import sys
import threading
from pathlib import Path

# Add src to path for imports
_src_dir = Path(__file__).parent.parent / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))


def test_metrics_tracker_thread_safe_singleton():
    """Test that get_metrics_tracker() returns the same instance across threads."""
    from rca.metrics_tracker import get_metrics_tracker

    instances = []
    lock = threading.Lock()

    def get_instance():
        instance = get_metrics_tracker()
        with lock:
            instances.append(instance)

    # Spawn multiple threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_instance) for _ in range(100)]
        concurrent.futures.wait(futures)

    # All instances should be the same
    first = instances[0]
    for instance in instances[1:]:
        assert instance is first, "All threads should get the same singleton instance"


def test_pattern_registry_thread_safe_singleton():
    """Test that get_pattern_registry() returns the same instance across threads."""
    from rca.pattern_registry import get_pattern_registry

    instances = []
    lock = threading.Lock()

    def get_instance():
        instance = get_pattern_registry()
        with lock:
            instances.append(instance)

    # Spawn multiple threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_instance) for _ in range(100)]
        concurrent.futures.wait(futures)

    # All instances should be the same
    first = instances[0]
    for instance in instances[1:]:
        assert instance is first, "All threads should get the same singleton instance"


def test_outcome_recorder_thread_safe_singleton():
    """Test that get_outcome_recorder() returns the same instance across threads."""
    from rca.outcome_recorder import get_outcome_recorder

    instances = []
    lock = threading.Lock()

    def get_instance():
        instance = get_outcome_recorder()
        with lock:
            instances.append(instance)

    # Spawn multiple threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_instance) for _ in range(100)]
        concurrent.futures.wait(futures)

    # All instances should be the same
    first = instances[0]
    for instance in instances[1:]:
        assert instance is first, "All threads should get the same singleton instance"


def test_fix_registry_thread_safe_singleton():
    """Test that get_fix_registry() returns the same instance across threads."""
    from rca.fix_registry import get_fix_registry

    instances = []
    lock = threading.Lock()

    def get_instance():
        instance = get_fix_registry()
        with lock:
            instances.append(instance)

    # Spawn multiple threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_instance) for _ in range(100)]
        concurrent.futures.wait(futures)

    # All instances should be the same
    first = instances[0]
    for instance in instances[1:]:
        assert instance is first, "All threads should get the same singleton instance"


def test_session_budget_thread_safe_singleton():
    """Test that get_session_budget() returns the same instance across threads."""
    from rca.metrics_tracker import get_session_budget

    # Reset the singleton first
    from rca.metrics_tracker import reset_session_budget
    reset_session_budget()

    instances = []
    lock = threading.Lock()

    def get_instance():
        instance = get_session_budget()
        with lock:
            instances.append(instance)

    # Spawn multiple threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(get_instance) for _ in range(100)]
        concurrent.futures.wait(futures)

    # All instances should be the same
    first = instances[0]
    for instance in instances[1:]:
        assert instance is first, "All threads should get the same singleton instance"


def test_singletons_have_lock():
    """Test that each singleton module has a lock for thread safety."""
    import rca.metrics_tracker as mt
    import rca.pattern_registry as pr
    import rca.outcome_recorder as orec
    import rca.fix_registry as fr

    # Check that locks exist
    assert hasattr(mt, '_tracker_lock'), "metrics_tracker should have _tracker_lock"
    assert hasattr(pr, '_registry_lock'), "pattern_registry should have _registry_lock"
    assert hasattr(orec, '_recorder_lock'), "outcome_recorder should have _recorder_lock"
    assert hasattr(fr, '_registry_lock'), "fix_registry should have _registry_lock"

    # Check they are threading.Lock or RLock
    assert isinstance(mt._tracker_lock, (threading.Lock, threading.RLock)), \
        "_tracker_lock should be a threading.Lock or RLock"
    assert isinstance(pr._registry_lock, (threading.Lock, threading.RLock)), \
        "_registry_lock should be a threading.Lock or RLock"
    assert isinstance(orec._recorder_lock, (threading.Lock, threading.RLock)), \
        "_recorder_lock should be a threading.Lock or RLock"
    assert isinstance(fr._registry_lock, (threading.Lock, threading.RLock)), \
        "_registry_lock should be a threading.Lock or RLock"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
