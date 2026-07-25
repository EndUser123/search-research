#!/usr/bin/env python3
"""expand_citations.py — Stage D: expand cited_text snippets via SourceFulltext.

NotebookLM query/report responses cite short snippets that are often section
headers or fragments. The nlm-skill SKILL.md warns: use SourceFulltext
.find_citation_context() to locate the real passage.

This script takes reconciled concepts JSON and enriches each citation with
the surrounding paragraph from the source fulltext (when available).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def get_source_fulltext(notebook_id: str, source_id: str, profile: str) -> str | None:
    """Return the indexed text of a source, or None on failure."""
    if not source_id or source_id == "(from data-table)":
        return None
    try:
        r = subprocess.run(
            ["nlm", "source", "fulltext", source_id, "--notebook", notebook_id,
             "--profile", profile, "--json"],
            capture_output=True, text=True, timeout=120, encoding="utf-8")
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout)
        return data.get("content") or None
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def find_context(fulltext: str, snippet: str, window: int = 600) -> str:
    """Return window chars around the first occurrence of snippet, or empty."""
    if not fulltext or not snippet:
        return ""
    # Strip citation wrapper chars
    clean = snippet.strip().strip("[]().,;:\"'")
    if len(clean) < 5:
        return ""
    idx = fulltext.find(clean)
    if idx < 0:
        # Try a shorter prefix
        idx = fulltext.find(clean[:40])
    if idx < 0:
        return ""
    start = max(0, idx - window // 2)
    end = min(len(fulltext), idx + len(clean) + window // 2)
    return fulltext[start:end].strip()


def enrich(concepts: list[dict], notebook_id: str, profile: str,
           cache: dict[str, str]) -> list[dict]:
    for c in concepts:
        for cit in c.get("citations", []):
            sid = cit.get("source_id", "")
            if not sid or sid == "(from data-table)":
                continue
            if sid not in cache:
                cache[sid] = get_source_fulltext(notebook_id, sid, profile) or ""
            ft = cache.get(sid, "")
            snippet = cit.get("cited_text") or cit.get("claim", "")
            ctx = find_context(ft, snippet)
            if ctx:
                cit["expanded_context"] = ctx
    return concepts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--notebook", required=True)
    ap.add_argument("--profile", default="codex")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    concepts = json.loads(args.input.read_text(encoding="utf-8"))
    cache: dict[str, str] = {}
    enriched = enrich(concepts, args.notebook, args.profile, cache)

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"Enriched {len(enriched)} concepts (cache: {len(cache)} sources fetched)",
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
