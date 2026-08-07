---
title: "Wiki search MCP server: pull-based knowledge retrieval over push-based context injection"
created: 2026-08-06
source: session-019fd8dc
tags: [mcp, wiki-search, fts5, context-injection, pull-based, design-decision, grok-build, hook-limitation]
summary: >
  Built wiki_search MCP server (FTS5 over 990 wiki concepts, <10ms) as a
  pull-based knowledge retrieval tool. Replaces the failed UserPromptSubmit
  push-based injection approach (Grok Build ignores stdout on passive events).
  The model calls wiki_search when it needs to check existing knowledge — no
  gate, no hook dependency. Shared query module importable by /www Phase 1,
  /tp Step 0.5, /check, and CLI. SessionStart hook auto-refreshes the index.
agent: grok
host: grok
cognitive_load: 2
verification: execution-confirmed
relations:
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: related
  - target: wiki/concepts/userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build.md
    type: extends
  - target: wiki/concepts/session-start-hooks-cannot-inject-visible-context-grok-build.md
    type: extends
  - target: wiki/concepts/mcp-server-sharing-multi-terminal.md
    type: related
  - target: wiki/concepts/stop-hook-false-positive-loop-obligation-nonce-gap.md
    type: related
  - target: wiki/concepts/model-delegation-cheap-models-for-code-edits.md
    type: related
  - target: wiki/concepts/i-have-adhd-skill-implementation-research.md
    type: related
---

# Wiki search MCP server: pull-based over push-based

## Decision context

**The problem:** the agent consistently skips checking the wiki before
researching externally. This session's own failure: the agent asked "can a
hook modify tool input?" and ran a full `/www` research cycle when the wiki
already had `[[execution-path-based-model-routing-grok-build]]` with the
exact answer. The behavioral rule "query the wiki first" has ~50% compliance.

**What was tried first (failed):** UserPromptSubmit hook that extracts
keywords from the operator's prompt, queries FTS5, and injects results as
`additionalContext` before the agent reasons. This is the pattern used by
retro-knowledge-injector (notque/claude-code-toolkit) and
claude-token-optimizer (nadimtuhin) on Claude Code.

**Why it failed:** Grok Build ignores stdout on UserPromptSubmit (verified
3 times — `[[userpromptsubmit-hooks-cannot-auto-invoke-skills-grok-build]]`).
The `.claude/settings.local.json` compat dispatch path was also tested and
confirmed passive. Multiple community projects (sqlew, cartograph, ai-memory,
grok-turn-index) document the same limitation.

## The decision

**Pull-based (MCP tool) over push-based (hook injection).**

Instead of injecting context at prompt time, expose the wiki index as an
MCP tool the model calls when it needs to. The tool description drives
usage: "Search the workspace knowledge base of 990+ concepts. Use this
BEFORE external research."

| Approach | Mechanism | Works on Grok Build? | Depends on agent behavior? |
|---|---|---|---|
| Push (hook injection) | UserPromptSubmit stdout → context | ❌ No | No (automatic) |
| Pull (MCP tool) | Model calls `wiki_search` on demand | ✅ Yes | Yes (tool description drives usage) |

## Steelman (rejected alternative)

**PreToolUse gate on web_search:** block external research until the wiki
is checked. Uses a mechanism that works (PreToolUse deny). Problem: the
fleet doesn't use `web_search` for research — it uses DDG via
`run_terminal_command`, firecrawl via `use_tool`, and subagent dispatches.
Gating `web_search` gates the wrong tool. And gating all research is
brittle (false positives on legitimate non-research uses).

## What was built

1. **FTS5 index** (`wiki_index_builder.py`) — 990 wiki concepts, frontmatter
   parsed (title + summary + tags), SQLite FTS5, WAL mode, atomic replace.
   Builds in ~150ms.
2. **Shared query module** (`wiki_search.py`) — keyword extraction with
   camelCase/underscore normalization, FTS5-safe quoted phrase queries,
   importable by any Python script. CLI interface for ad-hoc queries.
3. **MCP server** (`wiki_search_server.py`) — stdio server wrapping the
   query module. One tool: `wiki_search`. Returns title + summary + URL.
4. **SessionStart auto-refresh** (`wiki_index_refresh.py`) — rebuilds index
   if >24h old or concept count changed.
5. **Skill integrations** — `/www` Phase 1b + Round 3 + Round 3.5 + Step 3.15
   swapped from inline grep to `wiki_search`. `/tp` Step 0.5 swapped.

## What this means for our workspace

The wiki_search MCP server is now the **universal wiki query layer**. Every
skill that previously did inline grep (`/www` Phase 1b, `/tp` Step 0.5,
`/check` pattern matching, `/close` coverage scan) can call `wiki_search`
instead — faster (FTS5 vs grep), more comprehensive (matches summaries not
just body text), and available as a tool the model uses proactively.

**Skills updated this session:** `/www` (4 steps), `/tp` (1 step). Future
sessions should update `/check`, `/close`, and `/handoff` to use the same
query module for any wiki lookups they perform.

**Index maintenance:** SessionStart hook auto-refreshes. If a wiki concept
is written mid-session, the next session start picks it up. For same-session
freshness, the model can call `wiki_search` again (query is <10ms).

**Connection to [[execution-path-based-model-routing-grok-build]]:** the
three-layer architecture (behavioral guidance → deny-gate → execution-path)
now has a fourth layer: **MCP tools as pull-based knowledge access**. The
wiki_search tool sits at the behavioral layer — it makes wiki knowledge
available at the point of decision without depending on the agent remembering
to check.

## Falsifier

The MCP approach is wrong if: after 5 sessions, the model never calls
`wiki_search` proactively — meaning the tool description isn't sufficient
to drive usage and a gate is needed after all.

## Receipts

- FTS5 index: `P:/.data/wiki/_state/wiki-concepts-index.db` — 990 concepts, 1.1MB
- MCP server: `~/.grok/hooks/scripts/wiki_search_server.py` — stdio, mcp SDK v1.26.0
- Query module: `~/.grok/hooks/scripts/wiki_search.py` — 13 tests, all passing
- Config: `~/.grok/config.toml [mcp_servers.wiki_search]` — registered, live
- UserPromptSubmit falsifier: hook fired (logged), `updatedInput` emitted
  (logged), Grok Build ignored it (subagent ran on original model)
- Community confirmation: sqlew HOOKS_GUIDE.md, cartograph-plugin,
  ai-memory, grok-turn-index — all document Grok Build passive-event limitation
