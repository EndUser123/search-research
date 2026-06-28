#!/usr/bin/env python3
"""
Persistent-search MCP server.

Design goals (matching the harness's enforcement style):
  - Search results are ARTIFACTS, not ephemeral model context. The model never
    holds the only copy.
  - Every call writes a provenance-tagged JSON artifact + a SQLite ledger row
    BEFORE returning to the model.
  - Model-agnostic: any model routed by CCR (GLM, DeepSeek, MiniMax, local MiMo)
    calls the same `web_search` tool and gets identical behavior. No native
    search capability required from the model.
  - Dedup + reuse: identical queries return the cached artifact instead of
    re-fetching, so a later session reads prior evidence rather than re-searching.
  - Downstream gates can verify "did the model's claim trace to a captured
    source?" against the provenance fields (url, fetched_at, retrieval rank).

Provider: Tavily by default (clean, extraction-ready content for direct storage).
Swap PROVIDER + the fetch fn to use Exa or Brave.

Transport: stdio MCP. Register in Claude Code's mcp config (see README).
"""

import os
import sys
import json
import time
import hashlib
import sqlite3
import datetime
import urllib.request
import urllib.error
from pathlib import Path

# ---- config ---------------------------------------------------------------
HARNESS_ROOT = Path(os.environ.get("HARNESS_ROOT", Path.home() / ".harness"))
SEARCH_DIR = HARNESS_ROOT / "searches"
LEDGER_DB = HARNESS_ROOT / "search_ledger.sqlite"
PROVIDER = os.environ.get("SEARCH_PROVIDER", "tavily")  # tavily | exa | brave
TAVILY_KEY = os.environ.get("TAVILY_API_KEY", "")
REUSE_MAX_AGE_S = int(os.environ.get("SEARCH_REUSE_MAX_AGE_S", "86400"))  # 24h

SEARCH_DIR.mkdir(parents=True, exist_ok=True)


