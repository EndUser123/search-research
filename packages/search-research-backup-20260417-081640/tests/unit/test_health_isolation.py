"""TDD RED: BackendHealthRegistry terminal_id isolation.

Tests that BackendHealthRegistry instances with different terminal_ids do not
share health state entries. Uses CLAUDE_TERMINAL_ID env var to simulate
different terminals within a single test process.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from core.backend_health import BackendHealthRegistry

# Unique storage dir per test to isolate persistent state
TEST_STORAGE_DIR = Path.home() / ".search-research" / "health_isolation_test"


class TestHealthIsolation:
    """Two BackendHealthRegistry instances with different terminal_ids must not share state."""

    def setup_method(self):
        """Reset registry and clear all test storage files before each test."""
        BackendHealthRegistry._registry.clear()
        if TEST_STORAGE_DIR.exists():
            for f in TEST_STORAGE_DIR.iterdir():
                try:
                    f.unlink()
                except Exception:
                    pass
        else:
            TEST_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clear registry and wipe all test storage files."""
        BackendHealthRegistry._registry.clear()
        if TEST_STORAGE_DIR.exists():
            for f in TEST_STORAGE_DIR.iterdir():
                try:
                    f.unlink()
                except Exception:
                    pass

    def _make_registry(self, terminal_id: str) -> BackendHealthRegistry:
        """Create a BackendHealthRegistry with an isolated storage file."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": terminal_id}):
            reg = BackendHealthRegistry()
            reg._storage_path = TEST_STORAGE_DIR / f"backend_health_{terminal_id}.json"
        return reg

    def test_different_terminal_ids_have_separate_health_state(self):
        """Backend marked down in terminal A is still 'ready' in terminal B."""
        reg_a = self._make_registry("term-health-a")
        reg_a.record_result("cds_backend", success=False, error="Connection refused")

        reg_b = self._make_registry("term-health-b")
        status_b = reg_b.get_status("cds_backend")
        is_available_b = status_b is None or status_b.status != "down"
        assert is_available_b, (
            f"Terminal B must NOT see Terminal A's backend failures. "
            f"Got status={status_b.status if status_b else 'None'}. "
            f"reg_a._terminal_id={reg_a._terminal_id}, "
            f"reg_b._terminal_id={reg_b._terminal_id}"
        )

    def test_success_recorded_in_terminal_a_not_visible_in_terminal_b(self):
        """Backend success in terminal A doesn't affect terminal B's state."""
        reg_a = self._make_registry("term-succ-a")
        reg_a.record_result("grep_backend", success=True)

        reg_b = self._make_registry("term-succ-b")
        status_b = reg_b.get_status("grep_backend")
        assert status_b is None, (
            f"Terminal B must NOT see Terminal A's backend successes. "
            f"Got {status_b} for grep_backend. Expected None (unknown backend)."
        )

    def test_multiple_backends_isolated_per_terminal(self):
        """Three backends tracked independently per terminal."""
        reg = self._make_registry("term-multi-xyz")
        reg.record_result("cds", success=False, error="CDS down")
        reg.record_result("grep", success=True)
        reg.record_result("cks", success=False, error="CKS down")

        reg2 = self._make_registry("term-other-xyz")
        for backend in ("cds", "grep", "cks"):
            status = reg2.get_status(backend)
            assert status is None, (
                f"Terminal must have isolated health state. "
                f"Backend {backend} returned {status}, expected None."
            )

    def test_same_terminal_reuses_health_state(self):
        """Same terminal getting status twice returns same BackendHealth object."""
        reg1 = self._make_registry("term-same-xyz")
        reg1.record_result("test_backend", success=False, error="Test error")

        reg2 = self._make_registry("term-same-xyz")
        status = reg2.get_status("test_backend")
        assert status is not None, "Same terminal should have health record"
        assert status.consecutive_failures == 1, (
            f"Same terminal should return persisted health. "
            f"Got failures={status.consecutive_failures}, expected 1."
        )

    def test_terminal_id_stored_on_instance(self):
        """BackendHealthRegistry stores its terminal_id on self._terminal_id."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "my-health-xyz"}):
            reg = BackendHealthRegistry()
            assert hasattr(reg, "_terminal_id"), (
                "BackendHealthRegistry must have _terminal_id attribute"
            )
            assert reg._terminal_id == "my-health-xyz", (
                f"Expected _terminal_id='my-health-xyz', got '{reg._terminal_id}'"
            )

    def test_is_available_respects_terminal_isolation(self):
        """is_available returns correct result per terminal's view of backend."""
        reg_a = self._make_registry("term-avail-a")
        reg_a.record_result("backenda", success=False, error="Failed")

        reg_b = self._make_registry("term-avail-b")
        assert reg_b.is_available("backenda"), (
            "Unknown backend in terminal B should be available"
        )

        status_a = reg_a.get_status("backenda")
        if status_a and status_a.status == "down":
            assert not reg_a.is_available("backenda"), (
                "Down backend in terminal A should not be available during backoff"
            )