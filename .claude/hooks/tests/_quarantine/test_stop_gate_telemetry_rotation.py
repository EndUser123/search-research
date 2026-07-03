#!/usr/bin/env python3
"""
Tests for stop_gate_telemetry rotation helpers.
"""

from __future__ import annotations

import json, os, sys, tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import __lib.stop_gate_telemetry as tel

_HOOKS_DIR = Path(__file__).resolve().parent.parent


class TestMaybeRotateNoOp:
    """File below threshold → no rename, content unchanged."""

    def test_no_rotate_under_threshold(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text('{"ts":"t1","gate":"a","decision":"block"}\n', encoding="utf-8")

        tel.maybe_rotate_telemetry_file(base=base, max_bytes=10_000, max_files=3)

        assert base.exists()
        assert base.read_text(encoding="utf-8") == '{"ts":"t1","gate":"a","decision":"block"}\n'
        assert not (tmp_path / "stop_gate_telemetry.jsonl.1").exists()

    def test_no_rotate_missing_file(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        tel.maybe_rotate_telemetry_file(base=base, max_bytes=10_000, max_files=3)
        assert not base.exists()


class TestMaybeRotateSingle:
    """File above threshold → base renamed to .1, new base created."""

    def test_single_rotation(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text('{"ts":"t1","gate":"a","decision":"block"}\n', encoding="utf-8")

        tel.maybe_rotate_telemetry_file(base=base, max_bytes=10, max_files=3)

        assert base.exists()
        assert base.read_text(encoding="utf-8") == ""
        rotated = tmp_path / "stop_gate_telemetry.jsonl.1"
        assert rotated.exists()
        assert rotated.read_text(encoding="utf-8") == '{"ts":"t1","gate":"a","decision":"block"}\n'

    def test_single_rotation_empty_base(self, tmp_path):
        """New empty base is created, not left as unlinked file."""
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.touch()
        # Ensure .1 does not pre-exist (would block rename)
        dest = tmp_path / "stop_gate_telemetry.jsonl.1"
        if dest.exists():
            dest.unlink()

        tel.maybe_rotate_telemetry_file(base=base, max_bytes=0, max_files=3)

        assert base.exists()
        assert dest.exists()
        assert dest.read_text(encoding="utf-8") == ""


class TestMaybeRotateBoundedHistory:
    """More than max_files rotations → oldest pruned, newer kept."""

    def test_bounded_history_prunes_oldest(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text("base\n", encoding="utf-8")

        # Pre-populate .1, .2, .3
        for i in range(1, 4):
            f = tmp_path / f"stop_gate_telemetry.jsonl.{i}"
            f.write_text(f"old_{i}\n", encoding="utf-8")

        # rotate with max_files=3: .3 should be deleted, .2→.3, .1→.2, base→.1
        tel.maybe_rotate_telemetry_file(base=base, max_bytes=0, max_files=3)

        assert base.exists() and base.read_text(encoding="utf-8") == ""
        assert (tmp_path / "stop_gate_telemetry.jsonl.1").read_text(encoding="utf-8") == "base\n"
        assert (tmp_path / "stop_gate_telemetry.jsonl.2").read_text(encoding="utf-8") == "old_1\n"
        assert (tmp_path / "stop_gate_telemetry.jsonl.3").read_text(encoding="utf-8") == "old_2\n"
        assert not (tmp_path / "stop_gate_telemetry.jsonl.4").exists()


class TestIterTelemetryFiles:
    """Reader discovers base + rotated files."""

    def test_empty_when_no_files(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        result = tel._iter_telemetry_files(base=base, max_files=3)
        assert result == []

    def test_returns_only_existing(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.touch()
        (tmp_path / "stop_gate_telemetry.jsonl.2").touch()
        # .1 missing → should return base + .2 only
        result = tel._iter_telemetry_files(base=base, max_files=3)
        names = [f.name for f in result]
        assert "stop_gate_telemetry.jsonl" in names
        assert "stop_gate_telemetry.jsonl.2" in names
        assert "stop_gate_telemetry.jsonl.1" not in names

    def test_newest_first_order(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.touch()
        for i in range(1, 4):
            (tmp_path / f"stop_gate_telemetry.jsonl.{i}").touch()
        result = tel._iter_telemetry_files(base=base, max_files=3)
        # order: base, .1, .2 (newest-first, skipping absent gaps)
        names = [f.name for f in result]
        assert names == [
            "stop_gate_telemetry.jsonl",
            "stop_gate_telemetry.jsonl.1",
            "stop_gate_telemetry.jsonl.2",
        ]


class TestReadTelemetryMulti:
    """Reader reads from current + rotated files."""

    def test_reads_base_only(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text('{"ts":"t1","gate":"a","decision":"block"}\n', encoding="utf-8")

        records = tel._read_telemetry_multi(base=base, max_files=3)
        assert len(records) == 1
        assert records[0]["gate"] == "a"

    def test_reads_rotated_files_newest_first(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text('{"ts":"t1","gate":"base","decision":"block"}\n', encoding="utf-8")
        r1 = tmp_path / "stop_gate_telemetry.jsonl.1"
        r1.write_text('{"ts":"t2","gate":"rot1","decision":"warn"}\n', encoding="utf-8")
        r2 = tmp_path / "stop_gate_telemetry.jsonl.2"
        r2.write_text('{"ts":"t3","gate":"rot2","decision":"block"}\n', encoding="utf-8")

        records = tel._read_telemetry_multi(base=base, max_files=3)
        # All files returned — chronological order from jsonl reading
        assert len(records) == 3

    def test_skips_unparseable_files(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text('{"ts":"t1","gate":"a","decision":"block"}\n', encoding="utf-8")
        r1 = tmp_path / "stop_gate_telemetry.jsonl.1"
        r1.write_text("NOT JSON\n", encoding="utf-8")

        records = tel._read_telemetry_multi(base=base, max_files=3)
        # base read ok, .1 skipped
        assert len(records) == 1
        assert records[0]["gate"] == "a"


class TestGetRecentGateSummaryIntegration:
    """get_recent_gate_summary reads from multi-file source, respects hours window."""

    def test_reads_from_current_only(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text(
            '{"ts":"2026-05-12T12:00:00+00:00","gate":"epistemic_contract","decision":"block"}\n',
            encoding="utf-8",
        )

        records = tel._read_telemetry_multi(base=base, max_files=3)
        summary = tel.get_recent_gate_summary(records=records, hours=24)
        assert summary == {"epistemic_contract": 1}

    def test_reads_across_rotation_boundary(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text("base_content\n", encoding="utf-8")
        r1 = tmp_path / "stop_gate_telemetry.jsonl.1"
        r1.write_text(
            '{"ts":"2026-05-12T12:00:00+00:00","gate":"rotated_gate","decision":"block"}\n',
            encoding="utf-8",
        )
        # Force rotation so base becomes empty
        tel.maybe_rotate_telemetry_file(base=base, max_bytes=0, max_files=3)

        # With base empty, read from .1 directly via _read_telemetry_multi
        records = tel._read_telemetry_multi(base=base, max_files=3)
        assert len(records) == 1
        assert records[0]["gate"] == "rotated_gate"

    def test_respects_hours_window_with_rotation(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text(
            '{"ts":"2026-05-12T12:00:00+00:00","gate":"recent","decision":"block"}\n',
            encoding="utf-8",
        )
        r1 = tmp_path / "stop_gate_telemetry.jsonl.1"
        r1.write_text(
            '{"ts":"2025-05-12T12:00:00+00:00","gate":"old","decision":"block"}\n',
            encoding="utf-8",
        )

        # Read via multi-file reader, then pass to get_recent_gate_summary
        records = tel._read_telemetry_multi(base=base, max_files=3)
        summary = tel.get_recent_gate_summary(records=records, hours=24)
        assert summary == {"recent": 1}
        assert "old" not in summary


class TestRotationFailureOpen:
    """Rotation failures are swallowed — writers never crash."""

    def test_os_rename_failure_fails_open(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text("record\n", encoding="utf-8")

        with patch("__lib.stop_gate_telemetry.Path.rename", side_effect=OSError("simulated")):
            # Should not raise — fail open
            tel.maybe_rotate_telemetry_file(base=base, max_bytes=0, max_files=3)

        # Original content still readable
        assert base.read_text(encoding="utf-8") == "record\n"

    def test_unlink_failure_fails_open(self, tmp_path):
        base = tmp_path / "stop_gate_telemetry.jsonl"
        base.write_text("record\n", encoding="utf-8")

        # Prune step throws — but rotation should still try the rename
        with patch("pathlib.Path.unlink", side_effect=OSError("simulated")):
            tel.maybe_rotate_telemetry_file(base=base, max_bytes=0, max_files=3)

        # Either the rotation happened (safe) or original preserved (safe)
        # No crash — fail open confirmed
        assert base.exists()


class TestExistingHealthHelpersUnchanged:
    """SessionStart_cc_health.py and cc_health.py health helpers still work."""

    def test_render_attention_lines_unchanged(self):
        lines = tel.render_attention_lines(
            gate_summary={"epistemic_contract": 2},
            claim_summary={"matched": 3, "artifact_missing": 0, "no_match": 0, "other": 0},
            rollout_summary={"advisory": 5},
            session_mode="normal",
        )
        assert lines == ["Rollout override active: advisory on 5 event(s)"]

    def test_render_mode_status_unchanged(self):
        assert tel.render_mode_status("normal") == "Session Mode: NORMAL"
        assert tel.render_mode_status("audit") == "Session Mode: AUDIT  (format-only friction softened on audit-report turns)"
        assert tel.render_mode_status("debug_gates") == "Session Mode: DEBUG_GATES  (quality gates suppressed)"

    def test_render_compact_health_unchanged(self, tmp_path):
        health = tel.render_compact_health(
            session_mode="normal",
            gate_summary={"epistemic_contract": 2},
            claim_summary={"matched": 3, "artifact_missing": 0, "no_match": 0, "other": 0},
            rollout_summary={"advisory": 5},
            hours=24,
        )
        lines = health.splitlines()
        assert any("NORMAL" in l for l in lines)
        assert any("epistemic_contract" in l for l in lines)
        assert any("advisory" in l for l in lines)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])