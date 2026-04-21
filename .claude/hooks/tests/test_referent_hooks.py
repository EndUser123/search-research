"""Tests for referent collapse prevention hooks.

Tests the three-hook system:
1. UserPromptSubmit_referent_anchor - extracts anchor terms from user messages
2. PreToolUse_referent_scope_gate - blocks off-topic tool calls
3. Stop_referent_coverage - warns if response misses anchor terms
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add hooks dir to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "UserPromptSubmit_modules"))
sys.path.insert(0, str(HOOKS_DIR / "__lib"))

from referent_anchor import (
    _extract_bullet_items,
    _extract_table_rows,
    _has_expansion_language,
    _has_referential_language,
    _normalize_term,
    referent_anchor_hook,
    _write_state,
)
from base import HookContext

# Real incident from the ADR
REAL_INCIDENT_TABLE = """
Assembled priority

| Pattern | Source | Leverage for yt-is | Effort |
|---|---|---|---|
| RSS channel diff detection | YouTube section | High | Low |
| Multi-key API rotation with cooldown | YouTube section | High | Medium |
| ytInitialPlayerResponse JSON parsing | Nordstrom to YouTube | Medium | Medium |
| Per-terminal proxy credit tracking | Nordstrom | Medium | Medium |
| Playwright-style async context per terminal | Top 20 Pattern | Medium | High |
| Session browser + parallel page launch | Top 20 Pattern | Medium | Medium |

