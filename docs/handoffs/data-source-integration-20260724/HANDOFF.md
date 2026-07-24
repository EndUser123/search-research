---
thread_id: data-source-integration-20260724
parent_handoff_path: none
current_session_id: 019f94ac-82be-7f63-b308-13060d337601
current_terminal_id: console_16e8f28f-7b6c-48ba-b689-9ffb
produced_at: 2026-07-24T22:20:22Z
status: open
handoff_type: investigation
accurate_as_of_head: 854968a52b8922603ff67822cd11cf1fb20b8c76
---

## Objective

Integrate NotebookLM Deep Research, Context7, and Jina Reader as data sources into the /www → wiki → /go knowledge pipeline, reducing Firecrawl dependency and expanding source coverage.

## Status

OPEN — architecture designed and documented; NotebookLM auth done; wiring is deferred.

## Producing context

2026-07-24, session 019f94ac, terminal console_16e8f28f, Grok Build (glm-5-2).

## Read-first list

1. `P:/.data/wiki/concepts/notebooklm-gemini-notebook-programmatic-access.md` — NotebookLM tool comparison (nlm vs notebooklm-py), temp notebook staging pattern, integration architecture
2. `P:/.data/wiki/concepts/web-scraping-tool-alternatives-free-tier.md` — Jina Reader, free-tier comparison, routing strategy
3. `C:/Users/brsth/.grok/skills/www/scripts/nlm_deep_research.py` — staging script (create → research → extract → delete)
4. `C:/Users/brsth/.grok/skills/www/SKILL.md` — Round 2.5 Mode A + Mode B

## Verified facts

- [FACT] `nlm` CLI v0.9.0 installed and authenticated (a.hominidae@gmail.com, 51 cookies, profile "codex")
- [FACT] `notebooklm-py` v0.8.0rc1 installed, Python API: `NotebookLMClient.from_storage()` context manager
- [FACT] NotebookLM has Deep Research mode: `fast` (~30s, ~10 sources) and `deep` (~5min, ~40+ sources)
- [FACT] Existing notebooks: at least 3 visible (including one with 73 sources titled "_2026-01-15")
- [FACT] Context7 MCP live (2 tools: resolve-library-id, query-docs); resolved crawl4ai library with 6209 code snippets
- [FACT] Jina Reader (`r.jina.ai`) is free, unlimited fair-use, server-side JS rendering, clean markdown output
- [FACT] Firecrawl free tier: 100 pages/month — being consumed too fast
- [FACT] nlm_deep_research.py exists, syntax valid, has --mode/--keep flags, handles auth failure gracefully

## Current state

| Item | Done? |
|---|---|
| NotebookLM auth (nlm login) | ✅ |
| notebooklm-py vs nlm comparison wiki concept | ✅ |
| Temp notebook staging pattern documented | ✅ |
| nlm_deep_research.py script written | ✅ |
| /www Round 2.5 Mode B documented | ✅ |
| Jina Reader documented as Firecrawl alternative | ✅ |
| Context7 → wiki integration designed | ✅ (architecture only) |
| Live test of nlm_deep_research.py | ❌ Not run |
| Live test of Context7 query-docs | ❌ Tested resolve-library-id only |
| Jina Reader integrated into /web routing | ❌ Deferred |
| Context7 wired into /preflight | ❌ Deferred |

## Task packets

### DS-01: Test nlm_deep_research.py with a real topic
- **goal:** Verify the temp notebook staging pattern works end-to-end
- **command:** `python ~/.grok/skills/www/scripts/nlm_deep_research.py "textual python TUI framework" --mode fast`
- **acceptance:** Returns JSON array of {url, title} sources; temp notebook created and deleted
- **falsifier:** Script crashes or returns 0 sources
- **verification level:** LIVE_BEHAVIOR
- **estimate:** ~40s (fast mode ~30s + notebook create/delete ~10s)

### DS-02: Test Context7 query-docs
- **goal:** Verify Context7 returns useful library documentation
- **command:** `use_tool("context7__query-docs", {"libraryId": "/unclecode/crawl4ai", "query": "how to configure AsyncWebCrawler"})`
- **acceptance:** Returns relevant documentation snippets
- **verification level:** LIVE_BEHAVIOR

### DS-03: Wire Jina Reader into /web as free scraping fallback
- **goal:** Add Jina Reader to /web routing table for simple single-page scrapes
- **files:** `C:/Users/brsth/.grok/skills/web/SKILL.md`
- **acceptance:** Simple scrapes use Jina Reader (free) instead of Firecrawl (credits)
- **verification level:** LIVE_BEHAVIOR

### DS-04: Wire Context7 into /preflight
- **goal:** When /preflight discovers a library, query Context7 for current docs
- **files:** `P:/.agents/skills/preflight/SKILL.md`
- **acceptance:** /preflight reports `wiki_stale_vs_upstream` when Context7 shows different API than wiki
- **verification level:** LIVE_BEHAVIOR

## Open decisions

**Q: Should NotebookLM Mode B be default-on for depth=deep /www runs?**
- Options: (a) always-on for deep, (b) opt-in only, (c) auto-trigger when /web returns <5 results
- Criterion: research breadth vs latency cost (~5min for deep research)
- Currently leading: (c) — auto-trigger when /web underperforms
- Would change if: deep research proves consistently higher quality than /web

## Hard constraints

- NotebookLM auth is session-bound (cookies expire ~weeks); `nlm login` may need re-running
- Firecrawl credits are scarce — prefer free alternatives where quality allows
- Context7 max 3 calls per question (API limit)

## Cross-reference couplings

- `nlm_deep_research.py` → `notebooklm-py` → Google NotebookLM APIs (undocumented, may break)
- `config.toml [mcp_servers.context7]` → `context7-mcp` npm global binary → Context7 API (ctx7sk- key)
- `/www Round 2.5 Mode B` → `nlm_deep_research.py` → requires `nlm login` to have been run
- `web-scraping-tool-alternatives-free-tier.md` wiki concept → Jina Reader routing strategy

## Other outstanding streams

- **Skill infrastructure** — crawl4ai, version_check, config changes. Separate handoff.
- **NotebookLM consolidation** — reorganize Gemini Notebooks. Separate handoff.

## Explicit non-goals

- Do NOT replace /web with NotebookLM — they are complementary, not substitutes
- Do NOT auto-delete notebooks with sources (only temp staging notebooks are deleted)
- Do NOT expose the Context7 API key in git (it's in config.toml and .env, both gitignored)

## Resumption protocol

1. Run DS-01: `python ~/.grok/skills/www/scripts/nlm_deep_research.py "textual python TUI framework" --mode fast`
2. Run DS-02: `use_tool("context7__query-docs", {"libraryId": "/unclecode/crawl4ai", "query": "AsyncWebCrawler configuration"})`
3. Based on results, wire DS-03 (Jina Reader) and DS-04 (Context7 → /preflight)

## Suggested next invocation

```
Continue data-source integration. Test nlm_deep_research.py with a real topic, test Context7 query-docs, then wire Jina Reader into /web routing.
```

## Last user message (verbatim)

> "/handoff write handoffs for all the open and paused workstreams and all the decisions we made. Write one to cleanup and consolidate our gemini notesbooks into logical efficient groupings."

## Epistemic labels

- [FACT] nlm authenticated and working (verified via `nlm notebook list`)
- [FACT] Context7 live with 2 tools (verified via search_tool + resolve-library-id call)
- [INFERENCE] Jina Reader will work as a free scraping fallback (documented, not yet tested locally)
- [UNKNOWN] Whether NotebookLM Deep Research quality exceeds /web multi-backend fan-out (needs live comparison)
