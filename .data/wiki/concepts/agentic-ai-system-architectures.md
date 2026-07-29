---
title: "Agentic AI System Architectures"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, github]
summary: >
  Agentic AI system architectures refer to design patterns and implementations that enable autonomous AI agents to execute tasks, maintain state, and integrate with development environments. These architectures combine large language model capabilities with structured workflows, memory systems, and ve
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 59329bf3-4765-4d4e-8ec6-f2eceeba0f41" (Agentic Engineering Playbook, synced 2026-07-27)
  - "Agent hooks in Visual Studio Code (Preview)" (https://code.visualstudio.com/docs/copilot/customization/hooks, transcript synced 2026-07-27)
  - "documenting my work on what I'm calling the RPI Strategy for disciplined agentic workflows - GitHub" (https://github.com/patrob/rpi-strategy, transcript synced 2026-07-27)
  - "Kairong-Han/Causal_Agent: Causal Agent based on Large Language Model - GitHub" (https://github.com/kairong-han/causal_agent, transcript synced 2026-07-27)
  - "A memory architecture for agentic system - Gist" (https://gist.github.com/spikelab/7551c6368e23caa06a4056350f6b2db3, transcript synced 2026-07-27)
  - "GitHub - jmcentire/pact: Contracts before code. Tests as law. Agents that can't cheat." (https://github.com/jmcentire/pact, transcript synced 2026-07-27)
  - "How to Handle Schema Evolution in BigQuery When Source Schemas Change Frequently" (https://oneuptime.com/blog/post/2026-02-17-how-to-handle-schema-evolution-in-bigquery-when-source-schemas-change-frequently/view, transcript synced 2026-07-27)
  - "dfinke/PSClaudeCode: A PowerShell implementation of ... - GitHub" (https://github.com/dfinke/PSClaudeCode, transcript synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: agentic-ai-system-architectures
    - level: notebook
      id: 59329bf3-4765-4d4e-8ec6-f2eceeba0f41
      title: Agentic Engineering Playbook
      url: https://notebooklm.google.com/notebook/59329bf3-4765-4d4e-8ec6-f2eceeba0f41
    - level: cluster
      id: 8
      name: github-https-code
    - level: source_url
      url: https://code.visualstudio.com/docs/copilot/customization/hooks
      title: Agent hooks in Visual Studio Code (Preview)
    - level: source_url
      url: https://github.com/patrob/rpi-strategy
      title: documenting my work on what I'm calling the RPI Strategy for disciplined agentic workflows - GitHub
    - level: source_url
      url: https://github.com/kairong-han/causal_agent
      title: Kairong-Han/Causal_Agent: Causal Agent based on Large Language Model - GitHub
    - level: source_url
      url: https://gist.github.com/spikelab/7551c6368e23caa06a4056350f6b2db3
      title: A memory architecture for agentic system - Gist
    - level: source_url
      url: https://github.com/jmcentire/pact
      title: GitHub - jmcentire/pact: Contracts before code. Tests as law. Agents that can't cheat.
    - level: source_url
      url: https://oneuptime.com/blog/post/2026-02-17-how-to-handle-schema-evolution-in-bigquery-when-source-schemas-change-frequently/view
      title: How to Handle Schema Evolution in BigQuery When Source Schemas Change Frequently
    - level: source_url
      url: https://github.com/dfinke/PSClaudeCode
      title: dfinke/PSClaudeCode: A PowerShell implementation of ... - GitHub
relations:
  - target: wiki/concepts/large-language-model-agents.md
    type: related
  - target: wiki/concepts/agent-workflow-patterns.md
    type: related
  - target: wiki/concepts/ai-agent-memory-systems.md
    type: related
---

# Agentic AI System Architectures

## Decision context

**Definition:** Agentic AI system architectures refer to design patterns and implementations that enable autonomous AI agents to execute tasks, maintain state, and integrate with development environments. These architectures combine large language model capabilities with structured workflows, memory systems, and verification mechanisms.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *Agentic Engineering Playbook*, clustered into the "github-https-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Agent hooks provide integration points within development environments, allowing AI agents to interact with IDE features and extend functionality through defined extension APIs
- The RPI Strategy documents a disciplined approach to agentic workflows, emphasizing structured processes for managing autonomous agent behavior
- Causal Agent implementations apply causal reasoning to LLM-based agents, enabling more robust decision-making beyond pattern matching
- Memory architectures for agentic systems establish patterns for maintaining context and state across agent interactions and sessions
- Contract-based patterns define explicit agreements that govern agent behavior, treating tests and specifications as enforceable constraints
- Agent implementations like PowerShell-based Claude Code demonstrate how agent loops combined with tool access and permission models create functional autonomous systems

## Related concepts

- [[large-language-model-agents]] — Large Language Model Agents
- [[agent-workflow-patterns]] — Agent Workflow Patterns
- [[ai-agent-memory-systems]] — AI Agent Memory Systems
- [[contract-based-verification]] — Contract-Based Verification

## Citations (from contributing transcripts)

- **Claim:** Agent hooks provide integration points within VS Code for AI agent interaction
  - Source: Agent hooks in Visual Studio Code (Preview) (`48d3a2d5-27dd-4f6f-883d-b0c5a80f622f`)
  - Context: Agent hooks in Visual Studio Code (Preview)
- **Claim:** The RPI Strategy documents a disciplined approach to agentic workflows
  - Source: documenting my work on what I'm calling the RPI Strategy for disciplined agentic workflows - GitHub (`57aac094-1d92-4497-9d90-5844b401bb9a`)
  - Context: RPI Strategy for disciplined agentic workflows
- **Claim:** Causal Agent applies causal reasoning to LLM-based agent systems
  - Source: Kairong-Han/Causal_Agent: Causal Agent based on Large Language Model - GitHub (`81de6814-eba6-410a-8941-efd4be1cddcd`)
  - Context: Causal Agent based on Large Language Model
- **Claim:** Memory architecture establishes patterns for maintaining state in agentic systems
  - Source: A memory architecture for agentic system - Gist (`cad350ba-41a5-4159-8ada-7b923f0b4aaf`)
  - Context: A memory architecture for agentic system
- **Claim:** Contract-based patterns enforce agent behavior through tests and specifications
  - Source: GitHub - jmcentire/pact: Contracts before code. Tests as law. Agents that can't cheat. (`d174ae73-7f6c-4471-bf84-524efac4fbf7`)
  - Context: Contracts before code. Tests as law. Agents that can't cheat.
- **Claim:** Agent implementations combine agent loops with tool access and permissions
  - Source: dfinke/PSClaudeCode: A PowerShell implementation of Claude Code: agent loop + tools + permissions. - GitHub
  - Context: agent loop + tools + permissions

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `59329bf3-4765-4d4e-8ec6-f2eceeba0f41`
(cluster `github-https-code`). No claims are made
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