I thought we already had some of those. investigate what is outstanding.
"""


class TestTableExtraction:
    def test_extracts_first_column_from_markdown_table(self):
        rows = _extract_table_rows(REAL_INCIDENT_TABLE)
        assert len(rows) == 6
        assert "RSS channel diff detection" in rows[0]
        assert "Multi-key API rotation with cooldown" in rows[1]
        assert "Session browser + parallel page launch" in rows[5]

    def test_skips_separator_lines(self):
        text = "| A | B |\n|---|---|\n| C | D |"
        rows = _extract_table_rows(text)
        # "A" is header (immediately before separator), only "C" extracted
        assert len(rows) == 1
        assert rows[0] == "C"

    def test_empty_text_returns_empty(self):
        assert _extract_table_rows("") == []
        assert _extract_table_rows("no table here") == []


class TestBulletExtraction:
    def test_extracts_bullet_items(self):
        text = "- First item\n- Second item\n- Third item"
        items = _extract_bullet_items(text)
        assert len(items) == 3
        assert items[0] == "First item"

    def test_mixed_bullet_styles(self):
        text = "- Dash item\n* Star item\n- Another dash"
        items = _extract_bullet_items(text)
        assert len(items) == 3

    def test_no_bullets_returns_empty(self):
        assert _extract_bullet_items("plain text") == []


class TestReferentialDetection:
    def test_detects_those(self):
        assert _has_referential_language("investigate those")

    def test_detects_them(self):
        assert _has_referential_language("check them")

    def test_detects_any_of_those(self):
        assert _has_referential_language("any of those")

    def test_no_referential(self):
        assert not _has_referential_language("investigate the code")


class TestExpansionLanguage:
    def test_detects_and_anything_else(self):
        assert _has_expansion_language("investigate those and anything else")

    def test_detects_also_check(self):
        assert _has_expansion_language("also check the docs")

    def test_no_expansion(self):
        assert not _has_expansion_language("investigate those")


class TestNormalizeTerm:
    def test_lowercases(self):
        assert _normalize_term("RSS Channel Diff") == "rss channel diff"

    def test_strips_punctuation(self):
        assert _normalize_term("API rotation, with cooldown!") == "api rotation with cooldown"

    def test_collapses_whitespace(self):
        assert _normalize_term("  multi   key   ") == "multi key"


class TestRealIncident:
    def test_extracts_anchors_from_real_incident(self):
        ctx = HookContext(
            prompt=REAL_INCIDENT_TABLE,
            data={},
            session_id="test_session",
            terminal_id="test_terminal_real",
        )
        result = referent_anchor_hook(ctx)
        # Should write state file (returns empty HookResult - no injection needed)
        assert result.is_empty() or result.context is None

        state_file = Path(HOOKS_DIR) / "state" / "referent_anchors_test_terminal_real.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["extraction_attempted"] is True
        assert len(state["anchor_terms"]) == 6
        assert "rss channel diff detection" in state["anchor_terms"]
        assert state["bypass_scope"] is False
        # Cleanup
        state_file.unlink(missing_ok=True)


class TestNoAnchorsCase:
    def test_writes_no_anchors_status(self):
        ctx = HookContext(
            prompt="simple question with no structure",
            data={},
            session_id="test_session",
            terminal_id="test_terminal_no_anchors",
        )
        referent_anchor_hook(ctx)

        state_file = Path(HOOKS_DIR) / "state" / "referent_anchors_test_terminal_no_anchors.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["status"] == "no_anchors"
        assert state["extraction_attempted"] is True
        # Cleanup
        state_file.unlink(missing_ok=True)


class TestExpansionBypass:
    def test_sets_bypass_when_expansion_present(self):
        prompt = REAL_INCIDENT_TABLE.replace(
            "investigate what is outstanding",
            "investigate what is outstanding and anything else you find",
        )
        ctx = HookContext(
            prompt=prompt,
            data={},
            session_id="test_session",
            terminal_id="test_terminal_bypass",
        )
        referent_anchor_hook(ctx)

        state_file = Path(HOOKS_DIR) / "state" / "referent_anchors_test_terminal_bypass.json"
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["bypass_scope"] is True
        # Cleanup
        state_file.unlink(missing_ok=True)


class TestAnchorPreservation:
    def test_preserves_active_anchors_on_followup_message(self):
        """Second message without a table should NOT overwrite active anchors."""
        tid = "test_terminal_preserve"
        state_dir = Path(HOOKS_DIR) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"referent_anchors_{tid}.json"

        # First message: table with referential language creates active anchors
        ctx1 = HookContext(
            prompt=REAL_INCIDENT_TABLE,
            data={},
            session_id="test_session",
            terminal_id=tid,
        )
        referent_anchor_hook(ctx1)
        state1 = json.loads(state_file.read_text(encoding="utf-8"))
        assert len(state1["anchor_terms"]) == 6

        # Second message: referential but no table — must NOT overwrite
        ctx2 = HookContext(
            prompt="Before checking those, show me the recent git log for the hooks directory.",
            data={},
            session_id="test_session",
            terminal_id=tid,
        )
        referent_anchor_hook(ctx2)
        state2 = json.loads(state_file.read_text(encoding="utf-8"))
        assert len(state2["anchor_terms"]) == 6  # Preserved!
        assert "status" not in state2  # Still active, not no_anchors

        # Cleanup
        state_file.unlink(missing_ok=True)

    def test_no_anchors_still_written_when_no_existing_state(self):
        """No existing state → write no_anchors normally."""
        ctx = HookContext(
            prompt="simple question with no structure",
            data={},
            session_id="test_session",
            terminal_id="test_terminal_fresh_no_anchors",
        )
        referent_anchor_hook(ctx)
        state_file = Path(HOOKS_DIR) / "state" / "referent_anchors_test_terminal_fresh_no_anchors.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text(encoding="utf-8"))
        assert state["status"] == "no_anchors"
        state_file.unlink(missing_ok=True)


# --- PreToolUse gate tests ---

class TestPreToolUseGate:
    def _write_anchor_state(self, terminal_id: str, anchor_terms: list[str], bypass: bool = False):
        state_dir = Path(HOOKS_DIR) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"referent_anchors_{terminal_id}.json"
        state = {
            "anchor_terms": anchor_terms,
            "source_type": "table",
            "session_id": "test",
            "terminal_id": terminal_id,
            "timestamp": 1234.0,
            "bypass_scope": bypass,
            "extraction_attempted": True,
            "exploration_used": False,
        }
        state_file.write_text(json.dumps(state), encoding="utf-8")
        return state_file

    def test_blocks_zero_overlap_replay_incident(self):
        """Replay actual incident: git diff targeting csf-source has zero overlap."""
        from PreToolUse_referent_scope_gate import run as gate_run

        tid = "test_gate_block"
        self._write_anchor_state(tid, [
            "rss channel diff detection",
            "multi key api rotation",
            "ytinitialplayerresponse json parsing",
        ])

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git diff HEAD~5 --stat -- bin/csf-source"},
            "terminal_id": tid,
        }
        result = gate_run(data)
        assert result["decision"] == "block"
        assert "REFERENT SCOPE MISMATCH" in result["reason"]
        # Cleanup
        (Path(HOOKS_DIR) / "state" / f"referent_anchors_{tid}.json").unlink(missing_ok=True)

    def test_allows_overlap(self):
        from PreToolUse_referent_scope_gate import run as gate_run

        tid = "test_gate_allow"
        self._write_anchor_state(tid, ["rss channel diff detection", "api rotation"])

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "grep -r 'rss channel' packages/yt-is/"},
            "terminal_id": tid,
        }
        result = gate_run(data)
        assert result["decision"] == "allow"
        # Cleanup
        (Path(HOOKS_DIR) / "state" / f"referent_anchors_{tid}.json").unlink(missing_ok=True)

    def test_allows_no_state_file(self):
        from PreToolUse_referent_scope_gate import run as gate_run

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
            "terminal_id": "nonexistent_terminal",
        }
        result = gate_run(data)
        assert result["decision"] == "allow"
        assert "no state file" in result["reason"]

    def test_allows_bypass_scope(self):
        from PreToolUse_referent_scope_gate import run as gate_run

        tid = "test_gate_bypass"
        self._write_anchor_state(tid, ["rss channel diff"], bypass=True)

        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "git diff HEAD~5"},
            "terminal_id": tid,
        }
        result = gate_run(data)
        assert result["decision"] == "allow"
        # Cleanup
        (Path(HOOKS_DIR) / "state" / f"referent_anchors_{tid}.json").unlink(missing_ok=True)

    def test_allows_non_gated_tool(self):
        from PreToolUse_referent_scope_gate import run as gate_run

        tid = "test_gate_nongated"
        self._write_anchor_state(tid, ["rss channel diff"])

        data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file.py"},
            "terminal_id": tid,
        }
        result = gate_run(data)
        assert result["decision"] == "allow"
        # Cleanup
        (Path(HOOKS_DIR) / "state" / f"referent_anchors_{tid}.json").unlink(missing_ok=True)


# --- Stop hook tests ---

class TestStopCoverage:
    def _write_anchor_state(self, terminal_id: str, anchor_terms: list[str]):
        state_dir = Path(HOOKS_DIR) / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / f"referent_anchors_{terminal_id}.json"
        state = {
            "anchor_terms": anchor_terms,
            "source_type": "table",
            "session_id": "test",
            "terminal_id": terminal_id,
            "timestamp": 1234.0,
            "bypass_scope": False,
            "extraction_attempted": True,
            "exploration_used": False,
        }
        state_file.write_text(json.dumps(state), encoding="utf-8")
        return state_file

    def test_advisory_on_zero_coverage(self):
        """Import _run_referent_coverage from Stop.py"""
        # We test the logic directly to avoid importing all of Stop.py
        from Stop import _run_referent_coverage

        tid = "test_stop_zero"
        self._write_anchor_state(tid, [
            "rss channel diff detection",
            "multi key api rotation",
            "ytinitialplayerresponse json parsing",
        ])

        data = {
            "response": "I investigated the three bugs from last session.",
            "terminal_id": tid,
        }
        result = _run_referent_coverage(data)
        assert result is not None
        assert result["decision"] == "allow"
        assert "ADVISORY" in result["systemMessage"]
        # State file should persist (Stop doesn't manage lifecycle)
        state_file = Path(HOOKS_DIR) / "state" / f"referent_anchors_{tid}.json"
        assert state_file.exists()
        state_file.unlink(missing_ok=True)

    def test_allows_when_covered(self):
        from Stop import _run_referent_coverage

        tid = "test_stop_covered"
        self._write_anchor_state(tid, [
            "rss channel diff detection",
            "multi key api rotation",
            "ytinitialplayerresponse json parsing",
        ])

        data = {
            "response": "I found that RSS channel diff detection is already implemented.",
            "terminal_id": tid,
        }
        result = _run_referent_coverage(data)
        assert result is None  # No advisory when covered
        # State file should persist (Stop doesn't manage lifecycle)
        state_file = Path(HOOKS_DIR) / "state" / f"referent_anchors_{tid}.json"
        assert state_file.exists()
        state_file.unlink(missing_ok=True)

    def test_no_state_file_returns_none(self):
        from Stop import _run_referent_coverage

        data = {
            "response": "some response",
            "terminal_id": "nonexistent_stop",
        }
        result = _run_referent_coverage(data)
        assert result is None
