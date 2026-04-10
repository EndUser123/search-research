"""Session chain traversal for Claude Code.

Provides a unified interface for finding all session transcript files in a
session chain, given any session ID.

Three strategies, tried in order:
  1. Handoff-file chain   - reliable when handoff files exist
  2. sessions-index scan  - fallback using mtime gap heuristic + semantic verification
  3. Semantic similarity  - fallback using embedding similarity

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
import time
import asyncio

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
_cache_lock: Any = __import__("threading").Lock()

# mtime-gap chain heuristic constants
_MAX_MTIME_GAP_SECS: float = 120.0  # 2 minutes - close mtime gap = likely chain
_SEMANTIC_THRESHOLD: float = 0.35  # cosine similarity threshold for chain verification
_SEMANTIC_TIMEOUT_SECONDS: float = 30.0  # max time for embedding call before returning 0.0
_MAX_TRANSCRIPT_READ_BYTES: int = 1024 * 1024  # 1 MB max per transcript read
_CACHE_MAX_ENTRIES: int = 50  # max cached project sessions indexes
_CACHE_EVICT_COUNT: int = 10  # entries to evict when cache exceeds max


def _get_st_model() -> Any:
    """Get or create cached SentenceTransformer, unloading after 5 min idle."""
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
    created: datetime | None = None
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

    SECURITY: Validates that the extracted path has a .jsonl suffix before returning,
    preventing arbitrary file return from handoff data.
    """
    try:
        with open(handoff_path, encoding="utf-8") as f:
            data = json.load(f)
        path_str = data.get("resume_snapshot", {}).get("transcript_path")
        if path_str:
            p = Path(path_str)
            try:
                # SECURITY: Verify .jsonl suffix to prevent arbitrary file return
                if p.suffix == ".jsonl" and p.exists():
                    return p
                elif p.suffix != ".jsonl":
                    logger.warning("Handoff transcript_path is not .jsonl: %s", p)
            except (OSError, PermissionError) as e:
                logger.warning("Transcript path inaccessible %s: %s", p, e)
    except (OSError, json.JSONDecodeError, PermissionError) as e:
        logger.warning("Failed to read handoff file %s: %s", handoff_path, e)
    return None


def _find_handoff_referencing(transcript_path: Path) -> Path | None:
    """Find handoff file whose resume_snapshot.transcript_path == transcript_path.

    Synchronous version for use in sync walk_handoff_chain.
    """
    handoff_dir = _handoff_dir()
    if not handoff_dir.exists():
        return None
    target = str(transcript_path)

    for hf in handoff_dir.glob("console_*_handoff.json"):
        try:
            with open(hf, encoding="utf-8") as f:
                handoff_data = json.load(f)
            if handoff_data.get("resume_snapshot", {}).get("transcript_path") == target:
                return hf
        except (OSError, json.JSONDecodeError, PermissionError):
            continue
    return None


def _resolve_transcript_path(session_id: str) -> Path | None:
    """Find the .jsonl path for a session ID by scanning projects directory.

    SECURITY: Rejects session_ids containing path traversal sequences before glob
    interpolation to prevent directory traversal attacks.
    """
    # Reject path traversal attempts before using in glob
    if ".." in session_id or "/" in session_id or "\\" in session_id:
        logger.warning("Invalid session_id (path traversal attempt): %s", session_id)
        return None
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

    while handoff_path and len(entries) < max_depth:
        prior_transcript = None
        prior_session_id: str | None = None

        # TOCTOU-fix: read handoff within try/except to handle concurrent deletion
        try:
            prior_transcript = _get_prior_transcript_path(handoff_path)
        except (OSError, PermissionError, RuntimeError) as e:
            logger.warning("Failed to read handoff %s: %s", handoff_path, e)

        if prior_transcript:
            prior_session_id = prior_transcript.stem
            if str(prior_transcript) in visited:
                break
            visited.add(str(prior_transcript))
        else:
            prior_session_id = handoff_path.stem.replace("_handoff", "")

        entries.append(
            SessionChainEntry(
                session_id=prior_session_id or "unknown",
                transcript_path=prior_transcript or Path("."),
                parent_transcript_path=None,
                created=None,
            )
        )

        # TOCTOU-fix: find prior handoff within try/except
        if prior_transcript:
            try:
                handoff_path = _find_handoff_referencing(prior_transcript)
            except (OSError, PermissionError, RuntimeError) as e:
                logger.warning("Failed to find handoff referencing %s: %s", prior_transcript, e)
                handoff_path = None
        else:
            handoff_path = None

        if handoff_path is None:
            break

    entries.reverse()

    for i, entry in enumerate(entries):
        if i > 0:
            entry.parent_transcript_path = entries[i - 1].transcript_path

    # FIX: Use len(entries) instead of chain_depth+1 to avoid off-by-one on early break
    return SessionChainResult(
        entries=entries,
        depth=len(entries),
        origin_session_id=entries[0].session_id if entries else None,
    )


