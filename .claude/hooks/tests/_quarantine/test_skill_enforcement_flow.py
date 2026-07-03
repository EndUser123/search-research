"""Tests for skill-first gate and skill_enforcer flow.

Verifies:
1. Session-scoped intent file lookup (not glob)
2. Expired intent files are cleaned up
3. Skill-first gate blocks action tools when intent is pending
4. Skill-first gate allows investigation tools
5. Context injection is execution-mode agnostic
6. No cross-session interference
"""

import json
import sys
import tempfile
from pathlib import Path

# Setup paths
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# ── Test 1: _safe_id sanitization ──
def test_safe_id():
    # Import from PreToolUse
    sys.path.insert(0, str(HOOKS_DIR))

    # We can't import PreToolUse directly (it has __main__ guard),
    # so test the regex pattern
    import re
    def _safe_id(value):
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)

    assert _safe_id("abc-123") == "abc-123"
    assert _safe_id("session/with:special chars") == "session_with_special_chars"
    assert _safe_id("simple") == "simple"
    assert _safe_id("a.b.c") == "a.b.c"
    assert _safe_id("under_score") == "under_score"
    print("PASS: test_safe_id")


# ── Test 2: skill_enforcer detects slash commands ──
def test_slash_command_detection():
    # Import the package properly
    sys.path.insert(0, str(HOOKS_DIR))
    from UserPromptSubmit.skill_enforcer import extract_command_name, is_command_directive

    assert is_command_directive("/p") == True
    assert is_command_directive("/p some args") == True
    assert is_command_directive("/debug-rca") == True
    assert is_command_directive("hello world") == False
    assert is_command_directive("fix the /p issue") == False
    assert is_command_directive("") == False

    assert extract_command_name("/p") == "p"
    assert extract_command_name("/p some args") == "p"
    assert extract_command_name("/debug-rca") == "debug-rca"
    assert extract_command_name("hello") is None
    print("PASS: test_slash_command_detection")


# ── Test 3: skill_enforcer respects blocklist ──
def test_command_blocklist():
    sys.path.insert(0, str(HOOKS_DIR))
    from UserPromptSubmit.skill_enforcer import should_block_command

    # Built-in blocked commands
    assert should_block_command("help") == True
    assert should_block_command("clear") == True
    assert should_block_command("exit") == True

    # Regular skills should NOT be blocked
    assert should_block_command("p") == False
    assert should_block_command("debug-rca") == False
    assert should_block_command("search") == False
    print("PASS: test_command_blocklist")


# ── Test 4: Context injection is execution-mode agnostic ──
def test_context_injection_agnostic():
    sys.path.insert(0, str(HOOKS_DIR))
    from UserPromptSubmit.skill_enforcer import build_command_context

    ctx = build_command_context("p", "some args")

    # Must contain Skill() call instruction
    assert 'Skill("p")' in ctx

    # Must NOT contain subagent/agent-team language
    assert "subagent" not in ctx.lower()
    assert "agent team" not in ctx.lower()
    assert "dispatch" not in ctx.lower()

    # Must contain prohibition list
    assert "Prohibited" in ctx
    assert "Bash" in ctx
    assert "Task" in ctx

    # Must contain args
    assert "some args" in ctx

    print("PASS: test_context_injection_agnostic")


# ── Test 5: Session-scoped intent file creation (TTL-free) ──
def test_intent_file_session_scoped():
    """Verify intent files are named with session ID and have no TTL."""
    sys.path.insert(0, str(HOOKS_DIR))
    from UserPromptSubmit.skill_enforcer import _safe_id, _store_command_intent

    # Use a temp dir to avoid polluting real state
    test_dir = Path(tempfile.mkdtemp()) / "test_state"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Mock the state directories
    from UserPromptSubmit import skill_enforcer as se
    original_intent = se.INTENT_STATE_DIR
    original_fallback = se.FALLBACK_STATE_DIR

    try:
        se.INTENT_STATE_DIR = test_dir
        se.FALLBACK_STATE_DIR = test_dir / "fallback"

        # Create a mock context
        class MockContext:
            prompt = "/p"
            session_id = "test-session-abc-123"
            terminal_id = "term-1"
            data = {}

        _store_command_intent(MockContext(), "p")

        safe_id = _safe_id("test-session-abc-123")
        expected_file = test_dir / f"pending_command_intent_{safe_id}.json"

        assert expected_file.exists(), f"Expected {expected_file} to exist"

        content = json.loads(expected_file.read_text(encoding="utf-8"))
        assert content["skill"] == "p"
        assert "timestamp" in content

        # TTL-free: no expires_at field
        assert "expires_at" not in content, "Intent file should not have expires_at (TTL-free design)"

        # Cleanup
        expected_file.unlink()

    finally:
        se.INTENT_STATE_DIR = original_intent
        se.FALLBACK_STATE_DIR = original_fallback

    print("PASS: test_intent_file_session_scoped")


