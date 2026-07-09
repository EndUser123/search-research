"""Per-query telemetry for /search.

Emits ONE structured JSON line per query that reaches the intent filter,
capturing the inputs and outputs needed to answer "is the intent filter
load-bearing, and is result-quality actually broken?" from data.

Schema (one JSON object per line):
    {
      "ts": "2026-07-08T19:03:00.123456",      # ISO local time
      "query_hash": "a1b2c3d4e5f60718",         # sha256(query)[:16], never raw text
      "intent": "technical",                    # classified IntentType value
      "confidence": 0.90,                       # classifier confidence 0..1
      "all_backends_count": 18,                 # fan-out if filter were absent
      "filtered_backends_count": 8,             # fan-out after intent filter
      "classify_ms": 9.4,                       # classify_query_intent latency
      "returned_count": 7,                      # ranked results returned to caller
      "cache_hit": false                        # whether the query was served from cache
    }

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
    """Append one structured line to the telemetry log. Never raises.

    Args mirror the schema above. ``path`` is for tests; production writes go
    to resolve_path().
    """
    record = {
        "ts": datetime.now().isoformat(),
        "query_hash": query_hash,
        "intent": intent,
        "confidence": round(float(confidence), 4),
        "all_backends_count": int(all_backends_count),
        "filtered_backends_count": int(filtered_backends_count),
        "classify_ms": round(float(classify_ms), 3),
        "returned_count": int(returned_count),
        "cache_hit": bool(cache_hit),
    }
    target = path if path is not None else resolve_path()
    line = json.dumps(record, ensure_ascii=False)
    try:
        with _write_lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except OSError:
        # Telemetry is non-blocking: never propagate into the search path.
        return


def log_quality_check(
    *,
    query_hash: str,
    satisfactory: bool,
    confidence: float,
    backend_diversity: int,
    fresh: bool,
    path: Path | None = None,
) -> None:
    """Append a quality-check record for the best result of a /search.

    This is the FM-4 input: a soak over these records yields the
    is_satisfactory pass-rate on real traffic. Emitted from
    UnifiedAsyncRouter._should_skip_web (where is_satisfactory is actually
    called on the best result), which runs AFTER the local router has already
    emitted its intent_filter record — so it is a SEPARATE line, joined to the
    filter record by query_hash. Never raises.
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
    target = path if path is not None else resolve_path()
    line = json.dumps(record, ensure_ascii=False)
    try:
        with _write_lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "a", encoding="utf-8") as f:
                f.write(line + "
")
    except OSError:
        return


def log_quality_check(
    *,
    query_hash: str,
    satisfactory: bool,
    confidence: float,
    backend_diversity: int,
    fresh: bool,
    path: Path | None = None,
) -> None:
    """Append a quality-check record for the best result of a /search.

    This is the FM-4 input: a soak over these records yields the
    is_satisfactory pass-rate on real traffic. Emitted from
    UnifiedAsyncRouter._should_skip_web (where is_satisfactory is actually
    called on the best result), which runs AFTER the local router has already
    emitted its intent_filter record — so it is a SEPARATE line, joined to the
    filter record by query_hash. Never raises.
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
    target = path if path is not None else resolve_path()
    line = json.dumps(record, ensure_ascii=False)
    try:
        with _write_lock:
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "a", encoding="utf-8") as f:
                f.write(line + "
")
    except OSError:
        return
