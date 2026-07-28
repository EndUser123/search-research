---
thread_id: agentmemory-evaluation-20260727
parent_handoff_path: P:/docs/handoffs/qmd-fts5-replacement-20260727/HANDOFF.md
current_session_id: 019fa48a-fb52-79a3-b8dc-d13c5da284d2
current_terminal_id: grok-build-terminal
produced_at: 2026-07-27T23:00:00Z
status: resolved
handoff_type: investigation
accurate_as_of_head: 00e8458
---

# Evaluate agentmemory as qmd replacement + automated persistence layer

## Objective

Evaluate agentmemory (rohitg00/agentmemory, 25k+ stars) as a potential replacement for qmd AND as an automated persistence layer that could reduce the manual /wiki + /handoff + /aar burden. Fresh-session task: install, test MCP integration on Grok Build, compare search quality against qmd's current index.

## Status

**RESOLVED — do not adopt.** The /www investigation (session 019fa48a,
2026-07-27) resolved the open question: agentmemory is officially unsupported
on Windows. The GitHub README states verbatim: "Native Windows engine setup
is manual (about 10 to 20 minutes) and `agentmemory connect` is currently
unsupported there." The `connect` runtime — what captures and consolidates
sessions — only runs on macOS/Linux.

**Decision:** keep handoffs + wiki as the persistence substrate. The optimal
long-term alternative is `/dream` (async consolidator over existing artifacts),
not a memory-system replacement. Letta's LoCoMo benchmark (74.0% with just a
filesystem) confirms the substrate is sufficient at this scale. See
`P:/.data/wiki/concepts/workspace-infrastructure-investment-priorities-2026.md`
Track C for full evidence.

## Producing context

Date: 2026-07-27. Session: 019fa48a. Discovered via /www research on persistence skills.

## Read-first list