# ---- ledger ---------------------------------------------------------------
def _db():
    con = sqlite3.connect(LEDGER_DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS searches (
            query_hash   TEXT PRIMARY KEY,
            query        TEXT NOT NULL,
            artifact     TEXT NOT NULL,
            provider     TEXT NOT NULL,
            n_results    INTEGER NOT NULL,
            fetched_at   TEXT NOT NULL,
            fetched_ts   REAL NOT NULL
        )
    """)
    return con


def _query_hash(q: str) -> str:
    return hashlib.sha256(q.strip().lower().encode()).hexdigest()[:16]


def _lookup(qh: str):
    con = _db()
    row = con.execute(
        "SELECT query, artifact, provider, n_results, fetched_at, fetched_ts "
        "FROM searches WHERE query_hash = ?", (qh,)
    ).fetchone()
    con.close()
    if not row:
        return None
    if time.time() - row[5] > REUSE_MAX_AGE_S:
        return None  # too stale, force refetch
    return row


def _record(qh, query, artifact_path, provider, n_results, fetched_at, fetched_ts):
    con = _db()
    con.execute(
        "INSERT OR REPLACE INTO searches "
        "(query_hash, query, artifact, provider, n_results, fetched_at, fetched_ts) "
        "VALUES (?,?,?,?,?,?,?)",
        (qh, query, str(artifact_path), provider, n_results, fetched_at, fetched_ts),
    )
    con.commit()
    con.close()


# ---- provider fetch -------------------------------------------------------
def _fetch_tavily(query: str, max_results: int):
    if not TAVILY_KEY:
        raise RuntimeError("TAVILY_API_KEY not set")
    body = json.dumps({
        "api_key": TAVILY_KEY,
        "query": query,
        "max_results": max_results,
        "include_raw_content": True,
        "search_depth": "advanced",
    }).encode()
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    results = []
    for i, item in enumerate(data.get("results", [])):
        results.append({
            "rank": i,
            "url": item.get("url"),
            "title": item.get("title"),
            "content": item.get("content"),
            "raw_content": item.get("raw_content"),
            "score": item.get("score"),
        })
    return results


def _fetch(query: str, max_results: int):
    if PROVIDER == "tavily":
        return _fetch_tavily(query, max_results)
    raise RuntimeError(f"provider {PROVIDER} not implemented; add a fetch fn")


# ---- core: search-with-persistence ---------------------------------------
def do_search(query: str, max_results: int = 5, force: bool = False):
    """Returns a dict with results AND the artifact path. Writes artifact+ledger."""
    qh = _query_hash(query)

    if not force:
        cached = _lookup(qh)
        if cached:
            artifact = Path(cached[1])
            if artifact.exists():
                payload = json.loads(artifact.read_text())
                payload["_cache"] = "reused"
                return payload

    results = _fetch(query, max_results)
    now = datetime.datetime.now(datetime.timezone.utc)
    fetched_at = now.isoformat()
    fetched_ts = now.timestamp()

    # provenance-tagged artifact. Each result carries url + rank + fetched_at
    # so a downstream gate can verify a model claim traces to a captured source.
    payload = {
        "query": query,
        "query_hash": qh,
        "provider": PROVIDER,
        "fetched_at": fetched_at,
        "n_results": len(results),
        "results": [
            {**r, "fetched_at": fetched_at, "provenance_id": f"{qh}:{r['rank']}"}
            for r in results
        ],
        "_cache": "fresh",
    }

    artifact_path = SEARCH_DIR / f"{now.strftime('%Y%m%dT%H%M%S')}_{qh}.json"
    artifact_path.write_text(json.dumps(payload, indent=2))
    _record(qh, query, artifact_path, PROVIDER, len(results), fetched_at, fetched_ts)
    payload["artifact"] = str(artifact_path)
    return payload


# ---- MCP stdio loop -------------------------------------------------------
TOOLS = [{
    "name": "web_search",
    "description": (
        "Search the web. Results are persisted as a provenance-tagged artifact "
        "and logged to the search ledger before being returned. Identical recent "
        "queries are served from cache. Use this whenever you need current "
        "information; the evidence is captured automatically."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "default": 5, "minimum": 1, "maximum": 10},
            "force": {"type": "boolean", "default": False,
                      "description": "Bypass cache and re-fetch"},
        },
        "required": ["query"],
    },
}]


def _send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        mid = msg.get("id")
        method = msg.get("method")

        if method == "initialize":
            _send({"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "persistent-search", "version": "1.0.0"},
            }})
        elif method == "tools/list":
            _send({"jsonrpc": "2.0", "id": mid, "result": {"tools": TOOLS}})
        elif method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            if name != "web_search":
                _send({"jsonrpc": "2.0", "id": mid,
                       "error": {"code": -32601, "message": f"unknown tool {name}"}})
                continue
            try:
                payload = do_search(
                    args["query"],
                    int(args.get("max_results", 5)),
                    bool(args.get("force", False)),
                )
                # Return a compact view inline; full evidence is on disk.
                inline = {
                    "query": payload["query"],
                    "artifact": payload.get("artifact", "reused"),
                    "cache": payload["_cache"],
                    "results": [
                        {"rank": r["rank"], "title": r["title"],
                         "url": r["url"], "content": r["content"],
                         "provenance_id": r["provenance_id"]}
                        for r in payload["results"]
                    ],
                }
                _send({"jsonrpc": "2.0", "id": mid, "result": {
                    "content": [{"type": "text", "text": json.dumps(inline, indent=2)}]
                }})
            except Exception as e:
                _send({"jsonrpc": "2.0", "id": mid,
                       "error": {"code": -32000, "message": str(e)}})
        elif method == "notifications/initialized":
            pass
        else:
            if mid is not None:
                _send({"jsonrpc": "2.0", "id": mid,
                       "error": {"code": -32601, "message": f"unknown method {method}"}})


if __name__ == "__main__":
    main()
