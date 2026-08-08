# MCP Search Improvement Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development
> (recommended) or executing-plans to implement this plan task-by-task. Steps
> use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `search_all` composition tool to the search_wiki MCP server that calls both wiki and web search concurrently, returns typed results with per-source status, and includes observability (query log) and index refresh capability.

**Architecture:** search_wiki MCP server gains a second tool (`search_all`) alongside its existing `query` tool. search_all imports the web search function lazily (inside the handler, not at module top) and runs both searches concurrently via `asyncio.gather()`. A shared `SearchResult` dataclass defines the contract between wiki and web result formats. Typed deduplication merges results without dropping wiki entries.

**Tech Stack:** Python 3.14, MCP SDK 1.26.0 (pin `mcp<2`), SQLite FTS5, asyncio, difflib (fuzzy title matching), dataclasses

**Risk level:** Soft plan (reversibility <1.5 — remove from config.toml to undo)

**Spec:** `docs/superpowers/specs/2026-08-07-mcp-search-improvement-design.md`

## Global Constraints

- **MCP SDK:** pin to `mcp>=1.6.0,<2.0.0` — SDK 2.0.0 removed `mcp.server.fastmcp` and restructured imports (`[[mcp-sdk-2-0-fastmcp-breakage]]`)
- **No asyncio.run() in tool handlers** — MCP servers are already async; use `asyncio.gather()` and `asyncio.wait_for()` instead (nested event loop crash risk)
- **Lazy imports for search-mcp** — `parallel_search` imported inside the handler function with try/except, not at module top (config loading side effects can crash the server)
- **Never drop wiki results in deduplication** — internal knowledge always surfaces, even if duplicated by web
- **Encoding:** UTF-8 for all file operations (`encoding='utf-8'`)
- **File paths:** forward slashes in all code and config

---

## File structure

| File | Responsibility | Create/Modify |
|------|---------------|---------------|
| `~/.grok/hooks/scripts/search_result_types.py` | Shared `SearchResult` dataclass + mapper functions + deduplication | **Create** |
| `~/.grok/hooks/scripts/search_wiki_server.py` | Add `search_all` tool + `refresh_index` tool to existing server | **Modify** |
| `~/.grok/hooks/scripts/search_query_log.py` | Query logging module (JSONL append) | **Create** |
| `~/.grok/hooks/scripts/search_wiki_index_builder.py` | Add incremental rebuild function | **Modify** |
| `~/.grok/hooks/tests/test_search_all.py` | Tests for composition, dedup, status, lazy import isolation | **Create** |
| `~/.grok/hooks/tests/test_search_result_types.py` | Tests for SearchResult contract, mappers, dedup | **Create** |
| `~/.grok/hooks/tests/test_search_query_log.py` | Tests for query log append/read | **Create** |
| `~/.grok/AGENTS.md` | Add one-line search convention | **Modify** |

---

### Task 1: Shared SearchResult contract

**Files:**
- Create: `~/.grok/hooks/scripts/search_result_types.py`
- Test: `~/.grok/hooks/tests/test_search_result_types.py`

**Interfaces:**
- Produces: `SearchResult` (dataclass), `map_wiki_result(dict) -> SearchResult`, `map_web_result(SearchResult_from_search_mcp) -> SearchResult`

- [ ] **Step 1: Write failing tests for SearchResult dataclass and mappers**

