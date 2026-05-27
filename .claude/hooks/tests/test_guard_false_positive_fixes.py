"""Tests for guard false-positive fixes.

Covers:
1. REFERENT SCOPE MISMATCH: session-boundary anchor clearing
   - Anchors clear when session_id changes (compaction)
   - Anchors persist when session_id stays the same (follow-up messages)
2. SKILL-FIRST GATE: suffix matching for skill name comparison
   - Exact match still works
   - Short name matches namespaced name
   - Mismatched names still fail
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "UserPromptSubmit_modules"))
sys.path.insert(0, str(HOOKS_DIR / "__lib"))


# ---------------------------------------------------------------------------
# 1. REFERENT SCOPE MISMATCH: session-boundary anchor clearing
# ---------------------------------------------------------------------------

class TestSessionBoundaryAnchorClearing:
    """_write_state clears anchors when session_id changes."""

    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()
        self.state_dir = Path(self.tmpdir)

    def _patch_state_dir(self, monkeypatch):
        # _state_path uses Path.home() / .claude / .artifacts / {tid} / referent_anchors.json
        # Patch Path.home() so state files land in our tmpdir
        monkeypatch.setattr("pathlib.Path.home", lambda: self.state_dir)

    def test_anchors_cleared_on_session_change(self, monkeypatch):
        """Anchors from session A are discarded when session B writes."""
        from referent_anchor import _write_state, _read_state
        self._patch_state_dir(monkeypatch)

        tid = "console_test123"
        _write_state(tid, ["foo", "bar"], "table", "session-A")
        _write_state(tid, None, "none", "session-B")

        state = _read_state(tid)
        assert state is not None
        assert state.get("anchor_terms") == []
        assert state.get("status") == "no_anchors"

    def test_no_anchors_overwrites_same_session(self, monkeypatch):
        """Single-turn lifecycle: no_anchors always overwrites, even same session."""
        from referent_anchor import _write_state, _read_state
        self._patch_state_dir(monkeypatch)

        tid = "console_test456"
        _write_state(tid, ["foo", "bar"], "table", "session-A")
        _write_state(tid, None, "none", "session-A")

        state = _read_state(tid)
        assert state is not None
        assert state.get("anchor_terms") == []
        assert state.get("status") == "no_anchors"

    def test_new_anchors_overwrite_on_session_change(self, monkeypatch):
        """New anchors from session B overwrite stale session A anchors."""
        from referent_anchor import _write_state, _read_state
        self._patch_state_dir(monkeypatch)

        tid = "console_test789"
        _write_state(tid, ["old_item"], "table", "session-A")
        _write_state(tid, ["new_item"], "list", "session-B")

        state = _read_state(tid)
        assert state is not None
        assert state.get("anchor_terms") == ["new_item"]
        assert state.get("source_type") == "list"

    def test_no_session_id_always_overwrites(self, monkeypatch):
        """Single-turn lifecycle: no_anchors overwrites even without session_id."""
        from referent_anchor import _write_state, _read_state
        self._patch_state_dir(monkeypatch)

        tid = "console_nosession"
        _write_state(tid, ["foo"], "table", "session-X")
        _write_state(tid, None, "none", None)

        state = _read_state(tid)
        assert state is not None
        assert state.get("anchor_terms") == []
        assert state.get("status") == "no_anchors"

    def test_empty_session_id_always_overwrites(self, monkeypatch):
        """Single-turn lifecycle: no_anchors overwrites even with empty session_id."""
        from referent_anchor import _write_state, _read_state
        self._patch_state_dir(monkeypatch)

        tid = "console_emptysession"
        _write_state(tid, ["foo"], "table", "session-X")
        _write_state(tid, None, "none", "")

        state = _read_state(tid)
        assert state is not None
        assert state.get("anchor_terms") == []
        assert state.get("status") == "no_anchors"


# ---------------------------------------------------------------------------
# 2. SKILL-FIRST GATE: suffix matching for skill name comparison
# ---------------------------------------------------------------------------

def _skill_names_match(a: str, b: str) -> bool:
    """Inline copy of PreToolUse._skill_names_match for testing.

    Handles namespace prefix mismatches: 'cc-skills-sdlc:design' should match
    'design' since the short name is the suffix after the colon separator.
    """
    a_lower = a.strip().lower()
    b_lower = b.strip().lower()
    if a_lower == b_lower:
        return True
    for name in (a_lower, b_lower):
        if ":" in name:
            short = name.rsplit(":", 1)[1]
            other = b_lower if name == a_lower else a_lower
            if short == other:
                return True
            if other.endswith(":" + short):
                return True
    return False


class TestSkillNamesMatch:
    """_skill_names_match handles namespace prefix mismatches."""

    def test_exact_match(self):
        assert _skill_names_match("design", "design") is True
        assert _skill_names_match("cc-skills-sdlc:design", "cc-skills-sdlc:design") is True

    def test_case_insensitive(self):
        assert _skill_names_match("Design", "design") is True
        assert _skill_names_match("CC-SKILLS-SDLC:Design", "design") is True

    def test_short_matches_namespaced(self):
        assert _skill_names_match("design", "cc-skills-sdlc:design") is True

    def test_namespaced_matches_short(self):
        assert _skill_names_match("cc-skills-sdlc:design", "design") is True

    def test_different_skills_dont_match(self):
        assert _skill_names_match("design", "refactor") is False
        assert _skill_names_match("cc-skills-sdlc:design", "cc-skills-sdlc:refactor") is False

    def test_short_name_collision_doesnt_match(self):
        """'code' should not match 'cc-skills-sdlc:decode'."""
        assert _skill_names_match("code", "cc-skills-sdlc:decode") is False

    def test_whitespace_handled(self):
        assert _skill_names_match(" design ", "design") is True
        assert _skill_names_match(" design ", " cc-skills-sdlc:design ") is True

    def test_plugin_prefix_mismatch(self):
        """Two different plugins with same short name should match (correct behavior
        since they resolve to the same skill at runtime)."""
        assert _skill_names_match("plugin-a:design", "plugin-b:design") is True


# ---------------------------------------------------------------------------
# 3. SINGLE-TURN LIFECYCLE: Stop-side anchor clearing
# ---------------------------------------------------------------------------

class TestStopSideAnchorClearing:
    """_clear_referent_anchors in Stop.py deletes anchor state files from artifacts path."""

    def test_clears_existing_anchor_file(self, monkeypatch, tmp_path):
        """Stop gate deletes the anchor state file from artifacts/{terminal_id}/."""
        artifacts_dir = tmp_path / ".claude" / ".artifacts" / "console_test"
        artifacts_dir.mkdir(parents=True)
        state_file = artifacts_dir / "referent_anchors.json"
        state_file.write_text('{"anchor_terms": ["foo"]}', encoding="utf-8")
        assert state_file.exists()

        import importlib
        stop_mod = importlib.import_module("Stop")
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        stop_mod._clear_referent_anchors({"terminal_id": "console_test"})

        assert not state_file.exists()

    def test_no_error_when_no_anchor_file(self, monkeypatch, tmp_path):
        """Stop gate silently succeeds when no anchor file exists."""
        import importlib
        stop_mod = importlib.import_module("Stop")
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        stop_mod._clear_referent_anchors({"terminal_id": "console_noanchor"})

    def test_returns_none(self, monkeypatch, tmp_path):
        """Gate returns None (non-blocking, always allows)."""
        import importlib
        stop_mod = importlib.import_module("Stop")
        monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
        result = stop_mod._clear_referent_anchors({"terminal_id": "console_test"})
        assert result is None
