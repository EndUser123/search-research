---
title: "OpenHands Skills and Plugins Architecture"
created: 2026-08-10
source: nlm-sync-2026-08-10
tags: [nlm-synced, reference, https]
summary: >
  OpenHands provides a public registry (OpenHands/extensions on GitHub) and SDK-level structures for distributing reusable agent components called skills and plugins. Skills are Markdown-based knowledge units that inject domain-specific guidance into an agent, while plugins bundle skills together with
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook c8b07a4c-607c-4ddc-94be-688206daf737" ([INGESTED] - Claude Code x NotebookLM x Obsidian Research, synced 2026-08-10)
  - "Best OpenHands Alternatives & Competitors - SourceForge" (https://sourceforge.net/software/product/OpenHands/alternatives, transcript synced 2026-08-10)
  - "Top 5 GitHub Repositories to get Free Claude Code Skills (1000+ Skills) - Analytics Vidhya" (https://www.analyticsvidhya.com/blog/2026/03/github-repositories-to-get-free-claude-code-skills/, transcript synced 2026-08-10)
  - "OpenHands/extensions: Public registry for OpenHands skills. - GitHub" (https://github.com/OpenHands/extensions, transcript synced 2026-08-10)
  - "The OpenHands Software Agent SDK: A Composable and Extensible Foundation for Production Agents - arXiv" (https://arxiv.org/html/2511.03690v1, transcript synced 2026-08-10)
  - "Plugins - OpenHands Docs" (https://docs.openhands.dev/sdk/guides/plugins, transcript synced 2026-08-10)
  - "OpenHands vs SWE-Agent: Best AI Coding Agent 2026 | Local AI Master" (https://localaimaster.com/blog/openhands-vs-swe-agent, transcript synced 2026-08-10)
  - "Building AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv" (https://arxiv.org/html/2603.05344v1, transcript synced 2026-08-10)
  - "Feature: OpenHands Coding Agent Skill — Model-Agnostic Sandboxed Code Agent Delegation · Issue #477 · NousResearch/hermes-agent - GitHub" (https://github.com/NousResearch/hermes-agent/issues/477, transcript synced 2026-08-10)
  - "How to Create Effective Agent Skills | Feb 27, 2026 - OpenHands" (https://openhands.dev/blog/20260227-creating-effective-agent-skills, transcript synced 2026-08-10)
provenance:
  chain:
    - level: concept
      id: openhands-skills-and-plugins-architecture
    - level: notebook
      id: c8b07a4c-607c-4ddc-94be-688206daf737
      title: [INGESTED] - Claude Code x NotebookLM x Obsidian Research
      url: https://notebooklm.google.com/notebook/c8b07a4c-607c-4ddc-94be-688206daf737
    - level: cluster
      id: 2
      name: https-openhands-github
    - level: source_url
      url: https://sourceforge.net/software/product/OpenHands/alternatives
      title: Best OpenHands Alternatives & Competitors - SourceForge
    - level: source_url
      url: https://www.analyticsvidhya.com/blog/2026/03/github-repositories-to-get-free-claude-code-skills/
      title: Top 5 GitHub Repositories to get Free Claude Code Skills (1000+ Skills) - Analytics Vidhya
    - level: source_url
      url: https://github.com/OpenHands/extensions
      title: OpenHands/extensions: Public registry for OpenHands skills. - GitHub
    - level: source_url
      url: https://arxiv.org/html/2511.03690v1
      title: The OpenHands Software Agent SDK: A Composable and Extensible Foundation for Production Agents - arXiv
    - level: source_url
      url: https://docs.openhands.dev/sdk/guides/plugins
      title: Plugins - OpenHands Docs
    - level: source_url
      url: https://localaimaster.com/blog/openhands-vs-swe-agent
      title: OpenHands vs SWE-Agent: Best AI Coding Agent 2026 | Local AI Master
    - level: source_url
      url: https://arxiv.org/html/2603.05344v1
      title: Building AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv
    - level: source_url
      url: https://github.com/NousResearch/hermes-agent/issues/477
      title: Feature: OpenHands Coding Agent Skill — Model-Agnostic Sandboxed Code Agent Delegation · Issue #477 · NousResearch/hermes-agent - GitHub
    - level: source_url
      url: https://openhands.dev/blog/20260227-creating-effective-agent-skills
      title: How to Create Effective Agent Skills | Feb 27, 2026 - OpenHands
relations:
  - target: wiki/concepts/openhands-software-agent-sdk.md
    type: related
  - target: wiki/concepts/model-context-protocol-(mcp)-integration.md
    type: related
  - target: wiki/concepts/agent-computer-interface-(swe-agent-aci).md
    type: related
---

# OpenHands Skills and Plugins Architecture

## Decision context

**Definition:** OpenHands provides a public registry (OpenHands/extensions on GitHub) and SDK-level structures for distributing reusable agent components called skills and plugins. Skills are Markdown-based knowledge units that inject domain-specific guidance into an agent, while plugins bundle skills together with executable hooks, MCP server configs, and slash commands under a single manifest.

Synthesized from **9 contributing transcripts** in NotebookLM notebook *[INGESTED] - Claude Code x NotebookLM x Obsidian Research*, clustered into the "https-openhands-github" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are stored one-per-directory under `skills/<skill-name>/` and require a `SKILL.md` file using AgentSkills-style progressive disclosure; an optional `README.md` provides human-facing notes. [Source 3]
- Plugins are stored one-per-directory under `plugins/<plugin-name>/`, require a `SKILL.md`, and may additionally include `hooks/` and `scripts/` directories. [Source 3]
- At the SDK level, a plugin's mandatory manifest is `.plugin.json` (name, version, description, author, license, repository), alongside `skills/`, `hooks/`, `agents/`, `.mcp.json`, and `README.md`. [Source 5]
- Skills defined via Markdown files use YAML frontmatter to specify triggers such as keyword matching (e.g., `keywords: [lint, linting, code quality]`). [Source 5]
- Hooks are defined in `hooks.json` and map event matchers (e.g., `PostToolUse` with `matcher: file_editor`) to command-type handlers with timeout support. [Source 5]
- Plugins can be installed from local paths, GitHub shorthand (`github:owner/repo`), full Git URLs pinned to branches/tags/SHAs, or subdirectories of a monorepo. [Source 5]
- Plugin lifecycle is managed via functions `install_plugin`, `list_installed_plugins`, `load_installed_plugins` (enabled only), `disable_plugin`, `enable_plugin`, and `uninstall_plugin`, with persistence through a `.installed.json` file holding source, version, and an `enabled` boolean per plugin. [Source 5]
- Skills can be injected at the agent level via `AgentContext(skills=...)`, MCP configurations via `Agent(mcp_config=...)`, and hooks via `Conversation(hook_config=...)`. [Source 5]
- The repository `AGENTS.md` defines the rules any agent must follow when editing or adding skills and plugins; the registry is MIT-licensed. [Source 3]
- Beyond the registry, OpenHands SDK exposes skills as 'modular knowledge units loaded on-demand based on metadata discovery' to prevent context bloat. [Source 7]
- In the broader Claude Code ecosystem, third-party repositories such as alirezarezvani/claude-skills (200+), VoltAgent/awesome-agent-skills (200+), sickn33/antigravity-skills (1200+), and ComposioHQ/awesome-claude-skills (1000+) distribute compatible skills, many of which also work with OpenAI Codex, Gemini CLI, Cursor, and Copilot. [Source 2]
- The official Anthropic reference repository anthropics/skills ships 17 official skills oriented around document creation workflows. [Source 2]

## Verifiable values

| Name | Value |
|---|---|
| Official skills in anthropics/skills | `17` |
| Skills in alirezarezvani/claude-skills | `200+` |
| Skills in VoltAgent/awesome-agent-skills | `200+` |
| Skills in sickn33/antigravity-skills | `1200+` |
| Skills in ComposioHQ/awesome-claude-skills | `1000+` |
| OpenHands/extensions license | `MIT` |
| Required plugin manifest | `.plugin.json (name, version, description, author, license, repository)` |
| Persistence file for installed plugins | `.installed.json` |

## Related concepts

- [[openhands-software-agent-sdk]] — OpenHands Software Agent SDK
- [[model-context-protocol-(mcp)-integration]] — Model Context Protocol (MCP) integration
- [[agent-computer-interface-(swe-agent-aci)]] — Agent-Computer Interface (SWE-Agent ACI)
- [[claude-code-skills-ecosystem]] — Claude Code Skills ecosystem
- [[event-sourced-agent-state-management]] — Event-sourced agent state management
- [[sandboxed-code-execution-backends]] — Sandboxed code execution backends

## Citations (from contributing transcripts)

- **Claim:** OpenHands/extensions is a public registry of skills and plugins using SKILL.md, hooks/, and scripts/ directories, governed by AGENTS.md and MIT-licensed.
  - Source: OpenHands/extensions: Public registry for OpenHands skills. - GitHub (`4cb66266-5bae-435f-ac7d-ac9674a4d3a5`)
  - Context: OpenHands/extensions is a public registry for OpenHands extensions, containing reusable and shareable skills and plugins designed to customize agent behavior.
- **Claim:** Plugins bundle skills, hooks, MCP servers, and commands under a `.plugin.json` manifest and can be installed from local paths, GitHub shorthand, Git URLs, or monorepo subdirectories.
  - Source: Plugins - OpenHands Docs (`6b3a265d-1131-479c-b2de-6990d8e7b9e9`)
  - Context: Plugins: Reusable packages that bundle and distribute multiple agent components (skills, hooks, MCP servers, and commands) to extend agent capabilities.
- **Claim:** Skills use Markdown with YAML frontmatter to specify keyword triggers such as `lint`, `linting`, `code quality`.
  - Source: Plugins - OpenHands Docs (`6b3a265d-1131-479c-b2de-6990d8e7b9e9`)
  - Context: trigger: type: keyword keywords: - lint - linting - code quality
- **Claim:** Hooks.json binds event matchers like `PostToolUse` on `file_editor` to command-type handlers with timeout support.
  - Source: Plugins - OpenHands Docs (`6b3a265d-1131-479c-b2de-6990d8e7b9e9`)
  - Context: "PostToolUse": [ { "matcher": "file_editor", "hooks": [ { "type": "command", "command": "echo 'File edited: $OPENHANDS_TOOL_NAME'", "timeout": 5 } ] } ]
- **Claim:** Plugin state persistence is a `.installed.json` file storing source, version, and `enabled` flag for each plugin.
  - Source: Plugins - OpenHands Docs (`6b3a265d-1131-479c-b2de-6990d8e7b9e9`)
  - Context: Plugin state is maintained via a `.installed.json` file located within the specified `installed_dir`. This file stores metadata including the source, version, and a boolean `enabled` flag for each tracked plugin.
- **Claim:** Skills can be injected via `AgentContext(skills=...)`, MCP via `Agent(mcp_config=...)`, and hooks via `Conversation(hook_config=...)`.
  - Source: Plugins - OpenHands Docs (`6b3a265d-1131-479c-b2de-6990d8e7b9e9`)
  - Context: Skills can be injected into an `AgentContext` via the `skills` parameter, and MCP configurations can be passed to an `Agent` via the `mcp_config` parameter. Hooks can be passed to a `Conversation` via `hook_config`.
- **Claim:** Skills are modular knowledge units (Markdown files) loaded on-demand via metadata discovery to prevent context bloat.
  - Source: Building AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv (`a8bcc54f-2885-4a77-96db-7af913e04077`)
  - Context: Skills are modular knowledge units (Markdown files) that are loaded on-demand based on metadata discovery, preventing context bloat.
- **Claim:** anthropics/skills ships 17 official skills as the canonical starting point for Claude Code skills.
  - Source: Top 5 GitHub Repositories to get Free Claude Code Skills (1000+ Skills) - Analytics Vidhya (`17d2319c-ba91-41f6-820f-24f55574fa77`)
  - Context: anthropics/skills is the official GitHub starting point for Claude Code skills. It contains 17 official skills for document creation workflows.
- **Claim:** alirezarezvani/claude-skills provides 200+ production-ready skills compatible with Claude, OpenAI Codex, Gemini CLI, OpenClaude, and Cursor.
  - Source: Top 5 GitHub Repositories to get Free Claude Code Skills (1000+ Skills) - Analytics Vidhya (`17d2319c-ba91-41f6-820f-24f55574fa77`)
  - Context: alirezarezvani/claude-skills provides over 200 production-ready skills compatible with multiple AI tools, including Claude, OpenAI Codex, Gemini CLI, OpenClaude, and Cursor.
- **Claim:** sickn33/antigravity-skills contains 1200+ skills compatible with Claude, Copilot, and Gemini CLI.
  - Source: Top 5 GitHub Repositories to get Free Claude Code Skills (1000+ Skills) - Analytics Vidhya (`17d2319c-ba91-41f6-820f-24f55574fa77`)
  - Context: sickn33/antigravity-skills is a massive library with 1200+ skills covering a wide range of use cases and is compatible with Claude, Copilot, and Gemini CLI.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `c8b07a4c-607c-4ddc-94be-688206daf737`
(cluster `https-openhands-github`). No claims are made
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

- NotebookLM notebook [[INGESTED] - Claude Code x NotebookLM x Obsidian Research](https://notebooklm.google.com/notebook/c8b07a4c-607c-4ddc-94be-688206daf737)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
