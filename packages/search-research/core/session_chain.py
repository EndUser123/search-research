"""Session chain traversal for Claude Code.

Provides a unified interface for finding all session transcript files in a
session chain, given any session ID.

Three strategies, tried in order:
  1. Handoff-file chain   — reliable when handoff files exist
  2. sessions-index scan  — fallback using mtime gap heuristic + semantic verification
  3. Semantic similarity  — fallback using embedding similarity

Algorithm (Strategy 2):
  For each session, compute mtime gap to nearest prior session.
  Smallest gap < MAX_MTIME_GAP_SECS → candidate chain link.
  Semantic verify: prior session's ending goals vs successor's first user message.
  If similarity >= threshold → chain link confirmed.
  Otherwise → fall through to semantic strategy.

This captures ALL sessions, not just /compact continuations.
Multi-terminal interleaving is handled by semantic verification step.
"""

from __future__ import annotations

import json
import logging

import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Module-level cache for direct SentenceTransformer fallback (daemon unavailable)
_st_model: Any = None
_st_model_last_used: float = 0.0
_ST_MODEL_TTL_SECONDS: float = 300.0  # 5 minutes
_st_lock: Any = __import__("threading").Lock()

# mtime-gap chain heuristic constants
_MAX_MTIME_GAP_SECS: float = 120.0  # 2 minutes — close mtime gap = likely chain
_SEMANTIC_THRESHOLD: float = 0.35  # cosine similarity threshold for chain verification


def _get_st_model() -> Any:
    """Get or create cached SentenceTransformer, unloading after 5 min idle.

    Releases the model to free memory when no embeddings have been requested
    for 5 minutes. Subsequent calls re-load from scratch (~60s cold start).
    Thread-safe via _st_lock.
    """
    import time

    global _st_model, _st_model_last_used
    now = time.monotonic()

    with _st_lock:
        if _st_model is not None and (now - _st_model_last_used) > _ST_MODEL_TTL_SECONDS:
            del _st_model
            _st_model = None

        if _st_model is None:
            from sentence_transformers import SentenceTransformer

            _st_model = SentenceTransformer("all-MiniLM-L6-v2")
            _st_model_last_used = now
            logger.debug("Loaded SentenceTransformer (all-MiniLM-L6-v2)")
        else:
            _st_model_last_used = now

        return _st_model

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def _claude_base() -> Path:
    return Path.home() / ".claude"


def _projects_dir() -> Path:
    return _claude_base() / "projects"


def _handoff_dir() -> Path:
    return _claude_base() / "state" / "handoff"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SessionChainEntry:
    session_id: str
    transcript_path: Path
    parent_transcript_path: Path | None  # older → newer link
    created: datetime | None
    first_user_message: str | None = None


@dataclass
class SessionChainResult:
    entries: list[SessionChainEntry] = field(default_factory=list)
    depth: int = 0
    origin_session_id: str | None = None


# ---------------------------------------------------------------------------
# Strategy 1: Handoff-file chain
# ---------------------------------------------------------------------------


def _get_prior_transcript_path(handoff_path: Path) -> Path | None:
    """Extract prior session transcript path from a handoff file.

    Handles gracefully:
      - Missing handoff file
      - JSON decode errors
      - Missing/inaccessible transcript paths (archived or deleted files)
    """
    try:
        with open(handoff_path, encoding="utf-8") as f:
            data = json.load(f)
        path_str = data.get("resume_snapshot", {}).get("transcript_path")
        if path_str:
            p = Path(path_str)
            try:
                if p.exists():
                    return p
            except (OSError, PermissionError) as e:
                logger.warning("Transcript path inaccessible %s: %s", p, e)
    except (OSError, json.JSONDecodeError, PermissionError) as e:
        logger.warning("Failed to read handoff file %s: %s", handoff_path, e)
    return None


