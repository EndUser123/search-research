#!/usr/bin/env python3
"""Regression test for the /gitpack lockout (STATE-01 Skill-clear migration).

The bug: STATE-01 re-keyed the intent writer to `sessions/{session_id}/...`,
but the Skill-tool cleanup branch in PreToolUse.main() only knew the legacy
terminal-scoped paths. Result: user fires Skill(), the gate's intent file
survived, the next Bash call re-blocked — locking the turn until the user
sent a non-slash follow-up.

This is the discriminating test the writer/clear/UPS tests in
test_command_intent_session_isolation.py cannot provide: it exercises
PreToolUse.py's Skill-tool cleanup branch end-to-end via subprocess on the
real hook (no mocks), proving the candidate path list now mirrors the writer.

HARD REQUIREMENTS covered:
  - Multi-terminal isolation: a Skill() call in session_A must not delete
    session_B's in-flight intent, even when both share terminal_id (WT_SESSION
    is shared across concurrent Claude sessions in one Windows Terminal).
  - Stale-data immunity: robust cleanup of uniquely-prefixed test sessions;
    no leakage into real session state.

ISOLATION NOTE: PreToolUse.py hardcodes `HOOKS_DIR = Path(__file__).resolve().parent`
(line 44) and does NOT honor CLAUDE_PROJECT_DIR. So the test must write to the
REAL state dir at P:/.claude/hooks/state/. We use a `pytest_skillclear_<uuid>`
session_id prefix (cannot collide with real CC sessions) and remove every path
we create in teardown.
"""
import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

HOOK_FILE = Path("P:/.claude/hooks/PreToolUse.py")
STATE_DIR = Path("P:/.claude/hooks/state")
TEST_SID_PREFIX = "pytest_skillclear_"


@pytest.fixture
def isolated_sessions():
    """Track every state path we create and remove it in teardown."""
    created: list[Path] = []

    def _track(p: Path) -> Path:
        created.append(p)
        return p

    yield _track

    # Stale-data immunity: remove every session/terminal dir we created.
    for p in created:
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
    # Belt-and-suspenders: scrub any pytest_skillclear_* session dirs left behind
    # by a crashed prior run, so stale state can never arm the gate against a
    # real (or future test) invocation.
    sessions_root = STATE_DIR / "sessions"
    if sessions_root.exists():
        for d in sessions_root.iterdir():
            if d.is_dir() and d.name.startswith(TEST_SID_PREFIX):
                shutil.rmtree(d, ignore_errors=True)


def _write_state01_intent(track, session_id: str, skill: str = "wiki") -> Path:
    """Write a STATE-01 session-scoped intent file the way the writer does."""
    intent_path = STATE_DIR / "sessions" / session_id / "pending_command_intent.json"
    intent_path.parent.mkdir(parents=True, exist_ok=True)
    intent_path.write_text(
        json.dumps(
            {
                "skill": skill,
                "session_id": session_id,
                "prompt": f"/{skill} test",
                "created_at": "2026-07-05T12:00:00.000000",
            }
        ),
        encoding="utf-8",
    )
    return track(intent_path.parent)


def _run_pretooluse(skill: str, session_id: str, terminal_id: str) -> subprocess.CompletedProcess:
    """Real smoke proof: invoke PreToolUse.py exactly as Claude Code does."""
    payload = {
        "tool_name": "Skill",
        "tool_input": {"skill": skill},
        "session_id": session_id,
        "terminal_id": terminal_id,
        "cwd": "P:/",
    }
    return subprocess.run(
        [sys.executable, str(HOOK_FILE)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=15,
    )


class TestSkillClearState01:
    """The /gitpack lockout regression: Skill-tool cleanup must find and delete
    the STATE-01 session-scoped intent file."""

    def test_skill_tool_deletes_state01_session_scoped_intent(self, isolated_sessions):
        """THE discriminating test. Pre-fix this hangs/locks: Skill() fires but
        the file survives, so the next Bash re-blocks."""
        if not HOOK_FILE.exists():
            pytest.skip("PreToolUse.py not found")

        sid = f"{TEST_SID_PREFIX}{uuid.uuid4().hex[:8]}"
        intent_path = STATE_DIR / "sessions" / sid / "pending_command_intent.json"
        isolated_sessions(STATE_DIR / "sessions" / sid)
        _write_state01_intent(isolated_sessions, sid, skill="wiki")

        assert intent_path.exists(), "fixture: intent file must exist before Skill()"

        result = _run_pretooluse(skill="wiki", session_id=sid, terminal_id="tid_shared")

        assert intent_path.exists() is False, (
            f"REGRESSION: Skill() did not delete STATE-01 intent file. "
            f"stdout={result.stdout[:300]!r} stderr={result.stderr[:300]!r}"
        )

    def test_skill_tool_does_not_damage_sibling_session(self, isolated_sessions):
        """Multi-terminal isolation: two sessions share terminal_id (WT_SESSION);
        Skill() in session_A must NOT touch session_B's in-flight intent."""
        if not HOOK_FILE.exists():
            pytest.skip("PreToolUse.py not found")

        sid_a = f"{TEST_SID_PREFIX}a_{uuid.uuid4().hex[:8]}"
        sid_b = f"{TEST_SID_PREFIX}b_{uuid.uuid4().hex[:8]}"
        intent_a = STATE_DIR / "sessions" / sid_a / "pending_command_intent.json"
        intent_b = STATE_DIR / "sessions" / sid_b / "pending_command_intent.json"
        isolated_sessions(STATE_DIR / "sessions" / sid_a)
        isolated_sessions(STATE_DIR / "sessions" / sid_b)
        _write_state01_intent(isolated_sessions, sid_a, skill="wiki")
        _write_state01_intent(isolated_sessions, sid_b, skill="code")

        # Session A fires Skill() for its own slash command.
        _run_pretooluse(skill="wiki", session_id=sid_a, terminal_id="tid_shared")

        assert intent_a.exists() is False, "session A's intent should have been cleared"
        assert intent_b.exists() is True, (
            "T2 REGRESSION: Skill() in session A deleted session B's in-flight intent "
            "(WT_SESSION shared across concurrent sessions — isolation broken)"
        )

    def test_skill_mismatch_does_not_delete(self, isolated_sessions):
        """Stale-data / robustness: Skill() for a DIFFERENT skill than the
        pending intent must not clear the file. Guards against over-aggressive
        clearing that would disarm an unrelated in-flight command."""
        if not HOOK_FILE.exists():
            pytest.skip("PreToolUse.py not found")

        sid = f"{TEST_SID_PREFIX}{uuid.uuid4().hex[:8]}"
        intent_path = STATE_DIR / "sessions" / sid / "pending_command_intent.json"
        isolated_sessions(STATE_DIR / "sessions" / sid)
        _write_state01_intent(isolated_sessions, sid, skill="wiki")

        # User loaded 'code' while 'wiki' intent was pending.
        _run_pretooluse(skill="code", session_id=sid, terminal_id="tid_shared")

        assert intent_path.exists() is True, (
            "Skill() for a different skill name must NOT clear an unrelated intent"
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
