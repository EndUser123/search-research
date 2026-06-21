"""cc-lazy-closure-debt debt store — JSONL persistence for deferral phrases.

State path: P:/.claude/state/cc-lazy-closure-debt/{terminal_id}.jsonl
Per spec: append_deferral() / recent_deferrals() / clear_terminal().

All public functions are safe under concurrent append from the Stop hook
(write+fsync) and tolerant of a missing file in the read path.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import time
import unicodedata
from pathlib import Path
from typing import Optional

# Per-process monotonic counter used to disambiguate records appended in the
# same second (sub-second ordering is needed for stable sort + max_count).
_seq_lock = threading.Lock()
_seq_counter = 0


def _next_seq() -> int:
    global _seq_counter
    with _seq_lock:
        _seq_counter += 1
        return _seq_counter


# Default state root — overridable via env var (used by tests)
DEFAULT_STATE_ROOT = Path(
    os.environ.get("CC_LAZY_CLOSURE_DEBT_STATE_DIR", "P:/.claude/state")
)
PLUGIN_NAME = "cc-lazy-closure-debt"


def _safe_id(value: Optional[str]) -> str:
    """Filesystem-safe terminal id fragment."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _normalize_phrase(phrase: str) -> str:
    """Normalize a deferral phrase so equivalent repeats collapse together."""
    text = unicodedata.normalize("NFKC", phrase or "")
    text = text.casefold()
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r'^[\"\'`(\[\{<\s]+', "", text)
    text = re.sub(r'[\"\'`)\]\}>.,;:!?]+$', "", text)
    return text


def _fingerprint_phrase(phrase: str) -> str:
    normalized = _normalize_phrase(phrase)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def get_state_dir(root: Optional[Path] = None) -> Path:
    """Return the per-plugin state directory (creates it)."""
    base = Path(root) if root is not None else DEFAULT_STATE_ROOT
    p = base / PLUGIN_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def _get_state_path(terminal_id: str, root: Optional[Path] = None) -> Path:
    safe = _safe_id(terminal_id)
    return get_state_dir(root) / f"{safe}.jsonl"


def _get_terminal_id() -> str:
    """Resolve terminal id from env (matches Stop hook fallback)."""
    return _safe_id(os.environ.get("CLAUDE_TERMINAL_ID", "default"))


def append_deferral(
    terminal_id: str,
    phrase: str,
    transcript_excerpt: str = "",
    state_root: Optional[Path] = None,
) -> None:
    """Append a deferral event to the JSONL store.

    Each line is a JSON object with: ts (unix), terminal_id, phrase,
    transcript_excerpt (first 200 chars of the assistant response).
    """
    tid = _safe_id(terminal_id or _get_terminal_id())
    path = _get_state_path(tid, state_root)
    now = int(time.time())
    now_ms = int(time.time() * 1000)
    record = {
        "ts": now,
        "ts_ms": now_ms,  # millisecond precision for sort order
        "seq": _next_seq(),
        "terminal_id": tid,
        "phrase": phrase,
        "canonical_phrase": _normalize_phrase(phrase),
        "fingerprint": _fingerprint_phrase(phrase),
        "occurrences": 1,
        "transcript_excerpt": (transcript_excerpt or "")[:200],
    }
    # Append+fsync for crash safety. We open in append mode so concurrent
    # Stop-hook invocations don't truncate each other.
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def resolve_deferral(
    terminal_id: str,
    fingerprint: str,
    state_root: Optional[Path] = None,
) -> None:
    """Mark a deferral fingerprint as formalized by appending a tombstone.

    Append-only, mirroring append_deferral's concurrency model (no rewrite of
    existing lines, so concurrent Stop-hook appends never race). Once a tombstone
    exists for a fingerprint, recent_deferrals() filters out the matching
    deferral, so a phrase that has been turned into a task stops re-surfacing on
    every UserPromptSubmit (the duplicate-task root cause).
    """
    tid = _safe_id(terminal_id or _get_terminal_id())
    path = _get_state_path(tid, state_root)
    now = int(time.time())
    record = {
        "ts": now,
        "ts_ms": int(time.time() * 1000),
        "seq": _next_seq(),
        "terminal_id": tid,
        "kind": "tombstone",
        "resolved_fingerprint": str(fingerprint),
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True))
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())


def resolve_deferral_by_phrase(
    terminal_id: str,
    phrase: str,
    state_root: Optional[Path] = None,
) -> None:
    """Resolve a deferral by its phrase (fingerprints it first).

    Convenience for callers that only have the human phrase (e.g. the
    PostToolUse hook reading a "Deferral: <phrase>" task subject). Normalization
    is deterministic, so the fingerprint matches the one stored at append time.
    """
    resolve_deferral(terminal_id, _fingerprint_phrase(phrase), state_root)


