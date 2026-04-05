"""
Rate Limit Tracker - Dynamic worker count adjustment based on feedback.
"""
import logging
from collections.abc import Callable
from threading import Lock
from typing import TypeAlias

JobsCallback: TypeAlias = Callable[[int], None] | None
logger = logging.getLogger(__name__)

class RateLimitTracker:

    def __init__(self, *, start_jobs: int=2, min_jobs: int=1, max_jobs: int=8, success_threshold: int=10, unique_channel_threshold: int=0, penalty_clear_threshold: int=20, on_jobs_changed: JobsCallback=None):
        self._start_jobs = start_jobs
        self.min_jobs = min_jobs
        self.max_jobs = max_jobs
        self._success_threshold = success_threshold
        self._unique_channel_threshold = unique_channel_threshold
        self._penalty_clear_threshold = penalty_clear_threshold
        self._on_jobs_changed = on_jobs_changed
        self._current_jobs = start_jobs
        self._success_count = 0
        self._unique_channels: set[str] = set()
        self._problematic_levels: set[int] = set()
        self._level_success_count: dict[int, int] = {}
        self._lock = Lock()

    @property
    def current_jobs(self) -> int:
        with self._lock:
            return self._current_jobs

    def get_current_jobs(self) -> int:
        return self.current_jobs

    def get_problematic_levels(self) -> set[int]:
        with self._lock:
            return self._problematic_levels.copy()

    def __repr__(self) -> str:
        return f"RateLimitTracker(current={self.current_jobs}, min={self.min_jobs}, max={self.max_jobs})"

    def on_rate_limit(self, channel_id: str, error_msg: str) -> None:
        with self._lock:
            old_jobs = self._current_jobs
            new_jobs = max(self._current_jobs - 1, self.min_jobs)
            if new_jobs != old_jobs:
                self._problematic_levels.add(old_jobs)
                self._current_jobs = new_jobs
                self._notify_change(new_jobs)
                logger.info("Rate limit detected on %s: %s. Decreased workers to %s", channel_id, error_msg, new_jobs)
            self._success_count = 0
            self._unique_channels.clear()
            if old_jobs in self._level_success_count:
                del self._level_success_count[old_jobs]

    def on_success(self, channel_id: str) -> None:
        with self._lock:
            self._unique_channels.add(channel_id)
            self._success_count += 1
            level = self._current_jobs
            self._level_success_count[level] = self._level_success_count.get(level, 0) + 1
            next_level = self._current_jobs + 1
            required_threshold = self._success_threshold
            if next_level in self._problematic_levels:
                required_threshold = self._success_threshold * 2
            if self._success_count >= required_threshold and len(self._unique_channels) >= self._unique_channel_threshold:
                old_jobs = self._current_jobs
                new_jobs = min(self._current_jobs + 1, self.max_jobs)
                if new_jobs != old_jobs:
                    self._current_jobs = new_jobs
                    self._notify_change(new_jobs)
                    logger.info("Success threshold met. Increased workers to %s", new_jobs)
                    if new_jobs in self._problematic_levels:
                        self._problematic_levels.remove(new_jobs)
                    self._success_count = 0
                    self._unique_channels.clear()
            levels_to_remove = []
            for problematic_level in self._problematic_levels:
                total_successes = 0
                for lvl, count in self._level_success_count.items():
                    if lvl <= problematic_level:
                        total_successes += count
                if total_successes >= self._penalty_clear_threshold:
                    levels_to_remove.append(problematic_level)
            for lvl in levels_to_remove:
                self._problematic_levels.remove(lvl)

    def reset(self) -> None:
        with self._lock:
            old_jobs = self._current_jobs
            self._current_jobs = self._start_jobs
            self._success_count = 0
            self._unique_channels.clear()
            self._problematic_levels.clear()
            self._level_success_count.clear()
            if old_jobs != self._start_jobs:
                self._notify_change(self._start_jobs)
            logger.debug("RateLimitTracker reset to %s workers", self._start_jobs)

    def _notify_change(self, new_jobs: int) -> None:
        if self._on_jobs_changed is not None:
            try:
                self._on_jobs_changed(new_jobs)
            except Exception as e:
                logger.exception("Error in rate limit callback: %s", e)
