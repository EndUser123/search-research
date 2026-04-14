from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import sys

HOOKS_DIR = Path("P:/.claude/hooks")
sys.path.insert(0, str(HOOKS_DIR))

import cc_diagnostic_logger
import Stop as stop_module


def test_hook_invocation_persists_turn_id(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "diagnostics.db"

    monkeypatch.setattr(cc_diagnostic_logger, "DB_PATH", db_path)
    monkeypatch.setattr(cc_diagnostic_logger, "_local", threading.local())
    monkeypatch.setattr(cc_diagnostic_logger, "DIAGNOSTICS_ENABLED", True)

    cc_diagnostic_logger._init_schema()
    cc_diagnostic_logger.log_hook_invocation(
        hook_name="behavior_contract",
        event_type="UserPromptSubmit",
        action="inject",
        injection_content="If the question is concrete, answer directly.",
        reason="behavior_contract_injection",
        turn_id="turn-abc",
        session_id="session-abc",
        terminal_id="terminal-abc",
    )

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT session_id, terminal_id, turn_id, hook_name, event_type, action, reason
            FROM hooks
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()

    assert row is not None
    assert row == (
        "session-abc",
        "terminal-abc",
        "turn-abc",
        "behavior_contract",
        "UserPromptSubmit",
        "inject",
        "behavior_contract_injection",
    )


def test_init_schema_migrates_existing_hooks_table(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "diagnostics.db"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE hooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                session_id TEXT NOT NULL,
                terminal_id TEXT NOT NULL,
                event TEXT NOT NULL,
                hook_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                action TEXT NOT NULL,
                injection_preview TEXT,
                injection_length INTEGER,
                reason TEXT,
                duration_ms REAL,
                execution_time_ms REAL,
                timeout_ms INTEGER,
                output_size_bytes INTEGER
            )
            """
        )
        conn.commit()

    monkeypatch.setattr(cc_diagnostic_logger, "DB_PATH", db_path)
    monkeypatch.setattr(cc_diagnostic_logger, "_local", threading.local())
    monkeypatch.setattr(cc_diagnostic_logger, "DIAGNOSTICS_ENABLED", True)

    cc_diagnostic_logger._init_schema()

    with sqlite3.connect(db_path) as conn:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(hooks)")]

    assert "turn_id" in columns


def test_query_hook_invocations_filters_by_turn_id(tmp_path, monkeypatch) -> None:
    db_path = tmp_path / "diagnostics.db"

    monkeypatch.setattr(cc_diagnostic_logger, "DB_PATH", db_path)
    monkeypatch.setattr(cc_diagnostic_logger, "_local", threading.local())
    monkeypatch.setattr(cc_diagnostic_logger, "DIAGNOSTICS_ENABLED", True)

    cc_diagnostic_logger._init_schema()
    cc_diagnostic_logger.log_hook_invocation(
        hook_name="behavior_contract",
        event_type="UserPromptSubmit",
        action="inject",
        injection_content="If the question is concrete, answer directly.",
        reason="behavior_contract_injection",
        turn_id="turn-a",
        session_id="session-a",
        terminal_id="terminal-a",
    )
    cc_diagnostic_logger.log_hook_invocation(
        hook_name="Stop.py:behavior_audit",
        event_type="Stop",
        action="block",
        reason="UNVERIFIED CLAIMS",
        turn_id="turn-b",
        session_id="session-b",
        terminal_id="terminal-b",
    )

    rows = cc_diagnostic_logger.query_hook_invocations(days=7, turn_id="turn-b")

    assert len(rows) == 1
    assert rows[0]["turn_id"] == "turn-b"
    assert rows[0]["hook_name"] == "Stop.py:behavior_audit"
    assert rows[0]["action"] == "block"


def test_stop_block_event_forwards_turn_scope(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_logger(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(stop_module, "_log_hook_invocation", fake_logger)

    stop_module._log_stop_block_event(
        {
            "turn_id": "turn-xyz",
            "session_id": "session-xyz",
            "terminal_id": "terminal-xyz",
        },
        "behavior_audit",
        {
            "decision": "block",
            "reason": "UNVERIFIED CLAIMS: missing evidence",
            "blocking_hook": "Stop.py:behavior_audit",
        },
    )

    assert len(calls) == 1
    assert calls[0]["hook_name"] == "Stop.py:behavior_audit"
    assert calls[0]["event_type"] == "Stop"
    assert calls[0]["action"] == "block"
    assert calls[0]["turn_id"] == "turn-xyz"
    assert calls[0]["session_id"] == "session-xyz"
    assert calls[0]["terminal_id"] == "terminal-xyz"