def _find_handoff_referencing(transcript_path: Path) -> Path | None:
    """Find handoff file whose resume_snapshot.transcript_path == transcript_path."""
    handoff_dir = _handoff_dir()
    if not handoff_dir.exists():
        return None
    target = str(transcript_path)
    for hf in handoff_dir.glob("console_*_handoff.json"):
        try:
            with open(hf, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("resume_snapshot", {}).get("transcript_path") == target:
                return hf
        except (OSError, json.JSONDecodeError, PermissionError):
            continue
    return None


def _resolve_transcript_path(session_id: str) -> Path | None:
    """Find the .jsonl path for a session ID by scanning projects directory."""
    for jsonl_file in _projects_dir().rglob(f"{session_id}.jsonl"):
        if jsonl_file.exists():
            return jsonl_file
    return None


def walk_handoff_chain(session_id: str, max_depth: int = 50) -> SessionChainResult:
    """Walk session chain via handoff files.

    Finds the handoff file that references the current session's transcript,
    then follows prior transcript paths through handoff files recursively.
    Returns entries in oldest-to-newest order.
    """
    current_transcript = _resolve_transcript_path(session_id)
    if not current_transcript:
        return SessionChainResult()

    handoff_path = _find_handoff_referencing(current_transcript)
    if not handoff_path:
        # No prior handoff found — this is the origin session
        return SessionChainResult(
            entries=[
                SessionChainEntry(
                    session_id=session_id,
                    transcript_path=current_transcript,
                    parent_transcript_path=None,
                    created=None,
                )
            ],
            depth=1,
            origin_session_id=session_id,
        )

    entries: list[SessionChainEntry] = []
    visited: set[str] = set()
    chain_depth = 0

    while handoff_path and chain_depth < max_depth:
        try:
            prior_transcript = _get_prior_transcript_path(handoff_path)
            if not prior_transcript or str(prior_transcript) in visited:
                break
            visited.add(str(prior_transcript))

            prior_session_id = prior_transcript.stem
            prior_handoff = _find_handoff_referencing(prior_transcript)

            entries.append(
                SessionChainEntry(
                    session_id=prior_session_id,
                    transcript_path=prior_transcript,
                    parent_transcript_path=None,
                    created=None,
                )
            )

            handoff_path = prior_handoff
        except (OSError, PermissionError, RuntimeError) as e:
            logger.warning("Failed to traverse chain at %s: %s", handoff_path, e)
            break
        chain_depth += 1

    entries.reverse()

    # Fill in parent links (entries are oldest→newest, so previous entry is the parent)
    for i, entry in enumerate(entries):
        if i > 0:
            entry.parent_transcript_path = entries[i - 1].transcript_path
    return SessionChainResult(
        entries=entries,
        depth=chain_depth + 1,
        origin_session_id=entries[0].session_id if entries else None,
    )


# ---------------------------------------------------------------------------
# Strategy 2: sessions-index scan (fallback for recent sessions without handoffs)
# ---------------------------------------------------------------------------

# Reverse-engineered from session-chain investigation:
# - Only /compact sessions have a recorded prior session (in handoff file)
# - Non-compact sessions have no parentage recorded
# - For compact sessions, the handoff file links to the PRIOR session's transcript
#   (the session that was running before /compact was invoked)
# - The NEW session (after /compact) starts with /compact as first message


def load_sessions_index(project_path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load sessions-index.json as a dict keyed by sessionId."""
    if project_path is None:
        project_path = _projects_dir() / "P--"
    idx_path = Path(project_path) / "sessions-index.json"
    if not idx_path.exists():
        return {}
    try:
        with open(idx_path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    # Handle both list and dict formats
    if isinstance(data, list):
        return {entry["sessionId"]: entry for entry in data}
    if isinstance(data, dict):
        if "entries" in data:
            return {e["sessionId"]: e for e in data["entries"]}
        if "sessions" in data:
            return {e["sessionId"]: e for e in data["sessions"]}
        # sessions-index.json format: {"<sessionId>": {...}}
        return data
    return {}


def _extract_first_user_message(jsonl_path: Path) -> str | None:
    """Read first user message text from a session transcript."""
    try:
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") == "user":
                    msg = entry.get("message", {})
                    if isinstance(msg, dict):
                        content = msg.get("content", [])
                    else:
                        content = []
                    if isinstance(content, str):
                        return content[:200]
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                return block.get("text", "")[:200]
                    return None
    except (OSError, PermissionError):
        pass
    return None


def _extract_last_goals(jsonl_path: Path, max_chars: int = 300) -> str | None:
    """Extract last assistant goal statements from a session transcript.

    Looks for assistant messages with goal-related content near the end of the session.
    Used for semantic chain verification: prior session's ending goals should match
    successor session's opening actions.
    """
    try:
        lines = []
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    lines.append(line)
        # Scan backwards for assistant messages with goal/task content
        goal_parts = []
        for line in reversed(lines[-50:]):  # last 50 lines
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "assistant":
                msg = entry.get("message", {})
                content = msg.get("content", [])
                if isinstance(content, str) and content:
                    goal_parts.append(content[:max_chars])
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "")
                            if text:
                                goal_parts.append(text[:max_chars])
                if goal_parts:
                    break
        return " ".join(reversed(goal_parts))[:max_chars] if goal_parts else None
    except (OSError, PermissionError):
        pass
    return None


def walk_sessions_index_chain(
    session_id: str,
    project_path: Path | None = None,
) -> SessionChainResult:
    """Walk session chain using sessions-index.json mtime ordering.

    This is a best-effort fallback for recent sessions that have no handoff files.
    Heuristic: sessions whose first user message contains "/compact" are continuations.
    The chain is inferred by sorting sessions by mtime and linking /compact sessions
    to the nearest prior session.

    Limitations:
      - Only /compact sessions can be chained (they have a prior session)
      - Non-compact sessions (e.g., new terminal starts) cannot be linked to prior sessions
      - Chain inference via mtime ordering is approximate, not deterministic
    """
    if project_path is None:
        project_path = _projects_dir() / "P--"

    sessions_index = load_sessions_index(project_path)

    # Collect sessions using createdAt from sessions-index (st_birthtime = session birth)
    # Fall back to st_birthtime if sessions-index lacks the entry
    sessions: dict[str, tuple[Path, datetime]] = {}
    project = Path(project_path)
    for sid, info in sessions_index.items():
        # Try fullPath first, then reconstruct path
        full_path = info.get("fullPath")
        if full_path:
            p = Path(full_path)
        else:
            p = project / f"{sid}.jsonl"
        if not p.exists():
            continue
        # Use createdAt (st_birthtime) for chronological ordering
        created_at_ms = info.get("createdAt")
        if created_at_ms:
            try:
                created = datetime.fromtimestamp(created_at_ms / 1000)
            except (ValueError, OSError):
                created = datetime.min
        else:
            try:
                stat_result = p.stat()
                # st_birthtime = session birth (Python 3.12+ / Windows); st_ctime = metadata change on Unix
                if hasattr(stat_result, "st_birthtime"):
                    created = datetime.fromtimestamp(stat_result.st_birthtime)
                else:
                    created = datetime.fromtimestamp(stat_result.st_ctime)  # pyright: ignore[deprecated]
            except OSError:
                created = datetime.min
        sessions[sid] = (p, created)

    if session_id not in sessions:
        return SessionChainResult()

    # Pre-compute first user messages for all sessions
    first_user_messages: dict[str, str] = {}
    for sid, (path, _) in sessions.items():
        msg = _extract_first_user_message(path)
        if msg:
            first_user_messages[sid] = msg

    # ---- mtime-gap + semantic verification for ALL sessions ----
    # Algorithm: for each session, predecessor = closest prior session by mtime gap
    #            semantic verify prior's last-goals vs successor's first-user-message
    #            if cosine sim >= threshold → chain confirmed
    # This captures non-compact sessions too (new terminal starts, etc.)

    # Build sorted list by created timestamp
    sorted_sessions = sorted(sessions.items(), key=lambda x: x[1][1])
    sorted_ids = [sid for sid, _ in sorted_sessions]
    sid_to_idx = {sid: i for i, sid in enumerate(sorted_ids)}
    session_mtimes = {sid: ts for sid, (_, ts) in sorted_sessions}

    chain: list[str] = []
    visited: set[str] = set()
    current = session_id

    while current and current not in visited:
        visited.add(current)
        chain.append(current)

        current_idx = sid_to_idx.get(current, -1)
        if current_idx <= 0:
            break  # No prior sessions

        # Find predecessor with smallest mtime gap
        current_path, current_mtime = sessions[current]
        predecessor_id: str | None = None
        smallest_gap = _MAX_MTIME_GAP_SECS

        for i in range(current_idx - 1, -1, -1):
            pred_id = sorted_ids[i]
            if pred_id in visited:
                continue
            pred_path, pred_mtime = sessions[pred_id]
            gap = (current_mtime - pred_mtime).total_seconds()
            if gap <= 0 or gap >= smallest_gap:
                continue
            smallest_gap = gap
            predecessor_id = pred_id

        if predecessor_id is None:
            break

        # Semantic verification: prior's last-goals vs current's first-user-message
        prior_goals = _extract_last_goals(current_path)  # prior's ending goals
        current_first_msg = first_user_messages.get(current, "") or _extract_first_user_message(current_path)

        if prior_goals and current_first_msg:
            sim = _semantic_sim(prior_goals, current_first_msg)
            if sim < _SEMANTIC_THRESHOLD:
                break  # Gap too large or semantics don't match — stop chaining

        current = predecessor_id

    chain.reverse()

    # Build entries with parent links
    entries: list[SessionChainEntry] = []
    for i, sid in enumerate(chain):
        path, mtime = sessions[sid]
        parent_path: Path | None = None
        if i > 0:
            parent_path = sessions[chain[i - 1]][0]
        first_msg = first_user_messages.get(sid, "")
        if not first_msg:
            first_msg = _extract_first_user_message(path) or ""
        entries.append(
            SessionChainEntry(
                session_id=sid,
                transcript_path=path,
                parent_transcript_path=parent_path,
                created=mtime,
                first_user_message=first_msg or None,
            )
        )

    return SessionChainResult(
        entries=entries,
        depth=len(entries),
        origin_session_id=chain[0] if chain else None,
    )


# ---------------------------------------------------------------------------
# Strategy 3: Semantic similarity fallback (for sessions without handoffs)
# ---------------------------------------------------------------------------


def _session_text(info: dict) -> str:
    """Extract searchable text from sessions-index entry.

    Tries goal, lastPrompt, and summary (in that order) to find non-empty text.
    Falls back to summary if goal and lastPrompt are empty.
    """
    parts = []
    if info.get("goal"):
        parts.append(info["goal"])
    lp = info.get("lastPrompt", "")
    if lp:
        parts.append(lp[:500])
    # Fallback to summary if both goal and lastPrompt are empty
    elif info.get("summary"):
        parts.append(info["summary"][:500])
    af = info.get("active_files", [])
    if af:
        parts.append(" ".join(af[:10]))
    return " | ".join(parts) if parts else ""


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _semantic_sim(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two text strings using SentenceTransformer."""
    if not text_a or not text_b:
        return 0.0
    try:
        model = _get_st_model()
        vectors = model.encode([text_a, text_b], normalize_embeddings=True)
        return _cosine_sim(vectors[0].astype(np.float32), vectors[1].astype(np.float32))
    except (ImportError, OSError, RuntimeError):
        return 0.0


def walk_semantic_chain(
    session_id: str,
    project_path: Path | None = None,
    threshold: float = 0.5,
    window_days: int = 7,
    max_entries: int = 20,
) -> SessionChainResult:
    """Walk session chain via semantic similarity fallback.

    Uses EmbedClient to embed session text from sessions-index and finds
    prior sessions by cosine similarity. This is a best-effort fallback when
    both handoff files and mtime heuristic fail.

    Args:
        session_id: Session UUID to walk backward from.
        project_path: Project directory. Defaults to P--.
        threshold: Minimum cosine similarity to consider a match (default 0.5).
        window_days: Number of days to search around target's createdAt (default 7).
        max_entries: Maximum number of entries to return (default 20).

    Returns:
        SessionChainResult with semantic matches sorted by similarity.
    """
    if project_path is None:
        project_path = _projects_dir() / "P--"

    sessions_index = load_sessions_index(project_path)
    if session_id not in sessions_index:
        return SessionChainResult()

    target_info = sessions_index[session_id]
    target_text = _session_text(target_info)
    if not target_text:
        return SessionChainResult()

    target_created_ms = target_info.get("createdAt")
    if not target_created_ms:
        return SessionChainResult()

    try:
        target_created = datetime.fromtimestamp(target_created_ms / 1000)
    except (ValueError, OSError):
        return SessionChainResult()

    window_start = target_created - timedelta(days=window_days)
    window_end = target_created + timedelta(days=window_days)

    # Build candidate list
    candidates: list[tuple[str, dict, str]] = []
    for sid, info in sessions_index.items():
        if sid == session_id:
            continue
        created_ms = info.get("createdAt")
        if not created_ms:
            continue
        try:
            created = datetime.fromtimestamp(created_ms / 1000)
        except (ValueError, OSError):
            continue
        if window_start <= created <= window_end:
            text = _session_text(info)
            if text:
                candidates.append((sid, info, text))

    if not candidates:
        return SessionChainResult()

    # Batch embed all texts
    all_texts = [target_text] + [c[2] for c in candidates]

    try:
        from core.chs.embeddings import get_embed_client

        client = get_embed_client()
        embeddings = client.embed_texts(all_texts)

        target_emb = np.frombuffer(embeddings[0], dtype=np.float32)
        candidate_embs = [np.frombuffer(e, dtype=np.float32) for e in embeddings[1:]]

        # Fall back to direct SentenceTransformer if daemon returned near-zero vectors
        if np.linalg.norm(target_emb) < 0.01:
            raise ValueError("Daemon returned near-zero embedding")
    except (ImportError, OSError, ConnectionError, RuntimeError):
        # Daemon unavailable, import failure, or near-zero fallback —
        # use direct sentence-transformers
        try:
            model = _get_st_model()
            vectors = model.encode(all_texts, normalize_embeddings=True)
            target_emb = vectors[0].astype(np.float32)
            candidate_embs = [vectors[i + 1].astype(np.float32) for i in range(len(candidates))]
        except (ImportError, OSError, RuntimeError):
            # Model unavailable — graceful degradation
            return SessionChainResult()

    # Compute similarities
    matches: list[tuple[str, Path, datetime, float]] = []
    for i, (sid, info, _) in enumerate(candidates):
        sim = _cosine_sim(target_emb, candidate_embs[i])
        if sim >= threshold:
            full_path = info.get("fullPath")
            if full_path:
                p = Path(full_path)
            else:
                p = Path(project_path) / f"{sid}.jsonl"
            if p.exists():
                created_ms = info.get("createdAt")
                try:
                    created = datetime.fromtimestamp(created_ms / 1000)
                except (ValueError, OSError):
                    created = datetime.min
                matches.append((sid, p, created, sim))

    if not matches:
        return SessionChainResult()

    # Sort by similarity descending
    matches.sort(key=lambda x: x[3], reverse=True)

    entries = [
        SessionChainEntry(
            session_id=sid,
            transcript_path=path,
            parent_transcript_path=None,
            created=created,
            first_user_message=None,
        )
        for sid, path, created, _ in matches[:max_entries]
    ]

    return SessionChainResult(
        entries=entries,
        depth=len(entries),
        origin_session_id=entries[0].session_id if entries else None,
    )


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------


def walk_session_chain(
    session_id: str,
    project_path: Path | None = None,
    max_depth: int = 50,
    newest_first: bool = False,
) -> SessionChainResult:
    """Walk session chain using the best available strategy.

    Args:
        session_id: Session UUID to walk backward from.
        project_path: Project directory. Defaults to P--.
        max_depth: Maximum chain depth (handoff strategy only).
        newest_first: If True, return entries in newest-to-oldest order (current session first).
            Default False (oldest-to-newest).

    Returns:
        SessionChainResult with entries in oldest-to-newest order by default,
        or newest-to-oldest if newest_first=True.

    Strategy selection:
      - If handoff files exist linking to prior sessions → handoff chain
      - If sessions-index mtime heuristic finds priors → mtime chain
      - If semantic similarity finds matches → semantic chain
      - Otherwise → origin only (graceful degradation)
    """
    if project_path is None:
        project_path = _projects_dir() / "P--"

    # Strategy 1: Try handoff-file chain first (reliable for sessions with handoff files)
    handoff_result = walk_handoff_chain(session_id, max_depth)
    if handoff_result.entries and handoff_result.entries[0].session_id != session_id:
        if newest_first:
            handoff_result.entries.reverse()
        return handoff_result

    # Strategy 2: Fall back to sessions-index mtime heuristic
    mtime_result = walk_sessions_index_chain(session_id, project_path)
    if mtime_result.entries and mtime_result.entries[0].session_id != session_id:
        if newest_first:
            mtime_result.entries.reverse()
        return mtime_result  # mtime found prior(s)

    # Strategy 3: Fall back to semantic similarity
    semantic_result = walk_semantic_chain(session_id, project_path)
    if semantic_result.entries:
        if newest_first:
            semantic_result.entries.reverse()
        return semantic_result

    return mtime_result  # all fallbacks exhausted — origin only


def get_all_chain_files(
    session_id: str,
    project_path: Path | None = None,
    newest_first: bool = False,
) -> list[Path]:
    """Get all transcript file paths in a session chain.

    Args:
        session_id: Session UUID to walk backward from.
        project_path: Project directory. Defaults to P--.
        newest_first: If True, return paths in newest-to-oldest order (current session first).
            Default False (oldest-to-newest).

    Returns:
        List of transcript paths in the specified order.
    """
    result = walk_session_chain(session_id, project_path, newest_first=newest_first)
    return [e.transcript_path for e in result.entries]
