---
title: "Antigravity Codes Platform"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, antigravity]
summary: >
  Antigravity Codes is an online resource platform (antigravity.codes) that aggregates guides, tutorials, and documentation related to LLM knowledge management workflows, including content specifically focused on Karpathy's approach to organizing AI knowledge bases and idea files.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 55c988d8-818d-4ed9-b08b-12d6c697ff5f" (Claude Code and QMD: Persistent Knowledge Architecture, synced 2026-07-28)
  - "Karpathy's LLM Knowledge Bases: The Post-Code AI Workflow - Antigravity Codes" (https://antigravity.codes/blog/karpathy-llm-knowledge-bases, transcript synced 2026-07-28)
  - "Blog | Antigravity.codes - Guides, Tutorials & Updates" (https://antigravity.codes/blog, transcript synced 2026-07-28)
  - "Guide with AGENTS.md & Examples (2026) - Antigravity Rules" (https://antigravity.codes/blog/user-rules, transcript synced 2026-07-28)
  - "Karpathy's LLM Wiki: The Complete Guide to His Idea File" (https://antigravity.codes/blog/karpathy-llm-wiki-idea-file, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: antigravity-codes-platform
    - level: notebook
      id: 55c988d8-818d-4ed9-b08b-12d6c697ff5f
      title: Claude Code and QMD: Persistent Knowledge Architecture
      url: https://notebooklm.google.com/notebook/55c988d8-818d-4ed9-b08b-12d6c697ff5f
    - level: cluster
      id: 6
      name: antigravity-codes-https
    - level: source_url
      url: https://antigravity.codes/blog/karpathy-llm-knowledge-bases
      title: Karpathy's LLM Knowledge Bases: The Post-Code AI Workflow - Antigravity Codes
    - level: source_url
      url: https://antigravity.codes/blog
      title: Blog | Antigravity.codes - Guides, Tutorials & Updates
    - level: source_url
      url: https://antigravity.codes/blog/user-rules
      title: Guide with AGENTS.md & Examples (2026) - Antigravity Rules
    - level: source_url
      url: https://antigravity.codes/blog/karpathy-llm-wiki-idea-file
      title: Karpathy's LLM Wiki: The Complete Guide to His Idea File
relations:
  - target: wiki/concepts/llm-knowledge-bases.md
    type: related
  - target: wiki/concepts/agents.md-documentation.md
    type: related
  - target: wiki/concepts/model-context-protocol.md
    type: related
---

# Antigravity Codes Platform

## Decision context

**Definition:** Antigravity Codes is an online resource platform (antigravity.codes) that aggregates guides, tutorials, and documentation related to LLM knowledge management workflows, including content specifically focused on Karpathy's approach to organizing AI knowledge bases and idea files.

Synthesized from **4 contributing transcripts** in NotebookLM notebook *Claude Code and QMD: Persistent Knowledge Architecture*, clustered into the "antigravity-codes-https" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The platform hosts multiple content sections including Blog, Community, Prompts, Rules, Workflows, Agent Skills, and MCPs (Model Context Protocol resources)
- One documented use case involves Karpathy's LLM Knowledge Bases approach to post-code AI workflows
- The platform provides a Guide section featuring AGENTS.md documentation with examples
- Content is available in multiple languages including English, Spanish, Chinese, Japanese, German, Portuguese, and Russian

## Verifiable values

| Name | Value |
|---|---|
| Supported Languages | `7 (EN, ES, ZH, JA, DE, PT, RU)` |
| Primary Content Sections | `7 (Blog, Community, Prompts, Rules, Workflows, Agent Skills, MCPs)` |

## Related concepts

- [[llm-knowledge-bases]] — LLM Knowledge Bases
- [[agents.md-documentation]] — AGENTS.md Documentation
- [[model-context-protocol]] — Model Context Protocol

## Citations (from contributing transcripts)

- **Claim:** Antigravity Codes is a platform with multiple content sections
  - Source: Karpathy's LLM Knowledge Bases: The Post-Code AI Workflow - Antigravity Codes (`2eabe640-a933-4be6-b3b1-a589b054d484`)
  - Context: https://antigravity.codes/ with sections for Blog, Community, Prompts, Rules, Workflows, Agent Skills, and MCPs
- **Claim:** The platform contains guides about Karpathy's LLM knowledge management approach
  - Source: Karpathy's LLM Knowledge Bases: The Post-Code AI Workflow - Antigravity Codes (`2eabe640-a933-4be6-b3b1-a589b054d484`)
  - Context: https://antigravity.codes/blog/karpathy-llm-knowledge-bases
- **Claim:** The platform provides AGENTS.md documentation with examples
  - Source: Guide with AGENTS.md & Examples (2026) - Antigravity Rules (`8f150a4f-aec7-43fe-b276-39f3eb884859`)
  - Context: Guide with AGENTS.md & Examples (2026)
- **Claim:** Content is available in multiple languages
  - Source: Blog | Antigravity.codes - Guides, Tutorials & Updates (`8e7102f6-871d-430e-804b-b2c67fde9d11`)
  - Context: EN English, ES Español, ZH 中文, JA 日本語, DE Deutsch, PT Português, RU Русский

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `55c988d8-818d-4ed9-b08b-12d6c697ff5f`
(cluster `antigravity-codes-https`). No claims are made
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

- NotebookLM notebook [Claude Code and QMD: Persistent Knowledge Architecture](https://notebooklm.google.com/notebook/55c988d8-818d-4ed9-b08b-12d6c697ff5f)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
