"""Golden-case retrieval evaluation for CHS.

Measures recall@k of CHS retrieval against pinned expected results. Run it
before AND after any re-embed, re-index, chunking change, or embedding-model
swap; cut over only when recall holds.

Golden case format (JSONL, one object per line):
    {
      "id": "case-001",
      "query": "atomic json write pattern",
      "required_message_ids": ["msg-abc123"],       # v2 messages.message_id
      "required_content_sha256": ["<64-hex>"],      # alternative stable key
      "k": 10,                                       # optional, default 10
      "notes": "why this case exists"                # optional
    }
At least one of required_message_ids / required_content_sha256 must be
non-empty. Both are stable across rebuilds, unlike numeric row IDs.

Usage:
    python -m core.chs.eval.retrieval_eval --db <path> [--cases <path>]
        [--min-recall 0.8] [--mode fts]

Exit code 1 when mean recall falls below --min-recall (CI-friendly).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

DEFAULT_CASES = Path(__file__).parent / "golden_cases.jsonl"
DEFAULT_K = 10

# search_fn(conn, query, limit) -> list of dicts with at least "id" and "content"
SearchFn = Callable[[sqlite3.Connection, str, int], list]


@dataclass
class GoldenCase:
    id: str
    query: str
    required_message_ids: set = field(default_factory=set)
    required_content_sha256: set = field(default_factory=set)
    required_session_keys: set = field(default_factory=set)
    k: int = DEFAULT_K
    notes: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "GoldenCase":
        case = cls(
            id=d["id"],
            query=d["query"],
            required_message_ids=set(d.get("required_message_ids", [])),
            required_content_sha256=set(d.get("required_content_sha256", [])),
            required_session_keys=set(d.get("required_session_keys", [])),
            k=int(d.get("k", DEFAULT_K)),
            notes=d.get("notes", ""),
        )
        if not (case.required_message_ids or case.required_content_sha256
                or case.required_session_keys):
            raise ValueError(
                f"Golden case {case.id!r} pins no required results: set "
                "required_message_ids, required_content_sha256, and/or "
                "required_session_keys"
            )
        return case


@dataclass
class CaseResult:
    case_id: str
    recall: float
    found: int
    required: int
    missing: list


def load_cases(path: Path) -> list[GoldenCase]:
    cases = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            cases.append(GoldenCase.from_dict(json.loads(line)))
    if not cases:
        raise ValueError(f"No golden cases found in {path}")
    return cases


def _content_sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _stable_keys_for_results(
    conn: sqlite3.Connection, results: list
) -> tuple[set, set, set]:
    """Map search results to stable keys: (message_ids, content_hashes, session_keys)."""
    message_ids: set = set()
    content_hashes: set = set()
    session_keys: set = set()
    row_ids = [r["id"] for r in results if r.get("id") is not None]
    if row_ids:
        try:
            placeholders = ",".join("?" for _ in row_ids)
            cursor = conn.execute(
                f"SELECT id, message_id FROM messages WHERE id IN ({placeholders})",
                row_ids,
            )
            message_ids = {row[1] for row in cursor.fetchall() if row[1]}
        except sqlite3.OperationalError:
            pass  # legacy schema without messages.message_id
    session_row_ids = [r["session_id"] for r in results if r.get("session_id") is not None]
    if session_row_ids:
        try:
            placeholders = ",".join("?" for _ in session_row_ids)
            cursor = conn.execute(
                f"SELECT id, session_key FROM sessions WHERE id IN ({placeholders})",
                session_row_ids,
            )
            session_keys = {row[1] for row in cursor.fetchall() if row[1]}
        except sqlite3.OperationalError:
            pass  # legacy schema without sessions.session_key
    for r in results:
        content_hashes.add(_content_sha(r.get("content", "")))
    return message_ids, content_hashes, session_keys


def evaluate(
    conn: sqlite3.Connection, cases: list[GoldenCase], search_fn: SearchFn
) -> list[CaseResult]:
    """Run all golden cases; recall = |required ∩ retrieved-top-k| / |required|."""
    results = []
    for case in cases:
        retrieved = search_fn(conn, case.query, case.k)
        found_ids, found_hashes, found_session_keys = _stable_keys_for_results(conn, retrieved)

        required_total = (len(case.required_message_ids)
                          + len(case.required_content_sha256)
                          + len(case.required_session_keys))
        hit_ids = case.required_message_ids & found_ids
        hit_hashes = case.required_content_sha256 & found_hashes
        hit_sessions = case.required_session_keys & found_session_keys
        found_count = len(hit_ids) + len(hit_hashes) + len(hit_sessions)
        missing = sorted(
            (case.required_message_ids - hit_ids)
            | (case.required_session_keys - hit_sessions)
            | {h[:12] + "…" for h in (case.required_content_sha256 - hit_hashes)}
        )
        results.append(
            CaseResult(
                case_id=case.id,
                recall=found_count / required_total if required_total else 0.0,
                found=found_count,
                required=required_total,
                missing=missing,
            )
        )
    return results


def _default_fts_search(conn: sqlite3.Connection, query: str, limit: int) -> list:
    """Production FTS path (lazy import: search module pulls numpy)."""
    from ..search import search_fts_messages

    return search_fts_messages(conn, query, limit)


def make_semantic_sessions_search(
    embed_client, threshold: float = 0.0, expected_model: str | None = None
) -> SearchFn:
    """Build a semantic search_fn over sessions.embedding.

    This is the mode that actually validates a re-embed: FTS recall is
    lexical and does not change when vectors change. Threshold defaults to
    0.0 so recall@k is measured on ranking, not on a similarity cutoff
    calibrated to the previous model. Pass expected_model to exclude rows
    from other models (mixed-state protection).
    """

    def _search(conn: sqlite3.Connection, query: str, limit: int) -> list:
        from ..search import search_semantic_sessions

        results = search_semantic_sessions(
            conn, query, embed_client, limit=limit, threshold=threshold,
            expected_model=expected_model,
        )
        # Normalize: harness maps session_id -> sessions.session_key
        return [
            {"id": None, "session_id": r["session_id"],
             "content": r.get("summary_short") or r.get("first_prompt") or "",
             "score": r["score"]}
            for r in results
        ]

    return _search


def report(results: list[CaseResult]) -> float:
    """Print per-case and aggregate recall; returns mean recall."""
    print(f"{'case':<24} {'recall':>7} {'found':>6} {'req':>4}  missing")
    for r in sorted(results, key=lambda x: x.recall):
        marker = "PASS" if r.recall == 1.0 else "MISS"
        missing = ", ".join(r.missing[:3]) if r.missing else "-"
        print(f"{r.case_id:<24} {r.recall:>7.3f} {r.found:>6} {r.required:>4}  [{marker}] {missing}")
    mean = sum(r.recall for r in results) / len(results)
    perfect = sum(1 for r in results if r.recall == 1.0)
    print(f"\nCases: {len(results)}  perfect: {perfect}  mean recall: {mean:.3f}")
    return mean


def main() -> None:
    parser = argparse.ArgumentParser(description="CHS golden-case retrieval eval")
    parser.add_argument("--db", required=True, help="Path to CHS database")
    parser.add_argument("--cases", default=str(DEFAULT_CASES), help="Golden cases JSONL")
    parser.add_argument("--min-recall", type=float, default=0.8,
                        help="Fail (exit 1) below this mean recall")
    parser.add_argument("--mode", choices=["fts"], default="fts",
                        help="Retrieval mode under test (semantic: run via re-embed drill)")
    args = parser.parse_args()

    cases = load_cases(Path(args.cases))
    conn = sqlite3.connect(args.db)
    try:
        results = evaluate(conn, cases, _default_fts_search)
    finally:
        conn.close()
    mean = report(results)
    if mean < args.min_recall:
        print(f"FAIL: mean recall {mean:.3f} < threshold {args.min_recall}")
        sys.exit(1)
    print(f"OK: mean recall {mean:.3f} >= threshold {args.min_recall}")


if __name__ == "__main__":
    main()
