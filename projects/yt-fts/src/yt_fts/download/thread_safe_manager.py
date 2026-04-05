"""
ThreadSafeManager - Centralized thread-safe operations for download subsystem.

Consolidates 76 individual threading.Lock() instances across the download subsystem
into a single, well-tested manager.
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Any


class ThreadSafeManager:
    """Centralized thread-safe operations for download subsystem.
    
    Provides a unified interface for thread-safe operations:
    - Named lock management (get_lock)
    - Thread-safe counter increments (safe_increment)
    - Thread-safe dictionary updates (safe_update_dict)
    
    This replaces scattered threading.Lock() instances throughout the codebase,
    making it easier to test for thread-safety and maintain consistent behavior.
    
    Example:
        manager = ThreadSafeManager()
        
        # Use named locks
        with manager.get_lock("download_worker"):
            # Critical section protected by lock
            pass
        
        # Thread-safe counter
        count = manager.safe_increment("downloads_completed")
        
        # Thread-safe dict update
        result = manager.safe_update_dict("channel_stats", lambda d: d.update({"count": 1}))
    """

    def __init__(self) -> None:
        """Initialize the ThreadSafeManager."""
        self._locks: dict[str, threading.Lock] = {}
        self._lock_for_locks = threading.Lock()
        self._counters: dict[str, int] = {}
        self._dicts: dict[str, dict[str, Any]] = {}

    def get_lock(self, name: str) -> threading.Lock:
        """Get or create a named lock.
        
        Thread-safe. Returns the same lock instance for the same name.
        Uses double-checked locking pattern for efficiency.
        
        Args:
            name: Unique identifier for this lock (e.g., "download_worker", "progress_update")
        
        Returns:
            threading.Lock instance for the given name
        """
        # First check without lock (fast path)
        if name not in self._locks:
            # Acquire lock to create new lock
            with self._lock_for_locks:
                # Double-check inside lock (another thread might have created it)
                if name not in self._locks:
                    self._locks[name] = threading.Lock()
        return self._locks[name]

    def safe_increment(self, counter_name: str, value: int = 1) -> int:
        """Thread-safe counter increment.
        
        Increments a named counter by the specified value.
        Creates counter if it doesn't exist.
        
        Args:
            counter_name: Name of the counter to increment
            value: Amount to increment by (default: 1)
        
        Returns:
            New counter value after increment
        """
        lock = self.get_lock(f"counter_{counter_name}")
        with lock:
            if counter_name not in self._counters:
                self._counters[counter_name] = 0
            self._counters[counter_name] += value
            return self._counters[counter_name]

    def safe_update_dict(self, dict_name: str, update_func: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        """Thread-safe dictionary update.
        
        Executes update_func while holding a lock on the named dictionary.
        Creates dictionary if it doesn't exist.
        
        Args:
            dict_name: Name of the dictionary to update
            update_func: Function that takes the dict and modifies it
        
        Returns:
            The dictionary after update_func has been applied
        """
        lock = self.get_lock(f"dict_{dict_name}")
        with lock:
            if dict_name not in self._dicts:
                self._dicts[dict_name] = {}
            update_func(self._dicts[dict_name])
            return self._dicts[dict_name]
