---
thread_id: skill-infra-20260724
parent_handoff_path: none
current_session_id: 019f94ac-82be-7f63-b308-13060d337601
current_terminal_id: console_16e8f28f-7b6c-48ba-b689-9ffb
produced_at: 2026-07-24T22:20:22Z
status: open
handoff_type: investigation
accurate_as_of_head: 854968a52b8922603ff67822cd11cf1fb20b8c76
---

## Objective

Port, rename, and enhance the crawl4ai skill from Claude plugins to Grok; add version-check infrastructure across all research skills; wire Context7 MCP into Grok Build.

## Status

OPEN — most work done; Context7 → wiki integration and Jina Reader integration are deferred.

## Producing context

2026-07-24, session 019f94ac, terminal console_16e8f28f, Grok Build (glm-5-2).

## Read-first list

1. `C:/Users/brsth/.grok/skills/crawl4ai/SKILL.md` — skill definition (renamed from crawl/, host:grok added)
2. `C:/Users/brsth/.grok/skills/crawl4ai/crawl_to_qmd.py` — ingestion script with --check-version flag
3. `P:/.agents/scripts/version_check.py` — shared version-check utility
4. `C:/Users/brsth/.grok/config.toml` — Context7 MCP config ([mcp_servers.context7])
5. `C:/Users/brsth/.grok/skills/www/SKILL.md` — Round 2.5 with Mode A (crawl4ai) + Mode B (NotebookLM)

## Verified facts

