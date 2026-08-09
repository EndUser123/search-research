---
title: "Claude Code Official Plugins Ecosystem"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, claude]
summary: >
  The claude-plugins-official ecosystem is a curated set of user-scoped Claude Code plugins authored primarily by Anthropic (with community contributions) that bundle together skills, agents, commands, and MCP integrations to extend Claude Code's capabilities. These plugins collectively cover reposito
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8df98abe-6541-4d68-8921-5d39149a838d" (Claude Code - Plugin Optimization and Workflow Guides, synced 2026-08-09)
  - "NotebookLM source 1bcaeb3e-b7b8-4779-8651-b62e4ef436d5" (_ claude-code-setup @ claude-plugins-official_ Sco.md, synced 2026-08-09)
  - "NotebookLM source 4098953c-537c-4a12-b30f-fc17bdf029b6" (semgrep @ claude-plugins-official_  Scope_ user.md, synced 2026-08-09)
  - "NotebookLM source 4d3954c7-ad41-44da-8677-19ddb2c2305c" (_ claude-md-management @ claude-plugins-official.md, synced 2026-08-09)
  - "NotebookLM source 51679eeb-5b18-4797-842d-6504985d986f" (serena @ claude-plugins-official_  Scope_ user_  S.md, synced 2026-08-09)
  - "NotebookLM source 5cb2127c-127f-4b03-be76-d63e7b1e81f1" (playground @ claude-plugins-official_  Scope_ user.md, synced 2026-08-09)
  - "NotebookLM source 7eb62f0d-42c0-49c1-9c48-a37f2ce885c2" (skill-creator @ claude-plugins-official_  Scope_ u.md, synced 2026-08-09)
  - "NotebookLM source 86d747f9-ea42-43ae-b240-7b1667ce8b27" (_ Persistent memory system for Claude Code - seaml.md, synced 2026-08-09)
  - "NotebookLM source 87781e16-5784-4a25-9c56-9a67f98acf11" (_ code-review @ claude-plugins-official_ Scope_ us.md, synced 2026-08-09)
  - "NotebookLM source 8b44c28d-6342-4cfe-a807-03f6ec0fefd4" (plugin-dev @ claude-plugins-official_  Scope_ user.md, synced 2026-08-09)
  - "NotebookLM source 8e9a722a-8178-4cdc-8929-40e485146bde" (_ claudit @ quickstop_ Scope_ user_ Version_ 1.0.0.md, synced 2026-08-09)
  - "NotebookLM source 91f050d4-ccf8-4b53-9759-1fc4925d38ea" (Merged Sources, synced 2026-08-09)
  - "NotebookLM source a5ba8d8d-acaa-44bf-b74c-6c313cbb3313" (frontend-design @ claude-plugins-official_  Scope_.md, synced 2026-08-09)
  - "NotebookLM source c073c4f3-b497-4dc4-b0bf-79843609bf40" (_  agent-sdk-dev @ claude-plugins-official_  Scope.md, synced 2026-08-09)
  - "NotebookLM source ca55faf9-9769-436f-9816-a5a2119ced22" (_ code-simplifier @ claude-plugins-official_ Scope.md, synced 2026-08-09)
  - "NotebookLM source f3b2e27b-8dbf-4ffb-a2f9-8c28aeb531b9" (_ context7 @ claude-plugins-official_ Scope_ user.md, synced 2026-08-09)
  - "NotebookLM source fb8a8fc5-a2f5-4f05-9df0-757e44a5b593" (_ feature-dev @ claude-plugins-official_ Scope_ us.md, synced 2026-08-09)
  - "NotebookLM source fcefc48f-e3a4-413e-8dda-a95e4180c62c" (pr-review-toolkit @ claude-plugins-official_  Scop.md, synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: claude-code-official-plugins-ecosystem
    - level: notebook
      id: 8df98abe-6541-4d68-8921-5d39149a838d
      title: Claude Code - Plugin Optimization and Workflow Guides
      url: https://notebooklm.google.com/notebook/8df98abe-6541-4d68-8921-5d39149a838d
    - level: cluster
      id: 0
      name: claude-code-plugins
relations:
  - target: wiki/concepts/skills.md
    type: related
  - target: wiki/concepts/subagents.md
    type: related
  - target: wiki/concepts/mcp-servers.md
    type: related
---

# Claude Code Official Plugins Ecosystem

## Decision context

**Definition:** The claude-plugins-official ecosystem is a curated set of user-scoped Claude Code plugins authored primarily by Anthropic (with community contributions) that bundle together skills, agents, commands, and MCP integrations to extend Claude Code's capabilities. These plugins collectively cover repository automation discovery, code review and PR analysis, security scanning, persistent memory, project memory maintenance, semantic LSP-based code analysis, frontend design, interactive playground generation, Agent SDK scaffolding, and meta-tooling for building new plugins.

Synthesized from **17 contributing transcripts** in NotebookLM notebook *Claude Code - Plugin Optimization and Workflow Guides*, clustered into the "claude-code-plugins" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Plugin inventory: claude-code-setup (claude-automation-recommender skill), semgrep, claude-md-management (revise-claude-md command + claude-md-improver skill), serena (LSP MCP server), playground (skill with templates), skill-creator, claude-mem (commands do/make-plan, mem-search skill, hooks), code-review (code-review command), plugin-dev (create-plugin command, agents agent-creator/plugin-validator/skill-reviewer, 7 skills), claudit (audit-ecosystem/global/project agents, research-core/ecosystem/optimization agents, claudit skill), frontend-design (skill), agent-sdk-dev (new-sdk-app command, agent-sdk-verifier-py/ts), code-simplifier (code-simplifier agent), context7 (Upstash MCP), feature-dev (feature-dev command, code-architect/code-explorer/code-reviewer agents), pr-review-toolkit (review-pr command, code-reviewer/code-simplifier/comment-analyzer/pr-test-analyzer/silent-failure-hunter/type-design-analyzer agents)
- Scope convention: most official plugins are installed at user scope so they apply across all projects.
- Plugin structure pattern: plugins contain a manifest (e.g., plugin.json) plus a combination of skills (SKILL.md with frontmatter), agents (.md), commands (slash-invoked), hooks, and MCP server configs.
- Composition pattern: plugins are designed to chain with each other - e.g., claudit pairs with code-review, plugin-dev pairs with claude-md-management, skill-creator pairs with plugin-dev.
- Repository breadth: the claude-plugins-official repo contains 264 files across multiple slices, covering official plugins (code-review, feature-dev, plugin-dev, frontend-design, hookify, ralph-loop, etc.), LSP integrations (pyright, rust-analyzer, typescript-lsp, swift-lsp, kotlin-lsp, clangd-lsp, gopls-lsp, jdtls-lsp, lua-lsp, ruby-lsp, php-lsp, csharp-lsp), mcp-server-dev, external_plugins (discord, imessage, telegram, fakechat, greptile), and utility plugins (commit-commands, code-simplifier, pr-review-toolkit, security-guidance, learning-output-style, explanatory-output-style, example-plugin, math-olympiad, agent-sdk-dev).
- Workflow integration: plugins are typically enabled via marketplace config (marketplace.json) and activated with /plugin, then invoked via slash commands or natural-language skill triggers within Claude Code sessions.

## Verifiable values

| Name | Value |
|---|---|
| feature-dev workflow phases | `7 phases: Discovery, Exploration, Questions, Design, Implement, Review, Summary` |
| feature-dev confidence threshold for review issues | `80%+ confidence` |
| code-review plugin confidence threshold | `80 confidence` |
| claude-mem SessionStart observation load | `last 50 observations (<200ms)` |
| claude-mem token savings from 3-layer MCP search | `~10x token savings` |
| CLAUDE.md recommended length | `100-200 lines max (claude-md-management); <700 words total across files (claudit)` |
| MCP server limit recommendation | `2-3 core MCP servers globally` |
| code-simplifier token reduction | `20-30%` |
| playground preset count per playground | `3-5 presets for 80% results` |
| serena supported languages | `30+ languages (e.g., Python, TypeScript, Rust)` |
| skill-creator iteration time | `15-30 minutes per skill` |
| claude-mem web viewer port | `localhost:37777` |
| skill-creator workflow speedup claim | `50-70% workflow speedups` |
| plugin-dev reported acceleration | `50-70% automation of custom skills` |

## Related concepts

- [[skills]] — Skills
- [[subagents]] — Subagents
- [[mcp-servers]] — MCP servers
- [[hooks]] — Hooks
- [[commands]] — Commands
- [[claude.md]] — CLAUDE.md
- [[plugin-marketplaces]] — plugin marketplaces
- [[lsp-integration]] — LSP integration
- [[semantic-code-analysis]] — semantic code analysis
- [[code-review-automation]] — code review automation
- [[security-scanning-(semgrep)]] — security scanning (Semgrep)
- [[persistent-memory]] — persistent memory
- [[agent-sdk]] — Agent SDK
- [[frontend-design-skill]] — frontend design skill

## Citations (from contributing transcripts)

- **Claim:** The claude-plugins-official repository slice structure contains 264 files covering official plugins, LSP integrations, MCP server dev, external plugins, and utility plugins.
  - Source: Merged Sources (`91f050d4-ccf8-4b53-9759-1fc4925d38ea`)
  - Context: Slice: claude-plugins-official part 1 of 264 files
- **Claim:** Most official plugins are authored by Anthropic and installed at user scope.
  - Source: _ claude-code-setup @ claude-plugins-official_ Sco.md (`1bcaeb3e-b7b8-4779-8651-b62e4ef436d5`)
  - Context: Author: Anthropic / Scope: user
- **Claim:** The claudit plugin includes audit-ecosystem, audit-global, audit-project, research-core, research-ecosystem, and research-optimization agents plus the claudit skill.
  - Source: _ claudit @ quickstop_ Scope_ user_ Version_ 1.0.0.md (`8e9a722a-8178-4cdc-8929-40e485146bde`)
  - Context: Agents: audit-ecosystem, audit-global, audit-project, research-core, research-ecosystem, research-optimization / Skills: claudit
- **Claim:** The pr-review-toolkit bundles six specialized review agents and a review-pr command.
  - Source: pr-review-toolkit @ claude-plugins-official_  Scop.md (`fcefc48f-e3a4-413e-8dda-a95e4180c62c`)
  - Context: Agents: code-reviewer, code-simplifier, comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer
- **Claim:** The plugin-dev toolkit bundles 7 skills plus 3 agents and the create-plugin command for building Claude Code plugins.
  - Source: plugin-dev @ claude-plugins-official_  Scope_ user.md (`8b44c28d-6342-4cfe-a807-03f6ec0fefd4`)
  - Context: Skills: agent-development, command-development, hook-development, mcp-integration, plugin-settings, plugin-structure, skill-development / Agents: agent-creator, plugin-validator, skill-reviewer / Commands: create-plugin
- **Claim:** The feature-dev plugin implements a 7-phase workflow using code-explorer, code-architect, and code-reviewer agents.
  - Source: _ feature-dev @ claude-plugins-official_ Scope_ us.md (`fb8a8fc5-a2f5-4f05-9df0-757e44a5b593`)
  - Context: Phase 1: Discovery ... Phase 7: Summary
- **Claim:** The claude-mem plugin provides commands do and make-plan, the mem-search skill, and hooks for Setup, SessionStart, UserPromptSubmit, PostToolUse, and Stop events.
  - Source: _ Persistent memory system for Claude Code - seaml.md (`86d747f9-ea42-43ae-b240-7b1667ce8b27`)
  - Context: Commands: do, make-plan / Skills: mem-search / Hooks: Setup,SessionStart,UserPromptSubmit,PostToolUse,Stop
- **Claim:** Serena provides LSP-based semantic code analysis as an MCP server supporting 30+ languages.
  - Source: serena @ claude-plugins-official_  Scope_ user_  S.md (`51679eeb-5b18-4797-842d-6504985d986f`)
  - Context: Semantic code analysis MCP server providing intelligent code understanding, refactoring suggestions, and codebase navigation through language server protocol integration.
- **Claim:** The semgrep plugin detects vulnerabilities in real-time after edits and injects best practices into Claude's prompts.
  - Source: semgrep @ claude-plugins-official_  Scope_ user.md (`4098953c-537c-4a12-b30f-fc17bdf029b6`)
  - Context: Semgrep catches security vulnerabilities in real-time and guides Claude to write secure code from the start.
- **Claim:** The claude-md-management plugin provides revise-claude-md command and claude-md-improver skill for maintaining CLAUDE.md files.
  - Source: _ claude-md-management @ claude-plugins-official.md (`4d3954c7-ad41-44da-8677-19ddb2c2305c`)
  - Context: Commands: revise-claude-md / Skills: claude-md-improver

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `8df98abe-6541-4d68-8921-5d39149a838d`
(cluster `claude-code-plugins`). No claims are made
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

- NotebookLM notebook [Claude Code - Plugin Optimization and Workflow Guides](https://notebooklm.google.com/notebook/8df98abe-6541-4d68-8921-5d39149a838d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
