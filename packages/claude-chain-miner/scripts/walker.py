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


def _project_handoff_dir() -> Path:
    """Project-scoped handoff directory (where PreCompact writes on P: drive)."""
    p_drive = Path("P:/")
    if p_drive.exists():
        project_path = p_drive / ".claude" / "state" / "handoff"
        if project_path.exists():
            return project_path
    return _HANDOFF_DIR


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
# Session ID extraction
# ---------------------------------------------------------------------------

def _session_id_from_path(path: Path | str) -> str | None:
    """Extract UUID session ID from a path like .../59ba4da6-8417-4c06-9dc8-f5647591ad3e.jsonl."""
    stem = Path(path).stem
    if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", stem, re.I):
        return stem
    return None


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
    """Find the most recent .jsonl transcript in the projects dir."""
    all_jsonls: list[tuple[Path, float]] = []
    for proj_path in _PROJECTS_DIR.rglob("*.jsonl"):
        try:
            all_jsonls.append((proj_path, proj_path.stat().st_mtime))
        except OSError:
            continue

    if not all_jsonls:
        return None
    all_jsonls.sort(key=lambda x: x[1], reverse=True)
    return all_jsonls[0][0]


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
) -> tuple[list[ChainEntry], str | None]:
    """Walk the handoff chain.

    Args:
        slug: Unused — kept for API compatibility. Slug-based lookup is broken;
              the correct approach is reverse lookup via transcript path.
        start_session_id: Session ID to start from (default: newest .jsonl)
        max_depth: Maximum chain depth

    Returns:
        (entries, origin_session_id) — entries oldest→newest
    """
    # Resolve starting transcript
    current_transcript = _resolve_current_transcript()
    if current_transcript is None:
        logger.warning("No transcript .jsonl found in projects directory")
        return [], None

    current_session_id = _session_id_from_path(current_transcript)
    if start_session_id is None:
        start_session_id = current_session_id

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

        session_id = _session_id_from_path(current_transcript) or start_session_id

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

def get_chain_for_slug(slug: str, max_depth: int = 20) -> tuple[list[ChainEntry], str | None]:
    """Walk handoff chain. slug param is accepted but unused (kept for compatibility)."""
    return walk_handoff_chain(slug=slug, start_session_id=None, max_depth=max_depth)


def get_current_slug() -> str:
    """Return the terminal slug for the current working directory."""
    return _slug_from_cwd()
