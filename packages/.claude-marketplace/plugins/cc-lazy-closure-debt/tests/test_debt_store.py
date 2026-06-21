"""Tests for the cc-lazy-closure-debt debt_store module."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

# Make the plugin's __lib__ importable regardless of where pytest is run from.
import sys
from pathlib import Path
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "__lib__"))

from __lib.debt_store import (  # noqa: E402  # __lib__ is the plugin's lib package
    append_deferral,
    recent_deferrals,
    clear_terminal,
    list_terminals,
    resolve_deferral,
    resolve_deferral_by_phrase,
)


class TestAppendAndRead:
    def test_round_trip(self, tmp_path: Path):
        append_deferral("termA", "i'll leave that for now", "excerpt", state_root=tmp_path)
        items = recent_deferrals("termA", state_root=tmp_path)
        assert len(items) == 1
        assert items[0]["terminal_id"] == "termA"
        assert items[0]["phrase"] == "i'll leave that for now"
        assert items[0]["transcript_excerpt"] == "excerpt"
        assert isinstance(items[0]["ts"], int)

    def test_multiple_appends(self, tmp_path: Path):
        for i in range(3):
            append_deferral("termB", f"phrase {i}", "", state_root=tmp_path)
        items = recent_deferrals("termB", state_root=tmp_path, max_count=10)
        assert len(items) == 3
        # Newest first
        assert items[0]["phrase"] == "phrase 2"
        assert items[-1]["phrase"] == "phrase 0"

    def test_duplicate_phrase_is_grouped(self, tmp_path: Path):
        for _ in range(3):
            append_deferral("termDup", "we can leave that for now", "", state_root=tmp_path)
        items = recent_deferrals("termDup", state_root=tmp_path, max_count=10)
        assert len(items) == 1
        assert items[0]["phrase"] == "we can leave that for now"
        assert items[0]["occurrences"] == 3
        assert "fingerprint" in items[0]

    def test_excerpt_truncated_to_200(self, tmp_path: Path):
        long = "x" * 500
        append_deferral("termC", "we can address that later", long, state_root=tmp_path)
        items = recent_deferrals("termC", state_root=tmp_path)
        assert len(items[0]["transcript_excerpt"]) == 200

    def test_terminal_isolation(self, tmp_path: Path):
        append_deferral("term1", "phrase a", "", state_root=tmp_path)
        append_deferral("term2", "phrase b", "", state_root=tmp_path)
        assert len(recent_deferrals("term1", state_root=tmp_path)) == 1
        assert len(recent_deferrals("term2", state_root=tmp_path)) == 1
        assert recent_deferrals("term1", state_root=tmp_path)[0]["phrase"] == "phrase a"

    def test_unsafe_id_sanitized(self, tmp_path: Path):
        append_deferral(r"a/b\c:d*e?f" + chr(34) + r"g<h>i|j", "phrase X", "", state_root=tmp_path)
        items = recent_deferrals(r"a/b\c:d*e?f" + chr(34) + r"g<h>i|j", state_root=tmp_path)
        assert len(items) == 1
        # Filesystem-safe id (..etcpasswd) is what was used on disk
        assert (tmp_path / "cc-lazy-closure-debt" / "a_b_c_d_e_f_g_h_i_j.jsonl").exists()


class TestFiltering:
    def test_max_age_filters_old_items(self, tmp_path: Path, monkeypatch):
        # Insert a backdated record by writing the file directly
        state_dir = tmp_path / "cc-lazy-closure-debt"
        state_dir.mkdir(parents=True, exist_ok=True)
        path = state_dir / "termA.jsonl"
        old_ts = int(time.time()) - (48 * 3600)  # 2 days ago
        path.write_text(
            json.dumps({"ts": old_ts, "terminal_id": "termA", "phrase": "stale", "transcript_excerpt": ""})
            + "\n"
        )
        # And one fresh record
        append_deferral("termA", "fresh", "", state_root=tmp_path)
        items = recent_deferrals("termA", max_age_h=24, state_root=tmp_path)
        assert len(items) == 1
        assert items[0]["phrase"] == "fresh"

    def test_max_count_truncates(self, tmp_path: Path):
        for i in range(10):
            append_deferral("termA", f"phrase {i}", "", state_root=tmp_path)
        items = recent_deferrals("termA", max_count=5, state_root=tmp_path)
        assert len(items) == 5
        # Newest 5 = phrase 5..9
        assert [it["phrase"] for it in items] == [f"phrase {i}" for i in range(9, 4, -1)]


class TestClear:
    def test_clear_existing(self, tmp_path: Path):
        append_deferral("termA", "x", "", state_root=tmp_path)
        assert clear_terminal("termA", state_root=tmp_path) is True
        assert recent_deferrals("termA", state_root=tmp_path) == []

    def test_clear_nonexistent(self, tmp_path: Path):
        assert clear_terminal("termZ", state_root=tmp_path) is False

    def test_list_terminals(self, tmp_path: Path):
        append_deferral("termA", "x", "", state_root=tmp_path)
        append_deferral("termB", "y", "", state_root=tmp_path)
        terms = list_terminals(state_root=tmp_path)
        assert "termA" in terms
        assert "termB" in terms


class TestResolve:
    """Tombstone-based resolution — the fix for duplicate-task re-firing."""

    def test_resolve_by_phrase_stops_resurfacing(self, tmp_path: Path):
        append_deferral("termR", "defer that", "", state_root=tmp_path)
        assert len(recent_deferrals("termR", state_root=tmp_path)) == 1
        resolve_deferral_by_phrase("termR", "defer that", state_root=tmp_path)
        assert recent_deferrals("termR", state_root=tmp_path) == []

    def test_resolve_only_clears_matching_phrase(self, tmp_path: Path):
        append_deferral("termR", "defer that", "", state_root=tmp_path)
        append_deferral("termR", "look into caching later", "", state_root=tmp_path)
        resolve_deferral_by_phrase("termR", "defer that", state_root=tmp_path)
        items = recent_deferrals("termR", state_root=tmp_path, max_count=10)
        assert [it["phrase"] for it in items] == ["look into caching later"]

    def test_resolve_survives_phrase_normalization(self, tmp_path: Path):
        # Stored phrase and the task-subject phrase differ only by surrounding
        # quotes/whitespace/case; normalization must collapse them to one fp.
        append_deferral("termR", "Defer That", "", state_root=tmp_path)
        resolve_deferral_by_phrase("termR", '  "defer that"  ', state_root=tmp_path)
        assert recent_deferrals("termR", state_root=tmp_path) == []

    def test_resolve_by_fingerprint_directly(self, tmp_path: Path):
        from __lib.debt_store import _fingerprint_phrase
        append_deferral("termR", "we can address that later", "", state_root=tmp_path)
        fp = _fingerprint_phrase("we can address that later")
        resolve_deferral("termR", fp, state_root=tmp_path)
        assert recent_deferrals("termR", state_root=tmp_path) == []

    def test_tombstone_does_not_count_as_deferral(self, tmp_path: Path):
        # Resolving a phrase that was never appended must not itself surface.
        resolve_deferral_by_phrase("termR", "never deferred", state_root=tmp_path)
        assert recent_deferrals("termR", state_root=tmp_path) == []
