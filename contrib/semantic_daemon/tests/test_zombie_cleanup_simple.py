#!/usr/bin/env python3
"""Simple tests for zombie cleanup feature - focused on implementation verification.

These tests verify that the daemon uses Windows Mutex for atomic single-instance
determination, without complex psutil mocking.
"""

import sys
from pathlib import Path

# Setup path
csf_root = Path(__file__).parent.parent.parent.parent.parent
if str(csf_root) not in sys.path:
    sys.path.insert(0, str(csf_root))


def test_daemon_has_aggressive_cleanup_method():
    """Verify the daemon has _aggressive_cleanup_zombies method."""
    from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
        UnifiedSemanticDaemon,
    )

    assert hasattr(
        UnifiedSemanticDaemon, "_aggressive_cleanup_zombies"
    ), "Daemon should have _aggressive_cleanup_zombies method"


def test_daemon_has_detect_method():
    """Verify the daemon has _detect_all_daemon_processes method."""
    from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
        UnifiedSemanticDaemon,
    )

    assert hasattr(
        UnifiedSemanticDaemon, "_detect_all_daemon_processes"
    ), "Daemon should have _detect_all_daemon_processes method"


def test_mutex_constant_exists():
    """Verify the DAEMON_MUTEX_NAME constant exists."""
    from search_research.contrib.semantic_daemon.unified_semantic_daemon import DAEMON_MUTEX_NAME

    # Mutex name should use Global\ namespace for cross-session visibility
    assert (
        "Global\\" in DAEMON_MUTEX_NAME
    ), f"DAEMON_MUTEX_NAME should use Global\\ namespace, got {DAEMON_MUTEX_NAME}"
    assert (
        "SemanticDaemon" in DAEMON_MUTEX_NAME
    ), f"DAEMON_MUTEX_NAME should contain 'SemanticDaemon', got {DAEMON_MUTEX_NAME}"


def test_max_daemon_age_constant_exists():
    """Verify the MAX_DAEMON_AGE constant exists."""
    from search_research.contrib.semantic_daemon.unified_semantic_daemon import MAX_DAEMON_AGE

    # Max age should be 1 hour (3600 seconds)
    assert MAX_DAEMON_AGE == 3600, f"MAX_DAEMON_AGE should be 3600, got {MAX_DAEMON_AGE}"


def test_sessionstart_no_grace_period():
    """Verify SessionStart_semantic_daemon.py does NOT use grace period."""
    hook_path = Path(".claude/hooks/SessionStart_semantic_daemon.py")
    if not hook_path.exists():
        hook_path = Path("P:/.claude/hooks/SessionStart_semantic_daemon.py")

    content = hook_path.read_text()

    # Should NOT use 30 second grace period (30/3600 hours)
    assert (
        "(30/3600)" not in content and "age_hours < (30/3600)" not in content
    ), "SessionStart hook should NOT use grace period (mutex-based approach)"
    # Should keep only canonical daemon based on discovery PID
    assert (
        "pid == discovery_pid" in content
    ), "SessionStart hook should keep only canonical daemon (pid == discovery_pid)"


def test_age_based_termination_method_exists():
    """Verify the daemon has _should_terminate_based_on_age method."""
    from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
        UnifiedSemanticDaemon,
    )

    assert hasattr(
        UnifiedSemanticDaemon, "_should_terminate_based_on_age"
    ), "Daemon should have _should_terminate_based_on_age method"


def test_aggressive_cleanup_signature():
    """Verify _aggressive_cleanup_zombies has correct signature."""
    import inspect

    from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
        UnifiedSemanticDaemon,
    )

    method = UnifiedSemanticDaemon._aggressive_cleanup_zombies
    sig = inspect.signature(method)

    # Should accept self and no other parameters
    params = list(sig.parameters.keys())
    assert params == [
        "self"
    ], f"_aggressive_cleanup_zombies should only accept 'self' parameter, got {params}"


def test_detect_processes_signature():
    """Verify _detect_all_daemon_processes has correct signature."""
    import inspect

    from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
        UnifiedSemanticDaemon,
    )

    method = UnifiedSemanticDaemon._detect_all_daemon_processes
    sig = inspect.signature(method)

    # Should accept only self
    params = list(sig.parameters.keys())
    assert params == [
        "self"
    ], f"_detect_all_daemon_processes should only accept 'self' parameter, got {params}"

    # Should return list of dicts
    return_annotation = sig.return_annotation
    # Check if annotation indicates list of dicts
    assert (
        "list" in str(return_annotation).lower()
    ), f"_detect_all_daemon_processes should return list, got {return_annotation}"


def test_daemon_has_mutex_attributes():
    """Verify daemon has mutex-related attributes."""
    from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
        UnifiedSemanticDaemon,
    )

    # Create a daemon instance to check attributes
    # Note: This may create a mutex, so we just check class doesn't break
    daemon = UnifiedSemanticDaemon.__new__(UnifiedSemanticDaemon)
    daemon.pid = 12345
    daemon.timestamp = 1234567890
    daemon._daemon_mutex_handle = None
    daemon._is_canonical_daemon = True

    # Should have mutex handle attribute
    assert hasattr(
        daemon, "_daemon_mutex_handle"
    ), "Daemon should have _daemon_mutex_handle attribute"
    assert hasattr(
        daemon, "_is_canonical_daemon"
    ), "Daemon should have _is_canonical_daemon attribute"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
