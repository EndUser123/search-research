"""Tests for core/session_chain.py — identity.json scan strategy."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.session_chain import (
    SessionChainEntry,
    SessionChainResult,
    _projects_dir,
    _resolve_transcript_path,
    _scan_identity_files,
    get_all_chain_files,
    walk_session_chain,
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
def mock_artifacts_dir(tmp_path: Path) -> Path:
    """Fake ~/.claude/.artifacts/ directory."""
    fake_artifacts = tmp_path / ".claude" / ".artifacts"
    fake_artifacts.mkdir(parents=True)
    return fake_artifacts


def _write_identity(
    artifacts_dir: Path,
    terminal_id: str,
    session_id: str,
    transcript_path: str = "",
    transcript_chain: list[str] | None = None,
    captured_at: str = "2026-01-01T00:00:00+00:00",
) -> Path:
    """Helper to write an identity.json file."""
    terminal_dir = artifacts_dir / terminal_id
    terminal_dir.mkdir(parents=True, exist_ok=True)
    identity = {
        "terminal": {"id": terminal_id, "source": "WT_SESSION"},
        "claude": {
            "session_id": session_id,
            "transcript_path": transcript_path,
        },
        "captured_at": captured_at,
    }
    if transcript_chain is not None:
        identity["claude"]["transcript_chain"] = transcript_chain
    identity_file = terminal_dir / "identity.json"
    identity_file.write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
    return identity_file


def _write_transcript(projects_dir: Path, project_name: str, session_id: str) -> Path:
    """Helper to write a fake transcript .jsonl file."""
    project = projects_dir / project_name
    project.mkdir(parents=True, exist_ok=True)
    transcript = project / f"{session_id}.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "user",
                "sessionId": session_id,
                "message": {"content": [{"type": "text", "text": "Hello"}]},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return transcript


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


class TestSessionChainEntry:
    def test_fields(self) -> None:
        entry = SessionChainEntry(
            session_id="abc",
            transcript_path=Path("/foo/bar.jsonl"),
            parent_transcript_path=Path("/foo/baz.jsonl"),
            created=None,
            first_user_message="/compact",
        )
        assert entry.session_id == "abc"
        assert entry.transcript_path == Path("/foo/bar.jsonl")
        assert entry.parent_transcript_path == Path("/foo/baz.jsonl")

    def test_optional_parent(self) -> None:
        entry = SessionChainEntry(
            session_id="abc",
            transcript_path=Path("/foo/bar.jsonl"),
            parent_transcript_path=None,
            created=None,
        )
        assert entry.parent_transcript_path is None


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


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


class TestPathHelpers:
    def test_projects_dir_returns_pathlib(self) -> None:
        result = _projects_dir()
        assert isinstance(result, Path)
        assert result.name == "projects"


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

    def test_session_id_rejects_dotdot(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)
        result = _resolve_transcript_path("../../../etc/passwd")
        assert result is None

    def test_session_id_rejects_forward_slash(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)
        result = _resolve_transcript_path("foo/../../../etc/passwd")
        assert result is None

    def test_session_id_rejects_backslash(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)
        result = _resolve_transcript_path("foo\\..\\..\\etc\\passwd")
        assert result is None

    def test_finds_existing_transcript(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_transcript(mock_projects_dir, "P--", "valid_session")
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)
        result = _resolve_transcript_path("valid_session")
        assert result is not None
        assert result.name == "valid_session.jsonl"


# ---------------------------------------------------------------------------
# _scan_identity_files
# ---------------------------------------------------------------------------


class TestScanIdentityFiles:
    def test_returns_empty_for_no_artifacts(self, tmp_path: Path) -> None:
        with patch("core.session_chain._claude_base", return_value=tmp_path / ".claude"):
            result = _scan_identity_files()
        assert result == {}

    def test_finds_single_identity(
        self, mock_artifacts_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_identity(mock_artifacts_dir, "console_abc", "session-123")
        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = _scan_identity_files()
        assert "session-123" in result
        assert len(result["session-123"]) == 1
        assert result["session-123"][0]["terminal_id"] == "console_abc"

    def test_groups_multiple_terminals_same_session(
        self, mock_artifacts_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_identity(mock_artifacts_dir, "console_abc", "session-123", captured_at="2026-01-01T10:00:00+00:00")
        _write_identity(mock_artifacts_dir, "console_def", "session-123", captured_at="2026-01-02T10:00:00+00:00")
        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = _scan_identity_files()
        assert "session-123" in result
        assert len(result["session-123"]) == 2

    def test_extracts_transcript_chain(
        self, mock_artifacts_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_identity(
            mock_artifacts_dir,
            "console_abc",
            "session-456",
            transcript_chain=["session-100", "session-200"],
        )
        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = _scan_identity_files()
        assert result["session-456"][0]["transcript_chain"] == ["session-100", "session-200"]

    def test_skips_identity_without_session_id(
        self, mock_artifacts_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        terminal_dir = mock_artifacts_dir / "console_empty"
        terminal_dir.mkdir(parents=True)
        identity_file = terminal_dir / "identity.json"
        identity_file.write_text(
            json.dumps({"terminal": {"id": "console_empty"}, "claude": {}}) + "\n",
            encoding="utf-8",
        )
        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = _scan_identity_files()
        assert result == {}

    def test_skips_malformed_json(
        self, mock_artifacts_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        terminal_dir = mock_artifacts_dir / "console_bad"
        terminal_dir.mkdir(parents=True)
        identity_file = terminal_dir / "identity.json"
        identity_file.write_text("not json{", encoding="utf-8")
        _write_identity(mock_artifacts_dir, "console_good", "session-good")
        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = _scan_identity_files()
        assert "session-good" in result
        assert "session-bad" not in result


# ---------------------------------------------------------------------------
# walk_session_chain
# ---------------------------------------------------------------------------


class TestWalkSessionChain:
    def test_single_session_no_chain(
        self, mock_artifacts_dir: Path, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_identity(mock_artifacts_dir, "console_abc", "session-123")
        _write_transcript(mock_projects_dir, "P--", "session-123")

        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)

        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = walk_session_chain("session-123")

        assert result.depth == 1
        assert len(result.entries) == 1
        assert result.entries[0].session_id == "session-123"
        assert result.entries[0].parent_transcript_path is None

    def test_chain_with_transcript_chain(
        self, mock_artifacts_dir: Path, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_identity(
            mock_artifacts_dir,
            "console_abc",
            "session-300",
            transcript_chain=["session-100", "session-200"],
        )
        _write_transcript(mock_projects_dir, "P--", "session-100")
        _write_transcript(mock_projects_dir, "P--", "session-200")
        _write_transcript(mock_projects_dir, "P--", "session-300")

        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)

        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = walk_session_chain("session-300")

        assert result.depth == 3
        assert result.entries[0].session_id == "session-100"
        assert result.entries[1].session_id == "session-200"
        assert result.entries[2].session_id == "session-300"
        # Parent links
        assert result.entries[0].parent_transcript_path is None
        assert result.entries[1].parent_transcript_path == result.entries[0].transcript_path
        assert result.entries[2].parent_transcript_path == result.entries[1].transcript_path

    def test_chain_respects_max_depth(
        self, mock_artifacts_dir: Path, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_identity(
            mock_artifacts_dir,
            "console_abc",
            "session-500",
            transcript_chain=["session-100", "session-200", "session-300", "session-400"],
        )
        for sid in ["session-100", "session-200", "session-300", "session-400", "session-500"]:
            _write_transcript(mock_projects_dir, "P--", sid)

        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)

        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = walk_session_chain("session-500", max_depth=2)

        assert result.depth <= 3  # max_depth=2 from chain + current session

    def test_newest_first_reverses_order(
        self, mock_artifacts_dir: Path, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_identity(
            mock_artifacts_dir,
            "console_abc",
            "session-200",
            transcript_chain=["session-100"],
        )
        _write_transcript(mock_projects_dir, "P--", "session-100")
        _write_transcript(mock_projects_dir, "P--", "session-200")

        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)

        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = walk_session_chain("session-200", newest_first=True)

        assert result.entries[0].session_id == "session-200"
        assert result.entries[1].session_id == "session-100"

    def test_returns_empty_for_unknown_session(
        self, mock_artifacts_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("core.session_chain._projects_dir", lambda: Path("/nonexistent"))
        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = walk_session_chain("nonexistent-session")
        assert result.depth == 0
        assert result.entries == []

    def test_deduplicates_chain_entries(
        self, mock_artifacts_dir: Path, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _write_identity(
            mock_artifacts_dir,
            "console_abc",
            "session-200",
            transcript_chain=["session-100", "session-100"],  # duplicate
        )
        _write_transcript(mock_projects_dir, "P--", "session-100")
        _write_transcript(mock_projects_dir, "P--", "session-200")

        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)

        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = walk_session_chain("session-200")

        # Dedup: session-100 appears once + session-200 = 2 entries
        assert result.depth == 2

    def test_finds_chain_from_different_terminal(
        self, mock_artifacts_dir: Path, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Terminal A has the chain data
        _write_identity(
            mock_artifacts_dir,
            "console_aaa",
            "session-300",
            transcript_chain=["session-100", "session-200"],
        )
        # Terminal B also has same session but no chain
        _write_identity(
            mock_artifacts_dir,
            "console_bbb",
            "session-300",
        )
        _write_transcript(mock_projects_dir, "P--", "session-100")
        _write_transcript(mock_projects_dir, "P--", "session-200")
        _write_transcript(mock_projects_dir, "P--", "session-300")

        monkeypatch.setattr("core.session_chain._projects_dir", lambda: mock_projects_dir)

        with patch("core.session_chain._claude_base", return_value=mock_artifacts_dir.parent):
            result = walk_session_chain("session-300")

        assert result.depth == 3


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
                    SessionChainEntry(session_id="a", transcript_path=p1, parent_transcript_path=None, created=None),
                    SessionChainEntry(session_id="b", transcript_path=p2, parent_transcript_path=p1, created=None),
                    SessionChainEntry(session_id="c", transcript_path=p3, parent_transcript_path=p2, created=None),
                ],
                depth=3,
                origin_session_id="a",
            ),
        ):
            result = get_all_chain_files("c")
        assert result == [p1, p2, p3]
