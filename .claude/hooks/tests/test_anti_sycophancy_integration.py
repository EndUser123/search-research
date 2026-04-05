#!/usr/bin/env python3
"""
E2E integration test for anti-sycophancy system WITHOUT mocks.

Tests actual file I/O, TTL validation (FIX-001), and UUID fallback (FIX-003).

Finding 6 (RISK:9): Mock patches hide real behavior. This test uses real
file operations to catch integration issues that mock-based tests miss.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from pathlib import Path

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# Import the actual hook modules (not mocked)
from StopHook_unverified_stance import _is_challenge_active
from UserPromptSubmit_modules.anti_sycophancy_injector import (
    _challenge_marker_path,
    _clear_challenge_marker,
    _safe_id,
    _write_challenge_marker,
)


class TestChallengeMarkerTTL:
    """Test FIX-001: TTL validation prevents stale markers from blocking."""

    def test_ttl_rejects_old_marker(self) -> None:
        """Stale markers (>5 min) should be rejected and cleaned up."""
        session_id = "test_session_ttl"
        terminal_id = "test_terminal_ttl"

        # Write a marker with old timestamp (>5 minutes ago)
        marker_path = _challenge_marker_path(session_id, terminal_id)
        marker_path.parent.mkdir(parents=True, exist_ok=True)

        old_timestamp = time.time() - 400  # 6 minutes 40 seconds ago
        old_content = {
            "timestamp": old_timestamp,
            "trigger_level": "high",
            "session_id": session_id,
            "terminal_id": terminal_id,
        }
        marker_path.write_text(json.dumps(old_content))

        # Verify marker exists
        assert marker_path.exists()

        # FIX-001: _is_challenge_active should reject and clean up stale markers
        data = {"session_id": session_id, "terminal_id": terminal_id}
        result = _is_challenge_active(data)

        # Should return False (marker rejected due to TTL)
        assert result is False, "Stale marker should be rejected"

        # Marker file should be cleaned up
        assert not marker_path.exists(), "Stale marker file should be deleted"

    def test_ttl_accepts_fresh_marker(self) -> None:
        """Fresh markers (<5 min) should be accepted."""
        session_id = "test_session_fresh"
        terminal_id = "test_terminal_fresh"

        # Write a fresh marker using actual function
        _write_challenge_marker(session_id, terminal_id, "high")

        # FIX-001: Fresh marker should be accepted
        data = {"session_id": session_id, "terminal_id": terminal_id}
        result = _is_challenge_active(data)

        assert result is True, "Fresh marker should be accepted"

        # Clean up
        _clear_challenge_marker(session_id, terminal_id)

    def test_ttl_boundary_case(self) -> None:
        """Test exactly 5-minute boundary (300 seconds)."""
        session_id = "test_session_boundary"
        terminal_id = "test_terminal_boundary"

        marker_path = _challenge_marker_path(session_id, terminal_id)
        marker_path.parent.mkdir(parents=True, exist_ok=True)

        # Write marker exactly at 5-minute boundary
        boundary_timestamp = time.time() - 300
        boundary_content = {
            "timestamp": boundary_timestamp,
            "trigger_level": "high",
            "session_id": session_id,
            "terminal_id": terminal_id,
        }
        marker_path.write_text(json.dumps(boundary_content))

        # FIX-001: Exactly 300 seconds should be rejected (> check, not >=)
        data = {"session_id": session_id, "terminal_id": terminal_id}
        result = _is_challenge_active(data)

        assert result is False, "Marker at exactly 300s boundary should be rejected"
        assert not marker_path.exists()

    def test_ttl_accepts_299_seconds(self) -> None:
        """Test 299 seconds (just under 5-minute threshold)."""
        session_id = "test_session_299"
        terminal_id = "test_terminal_299"

        marker_path = _challenge_marker_path(session_id, terminal_id)
        marker_path.parent.mkdir(parents=True, exist_ok=True)

        # Write marker at 299 seconds
        fresh_timestamp = time.time() - 299
        fresh_content = {
            "timestamp": fresh_timestamp,
            "trigger_level": "high",
            "session_id": session_id,
            "terminal_id": terminal_id,
        }
        marker_path.write_text(json.dumps(fresh_content))

        # FIX-001: 299 seconds should be accepted
        data = {"session_id": session_id, "terminal_id": terminal_id}
        result = _is_challenge_active(data)

        assert result is True, "Marker at 299s should be accepted"

        # Clean up
        _clear_challenge_marker(session_id, terminal_id)


class TestUUIDFallback:
    """Test FIX-003: UUID fallback prevents unknown__unknown contamination."""

    def test_no_unknown_unknown_marker_contamination(self) -> None:
        """FIX-003: Empty IDs generate UUID fallback, not 'unknown__unknown'."""
        state_dir = HOOKS_DIR / "state" / "anti_sycophancy_injector"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Clean up any existing markers first
        for marker in state_dir.glob("challenge__*.json"):
            marker.unlink()

        # Call _is_challenge_active with empty IDs multiple times
        # FIX-003: Each call generates a unique UUID fallback (auto_XXXXXXXX)
        # This prevents all terminals from sharing challenge__unknown__unknown.json
        data = {"session_id": "", "terminal_id": ""}
        result1 = _is_challenge_active(data)
        result2 = _is_challenge_active(data)

        # Both should return False (no marker exists)
        assert result1 is False
        assert result2 is False

        # Check that challenge__unknown__unknown.json was NOT created
        unknown_marker = state_dir / "challenge__unknown__unknown.json"
        assert not unknown_marker.exists(), "Should NOT create challenge__unknown__unknown.json"

    def test_uuid_fallback_generates_different_ids(self) -> None:
        """FIX-003: Each call with empty IDs generates different UUID fallback."""
        # The UUID fallback ensures that when multiple terminals check for
        # challenge markers with empty IDs, they each look for different files
        # (challenge__auto_XXXXXXXX.json instead of shared challenge__unknown__unknown.json)

        # We can't directly test the UUID generation since it's internal to
        # _is_challenge_active, but we can verify the behavior:
        # - Empty IDs don't create challenge__unknown__unknown.json
        # - Multiple terminals with empty IDs don't share state

        state_dir = HOOKS_DIR / "state" / "anti_sycophancy_injector"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Clean up any existing markers
        for marker in state_dir.glob("challenge__*.json"):
            marker.unlink()

        # Verify that calling with empty IDs doesn't create unknown__unknown
        data = {"session_id": "", "terminal_id": ""}
        _is_challenge_active(data)

        unknown_marker = state_dir / "challenge__unknown__unknown.json"
        assert not unknown_marker.exists(), "Empty IDs should use UUID fallback, not 'unknown'"

    def test_known_ids_not_replaced(self) -> None:
        """Provided IDs should not be replaced with UUID fallback."""
        session_id = "my_session"
        terminal_id = "my_terminal"

        # Write a marker with known IDs
        _write_challenge_marker(session_id, terminal_id, "high")

        # Verify marker uses provided IDs (not auto_ fallback)
        marker_path = _challenge_marker_path(session_id, terminal_id)
        assert marker_path.exists(), "Marker with known IDs should exist"
        assert "my_session" in str(marker_path), "Marker should use provided session_id"
        assert "my_terminal" in str(marker_path), "Marker should use provided terminal_id"

        # Verify _is_challenge_active finds it
        data = {"session_id": session_id, "terminal_id": terminal_id}
        is_active = _is_challenge_active(data)
        assert is_active is True, "Marker with known IDs should be active"

        # Clean up
        _clear_challenge_marker(session_id, terminal_id)


class TestRealFileIO:
    """Test actual file I/O behavior (no mocks)."""

    def test_write_and_read_marker_roundtrip(self) -> None:
        """Full roundtrip: write marker, read it back, verify content."""
        session_id = f"test_roundtrip_{uuid.uuid4().hex[:8]}"
        terminal_id = f"test_term_{uuid.uuid4().hex[:8]}"

        # Write marker
        _write_challenge_marker(session_id, terminal_id, "high")

        # Read it back via _is_challenge_active
        data = {"session_id": session_id, "terminal_id": terminal_id}
        is_active = _is_challenge_active(data)

        assert is_active is True

        # Verify actual file exists and has valid JSON
        marker_path = _challenge_marker_path(session_id, terminal_id)
        assert marker_path.exists()

        file_content = json.loads(marker_path.read_text())
        assert file_content.get("trigger_level") == "high"
        assert file_content.get("session_id") == session_id
        assert file_content.get("terminal_id") == terminal_id
        assert "timestamp" in file_content

        # Clean up
        _clear_challenge_marker(session_id, terminal_id)
        assert not marker_path.exists()

    def test_clear_marker_deletes_file(self) -> None:
        """_clear_challenge_marker should actually delete the file."""
        session_id = f"test_clear_{uuid.uuid4().hex[:8]}"
        terminal_id = f"test_term_{uuid.uuid4().hex[:8]}"

        # Write marker
        _write_challenge_marker(session_id, terminal_id, "low")
        marker_path = _challenge_marker_path(session_id, terminal_id)
        assert marker_path.exists()

        # Clear marker
        _clear_challenge_marker(session_id, terminal_id)

        # File should actually be deleted
        assert not marker_path.exists()

    def test_marker_path_uses_safe_ids(self) -> None:
        """Marker paths should sanitize special characters."""
        # Session/terminal IDs with special chars
        unsafe_session = "test/session/with/slashes"
        unsafe_terminal = "term:with:colons"

        # _safe_id should sanitize
        safe_session = _safe_id(unsafe_session)
        safe_terminal = _safe_id(unsafe_terminal)

        expected_session = "test_session_with_slashes"
        expected_terminal = "term_with_colons"

        assert safe_session == expected_session
        assert safe_terminal == expected_terminal

        # Verify marker path uses sanitized IDs
        marker_path = _challenge_marker_path(unsafe_session, unsafe_terminal)
        assert "test_session_with_slashes" in str(marker_path)
        assert "term_with_colons" in str(marker_path)


class TestMultiTerminalIsolation:
    """Test FIX-003: Multi-terminal safety with actual file operations."""

    def test_concurrent_marker_writes_dont_corrupt(self) -> None:
        """Multiple terminals writing markers simultaneously should not corrupt."""
        import concurrent.futures

        markers_written = []

        def write_marker(term_id: int) -> str:
            """Write a marker from a simulated terminal."""
            session_id = "concurrent_test"
            terminal_id = f"terminal_{term_id}"

            _write_challenge_marker(session_id, terminal_id, "high")

            marker_path = _challenge_marker_path(session_id, terminal_id)
            markers_written.append(marker_path)

            # Read back to verify
            data = {"session_id": session_id, "terminal_id": terminal_id}
            is_active = _is_challenge_active(data)
            return terminal_id if is_active else "FAILED"

        # Simulate 5 terminals writing concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(write_marker, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert "FAILED" not in results, f"Some terminals failed: {results}"

        # All markers should exist and be valid JSON
        for marker_path in markers_written:
            assert marker_path.exists(), f"Marker missing: {marker_path}"
            content = json.loads(marker_path.read_text())
            assert content.get("trigger_level") == "high"

        # Clean up
        for marker_path in markers_written:
            if marker_path.exists():
                marker_path.unlink()

    def test_different_terminals_dont_share_markers(self) -> None:
        """Terminals with different IDs should have separate markers."""
        session_id = "shared_session"
        terminals = [f"term_{i}" for i in range(3)]

        markers = {}
        for term in terminals:
            _write_challenge_marker(session_id, term, "low")
            marker_path = _challenge_marker_path(session_id, term)
            markers[term] = marker_path

        # All markers should be different files
        marker_files = {str(m) for m in markers.values()}
        assert len(marker_files) == 3, "Each terminal should have its own marker file"

        # Each terminal should only read its own marker
        for term in terminals:
            data = {"session_id": session_id, "terminal_id": term}
            is_active = _is_challenge_active(data)
            assert is_active is True

        # Clean up
        for marker_path in markers.values():
            if marker_path.exists():
                marker_path.unlink()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_marker_with_missing_timestamp(self) -> None:
        """Marker without timestamp should be handled gracefully."""
        session_id = "test_no_ts"
        terminal_id = "test_no_ts_term"

        marker_path = _challenge_marker_path(session_id, terminal_id)
        marker_path.parent.mkdir(parents=True, exist_ok=True)

        # Write marker without timestamp field
        invalid_content = {
            "trigger_level": "high",
            "session_id": session_id,
            "terminal_id": terminal_id,
            # Missing timestamp
        }
        marker_path.write_text(json.dumps(invalid_content))

        # Should handle gracefully (reject as invalid due to timestamp check)
        data = {"session_id": session_id, "terminal_id": terminal_id}
        result = _is_challenge_active(data)

        # When timestamp is 0 (missing), time.time() - 0 > 300 will be True for any reasonable time
        # So marker should be rejected
        assert result is False, "Marker without timestamp should be rejected"

    def test_marker_with_invalid_json(self) -> None:
        """Marker file with invalid JSON is treated as active (safety-first)."""
        session_id = "test_bad_json"
        terminal_id = "test_bad_json_term"

        marker_path = _challenge_marker_path(session_id, terminal_id)
        marker_path.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid JSON
        marker_path.write_text("{invalid json content")

        # Safety-first: corrupted marker files are treated as active
        # (better to be safe than ignore a potentially active marker)
        data = {"session_id": session_id, "terminal_id": terminal_id}
        result = _is_challenge_active(data)

        # The implementation catches JSONDecodeError and returns True (safety-first)
        assert result is True, "Corrupted marker is treated as active (safety-first approach)"

        # Clean up
        if marker_path.exists():
            marker_path.unlink()

    def test_empty_marker_directory(self) -> None:
        """Reading from empty directory should not crash."""
        session_id = "nonexistent_session"
        terminal_id = "nonexistent_terminal"

        # Should return False, not crash
        data = {"session_id": session_id, "terminal_id": terminal_id}
        result = _is_challenge_active(data)

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
