---
title: "Agentic AI System Patterns"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, github]
summary: >
  Agentic AI systems are implementations that employ autonomous agents capable of reasoning, planning, and executing tasks using tools and external resources. These systems incorporate various architectural patterns to manage memory, workflow execution, and contractual constraints.
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
      id: agentic-ai-system-patterns
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
  - target: wiki/concepts/autonomous-agents.md
    type: related
  - target: wiki/concepts/ai-tool-use.md
    type: related
  - target: wiki/concepts/agent-memory-systems.md
    type: related
---

# Agentic AI System Patterns

## Decision context

**Definition:** Agentic AI systems are implementations that employ autonomous agents capable of reasoning, planning, and executing tasks using tools and external resources. These systems incorporate various architectural patterns to manage memory, workflow execution, and contractual constraints.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *Agentic Engineering Playbook*, clustered into the "github-https-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Agent implementations may include hook patterns that allow external intervention at specific execution points
- Workflow strategies such as the RPI Strategy provide structured approaches for disciplined agentic execution
- Memory architecture patterns address how agents retain and retrieve contextual information across interactions
- Contract-based approaches enforce behavioral constraints by treating tests as executable specifications
- Loop-and-tools patterns implement iterative agent behavior where tools extend agent capabilities

## Verifiable values

| Name | Value |
|---|---|
| implementation_count | `multiple open-source implementations available on GitHub` |

## Related concepts

- [[autonomous-agents]] — Autonomous Agents
- [[ai-tool-use]] — AI Tool Use
- [[agent-memory-systems]] — Agent Memory Systems
- [[workflow-automation]] — Workflow Automation

## Citations (from contributing transcripts)

- **Claim:** Agent hook patterns provide external intervention capabilities
  - Source: Agent hooks in Visual Studio Code (Preview) (`48d3a2d5-27dd-4f6f-883d-b0c5a80f622f`)
  - Context: Agent hooks in Visual Studio Code (Preview)
- **Claim:** RPI Strategy provides disciplined workflow execution for agents
  - Source: documenting my work on what I'm calling the RPI Strategy for disciplined agentic workflows - GitHub (`57aac094-1d92-4497-9d90-5844b401bb9a`)
  - Context: RPI Strategy for disciplined agentic workflows
- **Claim:** Memory architecture patterns manage contextual retention
  - Source: A memory architecture for agentic system - Gist (`cad350ba-41a5-4159-8ada-7b923f0b4aaf`)
  - Context: A memory architecture for agentic system
- **Claim:** Contract-based approaches enforce behavioral constraints through executable specifications
  - Source: GitHub - jmcentire/pact: Contracts before code. Tests as law. Agents that can't cheat. (`d174ae73-7f6c-4471-bf84-524efac4fbf7`)
  - Context: Contracts before code. Tests as law. Agents that can't cheat
- **Claim:** Loop-and-tools patterns implement iterative agent behavior with extended capabilities
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