def recent_deferrals(
    terminal_id: str,
    max_age_h: float = 24.0,
    max_count: int = 5,
    state_root: Optional[Path] = None,
) -> list[dict]:
    """Return up to max_count deferrals newer than max_age_h hours.

    Sorted by most recent first. Each returned dict has ts, terminal_id,
    phrase, transcript_excerpt keys.
    """
    tid = _safe_id(terminal_id or _get_terminal_id())
    path = _get_state_path(tid, state_root)
    if not path.exists():
        return []
    cutoff = int(time.time()) - int(max_age_h * 3600)

    items: list[dict] = []
    resolved: set[str] = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict):
                    continue
                # Tombstone records mark a deferral as formalized (turned into a
                # task). Honor them regardless of age so a resolved phrase never
                # re-surfaces, even if its original line is still inside the window.
                fp_resolved = obj.get("resolved_fingerprint")
                if fp_resolved:
                    resolved.add(str(fp_resolved))
                    continue
                ts = int(obj.get("ts", 0))
                if ts >= cutoff:
                    items.append(obj)
    except OSError:
        return []

    grouped = _dedupe_deferrals(items)
    if resolved:
        grouped = [
            g
            for g in grouped
            if str(
                g.get("fingerprint")
                or _fingerprint_phrase(str(g.get("phrase", "")))
            )
            not in resolved
        ]
    # Newest first; use last_ts_ms for sub-second precision, then seq as tiebreaker
    grouped.sort(
        key=lambda r: (
            int(r.get("last_ts_ms", r.get("ts_ms", r.get("ts", 0) * 1000))),
            int(r.get("last_seq", r.get("seq", 0))),
        ),
        reverse=True,
    )
    return grouped[:max_count]


def _dedupe_deferrals(items: list[dict]) -> list[dict]:
    """Group equivalent deferrals into a single taskable record per phrase."""
    grouped: dict[str, dict] = {}
    for record in items:
        if not isinstance(record, dict):
            continue
        phrase = str(record.get("phrase", "") or "")
        fingerprint = str(record.get("fingerprint") or _fingerprint_phrase(phrase))
        ts = int(record.get("ts", 0))
        ts_ms = int(record.get("ts_ms", ts * 1000))
        seq = int(record.get("seq", 0))
        occurrences = int(record.get("occurrences", 1) or 1)

        current = grouped.get(fingerprint)
        if current is None:
            current = dict(record)
            current["fingerprint"] = fingerprint
            current["canonical_phrase"] = str(record.get("canonical_phrase") or _normalize_phrase(phrase))
            current["occurrences"] = occurrences
            current["first_ts"] = ts
            current["first_ts_ms"] = ts_ms
            current["first_seq"] = seq
            current["last_ts"] = ts
            current["last_ts_ms"] = ts_ms
            current["last_seq"] = seq
            current["ts"] = ts
            current["ts_ms"] = ts_ms
            grouped[fingerprint] = current
            continue

        current["occurrences"] = int(current.get("occurrences", 1) or 1) + occurrences
        first_ts = int(current.get("first_ts", ts))
        first_ts_ms = int(current.get("first_ts_ms", ts_ms))
        first_seq = int(current.get("first_seq", seq))
        if ts_ms < first_ts_ms or (ts_ms == first_ts_ms and seq < first_seq):
            current["first_ts"] = ts
            current["first_ts_ms"] = ts_ms
            current["first_seq"] = seq
            current["canonical_phrase"] = str(record.get("canonical_phrase") or current.get("canonical_phrase") or _normalize_phrase(phrase))
        last_ts_ms = int(current.get("last_ts_ms", ts_ms))
        last_seq = int(current.get("last_seq", seq))
        if ts_ms > last_ts_ms or (ts_ms == last_ts_ms and seq > last_seq):
            current["phrase"] = phrase or str(current.get("phrase", ""))
            current["transcript_excerpt"] = str(record.get("transcript_excerpt", current.get("transcript_excerpt", "")))
            current["last_ts"] = ts
            current["last_ts_ms"] = ts_ms
            current["last_seq"] = seq
            current["ts"] = ts
            current["ts_ms"] = ts_ms

    return list(grouped.values())


def clear_terminal(
    terminal_id: str,
    state_root: Optional[Path] = None,
) -> bool:
    """Delete the per-terminal debt file. Returns True if a file was removed."""
    tid = _safe_id(terminal_id or _get_terminal_id())
    path = _get_state_path(tid, state_root)
    if path.exists():
        try:
            path.unlink()
            return True
        except OSError:
            return False
    return False


def list_terminals(state_root: Optional[Path] = None) -> list[str]:
    """Return all terminal ids with debt files (for /debt list-all)."""
    d = get_state_dir(state_root)
    out: list[str] = []
    for p in sorted(d.glob("*.jsonl")):
        out.append(p.stem)
    return out
