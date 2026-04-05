"""Tests for core/session_chain.py — session chain traversal via handoff files and sessions-index."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from core.session_chain import (
    SessionChainEntry,
    SessionChainResult,
    _extract_first_user_message,
    _find_handoff_referencing,
    _get_prior_transcript_path,
    _handoff_dir,
    _projects_dir,
    _resolve_transcript_path,
    get_all_chain_files,
    load_sessions_index,
    walk_handoff_chain,
    walk_session_chain,
    walk_sessions_index_chain,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_projects_dir(tmp_path: Path) -> Path:
    """Fake ~/.claude/projects/ directory."""
    fake_projects = tmp_path / ".claude" / "projects"
    fake_projects.mkdir(parents=True)
    return fake_projects


@pytest.fixture
def mock_handoff_dir(tmp_path: Path) -> Path:
    """Fake ~/.claude/state/handoff/ directory."""
    fake_handoff = tmp_path / ".claude" / "state" / "handoff"
    fake_handoff.mkdir(parents=True)
    return fake_handoff


@pytest.fixture
def fake_transcript(tmp_path: Path) -> Path:
    """A fake session transcript .jsonl file."""
    transcript_file = tmp_path / "fake_session.jsonl"
    transcript_file.write_text(
        json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": "/compact"}]}})
        + "\n",
        encoding="utf-8",
    )
    return transcript_file


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class TestSessionChainEntry:
    def test_fields(self) -> None:
        entry = SessionChainEntry(
            session_id="abc",
            transcript_path=Path("/foo/bar.jsonl"),
            parent_transcript_path=Path("/foo/baz.jsonl"),
            created=datetime(2026, 3, 31, 10, 0, 0),
            first_user_message="/compact",
        )
        assert entry.session_id == "abc"
        assert entry.transcript_path == Path("/foo/bar.jsonl")
        assert entry.parent_transcript_path == Path("/foo/baz.jsonl")
        assert entry.created == datetime(2026, 3, 31, 10, 0, 0)
        assert entry.first_user_message == "/compact"

    def test_optional_parent(self) -> None:
        entry = SessionChainEntry(
            session_id="abc",
            transcript_path=Path("/foo/bar.jsonl"),
            parent_transcript_path=None,
            created=None,
        )
        assert entry.parent_transcript_path is None
        assert entry.created is None


class TestSessionChainResult:
    def test_defaults(self) -> None:
        result = SessionChainResult()
        assert result.entries == []
        assert result.depth == 0
        assert result.origin_session_id is None

    def test_with_entries(self) -> None:
        entry = SessionChainEntry(
            session_id="abc",
            transcript_path=Path("/foo/bar.jsonl"),
            parent_transcript_path=None,
            created=None,
        )
        result = SessionChainResult(entries=[entry], depth=1, origin_session_id="abc")
        assert len(result.entries) == 1
        assert result.depth == 1
        assert result.origin_session_id == "abc"


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


class TestPathHelpers:
    def test_projects_dir_returns_pathlib(self) -> None:
        result = _projects_dir()
        assert isinstance(result, Path)
        assert result.name == "projects"

    def test_handoff_dir_returns_pathlib(self) -> None:
        result = _handoff_dir()
        assert isinstance(result, Path)
        assert "handoff" in str(result)


# ---------------------------------------------------------------------------
# _resolve_transcript_path
# ---------------------------------------------------------------------------


class TestResolveTranscriptPath:
    def test_returns_none_for_unknown_session(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)
        result = _resolve_transcript_path("00000000-0000-0000-0000-000000000000")
        assert result is None


# ---------------------------------------------------------------------------
# _get_prior_transcript_path
# ---------------------------------------------------------------------------


class TestGetPriorTranscriptPath:
    def test_returns_path_from_handoff_file(
        self, mock_handoff_dir: Path, fake_transcript: Path
    ) -> None:
        handoff_file = mock_handoff_dir / "console_test_handoff.json"
        handoff_file.write_text(
            json.dumps({"resume_snapshot": {"transcript_path": str(fake_transcript)}}),
            encoding="utf-8",
        )
        with patch("core.session_chain._handoff_dir", return_value=mock_handoff_dir):
            result = _get_prior_transcript_path(handoff_file)
        assert result == fake_transcript

    def test_returns_none_for_nonexistent_handoff(self, mock_handoff_dir: Path) -> None:
        result = _get_prior_transcript_path(mock_handoff_dir / "nonexistent.json")
        assert result is None

    def test_returns_none_for_invalid_json(self, mock_handoff_dir: Path) -> None:
        handoff_file = mock_handoff_dir / "bad_handoff.json"
        handoff_file.write_text("not valid json{", encoding="utf-8")
        result = _get_prior_transcript_path(handoff_file)
        assert result is None


# ---------------------------------------------------------------------------
# _find_handoff_referencing
# ---------------------------------------------------------------------------


class TestFindHandoffReferencing:
    def test_returns_none_when_no_match(
        self, mock_handoff_dir: Path, fake_transcript: Path
    ) -> None:
        with patch("core.session_chain._handoff_dir", return_value=mock_handoff_dir):
            result = _find_handoff_referencing(fake_transcript)
        assert result is None

    def test_finds_matching_handoff(self, mock_handoff_dir: Path, fake_transcript: Path) -> None:
        handoff_file = mock_handoff_dir / "console_abc123_handoff.json"
        handoff_file.write_text(
            json.dumps({"resume_snapshot": {"transcript_path": str(fake_transcript)}}),
            encoding="utf-8",
        )
        with patch("core.session_chain._handoff_dir", return_value=mock_handoff_dir):
            result = _find_handoff_referencing(fake_transcript)
        assert result == handoff_file

    def test_returns_none_for_empty_dir(
        self, mock_handoff_dir: Path, fake_transcript: Path
    ) -> None:
        with patch("core.session_chain._handoff_dir", return_value=mock_handoff_dir):
            result = _find_handoff_referencing(fake_transcript)
        assert result is None


# ---------------------------------------------------------------------------
# _extract_first_user_message
# ---------------------------------------------------------------------------


class TestExtractFirstUserMessage:
    def test_returns_first_user_text(self, tmp_path: Path) -> None:
        transcript = tmp_path / "session.jsonl"
        transcript.write_text(
            json.dumps({"type": "file-history-snapshot", "data": {}})
            + "\n"
            + json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": [
                            {"type": "text", "text": "Hello world this is the first message"}
                        ]
                    },
                }
            )
            + "\n"
            + json.dumps(
                {
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": "Second message"}]},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = _extract_first_user_message(transcript)
        assert result == "Hello world this is the first message"

    def test_returns_none_for_empty_file(self, tmp_path: Path) -> None:
        transcript = tmp_path / "empty.jsonl"
        transcript.write_text("", encoding="utf-8")
        result = _extract_first_user_message(transcript)
        assert result is None

    def test_returns_truncated_text_at_200_chars(self, tmp_path: Path) -> None:
        long_text = "A" * 500
        transcript = tmp_path / "session.jsonl"
        transcript.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": long_text}]},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = _extract_first_user_message(transcript)
        assert result is not None
        assert len(result) == 200
        assert result == "A" * 200

    def test_skips_non_user_entries(self, tmp_path: Path) -> None:
        transcript = tmp_path / "session.jsonl"
        transcript.write_text(
            json.dumps({"type": "file-history-snapshot", "data": {}})
            + "\n"
            + json.dumps({"type": "agent", "message": {"content": "Agent response"}})
            + "\n"
            + json.dumps(
                {
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": "First user message"}]},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = _extract_first_user_message(transcript)
        assert result == "First user message"


# ---------------------------------------------------------------------------
# walk_handoff_chain
# ---------------------------------------------------------------------------


class TestWalkHandoffChain:
    def test_returns_empty_for_unknown_session(self) -> None:
        with patch("core.session_chain._projects_dir", return_value=Path("/nonexistent")):
            result = walk_handoff_chain("00000000-0000-0000-0000-000000000000")
        assert result.depth == 0
        assert result.entries == []

    def test_single_session_no_prior_handoff(
        self, mock_projects_dir: Path, mock_handoff_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Write a transcript file directly in the projects dir
        project = mock_projects_dir / "P--"
        project.mkdir(parents=True)
        session_file = project / "standalone.jsonl"
        session_file.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": "Just a regular session"}]},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)
        monkeypatch.setattr("core.session_chain._handoff_dir", lambda: mock_handoff_dir)

        result = walk_handoff_chain("standalone")
        assert result.depth == 1
        assert len(result.entries) == 1
        assert result.entries[0].session_id == "standalone"
        assert result.entries[0].parent_transcript_path is None


# ---------------------------------------------------------------------------
# load_sessions_index
# ---------------------------------------------------------------------------


class TestLoadSessionsIndex:
    def test_returns_dict(self, tmp_path: Path) -> None:
        project = tmp_path / "P--"
        project.mkdir()
        index_file = project / "sessions-index.json"
        index_file.write_text(
            json.dumps(
                {
                    "00000000-0000-0000-0000-000000000001": {
                        "sessionId": "00000000-0000-0000-0000-000000000001"
                    }
                }
            ),
            encoding="utf-8",
        )
        result = load_sessions_index(project)
        assert isinstance(result, dict)

    def test_list_format(self, tmp_path: Path) -> None:
        project = tmp_path / "P--"
        project.mkdir()
        index_file = project / "sessions-index.json"
        index_file.write_text(
            json.dumps([{"sessionId": "00000000-0000-0000-0000-000000000001"}]),
            encoding="utf-8",
        )
        result = load_sessions_index(project)
        assert "00000000-0000-0000-0000-000000000001" in result

    def test_nonexistent_path_returns_empty_dict(self, tmp_path: Path) -> None:
        result = load_sessions_index(tmp_path / "nonexistent_path")
        assert result == {}


# ---------------------------------------------------------------------------
# walk_sessions_index_chain
# ---------------------------------------------------------------------------


class TestWalkSessionsIndexChain:
    def test_unknown_session_returns_empty(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = mock_projects_dir / "P--"
        project.mkdir()
        project.joinpath("sessions-index.json").write_text("{}", encoding="utf-8")
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)
        result = walk_sessions_index_chain("00000000-0000-0000-0000-000000000000")
        assert result.depth == 0

    def test_non_compact_session_returns_single_entry(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        project = mock_projects_dir / "P--"
        project.mkdir()
        sid = "11111111-1111-1111-1111-111111111111"
        session_file = project / f"{sid}.jsonl"
        session_file.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": [{"type": "text", "text": "I am not a compact session"}]
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        index_data = {
            sid: {
                "sessionId": sid,
                "fullPath": str(session_file),
                "createdAt": int(
                    datetime(2026, 3, 31, 10, 0, 0, tzinfo=timezone.utc).timestamp() * 1000
                ),
            }
        }
        project.joinpath("sessions-index.json").write_text(json.dumps(index_data), encoding="utf-8")
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)
        result = walk_sessions_index_chain(sid)
        assert result.depth == 1
        assert len(result.entries) == 1
        assert result.entries[0].first_user_message == "I am not a compact session"

    def test_extract_first_user_message_string_content(
        self, mock_projects_dir: Path
    ) -> None:
        """Modern .jsonl format uses string content, not list-of-blocks."""
        p = mock_projects_dir / "test_string_content.jsonl"
        p.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": "Hello, this is a direct string message"
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = _extract_first_user_message(p)
        assert result == "Hello, this is a direct string message"

    def test_extract_first_user_message_list_content(
        self, mock_projects_dir: Path
    ) -> None:
        """Legacy .jsonl format uses content as list of text blocks."""
        p = mock_projects_dir / "test_list_content.jsonl"
        p.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": [{"type": "text", "text": "Legacy block format"}]
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = _extract_first_user_message(p)
        assert result == "Legacy block format"

    def test_extract_first_user_message_command_format(
        self, mock_projects_dir: Path
    ) -> None:
        """Slash command messages use string content with XML-like tags."""
        p = mock_projects_dir / "test_command.jsonl"
        p.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {
                        "content": "<command-name>/compact</command-name>\n"
                        "<command-message>compact</command-message>\n"
                        "<command-args></command-args>"
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        result = _extract_first_user_message(p)
        assert result is not None
        assert "/compact" in result


# ---------------------------------------------------------------------------
# walk_session_chain (unified entry point)
# ---------------------------------------------------------------------------


class TestWalkSessionChain:
    def test_unknown_session_returns_empty(self) -> None:
        with patch("core.session_chain._projects_dir", return_value=Path("/nonexistent")):
            result = walk_session_chain("00000000-0000-0000-0000-000000000000")
        assert result.depth == 0


# ---------------------------------------------------------------------------
# get_all_chain_files
# ---------------------------------------------------------------------------


class TestGetAllChainFiles:
    def test_returns_list_of_paths(self) -> None:
        with patch(
            "core.session_chain.walk_session_chain",
            return_value=SessionChainResult(
                entries=[
                    SessionChainEntry(
                        session_id="abc",
                        transcript_path=Path("/foo/abc.jsonl"),
                        parent_transcript_path=None,
                        created=None,
                    )
                ],
                depth=1,
                origin_session_id="abc",
            ),
        ):
            result = get_all_chain_files("abc")
        assert result == [Path("/foo/abc.jsonl")]

    def test_returns_ordered_paths(self) -> None:
        p1, p2, p3 = Path("/oldest.jsonl"), Path("/middle.jsonl"), Path("/newest.jsonl")
        with patch(
            "core.session_chain.walk_session_chain",
            return_value=SessionChainResult(
                entries=[
                    SessionChainEntry(
                        session_id="a", transcript_path=p1, parent_transcript_path=p2, created=None
                    ),
                    SessionChainEntry(
                        session_id="b", transcript_path=p2, parent_transcript_path=p3, created=None
                    ),
                    SessionChainEntry(
                        session_id="c",
                        transcript_path=p3,
                        parent_transcript_path=None,
                        created=None,
                    ),
                ],
                depth=3,
                origin_session_id="a",
            ),
        ):
            result = get_all_chain_files("c")
        assert result == [p1, p2, p3]
