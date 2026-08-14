---
title: "Grok-chat-mem candidate repos: session transcript semantic search landscape (2026-08-13)"
created: 2026-08-13
source: session-019ffbf4 (/www research on grok-chat-mem candidates)
sources:
  - external: https://github.com/marcelocantos/mnemo (marcelocantos, 2026 — Go, Apache-2.0)
  - external: https://github.com/nerdyaustin/memory_mcp (nerdyaustin, 2026 — Python, MIT)
  - external: https://github.com/AerionDyseti/vector-memory-mcp (AerionDyseti, 2026 — TypeScript/Bun, MIT)
  - external: https://github.com/mcarlson/doc-memory (mcarlson, 2026 — TypeScript, MIT)
  - external: https://github.com/CynepMyx/deja (CynepMyx, 2026 — Python, MIT, PyPI: dejasearch)
  - external: https://github.com/obra/episodic-memory (obra, 2026 — TypeScript, MIT — current installed tool)
  - external: https://github.com/mem0ai/mem0 (Mem0, 2026 — 63K stars, Apache-2.0 — overkill)
  - external: https://github.com/getzep/graphiti (Zep/Graphiti, 2026 — 30K stars, Apache-2.0 — overkill)
  - external: https://github.com/ccf/agentcairn (agentcairn, 2026 — 34 stars, Apache-2.0 — Markdown vault model)
tags: [memory, semantic-search, session-transcripts, mcp, grok-sessions, episodic-memory, survey, grok-chat-mem]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  Survey of 15+ repos and plugins for "grok-chat-mem" (semantic search over
  Grok Build session transcripts at ~/.grok/sessions/). Only ONE tool —
  marcelocantos/mnemo — already indexes Grok sessions out of the box, with a
  documented Grok Build MCP registration path and a Windows installer. However,
  it has 0 stars and 0 Windows downloads (zero external validation). The
  safest path remains extending the already-installed episodic-memory, which
  has a well-tested multi-format parser and for which we already have a
  working Grok transcript parser at ~/.grok/skills/aar/__lib/transcript_parser.py.
  Three additional tools (memory_mcp, vector-memory-mcp, deja) have clean
  parser-extension architectures that would take ~50-150 LoC to add Grok
  support. Enterprise platforms (Mem0, Graphiti, Letta) are extreme overkill —
  they require LLM extraction per memory and target live agent loops, not
  archival transcript search.
relations:
  - target: wiki/concepts/cross-session-transcript-mining-continuous-improvement.md
    type: extends
  - target: wiki/concepts/conversation-distillation-review-packet-export.md
    type: extends
  - target: wiki/concepts/structured-behavioral-memory-architecture.md
    type: related
---

# Grok-chat-mem candidate repos: session transcript search landscape

## Decision context

The operator is renaming and rationalizing the two external memory systems:
- **claude-mem-grok → grok-tool-mem** (push-based, captures tool observations)
- **episodic-memory → grok-chat-mem** (pull-based, indexes session transcripts)

The rename exposes a functional gap: episodic-memory indexes Claude Code
(`~/.claude/projects/`) and Codex (`~/.codex/sessions/`) but NOT Grok Build
(`~/.grok/sessions/`). The operator asked: are there existing repos/plugins
that already meet the functionality requirements (semantic search over Grok
session transcripts via MCP), without needing to build it ourselves?

**Functionality requirements for grok-chat-mem:**
1. Semantic search over Grok session transcripts at `~/.grok/sessions/`
2. MCP server for agent integration
3. Local-first (no cloud API dependency for embeddings)
4. SQLite or similar local DB
5. Incremental indexing (only new/changed files)

## The standout: mnemo (already supports Grok)

**marcelocantos/mnemo** is the only candidate that already indexes
`~/.grok/sessions/` out of the box.

| Attribute | Value |
|---|---|
| Repo | https://github.com/marcelocantos/mnemo |
| Stars | 0 (zero — no external adoption) |
| Forks | 3 |
| Created | 2026-04-05 |
| Last push | 2026-08-08 (v0.85.0, rapid release cadence) |
| License | Apache 2.0 |
| Language | Go (CGo for SQLite FTS5) |
| Commits | 328 |
| DB | SQLite + FTS5 |
| Embeddings | FTS5 for text; CLIP for images |
| MCP transport | HTTP (daemon on port 19419, not stdio) |
| MCP tools | 27 |