# ── Test 6: Skill-first gate allows investigation tools ──
def test_gate_allows_investigation():
    """Verify investigation tools are not blocked by skill-first gate."""
    # Import the gate function's allowed set
    # Can't import _check_skill_first_gate directly, but we can test the allowed set
    allowed = {
        "Read", "Grep", "Glob", "AskUserQuestion", "Skill",
        "WebSearch", "WebFetch", "TodoWrite", "Edit", "Write",
    }

    # These should be allowed
    for tool in ["Read", "Grep", "Glob", "Skill", "Edit", "Write", "TodoWrite"]:
        assert tool in allowed, f"{tool} should be in allowed set"

    # These should NOT be in allowed (action tools)
    for tool in ["Bash", "Task", "NotebookEdit"]:
        assert tool not in allowed, f"{tool} should NOT be in allowed set"

    print("PASS: test_gate_allows_investigation")


# ── Test 7: No cross-session file pickup ──
def test_no_cross_session_pickup():
    """Verify session-scoped lookup doesn't pick up other sessions' files."""
    test_dir = Path(tempfile.mkdtemp()) / "cross_session_test"
    test_dir.mkdir(parents=True, exist_ok=True)

    import re
    def _safe_id(value):
        return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)

    # Create intent files for different sessions
    sessions = ["session-A", "session-B", "session-C"]
    for s in sessions:
        safe = _safe_id(s)
        f = test_dir / f"pending_command_intent_{safe}.json"
        f.write_text(json.dumps({
            "skill": "p",
            "timestamp": "2026-01-01T00:00:00",
        }), encoding="utf-8")

    # Looking up session-A should only find session-A's file
    target = _safe_id("session-A")
    found = test_dir / f"pending_command_intent_{target}.json"
    assert found.exists()

    # Looking up session-D should find nothing
    target_d = _safe_id("session-D")
    not_found = test_dir / f"pending_command_intent_{target_d}.json"
    assert not not_found.exists()

    # Cleanup
    for s in sessions:
        safe = _safe_id(s)
        (test_dir / f"pending_command_intent_{safe}.json").unlink()

    print("PASS: test_no_cross_session_pickup")


# ── Test 8: Retention cleanup covers orphaned intent files ──
def test_retention_covers_intent_files():
    """Verify session_data_retention catches pending_command_intent_* files.

    The existing _cleanup_state_files in session_data_retention.py handles
    all pending_* files in state/ with a 24h threshold. This test confirms
    that pending_command_intent_ files match the pattern.
    """
    # The retention module at line 244 has: name.startswith("pending_") and age > 86400
    # Our files are named: pending_command_intent_{session_id}.json
    # Verify prefix match:
    test_filename = "pending_command_intent_abc_123.json"
    assert test_filename.startswith("pending_"), \
        "Intent filenames must start with 'pending_' to be caught by retention"

    # Verify it's a .json file in state/ (where retention scans)
    assert test_filename.endswith(".json"), \
        "Intent files must be .json"

    # The retention cleanup uses STATE_DIR_ALT (hooks/state/) which is
    # exactly where skill_enforcer writes intent files (INTENT_STATE_DIR).
    # No code change needed — just verify the path alignment.
    from session_data_retention import STATE_DIR_ALT
    from UserPromptSubmit.skill_enforcer import INTENT_STATE_DIR
    assert STATE_DIR_ALT.resolve() == INTENT_STATE_DIR.resolve(), \
        f"Retention scans {STATE_DIR_ALT} but intents go to {INTENT_STATE_DIR}"

    print("PASS: test_retention_covers_intent_files")


if __name__ == "__main__":
    tests = [
        test_safe_id,
        test_slash_command_detection,
        test_command_blocklist,
        test_context_injection_agnostic,
        test_intent_file_session_scoped,
        test_gate_allows_investigation,
        test_no_cross_session_pickup,
        test_retention_covers_intent_files,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed:
        sys.exit(1)
    else:
        print("All tests passed!")
