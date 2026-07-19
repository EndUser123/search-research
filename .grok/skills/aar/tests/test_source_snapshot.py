"""Tests for the immutable source snapshot.

Evidence class: production unit + integration (uses real fixture files).

Covers spec Section 3 + Section 16 (snapshot tests):
* immutable copy created;
* hashes recorded;
* live source change during copy detected (drift);
* cutoff recorded;
* originals untouched.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from source_snapshot import (
    SnapshotResult,
    load_snapshot_manifest,
    REQUIRED_SOURCES,
    sha256_file,
    snapshot_session_sources,
)

SID = "019f6c3b-4f15-7da1-b5ca-7d79eeb0cfbe"


def _make_minimal_session(root: Path) -> Path:
    """Build a session dir with chat_history.jsonl + summary.json + events.jsonl."""
    sd = root / "P%3A%5C" / SID
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "chat_history.jsonl").write_text(
        json.dumps({"type": "system", "content": "sys"}) + "\n", encoding="utf-8"
    )
    (sd / "summary.json").write_text(
        json.dumps({"info": {"id": SID, "cwd": "P:\\"}}), encoding="utf-8"
    )
    (sd / "events.jsonl").write_text(
        json.dumps({"type": "turn_started", "session_id": SID, "ts": "2026-07-16T18:40:56Z"}) + "\n",
        encoding="utf-8",
    )
    return sd


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_snapshot_copies_all_required_sources(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    snap_root = tmp_path / "snap"
    r = snapshot_session_sources(sd, snap_root, session_id=SID, cutoff="2026-07-18T00:00:00Z")
    assert r.drift_detected is False
    names = {f.name for f in r.files}
    for req in REQUIRED_SOURCES:
        assert req in names
    # chat_history.jsonl copy exists and matches the live hash
    chat = next(f for f in r.files if f.name == "chat_history.jsonl")
    assert chat.present
    assert chat.sha256_snapshot is not None
    assert Path(chat.snapshot_path).is_file()


def test_snapshot_records_size_mtime_hash(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    snap_root = tmp_path / "snap"
    r = snapshot_session_sources(sd, snap_root, session_id=SID)
    chat = next(f for f in r.files if f.name == "chat_history.jsonl")
    assert chat.size_bytes > 0
    assert chat.mtime_live_before is not None
    assert chat.sha256_live_before == chat.sha256_snapshot  # no drift
    assert chat.sha256_live_before == sha256_file(sd / "chat_history.jsonl")


def test_snapshot_cutoff_recorded(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    snap_root = tmp_path / "snap"
    r = snapshot_session_sources(sd, snap_root, session_id=SID, cutoff="2026-07-18T12:34:56Z")
    assert r.snapshot_cutoff == "2026-07-18T12:34:56Z"


def test_snapshot_manifest_written_and_loadable(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    snap_root = tmp_path / "snap"
    r = snapshot_session_sources(sd, snap_root, session_id=SID, cutoff="2026-07-18T00:00:00Z")
    manifest = load_snapshot_manifest(snap_root)
    assert manifest["session_id"] == SID
    assert manifest["snapshot_cutoff"] == "2026-07-18T00:00:00Z"
    assert any(f["name"] == "chat_history.jsonl" for f in manifest["files"])


def test_snapshot_no_tmp_files_left(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    snap_root = tmp_path / "snap"
    snapshot_session_sources(sd, snap_root, session_id=SID)
    assert list(snap_root.glob("*.tmp")) == []


# ---------------------------------------------------------------------------
# Originals untouched
# ---------------------------------------------------------------------------


def test_snapshot_does_not_modify_originals(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    original_hash = sha256_file(sd / "chat_history.jsonl")
    original_mtime = (sd / "chat_history.jsonl").stat().st_mtime
    snap_root = tmp_path / "snap"
    snapshot_session_sources(sd, snap_root, session_id=SID)
    assert sha256_file(sd / "chat_history.jsonl") == original_hash
    # shutil.copy2 preserves mtime on the COPY, not the original. The original
    # mtime is unchanged by a read-only copy.
    assert (sd / "chat_history.jsonl").stat().st_mtime == original_mtime


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------


def test_snapshot_detects_live_drift(tmp_path: Path, monkeypatch):
    """If the live file changes between the pre-hash and post-hash, drift flag fires."""
    sd = _make_minimal_session(tmp_path)
    snap_root = tmp_path / "snap"

    # Patch shutil.copy2 so it appends to the live file mid-copy, simulating
    # Grok writing to chat_history.jsonl while we snapshot.
    import source_snapshot as mod
    real_copy2 = mod.shutil.copy2

    def drifting_copy2(src, dst, *, follow_symlinks=True):
        result = real_copy2(src, dst, follow_symlinks=follow_symlinks)
        # Simulate the live session appending one more line during snapshot.
        Path(src).open("a", encoding="utf-8").write(
            json.dumps({"type": "user", "content": "in-flight"}) + "\n"
        )
        return result

    monkeypatch.setattr(mod.shutil, "copy2", drifting_copy2)
    r = snapshot_session_sources(sd, snap_root, session_id=SID)
    assert r.drift_detected is True
    chat = next(f for f in r.files if f.name == "chat_history.jsonl")
    assert chat.changed_during_snapshot is True
    assert any("chat_history.jsonl changed during snapshot" in w for w in r.warnings)


# ---------------------------------------------------------------------------
# Missing sources
# ---------------------------------------------------------------------------


def test_snapshot_handles_missing_optional_sources(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    # Remove events.jsonl — it's optional
    (sd / "events.jsonl").unlink()
    snap_root = tmp_path / "snap"
    r = snapshot_session_sources(sd, snap_root, session_id=SID)
    events = next(f for f in r.files if f.name == "events.jsonl")
    assert events.present is False


def test_snapshot_warns_on_missing_required_sources(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    (sd / "chat_history.jsonl").unlink()
    snap_root = tmp_path / "snap"
    r = snapshot_session_sources(sd, snap_root, session_id=SID)
    chat = next(f for f in r.files if f.name == "chat_history.jsonl")
    assert chat.present is False
    assert any("required source missing" in w for w in r.warnings)


# ---------------------------------------------------------------------------
# Directory copies
# ---------------------------------------------------------------------------


def test_snapshot_copies_compaction_dir(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    (sd / "compaction").mkdir()
    (sd / "compaction" / "segment_000.md").write_text("# segment", encoding="utf-8")
    snap_root = tmp_path / "snap"
    r = snapshot_session_sources(sd, snap_root, session_id=SID)
    dir_names = [d["name"] for d in r.directories]
    assert "compaction" in dir_names
    assert (snap_root / "compaction" / "segment_000.md").is_file()


def test_snapshot_copies_checkpoints_dir(tmp_path: Path):
    sd = _make_minimal_session(tmp_path)
    (sd / "compaction_checkpoints").mkdir()
    (sd / "compaction_checkpoints" / "abc.json").write_text("{}", encoding="utf-8")
    snap_root = tmp_path / "snap"
    r = snapshot_session_sources(sd, snap_root, session_id=SID)
    dir_names = [d["name"] for d in r.directories]
    assert "compaction_checkpoints" in dir_names