**Confirmed Grok support (receipt: README at master branch):**
- README explicitly states: "mnemo indexes Claude Code (`~/.claude/projects/`), Codex CLI (`~/.codex/sessions/`), and **Grok CLI (`~/.grok/sessions/`)** transcripts"
- Documented Grok Build install: `grok mcp add --transport http mnemo http://localhost:19419/mcp`
- Windows installer (`mnemo-0.85.0-windows-amd64-setup.exe`) registers as Windows Service
- Supports Claude Code AND Grok CLI session resume via `mnemo resume`

**Strengths:**
- Only tool that already does the job — zero code to write
- HTTP daemon model means MCP tools survive agent restarts (unlike stdio)
- Rich feature set: dashboard, federation (mTLS peering), token analytics,
  session chain detection, context compaction, vault export (Obsidian/Logseq)
- Pre-migration backup before schema changes
- Rapid release cadence (v0.83 → v0.84 → v0.85 in 3 days)

**Risks:**
- **0 stars, 0 Windows downloads** — literally nobody has validated it on
  Windows. The author is clearly macOS-focused (6 darwin-arm64 downloads).
- Single author (marcelocantos) — bus factor of 1
- Go + CGo dependency: release binaries are statically linked, but
  build-from-source needs MinGW/LLVM on Windows
- HTTP daemon model adds operational complexity (service management,
  port conflicts) vs. episodic-memory's per-session stdio model
- 27 MCP tools may overwhelm tool-selection on smaller models
- The Grok parser implementation is not exposed at README level — the
  exact format handling is unverified beyond the feature claim

**Download counts (v0.85.0, receipt: GitHub API 2026-08-13):**
- darwin-arm64: 6 downloads
- linux-amd64: 1
- linux-arm64: 1
- windows-amd64-setup.exe: **0**
- windows-amd64.zip: **0**
- windows-arm64: **0**

## The "extend what we have" path: episodic-memory + AAR parser

We already have two pieces that make this the lowest-risk option:

1. **episodic-memory** (obra) — installed, working for Claude Code + Codex.
   TypeScript, SQLite + sqlite-vec, Transformers.js (all-MiniLM-L6-v2, 384-dim),
   MCP server (stdio). Well-tested (45+ test files). Uses LLM for summarization.

2. **AAR transcript parser** — already exists at
   `~/.grok/skills/aar/__lib/transcript_parser.py` (17KB) +
   `~/.grok/skills/aar/__lib/event_model.py` (12KB). Handles all 5 Grok
   message types (system, user, assistant, reasoning, tool_result),
   extracts tool_calls with arguments, joins tool_result back to producing
   tool_call. Documented in `[[conversation-distillation-review-packet-export]]`.

**To add Grok support to episodic-memory:**
- Write `parseGrokConversation()` in `src/parser.ts` — extract user/assistant
  exchanges from Grok's simpler format (no `message` wrapper, content directly
  on the object)
- Add `~/.grok/sessions/` to sync source list in `src/sync.ts`
- Build (`npm run build`)
- Effort: ~2-4 hours. The AAR parser already solves the hard part (format
  parsing); the episodic-memory parser just needs to map Grok types to its
  `ConversationExchange` interface.

**Strengths:**
- We control the code — no dependency on a zero-star project
- Already tested infrastructure (episodic-memory has 45+ test files)
- Reuses existing Grok parser knowledge from the AAR skill
- Same MCP interface the agent already uses (episodic-memory__search, read)

**Risks:**
- episodic-memory uses LLM calls for summarization (not just embedding) —
  this adds API dependency and cost (up to 10 calls per sync)
- Requires a TypeScript build step after changes
- stdio MCP transport means the server restarts per session (vs. mnemo's
  persistent daemon)

## Three viable alternatives with clean extension architectures

### nerdyaustin/memory_mcp (Python, MIT)
- **1 star, 12 commits** — but cleanest parser-extension pattern
- `SessionParser` protocol — adding Grok = ~50-100 LoC Python
- 7 sources already: Claude Code, Codex, Gemini CLI, LM Studio, OpenCode, OMP, Claude history
- SQLite + FTS5 + sqlite-vec (lazy vector), local fastembed (bge-small-en-v1.5)
- 10 MCP tools, optional PostgreSQL+pgvector sync for multi-machine
- **Best if:** we want a Python toolchain and the cleanest extension surface

