---
title: "Phylo Agent Architecture"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  Phylo's approach to AI agents for biomedical research centers on specialized agent types coordinated through defined interaction patterns, with the company's Biomni representing a general-purpose open-source biomedical AI agent implementation.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d" (Deep Research Prompts, Methods, Examples, synced 2026-07-28)
  - "The Agent Loop Decoded | developers - Oracle Blogs" (https://blogs.oracle.com/developers/the-agent-loop-decoded-three-levels-every-agent-engineer-must-know, transcript synced 2026-07-28)
  - "Harness engineering for coding agent users - Martin Fowler" (https://martinfowler.com/articles/harness-engineering.html, transcript synced 2026-07-28)
  - "SKILL.md vs CLAUDE.md vs AGENTS.md Compared | Termdock" (https://www.termdock.com/blog/skill-md-vs-claude-md-vs-agents-md, transcript synced 2026-07-28)
  - "Systematic Debugging — 4-phase root cause debugging: understand bugs before fixing" (https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging, transcript synced 2026-07-28)
  - "AI Agents for Biomedical Research - Phylo" (https://phylo.bio/research, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: phylo-agent-architecture
    - level: notebook
      id: 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
      title: Deep Research Prompts, Methods, Examples
      url: https://notebooklm.google.com/notebook/590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
    - level: cluster
      id: 6
      name: https-agent-phylo
    - level: source_url
      url: https://blogs.oracle.com/developers/the-agent-loop-decoded-three-levels-every-agent-engineer-must-know
      title: The Agent Loop Decoded | developers - Oracle Blogs
    - level: source_url
      url: https://martinfowler.com/articles/harness-engineering.html
      title: Harness engineering for coding agent users - Martin Fowler
    - level: source_url
      url: https://www.termdock.com/blog/skill-md-vs-claude-md-vs-agents-md
      title: SKILL.md vs CLAUDE.md vs AGENTS.md Compared | Termdock
    - level: source_url
      url: https://hermes-agent.nousresearch.com/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging
      title: Systematic Debugging — 4-phase root cause debugging: understand bugs before fixing
    - level: source_url
      url: https://phylo.bio/research
      title: AI Agents for Biomedical Research - Phylo
relations:
  - target: wiki/concepts/agent-loop-patterns.md
    type: related
  - target: wiki/concepts/biomni.md
    type: related
  - target: wiki/concepts/agent-configuration-methods.md
    type: related
---

# Phylo Agent Architecture

## Decision context

**Definition:** Phylo's approach to AI agents for biomedical research centers on specialized agent types coordinated through defined interaction patterns, with the company's Biomni representing a general-purpose open-source biomedical AI agent implementation.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *Deep Research Prompts, Methods, Examples*, clustered into the "https-agent-phylo" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Phylo develops AI agents specifically designed for biomedical research applications, operating under principles of open science with core research released as open source
- Biomni serves as Phylo's general-purpose biomedical AI agent, originally introduced through a Stanford paper and made available as open source via GitHub
- Agent engineering commonly employs a loop-based architecture that iterates through planning, action, and observation phases
- Configuration approaches for AI agents include specialized files such as SKILL.md, CLAUDE.md, and AGENTS.md that define agent capabilities and behaviors
- Systematic debugging techniques can be applied to agent interactions using phased approaches to identify and resolve issues

## Related concepts

- [[agent-loop-patterns]] — Agent Loop Patterns
- [[biomni]] — Biomni
- [[agent-configuration-methods]] — Agent Configuration Methods
- [[open-science-ai]] — Open Science AI

## Citations (from contributing transcripts)

- **Claim:** Phylo develops AI agents for biomedical research with open science principles
  - Source: AI Agents for Biomedical Research - Phylo (`fed7ebb4-102e-458f-b896-bfa78ab958fd`)
  - Context: We push the frontier of AI to build biomedical super-intelligence. We believe in open science— all of our core research is open source.
- **Claim:** Biomni is Phylo's general-purpose biomedical AI agent
  - Source: AI Agents for Biomedical Research - Phylo (`fed7ebb4-102e-458f-b896-bfa78ab958fd`)
  - Context: Biomni: A General-Purpose Biomedical AI Agent
- **Claim:** Agent loop architecture involves three levels that agent engineers must understand
  - Source: The Agent Loop Decoded | developers - Oracle Blogs (`592277ee-2c7e-4d85-9d66-ad9f7aeda6ba`)
  - Context: The Agent Loop Decoded | developers
- **Claim:** Configuration files like SKILL.md, CLAUDE.md, and AGENTS.md define agent capabilities
  - Source: SKILL.md vs CLAUDE.md vs AGENTS.md Compared | Termdock (`b3d65592-bbf4-4c6a-8ad1-7552bc2c9c81`)
  - Context: A clear comparison of SKILL.md, CLAUDE.md, and AGENTS.md — what each file does, which tools read them, and how to layer them for optimal AI agent performance.
- **Claim:** Systematic debugging approaches apply phased methods to agent issues
  - Source: Systematic Debugging — 4-phase root cause debugging: understand bugs before fixing (`cb20a67d-9aad-4b39-9311-16beb1469855`)
  - Context: Systematic Debugging — 4-phase root cause debugging: understand bugs before fixing

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `590ac9fd-01f0-4b85-97ff-7d49bd5ed78d`
(cluster `https-agent-phylo`). No claims are made
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
