from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evidence_store as es


def _configure_tmp_paths(tmp_path: Path, monkeypatch) -> None:
    session_dir = tmp_path / "session_data"
    monkeypatch.setattr(es, "SESSION_DATA_DIR", session_dir)
    monkeypatch.setattr(es, "EVIDENCE_DB_PATH", session_dir / "evidence.db")


def test_session_context_roundtrip(tmp_path: Path, monkeypatch) -> None:
    _configure_tmp_paths(tmp_path, monkeypatch)

    session_id = "11111111-1111-1111-1111-111111111111"
    assert es.write_session_context(session_id, terminal_id="console_abc")

    ctx = es.read_session_context()
    assert ctx.get("session_id") == session_id
    assert ctx.get("terminal_id") == "console_abc"
    assert es.resolve_session_id("") == session_id


def test_append_and_load_events_scoped_by_session(tmp_path: Path, monkeypatch) -> None:
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    s1 = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    s2 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    assert es.append_tool_event(s1, "console_1", "Read", command="a.py")
    assert es.append_tool_event(s2, "console_2", "Read", command="b.py")
    assert es.append_tool_event(s1, "console_1", "Grep", command="rg foo")

    events_s1 = es.load_tool_events(s1, limit=10)
    events_s2 = es.load_tool_events(s2, limit=10)

    assert [e["name"] for e in events_s1] == ["Read", "Grep"]
    assert [e["name"] for e in events_s2] == ["Read"]
    assert all(e["session_id"] == s1 for e in events_s1)
    assert all(e["session_id"] == s2 for e in events_s2)