### AerionDyseti/vector-memory-mcp (TypeScript/Bun, MIT)
- **5 stars, 173 commits, 3 contributors** — most active maintainer of the small tools
- `SessionLogParser` interface (2 methods: `parse()`, `findSessionFiles()`)
- Adding Grok = ~80-150 LoC TypeScript (trivial — Grok format is simpler than Claude's)
- SQLite + sqlite-vec, Transformers.js, session waypoints feature
- **Best if:** we want TypeScript with the least code to write

### CynepMyx/deja (Python, MIT, PyPI: dejasearch)
- **1 star, 78 commits** — source-registry design
- fastembed ONNX (multilingual-e5-small, 384-dim)
- **A complete Grok adapter has been drafted publicly** (web search surfaced
  the source code for `src/deja/parsers/grok.py`)
- Has a session-ID collision bug that needs fixing (derives session_id from
  filename, which gives "chat_history" for every Grok session)
- **Best if:** we want the Grok adapter already written for us

### mcarlson/doc-memory (TypeScript, MIT)
- **3 stars, 60 commits** — format-agnostic (text-only chunker)
- Works immediately: `DOC_MEMORY_WATCH="~/.grok/sessions:**/chat_history.jsonl"`
- Trade-off: treats JSONL as raw text — embeddings include JSON wrapper noise
- Would need a pre-processor to extract clean text for optimal embeddings
- **Best if:** we want zero-code setup and accept JSON noise in embeddings

## Enterprise platforms (all overkill)

Surveyed for completeness. None are appropriate for "index my Grok sessions":

| Platform | Stars | Why overkill |
|---|---|---|
| **Mem0** | 63K | Requires LLM extraction per memory (thousands of API calls for 2K sessions). Agent-loop architecture, not document retrieval. |
| **Graphiti/Zep** | 30K | Requires graph DB (Neo4j/FalkorDB) + LLM extraction. Bi-temporal knowledge graph modeling. Needs structured-output-capable LLM. |
| **Letta** | 24K | Agent self-editing framework. Designed for stateful agents that manage their own memory, not archival search. Legacy repo split. |
| **Redis Agent Memory** | 305 | Requires Redis. Two-tier working/long-term memory designed for live agent conversations. V0/ is "not the supported production path." |
| **agentcairn** | 34 | Closest competitor to episodic-memory, but requires Markdown vault as source of truth with frontmatter/provenance/supersession. Hybrid BM25+vector+graph, local-first, no required LLM. Good if you want Obsidian integration. |

## Grok session format reference

For any tool that needs a Grok parser:

```
~/.grok/sessions/<url-encoded-cwd>/<session-uuid-v7>/
  chat_history.jsonl    ← primary transcript (this is what needs indexing)
  updates.jsonl         ← tool I/O stream (ACP-style)
  summary.json          ← session metadata
```

**chat_history.jsonl line types:**
```json
{"type":"system","content":"You are Grok..."}
{"type":"user","content":[{"type":"text","text":"<user_query>...</user_query>"}]}
{"type":"reasoning","content":"..."}
{"type":"assistant","content":[{"type":"text","text":"..."}],"tool_calls":[{"id":"call_...","name":"read_file","arguments":{...}}]}
{"type":"tool_result","content":"...","tool_call_id":"call_..."}
```

Key differences from Claude Code format:
- No `message` wrapper — `content` is directly on the object
- No `role` key — `type` field serves as both message-type and content-block-type
- Tool calls are a top-level array on assistant messages, not nested in content blocks
- `tool_result` is a separate message type, not a content block in a user message
- `reasoning` type exists (thinking/chain-of-thought) — may be encrypted

## Recommendation

**Three viable paths, each with different risk/effort tradeoffs:**

### Path A: mnemo (zero code, highest external risk)
Install `mnemo-0.85.0-windows-amd64-setup.exe`, register as Grok MCP server.
If it works on Windows, you get the richest feature set immediately. If it
doesn't (0 Windows downloads means untested), you fall back to Path B.
**Time to evaluate:** 30 minutes. **Risk:** external dependency on a
0-star single-author project with no Windows validation.

### Path B: extend episodic-memory (lowest risk, moderate effort)
Write `parseGrokConversation()` using the AAR parser as reference, add
`~/.grok/sessions/` to sync sources, rebuild. We control the code, we
already understand the format, we already have a working parser.
**Time:** 2-4 hours. **Risk:** low — well-tested codebase, no new
external dependency.

### Path C: adopt memory_mcp + write Grok parser (middle ground)
Clone memory_mcp, write `parsers/grok.py` (~50-100 LoC), register it.
Cleanest extension architecture, but trades the episodic-memory test
suite for a 12-commit codebase.
**Time:** 4-8 hours. **Risk:** moderate — new dependency, but clean code.

**My read:** Path B is the optimal long-term solution. We already have
the parser, the test suite, and the MCP integration. The only argument
for Path A is if mnemo's daemon model (persistent HTTP MCP, survives
agent restarts) and richer features (federation, analytics, dashboard)
justify the external dependency risk. That argument is worth testing —
install mnemo, see if it works on Windows, and if it does, evaluate
whether the feature richness justifies depending on a 0-star project.
