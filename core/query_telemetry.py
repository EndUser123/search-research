"""Per-query telemetry for /search.

Emits structured JSON lines that make the question "is the intent filter
load-bearing, and is result-quality actually broken?" answerable from data.

Two record shapes share one log file (distinguished by the ``event`` field):

1. ``intent_filter`` (one per /search that reaches the classifier) — the FM-3
   input. Captures whether the filter narrowed fan-out and what it cost.
       {ts, event:"intent_filter", query_hash, intent, confidence,
        all_backends_count, filtered_backends_count, classify_ms,
        returned_count, cache_hit}

2. ``quality_check`` (one per /search that produced a best result) — the FM-4
   input. Captures the is_satisfactory verdict on the best result.
       {ts, event:"quality_check", query_hash, satisfactory, confidence,
        backend_diversity, fresh}

The two are joined by ``query_hash``. ``cache_hit`` records (cache_hit=true,
intent="skipped_cache") mark queries the cache served without classification.

Non-blocking by contract: a telemetry write failure MUST NEVER raise into the
search path. Every public call swallows OSError and returns silently.

Write path is EXTERNAL to the plugin dir (per plugin state/log contract) and
overridable via SR_QUERY_TELEMETRY_PATH for tests.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from threading import Lock

_DEFAULT_PATH = r"P:/.claude/state/search_research/query_telemetry.jsonl"
_ENV_OVERRIDE = "SR_QUERY_TELEMETRY_PATH"
_write_lock = Lock()


def resolve_path() -> Path:
    """Resolve the telemetry log path from env or default."""
    return Path(os.environ.get(_ENV_OVERRIDE, _DEFAULT_PATH))


def hash_query(query: str) -> str:
    """Stable, privacy-preserving identifier for the raw query text.

    sha256 truncated to 16 hex chars — enough to dedup/join across logs without
    retaining the plaintext query.
    """
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]


def _append(record: dict, target: Path) -> None:
    """Append one JSON line. Never raises."""
    line = json.dumps(record, ensure_ascii=False)
    try:
        with _write_lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except OSError:
        return


def log_query_event(
    *,
    query_hash: str,
    intent: str,
    confidence: float,
    all_backends_count: int,
    filtered_backends_count: int,
    classify_ms: float,
    returned_count: int,
    cache_hit: bool = False,
    path: Path | None = None,
) -> None:
    """Append one intent_filter record (FM-3 input). Never raises."""
    record = {
        "ts": datetime.now().isoformat(),
        "event": "intent_filter",
        "query_hash": query_hash,
        "intent": intent,
        "confidence": round(float(confidence), 4),
        "all_backends_count": int(all_backends_count),
        "filtered_backends_count": int(filtered_backends_count),
        "classify_ms": round(float(classify_ms), 3),
        "returned_count": int(returned_count),
        "cache_hit": bool(cache_hit),
    }
    _append(record, path if path is not None else resolve_path())


def log_quality_check(
    *,
    query_hash: str,
    satisfactory: bool,
    confidence: float,
    backend_diversity: int,
    fresh: bool,
    path: Path | None = None,
) -> None:
    """Append a quality_check record for the best result of a /search (FM-4 input).

    Emitted from UnifiedAsyncRouter._should_skip_web, where is_satisfactory is
    actually called on the best result — which runs AFTER the local router has
    emitted its intent_filter record, so it is a SEPARATE line joined by
    query_hash. Never raises.
    """
    record = {
        "ts": datetime.now().isoformat(),
        "event": "quality_check",
        "query_hash": query_hash,
        "satisfactory": bool(satisfactory),
        "confidence": round(float(confidence), 4),
        "backend_diversity": int(backend_diversity),
        "fresh": bool(fresh),
    }
    _append(record, path if path is not None else resolve_path())
