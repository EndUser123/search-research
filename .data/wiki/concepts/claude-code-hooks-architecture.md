---
title: "Claude Code Hooks Architecture"
created: 2026-08-11
source: nlm-sync-2026-08-11
tags: [nlm-synced, reference, claude]
summary: >
  Claude Code hooks are deterministic user-defined shell commands or scripts that execute at specific points in the Claude execution lifecycle. They provide a programmable enforcement layer to block, transform, or audit agent behavior without relying on probabilistic model judgment.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook 4017aa6e-35fb-426d-bc53-34620bec405e" ([INGESTED] - Claude Code Guide: Production Hooks and Agent Skills, synced 2026-08-11)
  - "Claude Code Hooks (2026): 6 Production Hooks + Common Gotchas | Setup Guide" (https://sandlabs.com.au/blog/claude-code-hooks-guide, transcript synced 2026-08-11)
  - "Claude Code Hooks Complete Guide - Deterministic Enforcement Across the Tool Lifecycle" (https://hidekazu-konishi.com/entry/claude_code_hooks_complete_guide.html, transcript synced 2026-08-11)
  - "Claude Code Skills Complete Guide - Creating, Testing, and Distributing Agent Skills" (https://hidekazu-konishi.com/entry/claude_code_skills_complete_guide.html, transcript synced 2026-08-11)
  - "Claude Code Hooks Explained: The Deterministic Layer Around Your Agent - Blake Crosley" (https://blakecrosley.com/blog/claude-code-hooks-explained, transcript synced 2026-08-11)
  - "Exploring Conversation History | CodeSignal Learn" (https://codesignal.com/learn/courses/foundation-getting-started-with-claude-code/lessons/exploring-conversation-history, transcript synced 2026-08-11)
  - "Claude Code: Hooks, Subagents & Skills Complete Guide - OfoxAI" (https://ofox.ai/blog/claude-code-hooks-subagents-skills-complete-guide-2026/, transcript synced 2026-08-11)
  - "get-session-id | Skills Marketplace - LobeHub" (https://lobehub.com/de/skills/cowwoc-cat-get-session-id, transcript synced 2026-08-11)
  - "Top 8 Claude Skills for Developers - Snyk" (https://snyk.io/articles/top-claude-skills-developers/, transcript synced 2026-08-11)
  - "Claude Code Extension Layer Decision Guide - Choosing Among Skills, Subagents, Hooks, and Plugins | hidekazu-konishi.com" (https://hidekazu-konishi.com/entry/claude_code_extension_layers_decision_guide.html, transcript synced 2026-08-11)
  - "Skills in Claude Code - Reusable Prompts and Workflows - codewithmukesh" (https://codewithmukesh.com/blog/skills-claude-code/, transcript synced 2026-08-11)
  - "Best Claude Code Skills to Try in 2026 - Firecrawl" (https://www.firecrawl.dev/blog/best-claude-code-skills, transcript synced 2026-08-11)
  - "NotebookLM source ee1b3b77-265d-4c43-904f-4bda0325edd0" (Unified Technical Specification for Claude Code Plugin Lifecycles: Deterministic State Machines, Session Boundary Isolation, and Quality Gate Hook Remediation, synced 2026-08-11)
  - "Claude Code Internal Architecture Analysis | Taeho Kim" (https://taeho.io/en/reading/claude-code-internal-architecture-analysis_20264, transcript synced 2026-08-11)
provenance:
  chain:
    - level: concept
      id: claude-code-hooks-architecture
    - level: notebook
      id: 4017aa6e-35fb-426d-bc53-34620bec405e
      title: [INGESTED] - Claude Code Guide: Production Hooks and Agent Skills
      url: https://notebooklm.google.com/notebook/4017aa6e-35fb-426d-bc53-34620bec405e
    - level: cluster
      id: 0
      name: claude-https-code
    - level: source_url
      url: https://sandlabs.com.au/blog/claude-code-hooks-guide
      title: Claude Code Hooks (2026): 6 Production Hooks + Common Gotchas | Setup Guide
    - level: source_url
      url: https://hidekazu-konishi.com/entry/claude_code_hooks_complete_guide.html
      title: Claude Code Hooks Complete Guide - Deterministic Enforcement Across the Tool Lifecycle
    - level: source_url
      url: https://hidekazu-konishi.com/entry/claude_code_skills_complete_guide.html
      title: Claude Code Skills Complete Guide - Creating, Testing, and Distributing Agent Skills
    - level: source_url
      url: https://blakecrosley.com/blog/claude-code-hooks-explained
      title: Claude Code Hooks Explained: The Deterministic Layer Around Your Agent - Blake Crosley
    - level: source_url
      url: https://codesignal.com/learn/courses/foundation-getting-started-with-claude-code/lessons/exploring-conversation-history
      title: Exploring Conversation History | CodeSignal Learn
    - level: source_url
      url: https://ofox.ai/blog/claude-code-hooks-subagents-skills-complete-guide-2026/
      title: Claude Code: Hooks, Subagents & Skills Complete Guide - OfoxAI
    - level: source_url
      url: https://lobehub.com/de/skills/cowwoc-cat-get-session-id
      title: get-session-id | Skills Marketplace - LobeHub
    - level: source_url
      url: https://snyk.io/articles/top-claude-skills-developers/
      title: Top 8 Claude Skills for Developers - Snyk
    - level: source_url
      url: https://hidekazu-konishi.com/entry/claude_code_extension_layers_decision_guide.html
      title: Claude Code Extension Layer Decision Guide - Choosing Among Skills, Subagents, Hooks, and Plugins | hidekazu-konishi.com
    - level: source_url
      url: https://codewithmukesh.com/blog/skills-claude-code/
      title: Skills in Claude Code - Reusable Prompts and Workflows - codewithmukesh
    - level: source_url
      url: https://www.firecrawl.dev/blog/best-claude-code-skills
      title: Best Claude Code Skills to Try in 2026 - Firecrawl
    - level: source_url
      url: https://taeho.io/en/reading/claude-code-internal-architecture-analysis_20264
      title: Claude Code Internal Architecture Analysis | Taeho Kim
relations:
  - target: wiki/concepts/claude-skills.md
    type: related
  - target: wiki/concepts/mcp-servers.md
    type: related
  - target: wiki/concepts/subagents.md
    type: related
---

# Claude Code Hooks Architecture

## Decision context

**Definition:** Claude Code hooks are deterministic user-defined shell commands or scripts that execute at specific points in the Claude execution lifecycle. They provide a programmable enforcement layer to block, transform, or audit agent behavior without relying on probabilistic model judgment.

Synthesized from **13 contributing transcripts** in NotebookLM notebook *[INGESTED] - Claude Code Guide: Production Hooks and Agent Skills*, clustered into the "claude-https-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Hooks are configured in settings.json files located across global (~/.claude/settings.json), project (.claude/settings.json), and local-ignored (.claude/settings.local.json) scopes.
- The system uses a merged execution model where hooks from all scopes aggregate and execute together, with higher-priority scopes taking precedence.
- Hooks are triggered by over 25 lifecycle events, including PreToolUse, PostToolUse, UserPromptSubmit, SessionStart, and Stop.
- Handler types include command (shell scripts), http (POST endpoints), mcp_tool (MCP servers), prompt (LLM evaluation), and agent (subagent verification).
- Exit codes control flow: exit 0 allows progression, exit 2 blocks the action and surfaces stderr to the model, and other non-zero codes result in non-blocking logged errors.
- Hooks can override default permission flows by emitting structured JSON on stdout with hookSpecificOutput.permissionDecision set to 'allow', 'deny', or 'ask'.
- Matchers allow event-specific filtering by tool name (e.g., 'Bash', 'Edit|Write') or regex patterns; matchers are case-sensitive.
- Hooks receive a structured JSON payload on stdin containing session_id, cwd, hook_event_name, tool_name, and tool_input.

## Verifiable values

| Name | Value |
|---|---|
| exit code 0 behavior | `proceeds` |
| exit code 2 behavior | `blocks action` |
| default timeout (command/http/mcp) | `600 seconds` |
| default timeout (prompt) | `30 seconds` |
| default timeout (agent) | `60 seconds` |

## Related concepts

- [[claude-skills]] — Claude Skills
- [[mcp-servers]] — MCP servers
- [[subagents]] — Subagents
- [[claude.md]] — CLAUDE.md

## Citations (from contributing transcripts)

- **Claim:** Claude Code hooks are user-defined shell commands that fire at specific points in Claude's execution lifecycle.
  - Source: Claude Code Hooks (2026): 6 Production Hooks + Common Gotchas | Setup Guide (`2dddd800-c911-498c-b1c9-48a63a2c30f9`)
  - Context: Claude Code hooks are user-defined shell commands that fire at specific points in Claude's execution lifecycle
- **Claim:** Hook exit codes control behavior: exit 0 proceeds, exit 2 blocks the action.
  - Source: Claude Code Hooks (2026): 6 Production Hooks + Common Gotchas | Setup Guide (`2dddd800-c911-498c-b1c9-48a63a2c30f9`)
  - Context: Hook exit codes control behavior: exit 0 proceeds (stdout becomes additional context for some events), exit 2 blocks the action (stderr is shown to Claude or user)
- **Claim:** The system uses a merged execution model where hooks from all scopes aggregate and execute together.
  - Source: Technical Specification for Plugin Lifecycles: Deterministic State Machines, Session Boundary, Quality Gate Remediation (`ee1b3b77-265d-4c43-904f-4bda0325edd0`)
  - Context: Unlike project settings where higher-priority files override lower ones, lifecycle hooks use a merged execution model: all registered handlers across global, local, plugin, and skill scopes aggregate and execute together when an event fires
- **Claim:** PreToolUse is the most powerful event where guardrails live.
  - Source: Claude Code Hooks (2026): 6 Production Hooks + Common Gotchas | Setup Guide (`2dddd800-c911-498c-b1c9-48a63a2c30f9`)
  - Context: PreToolUse fires before any tool runs and is used to block, ask, or transform tool input; it is described as the most powerful event and where guardrails live

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `4017aa6e-35fb-426d-bc53-34620bec405e`
(cluster `claude-https-code`). No claims are made
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
