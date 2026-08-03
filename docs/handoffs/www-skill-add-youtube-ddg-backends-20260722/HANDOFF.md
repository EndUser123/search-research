---
thread_id: 5b9e2f1a-8c4d-4e7a-b6f3-2d1e8a7c4f90
parent_handoff_path: none
current_session_id: 019f8082-9298-7561-b03e-3c21afc43115
current_terminal_id: grok
produced_at: 2026-07-22T15:10:00+00:00
status: CLOSED
handoff_type: investigation
accurate_as_of_head: c629aa1f61ecfbdbaa2a4390d955c7a47605c880
---

# Handoff: Update `/www` skill with YouTube, DDG, and other missing search backends

## Objective

Add YouTube, DuckDuckGo (DDG), and other currently-missing search backends to the `/www` (Wiki-Web-Wiki compound research) skill's query-diversity table and backend routing section, so that research covers sources the current 5-slot table misses.

## Status

OPEN — not started. Gap identified and documented; implementation is the residual work.

## Producing context

- **Date:** 2026-07-22
- **Session:** `019f8082-9298-7561-b03e-3c21afc43115` (Grok Build, forked session)
- **Host:** Grok Build on Windows 11, PowerShell 7
- **HEAD:** `c629aa1f61ecfbdbaa2a4390d955c7a47605c880`
- **Trigger:** During the DiffusionGemma spawn_subagent investigation, the user said *"I heard about it on YouTube. Did you search YouTube? Do you do that by default?"* — answer was no on both counts. This exposed a real methodology gap in `/www`.

## Last user message (verbatim)

> /handoff new update www with youtube and ddg and other things we are missing.

## Read-first list (ordered, with reasons)

1. `C:\Users\brsth\.grok\skills\www\SKILL.md` — the skill to update. Specifically:
   - **Lines 156-169** — "2.1b Plan query diversity" table (5 slots: official docs, practitioner blogs, academic, community discussion, disconfirmation)
   - **Lines 170-177** — "2.1c Select backends per query" routing (5 backends: web-search-prime, minimax-search, firecrawl_search, firecrawl_agent, default=minimax)
   - **Lines 183-202** — "2.2a-c Run searches + triage + scrape" section
2. `C:\Users\brsth\.grok\skills\web\SKILL.md` — the `/web` skill that `/www` delegates to for Phase 2; its routing logic may also need updating
3. `~/.grok/AGENTS.md` § "Web-search tool selection" (lines ~240-265) — the global tool-selection preference order that both skills reference
4. This handoff — for the concrete list of what's missing (below)

## Verified facts (with source paths)

- [FACT] `/www` SKILL.md query-diversity table has 5 slots: official docs, practitioner blogs, academic/research, community discussion (Reddit/forums), disconfirmation (`www/SKILL.md:160-169`)
- [FACT] `/www` SKILL.md backend routing lists 5 backends: `web-search-prime` (time-sensitive), `minimax-search` (technical), `web-search-prime` with `search_domain_filter` (domain-scoped), `firecrawl_agent` (deep multi-source), `minimax-search` (default) (`www/SKILL.md:170-177`)
- [FACT] YouTube is not mentioned anywhere in `/www` SKILL.md (verified via grep, 2026-07-22)
- [FACT] DuckDuckGo (DDG) is not mentioned anywhere in `/www` SKILL.md (verified via grep, 2026-07-22)
- [FACT] `search__fuse` (RRF-merge MCP tool) is available in this session's MCP server list but is NOT referenced in `/www` SKILL.md — it's the tool that merges results across backends via Reciprocal Rank Fusion
- [FACT] During the DiffusionGemma investigation, the user said "I heard about it on YouTube" and the research had NOT searched YouTube — the gap was real and load-bearing (session 019f8082, turn ~2026-07-22T14:00Z)
- [FACT] The `minimax-search__web_search` tool description says "You MUST use this tool whenever you need to search for real-time or external information on the web" — but it is a general-web search, not video-aware (verified via `search_tool` schema query, 2026-07-22)
- [FACT] YouTube URLs appeared incidentally in `/www` Phase 2 search results (general-web search returned YouTube links) but were treated as noise, not scraped — the methodology gap is not "YouTube never appears" but "YouTube is never targeted and YouTube results are never scraped" (session 019f8082)

## Current state

### What's in place
- `/www` has a 5-slot query-diversity table (lines 160-169)
- `/www` has a 5-backend routing section (lines 170-177)
- `/www` delegates Phase 2 to `/web` which has its own (also incomplete) routing logic
- The global `~/.grok/AGENTS.md` § "Web-search tool selection" defines a preference order (minimax → web-search-prime → built-in web_search) but also doesn't mention YouTube or DDG

### What's NOT in place (the gap)
The following backends/source-types are missing from `/www`'s methodology:

