---
title: "LLM-based Agent Architectures"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, arxiv]
summary: >
  LLM-based agent architectures refer to the structural designs and component arrangements that enable large language models to perform autonomous, goal-directed tasks by integrating perception, reasoning, planning, and action capabilities within a unified system.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 76ace35a-a66b-47fd-b2dd-c6b50936b3e2" (AI Architecture and Decision Record Frameworks, synced 2026-07-28)
  - "Agentic Artificial Intelligence (AI): Architectures, Taxonomies, and Evaluation of Large Language Model Agents - arXiv" (https://arxiv.org/html/2601.12560v1, transcript synced 2026-07-28)
  - "Building AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv" (https://arxiv.org/html/2603.05344v1, transcript synced 2026-07-28)
  - "AgenticRed: Optimizing Agentic Systems for Automated Red-teaming - arXiv" (https://arxiv.org/html/2601.13518v1, transcript synced 2026-07-28)
  - "Towards Scientific Intelligence: A Survey of LLM-based Scientific Agents - arXiv" (https://arxiv.org/html/2503.24047v3, transcript synced 2026-07-28)
  - "Multi-LLM-Agents Debate - Performance, Efficiency, and Scaling Challenges | ICLR Blogposts 2025" (https://d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/, transcript synced 2026-07-28)
  - "AI Agents: Evolution, Architecture, and Real-World Applications - arXiv" (https://arxiv.org/html/2503.12687v1, transcript synced 2026-07-28)
  - "Building Effective AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv" (https://arxiv.org/html/2603.05344v3, transcript synced 2026-07-28)
  - "M3MAD-Bench: Are Multi-Agent Debates Really Effective Across Domains and Modalities?" (https://arxiv.org/html/2601.02854v1, transcript synced 2026-07-28)
  - "AEGIS : Automated Co-Evolutionary Framework for Guarding Prompt Injections Schema" (https://arxiv.org/html/2509.00088v1, transcript synced 2026-07-28)
  - "AI Skills as the Institutional Knowledge Primitive for Agentic Software Development - arXiv" (https://arxiv.org/html/2603.14805v1, transcript synced 2026-07-28)
  - "AEGIS : Automated Co-Evolutionary Framework for Guarding Prompt Injection - arXiv" (https://arxiv.org/html/2509.00088v2, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: llm-based-agent-architectures
    - level: notebook
      id: 76ace35a-a66b-47fd-b2dd-c6b50936b3e2
      title: AI Architecture and Decision Record Frameworks
      url: https://notebooklm.google.com/notebook/76ace35a-a66b-47fd-b2dd-c6b50936b3e2
    - level: cluster
      id: 1
      name: arxiv-https-html
    - level: source_url
      url: https://arxiv.org/html/2601.12560v1
      title: Agentic Artificial Intelligence (AI): Architectures, Taxonomies, and Evaluation of Large Language Model Agents - arXiv
    - level: source_url
      url: https://arxiv.org/html/2603.05344v1
      title: Building AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv
    - level: source_url
      url: https://arxiv.org/html/2601.13518v1
      title: AgenticRed: Optimizing Agentic Systems for Automated Red-teaming - arXiv
    - level: source_url
      url: https://arxiv.org/html/2503.24047v3
      title: Towards Scientific Intelligence: A Survey of LLM-based Scientific Agents - arXiv
    - level: source_url
      url: https://d2jud02ci9yv69.cloudfront.net/2025-04-28-mad-159/blog/mad/
      title: Multi-LLM-Agents Debate - Performance, Efficiency, and Scaling Challenges | ICLR Blogposts 2025
    - level: source_url
      url: https://arxiv.org/html/2503.12687v1
      title: AI Agents: Evolution, Architecture, and Real-World Applications - arXiv
    - level: source_url
      url: https://arxiv.org/html/2603.05344v3
      title: Building Effective AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv
    - level: source_url
      url: https://arxiv.org/html/2601.02854v1
      title: M3MAD-Bench: Are Multi-Agent Debates Really Effective Across Domains and Modalities?
    - level: source_url
      url: https://arxiv.org/html/2509.00088v1
      title: AEGIS : Automated Co-Evolutionary Framework for Guarding Prompt Injections Schema
    - level: source_url
      url: https://arxiv.org/html/2603.14805v1
      title: AI Skills as the Institutional Knowledge Primitive for Agentic Software Development - arXiv
    - level: source_url
      url: https://arxiv.org/html/2509.00088v2
      title: AEGIS : Automated Co-Evolutionary Framework for Guarding Prompt Injection - arXiv
relations:
  - target: wiki/concepts/multi-agent-debate-systems.md
    type: related
  - target: wiki/concepts/prompt-injection-defenses.md
    type: related
  - target: wiki/concepts/agent-evaluation-frameworks.md
    type: related
---

# LLM-based Agent Architectures

## Decision context

**Definition:** LLM-based agent architectures refer to the structural designs and component arrangements that enable large language models to perform autonomous, goal-directed tasks by integrating perception, reasoning, planning, and action capabilities within a unified system.

Synthesized from **11 contributing transcripts** in NotebookLM notebook *AI Architecture and Decision Record Frameworks*, clustered into the "arxiv-https-html" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Agent architectures typically decompose into core components including a planner, memory system, and tool-use or action execution module that together enable autonomous task completion
- The planner component handles task decomposition and strategic reasoning, with prompt-native planners representing one approach for guiding LLM-based reasoning without external control structures
- Memory systems within agent architectures store and retrieve information across interactions, supporting context maintenance and learning across extended task sequences
- Multi-agent debate architectures leverage collaboration among multiple LLM agents to improve test-time performance through structured disagreement and synthesis processes
- Terminal-native agent designs adapt agent architectures for command-line environments, incorporating scaffolding, harness frameworks, and context engineering techniques
- Security-focused architectures like AEGIS employ co-evolutionary defensive patterns to protect agent systems from prompt injection threats
- Agent evaluation taxonomies assess systems across dimensions including task completion accuracy, autonomy levels, and robustness to adversarial inputs

## Verifiable values

| Name | Value |
|---|---|
| arXiv paper identifier | `2601.12560v1` |
| arXiv paper identifier | `2603.05344v1` |
| arXiv paper identifier | `2601.13518v1` |
| arXiv paper identifier | `2503.24047v3` |
| arXiv paper identifier | `2503.12687v1` |
| arXiv paper identifier | `2601.02854v1` |
| arXiv paper identifier | `2509.00088v1` |

## Related concepts

- [[multi-agent-debate-systems]] — Multi-Agent Debate Systems
- [[prompt-injection-defenses]] — Prompt Injection Defenses
- [[agent-evaluation-frameworks]] — Agent Evaluation Frameworks
- [[context-engineering-for-agents]] — Context Engineering for Agents
- [[ai-skills-for-agentic-systems]] — AI Skills for Agentic Systems

## Citations (from contributing transcripts)

- **Claim:** Agent architectures include planner, memory, and action components that enable autonomous task completion
  - Source: Agentic Artificial Intelligence (AI): Architectures, Taxonomies, and Evaluation of Large Language Model Agents - arXiv (`020ed2d9-e578-4b02-9c86-d7d2383c7509`)
  - Context: Table of Contents includes Abstract, Introduction, Background and Definitions sections indicating architectural components
- **Claim:** Multi-agent debate architectures leverage collaboration among multiple LLM agents to improve test-time performance
  - Source: Multi-LLM-Agents Debate - Performance, Efficiency, and Scaling Challenges | ICLR Blogposts 2025 (`7f1ffe6d-fa4a-4e29-a9d3-73697057f88a`)
  - Context: Multi-Agent Debate (MAD) explores leveraging collaboration among multiple large language model (LLM) agents to improve test-time performance
- **Claim:** Terminal-native agent designs incorporate scaffolding, harness frameworks, and context engineering techniques
  - Source: Building AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv (`4da7edf7-69f8-4c24-8002-08d583f392a8`)
  - Context: Section 2 System Architecture with Overview subsection indicates scaffolding and harness design patterns
- **Claim:** Security architectures employ co-evolutionary defensive patterns to protect against prompt injection
  - Source: AEGIS : Automated Co-Evolutionary Framework for Guarding Prompt Injections Schema - arXiv
  - Context: Abstract describes Automated Co-Evolutionary Framework for Guarding Prompt Injections Schema
- **Claim:** Planner components handle task decomposition with prompt-native approaches representing one design pattern
  - Source: Towards Scientific Intelligence: A Survey of LLM-based Scientific Agents - arXiv (`79561ee4-6177-44cb-9e03-406c5f602d97`)
  - Context: Section 2.1 Planner with 2.1.1 Prompt-Native Planners subsection
- **Claim:** Agent evaluation taxonomies assess systems across multiple dimensions including task completion and robustness
  - Source: Agentic Artificial Intelligence (AI): Architectures, Taxonomies, and Evaluation of Large Language Model Agents - arXiv (`020ed2d9-e578-4b02-9c86-d7d2383c7509`)
  - Context: Title indicates evaluation of Large Language Model Agents as a primary focus
- **Claim:** Multi-agent debate effectiveness varies across domains and modalities, evaluated through benchmarks
  - Source: M3MAD-Bench: Are Multi-Agent Debates Really Effective Across Domains and Modalities? - arXiv
  - Context: Abstract and Table of Contents with M3MAD-Bench section indicate evaluation across domains and modalities

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `76ace35a-a66b-47fd-b2dd-c6b50936b3e2`
(cluster `arxiv-https-html`). No claims are made
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

- NotebookLM notebook [AI Architecture and Decision Record Frameworks](https://notebooklm.google.com/notebook/76ace35a-a66b-47fd-b2dd-c6b50936b3e2)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
