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
import sys
from pathlib import Path

PROJECT_DIR = Path.home() / ".claude" / "projects" / "P--"
OUTPUT = Path(__file__).parent / "golden_cases.jsonl"
MAX_USER_LEN = 300  # cap query text to keep cases readable
MAX_CONTENT_HASH_LEN = 500  # chars to sha256 for response content
CASE_COUNT = 50


def _content_sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _extract_text(content_blocks: list) -> str:
    """Extract text from assistant content blocks."""
    parts = []
    for block in content_blocks or []:
        if not isinstance(block, dict):
            continue
        t = block.get("type")
        if t == "text":
            parts.append(block.get("text", ""))
        elif t == "thinking":
            parts.append(block.get("thinking", ""))
        elif t == "tool_use":
            parts.append(f"[Tool: {block.get('name', '')}]")
    return " ".join(parts)


def extract_user_queries(transcript_path: Path
                         ) -> list[tuple[str, str, str, str]]:
    """Return (session_id, query_text, response_text, response_msg_id)."""
    session_id = transcript_path.stem  # filename without .jsonl
    entries: list[dict] = []
    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))

    results: list[tuple[str, str, str, str]] = []
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
                msg = entry.get("message", {})
                if isinstance(msg, dict):
                    blocks = msg.get("content", [])
                    resp_text = _extract_text(blocks)
                    msg_id = msg.get("id", "")
                    if resp_text.strip() and query:
                        results.append((session_id, query, resp_text, msg_id))
            user_texts.clear()  # consume all pending user texts
        else:
            continue
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CHS golden cases")
    parser.add_argument("--sessions", type=int, default=10,
                        help="Number of session transcripts to scan")
    args = parser.parse_args()

    if not PROJECT_DIR.is_dir():
        print(f"Session directory not found: {PROJECT_DIR}", file=sys.stderr)
        return 1

    # Collect the N largest transcripts (most content → most queries)
    transcripts = sorted(
        [p for p in PROJECT_DIR.iterdir() if p.suffix == ".jsonl" and p.is_file()],
        key=lambda p: p.stat().st_size, reverse=True,
    )[:args.sessions]

    cases: list[dict] = []
    case_id = 0

    for tp in transcripts:
        pairs = extract_user_queries(tp)
        for session_id, query, resp_text, msg_id in pairs:
            if case_id >= CASE_COUNT:
                break
            # Truncate query for readability
            short_query = query[:MAX_USER_LEN].rstrip()

            # Content hash of response start (stable across DB rebuilds)
            resp_hash = _content_sha(resp_text[:MAX_CONTENT_HASH_LEN])

            case = {
                "id": f"case-{case_id + 1:03d}",
                "query": short_query,
                "required_session_keys": [session_id],
                "required_content_sha256": [resp_hash],
                "k": 10,
                "notes": f"session {session_id[:8]}…",
            }
            cases.append(case)
            case_id += 1
        if case_id >= CASE_COUNT:
            break

    if not cases:
        print("No golden cases extracted.", file=sys.stderr)
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Wrote {len(cases)} golden cases to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