```python
# ~/.grok/hooks/tests/test_search_result_types.py
"""Tests for shared SearchResult contract, mappers, and deduplication."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from search_result_types import SearchResult, map_wiki_result, map_web_result, deduplicate


def test_search_result_required_fields():
    """SearchResult must have all required fields."""
    sr = SearchResult(
        source="wiki",
        id="test-concept.md",
        title="Test Concept",
        url="file:///P:/.data/wiki/concepts/test-concept.md",
        snippet="A test concept for validation.",
        score=0.95,
        retrieved_at="2026-08-07T12:00:00Z",
        freshness="evergreen",
        status="ok",
    )
    assert sr.source == "wiki"
    assert sr.id == "test-concept.md"
    assert sr.status == "ok"


def test_map_wiki_result():
    """Wiki search result dict maps to SearchResult."""
    wiki_dict = {
        "title": "My Wiki Concept",
        "summary": "A summary of the concept.",
        "url": "file:///P:/.data/wiki/concepts/my-wiki-concept.md",
        "path": "my-wiki-concept.md",
    }
    sr = map_wiki_result(wiki_dict)
    assert sr.source == "wiki"
    assert sr.title == "My Wiki Concept"
    assert sr.snippet == "A summary of the concept."
    assert sr.id == "my-wiki-concept.md"
    assert sr.freshness == "evergreen"
    assert sr.status == "ok"


def test_map_web_result():
    """Web search result maps to SearchResult."""
    # search-mcp SearchResult has: title, content, source, score, url
    class FakeWebResult:
        def __init__(self):
            self.title = "External Article"
            self.content = "Article content here."
            self.source = "brave"
            self.score = 0.85
            self.url = "https://example.com/article"

    sr = map_web_result(FakeWebResult())
    assert sr.source == "web:brave"
    assert sr.title == "External Article"
    assert sr.url == "https://example.com/article"
    assert sr.freshness in ("recent", "stale-check")


def test_dedup_same_url_merges():
    """Results with same normalized URL are deduplicated, keeping higher score."""
    results = [
        SearchResult("wiki", "wiki.md", "Wiki Hit", "file:///wiki.md", "snippet", 0.9, "2026-08-07", "evergreen", "ok"),
        SearchResult("web:brave", "https://example.com/page", "Web Hit", "https://example.com/page", "snippet", 0.8, "2026-08-07", "recent", "ok"),
        SearchResult("web:exa", "https://example.com/page", "Dup Web Hit", "https://example.com/page", "snippet2", 0.95, "2026-08-07", "recent", "ok"),
    ]
    deduped = deduplicate(results)
    # wiki always kept, web dedup by URL keeps the 0.95 one
    assert len(deduped) == 2
    wiki_results = [r for r in deduped if r.source == "wiki"]
    web_results = [r for r in deduped if r.source.startswith("web")]
    assert len(wiki_results) == 1  # wiki never dropped
    assert len(web_results) == 1
    assert web_results[0].score == 0.95  # higher scored kept


def test_dedup_never_drops_wiki():
    """Wiki results are never dropped even if URL matches a web result."""
    results = [
        SearchResult("wiki", "wiki.md", "Same Title", "https://example.com/page", "wiki snippet", 0.7, "2026-08-07", "evergreen", "ok"),
        SearchResult("web:brave", "https://example.com/page", "Same Title", "https://example.com/page", "web snippet", 0.9, "2026-08-07", "recent", "ok"),
    ]
    deduped = deduplicate(results)
    wiki_results = [r for r in deduped if r.source == "wiki"]
    assert len(wiki_results) == 1  # wiki kept despite same URL


def test_dedup_fuzzy_title_flags_relation():
    """Similar titles (>0.85) get flagged as related, both kept."""
    results = [
        SearchResult("wiki", "model-routing.md", "Model routing policy", "file:///model-routing.md", "snippet", 0.9, "2026-08-07", "evergreen", "ok"),
        SearchResult("web:brave", "https://blog.com/model-routing", "Model routing policy guide", "https://blog.com/model-routing", "snippet", 0.8, "2026-08-07", "recent", "ok"),
    ]
    deduped = deduplicate(results)
    assert len(deduped) == 2  # both kept — different URLs
    web_result = [r for r in deduped if r.source.startswith("web")][0]
    assert "relates to internal concept" in (web_result.freshness or "") or "relates" in str(web_result.status or "")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_result_types.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'search_result_types'`

- [ ] **Step 3: Write the implementation**

