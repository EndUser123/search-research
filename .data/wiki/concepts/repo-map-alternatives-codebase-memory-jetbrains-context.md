---
title: "Repo Map Alternatives: Codebase-Memory (MCP) and JetBrains Context"
created: 2026-07-30
source: session-20260730
tags: [repo-map, codebase-memory, jetbrains-context, mcp, knowledge-graph, tree-sitter, decision-update]
summary: >
  Two new repo-intelligence tools emerged in 2026 that offer different
  architectures from Aider's PageRank text-map approach. Codebase-Memory
  (arXiv, MIT, 900+ stars) persists a tree-sitter knowledge graph in SQLite
  and exposes 14 queryable MCP tools — 10× fewer tokens than file exploration.
  JetBrains Context (July 2026) is a commercial semantic-index layer that
  reduced agent turns by 68%. Both warrant re-evaluation of the Aider
  extraction decision.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://arxiv.org/html/2603.27277v1 (Vogel et al., March 2026) — full paper read
  - https://blog.jetbrains.com/ai/2026/07/introducing-jetbrains-context-repository-intelligence-for-coding-agents/ (JetBrains, July 21, 2026) — full blog read
  - https://github.com/DeusData/codebase-memory-mcp (DeusData, 2026) — MIT licensed
relations:
  - target: wiki/concepts/repo-map-extraction-from-aider-decision.md
    type: refines
  - target: wiki/concepts/context-management-in-claude-code.md
    type: related
  - target: wiki/concepts/execution-path-based-model-routing.md
    type: related
---

# Repo Map Alternatives: Codebase-Memory (MCP) and JetBrains Context

## Decision context

The [[repo-map-extraction-from-aider-decision]] (made earlier today) chose to
extract Aider's `repomap.py` as a Python module — PageRank-ranked text map
injected into context. Two tools published in 2026 offer fundamentally
different architectures that may be superior for our multi-root workspace.

## Codebase-Memory: MCP knowledge graph (arXiv 2603.27277)

**Architecture:** Single statically-linked C binary. Parses 66 languages via
tree-sitter, builds a property-graph knowledge graph in SQLite, exposes 14
typed MCP tools for structural queries. Zero runtime dependencies.

