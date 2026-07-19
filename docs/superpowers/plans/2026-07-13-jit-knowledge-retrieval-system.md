# JIT Knowledge Retrieval System Design

> **Design document** — not an implementation plan. Architecture, tool selection, and integration design for push/pull just-in-time knowledge retrieval across OpenCode, Claude Code, and Codex.

**Goal:** Wire knowledge graphs (Graphify + Understand-Anything) into a unified MCP-based retrieval layer that provides just-in-time context to LLM coding sessions — both pull (LLM-initiated queries) and push (automatic context injection before edits).

**Core insight:** The two tools are complementary. Graphify tells you **where** things are (cheap, deterministic AST). Understand-Anything tells you **why** they exist (expensive, semantic, LLM-derived). kbask proved the hybrid pattern works. The question is how to operationalize it for real daily use.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LLM SESSION                            │
│  OpenCode / Claude Code / Codex                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  AGENTS.md / CLAUDE.md                            │   │
│  │  "Before editing, call kbask.ask() for context"   │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↕                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  MCP Tools (available to call)                   │   │
│  │  kbask.ask / kbask.trace / kbask.onboard         │   │
│  │  CodeGraph.explore / CodeGraph.impact            │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
            ↕ (MCP stdio)                    ↕ (MCP stdio)
  ┌──────────────────────┐    ┌──────────────────────────┐
  │  kbask (MCP server)  │    │  CodeGraph (MCP server)  │
  │  ┌───────┬────────┐  │    │  ┌────────────────────┐  │
  │  │struct │semantic│  │    │  │SQLite + FTS5       │  │
  │  │Graphify│ UA     │  │    │  │tree-sitter         │  │
  │  │(cheap) │(costly)│  │    │  │auto-sync on change │  │
  │  └───────┴────────┘  │    │  └────────────────────┘  │
  └──────────────────────┘    └──────────────────────────┘
            ↕                              ↕
  ┌──────────────────┐    ┌──────────────────────────────┐
  │ .ua/knowledge-   │    │ .codegraph/codegraph.db      │
  │ graph.json (UA)  │    │ (auto-synced on file change)  │
  │ graphify-out/    │    └──────────────────────────────┘
  │ (Graphify)       │
  └──────────────────┘
```

## Tool Selection Rationale

### Chosen: kbask + CodeGraph

**kbask** provides the hybrid Graphify + UA interface. One MCP server, three tool layers (structural, semantic, hybrid). Already exists, MIT, Python, installable via uvx.

**CodeGraph** provides structural always-on MCP. SQLite + FTS5, tree-sitter, auto-syncs on file change. The "auto-sync" is critical — it means the structural graph is never stale without the LLM having to remember to rebuild it. ~57K stars, TypeScript, MIT. Auto-detects and configures OpenCode during `codegraph install`.

### Why not the others

| Alternative | Rejected because |
|---|---|
| codebase-memory-mcp | C binary, no Windows native build without WSL2. 3-min Linux kernel indexing is impressive but irrelevant for this workspace's scale. |
| code-review-graph | Purpose-built for PR review blast radius — too narrow for general JIT retrieval. 28 MCP tools is noise for this use case. |
| ClawMem | Most architecturally serious push solution, but relies on Claude Code hooks (PreToolUse/UserPromptSubmit) that don't exist in OpenCode. Would be first choice if primary host were Claude Code. |
| claude-mem | Same hook dependency problem. SQLite + Chroma storage is well-designed but hooks are the wrong abstraction for OpenCode. |
| context-mode | 11 MCP tools, FTS5 + BM25, but hook-based push doesn't apply to OpenCode. The ctx_search tool is useful but CodeGraph already covers that better with auto-sync. |

### Push mechanism — the OpenCode constraint

OpenCode does not support PreToolUse, SessionStart, or PostToolUse hooks. This is the defining constraint on the design.

**Push in OpenCode is approximated via:**
1. **System prompt instruction** in AGENTS.md — "Before any Edit or Write, call kbask.ask() with the file path and task description." Not true push, but trains the LLM to self-trigger retrieval.
2. **MCP server with file watcher** — a lightweight sidecar (kbask serve or CodeGraph daemon) that watches the filesystem and holds the latest graph in memory. When the LLM queries, it gets current data. The graph is always fresh because the watcher keeps it synced.
3. **Custom /sync-context command** — a user-invoked command that rebuilds both graphs and primes the context, for when the LLM forgets to self-trigger.

**In Claude Code**, true push is available via hooks. The design should still support it — the kbask MCP server and CodeGraph work identically regardless of host. Only the push trigger mechanism differs.

## Pull design (both hosts)

### Step 1: Install and configure MCP servers

```jsonc
// ~/.config/opencode/opencode.json — add to mcp section
"kbask": {
  "type": "local",
  "command": ["uvx", "--from", "git+https://github.com/sughosh-pocketfm/kbask", "kbask", "serve"],
  "timeout": 30000,
  "enabled": true
},
"codegraph": {
  "type": "local",
  "command": ["npx", "-y", "@colbymchenry/codegraph"],
  "timeout": 30000,
  "enabled": true
}
```

### Step 2: Build the graphs

```bash
# Structural graph (Graphify or CodeGraph — CodeGraph auto-syncs so it's always fresh)
codegraph init .
codegraph install --platform opencode    # wires MCP config

