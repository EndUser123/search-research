---
title: "Claude Code Configuration Patterns"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, claude]
summary: >
  A cluster of design patterns for configuring Claude Code: MCP server setup, worktree-based parallel sessions, lifecycle event hooks, and enterprise gateway governance. The sources describe these as infrastructure layers that turn Claude Code from a conversational assistant into a controllable, paral
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook afd2f1dd-ff64-44f7-9259-6f923b6c081a" (Claude Code Worktree Guide: Hooks, Setup, and Parallel Workflows, synced 2026-08-09)
  - "Claude Code MCP Setup: A Practical 2026 Guide - Nimbalyst" (https://nimbalyst.com/blog/claude-code-mcp-setup/, transcript synced 2026-08-09)
  - "How to Use MCP Servers with Claude Code to Read and Write Data in Your Apps" (https://www.mindstudio.ai/blog/how-to-use-mcp-servers-with-claude-code, transcript synced 2026-08-09)
  - "Controlling Claude Code in the Enterprise: MCP Tool Scoping and Audit Trails - Truefoundry" (https://www.truefoundry.com/blog/claude-code-enterprise-mcp-gateway, transcript synced 2026-08-09)
  - "The Claude Code Git Worktree Pattern: A Primer for Builders - MindStudio" (https://www.mindstudio.ai/blog/what-is-claude-code-git-worktree-pattern-parallel-feature-branches, transcript synced 2026-08-09)
  - "Claude Code Hooks Explained: How Pre-Session and Post-Compaction Hooks Keep Your Agent on Track | MindStudio" (https://www.mindstudio.ai/blog/claude-code-hooks-pre-session-post-compaction-explained, transcript synced 2026-08-09)
  - "Claude Code Hooks: 18 Lifecycle Events Most Users Have Never Touched — and How to Use Them | MindStudio" (https://www.mindstudio.ai/blog/claude-code-hooks-18-lifecycle-events-most-users-never-touched-how-to-use-them, transcript synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: claude-code-configuration-patterns
    - level: notebook
      id: afd2f1dd-ff64-44f7-9259-6f923b6c081a
      title: Claude Code Worktree Guide: Hooks, Setup, and Parallel Workflows
      url: https://notebooklm.google.com/notebook/afd2f1dd-ff64-44f7-9259-6f923b6c081a
    - level: cluster
      id: 1
      name: claude-code-cookies
    - level: source_url
      url: https://nimbalyst.com/blog/claude-code-mcp-setup/
      title: Claude Code MCP Setup: A Practical 2026 Guide - Nimbalyst
    - level: source_url
      url: https://www.mindstudio.ai/blog/how-to-use-mcp-servers-with-claude-code
      title: How to Use MCP Servers with Claude Code to Read and Write Data in Your Apps
    - level: source_url
      url: https://www.truefoundry.com/blog/claude-code-enterprise-mcp-gateway
      title: Controlling Claude Code in the Enterprise: MCP Tool Scoping and Audit Trails - Truefoundry
    - level: source_url
      url: https://www.mindstudio.ai/blog/what-is-claude-code-git-worktree-pattern-parallel-feature-branches
      title: The Claude Code Git Worktree Pattern: A Primer for Builders - MindStudio
    - level: source_url
      url: https://www.mindstudio.ai/blog/claude-code-hooks-pre-session-post-compaction-explained
      title: Claude Code Hooks Explained: How Pre-Session and Post-Compaction Hooks Keep Your Agent on Track | MindStudio
    - level: source_url
      url: https://www.mindstudio.ai/blog/claude-code-hooks-18-lifecycle-events-most-users-never-touched-how-to-use-them
      title: Claude Code Hooks: 18 Lifecycle Events Most Users Have Never Touched — and How to Use Them | MindStudio
relations:
  - target: wiki/concepts/model-context-protocol.md
    type: related
  - target: wiki/concepts/claude.md-identity-document.md
    type: related
  - target: wiki/concepts/claude-code-skills-and-sub-agents.md
    type: related
---

# Claude Code Configuration Patterns

## Decision context

**Definition:** A cluster of design patterns for configuring Claude Code: MCP server setup, worktree-based parallel sessions, lifecycle event hooks, and enterprise gateway governance. The sources describe these as infrastructure layers that turn Claude Code from a conversational assistant into a controllable, parallelizable, governed agent.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *Claude Code Worktree Guide: Hooks, Setup, and Parallel Workflows*, clustered into the "claude-code-cookies" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The Model Context Protocol (MCP) lets Claude Code call external tools through configured servers; each server exposes a name, description, and JSON-schema arguments. Claude Code discovers these tools at startup and can call them during a session.
- MCP configuration lives at two scopes: user-level in ~/.claude/settings.json (available to every session) and project-level in .claude/settings.json inside the repo (overrides user scope, useful for team-shared tools).
- MCP servers run as subprocesses and talk over stdio (local) or HTTP (remote). Common practical servers include GitHub, Slack, Linear, Postgres, Playwright, Notion, HubSpot, and Gmail/Google Workspace.
- Each MCP server entry needs a command (how to launch), args (extra parameters), and env (where API keys/tokens live); npm-distributed servers typically use npx -y @scope/name. Tokens should not be committed to the repo.
- Tool name collisions occur when two MCP servers expose the same tool name; Claude Code will prefer one and ignore the other. The tools field in server config can rename or filter tools.
- The git worktree pattern uses Claude Code's -w flag to wrap a task in its own isolated git worktree; each session gets its own branch and directory, enabling multiple parallel sessions with separate file state.
- Worktree sessions do not share node_modules or build artifacts; each new worktree requires dependency installation. Two worktrees cannot check out the same branch simultaneously.
- Practical guidance from the worktree source is to run 2-4 parallel sessions at a time; more than that hits API rate limits and overwhelms review. Branches persist after the session ends for review/merge via standard git operations.
- Claude Code exposes 18+ lifecycle event hooks (session start, post-compaction, pre-response, post-response, pre/post tool call, etc.). Hooks are deterministic event triggers that fire regardless of model behavior.
- The pre-session injection hook fires before any user input and is typically used to inject CLAUDE.md content or dynamic context (e.g., Obsidian files relevant to the current project folder).
- The post-compaction hook fires immediately after Claude Code's automatic context compression, reinserting identity/rules so the agent does not drift from its original configuration across long sessions.
- Hooks are typically shell scripts or programs that output text injected into context; Claude Code's built-in 'Claude Code guide' sub-agent can generate hook configurations from a natural-language description.
- For enterprise deployments, a gateway sits between Claude Code and internal MCP servers; policies (Cedar or OPA) are evaluated against JWT claims from the corporate IdP and enforced at the Pre-Tool hook with default-deny semantics.
- The TrueFoundry gateway uses a sliding-window token-bucket rate limiter (60s window, twelve 5s buckets) applied at the tool-call layer rather than the prompt layer; per-developer and per-project limits are expressible in YAML.
- Audit logs from the gateway contain timestamp, SSO-resolved identity, target MCP server and tool, redacted parameters, policy decision, and a trace ID linking the tool call to the originating LLM generation; logs flow into ClickHouse then to a SIEM.
- Anomaly detection runs downstream of the audit log on aggregated metrics (invocations-per-minute, distinct-tools-per-hour, payload-size distribution) using a rolling z-score; above threshold the developer's agent loop is quarantined.

## Verifiable values

| Name | Value |
|---|---|
| MCP user-scope config path | `~/.claude/settings.json` |
| MCP project-scope config path | `.claude/settings.json` |
| Claude Code hook event types | `18+ lifecycle events` |
| Git worktree support minimum | `Git 2.5+` |
| Recommended parallel worktree sessions | `2-4 sessions` |
| Worktree config example | `{"worktree":{"prefix":"claude","base_branch":"main","auto_cleanup":false}}` |
| TrueFoundry gateway per-pod throughput | `~250 RPS per single-CPU pod (documented)` |
| TrueFoundry rate-limit sliding window | `60s window made of 12 x 5s buckets` |
| Example per-developer daily token cap | `1,000,000 tokens_per_day` |
| Example user-model minute cap | `200 requests_per_minute` |
| Example per-project hourly token cap | `50,000 tokens_per_hour` |
| Gateway control-plane reconcile interval | `10 minutes` |
| MCP server token overhead vs CLI tools (Kashef benchmark cited) | `35x more tokens` |

## Related concepts

- [[model-context-protocol]] — Model Context Protocol
- [[claude.md-identity-document]] — CLAUDE.md identity document
- [[claude-code-skills-and-sub-agents]] — Claude Code skills and sub-agents
- [[cedar-/-opa-policy-engines]] — Cedar / OPA policy engines
- [[git-worktree]] — Git worktree
- [[oauth/oidc-sso-and-jwt-based-authorization]] — OAuth/OIDC SSO and JWT-based authorization
- [[claude-code-/compact-command]] — Claude Code /compact command
- [[clickhouse-audit-pipeline]] — ClickHouse audit pipeline

## Citations (from contributing transcripts)

- **Claim:** MCP is a small protocol published by Anthropic in 2024 where each server exposes tools with a name, description, and JSON schema, and the protocol runs over stdio or HTTP.
  - Source: Claude Code MCP Setup: A Practical 2026 Guide - Nimbalyst (`2931b014-cdcb-4cc0-acb0-5183b34b30af`)
  - Context: MCP is a small protocol with a big payoff. Anthropic published the spec in 2024 and the ecosystem has compounded since. The mental model: A server is a process that exposes tools. Each tool has a name, a description, and a JSON schema for arguments.
- **Claim:** MCP configuration is read from ~/.claude/settings.json (user) and .claude/settings.json (project), with project scope overriding user scope.
  - Source: Claude Code MCP Setup: A Practical 2026 Guide - Nimbalyst (`2931b014-cdcb-4cc0-acb0-5183b34b30af`)
  - Context: Claude Code reads MCP configuration from two places. User scope: ~/.claude/settings.json . Project scope: .claude/settings.json in the project root. Project scope overrides user scope.
- **Claim:** Claude Code launches local MCP servers as subprocesses over stdio; remote servers run over HTTP.
  - Source: Claude Code MCP Setup: A Practical 2026 Guide - Nimbalyst (`2931b014-cdcb-4cc0-acb0-5183b34b30af`)
  - Context: The protocol runs over stdio or HTTP. Claude Code launches local servers as subprocesses and talks to them over stdio. Remote servers run over HTTP.
- **Claim:** When two MCP servers expose tools with the same name, Claude Code prefers one and ignores the other; the tools field can rename or filter.
  - Source: Claude Code MCP Setup: A Practical 2026 Guide - Nimbalyst (`2931b014-cdcb-4cc0-acb0-5183b34b30af`)
  - Context: If two MCP servers expose tools with the same name, Claude Code will prefer one and ignore the other. The tools field in the server config can rename or filter tools.
- **Claim:** The git worktree pattern uses Claude Code's -w flag so each session runs in its own isolated branch and working directory, enabling parallel sessions without file-state interference.
  - Source: The Claude Code Git Worktree Pattern: A Primer for Builders - MindStudio (`85540123-43a7-4996-b8b4-1b6d116ee19e`)
  - Context: Using the -w flag, Claude Code creates isolated git worktrees — separate working directories tied to individual branches — so you can run multiple parallel Claude sessions without them stepping on each other.
- **Claim:** Git worktree support requires Git 2.5+ and a repository with at least one commit; two worktrees cannot check out the same branch simultaneously.
  - Source: The Claude Code Git Worktree Pattern: A Primer for Builders - MindStudio (`85540123-43a7-4996-b8b4-1b6d116ee19e`)
  - Context: Git 2.5+ — Worktree support was introduced in Git 2.5… Git won't let two worktrees check out the same branch simultaneously.
- **Claim:** Claude Code fires hooks at 18+ lifecycle events; hooks are deterministic event triggers that run code regardless of model behavior.
  - Source: Claude Code Hooks Explained: How Pre-Session and Post-Compaction Hooks Keep Your Agent on Track | MindStudio (`9310f0df-f5c9-4c2a-9963-f0312ee5ad13`)
  - Context: Mark Kashef… describes it plainly: a hook is an event that will always fire at one of 18+ events that happen in Claude Code. Not "might fire." Not "fires if the model remembers." Always fires.
- **Claim:** The pre-session injection hook fires at the start of every session and is used to inject CLAUDE.md or dynamic context (e.g., Obsidian files relevant to the project folder).
  - Source: Claude Code Hooks Explained: How Pre-Session and Post-Compaction Hooks Keep Your Agent on Track | MindStudio (`9310f0df-f5c9-4c2a-9963-f0312ee5ad13`)
  - Context: What you put here gets injected into the context before the model sees any user input. The typical use case: inject your CLAUDE.md content, or a condensed version of it, so the agent starts every session with full context.
- **Claim:** The post-compaction hook reinserts the identity document after Claude Code's automatic context compression so the agent does not drift across long sessions.
  - Source: Claude Code Hooks Explained: How Pre-Session and Post-Compaction Hooks Keep Your Agent on Track | MindStudio (`9310f0df-f5c9-4c2a-9963-f0312ee5ad13`)
  - Context: The post-compaction hook fires immediately after Claude Code runs its context compression. That's the exact moment when your agent's identity is most at risk of being lost. The hook fires, and you can use it to reinsert your core identity document.
- **Claim:** Claude Code has no native enterprise controls; an agent with access to a postgres-mcp-server can issue DROP TABLE if the credentials allow it.
  - Source: Controlling Claude Code in the Enterprise: MCP Tool Scoping and Audit Trails - Truefoundry (`6a2e237b-5902-43b5-a2cb-981573b62d04`)
  - Context: Hand it an MCP server configuration and it assumes total authority over every tool that server exposes. Stand up a postgres-mcp-server so agents can query staging data, and there is no built-in mechanism to prevent an overconfident agent… from issuing DROP TABLE if the underlying credentials allow it.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `afd2f1dd-ff64-44f7-9259-6f923b6c081a`
(cluster `claude-code-cookies`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Claude Code Worktree Guide: Hooks, Setup, and Parallel Workflows](https://notebooklm.google.com/notebook/afd2f1dd-ff64-44f7-9259-6f923b6c081a)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
