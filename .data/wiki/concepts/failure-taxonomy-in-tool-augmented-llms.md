---
title: "Failure Taxonomy in Tool-Augmented LLMs"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  Tool-augmented large language models (TALLMs) experience characteristic failure modes arising from the integration of external tools (APIs, deep learning models) with language model capabilities, necessitating systematic categorization and repair approaches.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 2c9cc8e9-f1c4-4724-a83b-62412d20846c" (Claude Code - Workflow and Logic Inefficiencies, synced 2026-07-28)
  - "A Taxonomy of Failures in Tool-Augmented LLMs - University of Washington" (https://homes.cs.washington.edu/~rjust/publ/tallm_testing_ast_2025.pdf, transcript synced 2026-07-28)
  - "(PDF) Cognitive Workspace: Active Memory Management for LLMs -- An Empirical Study of Functional Infinite Context - ResearchGate" (https://www.researchgate.net/publication/394687800_Cognitive_Workspace_Active_Memory_Management_for_LLMs_--_An_Empirical_Study_of_Functional_Infinite_Context, transcript synced 2026-07-28)
  - "Cognitive Workspace: Active Memory Management for LLMs -- An Empirical Study of Functional Infinite Context - arXiv" (https://arxiv.org/pdf/2508.13171, transcript synced 2026-07-28)
  - "NotebookLM source 42d557c4-9102-488d-a939-a0b3966f2af9" (Practical Failure Modes in LLM Systems (and Where They Usually Come From) | by Lorenzo Kotalla | Feb, 2026 | Medium.pdf, synced 2026-07-28)
  - "(PDF) The Open -On the Metaphysics of the Semantic Field A fissure through which meaning breathes - ResearchGate" (https://www.researchgate.net/publication/395868305_The_Open_-On_the_Metaphysics_of_the_Semantic_Field_A_fissure_through_which_meaning_breathes, transcript synced 2026-07-28)
  - "(PDF) Learning to Repair Tool Failures: Post-hoc Adaptation for LLM Tool Use" (https://www.researchgate.net/publication/397170083_Learning_to_Repair_Tool_Failures_Post-hoc_Adaptation_for_LLM_Tool_Use, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: failure-taxonomy-in-tool-augmented-llms
    - level: notebook
      id: 2c9cc8e9-f1c4-4724-a83b-62412d20846c
      title: Claude Code - Workflow and Logic Inefficiencies
      url: https://notebooklm.google.com/notebook/2c9cc8e9-f1c4-4724-a83b-62412d20846c
    - level: cluster
      id: 6
      name: https-llms-researchgate
    - level: source_url
      url: https://homes.cs.washington.edu/~rjust/publ/tallm_testing_ast_2025.pdf
      title: A Taxonomy of Failures in Tool-Augmented LLMs - University of Washington
    - level: source_url
      url: https://www.researchgate.net/publication/394687800_Cognitive_Workspace_Active_Memory_Management_for_LLMs_--_An_Empirical_Study_of_Functional_Infinite_Context
      title: (PDF) Cognitive Workspace: Active Memory Management for LLMs -- An Empirical Study of Functional Infinite Context - ResearchGate
    - level: source_url
      url: https://arxiv.org/pdf/2508.13171
      title: Cognitive Workspace: Active Memory Management for LLMs -- An Empirical Study of Functional Infinite Context - arXiv
    - level: source_url
      url: https://www.researchgate.net/publication/395868305_The_Open_-On_the_Metaphysics_of_the_Semantic_Field_A_fissure_through_which_meaning_breathes
      title: (PDF) The Open -On the Metaphysics of the Semantic Field A fissure through which meaning breathes - ResearchGate
    - level: source_url
      url: https://www.researchgate.net/publication/397170083_Learning_to_Repair_Tool_Failures_Post-hoc_Adaptation_for_LLM_Tool_Use
      title: (PDF) Learning to Repair Tool Failures: Post-hoc Adaptation for LLM Tool Use
relations:
  - target: wiki/concepts/cognitive-workspace.md
    type: related
  - target: wiki/concepts/retrieval-augmented-generation.md
    type: related
  - target: wiki/concepts/llm-failure-modes.md
    type: related
---

# Failure Taxonomy in Tool-Augmented LLMs

## Decision context

**Definition:** Tool-augmented large language models (TALLMs) experience characteristic failure modes arising from the integration of external tools (APIs, deep learning models) with language model capabilities, necessitating systematic categorization and repair approaches.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *Claude Code - Workflow and Logic Inefficiencies*, clustered into the "https-llms-researchgate" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Failures in TALLMs originate at integration boundaries between prompts, context, retrieval systems, tool execution, and evaluation logic rather than from the model alone
- The taxonomy from University of Washington research analyzes failures in published TALLMs including Gorilla and Chameleon systems
- Current passive retrieval systems fail to capture the dynamic, task-driven nature of human memory management despite extended context window techniques
- Extended context techniques like Infini-attention and StreamingLLM achieve large context lengths but lack metacognitive awareness and active planning capabilities
- Post-hoc adaptation approaches address tool failures by learning repair strategies after failures occur during tool use
- Research identifies that LLMs appear reliable during early testing but reveal different technical issues once integrated into structured workflows

## Verifiable values

| Name | Value |
|---|---|
| Context Window Extension | `millions of tokens via techniques like Infini-attention and StreamingLLM` |
| Analysis Period | `2024-2025 developments in memory management approaches` |

## Related concepts

- cognitive-workspace — Cognitive Workspace
- retrieval-augmented-generation — Retrieval-Augmented Generation
- llm-failure-modes — LLM Failure Modes

## Citations (from contributing transcripts)

- **Claim:** Failures arise at boundaries between prompts, context, retrieval, tools, and evaluation logic rather than from the model alone
  - Source: Practical Failure Modes in LLM Systems (and Where They Usually Come From) | by Lorenzo Kotalla | Feb, 2026 | Medium.pdf (`42d557c4-9102-488d-a939-a0b3966f2af9`)
  - Context: these problems rarely come from the model alone. More often, they arise at the boundaries between prompts, context, retrieval, tools, and evaluation logic
- **Claim:** Extended context techniques lack metacognitive awareness and active planning capabilities
  - Source: Cognitive Workspace: Active Memory Management for LLMs -- An Empirical Study of Functional Infinite Context - arXiv (`3f8681be-6e91-41ad-8785-83bb0a23e913`)
  - Context: techniques like Infini-attention [5] and StreamingLLM [6] achieve impressive context lengths, they lack the metacognitive awareness and active planning capabilities essential for
- **Claim:** The taxonomy analyzes failures in published TALLMs including Gorilla and Chameleon
  - Source: A Taxonomy of Failures in Tool-Augmented LLMs - University of Washington (`0f91fb91-818c-4d8e-8aa6-75c22346550f`)
  - Context: provides recommendations for testing and repair of TALLMs
- **Claim:** Post-hoc adaptation addresses tool failures by learning repair strategies
  - Source: Learning to Repair Tool Failures: Post-hoc Adaptation for LLM Tool Use
  - Context: Learning to Repair Tool Failures: Post-hoc Adaptation for LLM Tool Use
- **Claim:** Current passive retrieval systems fail to capture dynamic task-driven memory management
  - Source: Cognitive Workspace: Active Memory Management for LLMs -- An Empirical Study of Functional Infinite Context - arXiv (`3f8681be-6e91-41ad-8785-83bb0a23e913`)
  - Context: we demonstrate that current passive retrieval systems fail to capture the dynamic, task-driven nature of human memory management

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `2c9cc8e9-f1c4-4724-a83b-62412d20846c`
(cluster `https-llms-researchgate`). No claims are made
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

- NotebookLM notebook [Claude Code - Workflow and Logic Inefficiencies](https://notebooklm.google.com/notebook/2c9cc8e9-f1c4-4724-a83b-62412d20846c)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
