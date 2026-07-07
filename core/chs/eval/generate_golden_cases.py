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
    r"^\s*(yes|no|ok|thanks|done|nope|yep|sure|please|ty|got it|"
    r"restarted claude code|accepted|"
    r"<local-command-caveat>|"
    r"This session is being continued|"
    r"I won't rememmber|"
    r"<system-reminder>|"
    r"<command-message>.*</command-message>\s*$"
    r")\s*$",
    re.IGNORECASE,
)


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
                if _SKIP_PATTERNS.match(query):
                    user_texts.clear()
                    continue
                msg = entry.get("message", {})
                if isinstance(msg, dict):
                    blocks = msg.get("content", [])
                    resp_text = _extract_text(blocks)
                    if resp_text.strip() and len(query) >= MIN_QUERY_LEN:
                        results.append((session_id, query, resp_text))
            user_texts.clear()
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHS golden cases")
    parser.add_argument("--sessions", type=int, default=15,
                        help="Number of session transcripts to scan")
    args = parser.parse_args()

    if not PROJECT_DIR.is_dir():
        print(f"Session directory not found: {PROJECT_DIR}", file=sys.stderr)
        return 1

    transcripts = sorted(
        [p for p in PROJECT_DIR.iterdir() if p.suffix == ".jsonl" and p.is_file()],
        key=lambda p: p.stat().st_size, reverse=True,
    )[:args.sessions]

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

            short_query = query[:MAX_USER_LEN].rstrip()
            resp_hash = _content_sha(resp_text[:MAX_CONTENT_HASH_LEN])
            cases.append({
                "id": f"case-{case_id + 1:03d}",
                "query": short_query,
                "required_session_keys": [sid],
                "required_content_sha256": [resp_hash],
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