- [FACT] crawl4ai skill at `~/.grok/skills/crawl4ai/` — 4 files, 8/8 tests pass, `--check-version` works (installed=0.7.8, latest=0.9.2)
- [FACT] crawl4ai 0.7.8 cannot be upgraded to 0.9.2 on Python 3.14 due to lxml~=5.3 incompatibility (GitHub issue #1903)
- [FACT] version_check.py supports --skill {web,www,crawl4ai,wiki}, --all, --json; exit 0=all current, 1=behind, 2=below min
- [FACT] exa_py upgraded 2.0.1→2.16.0, qmd upgraded 0.1.1→0.1.2; both import OK
- [FACT] Context7 MCP in config.toml using global binary `context7-mcp` (npm global install); live this session (2 tools: resolve-library-id, query-docs)
- [FACT] /www Round 2.5 has Mode A (/crawl4ai) + Mode B (NotebookLM Deep Research); 7 correctness fixes applied
- [FACT] /check PASS (41/41 checks), /review healthy (0 bugs, 1 pre-existing risk: frontmatter injection)
- [FACT] `go-deepseek-v4-flash` subagent model fails with serialization error across all 5 /check verifiers

## Current state

| Item | Done? |
|---|---|
| crawl4ai skill ported + renamed + version check | ✅ |
| Shared version_check.py utility | ✅ |
| /web + /www + /crawl4ai SKILL.md version-check sections | ✅ |
| Context7 MCP in config.toml + npm global install | ✅ |
| /www Round 2.5 Mode A + Mode B | ✅ |
| /www correctness review (7 fixes) | ✅ |
| nlm_deep_research.py staging script | ✅ |
| nlm login (NotebookLM auth) | ✅ (authenticated as a.hominidae@gmail.com) |
| Library upgrades (exa_py, qmd) | ✅ |
| crawl4ai upgrade | ⛔ Blocked (Python 3.14 / lxml) |
| Context7 → wiki integration in /preflight | ❌ Deferred |
| Jina Reader integration into /web | ❌ Deferred |
| go-deepseek-v4-flash in tool-fallbacks.md | ❌ Not done |
| /www-ingest compound skill | ❌ Removed from trigger table |

## Task packets

### SI-01: Record go-deepseek-v4-flash failure
- **goal:** Add `go-deepseek-v4-flash` to `~/.grok/tool-fallbacks.md` as broken for subagent spawns
- **files:** `C:/Users/brsth/.grok/tool-fallbacks.md`
- **acceptance:** Entry exists with date, symptom (serialization error: missing field 'id'), workaround (use minimax-m3 or parent-verify)
- **verification level:** STATIC_INSPECTION

### SI-02: Context7 → wiki integration
- **goal:** When /preflight discovers a library, query Context7 for current docs and flag wiki staleness
- **in scope:** `/preflight` SKILL.md, `/www` Phase 1 (query Context7 alongside /wiki)
- **out of scope:** Auto-populating wiki from Context7 (staleness rubric handles this)
- **acceptance:** /preflight flags `wiki_stale_vs_upstream` when Context7 shows different API than wiki concept
- **verification level:** LIVE_BEHAVIOR

### SI-03: Jina Reader free scraping fallback
- **goal:** Add Jina Reader (`https://r.jina.ai/<url>`) as a free scraping option in /web or /crawl4ai
- **files:** `C:/Users/brsth/.grok/skills/web/SKILL.md` routing table
- **acceptance:** Simple single-page scrapes use Jina instead of Firecrawl (saves credits)
- **verification level:** LIVE_BEHAVIOR

## Open decisions

**Q: Should crawl4ai stay at 0.7.8 or migrate to raw Playwright?**
- Options: (a) wait for lxml 3.14 wheels, (b) `pip install crawl4ai==0.9.2 --no-deps` (risky), (c) migrate _normalize_result to raw Playwright
- Criterion: stability vs feature access
- Currently leading: (a) — 0.7.8 works fine, the lxml issue is upstream
- Would change if: crawl4ai 0.9.x has a feature we critically need

## Hard constraints

- No destructive git (shared remote, multi-agent)
- crawl4ai upgrade blocked by Python 3.14 / lxml (GitHub #1903)
- Firecrawl credits are limited — route simple scrapes to free alternatives

## Cross-reference couplings

- `~/.grok/config.toml [mcp_servers.context7]` → Context7 MCP server binary (`context7-mcp` via npm global). If npm global is removed, MCP breaks.
- `/www Round 2.5 Mode B` → `nlm_deep_research.py` → `notebooklm-py` package. If notebooklm-py is uninstalled, Mode B fails.
- `version_check.py SKILL_DEPS` → hardcoded package names. If a package renames on PyPI, the check breaks.
- `/crawl4ai crawl_to_qmd.py` → `crawl4ai==0.7.8` + `qmd==0.1.2`. Upgrading either may break the script.

## Other outstanding streams

- **Data-source integration** — NotebookLM + Context7 + Jina Reader integration into research workflow. Separate handoff.
- **NotebookLM consolidation** — reorganize existing Gemini Notebooks into logical groupings. Separate handoff.

## Explicit non-goals

- Do NOT upgrade crawl4ai until lxml ships Python 3.14 wheels
- Do NOT self-host Firecrawl (infrastructure overhead not justified yet)
- Do NOT implement /www-ingest compound skill (removed from trigger table; three criteria sufficient)

## Resumption protocol

1. `python ~/.grok/skills/crawl4ai/test_crawl_to_qmd.py` — verify tests still pass
2. `python P:/.agents/scripts/version_check.py --all` — check for new package updates
3. Pick up SI-01 (2-minute task: add go-deepseek-v4-flash to tool-fallbacks.md)

## Suggested next invocation

```
Continue the skill infrastructure workstream. Start with SI-01 (add go-deepseek-v4-flash to tool-fallbacks.md), then evaluate SI-02 (Context7 → wiki integration in /preflight).
```

## Last user message (verbatim)

> "/handoff write handoffs for all the open and paused workstreams and all the decisions we made. Write one to cleanup and consolidate our gemini notesbooks into logical efficient groupings."

## Epistemic labels

- [FACT] All claims verified via tool calls this session (test runs, CLI smoke, file reads)
- [INFERENCE] Context7 → wiki integration is the right architecture (user agreed; not yet implemented)
- [UNKNOWN] When lxml will ship Python 3.14 wheels (monitor GitHub #1903)