**Key difference from Aider:** Instead of generating a compressed text map and
injecting it into context (Aider's approach), Codebase-Memory persists the graph
and lets the agent **query it on demand** via MCP tools:
- `trace_call_path` — call-chain traversal (inbound/outbound)
- `detect_changes` — git diff impact analysis
- `get_architecture` — community-detection-based architecture summary
- `query_graph` — Cypher-like graph queries
- `search_graph` — symbol search

**Benchmark results (31 languages, Claude Opus 4.6):**

| Metric | Codebase-Memory (MCP) | File Explorer | Difference |
|--------|----------------------|---------------|------------|
| Answer quality | 83% | 92% | 90% of explorer |
| Tool calls | 2.3 avg | 4.8 avg | 2.1× fewer |
| Tokens | ~1,000 | ~10,000 | **10× fewer** |
| Query latency | <1ms | 10-30s | 100× faster |

The 9pp quality gap comes from full-source-context queries (where the graph
intentionally doesn't store source lines). For structural queries (hub
detection, caller ranking, call-chain tracing), it matches or exceeds file
exploration on 19 of 31 languages.

**Scale:** Linux kernel (2.1M nodes, 4.9M edges) indexed in ~3 minutes.
Incremental re-index ~1.2s via XXH3 content hashing. Louvain community
detection for architecture summarization.

**Why it matters for our decision:** Our [[repo-map-extraction-from-aider-decision]]
chose Aider because it's Python-extractable. But Codebase-Memory is:
1. MCP-native (we already use MCP servers — zero new integration pattern)
2. A single binary (simpler deployment than extracting + maintaining Python code)
3. Incrementally updated (Aider re-runs PageRank on every query)
4. Capable of structural queries Aider can't do (call paths, impact analysis)
5. MIT licensed with 900+ stars and active development

**The trade-off:** Aider's text map is a passive context injection — every
agent gets it for free. Codebase-Memory requires the agent to actively query
via MCP tools, which means the agent must know to query. For simple "where is
this function defined" tasks, the text map is zero-friction. For "what breaks
if I change this" tasks, the graph is dramatically better.

## JetBrains Context: commercial semantic index (July 2026)

**Architecture:** Semantic index built by JetBrains, accessed via `jbcontext`
CLI. Pre-indexes repos, provides semantic retrieval tools to Claude Code,
Codex CLI, and Junie CLI. **Multi-repo search** — can find code across repos
not checked out locally.

**Benchmark results (SWE-bench + production monorepo):**
- Agent turns reduced by up to **68%**
- Latency reduced by up to **59%**
- Execution cost reduced by up to **48%**

**Why it doesn't fit us:** Requires JetBrains AI subscription. Source code is
not stored on their servers (privacy-respecting), but we'd be dependent on a
commercial service for a core capability. Not applicable to our open-source
toolchain.

## Updated decision matrix

| Criterion | Aider repomap.py | Codebase-Memory | JetBrains Context |
|-----------|-----------------|-----------------|-------------------|
| **Architecture** | Text map in context | Persistent graph + MCP tools | Semantic index + cloud |
| **Token cost** | ~1K per map injection | ~1K per session (on-demand queries) | Unknown (cloud) |
| **License** | Apache (extract) | MIT | Commercial |
| **Dependencies** | tree-sitter, networkx, grep_ast | Zero (single binary) | JetBrains AI sub |
| **Incremental updates** | No (re-rank per query) | Yes (XXH3 file watcher) | Yes (cloud-indexed) |
| **Structural queries** | No (text only) | Yes (14 MCP tools) | Yes (semantic search) |
| **Multi-repo** | Partial (multiple roots) | Yes (project-per-repo) | Yes (cross-repo) |
| **Our integration** | Python extraction (~1.5h) | MCP server add (~10 min) | N/A (no subscription) |
| **Active development** | Stable (mature) | v0.5.5, 900+ stars | JetBrains-backed |

## What this means for our workspace

The [[repo-map-extraction-from-aider-decision]] remains valid for its stated
goal: a lightweight, always-present context map. But Codebase-Memory is the
better tool for deep structural navigation ("what calls this function across
5 roots?", "what breaks if I change this hook?").

**Recommended path:** deploy BOTH.
- **Aider repomap.py** (or simpler equivalent) for passive context injection
  at session start — gives every agent a compressed codebase overview
- **Codebase-Memory MCP server** for active structural queries when an agent
  needs to trace dependencies, analyze impact, or find callers

This matches the paper's own recommendation: "the optimal architecture is a
hybrid: graph-based retrieval for structural queries, with fallback to file
exploration for source-level tasks" (§5.1).

The falsifier from the original decision (Aider ranking quality doesn't
transfer to multi-root workspaces) remains untested. Codebase-Memory sidesteps
this concern entirely — it indexes per-project and queries via graph
traversal, so multi-root is native.

## Falsifier

This update is wrong if:
- Codebase-Memory's C binary doesn't build/run on Windows 11 (the paper claims
  Windows support but we haven't tested it)
- The MCP tool-call overhead (agent must decide to query) is worse than
  Aider's passive injection for our typical task profile (mostly short
  "where is X" queries, not deep structural analysis)
- The 83% vs 92% quality gap matters more than the 10× token savings for our
  use case (we may prefer correctness over efficiency)

## Sources

- [Codebase-Memory paper (arXiv 2603.27277)](https://arxiv.org/html/2603.27277v1) (Vogel et al., March 2026) — full paper read; benchmark data from Table 6, architecture from §3
- [JetBrains Context announcement](https://blog.jetbrains.com/ai/2026/07/introducing-jetbrains-context-repository-intelligence-for-coding-agents/) (JetBrains, July 21, 2026) — full blog read; benchmark claims from their evaluation
- [Codebase-Memory GitHub](https://github.com/DeusData/codebase-memory-mcp) (DeusData, 2026) — MIT licensed, v0.5.5

## Receipts

- Paper §4.1 Table 6: MCP agent 0.83 quality, 2.3 tool calls, ~1K tokens vs Explorer 0.92, 4.8, ~10K
- Paper §4.3 Table 8: Linux kernel 2.1M nodes in ~3 min, incremental ~1.2s
- Paper §3.5 Table 4: 14 MCP tools listed (index_repository, trace_call_path, detect_changes, etc.)
- JetBrains blog: "reduced agent turns by up to 68%, latency by up to 59%, execution cost by up to 48%"
