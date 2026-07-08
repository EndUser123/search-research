"""Extract golden cases from real session transcripts for CHS retrieval eval.

Reads session transcripts from ~/.claude/projects/P--/ and produces
golden_cases.jsonl with queries, expected session keys, and content hashes.

Usage:
    python -m core.chs.eval.generate_golden_cases [--sessions N]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

PROJECT_DIR = Path.home() / ".claude" / "projects" / "P--"
OUTPUT = Path(__file__).parent / "golden_cases.jsonl"
MAX_USER_LEN = 300
MAX_CONTENT_HASH_LEN = 500
CASE_COUNT = 50
MIN_QUERY_LEN = 15

_SKIP_PATTERNS = re.compile(
    r"(yes|no|ok|thanks|done|nope|yep|sure|please|ty|got it|"
    r"restarted claude code|accepted|"
    r"local-command-caveat|"
    r"This session is being continued|"
    r"I won't rememmber|"
    r"system-reminder|"
    r"command-message|"
    r"command-name|"
    r"command-args|"
    r"task-notification|"
    r"Caveat: The messages|"
    r"COMMITMENT CHECK|"
    r"TEST STRATEGY|"
    r"EVIDENCE-FIRST|"
    r"Task Tracker|"
    r"PostToolUse:|"
    r"hook additional context:"
    r")",
    re.IGNORECASE,
)
# Path-like content (backslashes or forward slashes with filenames)
_PATH_LIKE = re.compile(r"[/\\][\w.]+[/\\]")
# Command invocation pattern: word:word (like plugin:command)
_CMD_INVOCATION = re.compile(r"^\s*[\w-]+:[\w-]+")
# Strip XML-like tags from queries to get clean FTS-friendly text
_TAG_STRIP = re.compile(r"<[^>]+>")
_MULTIPLE_SPACE = re.compile(r"\s{2,}")


def _strip_tags(text: str) -> str:
    """Strip XML-like tags and collapse whitespace for FTS-friendly queries."""
    return _MULTIPLE_SPACE.sub(" ", _TAG_STRIP.sub("", text)).strip()


def _content_sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _extract_text(content_blocks: list) -> str:
    parts = []
    for block in content_blocks or []:
        if not isinstance(block, dict):
            continue
        t = block.get("type")
        if t == "text":
            parts.append(block.get("text", ""))
        elif t == "thinking":
            parts.append(block.get("thinking", ""))
    return " ".join(parts)


def extract_user_queries(transcript_path: Path
                         ) -> list[tuple[str, str, str]]:
    """Return (session_id, query_text, response_text)."""
    session_id = transcript_path.stem
    entries: list[dict] = []
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))

    results: list[tuple[str, str, str]] = []
    user_texts: list[str] = []
    for entry in entries:
        t = entry.get("type")
        if t == "user":
            msg = entry.get("message", {})
            if isinstance(msg, dict):
                text = msg.get("content", "")
                if isinstance(text, str) and text.strip():
                    user_texts.append(text.strip())
        elif t == "assistant":
            if user_texts:
                query = user_texts.pop(0)
                # Strip tags first, then check skip patterns on clean text
                clean = _strip_tags(query)
                if not clean or len(clean) < MIN_QUERY_LEN:
                    user_texts.clear()
                    continue
                # Skip system-injected content, command invocations, file paths
                if (_SKIP_PATTERNS.search(clean) or _CMD_INVOCATION.match(clean)
                        or _PATH_LIKE.search(clean)):
                    user_texts.clear()
                    continue
                msg = entry.get("message", {})
                if isinstance(msg, dict):
                    blocks = msg.get("content", [])
                    resp_text = _extract_text(blocks)
                    if resp_text.strip():
                        results.append((session_id, clean, resp_text))
            user_texts.clear()
    return results


def _valid_session_keys(db_path: str | None) -> set[str] | None:
    """Load session_keys from DB that have at least one message.

    Returns None when db_path is None (no filtering).
    """
    if not db_path:
        return None
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    conn.execute("PRAGMA query_only=ON;")
    keys = {row[0] for row in conn.execute(
        "SELECT s.session_key FROM sessions s "
        "INNER JOIN messages m ON m.session_id = s.id "
        "GROUP BY s.id HAVING COUNT(m.id) > 0"
    )}
    conn.close()
    return keys


def _cases_from_db(db_path: str, limit: int) -> list[dict]:
    """Generate golden cases directly from DB sessions with messages.

    Uses first_prompt as the query (it's the first user message, which is
    what FTS indexes and searches against).
    """
    import sqlite3 as _sqlite3
    conn = _sqlite3.connect(db_path)
    conn.execute("PRAGMA query_only=ON;")
    rows = conn.execute("""
        SELECT s.session_key, s.first_prompt
        FROM sessions s
        INNER JOIN messages m ON m.session_id = s.id
        WHERE s.first_prompt IS NOT NULL AND LENGTH(s.first_prompt) >= ?
        GROUP BY s.id HAVING COUNT(m.id) > 0
        ORDER BY COUNT(m.id) DESC
    """, (MIN_QUERY_LEN,)).fetchall()
    conn.close()

    cases: list[dict] = []
    for i, (session_key, first_prompt) in enumerate(rows[:limit]):
        clean = _strip_tags(first_prompt[:MAX_USER_LEN]).rstrip()
        if not clean or len(clean) < MIN_QUERY_LEN:
            continue
        if (_SKIP_PATTERNS.search(clean) or _CMD_INVOCATION.match(clean)
                or _PATH_LIKE.search(clean)):
            continue
        cases.append({
            "id": f"case-{len(cases) + 1:03d}",
            "query": clean,
            "required_session_keys": [session_key],
            "k": 10,
            "notes": f"session {session_key[:8]}…",
        })
    return cases


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHS golden cases")
    parser.add_argument("--sessions", type=int, default=15,
                        help="Number of session transcripts to scan")
    parser.add_argument("--db", default=None,
                        help="CHS database path; filter to session_keys that exist in it")
    args = parser.parse_args()

    if not PROJECT_DIR.is_dir():
        print(f"Session directory not found: {PROJECT_DIR}", file=sys.stderr)
        return 1

    valid_keys = _valid_session_keys(args.db)

    # When --db is provided, generate cases directly from the DB
    # (transcript UUIDs may not match DB session_keys)
    if args.db:
        cases = _cases_from_db(args.db, CASE_COUNT)
        if not cases:
            print("No golden cases extracted from DB.", file=sys.stderr)
            return 1
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT, "w", encoding="utf-8") as f:
            for case in cases:
                f.write(json.dumps(case, ensure_ascii=False) + "\n")
        print(f"Wrote {len(cases)} golden cases from DB")
        return 0

    transcripts = sorted(
        [p for p in PROJECT_DIR.iterdir() if p.suffix == ".jsonl" and p.is_file()],
        key=lambda p: p.stat().st_size, reverse=True,
    )
    if valid_keys is not None:
        transcripts = [p for p in transcripts if p.stem in valid_keys]
    transcripts = transcripts[:args.sessions]

    # Extract all query pairs from all sessions
    session_pairs: dict[str, list[tuple[str, str, str]]] = {}
    for tp in transcripts:
        pairs = extract_user_queries(tp)
        if pairs:
            session_pairs[tp.stem] = pairs

    if not session_pairs:
        print("No golden cases extracted.", file=sys.stderr)
        return 1

    # Round-robin across sessions for diversity
    cases: list[dict] = []
    case_id = 0
    iters = {sid: iter(pairs) for sid, pairs in session_pairs.items()}
    session_order = list(iters.keys())
    exhausted = set()

    while case_id < CASE_COUNT and len(exhausted) < len(session_order):
        for sid in session_order:
            if sid in exhausted:
                continue
            try:
                _, query, resp_text = next(iters[sid])
            except StopIteration:
                exhausted.add(sid)
                continue

            short_query = _strip_tags(query[:MAX_USER_LEN]).rstrip()
            # Pin session_key ONLY. The --golden-cases gate runs in
            # semantic-sessions mode, where retrieved "content" is the session
            # summary — a hash of the assistant response (let alone a truncated
            # one) can never match, and an unmatchable required key caps every
            # case at recall < 1.0, making the gate permanently red.
            cases.append({
                "id": f"case-{case_id + 1:03d}",
                "query": short_query,
                "required_session_keys": [sid],
                "k": 10,
                "notes": f"session {sid[:8]}…",
            })
            case_id += 1
            if case_id >= CASE_COUNT:
                break

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Wrote {len(cases)} golden cases from {len(session_pairs)} sessions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
