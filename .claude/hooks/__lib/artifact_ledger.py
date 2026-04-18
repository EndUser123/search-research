"""Session-scoped ledger of 'found locally' artifacts.

Records file paths and keywords found via Grep/Glob/Read, then matches
against subsequent external fetch/install queries to enforce local-first evidence.
"""
import json
import os
import tempfile
import time
from pathlib import Path

LEDGER_DIR = Path.home() / ".claude" / "state"
TTL_SECONDS = 1800  # 30 minutes — stale findings expire
# Minimum keyword length to reduce false-positive collision (e.g., "py" matching unrelated queries)
MIN_KEYWORD_LEN = 5


def _path(session_id: str) -> Path:
    """Get ledger file path for session."""
    return LEDGER_DIR / f"artifact_ledger_{session_id}.json"


def record(session_id: str, keyword: str, source: str, turn: int) -> None:
    """Record a found artifact (keyword + source path) into the ledger.

    Args:
        session_id: Current session ID
        keyword: Search term (pattern, filename stem, etc.)
        source: Path where it was found
        turn: Turn index when found
    """
    if not session_id or not keyword or not source:
        return

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    p = _path(session_id)
    data = load(session_id)

    data["entries"].append({
        "keyword": keyword.lower(),
        "source": source,
        "turn": turn,
        "ts": time.time(),
    })

    # Atomic write pattern: temp + os.replace
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, dir=LEDGER_DIR, suffix=".json"
    ) as tmp:
        json.dump(data, tmp)
        tmp_path = tmp.name

    os.replace(tmp_path, p)


def load(session_id: str) -> dict:
    """Load ledger for session, filtering out expired entries.

    Returns:
        Dict with "entries" key containing list of non-expired records.
    """
    p = _path(session_id)
    if not p.exists():
        return {"entries": []}

    try:
        data = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return {"entries": []}

    # Filter: keep only entries younger than TTL
    now = time.time()
    data["entries"] = [
        e
        for e in data.get("entries", [])
        if now - e.get("ts", 0) < TTL_SECONDS
    ]
    return data


def find_matches(session_id: str, query: str) -> list[dict]:
    """Find ledger entries matching the query string.

    Args:
        session_id: Current session ID
        query: Search query (will lowercase; minimum 3 chars for meaningful match)

    Returns:
        List of matching entries (keyword in query or vice versa).
    """
    q = (query or "").lower()
    if len(q) < MIN_KEYWORD_LEN:
        return []

    entries = load(session_id)["entries"]
    return [
        e
        for e in entries
        if e["keyword"] in q or q in e["keyword"]
    ]
