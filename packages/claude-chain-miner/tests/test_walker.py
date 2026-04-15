from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from scripts import walker


def _write_handoff(
    handoff_dir: Path,
    transcript_path: Path,
    *,
    prior_transcript_path: str = "N/A",
) -> Path:
    handoff_dir.mkdir(parents=True, exist_ok=True)
    handoff_path = handoff_dir / "console_test_handoff.json"
    payload = {
        "resume_snapshot": {
            "transcript_path": str(transcript_path),
            "prior_transcript_path": prior_transcript_path,
            "created_at": "2026-04-14T00:00:00",
        }
    }
    handoff_path.write_text(json.dumps(payload), encoding="utf-8")
    return handoff_path


def test_resolve_transcript_from_session_id_prefers_exact_filename(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_dir = tmp_path / ".claude" / "projects"
    project_dir = projects_dir / "P--"
    project_dir.mkdir(parents=True)

    session_id = "123e4567-e89b-12d3-a456-426614174000"
    target = project_dir / f"{session_id}.jsonl"
    target.write_text("{}", encoding="utf-8")

    monkeypatch.setattr(walker, "_PROJECTS_DIR", projects_dir)

    resolved = walker._resolve_transcript_from_session_id(session_id)

    assert resolved == target


def test_walk_handoff_chain_uses_explicit_transcript_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_dir = tmp_path / ".claude" / "projects"
    project_dir = projects_dir / "P--"
    project_dir.mkdir(parents=True)
    handoff_dir = tmp_path / ".claude" / "state" / "handoff"

    session_id = "123e4567-e89b-12d3-a456-426614174001"
    transcript_path = project_dir / f"{session_id}.jsonl"
    transcript_path.write_text("{}", encoding="utf-8")
    _write_handoff(handoff_dir, transcript_path)

    def _fail_if_called() -> Path:
        raise AssertionError("mtime fallback should not be used when transcript_path is explicit")

    monkeypatch.setattr(walker, "_PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(walker, "_HANDOFF_DIR", handoff_dir)
    monkeypatch.setattr(walker, "_project_handoff_dir", lambda: handoff_dir)
    monkeypatch.setattr(walker, "_resolve_current_transcript", _fail_if_called)

    entries, origin = walker.walk_handoff_chain(
        start_session_id=None,
        start_transcript_path=transcript_path,
        max_depth=5,
    )

    assert origin == session_id
    assert len(entries) == 1
    assert entries[0].session_id == session_id
    assert entries[0].transcript_path == transcript_path


def test_walk_handoff_chain_resolves_from_session_id_when_path_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    projects_dir = tmp_path / ".claude" / "projects"
    project_dir = projects_dir / "P--"
    project_dir.mkdir(parents=True)
    handoff_dir = tmp_path / ".claude" / "state" / "handoff"

    session_id = "123e4567-e89b-12d3-a456-426614174002"
    transcript_path = project_dir / f"{session_id}.jsonl"
    transcript_path.write_text("{}", encoding="utf-8")
    _write_handoff(handoff_dir, transcript_path)

    def _fail_if_called() -> Path:
        raise AssertionError("mtime fallback should not be used when session_id resolves")

    monkeypatch.setattr(walker, "_PROJECTS_DIR", projects_dir)
    monkeypatch.setattr(walker, "_HANDOFF_DIR", handoff_dir)
    monkeypatch.setattr(walker, "_project_handoff_dir", lambda: handoff_dir)
    monkeypatch.setattr(walker, "_resolve_current_transcript", _fail_if_called)

    entries, origin = walker.walk_handoff_chain(
        start_session_id=session_id,
        max_depth=5,
    )

    assert origin == session_id
    assert len(entries) == 1
    assert entries[0].transcript_path == transcript_path


def test_resolve_start_anchor_uses_env_transcript_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    projects_dir = tmp_path / ".claude" / "projects"
    project_dir = projects_dir / "P--"
    project_dir.mkdir(parents=True)

    session_id = "123e4567-e89b-12d3-a456-426614174003"
    transcript_path = project_dir / f"{session_id}.jsonl"
    transcript_path.write_text("{}", encoding="utf-8")

    monkeypatch.setenv("CLAUDE_TRANSCRIPT_PATH", str(transcript_path))
    monkeypatch.setattr(walker, "_candidate_projects_dirs", lambda: [projects_dir])

    resolved_session_id, resolved_path, source = walker.resolve_start_anchor(cwd=tmp_path)

    assert source == "env_transcript_path"
    assert resolved_session_id == session_id
    assert resolved_path == transcript_path


def test_resolve_start_anchor_uses_sessions_index_when_env_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    projects_dir = tmp_path / ".claude" / "projects"
    project_dir = projects_dir / "P--"
    project_dir.mkdir(parents=True)
    session_index = tmp_path / ".claude" / "sessions.json"
    session_index.parent.mkdir(parents=True, exist_ok=True)

    session_id = "123e4567-e89b-12d3-a456-426614174004"
    transcript_path = project_dir / f"{session_id}.jsonl"
    transcript_path.write_text("{}", encoding="utf-8")

    session_index.write_text(
        json.dumps(
            [
                {
                    "session_id": session_id,
                    "working_directory": str(tmp_path),
                    "claude_project_dir": str(tmp_path),
                    "status": "active",
                }
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_SESSION_ID", raising=False)
    monkeypatch.delenv("CLAUDE_TRANSCRIPT_PATH", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_TRANSCRIPT_PATH", raising=False)
    monkeypatch.setattr(walker, "_candidate_projects_dirs", lambda: [projects_dir])
    monkeypatch.setattr(walker, "_candidate_session_index_paths", lambda: [session_index])

    resolved_session_id, resolved_path, source = walker.resolve_start_anchor(cwd=tmp_path)

    assert source == "session_index"
    assert resolved_session_id == session_id
    assert resolved_path == transcript_path
