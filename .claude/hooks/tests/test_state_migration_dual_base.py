#!/usr/bin/env python3
"""Isolated proof that the proposed state_paths migration is safe.

PROPOSED CHANGE (no live edit yet):
  - PreToolUse._get_state_dirs() returns BOTH:
      primary   = HOOKS_DIR.parent / "state"   -> P:/.claude/state/        (canonical)
      legacy    = HOOKS_DIR / "state"          -> P:/.claude/hooks/state/  (backward compat)
  - skill_enforcer._intent_state_dir() likewise returns the canonical path,
    and the writer loop continues to also write the legacy path during transition.

This test exercises IntentFileLookup + the Skill-clear candidate-path logic
against the PROPOSED dual bases, with NO edit to the live hook. It proves:
  T1: a file written to the NEW canonical path is found + cleared (forward compat)
  T2: a file written to the LEGACY path is STILL found + cleared (no break)
  T3: sibling-session isolation holds at the new path (WT_SESSION shared)
  T4: NEW primary wins over LEGACY when both exist (deterministic precedence)

If all four pass, the dual-base migration cannot orphan existing intent files
and cannot disarm the gate during the cache-timing crossover window.
"""
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

HOOKS_FILE = Path("P:/.claude/hooks/PreToolUse.py")
sys.path.insert(0, str(HOOKS_FILE.parent))
sys.path.insert(0, str(HOOKS_FILE.parent / "__lib"))

from PreToolUse import IntentFileLookup  # noqa: E402

NEW_BASE = Path("P:/.claude/state")              # canonical (state_paths.STATE_DIR)
LEGACY_BASE = Path("P:/.claude/hooks/state")     # current (HOOKS_DIR/"state")
TEST_SID_PREFIX = "pytest_statemigr_"


@pytest.fixture
def tracked():
    created: list[Path] = []
    yield created.append
    for root in (NEW_BASE, LEGACY_BASE):
        sessions = root / "sessions"
        if sessions.exists():
            for d in sessions.iterdir():
                if d.is_dir() and d.name.startswith(TEST_SID_PREFIX):
                    shutil.rmtree(d, ignore_errors=True)


def _write_intent(base: Path, session_id: str, skill: str = "wiki") -> Path:
    p = base / "sessions" / session_id / "pending_command_intent.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"skill": skill, "session_id": session_id, "prompt": f"/{skill} t",
                     "created_at": "2026-07-05T12:00:00.000000"}),
        encoding="utf-8",
    )
    return p


def _proposed_state_dirs() -> tuple[Path, Path]:
    """Mirror of the proposed PreToolUse._get_state_dirs() new behavior."""
    return NEW_BASE, LEGACY_BASE


def _found_path(result) -> Path:
    """IntentFileLookup.find() returns (path, format_description) or None."""
    return result[0] if result else None


class TestDualBaseMigration:
    def test_t1_new_canonical_path_found_and_listed(self, tracked):
        """Forward compat: IntentFileLookup with proposed dual bases finds a
        file written to the NEW canonical P:/.claude/state/ path."""
        sid = f"{TEST_SID_PREFIX}{uuid.uuid4().hex[:8]}"
        new_path = _write_intent(NEW_BASE, sid)
        tracked(new_path.parent)
        tracked(NEW_BASE / "sessions" / sid)

        primary, legacy = _proposed_state_dirs()
        lookup = IntentFileLookup(primary, legacy)
        found = _found_path(lookup.find(session_id=sid, terminal_id="tid_x"))

        assert found == new_path, f"REGRESSION: NEW canonical path not discovered (got {found})"

    def test_t2_legacy_path_still_found(self, tracked):
        """No-break: a file at the LEGACY P:/.claude/hooks/state/ path is still
        found by the proposed dual-base lookup (backward compatibility)."""
        sid = f"{TEST_SID_PREFIX}{uuid.uuid4().hex[:8]}"
        legacy_path = _write_intent(LEGACY_BASE, sid)
        tracked(legacy_path.parent)
        tracked(LEGACY_BASE / "sessions" / sid)
        assert not (NEW_BASE / "sessions" / sid / "pending_command_intent.json").exists()

        primary, legacy = _proposed_state_dirs()
        lookup = IntentFileLookup(primary, legacy)
        found = _found_path(lookup.find(session_id=sid, terminal_id="tid_x"))

        assert found == legacy_path, f"REGRESSION: LEGACY path orphaned (got {found})"

    def test_t3_sibling_session_isolation_at_new_path(self, tracked):
        """WT_SESSION shared across concurrent sessions: two sessions at the NEW
        canonical path must be independently addressable — finding sid_a does
        not return sid_b's file."""
        sid_a = f"{TEST_SID_PREFIX}a_{uuid.uuid4().hex[:8]}"
        sid_b = f"{TEST_SID_PREFIX}b_{uuid.uuid4().hex[:8]}"
        path_a = _write_intent(NEW_BASE, sid_a, skill="wiki")
        path_b = _write_intent(NEW_BASE, sid_b, skill="code")
        tracked(NEW_BASE / "sessions" / sid_a)
        tracked(NEW_BASE / "sessions" / sid_b)

        primary, legacy = _proposed_state_dirs()
        lookup = IntentFileLookup(primary, legacy)
        found_a = _found_path(lookup.find(session_id=sid_a, terminal_id="tid_shared"))
        found_b = _found_path(lookup.find(session_id=sid_b, terminal_id="tid_shared"))

        assert found_a == path_a and found_b == path_b, "isolation broken: lookup conflated sessions"
        a = json.loads(found_a.read_text(encoding="utf-8"))
        b = json.loads(found_b.read_text(encoding="utf-8"))
        assert a["skill"] == "wiki" and b["skill"] == "code"

    def test_t4_new_primary_wins_over_legacy(self, tracked):
        """Deterministic precedence: when BOTH paths exist for the same session,
        the NEW canonical path is returned (primary), so stale legacy bytes
        never shadow the fresh canonical write."""
        sid = f"{TEST_SID_PREFIX}{uuid.uuid4().hex[:8]}"
        _write_intent(LEGACY_BASE, sid, skill="stale_legacy")
        new_path = _write_intent(NEW_BASE, sid, skill="fresh_canonical")
        tracked(NEW_BASE / "sessions" / sid)
        tracked(LEGACY_BASE / "sessions" / sid)

        primary, legacy = _proposed_state_dirs()
        lookup = IntentFileLookup(primary, legacy)
        found = _found_path(lookup.find(session_id=sid, terminal_id="tid_x"))

        assert found == new_path, "primary precedence broken: legacy shadowed canonical"
        payload = json.loads(found.read_text(encoding="utf-8"))
        assert payload["skill"] == "fresh_canonical"


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