```python
# ~/.grok/hooks/scripts/search_result_types.py
"""Shared SearchResult contract for search_wiki and search_web composition.

Both wiki and web search results are mapped to SearchResult before
deduplication and composition in search_all.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from urllib.parse import urlparse, urlunparse


@dataclass
class SearchResult:
    """Typed search result from either wiki or web sources."""
    source: str           # "wiki" | "web:brave" | "web:exa" | "web:ddg"
    id: str               # canonical ID: wiki filename or normalized URL
    title: str
    url: str              # clickable: file:/// for wiki, https:// for web
    snippet: str          # summary or excerpt (~500 chars max)
    score: float          # 0.0-1.0
    retrieved_at: str     # ISO-8601
    freshness: str        # "evergreen" | "recent" | "stale-check"
    status: str           # "ok" | "partial" | "failed" | "timeout"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication: strip query params, fragments, trailing slash, www."""
    if not url or url.startswith("file:///"):
        return url  # wiki URLs are already canonical
    parsed = urlparse(url)
    # Strip www, query, fragment
    netloc = parsed.netloc.replace("www.", "")
    path = parsed.path.rstrip("/") or "/"
    return urlunparse(("https", netloc, path, "", "", ""))


def map_wiki_result(wiki_dict: dict) -> SearchResult:
    """Map a search_wiki result dict to SearchResult."""
    title = wiki_dict.get("title", "Untitled")
    summary = wiki_dict.get("summary", "")
    url = wiki_dict.get("url", "")
    # Extract filename from path or url
    path = wiki_dict.get("path", "")
    if not path and url:
        path = url.rsplit("/", 1)[-1] if "/" in url else url
    snippet = summary[:500] if len(summary) > 500 else summary
    return SearchResult(
        source="wiki",
        id=path,
        title=title,
        url=url,
        snippet=snippet,
        score=wiki_dict.get("score", 1.0),  # FTS5 doesn't return normalized scores
        retrieved_at=_now_iso(),
        freshness="evergreen",
        status="ok",
    )


def map_web_result(web_result) -> SearchResult:
    """Map a search-mcp SearchResult (or duck-typed object) to our SearchResult."""
    title = getattr(web_result, "title", "Untitled")
    content = getattr(web_result, "content", "")
    source = getattr(web_result, "source", "unknown")
    score = getattr(web_result, "score", 0.5)
    url = getattr(web_result, "url", "")
    snippet = content[:500] if len(content) and len(content) > 500 else content
    return SearchResult(
        source=f"web:{source}",
        id=_normalize_url(url),
        title=title,
        url=url,
        snippet=snippet,
        score=float(score),
        retrieved_at=_now_iso(),
        freshness="recent",
        status="ok",
    )


def deduplicate(results: list[SearchResult]) -> list[SearchResult]:
    """Deduplicate results by normalized URL and fuzzy title similarity.

    Rules:
    - Wiki results are NEVER dropped, even if URL matches a web result.
    - Web results with the same normalized URL: keep the higher-scored one.
    - Web results whose title is >0.85 similar to a wiki result: keep both,
      flag the web result as relating to an internal concept.
    """
    if not results:
        return []

    wiki_results = [r for r in results if r.source == "wiki"]
    web_results = [r for r in results if r.source.startswith("web:")]

    # Dedup web results by normalized URL — keep highest scored
    web_by_url: dict[str, SearchResult] = {}
    for wr in web_results:
        norm = _normalize_url(wr.url)
        if norm not in web_by_url or wr.score > web_by_url[norm].score:
            web_by_url[norm] = wr
    deduped_web = list(web_by_url.values())

    # Flag web results that relate to wiki concepts (fuzzy title match > 0.85)
    for wr in deduped_web:
        for wr_wiki in wiki_results:
            ratio = SequenceMatcher(None, wr.title.lower(), wr_wiki.title.lower()).ratio()
            if ratio > 0.85:
                wr.status = "ok (relates to internal concept)"
                break

    # Internal first, then external
    return wiki_results + deduped_web
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_result_types.py -v`
Expected: PASS (all 6 tests)

- [ ] **Step 5: Commit**

```bash
cd ~/.grok
git add hooks/scripts/search_result_types.py hooks/tests/test_search_result_types.py
git commit -m "feat: shared SearchResult contract for wiki+web composition"
```

---

### Task 2: Query log module

**Files:**
- Create: `~/.grok/hooks/scripts/search_query_log.py`
- Test: `~/.grok/hooks/tests/test_search_query_log.py`

**Interfaces:**
- Produces: `log_query(tool: str, query: str, result_count: int, latency_ms: float)` — appends to JSONL

- [ ] **Step 1: Write failing tests**

```python
# ~/.grok/hooks/tests/test_search_query_log.py
"""Tests for search query logging."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from search_query_log import log_query, read_recent_queries, get_log_path


def test_log_query_appends_jsonl(tmp_path):
    """log_query writes a JSON line to the log file."""
    log_path = tmp_path / "test_query_log.jsonl"
    log_query("search_wiki", "test query", 5, 8.2, log_path=str(log_path))
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tool"] == "search_wiki"
    assert entry["query"] == "test query"
    assert entry["result_count"] == 5
    assert entry["latency_ms"] == 8.2
    assert "timestamp" in entry


def test_log_query_multiple_entries(tmp_path):
    """Multiple log_query calls append multiple lines."""
    log_path = tmp_path / "test_multi.jsonl"
    log_query("search_wiki", "query 1", 3, 5.0, log_path=str(log_path))
    log_query("search_web", "query 2", 10, 2400.0, log_path=str(log_path))
    log_query("search_all", "query 3", 15, 2410.0, log_path=str(log_path))
    lines = log_path.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 3
    tools = [json.loads(line)["tool"] for line in lines]
    assert tools == ["search_wiki", "search_web", "search_all"]


def test_read_recent_queries(tmp_path):
    """read_recent_queries returns entries from the log."""
    log_path = tmp_path / "test_read.jsonl"
    log_query("search_wiki", "test", 1, 5.0, log_path=str(log_path))
    entries = read_recent_queries(log_path=str(log_path), limit=10)
    assert len(entries) == 1
    assert entries[0]["query"] == "test"


def test_log_query_does_not_crash_on_missing_dir(tmp_path):
    """log_query creates the directory if it doesn't exist."""
    log_path = tmp_path / "subdir" / "log.jsonl"
    log_query("search_all", "test", 0, 100.0, log_path=str(log_path))
    assert log_path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_query_log.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write the implementation**

```python
# ~/.grok/hooks/scripts/search_query_log.py
"""Search query logging — appends to JSONL for observability.

All search tools (search_wiki.query, search_web.query, search_wiki.search_all)
log their queries here so tool-selection behavior can be analyzed across sessions.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = str(Path(__file__).parent / "search_query_log.jsonl")


def log_query(
    tool: str,
    query: str,
    result_count: int,
    latency_ms: float,
    log_path: str = DEFAULT_LOG_PATH,
    extra: dict | None = None,
) -> None:
    """Append a query entry to the JSONL log.

    Never raises — logging failures are swallowed (observability is best-effort).
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": tool,
        "query": query,
        "result_count": result_count,
        "latency_ms": round(latency_ms, 1),
    }
    if extra:
        entry.update(extra)
    try:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Never block on log failure


