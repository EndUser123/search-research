"""Immutable source snapshot for AAR preprocessing.

Per spec Section 3: "The session files may still be changing while /aar runs.
Before parsing: record source file size, modification time, and hash where
practical; copy the exact required source files into the current AAR run
directory; record a snapshot cutoff timestamp; hash the immutable copies;
parse the copies, not the live files; report whether source files changed
during snapshot."

Design contract
---------------
* **Atomic copy.** Each source file is copied via a ``.tmp`` + ``os.replace``
  so partial copies never appear as valid snapshots.
* **Mid-snapshot drift detection.** After every file is copied, we re-hash
  the live original. A changed hash sets ``changed_during_snapshot=True``
  and emits a warning, but we still proceed using the captured copy. The
  packet is honest: it says "snapshot as of cutoff T, with drift detected".
* **No originals modified.** Only read+copy. No writes to the session dir.
* **Forward-slash paths.** Snapshot root is stored with ``/`` separators.

Output structure
----------------
``<snapshot_root>/``
    ``chat_history.jsonl``      (copy)
    ``summary.json``             (copy)
    ``events.jsonl``             (copy, may be filtered to useful types in
                                  a downstream step — the snapshot itself is
                                  a faithful copy)
    ``rewind_points.jsonl``      (copy)
    ``compaction_checkpoints/``  (deep copy of directory)
    ``compaction/``              (deep copy of directory)
    ``snapshot-manifest.json``   (per-file hashes, sizes, mtimes, drift flag)

The manifest is the single source of truth for "what was snapshotted and
when". Downstream reconciliation reads the manifest, not the live files.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

__all__ = [
    "SourceFile",
    "SnapshotResult",
    "REQUIRED_SOURCES",
    "OPTIONAL_SOURCES",
    "snapshot_session_sources",
    "load_snapshot_manifest",
    "sha256_file",
]

#: Sources we always try to snapshot. Missing required sources downgrade
#: completeness (see completeness.py).
REQUIRED_SOURCES: tuple[str, ...] = (
    "chat_history.jsonl",
    "summary.json",
)

#: Sources that are valuable when present but not required for a minimal AAR.
#: Each is snapshotted iff it exists in the session dir.
OPTIONAL_SOURCES: tuple[str, ...] = (
    "events.jsonl",
    "rewind_points.jsonl",
)

#: Directories under the session dir to deep-copy when present. These hold
#: many files (compaction segments, checkpoints) so we copy the whole subdir.
SOURCE_DIRS: tuple[str, ...] = (
    "compaction",
    "compaction_checkpoints",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(frozen=True)
class SourceFile:
    """One snapshotted source: live stats + copied-file hash + drift flag."""

    name: str
    source_role: str  #: 'primary' | 'metadata' | 'operational' | 'branch' | 'recovery' | 'navigation'
    live_path: str
    snapshot_path: str
    present: bool
    size_bytes: int
    sha256_live_before: str | None
    sha256_snapshot: str | None
    mtime_live_before: str | None
    changed_during_snapshot: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_role": self.source_role,
            "live_path": self.live_path,
            "snapshot_path": self.snapshot_path,
            "present": self.present,
            "size_bytes": self.size_bytes,
            "sha256_live_before": self.sha256_live_before,
            "sha256_snapshot": self.sha256_snapshot,
            "mtime_live_before": self.mtime_live_before,
            "changed_during_snapshot": self.changed_during_snapshot,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class SnapshotResult:
    """Aggregate snapshot outcome."""

    snapshot_root: str
    snapshot_cutoff: str  #: ISO-8601 UTC; the instant snapshotting began
    completed_at: str
    session_id: str
    session_dir: str
    files: tuple[SourceFile, ...]
    directories: tuple[dict[str, Any], ...]
    drift_detected: bool
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_root": self.snapshot_root,
            "snapshot_cutoff": self.snapshot_cutoff,
            "completed_at": self.completed_at,
            "session_id": self.session_id,
            "session_dir": self.session_dir,
            "files": [f.to_dict() for f in self.files],
            "directories": [dict(d) for d in self.directories],
            "drift_detected": self.drift_detected,
            "warnings": list(self.warnings),
        }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def snapshot_session_sources(
    session_dir: str | Path,
    snapshot_root: str | Path,
    *,
    session_id: str,
    cutoff: str | None = None,
) -> SnapshotResult:
    """Snapshot all session sources atomically into ``snapshot_root``.

    ``session_dir`` is the verified live session directory (see
    ``session_resolver``). ``snapshot_root`` is created if missing; should
    live under ``P:/.artifacts/<terminal>/grok-aar/<run>/preprocess/source-snapshot/``.

    ``cutoff`` is normally injected by the orchestrator for deterministic
    tests. In production, the cutoff is captured *before* the first file is
    touched and represents the instant the snapshot began.
    """
    sd = Path(session_dir)
    sr = Path(snapshot_root)
    sr.mkdir(parents=True, exist_ok=True)

    cutoff_ts = cutoff or _utc_now_iso()
    files: list[SourceFile] = []
    dir_copies: list[dict[str, Any]] = []
    warnings: list[str] = []
    drift = False

    role_map = {
        "chat_history.jsonl": "primary",
        "summary.json": "metadata",
        "events.jsonl": "operational",
        "rewind_points.jsonl": "branch",
    }

    for name in REQUIRED_SOURCES + OPTIONAL_SOURCES:
        live = sd / name
        snap = sr / name
        role = role_map.get(name, "unknown")
        if not live.is_file():
            sf = SourceFile(
                name=name,
                source_role=role,
                live_path=str(live).replace("\\", "/"),
                snapshot_path=str(snap).replace("\\", "/"),
                present=False,
                size_bytes=0,
                sha256_live_before=None,
                sha256_snapshot=None,
                mtime_live_before=None,
                changed_during_snapshot=False,
            )
            files.append(sf)
            if name in REQUIRED_SOURCES:
                warnings.append(f"required source missing: {name}")
            continue

        # Capture pre-copy state.
        size_before = live.stat().st_size
        mtime_before = datetime.fromtimestamp(
            live.stat().st_mtime, tz=timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        sha_before = sha256_file(live)

        # Atomic copy: tmp + os.replace.
        tmp = snap.with_suffix(snap.suffix + ".tmp")
        try:
            shutil.copy2(live, tmp)
            os.replace(tmp, snap)
        except OSError as exc:
            warnings.append(f"copy failed for {name}: {exc}")
            files.append(
                SourceFile(
                    name=name,
                    source_role=role,
                    live_path=str(live).replace("\\", "/"),
                    snapshot_path=str(snap).replace("\\", "/"),
                    present=True,
                    size_bytes=size_before,
                    sha256_live_before=sha_before,
                    sha256_snapshot=None,
                    mtime_live_before=mtime_before,
                    changed_during_snapshot=False,
                    warnings=(f"copy failed: {exc}",),
                )
            )
            continue

        sha_snapshot = sha256_file(snap)
        # Re-hash the live original to detect drift during copy.
        try:
            sha_after = sha256_file(live)
        except OSError as exc:
            sha_after = sha_before
            warnings.append(f"post-copy hash failed for {name}: {exc}")
        changed = sha_after != sha_before
        if changed:
            drift = True
            warnings.append(
                f"{name} changed during snapshot (live hash differs pre/post)"
            )

        files.append(
            SourceFile(
                name=name,
                source_role=role,
                live_path=str(live).replace("\\", "/"),
                snapshot_path=str(snap).replace("\\", "/"),
                present=True,
                size_bytes=size_before,
                sha256_live_before=sha_before,
                sha256_snapshot=sha_snapshot,
                mtime_live_before=mtime_before,
                changed_during_snapshot=changed,
            )
        )

    # Deep-copy optional directories (compaction, checkpoints) when present.
    for dname in SOURCE_DIRS:
        live_dir = sd / dname
        snap_dir = sr / dname
        if not live_dir.is_dir():
            continue
        try:
            if snap_dir.exists():
                shutil.rmtree(snap_dir)
            shutil.copytree(live_dir, snap_dir)
            file_count = sum(1 for _ in snap_dir.rglob("*") if _.is_file())
            dir_copies.append(
                {
                    "name": dname,
                    "source_role": "navigation" if dname == "compaction" else "recovery",
                    "live_path": str(live_dir).replace("\\", "/"),
                    "snapshot_path": str(snap_dir).replace("\\", "/"),
                    "file_count": file_count,
                }
            )
        except OSError as exc:
            warnings.append(f"directory copy failed for {dname}: {exc}")

    completed = _utc_now_iso()
    result = SnapshotResult(
        snapshot_root=str(sr).replace("\\", "/"),
        snapshot_cutoff=cutoff_ts,
        completed_at=completed,
        session_id=session_id,
        session_dir=str(sd).replace("\\", "/"),
        files=tuple(files),
        directories=tuple(dir_copies),
        drift_detected=drift,
        warnings=tuple(warnings),
    )

    # Write the manifest next to the snapshot copies. Atomic.
    _write_atomic_json(sr / "snapshot-manifest.json", result.to_dict())
    return result


def load_snapshot_manifest(snapshot_root: str | Path) -> dict[str, Any]:
    """Load the snapshot manifest written by :func:`snapshot_session_sources`.

    Raises ``FileNotFoundError`` if the manifest is missing.
    """
    p = Path(snapshot_root) / "snapshot-manifest.json"
    if not p.is_file():
        raise FileNotFoundError(f"snapshot manifest not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def sha256_file(path: str | Path, *, chunk: int = 65536) -> str:
    """Stream-hash a file. Returns hex digest."""
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------


def _write_atomic_json(path: str | Path, payload: Any) -> None:
    """Write ``payload`` as JSON via ``.tmp`` + ``os.replace``."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
        encoding="utf-8",
    )
    os.replace(tmp, p)
