#!/usr/bin/env python3
"""reconcile.py — Stage C: dedup candidate concepts against the wiki vault.

For each candidate, qmd-search the vault; if similarity ≥ threshold, mark as
`refines <existing-slug>`; else mark as new.

Reads concepts JSON from stdin (or --input), writes reconciled JSON to stdout.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def qmd_search(query: str, top_k: int = 5) -> list[dict]:
    """Run qmd search, return parsed results (or empty on failure)."""
    try:
        r = subprocess.run(
            ["qmd", "search", "--collection", "wiki", "--query", query, "--top-k", str(top_k)],
            capture_output=True, text=True, timeout=60, encoding="utf-8")
        if r.returncode != 0:
            return []
        # qmd emits an INFO log line first; find the JSON
        out = r.stdout.strip()
        # Strip leading non-JSON lines
        idx = out.find("[")
        if idx < 0:
            return []
        return json.loads(out[idx:])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return []


def best_match(query: str, threshold: float) -> tuple[str | None, float]:
    """Return (doc_id, score) of best match above threshold, else (None, 0)."""
    results = qmd_search(query, top_k=5)
    for r in results:
        score = r.get("score") or 0
        doc_id = r.get("chunk_ref", {}).get("document_id")
        if not doc_id:
            continue
        # qmd scores are similarity-like; treat directly
        if score >= threshold:
            return doc_id, score
    return None, 0.0


def reconcile(concepts: list[dict], threshold: float) -> list[dict]:
    for c in concepts:
        # Query with title + definition (truncated)
        query = c["title"]
        if c.get("definition"):
            query += " " + c["definition"][:200]
        match_id, score = best_match(query, threshold)
        if match_id:
            c["disposition"] = "refines"
            c["refines_target"] = match_id
            c["match_score"] = score
        else:
            c["disposition"] = "new"
            c["refines_target"] = None
            c["match_score"] = score
    return concepts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, help="concepts JSON (default: stdin)")
    ap.add_argument("--threshold", type=float, default=0.75,
                    help="qmd similarity threshold for refines (default 0.75)")
    args = ap.parse_args()

    if args.input:
        concepts = json.loads(args.input.read_text(encoding="utf-8"))
    else:
        concepts = json.load(sys.stdin)

    reconciled = reconcile(concepts, args.threshold)
    json.dump(reconciled, sys.stdout, ensure_ascii=False, indent=2)

    n_new = sum(1 for c in reconciled if c["disposition"] == "new")
    n_refine = sum(1 for c in reconciled if c["disposition"] == "refines")
    print(f"\nReconciled: {n_new} new, {n_refine} refines", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
