"""
Thread-safe manager tests (TDD Phase 1: RED).
"""

from threading import Thread
import time
import pytest

try:
    from yt_fts.download.thread_safe_manager import ThreadSafeManager
except ImportError:
    pytest.skip("ThreadSafeManager not implemented yet", allow_module_level=True)


class TestThreadSafeManagerInstantiation:
    def test_can_instantiate(self):
        manager = ThreadSafeManager()
        assert manager is not None

    def test_has_locks_dict(self):
        manager = ThreadSafeManager()
        assert hasattr(manager, "_locks")
        assert manager._locks == {}

    def test_has_lock_for_locks(self):
        manager = ThreadSafeManager()
        assert hasattr(manager, "_lock_for_locks")


class TestGetLock:
    def test_returns_lock_object(self):
        manager = ThreadSafeManager()
        lock = manager.get_lock("test_lock")
        import threading
        assert isinstance(lock, threading.Lock)

    def test_same_name_returns_same_lock(self):
        manager = ThreadSafeManager()
        lock1 = manager.get_lock("test_lock")
        lock2 = manager.get_lock("test_lock")
        assert lock1 is lock2

    def test_different_names_return_different_locks(self):
        manager = ThreadSafeManager()
        lock1 = manager.get_lock("lock_a")
        lock2 = manager.get_lock("lock_b")
        assert lock1 is not lock2


class TestSafeIncrement:
    def test_increment_from_zero(self):
        manager = ThreadSafeManager()
        result = manager.safe_increment("test_counter", value=1)
        assert result == 1

    def test_multiple_increments(self):
        manager = ThreadSafeManager()
        manager.safe_increment("test_counter", value=5)
        result = manager.safe_increment("test_counter", value=3)
        assert result == 8

    def test_thread_safety_with_concurrent_access(self):
        manager = ThreadSafeManager()
        num_threads = 100
        increments_per_thread = 100
        
        def increment_many():
            for _ in range(increments_per_thread):
                manager.safe_increment("race_counter")
        
        threads = []
        for _ in range(num_threads):
            t = Thread(target=increment_many)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        final_value = manager.safe_increment("race_counter", value=0)
        expected = num_threads * increments_per_thread
        assert final_value == expected


class TestSafeUpdateDict:
    def test_update_single_key(self):
        manager = ThreadSafeManager()
        
        def update_func(d):
            d["key1"] = "value1"
        
        result = manager.safe_update_dict("test_dict", update_func)
        assert result["key1"] == "value1"

    def test_thread_safety_with_concurrent_updates(self):
        manager = ThreadSafeManager()
        num_threads = 50
        
        def add_entry(thread_id):
            def update_func(d):
                d[f"thread_{thread_id}"] = f"value_{thread_id}"
            manager.safe_update_dict("concurrent_dict", update_func)
        
        threads = []
        for i in range(num_threads):
            t = Thread(target=add_entry, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        result = manager.safe_update_dict("concurrent_dict", lambda d: d)
        assert len(result) == num_threads