# Semantic graph (Understand-Anything — LLM-dependent, one-time build)
# Run in Claude Code: /understand
# Or use the installed plugin directly

# kbask meta-graph (combines both)
kbask update .
kbask install opencode --repo .           # wires slash command + MCP
```

### Step 3: AGENTS.md retrieval instructions

```markdown
## Knowledge Retrieval Protocol

Before editing a file or answering an architecture question:
1. Call `kbask.ask("<question>")` to get both structural and semantic context
2. If `_meta.tokens` suggests the result is thin, narrow with `codegraph explore <symbol>`
3. Only read source files directly if the graph returns insufficient context
4. After making changes, the LLM should NOT rebuild the graph — CodeGraph auto-syncs
```

## Push design

### For OpenCode (approximate push)

The AGENTS.md instruction above is the primary mechanism. To strengthen it:

**Custom /sync-context command:**
```markdown
# ~/.config/opencode/commands/sync-context.md
---
description: Rebuild knowledge graphs and inject context into the session
---
Rebuild the structural and semantic knowledge graphs for this project.
1. `codegraph init .` — re-index source files (fast, tree-sitter only)
2. `kbask update .` — mirror updated graphs into kbask-out/
3. Report: node count, edge count, communities found
```

**File-watcher sidecar (optional):**
A small PowerShell script that watches source files via .NET FileSystemWatcher and runs `kbask update .` on change. Output goes to kbask-out/ which the MCP server reads. The LLM always queries fresh data because the MCP server responds from disk.

```powershell
# watch-knowledge-graph.ps1
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = (Get-Location).Path
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true
$action = { & kbask update . 2>$null }
Register-ObjectEvent $watcher "Changed" -Action $action
# Run in background: Start-Process -NoNewWindow pwsh watch-knowledge-graph.ps1
```

### For Claude Code (true push via hooks)

Claude Code supports hooks that OpenCode doesn't. When the primary host is Claude Code:
- **kbask** MCP server responds to tools
- **CodeGraph** auto-syncs + PreToolUse hook nudges toward graph queries
- **ClawMem** context-surfacing hook on UserPromptSubmit for automatic wiki injection

This is the ideal push setup but requires Claude Code as the primary session host.

## The three-tier rollout

### Tier 1: Pull only (today, zero build)
1. Install CodeGraph via `npx -y @colbymchenry/codegraph`
2. Run `codegraph init . && codegraph install --platform opencode`
3. Add retrieval instructions to AGENTS.md
4. Install kbask via `uvx`
5. Build UA graph once in Claude Code: `/understand`
6. `kbask update .`
7. Wire both MCP servers in opencode.json

Cost: ~15 minutes. Result: LLM can call `kbask.ask()` and `codegraph explore` for JIT context.

### Tier 2: Approximate push (weekend project)
1. Build `/sync-context` command for OpenCode
2. Optional: file-watcher sidecar for auto-refresh
3. Strengthen AGENTS.md with retrieval-before-edit protocol
4. Wire CodeGraph auto-sync (it already watches files)

Cost: ~2-3 hours. Result: graph stays fresh, LLM has strong prompt-level retrieval discipline.

### Tier 3: True push (Claude Code host)
1. Install ClawMem or claude-mem for hook-driven context injection
2. Wire the kbask MCP server identically
3. Wire ClawMem vault as a write target for the wiki ingestion pipeline
4. Session-start onboarding via hooks

Cost: ~1 hour (Claude Code host + hooks already exist). Result: automatic context injection without LLM needing to ask.

## Key design decisions

**Why two MCP servers instead of one?** kbask depends on UA's knowledge graph which requires an LLM to build (expensive, manual trigger). CodeGraph auto-syncs on file change (zero LLM cost, always current). Running both means structural context is always fresh even when the semantic layer is stale. kbask's hybrid `ask()` tool degrades gracefully to graphify-only mode when UA is absent.

**Why CodeGraph over Graphify for structural?** Graphify requires a manual `/graphify` command to rebuild. CodeGraph auto-syncs via file watcher. For JIT retrieval, auto-sync is the difference between "query is current" and "query might be stale." Graphify's multi-modal strength (PDFs, images, video) is irrelevant for code-structure queries.

**Why not build a single combined MCP server?** kbask already exists, is MIT, and works. Forking or replacing it before proving the integration works is premature. Install it, use it, identify the gap, then decide whether to build.

## What remains unaddressed

- **Session memory persistence across restarts.** The graph survives but the LLM's in-context memory doesn't. ClawMem or claude-mem solve this via hooks, but only on Claude Code. OpenCode has no equivalent.
- **Wiki ingestion pipeline integration.** The existing YouTube→wiki pipeline produces pages in P:/.data/wiki/ that are indexed by QMD but not reflected in the kbask/CodeGraph graphs. A bridge script would need to run `kbask update .` after wiki ingest.
- **Cross-repo knowledge.** Both kbask and CodeGraph are per-repo. No current tool in this stack supports querying across multiple repos in a single call.
