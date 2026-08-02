"""Tests for extract_user_messages whitespace tolerance (F3-05 fix)."""
import re
import sys
from pathlib import Path

# Add parent dir to path so we can import the module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analyze_session_patterns import extract_user_messages


def _write_temp_chat(tmp_path: Path, lines: list[str]) -> Path:
    """Write a fake chat_history.jsonl file."""
    f = tmp_path / "chat_history.jsonl"
    f.write_text("\n".join(lines), encoding="utf-8")
    return f


def test_exact_match(tmp_path):
    """Standard format: '"type":"user"' with no spaces."""
    f = _write_temp_chat(tmp_path, [
        '{"type":"user","content":[{"type":"text","text":"hello world"}]}',
    ])
    msgs = extract_user_messages(f)
    assert len(msgs) == 1
    assert "hello world" in msgs[0]


def test_space_after_colon(tmp_path):
    """Format drift: '"type": "user"' with space after colon."""
    f = _write_temp_chat(tmp_path, [
        '{"type": "user", "content": [{"type": "text", "text": "space test"}]}',
    ])
    msgs = extract_user_messages(f)
    assert len(msgs) == 1
    assert "space test" in msgs[0]


def test_spaces_around_colon(tmp_path):
    """Format drift: '"type" : "user"' with spaces on both sides."""
    f = _write_temp_chat(tmp_path, [
        '{"type" : "user", "content": [{"type": "text", "text": "both sides"}]}',
    ])
    msgs = extract_user_messages(f)
    assert len(msgs) == 1
    assert "both sides" in msgs[0]


def test_non_user_lines_skipped(tmp_path):
    """Assistant and function lines should not be matched."""
    f = _write_temp_chat(tmp_path, [
        '{"type":"assistant","content":[{"type":"text","text":"response"}]}',
        '{"type":"function","name":"read_file"}',
        '{"type":"user","content":[{"type":"text","text":"real user"}]}',
    ])
    msgs = extract_user_messages(f)
    assert len(msgs) == 1
    assert "real user" in msgs[0]


def test_empty_file(tmp_path):
    """Empty file returns empty list, not crash."""
    f = _write_temp_chat(tmp_path, [])
    msgs = extract_user_messages(f)
    assert msgs == []


def test_file_not_found():
    """Missing file returns empty list (handled by OSError catch)."""
    msgs = extract_user_messages(Path("/nonexistent/path/file.jsonl"))
    assert msgs == []


def test_empty_messages_returns_empty(tmp_path):
    """File with no user-type lines returns empty list."""
    f = _write_temp_chat(tmp_path, [
        '{"type":"assistant","content":[]}',
        '{"type":"system"}',
    ])
    msgs = extract_user_messages(f)
    assert msgs == []
