"""
Tests for SEC-004: Session-Scoped State File Isolation.

These tests validate that state files are properly scoped by both
terminal_id AND session_id, preventing terminals with the same terminal_id
but different sessions from sharing state.

Run with: pytest .claude/hooks/tests/test_session_isolation.py -v
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# The state file mechanism doesn't exist yet - use skipif pattern
try:
    from __lib.state_file_manager import (
        StateFileManager,
        get_session_id,
        read_state_file,
        write_state_file,
    )
except (ImportError, ModuleNotFoundError):
    StateFileManager = None
    get_session_id = None
    write_state_file = None
    read_state_file = None


# -------------------------------------------------------------------
# Test: SEC-004-001 — Same terminal_id, different session_id = separate files
# -------------------------------------------------------------------
@pytest.mark.skipif(
    StateFileManager is None,
    reason="state_file_manager not implemented yet",
)
def test_same_terminal_different_session_creates_separate_files(tmp_path):
    """
    Two sessions with same terminal_id must create separate state files.

    Given: terminal_id='console_123', session_id='abc'
    And:   terminal_id='console_123', session_id='xyz'
    When:  Both create state files
    Then:  Two separate files exist with different session_id in path
    """
    manager1 = StateFileManager(tmp_path, terminal_id="console_123", session_id="abc")
    manager2 = StateFileManager(tmp_path, terminal_id="console_123", session_id="xyz")

    path1 = manager1.get_state_file_path()
    path2 = manager2.get_state_file_path()

    # Paths must be different
    assert path1 != path2, "Same terminal_id, different session_id must have separate paths"

    # Write to each
    manager1.write({"data": "session_abc"})
    manager2.write({"data": "session_xyz"})

    # Both files must exist
    assert path1.exists(), "First session file must exist"
    assert path2.exists(), "Second session file must exist"

    # Data must not leak between sessions
    data1 = json.loads(path1.read_text())
    data2 = json.loads(path2.read_text())
    assert data1["data"] == "session_abc", "First session data must be preserved"
    assert data2["data"] == "session_xyz", "Second session data must be preserved"


# -------------------------------------------------------------------
# Test: SEC-004-002 — Missing CLAUDE_SESSION_ID generates UUID fallback
# -------------------------------------------------------------------
@pytest.mark.skipif(
    get_session_id is None,
    reason="state_file_manager not implemented yet",
)
def test_generates_uuid_fallback():
    """
    When CLAUDE_SESSION_ID is not set, generate a unique session ID.

    The fallback must NOT be terminal_id alone - that would reintroduce
    the vulnerability. A unique ID via uuid.uuid4().hex[:8] is required.
    """
    # Ensure CLAUDE_SESSION_ID is not in environment
    original = os.environ.pop("CLAUDE_SESSION_ID", None)
    try:
        session_id = get_session_id()
        assert session_id is not None, "Session ID must be generated"
        # Must be a valid hex string of reasonable length
        assert len(session_id) >= 6, "Session ID must be at least 6 chars"
        # Must not be the terminal_id fallback
        assert session_id != "console_123", "Must not fallback to terminal_id"
    finally:
        if original is not None:
            os.environ["CLAUDE_SESSION_ID"] = original


# -------------------------------------------------------------------
# Test: SEC-004-003 — session_id written to CLAUDE_ENV_FILE for persistence
# -------------------------------------------------------------------
@pytest.mark.skipif(
    StateFileManager is None,
    reason="state_file_manager not implemented yet",
)
def test_env_file_persistence(tmp_path, monkeypatch):
    """
    session_id must be written to $CLAUDE_ENV_FILE for persistence.

    This is the NBM-1 workaround: CLAUDE_SESSION_ID is frequently missing
    in Bash hooks, so we persist session_id to CLAUDE_ENV_FILE.
    """
    # Create a temp env file
    env_file = tmp_path / ".claude_env"
    monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))

    original = os.environ.pop("CLAUDE_SESSION_ID", None)
    try:
        manager = StateFileManager(tmp_path, terminal_id="console_123", session_id=None)
        session_id = manager.get_session_id()

        # session_id should be written to CLAUDE_ENV_FILE
        assert env_file.exists(), "session_id must be written to CLAUDE_ENV_FILE"

        content = env_file.read_text()
        assert session_id in content, "CLAUDE_ENV_FILE must contain session_id"
    finally:
        if original is not None:
            os.environ["CLAUDE_SESSION_ID"] = original


# -------------------------------------------------------------------
# Test: SEC-004-004 — FileLock prevents concurrent write corruption
# -------------------------------------------------------------------
@pytest.mark.skipif(
    StateFileManager is None,
    reason="state_file_manager not implemented yet",
)
def test_filelock_prevents_concurrent_corruption(tmp_path):
    """
    Multiple concurrent writes to same state file must be serialized.

    Without locking, concurrent writes cause lost updates. With FileLock,
    all writes must be atomic and no data is lost.
    """
    import threading

    manager = StateFileManager(tmp_path, terminal_id="console_123", session_id="abc")

    # Shared state
    results = []
    lock_errors = []

    def write_increment(n):
        try:
            for i in range(10):
                manager.atomic_increment("counter")
                results.append(n)
        except Exception as e:
            lock_errors.append((n, str(e)))

    threads = [threading.Thread(target=write_increment, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # No lock errors should occur
    assert len(lock_errors) == 0, f"Lock errors: {lock_errors}"

    # Counter must be exactly 50 (5 threads * 10 increments)
    final = manager.read()
    assert final["counter"] == 50, f"Expected 50, got {final['counter']} - lost updates!"


# -------------------------------------------------------------------
# Test: SEC-004-005 — State file uses correct naming convention
# -------------------------------------------------------------------
@pytest.mark.skipif(
    StateFileManager is None,
    reason="state_file_manager not implemented yet",
)
def test_state_file_naming_convention(tmp_path):
    """
    State file must follow naming: {terminal_id}_{session_id}_restoration_pending.json

    The plan explicitly requires session_id in the filename for proper isolation.
    Using suffix replacement (.with_suffix) is explicitly forbidden.
    """
    manager = StateFileManager(tmp_path, terminal_id="console_123", session_id="abc")

    path = manager.get_state_file_path()
    path_str = str(path)

    # Must contain both terminal_id and session_id
    assert "console_123" in path_str, "Path must contain terminal_id"
    assert "abc" in path_str, "Path must contain session_id"
    assert "restoration_pending" in path_str, "Path must contain restoration_pending"
    assert path_str.endswith(".json"), "Path must end with .json"

    # Must NOT use with_suffix() pattern that would corrupt the name
    # e.g., "file.json" -> "file.lock" (WRONG)
    assert ".lock" not in path_str.replace(".json.lock", ""), "Must not use with_suffix() pattern"


# -------------------------------------------------------------------
# Characterization test: Import module
# -------------------------------------------------------------------
def test_module_import():
    """
    Characterization test: Verify state_file_manager module can be imported.

    This test will FAIL in the RED phase because the module doesn't exist yet.
    """
    from __lib.state_file_manager import (
        StateFileManager,
        get_session_id,
        read_state_file,
        write_state_file,
    )

    assert StateFileManager is not None
    assert get_session_id is not None
    assert write_state_file is not None
    assert read_state_file is not None
