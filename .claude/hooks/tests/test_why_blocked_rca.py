"""Tests for why_blocked_rca.py — synthetic fixtures only, no real logs."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from why_blocked_rca import (
    _utc,
    _parse_ts,
    read_stop_blocks,
    read_db_blocks,
    read_db_importer,
)


# ── Helpers ────────────────────────────────────────────────────


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r) for r in records) + "\n",
        encoding="utf-8",
    )


def _create_hooks_db(db_path: Path) -> None:
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE hooks ("
        "  id INTEGER PRIMARY KEY, timestamp TEXT, event TEXT,"
        "  hook_name TEXT, reason TEXT, action TEXT,"
        "  session_id TEXT, terminal_id TEXT"
        ")"
    )
    cur.execute(
        "CREATE TABLE importer_diagnostics ("
        "  id INTEGER PRIMARY KEY, timestamp TEXT, hook_name TEXT,"
        "  phase TEXT, session_id TEXT, terminal_id TEXT,"
        "  tool_name TEXT, error_text TEXT"
        ")"
    )
    conn.commit()
    conn.close()


# ── Unit tests ─────────────────────────────────────────────────


class TestUtcNormalization:
    def test_naive_gets_utc(self):
        naive = datetime(2026, 7, 2, 12, 0, 0)
        result = _utc(naive)
        assert result.tzinfo is timezone.utc

    def test_aware_stays_aware(self):
        aware = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)
        result = _utc(aware)
        assert result.tzinfo is timezone.utc

    def test_parse_ts_valid(self):
        dt = _parse_ts("2026-07-02T12:00:00+00:00")
        assert dt is not None
        assert dt.year == 2026

    def test_parse_ts_empty(self):
        assert _parse_ts("") is None

    def test_parse_ts_invalid(self):
        assert _parse_ts("not-a-date") is None


class TestReadStopBlocks:
    def test_reads_all(self, tmp_path: Path):
        recs = [
            {"timestamp": "2026-07-02T10:00:00+00:00", "gate_name": "gate_a",
             "reason": "r1", "session_id": "s1", "terminal_id": "t1"},
            {"timestamp": "2026-07-02T11:00:00+00:00", "gate_name": "gate_b",
             "reason": "r2", "session_id": "s2", "terminal_id": "t2"},
        ]
        # Patch the module's path constant
        import why_blocked_rca as mod
        old = mod._STOP_BLOCKS
        try:
            mod._STOP_BLOCKS = tmp_path / "stop_blocks.jsonl"
            _write_jsonl(mod._STOP_BLOCKS, recs)
            rows = read_stop_blocks()
            assert len(rows) == 2
            assert rows[0]["gate_name"] == "gate_a"
        finally:
            mod._STOP_BLOCKS = old

    def test_filters_by_session(self, tmp_path: Path):
        recs = [
            {"timestamp": "2026-07-02T10:00:00+00:00", "gate_name": "g1",
             "reason": "r", "session_id": "s1", "terminal_id": "t"},
            {"timestamp": "2026-07-02T11:00:00+00:00", "gate_name": "g2",
             "reason": "r", "session_id": "s2", "terminal_id": "t"},
        ]
        import why_blocked_rca as mod
        old = mod._STOP_BLOCKS
        try:
            mod._STOP_BLOCKS = tmp_path / "stop_blocks.jsonl"
            _write_jsonl(mod._STOP_BLOCKS, recs)
            rows = read_stop_blocks(session_ids={"s2"})
            assert len(rows) == 1
            assert rows[0]["session_id"] == "s2"
        finally:
            mod._STOP_BLOCKS = old


class TestReadDbBlocks:
    def test_reads_hooks(self, tmp_path: Path):
        db = tmp_path / "diagnostics.db"
        _create_hooks_db(db)
        conn = sqlite3.connect(str(db))
        conn.execute(
            "INSERT INTO hooks (timestamp, event, hook_name, reason, action, session_id, terminal_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2026-07-02T12:00:00+00:00", "Stop", "my_gate", "reason1", "block", "s1", "t1"),
        )
        conn.commit()
        conn.close()

        import why_blocked_rca as mod
        old_db = mod._DB_PATH
        try:
            mod._DB_PATH = db
            rows = read_db_blocks()
            assert len(rows) == 1
            assert rows[0]["gate_name"] == "my_gate"
            assert rows[0]["action"] == "block"
        finally:
            mod._DB_PATH = old_db


class TestReadDbImporter:
    def test_reads_importer(self, tmp_path: Path):
        db = tmp_path / "diagnostics.db"
        _create_hooks_db(db)
        conn = sqlite3.connect(str(db))
        conn.execute(
            "INSERT INTO importer_diagnostics "
            "(timestamp, hook_name, phase, session_id, terminal_id, tool_name, error_text) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("2026-07-02T12:00:00", "router.py", "Stop", "s1", "", "", "import error"),
        )
        conn.commit()
        conn.close()

        import why_blocked_rca as mod
        old_db = mod._DB_PATH
        try:
            mod._DB_PATH = db
            rows = read_db_importer()
            assert len(rows) == 1
            assert rows[0]["reason"] == "import error"
        finally:
            mod._DB_PATH = old_db


class TestMixedTimestampOrdering:
    """Verify naive and aware timestamps sort correctly (naive assumed UTC)."""

    def test_mixed_sorting(self, tmp_path: Path):
        recs = [
            # Naive timestamp — should be treated as UTC
            {"timestamp": "2026-07-02T08:00:00", "gate_name": "naive_early",
             "reason": "", "session_id": "s1", "terminal_id": ""},
            # Aware UTC — later
            {"timestamp": "2026-07-02T12:00:00+00:00", "gate_name": "aware_later",
             "reason": "", "session_id": "s1", "terminal_id": ""},
            # Aware UTC — earliest
            {"timestamp": "2026-07-02T06:00:00+00:00", "gate_name": "aware_earliest",
             "reason": "", "session_id": "s1", "terminal_id": ""},
        ]
        import why_blocked_rca as mod
        old = mod._STOP_BLOCKS
        try:
            mod._STOP_BLOCKS = tmp_path / "stop_blocks.jsonl"
            _write_jsonl(mod._STOP_BLOCKS, recs)
            rows = read_stop_blocks()
            # All should have valid timestamps (none should be None)
            assert all(r["timestamp"] is not None for r in rows)
            # Sort by timestamp to verify ordering works
            sorted_rows = sorted(rows, key=lambda r: r["timestamp"])
            assert sorted_rows[0]["gate_name"] == "aware_earliest"
            assert sorted_rows[1]["gate_name"] == "naive_early"
            assert sorted_rows[2]["gate_name"] == "aware_later"
        finally:
            mod._STOP_BLOCKS = old
