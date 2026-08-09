---
title: "LLM Coding Agent Architecture Patterns"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, arxiv]
summary: >
  LLM coding agent architecture encompasses the structural patterns, control mechanisms, and orchestration frameworks that govern how large language model agents interact with codebases, execute tasks, and manage execution flow. These architectures range from simple prompting approaches to complex mul
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d" (Deep Research Prompts, Methods, Examples, synced 2026-07-28)
  - "A Deterministic Control Plane for LLM Coding Agents - arXiv" (https://arxiv.org/html/2606.26924v1, transcript synced 2026-07-28)
  - "Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - arXiv" (https://arxiv.org/html/2607.00038v1, transcript synced 2026-07-28)
  - "Nested Code Fences in Markdown - Susam Pal" (https://susam.net/nested-code-fences.html, transcript synced 2026-07-28)
  - "Agentic Program Repair from Test Failures at Scale: A Neuro-symbolic approach with static analysis and test execution feedback - arXiv" (https://arxiv.org/html/2507.18755v1, transcript synced 2026-07-28)
  - "[2606.26924] A Deterministic Control Plane for LLM Coding Agents - arXiv" (https://arxiv.org/abs/2606.26924, transcript synced 2026-07-28)
  - "Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures - arXiv" (https://arxiv.org/html/2604.03515v2, transcript synced 2026-07-28)
  - "Code-Augur: Agentic Vulnerability Detection via Specification Inference - arXiv" (https://arxiv.org/html/2606.18619v1, transcript synced 2026-07-28)
  - "Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - arXiv" (https://arxiv.org/html/2607.00038v1, transcript synced 2026-07-28)
  - "[2607.00038] Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - arXiv" (https://arxiv.org/abs/2607.00038, transcript synced 2026-07-28)
  - "Code-Augur: Agentic Vulnerability Detection via Specification Inference - arXiv" (https://arxiv.org/html/2606.18619v1, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: llm-coding-agent-architecture-patterns
    - level: notebook
      id: 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
      title: Deep Research Prompts, Methods, Examples
      url: https://notebooklm.google.com/notebook/590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
    - level: cluster
      id: 4
      name: arxiv-https-html
    - level: source_url
      url: https://arxiv.org/html/2606.26924v1
      title: A Deterministic Control Plane for LLM Coding Agents - arXiv
    - level: source_url
      url: https://arxiv.org/html/2607.00038v1
      title: Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - arXiv
    - level: source_url
      url: https://susam.net/nested-code-fences.html
      title: Nested Code Fences in Markdown - Susam Pal
    - level: source_url
      url: https://arxiv.org/html/2507.18755v1
      title: Agentic Program Repair from Test Failures at Scale: A Neuro-symbolic approach with static analysis and test execution feedback - arXiv
    - level: source_url
      url: https://arxiv.org/abs/2606.26924
      title: [2606.26924] A Deterministic Control Plane for LLM Coding Agents - arXiv
    - level: source_url
      url: https://arxiv.org/html/2604.03515v2
      title: Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures - arXiv
    - level: source_url
      url: https://arxiv.org/html/2606.18619v1
      title: Code-Augur: Agentic Vulnerability Detection via Specification Inference - arXiv
    - level: source_url
      url: https://arxiv.org/abs/2607.00038
      title: [2607.00038] Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - arXiv
relations:
  - target: wiki/concepts/loop-engineering-patterns.md
    type: related
  - target: wiki/concepts/deterministic-control-planes.md
    type: related
  - target: wiki/concepts/coding-agent-taxonomies.md
    type: related
---

# LLM Coding Agent Architecture Patterns

## Decision context

**Definition:** LLM coding agent architecture encompasses the structural patterns, control mechanisms, and orchestration frameworks that govern how large language model agents interact with codebases, execute tasks, and manage execution flow. These architectures range from simple prompting approaches to complex multi-component systems with deterministic control planes and explicit loop specifications.

Synthesized from **10 contributing transcripts** in NotebookLM notebook *Deep Research Prompts, Methods, Examples*, clustered into the "arxiv-https-html" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- LLM coding harnesses grant agents broad file and shell access, controlled by configuration layers comprising rules files and agent definitions (Source 1, 5)
- Loop engineering represents a design technique that replaces step-by-step prompting with structured, repeatable loop specifications governing agent behavior (Source 2, 8, 9)
- A deterministic control plane provides governance surface through configuration that steers agent behavior without requiring runtime prompting (Source 1, 5)
- The taxonomy of coding agent architectures categorizes systems by their scaffolding components, trajectory handling, and evaluation approaches (Source 6)
- Nested code fences in markdown follow CommonMark specification, with GitHub Flavoured Markdown as a strict superset providing consistent rendering rules (Source 3)
- Agentic approaches to program repair leverage static analysis combined with test execution feedback to identify and resolve failures at scale (Source 4)
- Agentic vulnerability detection systems employ specification inference to identify security weaknesses without requiring explicit vulnerability patterns (Source 7, 10)

## Related concepts

- loop-engineering-patterns — Loop Engineering Patterns
- deterministic-control-planes — Deterministic Control Planes
- coding-agent-taxonomies — Coding Agent Taxonomies
- agentic-program-repair — Agentic Program Repair
- specification-inference — Specification Inference

## Citations (from contributing transcripts)

- **Claim:** LLM coding harnesses grant agents file and shell access controlled by configuration layers
  - Source: A Deterministic Control Plane for LLM Coding Agents - arXiv (`1b1e9779-b8b5-43a5-b491-8b275638b092`)
  - Context: LLM coding harnesses grant agents broad file and shell access, yet the configuration layer that steers them -- rules files, agent definitions
- **Claim:** Loop engineering replaces step-by-step prompting with explicit loop specifications
  - Source: Stop Hand-Holding Your Coding Agent: Engineering the Loops that Replace Step-by-Step Prompting - arXiv (`900035bb-9491-4da0-9d90-8850cd9829ef`)
  - Context: Loop Engineering: Definition and Scope
- **Claim:** Nested code fences follow CommonMark specification with GFM as a strict superset
  - Source: Nested Code Fences in Markdown - Susam Pal (`3af861e5-2507-4d1b-ba6e-80b5d4064daa`)
  - Context: GitHub Flavoured Markdown (GFM) is a strict superset of CommonMark
- **Claim:** Agentic program repair combines static analysis with test execution feedback
  - Source: Agentic Program Repair from Test Failures at Scale: A Neuro-symbolic approach with static analysis and test execution feedback - arXiv (`5a7f160c-1fb6-4441-9c85-9390f0065e1c`)
  - Context: A Neuro-symbolic approach with static analysis and test execution feedback
- **Claim:** Coding agent taxonomy categorizes systems by scaffolding components and architecture
  - Source: Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures - arXiv (`7c394014-3a4f-46cd-b8bc-4c24bfb4c6b2`)
  - Context: Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures
- **Claim:** Code-Augur uses specification inference for vulnerability detection
  - Source: Code-Augur: Agentic Vulnerability Detection via Specification Inference - arXiv (`eed7da18-7d5c-49a1-bbec-de5e0ca4e107`)
  - Context: Agentic Vulnerability Detection via Specification Inference

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `590ac9fd-01f0-4b85-97ff-7d49bd5ed78d`
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

- NotebookLM notebook [Deep Research Prompts, Methods, Examples](https://notebooklm.google.com/notebook/590ac9fd-01f0-4b85-97ff-7d49bd5ed78d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