1. `https://github.com/rohitg00/agentmemory` — the repo (README has full install + benchmark data)
2. `P:/docs/handoffs/qmd-fts5-replacement-20260727/HANDOFF.md` — the sibling handoff (200-LOC FTS5 wrapper); this evaluation may supersede it
3. `P:/.data/wiki/concepts/qmd-patch-durability-strategy.md` — the prior decision to keep patching qmd (with re-evaluation trigger)
4. `P:/.data/wiki/concepts/operator-model-routing-directives.md` — operator directives on provider preference (may apply to agentmemory's engine dependencies)

## The evaluation question

agentmemory implements in code what our skills implement manually:
- **qmd replacement:** BM25 + vector + graph search with RRF fusion (95.2% R@5 on LongMemEval-S)
- **Automated persistence:** 12 hooks auto-capture tool use → compress → index (vs our manual /wiki + /handoff)
- **4-tier consolidation:** working → episodic → semantic → procedural (vs our session → wiki → handoff → AAR → dream)
- **Cross-agent:** MCP server accessible from Grok Build, Claude Code, Codex, Cursor, etc.
- **Token efficiency:** ~1,900 tokens/session vs 22K+ for CLAUDE.md at 240 observations

The question: does it work on this host (Windows, Grok Build, multi-agent shared filesystem), and is its search quality + capture automation better than our current manual pipeline?

## Verified facts

- [FACT] agentmemory supports MCP server mode (`npx -y @agentmemory/mcp`) — works with any MCP client (GitHub README)
- [FACT] agentmemory requires iii-engine v0.11.2 runtime (a native binary) — Windows binary available but manual install
- [FACT] agentmemory has 1,428+ tests, 53 MCP tools, 15 skills, 12 hooks (GitHub README)
- [FACT] agentmemory benchmarks: 95.2% R@5 on LongMemEval-S, 92% token reduction vs paste-full-context (benchmark/LONGMEMEVAL.md)
- [FACT] qmd current state: 76 documents, 650 chunks, 1024-dim embeddings, 56MB, dead upstream, 4+ site-packages patches (from qmd-viability handoff)
- [FACT] Our manual persistence pipeline: /wiki (6+ concepts/session) + /handoff (5+ handoffs/session) + /aar (1/session) + /dream (cross-session) = significant operator + model overhead per session
- [INFERENCE] agentmemory's automated capture could reduce the manual /wiki + /handoff burden — untested

## Task packets

### AM-01: Install agentmemory on Windows

- **goal:** Get agentmemory running on this host with the iii-engine
- **in scope:** npm install, iii-engine binary download, Windows path configuration, health check
- **out of scope:** Grok Build MCP wiring (AM-02), search quality comparison (AM-03)
- **acceptance:** `curl http://localhost:3111/agentmemory/health` returns OK
- **falsifier:** iii-engine fails to start on Windows; or agentmemory requires dependencies incompatible with Python 3.14 / Node version on this host
- **verification level required:** LIVE_BEHAVIOR
- **known risk:** Windows native support is "manual setup, 10-20 minutes" per README. iii-engine binary is prebuilt but may have DLL/runtime issues.

### AM-02: Wire MCP integration with Grok Build

- **goal:** Connect agentmemory's MCP server to Grok Build so its 53 tools are accessible
- **in scope:** MCP config in config.toml, tool discovery verification, smoke test (memory_save + memory_recall)
- **out of scope:** migrating existing wiki concepts into agentmemory (AM-04)
- **acceptance:** `search_tool "agentmemory"` returns the tool surface; `use_tool` with memory_smart_search returns results
- **falsifier:** MCP integration fails (agentmemory tools not discoverable or not callable from Grok Build)
- **verification level required:** LIVE_BEHAVIOR

### AM-03: Compare search quality against qmd

- **goal:** Run the same queries against both qmd and agentmemory; compare recall + precision
- **in scope:** 10-20 representative queries from this session's /wiki, /tp, /why, /review, /aar invocations
- **out of scope:** full benchmark suite (LongMemEval)
- **acceptance:** agentmemory search quality ≥ qmd on at least 80% of test queries
- **falsifier:** agentmemory returns worse results than qmd's patched FTS5 on ≥30% of queries
- **verification level required:** LIVE_BEHAVIOR
- **test queries (from this session):**
  - "nemotron routing operator directive preference" (qmd: found operator-model-routing-directives)
  - "qmd decision fork vendor replace" (qmd: found qmd-patch-durability-strategy)
  - "fts5 query syntax escaping" (qmd: found fts5-query-syntax-escaping-required)
  - "closure pressure model bypass skill design" (qmd: found reactive-pattern-matching)
  - "AGENTS.md construction best practices" (qmd: found agents-md-construction-best-practices)

### AM-04: Evaluate automated capture vs manual persistence

- **goal:** Assess whether agentmemory's 12-hook auto-capture can replace or reduce the manual /wiki + /handoff workflow
- **in scope:** one full session with agentmemory running alongside the current skill pipeline; compare what it captures vs what /wiki + /handoff capture
- **out of scope:** actually replacing /wiki + /handoff (decision-only task)
- **acceptance:** written assessment of (a) what agentmemory captures that our skills miss, (b) what our skills capture that agentmemory misses, (c) whether the overlap justifies replacing either
- **falsifier:** agentmemory captures noise (skill body text, system prompts) that drowns signal — same problem as extract_operator_directives.py
- **verification level required:** STATIC_INSPECTION

## Open decisions

### OD-1: Does agentmemory supersede the 200-LOC FTS5 wrapper?

- **Options:** (A) agentmemory replaces both qmd and the planned wrapper, (B) 200-LOC wrapper for search + agentmemory for capture, (C) keep qmd + agentmemory for capture only
- **Selection criterion:** search quality + maintenance burden + Windows compatibility
- **Current lead:** (A) if search quality matches — agentmemory has more features, better benchmarks, and active maintenance
- **What would change:** if agentmemory's iii-engine is unreliable on Windows, fall back to (B) or (C)

### OD-2: Does automated capture reduce the need for /wiki + /handoff?

- **Options:** (A) agentmemory auto-capture replaces /wiki + /handoff, (B) agentmemory complements them (auto-captures observations; skills handle deliberate knowledge distillation), (C) no change to skills
- **Selection criterion:** knowledge quality (does auto-captured memory match the quality of deliberately distilled wiki concepts?)
- **Current lead:** (B) — agentmemory captures raw observations; our skills add the judgment layer (falsifier, decision context, receipts). Auto-capture without judgment produces noise.
- **What would change:** if agentmemory's compression + consolidation produces wiki-quality concepts automatically

### OD-3: Is agentmemory's iii-engine dependency acceptable?

- **Options:** (A) accept the dependency, (B) evaluate standalone MCP mode (7 tools, no engine), (C) reject (too many dependencies)
- **Selection criterion:** reliability on Windows + dependency surface vs feature value
- **Current lead:** (A) if AM-01 succeeds — the engine is a single binary, not a service mesh
- **What would change:** if iii-engine causes conflicts with existing infrastructure (CCR, llama.cpp)

## Hard constraints

- Do NOT uninstall qmd until agentmemory is proven as a replacement
- Do NOT modify existing skills (/wiki, /handoff, /aar) until OD-2 is decided
- Honor the operator's provider preference (direct over intermediary) — iii-engine is local, so this doesn't conflict
- English-only requirement applies to any agentmemory output

## Cross-reference couplings

- `qmd-fts5-replacement-20260727/HANDOFF.md` → this evaluation may supersede the 200-LOC wrapper plan
- `P:/.data/wiki/concepts/qmd-patch-durability-strategy.md` → the re-evaluation trigger has fired; agentmemory is a candidate Option D (not previously evaluated)
- `operator-directive-capture-fix-20260727/HANDOFF.md` → agentmemory's auto-capture could reduce the need for extract_operator_directives.py
- Our 10 persistence skills (/wiki, /handoff, /aar, /debrief, /dream, /tasks, /notice, /crawl4ai, /packet, /close) → agentmemory may overlap with several

## Other outstanding streams

- AGENTS.md refactor (agents-md-refactor-20260727) — independent
- /review consolidation (review-consolidation-20260727) — independent
- /packet bug fixes (CORR-001 through CORR-004) — fixed this session

## Resumption protocol

1. Read the agentmemory GitHub README (link in Read-first)
2. For AM-01: download iii-engine v0.11.2 Windows binary, install agentmemory via npm, run health check
3. For AM-02: add agentmemory MCP server to Grok Build config, verify tool discovery
4. For AM-03: run the 5 test queries against both qmd and agentmemory
5. For AM-04: run one session with agentmemory active, compare captures

## Suggested next invocation

```
/go evaluate agentmemory: install on Windows (AM-01), wire MCP to Grok Build (AM-02), compare search quality vs qmd (AM-03)
```

## Last user message (verbatim)

> /handoff "Recommendation: evaluate agentmemory as a potential qmd replacement + automated persistence layer. It's the most mature, most benchmarked, and most architecturally aligned option. The evaluation should be a fresh-session task (install + test MCP integration + compare search quality against qmd's current index)."

## Epistemic labels

- agentmemory's capabilities and benchmarks are [FACT] (from GitHub README, fetched this session)
- Whether it works on this host is [UNKNOWN] (not tested)
- Whether it can replace qmd is [INFERENCE] (based on benchmark comparison, not direct A/B test)
- Whether auto-capture reduces manual persistence burden is [INFERENCE] (based on architecture comparison, not live evaluation)
