---
title: "Claude Code HTTPS Documentation Site"
created: 2026-08-11
source: nlm-sync-2026-08-11
tags: [nlm-synced, reference, claude]
summary: >
  The Claude Code documentation site is served over HTTPS at `https://code.claude.com/docs/`, with a machine-readable index at `https://code.claude.com/docs/llms.txt` for programmatic discovery of all available pages. The Skills documentation page lives at `https://code.claude.com/docs/en/skills` with
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook 4017aa6e-35fb-426d-bc53-34620bec405e" ([INGESTED] - Claude Code Guide: Production Hooks and Agent Skills, synced 2026-08-11)
  - "Extend Claude with skills - Claude Code Docs" (https://code.claude.com/docs/en/skills, transcript synced 2026-08-11)
  - "Best practices for Claude Code - Claude Code Docs" (https://code.claude.com/docs/en/best-practices, transcript synced 2026-08-11)
  - "Manage sessions - Claude Code Docs" (https://code.claude.com/docs/en/sessions, transcript synced 2026-08-11)
  - "Claude Code JSONL transcript format explained" (https://claude-dev.tools/docs/jsonl-format, transcript synced 2026-08-11)
  - "Claude Code Ignores Your CLAUDE.md? It's the Delivery Mechanism, Not a Bug (2026 Fix)" (https://www.shareuhack.com/en/posts/claude-code-claude-md-setup-guide-2026, transcript synced 2026-08-11)
  - "Anatomy of the .claude Folder - Every File Explained (2026) - codewithmukesh" (https://codewithmukesh.com/blog/anatomy-of-the-claude-folder/, transcript synced 2026-08-11)
  - "Claude Code Source Code Deep Research Report" (https://claudeai.dev/docs/mechanics/development/claude-code-source-deep-research/, transcript synced 2026-08-11)
  - "Claude Code Hooks: Complete Guide to All 12 Lifecycle Events" (https://claudefa.st/blog/tools/hooks/hooks-guide, transcript synced 2026-08-11)
  - "Claude Code Stop Hook: Force Task Completion" (https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement, transcript synced 2026-08-11)
  - "Hooks reference - Claude Code Docs" (https://code.claude.com/docs/en/hooks, transcript synced 2026-08-11)
provenance:
  chain:
    - level: concept
      id: claude-code-https-documentation-site
    - level: notebook
      id: 4017aa6e-35fb-426d-bc53-34620bec405e
      title: [INGESTED] - Claude Code Guide: Production Hooks and Agent Skills
      url: https://notebooklm.google.com/notebook/4017aa6e-35fb-426d-bc53-34620bec405e
    - level: cluster
      id: 1
      name: claude-code-https
    - level: source_url
      url: https://code.claude.com/docs/en/skills
      title: Extend Claude with skills - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/best-practices
      title: Best practices for Claude Code - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/sessions
      title: Manage sessions - Claude Code Docs
    - level: source_url
      url: https://claude-dev.tools/docs/jsonl-format
      title: Claude Code JSONL transcript format explained
    - level: source_url
      url: https://www.shareuhack.com/en/posts/claude-code-claude-md-setup-guide-2026
      title: Claude Code Ignores Your CLAUDE.md? It's the Delivery Mechanism, Not a Bug (2026 Fix)
    - level: source_url
      url: https://codewithmukesh.com/blog/anatomy-of-the-claude-folder/
      title: Anatomy of the .claude Folder - Every File Explained (2026) - codewithmukesh
    - level: source_url
      url: https://claudeai.dev/docs/mechanics/development/claude-code-source-deep-research/
      title: Claude Code Source Code Deep Research Report
    - level: source_url
      url: https://claudefa.st/blog/tools/hooks/hooks-guide
      title: Claude Code Hooks: Complete Guide to All 12 Lifecycle Events
    - level: source_url
      url: https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement
      title: Claude Code Stop Hook: Force Task Completion
    - level: source_url
      url: https://code.claude.com/docs/en/hooks
      title: Hooks reference - Claude Code Docs
relations:
  - target: wiki/concepts/claude-code-skills-(skill.md-system).md
    type: related
  - target: wiki/concepts/agent-skills-open-standard-(agentskills.io).md
    type: related
  - target: wiki/concepts/claude-code-mcp-documentation.md
    type: related
---

# Claude Code HTTPS Documentation Site

## Decision context

**Definition:** The Claude Code documentation site is served over HTTPS at `https://code.claude.com/docs/`, with a machine-readable index at `https://code.claude.com/docs/llms.txt` for programmatic discovery of all available pages. The Skills documentation page lives at `https://code.claude.com/docs/en/skills` with section anchors (e.g., `#bundled-skills`, `#getting-started`), and cross-referenced documentation includes agents, sub-agents, MCP, hooks, permissions, and settings pages under the same `/docs/en/` path.

Synthesized from **10 contributing transcripts** in NotebookLM notebook *[INGESTED] - Claude Code Guide: Production Hooks and Agent Skills*, clustered into the "claude-code-https" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Documentation index URL: `https://code.claude.com/docs/llms.txt` provides a machine-readable complete documentation index for programmatic discovery.
- Skills documentation root URL: `https://code.claude.com/docs/en/skills` with section anchors such as `#bundled-skills`, `#run-and-verify-your-app`, `#getting-started`, and `#create-your-first-skill`; the full anchorable URL pattern is `https://code.claude.com/docs/en/skills#content-area`.
- Cross-referenced documentation paths all hosted under `https://code.claude.com/docs/en/`: agents, sub-agents, MCP, hooks-guide, permissions, and settings.
- The Skills system (described at this URL) is the canonical way to extend Claude Code capabilities: a `SKILL.md` file with YAML frontmatter between `---` markers and markdown instructions defines a skill that Claude can invoke automatically or via `/skill-name`.
- Skills follow the open Agent Skills standard at `https://agentskills.io/`, with Claude Code extending the standard with invocation control, subagent execution, and dynamic context injection.
- Documentation site top-level sections include: Getting started, Build with Claude Code, Administration, Configuration, Reference, Agent SDK, What's New, and Resources, with sub-sections for Agents and parallel work (workflows, worktrees), MCP, Skills, Plugins, Artifacts, Automation (hooks, channels, scheduled tasks), Goals, Programmatic usage (headless, deep-links), Guides (monorepos), and Troubleshooting.
- The hint `claude-code-https` matches the documentation site's HTTPS-served nature rather than any HTTPS-specific Claude Code feature; one source (a deep-research report on Claude Code's source code) explicitly notes the topic hint does not match the actual content since no HTTPS-specific information is present in that report.

## Verifiable values

| Name | Value |
|---|---|
| Documentation site root URL | `https://code.claude.com/docs/` |
| Documentation index URL | `https://code.claude.com/docs/llms.txt` |
| Skills page root URL | `https://code.claude.com/docs/en/skills` |
| Skills page anchorable URL | `https://code.claude.com/docs/en/skills#content-area` |
| Skills standard URL | `https://agentskills.io/` |
| Skill description per-skill cap in listing | `250 characters` |
| Skill listing budget fraction | `1% of the model's context window` |
| Skill listing fallback character budget | `8,000 characters` |
| Skill listing budget override env var | `SLASH_COMMAND_TOOL_CHAR_BUDGET` |
| Skill description listing truncation threshold | `1,536 characters (combined description + when_to_use)` |
| Skill directory naming constraints | `lowercase letters, numbers, hyphens only; max 64 characters` |
| Skill re-attachment per-skill token cap | `5,000 tokens (first 5,000 of most recent invocation kept)` |
| Skill re-attachment combined budget | `25,000 tokens across re-attached skills` |
| Auto-memory MEMORY.md cap | `first 200 lines OR 25KB, whichever comes first` |
| @import recursion depth limit | `5 hops` |
| Stop hook default timeout | `60 seconds` |
| HTTP hook default timeout | `600 seconds (10 minutes)` |
| UserPromptSubmit timeout (HTTP hooks) | `30 seconds` |
| MessageDisplay timeout (HTTP hooks) | `10 seconds` |
| Hook output string cap | `10,000 characters (excess saved to file with preview)` |
| HTTP hooks minimum Claude Code version | `February 2026 (introduced)` |
| Async hooks minimum Claude Code version | `January 2026` |
| Transcripts default retention (cleanupPeriodDays) | `30 days` |
| Skills system minimum version for bundled run-and-verify skills (/run, /verify, /run-skill-generator) | `v2.1.145` |
| Skills stacking introduced | `v2.1.199 (up to first skill plus 5 stacked)` |
| ${CLAUDE_PROJECT_DIR} substitution introduced | `v2.1.196` |
| Auto-compaction re-attachment introduced | `v2.1.198 (named branches after compaction)` |
| Hook /cd behavior stabilized | `v2.1.169 (session relocates cleanly) and v2.1.196 (stays out of old directory's picker after crash/forced exit)` |
| Default session display name requires | `v2.1.196+` |

## Related concepts

- /claude-code-skills-(skill.md-system) — Claude Code Skills (SKILL.md system)
- /agent-skills-open-standard-(agentskills.io) — Agent Skills open standard (agentskills.io)
- /claude-code-mcp-documentation — Claude Code MCP documentation
- /claude-code-hooks-guide — Claude Code Hooks Guide
- /claude-code-permissions-documentation — Claude Code Permissions documentation
- /claude-code-settings-documentation — Claude Code Settings documentation
- /claude-code-agents-documentation — Claude Code Agents documentation
- /claude-code-sub-agents-documentation — Claude Code Sub-agents documentation
- /claude-code-jsonl-transcript-format — Claude Code JSONL transcript format
- /claude-code-session-management — Claude Code session management
- /claude-code-plugins-system — Claude Code Plugins system
- /http-hooks-(post-based-hook-handler-type) — HTTP hooks (POST-based hook handler type)
- /stop-hook-(task-enforcement-pattern) — Stop hook (task enforcement pattern)
- /claude.md-delivery-semantics — CLAUDE.md delivery semantics
- /subagent-fork-semantics — Subagent fork semantics
- /prompt-cache-boundary-(system_prompt_dynamic_boundary) — Prompt cache boundary (SYSTEM_PROMPT_DYNAMIC_BOUNDARY)
- /memory-directory-(memdir)-and-auto-memory — Memory directory (memdir) and auto-memory

## Citations (from contributing transcripts)

- **Claim:** The documentation is served over HTTPS at code.claude.com/docs with a machine-readable index at code.claude.com/docs/llms.txt
  - Source: Extend Claude with skills - Claude Code Docs (`37f17108-b215-4776-b9e7-ba19467ab615`)
  - Context: All Skills documentation is hosted under the https://code.claude.com/docs/en/ path
- **Claim:** The Skills documentation page URL is https://code.claude.com/docs/en/skills with section anchors such as #bundled-skills and #getting-started
  - Source: Extend Claude with skills - Claude Code Docs (`37f17108-b215-4776-b9e7-ba19467ab615`)
  - Context: The Skills documentation page URL is https://code.claude.com/docs/en/skills#content-area (or https://code.claude.com/docs/en/skills for the page root), with anchor links for each section (e.g., #bundled-skills, #run-and-verify-your-app, #getting-started, #create-your-first-skill)
- **Claim:** Cross-referenced documentation paths include agents, sub-agents, MCP, hooks-guide, permissions, and settings all under /docs/en/
  - Source: Extend Claude with skills - Claude Code Docs (`37f17108-b215-4776-b9e7-ba19467ab615`)
  - Context: All Skills documentation is hosted under the https://code.claude.com/docs/en/ path; cross-referenced documentation includes https://code.claude.com/docs/en/agents, https://code.claude.com/docs/en/sub-agents, https://code.claude.com/docs/en/mcp, https://code.claude.com/docs/en/hooks-guide, https://code.claude.com/docs/en/permissions, and https://code.claude.com/docs/en/settings
- **Claim:** Skills follow the open Agent Skills standard at https://agentskills.io/, with Claude Code extending it
  - Source: Extend Claude with skills - Claude Code Docs (`37f17108-b215-4776-b9e7-ba19467ab615`)
  - Context: Skills follow the open Agent Skills standard at https://agentskills.io/, with Claude Code extending the standard with invocation control, subagent execution, and dynamic context injection
- **Claim:** The skill description per-skill cap is 250 characters in the listing
  - Source: Anatomy of the .claude Folder - Every File Explained (2026) - codewithmukesh (`7331528f-ed44-4720-8403-abd43e08f69c`)
  - Context: Each description is capped at 250 characters in the listing regardless of total budget
- **Claim:** Skill listing budget fraction is 1% of context window with 8,000-character fallback
  - Source: Anatomy of the .claude Folder - Every File Explained (2026) - codewithmukesh (`7331528f-ed44-4720-8403-abd43e08f69c`)
  - Context: Skill context budget: descriptions consume ~1% of the context window with an 8,000 character fallback; descriptions are shortened to fit if exceeded
- **Claim:** Stop hook default timeout is 60 seconds
  - Source: Claude Code Stop Hook: Force Task Completion (`d70a5edc-e447-47ed-a867-b9de4c888a9b`)
  - Context: Bad use cases for Stop hooks: long-running operations (hooks have a 60 second timeout)
- **Claim:** HTTP hook default timeout is 600 seconds
  - Source: Hooks reference - Claude Code Docs (`eef45280-e3d8-49bc-be84-b87b0ad7ef8d`)
  - Context: HTTP hook default timeout is 600 seconds (10 minutes), inherited from the common timeout field
- **Claim:** HTTP hooks were introduced in February 2026; async hooks in January 2026
  - Source: Claude Code Hooks: Complete Guide to All 12 Lifecycle Events (`92f0be8c-3959-4520-9463-b6d9bb075806`)
  - Context: HTTP hooks are a Claude Code hook handler type introduced in February 2026 that POST hook event JSON to an HTTP endpoint and receive a JSON response back
- **Claim:** Auto-memory MEMORY.md cap is 200 lines or 25KB
  - Source: Anatomy of the .claude Folder - Every File Explained (2026) - codewithmukesh (`7331528f-ed44-4720-8403-abd43e08f69c`)
  - Context: MEMORY.md index (first 200 lines or 25KB, whichever comes first, loaded at session start) plus topic-specific files

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `4017aa6e-35fb-426d-bc53-34620bec405e`
(cluster `claude-code-https`). No claims are made
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

- NotebookLM notebook [[INGESTED] - Claude Code Guide: Production Hooks and Agent Skills](https://notebooklm.google.com/notebook/4017aa6e-35fb-426d-bc53-34620bec405e)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