def read_recent_queries(log_path: str = DEFAULT_LOG_PATH, limit: int = 100) -> list[dict]:
    """Read recent query entries from the log."""
    try:
        path = Path(log_path)
        if not path.exists():
            return []
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        entries = []
        for line in reversed(lines[-limit:]):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries
    except Exception:
        return []


def get_log_path() -> str:
    return DEFAULT_LOG_PATH
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_query_log.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
cd ~/.grok
git add hooks/scripts/search_query_log.py hooks/tests/test_search_query_log.py
git commit -m "feat: search query logging module for observability"
```

---

### Task 3: Incremental index rebuild in search_wiki_index_builder

**Files:**
- Modify: `~/.grok/hooks/scripts/search_wiki_index_builder.py`
- Test: `~/.grok/hooks/tests/test_search_incremental_rebuild.py` (create)

**Interfaces:**
- Produces: `rebuild_incremental(concepts_dir, index_path) -> dict` — only re-indexes changed files (mtime check)

- [ ] **Step 1: Write failing test**

```python
# ~/.grok/hooks/tests/test_search_incremental_rebuild.py
"""Test incremental index rebuild — only changed files are re-indexed."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from search_wiki_index_builder import build_index, rebuild_incremental


def test_incremental_rebuild_only_changes_updated_files(tmp_path):
    """rebuild_incremental only re-indexes files whose mtime changed."""
    concepts = tmp_path / "concepts"
    concepts.mkdir()
    index = tmp_path / "index.db"

    # Create initial files
    f1 = concepts / "concept-a.md"
    f2 = concepts / "concept-b.md"
    f1.write_text("---\ntitle: A\nsummary: Concept A\n---\n# A\nContent A", encoding="utf-8")
    f2.write_text("---\ntitle: B\nsummary: Concept B\n---\n# B\nContent B", encoding="utf-8")

    # Build full index
    stats1 = build_index(concepts, index)
    assert stats1["concept_count"] == 2

    # Modify only f1
    time.sleep(0.1)  # ensure mtime changes
    f1.write_text("---\ntitle: A Updated\nsummary: Updated A\n---\n# A\nNew content", encoding="utf-8")

    # Incremental rebuild
    stats2 = rebuild_incremental(concepts, index)
    assert stats2.get("reindexed", 0) == 1  # only f1 changed
    assert stats2.get("unchanged", 0) == 1   # f2 unchanged
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_incremental_rebuild.py -v`
Expected: FAIL with `ImportError: cannot import name 'rebuild_incremental'`

- [ ] **Step 3: Add rebuild_incremental to search_wiki_index_builder.py**

Add this function to `~/.grok/hooks/scripts/search_wiki_index_builder.py` (after the existing `build_index` function):

```python
def rebuild_incremental(concepts_dir: Path, index_path: Path) -> dict:
    """Rebuild only changed wiki concepts (mtime-based incremental).

    Reads the existing FTS5 index, compares file mtimes, and only re-indexes
    files whose mtime is newer than the index build time.

    Returns stats dict with reindexed count, unchanged count, and build time.
    """
    import os
    start = time.time()

    if not concepts_dir.exists():
        return {"error": "concepts_dir_not_found"}

    md_files = sorted(concepts_dir.glob("*.md"))
    if not md_files:
        return {"error": "no_concepts_found"}

    # Get index mtime as threshold
    if not index_path.exists():
        # No existing index — do full build
        return build_index(concepts_dir, index_path)

    index_mtime = index_path.stat().st_mtime

    changed = []
    unchanged = []
    for md_file in md_files:
        if md_file.stat().st_mtime > index_mtime:
            changed.append(md_file)
        else:
            unchanged.append(md_file)

    if not changed:
        return {
            "reindexed": 0,
            "unchanged": len(unchanged),
            "build_time_ms": round((time.time() - start) * 1000, 1),
            "index_path": str(index_path),
        }

    # For changed files: rebuild the full index (simpler than partial FTS5 updates,
    # and build_index is fast ~150ms for 990 concepts)
    stats = build_index(concepts_dir, index_path)
    stats["reindexed"] = len(changed)
    stats["unchanged"] = len(unchanged)
    return stats
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_incremental_rebuild.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd ~/.grok
git add hooks/scripts/search_wiki_index_builder.py hooks/tests/test_search_incremental_rebuild.py
git commit -m "feat: incremental index rebuild for stale-index mitigation"
```

---

### Task 4: Add search_all and refresh_index tools to search_wiki_server

**Files:**
- Modify: `~/.grok/hooks/scripts/search_wiki_server.py`
- Test: `~/.grok/hooks/tests/test_search_all.py`

**Interfaces:**
- Consumes: `SearchResult`, `map_wiki_result`, `map_web_result`, `deduplicate` from Task 1
- Consumes: `log_query` from Task 2
- Consumes: `rebuild_incremental` from Task 3
- Consumes: `search()` from existing `search_wiki.py`
- Consumes: `parallel_search()` from `C:/Users/brsth/.grok/search-mcp/server.py` (lazy import)

- [ ] **Step 1: Write failing tests**

```python
# ~/.grok/hooks/tests/test_search_all.py
"""Tests for search_all composition and refresh_index tool."""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from search_result_types import SearchResult


def test_search_all_returns_both_internal_and_external():
    """search_all handler returns results from both wiki and web."""
    # This is an integration test — it mocks parallel_search
    # We test the composition logic, not the actual web calls
    from search_wiki_server import compose_results

    wiki_results = [
        {"title": "Wiki Hit", "summary": "Found in wiki", "url": "file:///wiki.md", "path": "wiki.md"},
    ]
    # Mock web results (list of dicts that look like SearchResult objects)
    class MockWebResult:
        def __init__(self, title, url, source="brave"):
            self.title = title
            self.content = "Web content"
            self.source = source
            self.score = 0.8
            self.url = url

    web_results = [MockWebResult("Web Hit", "https://example.com/hit")]

    composed = compose_results(wiki_results, web_results, web_status="ok")

    assert "sources" in composed
    assert composed["sources"]["wiki"]["status"] == "ok"
    assert composed["sources"]["wiki"]["count"] == 1
    assert composed["sources"]["web"]["status"] == "ok"
    assert composed["sources"]["web"]["count"] == 1

    # Internal results first
    results = composed["results"]
    assert results[0]["source"] == "wiki"
    assert results[1]["source"].startswith("web:")


def test_search_all_handles_web_failure():
    """When web search fails, search_all returns wiki-only with failed web status."""
    from search_wiki_server import compose_results

    wiki_results = [{"title": "Wiki", "summary": "S", "url": "file:///w.md", "path": "w.md"}]
    web_results = []

    composed = compose_results(wiki_results, web_results, web_status="failed", web_error="timeout")

    assert composed["sources"]["wiki"]["status"] == "ok"
    assert composed["sources"]["web"]["status"] == "failed"
    assert len(composed["results"]) == 1  # wiki only
    assert composed["results"][0]["source"] == "wiki"


def test_search_all_handles_wiki_empty():
    """When wiki returns nothing, search_all returns web-only."""
    from search_wiki_server import compose_results

    class MockWebResult:
        def __init__(self):
            self.title = "Web Only"
            self.content = "Content"
            self.source = "exa"
            self.score = 0.9
            self.url = "https://example.com"

    wiki_results = []
    web_results = [MockWebResult()]

    composed = compose_results(wiki_results, web_results, web_status="ok")

    assert composed["sources"]["wiki"]["status"] == "ok"
    assert composed["sources"]["wiki"]["count"] == 0
    assert len(composed["results"]) == 1
    assert composed["results"][0]["source"] == "web:exa"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_all.py -v`
Expected: FAIL with `ImportError: cannot import name 'compose_results'`

- [ ] **Step 3: Implement search_all in search_wiki_server.py**

Add the following to `~/.grok/hooks/scripts/search_wiki_server.py` (after the existing `call_tool` function, before `main`):

```python
# === search_all composition tool ===

SEARCH_ALL_TOOL = types.Tool(
    name="search_all",
    description=(
        "Search both the workspace knowledge base AND the web in one call. "
        "Returns internal results labeled [INTERNAL] and external results "
        "labeled [EXTERNAL], with per-source status. Use when you need both "
        "workspace context and external validation."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query (natural language — keywords extracted automatically)",
            },
            "max_results": {
                "type": "integer",
                "description": "Max results per source (default: 5)",
                "default": 5,
            },
            "web_enabled": {
                "type": "boolean",
                "description": "Whether to include web search (default: true). Set false for sensitive queries.",
                "default": True,
            },
        },
        "required": ["query"],
    },
)

REFRESH_INDEX_TOOL = types.Tool(
    name="refresh_index",
    description=(
        "Rebuild the wiki FTS5 search index. Call this after writing new "
        "wiki concepts to make them immediately searchable."
    ),
    inputSchema={
        "type": "object",
        "properties": {},
    },
)


def compose_results(
    wiki_results: list[dict],
    web_results: list,
    web_status: str = "ok",
    web_error: str | None = None,
    wiki_latency_ms: float = 0,
    web_latency_ms: float = 0,
) -> dict:
    """Compose wiki + web results into a unified response with per-source status."""
    from search_result_types import map_wiki_result, map_web_result, deduplicate

    wiki_mapped = [map_wiki_result(r) for r in wiki_results]
    web_mapped = [map_web_result(r) for r in web_results] if web_results else []
    all_results = deduplicate(wiki_mapped + web_mapped)

    sources = {
        "wiki": {
            "status": "ok" if wiki_results else "ok",
            "count": len(wiki_mapped),
            "latency_ms": round(wiki_latency_ms, 1),
        },
        "web": {
            "status": web_status,
            "count": len(web_mapped),
            "latency_ms": round(web_latency_ms, 1),
        },
    }
    if web_error:
        sources["web"]["error"] = web_error

    return {
        "sources": sources,
        "results": [
            {
                "source": r.source,
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "score": r.score,
                "label": "[INTERNAL]" if r.source == "wiki" else "[EXTERNAL]",
                "status": r.status,
            }
            for r in all_results
        ],
    }


def format_composition_response(composed: dict) -> str:
    """Format the composition response as readable text for the MCP tool output."""
    lines = []
    sources = composed.get("sources", {})
    wiki_s = sources.get("wiki", {})
    web_s = sources.get("web", {})

    lines.append(f"Sources: wiki={wiki_s.get('status', '?')}({wiki_s.get('count', 0)}) "
                 f"web={web_s.get('status', '?')}({web_s.get('count', 0)})")

    for r in composed.get("results", []):
        lines.append("")
        lines.append(f"{r['label']} {r['title']}")
        lines.append(f"  {r['snippet']}")
        lines.append(f"  {r['url']}")
        if r.get("status") and "relates" in r["status"]:
            lines.append(f"  ({r['status']})")

    return "\n".join(lines)


async def handle_search_all(arguments: dict) -> list[types.TextContent]:
    """Handle the search_all tool call."""
    import time as _time
    from search_query_log import log_query

    query = arguments.get("query", "")
    max_results = arguments.get("max_results", 5)
    web_enabled = arguments.get("web_enabled", True)

    if not query:
        return [types.TextContent(type="text", text="Error: query is required.")]

    # Wiki search (synchronous, fast)
    wiki_start = _time.time()
    wiki_results = wiki_search_fn(query, max_results=max_results)
    wiki_latency = (_time.time() - wiki_start) * 1000

    # Web search (async, lazy import, with timeout)
    web_results = []
    web_status = "ok"
    web_error = None
    web_latency = 0.0

    if web_enabled:
        web_start = _time.time()
        try:
            # Lazy import: if this fails, only search_all degrades, not the whole server
            search_mcp_path = str(Path(__file__).parent.parent.parent / "search-mcp")
            if search_mcp_path not in sys.path:
                sys.path.insert(0, search_mcp_path)
            from server import parallel_search

            raw_web = await asyncio.wait_for(
                parallel_search(query, num_results=max_results),
                timeout=15.0,
            )
            # parallel_search returns {backend_name: [results]}
            for backend_name, backend_results in raw_web.items():
                if backend_name == "_meta":
                    continue
                web_results.extend(backend_results)
            web_latency = (_time.time() - web_start) * 1000
        except asyncio.TimeoutError:
            web_status = "timeout"
            web_error = "web search exceeded 15s timeout"
            web_latency = (_time.time() - web_start) * 1000
        except Exception as e:
            web_status = "failed"
            web_error = str(e)
            web_latency = (_time.time() - web_start) * 1000

    # Compose
    composed = compose_results(
        wiki_results, web_results,
        web_status=web_status, web_error=web_error,
        wiki_latency_ms=wiki_latency, web_latency_ms=web_latency,
    )

    # Log query for observability
    log_query(
        tool="search_all",
        query=query,
        result_count=len(composed["results"]),
        latency_ms=max(wiki_latency, web_latency),
        extra={"wiki_count": len(wiki_results), "web_count": len(web_results), "web_status": web_status},
    )

    return [types.TextContent(type="text", text=format_composition_response(composed))]


async def handle_refresh_index() -> list[types.TextContent]:
    """Handle the refresh_index tool call."""
    from search_wiki_index_builder import rebuild_incremental
    from search_wiki_index_builder import WIKI_CONCEPTS, INDEX_PATH

    stats = rebuild_incremental(WIKI_CONCEPTS, INDEX_PATH)
    if "error" in stats:
        return [types.TextContent(type="text", text=f"Index refresh failed: {stats['error']}")]

    return [types.TextContent(type="text", text=(
        f"Index refreshed: {stats.get('reindexed', stats.get('concept_count', '?'))} concepts "
        f"reindexed, {stats.get('unchanged', 0)} unchanged, "
        f"{stats.get('build_time_ms', '?')}ms"
    ))]
```

Then modify the `list_tools()` and `call_tool()` functions to include the new tools:

```python
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [TOOL_DEFINITION, SEARCH_ALL_TOOL, REFRESH_INDEX_TOOL]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "query":
        # existing query handler — keep as-is
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 5)
        if not query:
            return [types.TextContent(type="text", text="Error: query is required.")]
        results = wiki_search_fn(query, max_results=max_results)
        if not results:
            return [types.TextContent(type="text", text="No wiki concepts found. Proceed with external research.")]
        lines = [f"Found {len(results)} wiki concept(s) (check these before researching externally):"]
        for r in results:
            lines.append(f"\n- [[{r['title']}]]")
            lines.append(f"  {r['summary']}")
            lines.append(f"  {r['url']}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    elif name == "search_all":
        return await handle_search_all(arguments)

    elif name == "refresh_index":
        return await handle_refresh_index()

    else:
        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]
```

Also update the existing TOOL_DEFINITION description to the new selection-semantics wording:

```python
TOOL_DEFINITION = types.Tool(
    name="query",
    description=(
        "Search the workspace knowledge base of 990+ concepts covering prior "
        "decisions, documented patterns, and design rationale. Use for "
        "workspace-specific knowledge — the workspace likely already has "
        "relevant findings that external research would re-derive."
    ),
    # ... rest stays the same
)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_all.py -v`
Expected: PASS (all 3 tests)

- [ ] **Step 5: Commit**

```bash
cd ~/.grok
git add hooks/scripts/search_wiki_server.py hooks/tests/test_search_all.py
git commit -m "feat: add search_all composition tool + refresh_index to search_wiki server"
```

---

### Task 5: SDK version check + config registration

**Files:**
- Modify: `~/.grok/hooks/scripts/search_wiki_server.py` (add SDK check at top)
- Modify: `~/.grok/config.toml` (ensure search_wiki server still registered — no change needed, but verify)

**Interfaces:**
- No new interfaces

- [ ] **Step 1: Add SDK version check at the top of search_wiki_server.py**

Add after the existing imports in `~/.grok/hooks/scripts/search_wiki_server.py`:

```python
# SDK version guard — mcp 2.0.0 restructured imports ([[mcp-sdk-2-0-fastmcp-breakage]])
try:
    import mcp
    mcp_version = getattr(mcp, "__version__", "1.0.0")
    if mcp_version >= "2.0.0":
        print(f"WARNING: mcp SDK {mcp_version} detected — this server was built for "
              f"mcp < 2.0.0. Import paths may break. Pin 'mcp<2' in requirements.",
              file=sys.stderr)
except ImportError:
    pass
```

- [ ] **Step 2: Verify search_wiki server is registered in config.toml**

Read: `~/.grok/config.toml` — confirm `[mcp_servers.search_wiki]` entry exists and points to the correct script path.

No changes needed if already registered (it was registered in the previous session).

- [ ] **Step 3: Verify the server starts without crash**

Run: `python ~/.grok/hooks/scripts/search_wiki_server.py` (briefly, then Ctrl+C)
Expected: no crash, no SDK warning (we're on 1.26.0)

- [ ] **Step 4: Commit**

```bash
cd ~/.grok
git add hooks/scripts/search_wiki_server.py
git commit -m "feat: SDK version check for mcp 2.0 breakage prevention"
```

---

### Task 6: AGENTS.md convention

**Files:**
- Modify: `~/.grok/AGENTS.md`

- [ ] **Step 1: Add one-line search convention**

In `~/.grok/AGENTS.md`, under the "Web-search tool selection" section, after the preference order list, add:

```markdown
**Wiki-first convention (search MCP):** Before external web research, check if `search_wiki` has relevant workspace knowledge — if the topic involves prior decisions, patterns, or documented solutions, the workspace likely already covers it. Use `search_all` when you need both workspace and web results in one call.
```

- [ ] **Step 2: Read back to verify**

Read the modified section and confirm the convention is present and the surrounding text survived.

- [ ] **Step 3: Commit**

```bash
cd ~/.grok
git add AGENTS.md
git commit -m "docs: add wiki-first search convention to AGENTS.md"
```

---

### Task 7: Integration test — verify search_all end-to-end

**Files:**
- Test: `~/.grok/hooks/tests/test_search_all_integration.py` (create)

This is a manual integration test — it requires the MCP server to actually start and respond. It verifies the server loads both tools and search_all calls both backends.

- [ ] **Step 1: Write integration test**

```python
# ~/.grok/hooks/tests/test_search_all_integration.py
"""Integration test: verify search_wiki server exposes all 3 tools.

