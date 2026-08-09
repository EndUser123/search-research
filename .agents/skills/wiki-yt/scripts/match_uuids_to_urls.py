#!/usr/bin/env python3
"""match_uuids_to_urls.py — Hop 4: match NotebookLM source UUIDs to original URLs.

NotebookLM's `nlm source list` returns `url: null` for YouTube sources — only
the title is preserved. To close the 4-hop provenance chain (concept → notebook
→ cluster → original URL), we match UUIDs to URLs via title.

Strategy:
  1. Load cluster's videos from clusters.json (each has title + url).
2. Load notebook's sources through the canonical YTIS direct client (each has
   id + title).
  3. Build a title → URL index from clusters.json.
  4. For each source UUID, look up by exact title match; fall back to fuzzy.

Usage:
  python match_uuids_to_urls.py --notebook <uuid> --cluster-id <id> \\
      --clusters-json clusters.json --account-profile a.hominidae
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

from ytis_nlm import ensure_account_session, list_sources as list_canonical_sources


def run(cmd: list[str], timeout: int = 120) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


def normalize_title(t: str) -> str:
    """Aggressive normalization: lowercase, strip punctuation, collapse whitespace.

    Preserves Unicode letters/digits (Cyrillic, CJK, accents) so non-English
    titles can still match.
    """
    import re
    import unicodedata
    t = (t or "").lower().strip()
    # Keep Unicode word chars + spaces; strip punctuation
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_url_if_urllike(text: str) -> str | None:
    """If the text IS a URL, return it; else None."""
    text = (text or "").strip()
    if text.startswith(("http://", "https://", "www.")):
        return text
    return None


def list_sources(notebook_id: str, profile: str) -> list[dict]:
    try:
        return list_canonical_sources(profile, notebook_id, worker_id="wiki-yt-match")
    except Exception as exc:
        raise RuntimeError(
            f"canonical source list failed for notebook {notebook_id}: "
            f"{type(exc).__name__}: {str(exc)[:300]}"
        ) from exc


def build_title_index(clusters: list[dict], cluster_id: int) -> dict[str, dict]:
    """Build {normalized_title: video_record} AND {url: video_record} for the cluster."""
    cluster = next((c for c in clusters if c["cluster_id"] == cluster_id), None)
    if not cluster:
        return {}
    title_index = {}
    url_index = {}
    for v in cluster.get("videos", []):
        norm = normalize_title(v.get("title", ""))
        if norm:
            title_index[norm] = v
        url = (v.get("url") or "").strip()
        if url:
            url_index[url] = v
    return {"title": title_index, "url": url_index}


def match_with_fallback(source_title: str, source_id: str, indices: dict,
                         threshold: float = 0.85) -> dict | None:
    """Try URL match, then title exact, then fuzzy title.

    Indices is the dict returned by build_title_index: {"title": {...}, "url": {...}}.
    """
    title_index = indices.get("title", {})
    url_index = indices.get("url", {})

    # 1. If the source title IS a URL (NotebookLM sometimes shows the raw URL),
    #    match directly.
    url = extract_url_if_urllike(source_title)
    if url and url in url_index:
        return {**url_index[url], "_match_type": "url_exact"}

    # 2. Exact title match
    norm = normalize_title(source_title)
    if not norm:
        return None
    if norm in title_index:
        return {**title_index[norm], "_match_type": "exact"}

    # 3. Fuzzy title
    best_score = 0.0
    best_match = None
    for key, rec in title_index.items():
        score = SequenceMatcher(None, norm, key).ratio()
        if score > best_score:
            best_score = score
            best_match = rec
    if best_score >= threshold:
        return {**best_match, "_match_score": best_score, "_match_type": "fuzzy"}
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--notebook", required=True)
    ap.add_argument("--cluster-id", type=int, required=True)
    ap.add_argument("--clusters-json", type=Path, required=True)
    ap.add_argument("--profile", "--account-profile", dest="profile", default="a.hominidae",
                    help="exact account identity (a.hominidae, troup.hominidae, or brsthomson)")
    ap.add_argument("--threshold", type=float, default=0.85,
                    help="Fuzzy-match threshold (0-1); below this, UUID is unmatched")
    ap.add_argument("-o", "--output", type=Path, help="Output JSON (default: stdout)")
    args = ap.parse_args()

    clusters = json.loads(args.clusters_json.read_text(encoding="utf-8"))
    index = build_title_index(clusters, args.cluster_id)
    if not index or not index.get("title"):
        print(f"FATAL: cluster {args.cluster_id} not found or has no videos", file=sys.stderr)
        return 2
    print(f"Index: {len(index['title'])} videos, {len(index.get('url', {}))} URLs in cluster {args.cluster_id}", file=sys.stderr)

    try:
        probe = ensure_account_session(args.profile, worker_id="wiki-yt-match-preflight")
        if not probe.ok:
            print(f"FATAL: canonical auth unavailable: {probe.reason}", file=sys.stderr)
            return 2
        sources = list_sources(args.notebook, args.profile)
    except RuntimeError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        return 2
    print(f"Sources: {len(sources)} in notebook {args.notebook}", file=sys.stderr)

    matches = []
    exact = url_exact = fuzzy = unmatched = 0
    for s in sources:
        sid = s.get("id")
        stitle = s.get("title", "")
        match = match_with_fallback(stitle, sid, index, args.threshold)
        if match is None:
            unmatched += 1
            matches.append({"source_id": sid, "source_title": stitle,
                             "matched_url": None, "match_type": "unmatched"})
        else:
            mtype = match.get("_match_type", "unknown")
            matches.append({"source_id": sid, "source_title": stitle,
                             "matched_url": match.get("url"),
                             "matched_title": match.get("title"),
                             "match_score": match.get("_match_score", 1.0) if mtype == "fuzzy" else 1.0,
                             "match_type": mtype})
            if mtype == "exact":
                exact += 1
            elif mtype == "url_exact":
                url_exact += 1
            elif mtype == "fuzzy":
                fuzzy += 1

    result = {
        "notebook_id": args.notebook,
        "cluster_id": args.cluster_id,
        "total_sources": len(sources),
        "matches": {
            "exact": exact,
            "url_exact": url_exact,
            "fuzzy": fuzzy,
            "unmatched": unmatched,
            "match_rate": (exact + url_exact + fuzzy) / len(sources) if sources else 0,
        },
        "mappings": matches,
    }

    out_text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out_text, encoding="utf-8")
        print(f"Output: {args.output}", file=sys.stderr)
    else:
        print(out_text)

    print(f"\nMatches: {exact} exact, {url_exact} url_exact, {fuzzy} fuzzy, "
          f"{unmatched} unmatched ({result['matches']['match_rate']:.1%})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
