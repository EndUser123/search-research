---
title: "Claude Agent SDK Core Concepts"
created: 2026-08-10
source: nlm-sync-2026-08-10
tags: [nlm-synced, reference, claude]
summary: >
  The Claude Agent SDK is a framework for building autonomous agents using the same architecture as Claude Code. It provides tools for interacting with Claude through agentic loops, managing context, and extending model capabilities.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook c8b07a4c-607c-4ddc-94be-688206daf737" ([INGESTED] - Claude Code x NotebookLM x Obsidian Research, synced 2026-08-10)
  - "Agent SDK reference - Python - Claude API Docs" (https://platform.claude.com/docs/en/agent-sdk/python, transcript synced 2026-08-10)
  - "Agent SDK reference - TypeScript - Claude API Docs" (https://platform.claude.com/docs/en/agent-sdk/typescript, transcript synced 2026-08-10)
  - "Agent Skills - Claude API Docs" (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview, transcript synced 2026-08-10)
  - "Claude Agent SDK Tutorial: Create Agents Using Claude Sonnet 4.5 | DataCamp" (https://www.datacamp.com/tutorial/how-to-use-claude-agent-sdk, transcript synced 2026-08-10)
  - "Agent SDK overview - Claude API Docs" (https://platform.claude.com/docs/en/agent-sdk/overview, transcript synced 2026-08-10)
provenance:
  chain:
    - level: concept
      id: claude-agent-sdk-core-concepts
    - level: notebook
      id: c8b07a4c-607c-4ddc-94be-688206daf737
      title: [INGESTED] - Claude Code x NotebookLM x Obsidian Research
      url: https://notebooklm.google.com/notebook/c8b07a4c-607c-4ddc-94be-688206daf737
    - level: cluster
      id: 3
      name: claude-docs-https
    - level: source_url
      url: https://platform.claude.com/docs/en/agent-sdk/python
      title: Agent SDK reference - Python - Claude API Docs
    - level: source_url
      url: https://platform.claude.com/docs/en/agent-sdk/typescript
      title: Agent SDK reference - TypeScript - Claude API Docs
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
      title: Agent Skills - Claude API Docs
    - level: source_url
      url: https://www.datacamp.com/tutorial/how-to-use-claude-agent-sdk
      title: Claude Agent SDK Tutorial: Create Agents Using Claude Sonnet 4.5 | DataCamp
    - level: source_url
      url: https://platform.claude.com/docs/en/agent-sdk/overview
      title: Agent SDK overview - Claude API Docs
relations:
  - target: wiki/concepts/claude-code.md
    type: related
  - target: wiki/concepts/model-context-protocol-(mcp).md
    type: related
  - target: wiki/concepts/agent-skills.md
    type: related
---

# Claude Agent SDK Core Concepts

## Decision context

**Definition:** The Claude Agent SDK is a framework for building autonomous agents using the same architecture as Claude Code. It provides tools for interacting with Claude through agentic loops, managing context, and extending model capabilities.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *[INGESTED] - Claude Code x NotebookLM x Obsidian Research*, clustered into the "claude-docs-https" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The SDK offers two primary interaction patterns: the query() function for one-off tasks and the ClaudeSDKClient for continuous, stateful conversations.
- Agents operate through a structured loop that gathers context, takes actions via tools, verifies work, and iterates until completion.
- Custom tools are defined using the @tool decorator, allowing developers to expose Python functions as Model Context Protocol (MCP) tools.
- Context management is handled through session persistence, message history, and automatic compaction to maintain focus during long-running tasks.
- Security control is enforced via permission systems, including per-tool allow/deny rules and sandboxed environments for command execution.
- Extensibility is achieved through hooks that intercept and respond to lifecycle events such as tool usage, prompt submission, and message streaming.

## Verifiable values

| Name | Value |
|---|---|
| supported models | `Sonnet 3.5, Sonnet 4.5, Opus 4.6` |
| context window | `1M tokens (for Sonnet 4.5 and 4.6)` |
| max agentic turns | `Configurable via max_turns` |

## Related concepts

- [[claude-code]] — Claude Code
- [[model-context-protocol-(mcp)]] — Model Context Protocol (MCP)
- [[agent-skills]] — Agent Skills
- [[structured-outputs]] — Structured Outputs

## Citations (from contributing transcripts)

- **Claim:** The Claude Agent SDK is a framework for building autonomous agents using the same architecture as Claude Code.
  - Source: Agent SDK reference - Python - Claude API Docs (`110e8887-b304-4909-adbd-863a8244256d`)
  - Context: The Claude Agent SDK is a framework for building autonomous agents using the same architecture as Claude Code.
- **Claim:** The SDK offers two primary interaction patterns: the query() function for one-off tasks and the ClaudeSDKClient for continuous, stateful conversations.
  - Source: Agent SDK reference - Python - Claude API Docs (`110e8887-b304-4909-adbd-863a8244256d`)
  - Context: The SDK offers two primary interaction patterns: the query() function for one-off tasks and the ClaudeSDKClient for continuous, stateful conversations.
- **Claim:** Agents operate through a structured loop that gathers context, takes actions via tools, verifies work, and iterates until completion.
  - Source: Agent SDK reference - Python - Claude API Docs (`110e8887-b304-4909-adbd-863a8244256d`)
  - Context: The agentic loop involves four steps: gathering context, taking action, verifying work, and repeating.
- **Claim:** Custom tools are defined using the @tool decorator, allowing developers to expose Python functions as Model Context Protocol (MCP) tools.
  - Source: Agent SDK reference - Python - Claude API Docs (`110e8887-b304-4909-adbd-863a8244256d`)
  - Context: Custom tools are defined using the @tool decorator, allowing developers to expose Python functions as Model Context Protocol (MCP) tools.
- **Claim:** Context management is handled through session persistence, message history, and automatic compaction to maintain focus during long-running tasks.
  - Source: Agent SDK reference - Python - Claude API Docs (`110e8887-b304-4909-adbd-863a8244256d`)
  - Context: Context management is handled through session persistence, message history, and automatic compaction to maintain focus during long-running tasks.
- **Claim:** Security control is enforced via permission systems, including per-tool allow/deny rules and sandboxed environments for command execution.
  - Source: Agent SDK reference - Python - Claude API Docs (`110e8887-b304-4909-adbd-863a8244256d`)
  - Context: Security control is enforced via permission systems, including per-tool allow/deny rules and sandboxed environments for command execution.
- **Claim:** Extensibility is achieved through hooks that intercept and respond to lifecycle events such as tool usage, prompt submission, and message streaming.
  - Source: Agent SDK reference - Python - Claude API Docs (`110e8887-b304-4909-adbd-863a8244256d`)
  - Context: Extensibility is achieved through hooks that intercept and respond to lifecycle events such as tool usage, prompt submission, and message streaming.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `c8b07a4c-607c-4ddc-94be-688206daf737`
(cluster `claude-docs-https`). No claims are made
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