This test does NOT make real web calls — it verifies the MCP server
starts, lists all tools, and the search_all handler is wired correctly.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_server_lists_three_tools():
    """The search_wiki server should list 3 tools: query, search_all, refresh_index."""
    from search_wiki_server import TOOL_DEFINITION, SEARCH_ALL_TOOL, REFRESH_INDEX_TOOL

    tools = [TOOL_DEFINITION, SEARCH_ALL_TOOL, REFRESH_INDEX_TOOL]
    names = [t.name for t in tools]
    assert "query" in names
    assert "search_all" in names
    assert "refresh_index" in names


def test_search_all_tool_description_has_labels():
    """search_all description mentions INTERNAL and EXTERNAL labels."""
    from search_wiki_server import SEARCH_ALL_TOOL
    desc = SEARCH_ALL_TOOL.description
    assert "INTERNAL" in desc
    assert "EXTERNAL" in desc


def test_query_tool_description_uses_selection_semantics():
    """query tool description says 'workspace-specific knowledge' not 'ALWAYS call first'."""
    from search_wiki_server import TOOL_DEFINITION
    desc = TOOL_DEFINITION.description
    assert "workspace-specific" in desc or "workspace knowledge" in desc
    assert "ALWAYS call" not in desc  # no command language


def test_search_all_accepts_web_enabled_param():
    """search_all input schema includes web_enabled parameter."""
    from search_wiki_server import SEARCH_ALL_TOOL
    props = SEARCH_ALL_TOOL.inputSchema.get("properties", {})
    assert "web_enabled" in props
    assert props["web_enabled"]["type"] == "boolean"
