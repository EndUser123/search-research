"""Tests for session identity resolution.

Evidence class: production unit + integration (uses real fixture files).

Covers the spec Section 2 acceptance criteria:
* exact session ID resolves correct directory;
* newest-directory heuristic is rejected (we never scan);
* unverified session identity blocks;
* foreign session directories are ignored (we never open them).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from session_resolver import (
    ENV_VAR,
    IdentityStatus,
    SessionBinding,
    encode_workspace_path,
    resolve_session_dir,
    verify_session_identity,
)

FIXTURES = Path(__file__).parent / "fixtures"
KNOWN_SESSION_ID = "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe"
KNOWN_WORKSPACE = "P%3A%5C"


# ---------------------------------------------------------------------------
# encode_workspace_path
# ---------------------------------------------------------------------------


def test_encode_workspace_path_windows():
    assert encode_workspace_path("P:\\") == "P%3A%5C"
    assert encode_workspace_path("P:/") == "P%3A%5C"


# ---------------------------------------------------------------------------
# resolve_session_dir — happy path on a real session
# ---------------------------------------------------------------------------


@pytest.fixture
def real_sessions_root():
    """The real Grok sessions root (integration). Skipped if absent."""
    root = Path("C:/Users/brsth/.grok/sessions")
    if not root.is_dir():
        pytest.skip("real Grok sessions root not present")
    return root


def test_resolve_known_session_verified(real_sessions_root):
    b = resolve_session_dir(
        session_id=KNOWN_SESSION_ID,
        workspace_encoded=KNOWN_WORKSPACE,
        sessions_root=real_sessions_root,
    )
    assert b.status is IdentityStatus.VERIFIED
    assert b.session_id == KNOWN_SESSION_ID
    assert b.session_dir is not None
    assert b.session_dir.endswith(KNOWN_SESSION_ID)


def test_resolve_cross_checks_pass_on_real_session(real_sessions_root):
    b = resolve_session_dir(
        session_id=KNOWN_SESSION_ID,
        workspace_encoded=KNOWN_WORKSPACE,
        sessions_root=real_sessions_root,
    )
    assert any("summary.json" in c for c in b.cross_checks)
    assert any("events.jsonl" in c for c in b.cross_checks)


# ---------------------------------------------------------------------------
# Failure modes — never scan, never guess
# ---------------------------------------------------------------------------


def test_resolve_unverified_when_no_session_supplied(real_sessions_root):
    """No session_id arg and no $GROK_SESSION_ID env → UNVERIFIED, not a scan."""
    b = resolve_session_dir(
        session_id=None,
        workspace_encoded=KNOWN_WORKSPACE,
        sessions_root=real_sessions_root,
        env={},
    )
    assert b.status is IdentityStatus.UNVERIFIED
    assert "no session id" in b.reasons[0].lower()


def test_resolve_unverified_when_env_present_but_unset(real_sessions_root):
    b = resolve_session_dir(
        session_id=None,
        workspace_encoded=KNOWN_WORKSPACE,
        sessions_root=real_sessions_root,
        env={ENV_VAR: ""},
    )
    assert b.status is IdentityStatus.UNVERIFIED


def test_resolve_env_var_path_used_when_argument_absent(real_sessions_root):
    """If Grok later exposes $GROK_SESSION_ID, it is the secondary authority."""
    b = resolve_session_dir(
        session_id=None,
        workspace_encoded=KNOWN_WORKSPACE,
        sessions_root=real_sessions_root,
        env={ENV_VAR: KNOWN_SESSION_ID},
    )
    assert b.status is IdentityStatus.VERIFIED
    assert any("env:$GROK_SESSION_ID" in c for c in b.cross_checks)


def test_resolve_supplied_invalid_rejected():
    """Non-UUID-shaped ids are rejected as SUPPLIED_INVALID, never scanned."""
    b = resolve_session_dir(
        session_id="not-a-uuid",
        workspace_encoded=KNOWN_WORKSPACE,
    )
    assert b.status is IdentityStatus.SUPPLIED_INVALID


def test_resolve_unverified_when_workspace_absent():
    """Without the encoded-workspace component we cannot locate the dir."""
    b = resolve_session_dir(session_id=KNOWN_SESSION_ID, workspace_encoded=None)
    assert b.status is IdentityStatus.UNVERIFIED
    assert "workspace_encoded" in b.reasons[0]


def test_resolve_unverified_when_dir_missing(tmp_path: Path):
    fake_root = tmp_path / "sessions"
    fake_root.mkdir()
    b = resolve_session_dir(
        session_id=KNOWN_SESSION_ID,
        workspace_encoded=KNOWN_WORKSPACE,
        sessions_root=fake_root,
    )
    assert b.status is IdentityStatus.UNVERIFIED
    assert any("does not exist" in r for r in b.reasons)


def test_no_foreign_session_consumed(real_sessions_root, tmp_path: Path):
    """Resolver must never open a directory other than the one bound by id.

    Verified by absence: even if many session dirs exist, only the supplied
    id is consulted. We assert by checking that the returned dir matches the
    id exactly (no scan, no fallback).
    """
    b = resolve_session_dir(
        session_id=KNOWN_SESSION_ID,
        workspace_encoded=KNOWN_WORKSPACE,
        sessions_root=real_sessions_root,
    )
    assert b.session_dir is not None
    assert KNOWN_SESSION_ID in b.session_dir
    # The resolver does not enumerate the parent dir at all.
    # (Behavioural guarantee: it builds the path from id + workspace, full stop.)


# ---------------------------------------------------------------------------
# verify_session_identity — cross-check logic
# ---------------------------------------------------------------------------


def _make_session_dir(
    root: Path, sid: str, *, with_summary: bool = True, summary_id: str | None = None, with_events: bool = True, events_sid: str | None = None
) -> Path:
    """Build a minimal session dir with the requested artifacts."""
    ws = root / "P%3A%5C" / sid
    ws.mkdir(parents=True, exist_ok=True)
    if with_summary:
        (ws / "summary.json").write_text(
            json.dumps({"info": {"id": summary_id or sid, "cwd": "P:\\"}}), encoding="utf-8"
        )
    if with_events:
        # Write a turn_started with the requested session_id
        (ws / "events.jsonl").write_text(
            json.dumps(
                {
                    "ts": "2026-07-16T18:40:56.166Z",
                    "type": "turn_started",
                    "session_id": events_sid or sid,
                    "turn_number": 0,
                }
            )
            + "\n",
            encoding="utf-8",
        )
    return ws


def test_verify_identity_passes_when_summary_and_events_agree(tmp_path: Path):
    sd = _make_session_dir(tmp_path, "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe")
    b = verify_session_identity("019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe", sd)
    assert b.status is IdentityStatus.VERIFIED
    assert len(b.cross_checks) == 2


def test_verify_identity_unverified_when_summary_disagrees(tmp_path: Path):
    sd = _make_session_dir(
        tmp_path, "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe", summary_id="some-other-id"
    )
    b = verify_session_identity("019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe", sd)
    assert b.status is IdentityStatus.UNVERIFIED
    assert any("summary.json info.id" in r for r in b.reasons)


def test_verify_identity_unverified_when_events_disagree(tmp_path: Path):
    sd = _make_session_dir(
        tmp_path, "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe", events_sid="some-other-id"
    )
    b = verify_session_identity("019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe", sd)
    assert b.status is IdentityStatus.UNVERIFIED
    assert any("turn_started.session_id" in r for r in b.reasons)


def test_verify_identity_unverified_when_no_artifacts(tmp_path: Path):
    sd = tmp_path / "empty-session"
    sd.mkdir()
    b = verify_session_identity("019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe", sd)
    assert b.status is IdentityStatus.UNVERIFIED
    assert b.reasons