# ---------------------------------------------------------------------------
# Strategy 2: sessions-index scan (mtime-gap + semantic verification)
# ---------------------------------------------------------------------------


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
    if isinstance(data, list):
        return {entry["sessionId"]: entry for entry in data}
    if isinstance(data, dict):
        if "entries" in data:
            return {e["sessionId"]: e for e in data["entries"]}
        if "sessions" in data:
            return {e["sessionId"]: e for e in data["sessions"]}
        if not isinstance(data, list) and "entries" not in data:
            # Direct-key format: {"uuid": {"sessionId": "...", ...}, ...}
            return data
    return {}


def _extract_first_user_message(jsonl_path: Path) -> str | None:
    """Read first user message text from a session transcript.

    SECURITY: Bounded read — stops after _MAX_TRANSCRIPT_READ_BYTES to prevent
    memory pressure from large files. Finishes the current line before stopping
    to avoid producing partial JSON objects.
    """
    try:
        bytes_read = 0
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line_bytes = len(line.encode("utf-8"))
                if bytes_read + line_bytes > _MAX_TRANSCRIPT_READ_BYTES:
                    # SECURITY: If the very first line alone exceeds the limit, the file is
                    # oversized. Return the content directly (truncated) rather than None,
                    # preserving at least partial functionality for legitimate large files.
                    if bytes_read == 0:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                            except json.JSONDecodeError:
                                return None
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
                    break  # Stop at boundary; do not produce partial JSON
                bytes_read += line_bytes
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

    SECURITY: Bounded read — stops after _MAX_TRANSCRIPT_READ_BYTES to prevent
    memory pressure. Reads all lines into memory up to the limit, then processes
    the last 50 lines of the buffered content.
    """
    try:
        lines = []
        bytes_read = 0
        with open(jsonl_path, encoding="utf-8") as f:
            for line in f:
                line_bytes = len(line.encode("utf-8"))
                if bytes_read + line_bytes > _MAX_TRANSCRIPT_READ_BYTES:
                    # SECURITY: If the very first line alone exceeds the limit, include it
                    # directly rather than skipping — preserves partial data for oversized files.
                    if bytes_read == 0:
                        line = line.strip()
                        if line:
                            lines.append(line)
                    break  # Stop at boundary; do not produce partial JSON
                bytes_read += line_bytes
                line = line.strip()
                if line:
                    lines.append(line)
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


def _scan_jsonl_sessions(project_path: Path) -> dict[str, dict[str, Any]]:
    """Scan JSONL files directly to build an in-memory sessions index.

    Returns dict: {session_id: {"sessionId": str, "createdAt": float, "fullPath": Path}}
    Reads first entry of each .jsonl for sessionId and createdAt.
    Cached for the lifetime of the process on that project_path.

    Cache is bounded to _CACHE_MAX_ENTRIES entries (LRU eviction of _CACHE_EVICT_COUNT
    oldest entries when limit is exceeded). Access and eviction are atomic via
    _cache_lock to prevent concurrent corruption.
    """
    if not hasattr(_scan_jsonl_sessions, "_cache"):
        _scan_jsonl_sessions._cache: dict[str, dict[str, dict[str, Any]]] = {}

    cache = _scan_jsonl_sessions._cache
    key = str(project_path)

    with _cache_lock:
        if key in cache:
            return cache[key]

        sessions: dict[str, dict[str, Any]] = {}
        try:
            for jsonl_path in Path(project_path).rglob("*.jsonl"):
                try:
                    with open(jsonl_path, encoding="utf-8") as f:
                        first_line = f.readline()
                    if not first_line.strip():
                        continue
                    entry = json.loads(first_line)
                    sid = entry.get("sessionId") or entry.get("session_id")
                    if not sid:
                        continue
                    ts_val = entry.get("timestamp") or entry.get("createdAt")
                    # Handle both integer milliseconds (correct) and ISO 8601 strings (incorrect)
                    if isinstance(ts_val, str):
                        try:
                            dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                            ts_val = int(dt.timestamp() * 1000)  # convert to milliseconds
                        except (ValueError, TypeError):
                            ts_val = None
                    sessions[sid] = {
                        "sessionId": sid,
                        "createdAt": ts_val,
                        "fullPath": str(jsonl_path),
                    }
                except (OSError, json.JSONDecodeError):
                    continue
        except OSError:
            pass

        cache[key] = sessions

        # LRU eviction: remove oldest entries when cache exceeds limit
        if len(cache) > _CACHE_MAX_ENTRIES:
            # Sort by insertion order (dict preserves insertion order in Python 3.7+)
            # Evict the first _CACHE_EVICT_COUNT entries (oldest)
            for _ in range(_CACHE_EVICT_COUNT):
                if cache:
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]

        return sessions


def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _semantic_sim(text_a: str, text_b: str) -> float:
    """Compute cosine similarity between two text strings using SentenceTransformer.

    Uses ThreadPoolExecutor + Future.result(timeout) to bound wall-clock time.
    Returns 0.0 if the embedding call does not complete within _SEMANTIC_TIMEOUT_SECONDS.
    """
    if not text_a or not text_b:
        return 0.0
    try:
        model = _get_st_model()
        # ThreadPoolExecutor with timeout is the only way to bound a blocking call
        with __import__("concurrent.futures", fromlist=["ThreadPoolExecutor"]).ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(model.encode, [text_a, text_b], normalize_embeddings=True)
            try:
                vectors = future.result(timeout=_SEMANTIC_TIMEOUT_SECONDS)
                return _cosine_sim(vectors[0].astype(np.float32), vectors[1].astype(np.float32))
            except __import__("concurrent.futures").TimeoutError:
                logger.warning("Semantic similarity timed out after %ss", _SEMANTIC_TIMEOUT_SECONDS)
                return 0.0
    except (ImportError, OSError, RuntimeError) as e:
        logger.warning("Semantic similarity computation failed: %s", e)
        return 0.0


def walk_sessions_index_chain(
    session_id: str,
    project_path: Path | None = None,
    max_depth: int = 50,
) -> SessionChainResult:
    """Walk session chain using sessions-index.json mtime ordering + semantic verification.

    For each session, finds predecessor with smallest mtime gap (< MAX_MTIME_GAP_SECS).
    Semantic verification: predecessor's last-goals vs successor's first-user-message.
    If cosine sim >= threshold → chain link confirmed.
    Otherwise → try next-best mtime candidate (not: stop entire chain).

    This captures ALL sessions, not just /compact continuations.
    """
    if project_path is None:
        project_path = _projects_dir() / "P--"

    sessions_index = load_sessions_index(project_path)
    # Fallback: if sessions-index is stale, scan JSONL files directly
    if session_id not in sessions_index:
        sessions_index = _scan_jsonl_sessions(project_path)

    sessions: dict[str, tuple[Path, datetime]] = {}
    project = Path(project_path)
    for sid, info in sessions_index.items():
        full_path = info.get("fullPath")
        if full_path:
            p = Path(full_path)
        else:
            p = project / f"{sid}.jsonl"
        if not p.exists():
            logger.warning("Transcript file missing for session %s: %s", sid, p)
            continue
        created_at_ms = info.get("createdAt")
        if created_at_ms:
            try:
                created = datetime.fromtimestamp(created_at_ms / 1000)
            except (ValueError, OSError):
                created = datetime.min
        else:
            try:
                stat_result = p.stat()
                if hasattr(stat_result, "st_birthtime"):
                    created = datetime.fromtimestamp(stat_result.st_birthtime)
                else:
                    created = datetime.fromtimestamp(stat_result.st_ctime)
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

    # Build sorted list by created timestamp
    sorted_sessions = sorted(sessions.items(), key=lambda x: x[1][1])
    sorted_ids = [sid for sid, _ in sorted_sessions]
    sid_to_idx = {sid: i for i, sid in enumerate(sorted_ids)}

    chain: list[str] = []
    visited: set[str] = set()
    current = session_id

    while current and current not in visited and len(chain) < max_depth:
        visited.add(current)
        chain.append(current)

        current_idx = sid_to_idx.get(current, -1)
        if current_idx <= 0:
            break  # No prior sessions

        current_path, current_mtime = sessions[current]

        # Find predecessor with smallest mtime gap
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

        # Semantic verification: predecessor's last-goals vs current's first-message
        predecessor_path = sessions[predecessor_id][0]
        prior_goals = _extract_last_goals(predecessor_path)
        current_first_msg = first_user_messages.get(current, "") or _extract_first_user_message(current_path)

        # prior_goals handling: if extraction failed, log warning and continue chain attempt
        if not prior_goals:
            logger.warning("Could not extract last goals from %s (chain verification may be impaired)", predecessor_id)

        if prior_goals and current_first_msg:
            sim = _semantic_sim(prior_goals, current_first_msg)
            if sim < _SEMANTIC_THRESHOLD:
                # FIX: Instead of breaking entirely, try next-best mtime candidate
                # Don't break - try to find an alternative predecessor with same gap constraint
                # Clear predecessor and loop to find next-best
                alt_found = False
                alt_gap = _MAX_MTIME_GAP_SECS
                alt_pred: str | None = None
                for i in range(current_idx - 1, -1, -1):
                    pid = sorted_ids[i]
                    if pid in visited:
                        continue
                    pp, pt = sessions[pid]
                    g = (current_mtime - pt).total_seconds()
                    if g <= 0 or g >= alt_gap:
                        continue
                    alt_gap = g
                    alt_pred = pid

                if alt_pred is not None and alt_pred != predecessor_id:
                    predecessor_id = alt_pred
                    predecessor_path = sessions[predecessor_id][0]
                    prior_goals_alt = _extract_last_goals(predecessor_path)
                    current_first_alt = first_user_messages.get(current, "") or _extract_first_user_message(current_path)
                    if prior_goals_alt and current_first_alt:
                        sim_alt = _semantic_sim(prior_goals_alt, current_first_alt)
                        if sim_alt >= _SEMANTIC_THRESHOLD:
                            alt_found = True
                        # else: no verified alternative, stop

                if not alt_found:
                    # Intentional early exit: chain verification must not proceed on below-threshold
                    # similarity. This exits before reaching max_depth — this is expected behavior
                    # for semantic verification failure. The partial chain is returned as-is.
                    logger.warning(
                        "Semantic similarity below threshold for session %s — returning partial chain (depth=%d, max_depth=%d)",
                        current,
                        len(chain),
                        max_depth,
                    )
                    break  # No verified alternative - stop chaining

        current = predecessor_id

    chain.reverse()

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
# Strategy 3: Semantic similarity fallback
# ---------------------------------------------------------------------------


def _semantic_text(info: dict) -> str:
    """Extract searchable text from a sessions-index info dict or JSONL transcript.

    Reads goal/lastPrompt/summary from info dict if present (sessions-index path).
    Falls back to _extract_first_user_message and _extract_last_goals from JSONL.
    """
    # Try info dict fields first (sessions-index path)
    parts = []
    if info.get("goal"):
        parts.append(info["goal"])
    lp = info.get("lastPrompt", "")
    if lp:
        parts.append(lp[:500])
    elif info.get("summary"):
        parts.append(info["summary"][:500])
    af = info.get("active_files", [])
    if af:
        parts.append(" ".join(af[:10])[:500])
    if parts:
        return " | ".join(parts)

    # Fallback: extract from JSONL transcript directly
    full_path = info.get("fullPath")
    if full_path:
        p = Path(full_path)
        first_msg = _extract_first_user_message(p) or ""
        goals_text = _extract_last_goals(p) or ""
        combined = f"{goals_text} | {first_msg}".strip()
        if combined:
            return combined
    return ""


def walk_semantic_chain(
    session_id: str,
    project_path: Path | None = None,
    threshold: float = 0.5,
    window_days: int = 7,
    max_entries: int = 20,
) -> SessionChainResult:
    """Walk session chain via semantic similarity (no mtime constraint).

    Embeds all sessions in a time window and ranks by cosine similarity.
    Called directly when mtime-gapped chain is insufficient.
    Kept as a standalone function for direct invocation if needed.
    """
    if project_path is None:
        project_path = _projects_dir() / "P--"

    sessions_index = load_sessions_index(project_path)
    # Fallback: if sessions-index is stale, scan JSONL files directly
    if session_id not in sessions_index:
        sessions_index = _scan_jsonl_sessions(project_path)
    if session_id not in sessions_index:
        return SessionChainResult()

    target_info = sessions_index[session_id]
    target_text = _semantic_text(target_info)
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
            text = _semantic_text(info)
            if text:
                candidates.append((sid, info, text))

    if not candidates:
        return SessionChainResult()

    all_texts = [target_text] + [c[2] for c in candidates]

    try:
        from search_research.core.chs.embeddings import get_embed_client

        client = get_embed_client()
        embeddings = client.embed_texts(all_texts)

        target_emb = np.frombuffer(embeddings[0], dtype=np.float32)
        candidate_embs = [np.frombuffer(e, dtype=np.float32) for e in embeddings[1:]]

        if np.linalg.norm(target_emb) < 0.01:
            raise ValueError("Daemon returned near-zero embedding")
    except (ImportError, OSError, ConnectionError, RuntimeError):
        try:
            model = _get_st_model()
            vectors = model.encode(all_texts, normalize_embeddings=True)
            target_emb = vectors[0].astype(np.float32)
            candidate_embs = [vectors[i + 1].astype(np.float32) for i in range(len(candidates))]
        except (ImportError, OSError, RuntimeError):
            return SessionChainResult()

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

    Two strategies tried in order:
      1. Handoff-file chain    - deterministic via PreCompact hook handoff files
      2. mtime + semantic chain - finds candidates by mtime gap, verifies with semantic similarity

    Falls back gracefully: if Strategy 2 builds a partial chain, returns it as-is.
    """
    if project_path is None:
        project_path = _projects_dir() / "P--"

    # Strategy 1: Handoff-file chain
    handoff_result = walk_handoff_chain(session_id, max_depth)
    if handoff_result.entries and handoff_result.entries[0].session_id != session_id:
        if newest_first:
            handoff_result.entries.reverse()
        return handoff_result

    # Strategy 2: sessions-index mtime-gap + semantic
    mtime_result = walk_sessions_index_chain(session_id, project_path, max_depth)
    if mtime_result.entries and mtime_result.entries[0].session_id != session_id:
        if newest_first:
            mtime_result.entries.reverse()
        return mtime_result

    return mtime_result


def get_all_chain_files(
    session_id: str,
    project_path: Path | None = None,
    newest_first: bool = False,
) -> list[Path]:
    """Get all transcript file paths in a session chain."""
    result = walk_session_chain(session_id, project_path, newest_first=newest_first)
    return [e.transcript_path for e in result.entries]
