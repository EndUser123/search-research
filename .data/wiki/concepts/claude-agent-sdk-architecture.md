---
title: "Claude Agent SDK Architecture"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, https]
summary: >
  Claude Agent SDK provides a structured approach for building AI agents through modular components including skills, subagents, and context management techniques that enable developers to create complex, multi-step agentic workflows.
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
      id: claude-agent-sdk-architecture
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
  - target: wiki/concepts/agent-skills.md
    type: related
  - target: wiki/concepts/context-windows.md
    type: related
  - target: wiki/concepts/model-context-protocol.md
    type: related
---

# Claude Agent SDK Architecture

## Decision context

**Definition:** Claude Agent SDK provides a structured approach for building AI agents through modular components including skills, subagents, and context management techniques that enable developers to create complex, multi-step agentic workflows.

Synthesized from **14 contributing transcripts** in NotebookLM notebook *Agentic Engineering Playbook*, clustered into the "https-claude-docs" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills serve as reusable, callable units that encapsulate specific capabilities and can be authored with best practices for reuse across different agent configurations
- Subagents enable hierarchical task decomposition, allowing parent agents to delegate specialized subtasks to child agent instances
- Context windows define the operational memory boundary within which agents can process and retain information during a session
- Compaction addresses context window constraints by consolidating conversation history when approaching token limits
- The Model Context Protocol (MCP) provides a standardized architecture for connecting agents to external data sources and tools
- Hooks provide interception points that enable developers to observe and modify agent behavior at defined stages of execution

## Verifiable values

| Name | Value |
|---|---|
| context_window_approaches | `Compaction, which consolidates conversation history` |
| architectural_pattern | `Explicit hybrid structure combining deterministic and probabilistic reasoning` |
| control_pattern | `Hooks for intercepting agent behavior at specific execution points` |

## Related concepts

- [[agent-skills]] — Agent Skills
- [[context-windows]] — Context Windows
- [[model-context-protocol]] — Model Context Protocol
- [[subagents]] — Subagents
- [[compaction]] — Compaction

## Citations (from contributing transcripts)

- **Claim:** Skills serve as reusable capability units within the SDK
  - Source: Agent Skills - Claude API Docs (`078510ca-65d8-4db2-8c61-04c4b36da601`)
  - Context: Agent Skills - Claude API Docs
- **Claim:** Subagents enable hierarchical agent task delegation
  - Source: Subagents in the SDK - Claude API Docs - Claude Console (`cc548823-abf5-4103-97c6-02729302a7ed`)
  - Context: Subagents in the SDK - Claude API Docs
- **Claim:** Context windows define operational memory boundaries
  - Source: Context windows - Claude API Docs (`66b5a66a-37d3-4dc4-bac5-0c415d9b4dde`)
  - Context: Context windows - Claude API Docs
- **Claim:** Compaction consolidates conversation history to address context limits
  - Source: Compaction - Claude API Docs (`9bd8f117-8cb0-4122-924d-793db7cfeb14`)
  - Context: Compaction - Claude API Docs
- **Claim:** MCP provides standardized architecture for external integrations
  - Source: Architecture overview - Model Context Protocol (`968d7ddc-89f6-43e6-ba35-4c7e88222c71`)
  - Context: Architecture overview - Model Context Protocol
- **Claim:** Hooks provide interception points for observing and modifying agent behavior
  - Source: Intercept and control agent behavior with hooks - Claude API Docs (`67dcb7e1-2b09-4268-b05c-bcfff535bbae`)
  - Context: Intercept and control agent behavior with hooks
- **Claim:** Explicit hybrid structures combine deterministic and probabilistic reasoning
  - Source: Retake the control with Deterministic Reasoning Graph (DRG) (`c64be41e-b46d-47eb-b555-e1ad6185ee93`)
  - Context: Core concept: an explicit hybrid structure

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
