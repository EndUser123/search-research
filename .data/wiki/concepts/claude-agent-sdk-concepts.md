---
title: "Claude Agent SDK Concepts"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, https]
summary: >
  A set of design patterns and techniques provided by the Claude Agent SDK for building AI agents, including approaches for managing conversational context, integrating agent skills, controlling agent behavior, and structuring multi-agent hierarchies.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 59329bf3-4765-4d4e-8ec6-f2eceeba0f41" (Agentic Engineering Playbook, synced 2026-07-27)
  - "Agent Skills - Claude API Docs" (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview, transcript synced 2026-07-27)
  - "(PDF) Demand-Driven Context: A Methodology for Building Enterprise Knowledge Bases Through Agent Failure - ResearchGate" (https://www.researchgate.net/publication/402480507_Demand-Driven_Context_A_Methodology_for_Building_Enterprise_Knowledge_Bases_Through_Agent_Failure, transcript synced 2026-07-27)
  - "Comparing Open-Source AI Agent Frameworks - Langfuse" (https://langfuse.com/blog/2025-03-19-ai-agent-comparison, transcript synced 2026-07-27)
  - "How to Measure Brand Awareness, Trust, and Reputation - Spin Sucks" (https://spinsucks.com/communication/brand-awareness-trust-reputation-measurement/, transcript synced 2026-07-27)
  - "Context windows - Claude API Docs" (https://platform.claude.com/docs/en/build-with-claude/context-windows, transcript synced 2026-07-27)
  - "Intercept and control agent behavior with hooks - Claude API Docs" (https://platform.claude.com/docs/en/agent-sdk/hooks, transcript synced 2026-07-27)
  - "(PDF) Strategic Dialogue Architecture for LLMs: From Prompting to Context Engineering" (https://www.researchgate.net/publication/395572928_Strategic_Dialogue_Architecture_for_LLMs_From_Prompting_to_Context_Engineering, transcript synced 2026-07-27)
  - "Architecture overview - Model Context Protocol" (https://modelcontextprotocol.io/docs/learn/architecture, transcript synced 2026-07-27)
  - "Compaction - Claude API Docs" (https://platform.claude.com/docs/en/build-with-claude/compaction, transcript synced 2026-07-27)
  - "Using Agent Skills with the API - Claude Console" (https://platform.claude.com/docs/en/build-with-claude/skills-guide, transcript synced 2026-07-27)
  - "Daily Papers - Hugging Face" (https://huggingface.co/papers?q=tool-integrated%20reasoning, transcript synced 2026-07-27)
  - "Retake the control with Deterministic Reasoning Graph (DRG)" (https://huggingface.co/blog/TeamAIris/deterministic-reasoning-graph, transcript synced 2026-07-27)
  - "Subagents in the SDK - Claude API Docs - Claude Console" (https://platform.claude.com/docs/en/agent-sdk/subagents, transcript synced 2026-07-27)
  - "Skill authoring best practices - Claude API Docs" (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, transcript synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: claude-agent-sdk-concepts
    - level: notebook
      id: 59329bf3-4765-4d4e-8ec6-f2eceeba0f41
      title: Agentic Engineering Playbook
      url: https://notebooklm.google.com/notebook/59329bf3-4765-4d4e-8ec6-f2eceeba0f41
    - level: cluster
      id: 3
      name: https-claude-docs
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
      title: Agent Skills - Claude API Docs
    - level: source_url
      url: https://www.researchgate.net/publication/402480507_Demand-Driven_Context_A_Methodology_for_Building_Enterprise_Knowledge_Bases_Through_Agent_Failure
      title: (PDF) Demand-Driven Context: A Methodology for Building Enterprise Knowledge Bases Through Agent Failure - ResearchGate
    - level: source_url
      url: https://langfuse.com/blog/2025-03-19-ai-agent-comparison
      title: Comparing Open-Source AI Agent Frameworks - Langfuse
    - level: source_url
      url: https://spinsucks.com/communication/brand-awareness-trust-reputation-measurement/
      title: How to Measure Brand Awareness, Trust, and Reputation - Spin Sucks
    - level: source_url
      url: https://platform.claude.com/docs/en/build-with-claude/context-windows
      title: Context windows - Claude API Docs
    - level: source_url
      url: https://platform.claude.com/docs/en/agent-sdk/hooks
      title: Intercept and control agent behavior with hooks - Claude API Docs
    - level: source_url
      url: https://www.researchgate.net/publication/395572928_Strategic_Dialogue_Architecture_for_LLMs_From_Prompting_to_Context_Engineering
      title: (PDF) Strategic Dialogue Architecture for LLMs: From Prompting to Context Engineering
    - level: source_url
      url: https://modelcontextprotocol.io/docs/learn/architecture
      title: Architecture overview - Model Context Protocol
    - level: source_url
      url: https://platform.claude.com/docs/en/build-with-claude/compaction
      title: Compaction - Claude API Docs
    - level: source_url
      url: https://platform.claude.com/docs/en/build-with-claude/skills-guide
      title: Using Agent Skills with the API - Claude Console
    - level: source_url
      url: https://huggingface.co/papers?q=tool-integrated%20reasoning
      title: Daily Papers - Hugging Face
    - level: source_url
      url: https://huggingface.co/blog/TeamAIris/deterministic-reasoning-graph
      title: Retake the control with Deterministic Reasoning Graph (DRG)
    - level: source_url
      url: https://platform.claude.com/docs/en/agent-sdk/subagents
      title: Subagents in the SDK - Claude API Docs - Claude Console
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
      title: Skill authoring best practices - Claude API Docs
relations:
  - target: wiki/concepts/context-windows.md
    type: related
  - target: wiki/concepts/agent-skills.md
    type: related
  - target: wiki/concepts/model-context-protocol.md
    type: related
---

# Claude Agent SDK Concepts

## Decision context

**Definition:** A set of design patterns and techniques provided by the Claude Agent SDK for building AI agents, including approaches for managing conversational context, integrating agent skills, controlling agent behavior, and structuring multi-agent hierarchies.

Synthesized from **14 contributing transcripts** in NotebookLM notebook *Agentic Engineering Playbook*, clustered into the "https-claude-docs" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Context windows define the maximum token capacity for agent conversations, limiting how much information can be processed in a single exchange
- Compaction is a technique for reducing conversation length by summarizing earlier messages, freeing up context window space for new content
- Agent skills are discrete capabilities that can be assigned to agents, with best practices recommending intentional skill selection to avoid unnecessary complexity
- Hooks provide designated points in agent execution where developers can intercept and modify agent behavior, enabling custom control without altering core logic
- Subagents allow agents to delegate tasks to child agents, supporting hierarchical task decomposition and modular system design
- The Model Context Protocol (MCP) establishes a standardized approach for connecting agents to external data sources and services
- Skill authoring best practices emphasize selecting skills purposefully based on actual task requirements rather than including all available options
- Context window management is critical when authoring skills, as exceeding capacity limits impacts agent performance

## Verifiable values

| Name | Value |
|---|---|
| Context Window | `Maximum token capacity for a single agent conversation (varies by model)` |

## Related concepts

- context-windows — Context Windows
- [[agent-skills]] — Agent Skills
- model-context-protocol — Model Context Protocol
- subagents — Subagents
- compaction — Compaction

## Citations (from contributing transcripts)

- **Claim:** The Claude Agent SDK provides hooks as points for intercepting and modifying agent behavior
  - Source: Intercept and control agent behavior with hooks - Claude API Docs (`67dcb7e1-2b09-4268-b05c-bcfff535bbae`)
  - Context: Intercept and control agent behavior with hooks - Claude API Docs
- **Claim:** Subagents enable hierarchical agent design by allowing agents to delegate tasks
  - Source: Subagents in the SDK - Claude API Docs - Claude Console (`cc548823-abf5-4103-97c6-02729302a7ed`)
  - Context: Subagents in the SDK - Claude API Docs
- **Claim:** Context windows define the operational boundary for agent conversations
  - Source: Context windows - Claude API Docs (`66b5a66a-37d3-4dc4-bac5-0c415d9b4dde`)
  - Context: Context windows - Claude API Docs
- **Claim:** Compaction reduces conversation length to manage context window usage
  - Source: Compaction - Claude API Docs (`9bd8f117-8cb0-4122-924d-793db7cfeb14`)
  - Context: Compaction - Claude API Docs
- **Claim:** Skill authoring should be intentional, selecting only required skills rather than all available options
  - Source: Skill authoring best practices - Claude API Docs (`f27d58d4-e785-4848-a662-cdd6fb6ce497`)
  - Context: Skill authoring best practices - Claude API Docs
- **Claim:** Agent skills provide discrete capabilities that extend agent functionality
  - Source: Agent Skills - Claude API Docs (`078510ca-65d8-4db2-8c61-04c4b36da601`)
  - Context: Agent Skills - Claude API Docs
- **Claim:** MCP provides a standardized protocol for connecting agents to external data sources
  - Source: Architecture overview - Model Context Protocol (`968d7ddc-89f6-43e6-ba35-4c7e88222c71`)
  - Context: Architecture overview - Model Context Protocol

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `59329bf3-4765-4d4e-8ec6-f2eceeba0f41`
(cluster `https-claude-docs`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Agentic Engineering Playbook](https://notebooklm.google.com/notebook/59329bf3-4765-4d4e-8ec6-f2eceeba0f41)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
