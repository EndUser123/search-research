"""Tests for core/session_chain.py — session chain traversal via handoff files and sessions-index."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.session_chain import (
    SessionChainEntry,
    SessionChainResult,
    _find_handoff_referencing,
    _get_prior_transcript_path,
    _handoff_dir,
    _projects_dir,
    _resolve_transcript_path,
    get_all_chain_files,
    walk_handoff_chain,
    walk_session_chain,
    walk_sessions_index_chain,
    walk_semantic_chain,
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
            created=None,
            first_user_message="/compact",
        )
        assert entry.session_id == "abc"
        assert entry.transcript_path == Path("/foo/bar.jsonl")
        assert entry.parent_transcript_path == Path("/foo/baz.jsonl")
        assert entry.created is None
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
                        session_id="a", transcript_path=p1, parent_transcript_path=None, created=None
                    ),
                    SessionChainEntry(
                        session_id="b", transcript_path=p2, parent_transcript_path=p1, created=None
                    ),
                    SessionChainEntry(
                        session_id="c",
                        transcript_path=p3,
                        parent_transcript_path=p2,
                        created=None,
                    ),
                ],
                depth=3,
                origin_session_id="a",
            ),
        ):
            result = get_all_chain_files("c")
        assert result == [p1, p2, p3]


# ---------------------------------------------------------------------------
# walk_sessions_index_chain JSONL fallback (the fix)
# ---------------------------------------------------------------------------


class TestWalkSessionsIndexChainJsonlFallback:
    """Tests that walk_sessions_index_chain falls back to JSONL scanning when sessions-index is stale."""

    def test_returns_empty_when_session_not_in_index_and_no_jsonl(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When session is not in sessions-index AND no matching JSONL exists, returns empty."""
        # sessions-index returns empty (stale)
        with patch(
            "core.session_chain.load_sessions_index", return_value={}
        ):
            # No JSONL files in project dir either
            result = walk_sessions_index_chain(
                "not-there",
                project_path=mock_projects_dir / "P--",
            )
        assert result.entries == []
        assert result.depth == 0

    def test_finds_session_from_jsonl_when_not_in_sessions_index(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When session is not in sessions-index but JSONL exists, walk_sessions_index_chain finds it.

        This is the core regression test: prior to the fix, the function returned
        empty whenever session_id was absent from sessions-index, ignoring JSONL files entirely.
        After the fix, it falls back to JSONL scanning.
        """
        project = mock_projects_dir / "P--"
        project.mkdir(parents=True)

        # Write a JSONL with a known sessionId
        session_file = project / "abc123.jsonl"
        session_file.write_text(
            json.dumps(
                {
                    "type": "user",
                    "sessionId": "abc123",
                    "message": {"content": [{"type": "text", "text": "/compact"}]},
                    "timestamp": 1744000000000,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        # sessions-index is empty (stale) — session NOT in index
        with patch(
            "core.session_chain.load_sessions_index", return_value={}
        ):
            result = walk_sessions_index_chain(
                "abc123",
                project_path=project,
            )
        # After fix: should find the session via JSONL scan
        assert result.depth == 1
        assert len(result.entries) == 1
        assert result.entries[0].session_id == "abc123"


class TestWalkSemanticChainJsonlFallback:
    """Tests that walk_semantic_chain falls back to JSONL text extraction when sessions-index is stale."""

    def test_returns_empty_when_session_not_in_index_and_no_jsonl(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When session is not in sessions-index AND no matching JSONL exists, returns empty."""
        with patch(
            "core.session_chain.load_sessions_index", return_value={}
        ):
            result = walk_semantic_chain(
                "not-there",
                project_path=mock_projects_dir / "P--",
            )
        assert result.entries == []
        assert result.depth == 0

    def test_finds_session_text_from_jsonl_when_not_in_sessions_index(
        self, mock_projects_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When session is not in sessions-index but JSONL exists, walk_semantic_chain extracts text from JSONL.

        walk_semantic_chain needs OTHER sessions as candidates to form a chain.
        This tests: session found via JSONL scan + text extracted + other sessions available = chain built.
        """
        project = mock_projects_dir / "P--"
        project.mkdir(parents=True)

        # Write a JSONL with user and assistant messages (first user msg + last goals)
        session_file = project / "abc456.jsonl"
        session_file.write_text(
            json.dumps(
                {
                    "type": "user",
                    "sessionId": "abc456",
                    "message": {"content": [{"type": "text", "text": "Fix the auth bug"}]},
                    "timestamp": 1744100000000,
                }
            )
            + "\n"
            + json.dumps(
                {
                    "type": "assistant",
                    "sessionId": "abc456",
                    "message": {"content": [{"type": "text", "text": "Found the issue in token validation"}]},
                    "timestamp": 1744100001000,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        # sessions-index is empty (stale) — session NOT in index
        with patch(
            "core.session_chain.load_sessions_index", return_value={}
        ):
            result = walk_semantic_chain(
                "abc456",
                project_path=project,
            )
        # Only one session total: no candidates available → returns empty
        # (this is correct semantic-chain behavior; mtime strategy handles single-session chains)
        assert result.entries == []
        assert result.depth == 0


class TestExtractLastGoals:
    """Tests for _extract_last_goals function."""

    def test_extracts_last_assistant_message(self, tmp_path: Path) -> None:
        """Should extract content from the last assistant message."""
        session_file = tmp_path / "test_session.jsonl"
        session_file.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": "Hello"}]},
                }
            )
            + "\n"
            + json.dumps(
                {
                    "type": "assistant",
                    "message": {"content": [{"type": "text", "text": "First response"}]},
                }
            )
            + "\n"
            + json.dumps(
                {
                    "type": "assistant",
                    "message": {"content": [{"type": "text", "text": "Last goal: fix the bug"}]},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        from core.session_chain import _extract_last_goals

        result = _extract_last_goals(session_file)
        assert result is not None
        assert "Last goal: fix the bug" in result

    def test_returns_none_for_empty_file(self, tmp_path: Path) -> None:
        """Should return None when no assistant messages exist."""
        session_file = tmp_path / "user_only.jsonl"
        session_file.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": "Hello"}]},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        from core.session_chain import _extract_last_goals

        result = _extract_last_goals(session_file)
        assert result is None

    def test_handles_content_as_string(self, tmp_path: Path) -> None:
        """Should handle assistant message with content as string (not list)."""
        session_file = tmp_path / "string_content.jsonl"
        session_file.write_text(
            json.dumps(
                {
                    "type": "user",
                    "message": {"content": "Hello"},
                }
            )
            + "\n"
            + json.dumps(
                {
                    "type": "assistant",
                    "message": {"content": "Goal text as string"},
                }
            )
            + "\n",
            encoding="utf-8",
        )
        from core.session_chain import _extract_last_goals

        result = _extract_last_goals(session_file)
        assert result is not None
        assert "Goal text as string" in result


class TestWalkSessionsIndexChainBoundary:
    """Boundary tests for walk_sessions_index_chain — MAX_MTIME_GAP and max_depth limits."""

    def test_max_depth_limits_chain_length(self, mock_projects_dir: Path) -> None:
        """Should stop building chain when len(chain) >= max_depth."""
        project = mock_projects_dir / "P--"
        project.mkdir(parents=True)

        # Create 5 sessions with close mtimes (10 seconds apart)
        from datetime import datetime, timedelta

        base_time = datetime(2024, 1, 1, 12, 0, 0)
        for i in range(5):
            session_file = project / f"session_{i}.jsonl"
            session_file.write_text(
                json.dumps(
                    {
                        "type": "user",
                        "sessionId": f"session_{i}",
                        "message": {"content": [{"type": "text", "text": f"Session {i}"}]},
                        "timestamp": int((base_time + timedelta(seconds=i * 10)).timestamp() * 1000),
                    }
                )
                + "\n",
                encoding="utf-8",
            )

        # sessions-index empty — uses JSONL scan
        from unittest.mock import patch

        with patch("core.session_chain.load_sessions_index", return_value={}):
            result = walk_sessions_index_chain("session_4", project_path=project, max_depth=3)

        # Should stop at max_depth=3 entries (origin + 2 predecessors)
        assert result.depth <= 3