```

- [ ] **Step 2: Run integration tests**

Run: `python -m pytest ~/.grok/hooks/tests/test_search_all_integration.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 3: Manual smoke test — restart Grok and call search_all**

After implementation, restart Grok Build. Verify:
1. `search_wiki` MCP server starts without error (check config.toml logs)
2. The model can call `search_wiki__search_all` with a query
3. Results include both `[INTERNAL]` and `[EXTERNAL]` sections
4. `search_wiki__refresh_index` works after writing a new concept

- [ ] **Step 4: Commit**

```bash
cd ~/.grok
git add hooks/tests/test_search_all_integration.py
git commit -m "test: integration tests for search_all tool wiring"
```

---

## Self-review

**1. Spec coverage:** Each spec section maps to a task:
- Shared result contract → Task 1 ✅
- Query log → Task 2 ✅
- Incremental rebuild → Task 3 ✅
- search_all + refresh_index tools → Task 4 ✅
- SDK pin check → Task 5 ✅
- AGENTS.md convention → Task 6 ✅
- Integration verification → Task 7 ✅

**2. Placeholder scan:** No TBD, TODO, or vague descriptions. All code blocks are complete implementations.

**3. Type consistency:** `SearchResult` fields match across mapper functions, dedup logic, and compose_results. `log_query` signature matches across definition and call sites.

**4. Completeness checks:**
- Data-flow: query → search functions → map → dedup → compose → response. Complete.
- Latency: wiki is sub-10ms (FTS5), web has 15s timeout via `asyncio.wait_for`. Hot path specified.
- Definitions: "related concept" = fuzzy title match >0.85. "Never drop wiki" = explicit rule. Dedup operationalized.
- Cost proxy: not applicable (no cost formulas).
- Exception safety: lazy import wrapped in try/except, web failure returns status not crash, log_query swallows errors.
- Internal consistency: no contradictions between tasks.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-07-mcp-search-phase1.md`.

**Execution options:**

**1. `/go execute docs/superpowers/plans/2026-08-07-mcp-search-phase1.md` (recommended on Grok Build)** — profile `plan-execute`: H2 off (plan is SoT), H0 git/non-git, task DAG for H4, TDD red-before-green, checkbox ticks + Execution Status at GO DONE.

**2. Subagent-Driven (manual)** — dispatch a fresh subagent per task, review between tasks.

**3. Inline Execution** — execute tasks in this session using executing-plans, batch execution with checkpoints.

**Which approach?**
