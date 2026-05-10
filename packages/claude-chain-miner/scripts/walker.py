"""Handoff-chain walker for ClaudeChainMiner.

Traverses session chains via handoff files written by PreCompact hook.
Handles the prior_transcript_path=N/A self-match bug via visited-set loop breaking.

Key insight: handoff files are named console_{session_id}_handoff.json, NOT
{slug}_{session_id}_handoff.json. We find them by:
  1. Resolving the current session's .jsonl path from the projects dir
  2. Finding the handoff that references that transcript (reverse lookup)
  3. Following prior_transcript_path links through successive handoffs
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_CLAUDE_BASE = Path.home() / ".claude"
_HANDOFF_DIR = _CLAUDE_BASE / "state" / "handoff"
_PROJECTS_DIR = _CLAUDE_BASE / "projects"
_SESSION_INDEX_CANDIDATES = (
    Path("P:\\\\\\.claude/sessions.json"),
    _CLAUDE_BASE / "sessions.json",
)


def _project_handoff_dir() -> Path:
    """Project-scoped handoff directory (where PreCompact writes on P: drive)."""
    p_drive = Path("P:\\\\\\")
    if p_drive.exists():
        project_path = p_drive / ".claude" / "state" / "handoff"
        if project_path.exists():
            return project_path
    return _HANDOFF_DIR


def _candidate_projects_dirs() -> list[Path]:
    """Return project transcript directories to search, in priority order."""
    dirs: list[Path] = []
    for candidate in (Path("P:\\\\\\.claude/projects"), _PROJECTS_DIR):
        try:
            if candidate.exists() and candidate not in dirs:
                dirs.append(candidate)
        except OSError:
            continue
    if not dirs:
        dirs.append(_PROJECTS_DIR)
    return dirs


def _candidate_session_index_paths() -> list[Path]:
    """Return session index files to consult when explicit anchors are absent."""
    paths: list[Path] = []
    for candidate in _SESSION_INDEX_CANDIDATES:
        try:
            if candidate.exists() and candidate not in paths:
                paths.append(candidate)
        except OSError:
            continue
    return paths


# ---------------------------------------------------------------------------
# Slug resolution
# ---------------------------------------------------------------------------

def _slug_from_cwd() -> str:
    """Derive terminal slug from current working directory."""
    cwd = Path.cwd().resolve()
    slug = str(cwd).replace(":\\", "--").replace("\\", "--").replace(":", "--")
    slug = re.sub(r"[^a-zA-Z0-9_\-.]", "-", slug)
    return slug


# ---------------------------------------------------------------------------
# Session / transcript resolution
# ---------------------------------------------------------------------------

def _session_id_from_path(path: Path | str) -> str | None:
    """Extract UUID session ID from a path like .../59ba4da6-8417-4c06-9dc8-f5647591ad3e.jsonl."""
    stem = Path(path).stem
    if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", stem, re.I):
        return stem
    return None


def _coerce_transcript_path(value: Path | str | None) -> Path | None:
    """Resolve a transcript path from a path-like value or session-id-like stem."""
    if value is None:
        return None

    candidate = Path(value)
    if candidate.exists():
        return candidate.resolve()

    session_id = _session_id_from_path(candidate)
    if session_id is None and re.match(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        str(value).strip(),
        re.I,
    ):
        session_id = str(value).strip()

    if session_id:
        return _resolve_transcript_from_session_id(session_id)

    return None


def _resolve_transcript_from_session_id(session_id: str | None) -> Path | None:
    """Resolve a transcript path from a deterministic Claude session id.

    Claude Code transcripts are stored as ``<session_id>.jsonl`` under the
    per-project directory in ``~/.claude/projects``. When a caller already knows
    the exact session id, that is a stronger source of truth than scanning by
    modification time.
    """
    if not session_id:
        return None

    session_stem = Path(session_id).stem
    candidates: list[Path] = []
    for projects_dir in _candidate_projects_dirs():
        for proj_path in projects_dir.rglob(f"{session_stem}.jsonl"):
            try:
                if proj_path.is_file():
                    candidates.append(proj_path)
            except OSError:
                continue

    if not candidates:
        return None

    # Prefer the newest matching transcript if multiple copies exist.
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


# ---------------------------------------------------------------------------
# Handoff discovery
# ---------------------------------------------------------------------------

def _glob_all_handoffs() -> list[Path]:
    """Return all handoff files from both project and home handoff dirs."""
    results: list[Path] = []
    for hdir in [_project_handoff_dir(), _HANDOFF_DIR]:
        if hdir.exists():
            for p in hdir.glob("*.json"):
                if "handoff" in p.name and p not in results:
                    results.append(p)
    results.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return results


def _find_handoff_referencing(transcript_path: Path | str) -> Path | None:
    """Find the handoff file whose transcript_path field points to the given transcript.

    This is the correct reverse-lookup: handoff files don't contain their own
    session ID in the name — they contain the NEXT session's transcript path.
    We find the prior handoff by matching the transcript it references.
    """
    target = str(Path(transcript_path))
    for hdir in [_project_handoff_dir(), _HANDOFF_DIR]:
        if not hdir.exists():
            continue
        for hf in hdir.glob("console_*_handoff.json"):
            try:
                with open(hf, encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("resume_snapshot", {}).get("transcript_path") == target:
                    return hf
            except (OSError, json.JSONDecodeError):
                continue
    return None


def _get_prior_transcript_path(handoff_path: Path) -> Path | None:
    """Extract prior_transcript_path from a handoff file."""
    try:
        with open(handoff_path, encoding="utf-8") as f:
            data = json.load(f)
        path_str = data.get("resume_snapshot", {}).get("prior_transcript_path")
        if path_str and path_str != "N/A":
            p = Path(path_str)
            if p.exists():
                return p
    except (OSError, json.JSONDecodeError):
        pass
    return None


def _resolve_current_transcript() -> Path | None:
    """Find the most recent .jsonl transcript in any known projects dir."""
    all_jsonls: list[tuple[Path, float]] = []
    for projects_dir in _candidate_projects_dirs():
        for proj_path in projects_dir.rglob("*.jsonl"):
            try:
                all_jsonls.append((proj_path, proj_path.stat().st_mtime))
            except OSError:
                continue

    if not all_jsonls:
        return None
    all_jsonls.sort(key=lambda x: x[1], reverse=True)
    return all_jsonls[0][0]


def _read_session_index_records() -> list[dict]:
    """Read active session records from known session index files."""
    records: list[dict] = []
    for index_path in _candidate_session_index_paths():
        try:
            raw = json.loads(index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, dict):
                    records.append(item)
    return records


def _working_directory_matches(record: dict, cwd: Path) -> bool:
    """Return True if a session record is plausibly associated with cwd."""
    cwd_resolved = cwd.resolve()
    for key in ("working_directory", "claude_project_dir"):
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            continue
        try:
            candidate = Path(value).resolve()
        except OSError:
            continue

        if candidate == cwd_resolved:
            return True

        try:
            if candidate in cwd_resolved.parents or cwd_resolved in candidate.parents:
                return True
        except Exception:
            continue
    return False


def _select_session_record(records: list[dict], cwd: Path | None = None) -> dict | None:
    """Select the most plausible active session record from sessions.json."""
    active_records = [
        record
        for record in records
        if record.get("status") == "active" and isinstance(record.get("session_id"), str)
    ]
    if not active_records:
        return None

    if cwd is not None:
        for record in reversed(active_records):
            if _working_directory_matches(record, cwd):
                return record

    return active_records[-1]


def resolve_start_anchor(
    start_session_id: str | None = None,
    start_transcript_path: Path | str | None = None,
    cwd: Path | None = None,
) -> tuple[str | None, Path | None, str]:
    """Resolve the best available session/transcript anchor.

    Resolution priority:
    1. Explicit transcript path
    2. Explicit session id
    3. Transcript-path env vars
    4. Explicit session-id env vars
    5. Active session record from sessions.json
    6. Most recent transcript file as a fallback
    """
    source = "fallback"
    session_id = start_session_id.strip() if isinstance(start_session_id, str) else None

    transcript_path = _coerce_transcript_path(start_transcript_path)
    if transcript_path is not None:
        source = "explicit_transcript_path"
        if session_id is None:
            session_id = _session_id_from_path(transcript_path)
        return session_id, transcript_path, source

    if session_id is not None:
        transcript_path = _resolve_transcript_from_session_id(session_id)
        if transcript_path is not None:
            return _session_id_from_path(transcript_path) or session_id, transcript_path, "explicit_session_id"

    env_transcript_path = (
        os.environ.get("CLAUDE_TRANSCRIPT_PATH", "").strip()
        or os.environ.get("CLAUDE_CODE_TRANSCRIPT_PATH", "").strip()
    )
    if env_transcript_path:
        transcript_path = _coerce_transcript_path(env_transcript_path)
        if transcript_path is not None:
            if session_id is None:
                session_id = _session_id_from_path(transcript_path)
            return session_id, transcript_path, "env_transcript_path"

    if session_id is None:
        env_session_id = (
            os.environ.get("CLAUDE_SESSION_ID", "").strip()
            or os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
            or os.environ.get("conversation_id", "").strip()
        )
        if env_session_id:
            session_id = env_session_id
            transcript_path = _resolve_transcript_from_session_id(session_id)
            if transcript_path is not None:
                return _session_id_from_path(transcript_path) or session_id, transcript_path, "env_session_id"

    session_record = _select_session_record(_read_session_index_records(), cwd or Path.cwd())
    if session_record is not None:
        record_session_id = str(session_record.get("session_id", "")).strip()
        if record_session_id:
            transcript_path = _resolve_transcript_from_session_id(record_session_id)
            if transcript_path is not None:
                return (
                    _session_id_from_path(transcript_path) or record_session_id,
                    transcript_path,
                    "session_index",
                )
            return record_session_id, None, "session_index"

    transcript_path = _resolve_current_transcript()
    if transcript_path is not None:
        return _session_id_from_path(transcript_path), transcript_path, "mtime_fallback"

    return session_id, None, source


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class ChainEntry:
    session_id: str
    transcript_path: Path
    parent_transcript_path: Path | None = None
    created: str | None = None


# ---------------------------------------------------------------------------
# Core walker
# ---------------------------------------------------------------------------

def walk_handoff_chain(
    slug: str | None = None,
    start_session_id: str | None = None,
    max_depth: int = 20,
    start_transcript_path: Path | str | None = None,
) -> tuple[list[ChainEntry], str | None]:
    """Walk the handoff chain.

    Args:
        slug: Unused — kept for API compatibility. Slug-based lookup is broken;
              the correct approach is reverse lookup via transcript path.
        start_session_id: Deterministic session UUID to start from.
        start_transcript_path: Deterministic transcript path to start from.
        max_depth: Maximum chain depth.

    Resolution order:
        1. start_transcript_path if provided
        2. start_session_id resolved to ``<session_id>.jsonl``
        3. newest ``.jsonl`` in the projects directory

    Returns:
        (entries, origin_session_id) — entries oldest→newest
    """
    # Resolve starting transcript from the strongest available anchor first.
    resolved_session_id, current_transcript, anchor_source = resolve_start_anchor(
        start_session_id=start_session_id,
        start_transcript_path=start_transcript_path,
        cwd=Path.cwd(),
    )

    if current_transcript is None:
        if resolved_session_id:
            logger.warning(
                "No transcript .jsonl found for session %s (anchor source: %s)",
                resolved_session_id,
                anchor_source,
            )
        else:
            logger.warning("No transcript .jsonl found in projects directory")
        return [], None

    # Find the handoff that references this current transcript
    current_handoff = _find_handoff_referencing(current_transcript)

    entries: list[ChainEntry] = []
    visited: set[str] = set()
    origin_session_id: str | None = None
    chain_depth = 0

    while current_handoff and chain_depth < max_depth:
        hf_str = str(current_handoff)
        if hf_str in visited:
            logger.warning("Self-match loop detected at %s, breaking", hf_str)
            break
        visited.add(hf_str)

        try:
            with open(current_handoff, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to read %s: %s", current_handoff, exc)
            break

        resume = data.get("resume_snapshot", {})
        prior_transcript_path_str = resume.get("prior_transcript_path")

        session_id = _session_id_from_path(current_transcript) or resolved_session_id or start_session_id

        # Check if this handoff has a prior — if not, it's the origin
        prior_transcript: Path | None = None
        if prior_transcript_path_str and prior_transcript_path_str != "N/A":
            prior_transcript = Path(prior_transcript_path_str)

        # Mark origin when there are no more priors
        if prior_transcript is None or not prior_transcript.exists():
            origin_session_id = session_id

        entries.append(ChainEntry(
            session_id=session_id,
            transcript_path=Path(current_transcript),
            parent_transcript_path=None,
            created=resume.get("created_at"),
        ))

        if prior_transcript is None or not prior_transcript.exists():
            break

        # Move to prior session
        current_transcript = prior_transcript
        current_handoff = _find_handoff_referencing(prior_transcript)
        chain_depth += 1

    # Fill parent links (reverse: newest→older → older→newest)
    entries.reverse()
    for i, entry in enumerate(entries):
        if i < len(entries) - 1:
            entry.parent_transcript_path = entries[i + 1].transcript_path

    return entries, origin_session_id or (entries[0].session_id if entries else None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_chain_for_slug(
    slug: str,
    max_depth: int = 20,
    *,
    start_session_id: str | None = None,
    start_transcript_path: Path | str | None = None,
) -> tuple[list[ChainEntry], str | None]:
    """Walk handoff chain.

    Args:
        slug: Accepted for compatibility with older callers.
        max_depth: Maximum chain depth.
        start_session_id: Deterministic Claude session UUID anchor.
        start_transcript_path: Deterministic transcript path anchor.
    """
    return walk_handoff_chain(
        slug=slug,
        start_session_id=start_session_id,
        max_depth=max_depth,
        start_transcript_path=start_transcript_path,
    )


def get_current_slug() -> str:
    """Return the terminal slug for the current working directory."""
    return _slug_from_cwd()
