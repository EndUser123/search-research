"""Backend Health Registry - Track success/failure with exponential backoff."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .terminal_id import canonical_terminal_id

HealthStatus = Literal["ready", "degraded", "down"]


@dataclass
class BackendHealth:
    """Health status for a single backend."""

    name: str
    status: HealthStatus
    consecutive_failures: int
    last_error: str | None
    next_retry: float

    def should_retry(self) -> bool:
        """Check if enough time has passed to retry."""
        return time.time() >= self.next_retry

    def record_success(self) -> None:
        """Reset failure count on success."""
        self.consecutive_failures = 0
        self.status = "ready"
        self.last_error = None

    def record_failure(self, error: str) -> None:
        """Record failure with exponential backoff."""
        self.consecutive_failures += 1
        self.last_error = error

        # Calculate backoff: 5s -> 10s -> 20s -> 40s -> 80s -> 160s -> 300s max
        backoffs = [5, 10, 20, 40, 80, 160, 300]
        idx = min(self.consecutive_failures - 1, len(backoffs) - 1)
        backoff_seconds = backoffs[idx]

        self.next_retry = time.time() + backoff_seconds

        if self.consecutive_failures >= 3:
            self.status = "down"
        else:
            self.status = "degraded"


class BackendHealthRegistry:
    """Registry for tracking backend health with thread-safe operations.

    Uses a class-level registry keyed by terminal_id so all instances with
    the same terminal_id share health state. Different terminals get isolated
    state. No singleton — every BackendHealthRegistry() is a proper instance.
    """

    _lock = threading.Lock()
    # Class-level registry: terminal_id -> {"health": dict, "lock": Lock, "storage_path": Path}
    _registry: dict[str, dict] = {}

    def __init__(self):
        self._terminal_id = canonical_terminal_id()

        with BackendHealthRegistry._lock:
            if self._terminal_id not in BackendHealthRegistry._registry:
                storage_path = (
                    Path.home()
                    / ".search-research"
                    / f"backend_health_{self._terminal_id}.json"
                )
                storage_path.parent.mkdir(parents=True, exist_ok=True)
                BackendHealthRegistry._registry[self._terminal_id] = {
                    "health": {},
                    "lock": threading.Lock(),
                    "storage_path": storage_path,
                }
            reg = BackendHealthRegistry._registry[self._terminal_id]
            self._health: dict[str, BackendHealth] = reg["health"]
            self._lock = reg["lock"]
            self._storage_path: Path = reg["storage_path"]

        self._load_state()

    def get_status(self, backend: str) -> BackendHealth | None:
        """Get health status for a specific backend."""
        with self._lock:
            return self._health.get(backend)

    def get_all_status(self) -> dict[str, BackendHealth]:
        """Get status of all backends."""
        with self._lock:
            return dict(self._health)

    def is_available(self, backend: str) -> bool:
        """
        Check if backend is available for search.

        Returns:
            True if backend is ready or degraded (can retry)
            False if backend is down (within backoff period)
        """
        health = self.get_status(backend)
        if health is None:
            return True  # Unknown backend, assume available

        # Always allow retry if backoff period passed
        if health.status == "down" and health.should_retry():
            return True

        return health.status in ("ready", "degraded")

    def record_result(self, backend: str, success: bool, error: str | None = None) -> None:
        """Record backend result and update health status."""
        with self._lock:
            if backend not in self._health:
                self._health[backend] = BackendHealth(
                    name=backend,
                    status="ready",
                    consecutive_failures=0,
                    last_error=None,
                    next_retry=0.0,
                )

            health = self._health[backend]
            if success:
                health.record_success()
            else:
                health.record_failure(error or "Unknown error")

            self._save_state()

    def _load_state(self) -> None:
        """Load health state from disk."""
        if not self._storage_path.exists():
            return

        try:
            data = json.loads(self._storage_path.read_text())
            for name, health_data in data.items():
                self._health[name] = BackendHealth(**health_data)
        except Exception:
            pass  # Start fresh on load error

    def _save_state(self) -> None:
        """Save health state to disk."""
        try:
            data = {name: asdict(health) for name, health in self._health.items()}
            self._storage_path.write_text(json.dumps(data, indent=2))
        except Exception:
            pass  # Don't fail if save fails

    def _reset(self) -> None:
        """Reset all state. For testing only."""
        with self._lock:
            self._health.clear()
        tid = self._terminal_id
        if self._storage_path.exists():
            try:
                self._storage_path.unlink()
            except Exception:
                pass
        with BackendHealthRegistry._lock:
            if tid in BackendHealthRegistry._registry:
                del BackendHealthRegistry._registry[tid]