| Missing source-type | Why it matters | How to add |
|---|---|---|
| **YouTube** | Primary distribution channel for AI tooling tutorials, demos, and practitioner walkthroughs. User explicitly named it as where they heard about the NVIDIA proxy. | Add a "Video platforms" slot to the diversity table (slot 6). Add YouTube-specific search to backend routing. Add guidance for scraping YouTube content (transcript extraction vs page scrape). |
| **DuckDuckGo (DDG)** | Different index bias than Google-backed engines (minimax, firecrawl). Catches results Google downranks. | Add to backend routing as an alternative to minimax for the disconfirmation query (DDG's different ranking surfaces different perspectives). |
| **`search__fuse` (RRF merge)** | Already available as an MCP tool in this session. Merges ranked lists from multiple backends via Reciprocal Rank Fusion. `/www` currently runs backends in parallel but doesn't merge — it manually triages. | Add to Step 2.2 as an optional merge step: run N backends, pass all result lists to `search__fuse`, get one fused ranked list. Reduces manual triage. |
| **GitHub-specific search** | For code/tooling topics, `site:github.com` via firecrawl or web-search-prime surfaces repos, issues, PRs that general-web misses. | Add as a query-modifier option in 2.1a when the topic involves code, tools, or libraries. |
| **Stack Overflow / dev.to / Medium** | Practitioner signal with different demographics than Reddit. | Could fold into existing "practitioner blogs" slot, or add as a sub-type. |
| **arxiv / Semantic Scholar** | For academic claims, generic "academic" is too vague. arxiv has an API; Semantic Scholar has a free API. | Add as a query-modifier when the shape is `facts` and the topic is research-heavy. |

## Task packets

### WWW-01: Add YouTube to query-diversity table and backend routing

- **goal:** YouTube becomes a first-class source type in `/www` Phase 2
- **in scope:** `/www` SKILL.md lines 156-177 (diversity table + backend routing); `/www` SKILL.md Step 2.2c (scraping guidance for YouTube — use firecrawl_scrape on the YouTube URL, or note that YouTube transcripts need a different approach)
- **out of scope:** `/web` SKILL.md (separate update if needed); building a YouTube-specific MCP tool
- **files / anchors:**
  - `C:\Users\brsth\.grok\skills\www\SKILL.md:156-177` — diversity table + backend routing
  - `C:\Users\brsth\.grok\skills\www\SKILL.md:183-202` — search/scrape steps
- **acceptance:**
  - YouTube appears as a named slot in the diversity table
  - Backend routing includes a YouTube-targeting query pattern (e.g., `site:youtube.com` via firecrawl_search or web-search-prime)
  - Scraping guidance addresses YouTube's特殊性 (transcript vs page content; firecrawl may only get description, not transcript)
- **falsifier:** if a `/www` run on an AI tooling topic still produces 0 YouTube results after this change, the integration isn't working
- **verification level required:** LIVE_BEHAVIOR (run a test `/www` query that should surface YouTube results)
- **estimate:** ~15 minutes (3 SKILL.md section edits)

### WWW-02: Add DDG to backend routing

- **goal:** DDG is available as an alternative backend for disconfirmation queries
- **in scope:** `/www` SKILL.md backend routing section; `/web` SKILL.md if it has its own routing
- **out of scope:** building a DDG MCP tool (DDG has a lite endpoint that can be scraped, or use `firecrawl_search` with DDG as the source)
- **files / anchors:**
  - `C:\Users\brsth\.grok\skills\www\SKILL.md:170-177`
- **acceptance:**
  - DDG appears in backend routing with a specific use case (disconfirmation — different index bias)
  - Guidance on how to query DDG (likely `firecrawl_search` with DuckDuckGo URL, or `web_search` built-in with DDG-targeting query)
- **falsifier:** if DDG returns identical results to minimax for the same query, it's not adding diversity value
- **verification level required:** LIVE_BEHAVIOR
- **estimate:** ~10 minutes

### WWW-03: Add `search__fuse` (RRF merge) as optional Phase 2 merge step

- **goal:** `/www` can optionally merge results from multiple backends into one ranked list instead of manual triage
- **in scope:** `/www` SKILL.md Step 2.2 (add a 2.2d "Optional: RRF merge" step); document the `search__fuse` tool's input format
- **out of scope:** modifying the `search__fuse` tool itself
- **files / anchors:**
  - `C:\Users\brsth\.grok\skills\www\SKILL.md:183-202`
- **acceptance:**
  - Step 2.2 has an optional merge substep that calls `search__fuse` with results from multiple backends
  - The input format is documented (JSON object mapping source names to ranked result lists)
  - Guidance on when to merge vs when to triage manually (merge when >3 backends; triage when ≤3)
- **falsifier:** if `search__fuse` is never called in practice because the manual triage is easier, the merge step is ceremony
- **verification level required:** STATIC_INSPECTION (the tool is already verified working — this is documentation)
- **estimate:** ~10 minutes

### WWW-04: Add GitHub-specific and academic-specific query modifiers

- **goal:** When the topic involves code/tools or research, `/www` adds targeted queries for GitHub and arxiv/Semantic Scholar
- **in scope:** `/www` SKILL.md Step 2.1a (query enhancement — add domain-specific query modifiers)
- **out of scope:** building GitHub or arxiv MCP tools
- **files / anchors:**
  - `C:\Users\brsth\.grok\skills\www\SKILL.md` Step 2.1a
- **acceptance:**
  - 2.1a has a "domain-specific query modifiers" subsection listing: `site:github.com` (code/tools), `site:arxiv.org` (research), `site:stackoverflow.com` (technical errors)
  - Guidance on when each modifier applies (based on topic keywords)
- **falsifier:** if the modifiers never change which results are returned, they're noise
- **verification level required:** STATIC_INSPECTION
- **estimate:** ~10 minutes

### WWW-05: Update global web-search preference in AGENTS.md

- **goal:** The global `~/.grok/AGENTS.md` § "Web-search tool selection" should mention YouTube and DDG as source types, not just tools
- **in scope:** `C:\Users\brsth\.grok\AGENTS.md` § "Web-search tool selection" (lines ~240-265)
- **out of scope:** `/www` and `/web` SKILL.md (covered by WWW-01 through WWW-04)
- **files / anchors:**
  - `C:\Users\brsth\.grok\AGENTS.md:240-265`
- **acceptance:**
  - The web-search preference section acknowledges that different source types (video, code repos, academic) may need different backends
  - YouTube and DDG are named as source-type-aware options
- **falsifier:** if the AGENTS.md update contradicts the `/www` and `/web` SKILL.md updates, there's a conflict
- **verification level required:** STATIC_INSPECTION
- **estimate:** ~5 minutes

## Open decisions

1. **YouTube transcript scraping:** firecrawl can scrape YouTube pages but may only get the description, not the transcript. Should `/www`:
   - (a) Accept description-only as "good enough" for triage, then scrape transcript only for score-3 results?
   - (b) Use a YouTube transcript extraction tool/script (e.g., `yt-dlp --write-auto-sub`)?
   - (c) Just use the video title + description for snippet triage and never scrape transcripts?

2. **DDG access method:** DuckDuckGo doesn't have a clean API. Options:
   - (a) `firecrawl_search` with DDG-formatted query (may not target DDG specifically)
   - (b) `web_search` built-in (may route through Google)
   - (c) Direct scrape of `https://duckduckgo.com/html/?q=<query>` (lite HTML endpoint)
   - (d) A DDG MCP tool if one exists or can be installed

3. **Should the diversity table be expanded to 7-8 slots, or should YouTube/DDG/etc. be added as optional modifiers to existing slots?** Expanding the table increases minimum query count (currently scales by depth: quick=1-2, standard=3-4, deep=5-6). Adding 3 more mandatory slots would push deep to 8-9 queries. Alternatively, make them conditional ("add YouTube slot when topic involves tutorials/demos/tools").

## Evidence (session-specific)

The gap was discovered live during the DiffusionGemma spawn_subagent investigation (session 019f8082, 2026-07-22):

1. User asked `/www` to find an NVIDIA engineer's proxy repo for Claude Code
2. `/www` searched general-web backends (minimax, firecrawl) — found repos but none from an "NVIDIA engineer"
3. User said "I heard about it on YouTube. Did you search YouTube? Do you do that by default?"
4. Answer: no on both counts
5. Belated YouTube search found the same repos wrapped in video tutorials — confirmed the methodology gap was real but didn't surface new information in this specific case
6. The gap is structural: for AI tooling topics where YouTube is a primary distribution channel, general-web search is insufficient

## Deep research upgrade path (added 2026-07-22, session 019f819a)

Source: `/www` compound research on deep research systems → wiki concept
`P:/.data/wiki/concepts/deep-research-systems-and-web-upgrade.md`

Research into how Anthropic, OpenAI, Perplexity, and open-source projects (GPT-Researcher,
open_deep_research) implement deep research revealed five upgrade patterns applicable to
`/web` and `/www`. These are architecturally larger than the backend-addition tasks
(WWW-01 through WWW-05) above, so they're tracked as a separate task group.

### DR-01: Make iterative refinement actually execute on depth=deep

- **goal:** `/www` Phase 2.8 (iterative refinement) describes a search-reason-search loop but rarely executes in practice. Make it the default for `depth=deep`.
- **in scope:** `/www` SKILL.md Step 2.8 — change from optional to mandatory when depth=deep
- **why:** Anthropic and OpenAI both confirm iterative retrieval is the biggest quality lever for multi-hop topics. Our existing wiki concept `optimal-multi-backend-search-strategy` identified this gap.
- **acceptance:** a `/www depth=deep` run performs at least 1 refinement round (assess gaps → reformulate → search again)
- **estimate:** ~15 min (SKILL.md edit + gap-assessment prompt)

### DR-02: Add /web --deep mode with parallel subagent decomposition

- **goal:** complex queries decompose into sub-queries, each dispatched to a subagent with its own context window (Anthropic orchestrator-worker pattern)
- **in scope:** `/web` SKILL.md — add `--deep` flag that triggers parallel subagent spawning via `spawn_subagent`
- **why:** Anthropic reports +90.2% improvement over single-agent; token usage explains 80% of variance. Our `/go` skill already supports parallel subagent spawning.
- **acceptance:** `/web --deep` spawns 3-5 subagents for independent facets, merges findings, synthesizes with citations
- **estimate:** ~1-2 hours (new /web mode + delegation packets for subagents)

### DR-03: Wire GPT-Researcher MCP server for genuine deep research

- **goal:** install [gptr-mcp](https://github.com/assafelovic/gptr-mcp) as an MCP backend for tree-exploration + Plan-and-Solve deep research
- **in scope:** `~/.grok/config.toml` — add `[mcp_servers.gpt-researcher]`; `/web` SKILL.md — add delegation path for --deep mode
- **why:** GPT-Researcher (28.6k stars) has a mature MCP server with tree-based deep research. Don't build what already exists.
- **acceptance:** GPT-Researcher MCP server is wired in config.toml; `/web --deep` can delegate to it
- **estimate:** ~30 min (install + config + smoke test)

### DR-04: Add citation tracking to /web output

- **goal:** every claim in /web output has source URL + excerpt (like vendor deep research products)
- **in scope:** `/web` SKILL.md output format; `/www` Phase 2.5 synthesis format
- **why:** Anthropic uses a dedicated CitationAgent; OpenAI provides clickable inline citations. Our output currently tags sources but doesn't bind specific claims to specific excerpts.
- **acceptance:** each finding in /web output has `[source: URL, excerpt: "..."]` binding
- **estimate:** ~30 min

### DR-05: Add budget-driven stopping

- **goal:** hard limits on max searches, max pages, max time per /web or /www run
- **in scope:** `/web` SKILL.md — add budget parameters; `/www` SKILL.md — add budget enforcement in Phase 2
- **why:** every vendor has this (OpenAI: 30-60 searches, 120-150 pages, 20-30 min). Without it, agents spiral. Anthropic reports agents "scouring the web endlessly for nonexistent sources."
- **acceptance:** `/web` accepts `--max-searches N --max-pages N --max-time M` parameters
- **estimate:** ~20 min

### Recommended priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| 1 | DR-01 (iterative refinement on deep) | Low | Highest ROI — closes single-pass gap |
| 2 | DR-05 (budget-driven stopping) | Low | Prevents runaway; prerequisite for DR-02 |
| 3 | DR-02 (parallel subagent --deep mode) | Medium | +90% on breadth-first queries (Anthropic data) |
| 4 | DR-03 (GPT-Researcher MCP) | Low (install) | Gets tree-exploration for free |
| 5 | DR-04 (citation tracking) | Medium | Makes output verifiable |

### Reference

- Wiki concept: `P:/.data/wiki/concepts/deep-research-systems-and-web-upgrade.md`
- Research ledger: `P:/.data/www-ledger/deep-research-systems.md`
- Anthropic architecture blog: https://www.anthropic.com/engineering/multi-agent-research-system
- GPT-Researcher: https://github.com/assafelovic/gpt-researcher (28.6k stars)
- open_deep_research: https://github.com/langchain-ai/open_deep_research (12.4k stars)
- Deep Research Bench: https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard

## Other outstanding streams (noted, not handed off)

- **DiffusionGemma spawn_subagent fix:** bug report drafted at `P:/tmp/grok-build-bug-report-nvidia-empty-content.md`; root cause verified (NVIDIA NIM rejects `content: ""` on assistant messages with tool_calls); fix verified (`content: null` works). User needs to submit the bug report to `xai-org/grok-build` and/or decide on the proxy path. This is a separate work stream from the `/www` update.
- **Worktree design (from `/design` earlier this session):** 8-PR design doc at `C:\Users\brsth\AppData\Local\Temp\grok-design-6788cc35\grok-design-doc-6788cc35.md`. Unrelated to the `/www` update.
- **QMD patch durability PRs (PR-1 through PR-4):** pending from earlier in the session. Unrelated.
