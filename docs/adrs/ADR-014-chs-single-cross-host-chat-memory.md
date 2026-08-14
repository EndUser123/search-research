---
title: "ADR-014: CHS as the single cross-host chat-memory layer — absorb, unify, expose via dedicated MCP"
date: 2026-08-14
status: accepted
deciders: operator (grill-me rounds 1-2, session 019ffbf4)
source: P:/docs/decisions/chs-remediation-decision-record-20260814.md
tags: [adr, memory, chs, search-research, mcp, architecture]
---

# ADR-014: CHS as the single cross-host chat-memory layer

## Context

The workspace runs multiple AI agent hosts (Grok Build, Claude Code, Codex)
whose session transcripts were searchable only per-host: episodic-memory
(Claude+Codex MCP) and search-research's CHS (Claude-only CLI). The 2026-08-13
port added a Grok provider to CHS but shipped structural debt: package under a
Claude-branded path, DB in the replaced system's data dir, two separate DBs
with no provider column, a submodule that had failed four ways in one session,
and an episodic-memory overlap contradicting the "unification & rationalization"
goal. A /tp critique surfaced these; /grill-me resolved 16 decisions.

## Decision

1. **Absorb** `search-research` into the parent repo at `P:/packages/search-research/`
   (no submodule). GitHub repo demoted to subtree-push mirror (`absorbed-main`).
2. **One unified DB** at `P:/.data/chs/chat_history.db` with a `provider`
   column; built by fresh rebuild through all four providers; watermark-based
   incremental indexing; `first_prompt` + turns populated so the CLI works.
3. **Dedicated `chs` MCP server** (FastMCP stdio, tools `search`/`read` under
   prefix `chs`) registered on Grok; also a backend in the search-fleet
   registry so unified search covers chat history. The sr web MCP server is
   untouched and out of scope.
4. **episodic-memory retired on Grok** (MCP off, `remembering-conversations`
   skill ported to CHS). Claude side handled by operator separately.

## Alternatives rejected

- **Extend the sr MCP server** — not registered on Grok; drags web/CKS
  machinery; bigger surface for a 2-tool need. Rejected (operator challenge
  confirmed non-use).
- **Keep separate per-host DBs** — disables cross-agent search, the only real
  payoff of the provider architecture.
- **Keep the submodule + fix it** — four distinct submodule failures in one
  session (empty dir, unreachable gitlink, placeholder URL, broken worktree);
  the failure class, not one instance, was the problem.
- **Migrate existing DBs in place** — three-way merge vs. rebuild-from-source;
  rebuild is simpler and guarantees provider tagging.

## Consequences

- Cross-agent queries ("what did any agent conclude about X") become one FTS
  query over one DB.
- Claude continuity preserved via marketplace junction → operator reinstall.
- Embeddings remain deferred (FTS first); schema supports them unchanged.
- Old DBs stay on disk as rollback until the unified DB is verified.
