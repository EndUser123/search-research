---
title: "Laguna S 2.1 Local Model Capabilities"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, model]
summary: >
  Laguna S 2.1 is a 118-billion parameter mixture-of-experts model released by Poolside that achieves performance comparable to models 10x its size while remaining runnable on consumer-grade hardware such as a single Nvidia DGX Spark.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 32b2f92f-b402-44f9-8069-6faca3dd20c9" (Testing Buzz by Block: The Limits of Agent Orchestration, synced 2026-07-28)
  - "NotebookLM source 05024df4-c152-4edf-b415-808fbed97fc8" (AI News: This New Model Has Big AI Labs Panicking!, synced 2026-07-28)
  - "NotebookLM source 0f16cb9a-2bd6-4f1f-b749-8af65df0d0e8" (Laguna S 2.1: The Best Local Agentic Coder?, synced 2026-07-28)
  - "NotebookLM source 7f8c786c-28de-4816-a8d9-7129971f9aab" (Kimi K3 Is INSANE with Claude Code (FREE + Local + open Source), synced 2026-07-28)
  - "NotebookLM source af7bf2ca-380c-4aaf-954b-a213b953d6e1" (New Laguna S2.1 AI Model: Complete Review & Coding Test, synced 2026-07-28)
  - "NotebookLM source c9eaa7fd-0e9e-4314-b67d-038161deea82" (AI News: NotebookLM Folders; New Models (Kimi, Gemini, Grok); Rogue AI Models + More, synced 2026-07-28)
  - "NotebookLM source fdd83cde-d0d7-4775-b6cb-c4db7f077df3" (Laguna S 2.1: The Best Local Model? Beats GLM 5.2, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: laguna-s-21-local-model-capabilities
    - level: notebook
      id: 32b2f92f-b402-44f9-8069-6faca3dd20c9
      title: Testing Buzz by Block: The Limits of Agent Orchestration
      url: https://notebooklm.google.com/notebook/32b2f92f-b402-44f9-8069-6faca3dd20c9
    - level: cluster
      id: 3
      name: model-laguna-local
relations:
  - target: wiki/concepts/kimi-k3-open-weight-model.md
    type: related
  - target: wiki/concepts/mixture-of-experts-architecture.md
    type: related
  - target: wiki/concepts/local-ai-model-deployment.md
    type: related
---

# Laguna S 2.1 Local Model Capabilities

## Decision context

**Definition:** Laguna S 2.1 is a 118-billion parameter mixture-of-experts model released by Poolside that achieves performance comparable to models 10x its size while remaining runnable on consumer-grade hardware such as a single Nvidia DGX Spark.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *Testing Buzz by Block: The Limits of Agent Orchestration*, clustered into the "model-laguna-local" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The model utilizes a mixture-of-experts architecture with 118 billion total parameters but only activates 8 billion parameters per token during inference, enabling computational efficiency
- It supports a context window of 1 million tokens, allowing for processing of extremely long documents or codebases
- The model achieves performance competitive with much larger models, including reportedly beating models with 1.6 trillion parameters on coding benchmarks
- Poolside released both the model weights and full benchmark trajectories, making the evaluation methodology transparent and reproducible
- The model can be run locally on a single Nvidia DGX Spark at 80 tokens per second with speculative decoding enabled
- Poolside provides their own agentic coding harness called Pool, designed specifically for long-horizon coding tasks
- Laguna S 2.1 achieved favorable results compared to models including GLM 5.2, Kimi K3, and Deepseek V4 in benchmark comparisons

## Verifiable values

| Name | Value |
|---|---|
| total_parameters | `118 billion` |
| active_parameters_per_token | `8 billion` |
| context_window | `1 million tokens` |
| throughput_with_speculative_decoding | `80 tokens per second (on Nvidia DGX Spark)` |
| parameter_efficiency_vs_comparison_model | `13x fewer parameters than a 1.6 trillion parameter model it competes with` |

## Related concepts

- kimi-k3-open-weight-model — Kimi K3 Open-Weight Model
- mixture-of-experts-architecture — Mixture-of-Experts Architecture
- local-ai-model-deployment — Local AI Model Deployment

## Citations (from contributing transcripts)

- **Claim:** Laguna S 2.1 is 118 billion parameters with 8 billion active parameters per token
  - Source: Laguna S 2.1: The Best Local Agentic Coder? (`0f16cb9a-2bd6-4f1f-b749-8af65df0d0e8`)
  - Context: it's an 118 billion parameter MOE with 8 billion active parameters per token uh with a context window of 1 million token
- **Claim:** The model can run on a single Nvidia DGX Spark at 80 tokens per second
  - Source: Laguna S 2.1: The Best Local Agentic Coder? (`0f16cb9a-2bd6-4f1f-b749-8af65df0d0e8`)
  - Context: you can run it on DGX park at 80 tokens per second with speculative decoding enabled
- **Claim:** Poolside released the full trajectories of the benchmark
  - Source: Laguna S 2.1: The Best Local Agentic Coder? (`0f16cb9a-2bd6-4f1f-b749-8af65df0d0e8`)
  - Context: they also release the full trajectories of the benchmark so everybody can go and look at how exactly this model performs
- **Claim:** The model is comparable to models 10x its size
  - Source: Laguna S 2.1: The Best Local Model? Beats GLM 5.2 (`fdd83cde-d0d7-4775-b6cb-c4db7f077df3`)
  - Context: it does the work of models more than 10 times its size on one coding benchmark it beats arrival with 1.6 trillion parameters it has 13 times fewer
- **Claim:** Poolside released their own agentic coding harness called Pool
  - Source: Laguna S 2.1: The Best Local Agentic Coder? (`0f16cb9a-2bd6-4f1f-b749-8af65df0d0e8`)
  - Context: they also released their own agentic coding harness called pool we're going to look at that in a minute because it's specifically designed for long horizon tasks
- **Claim:** The model is fully open and uploaded on Hugging Face
  - Source: New Laguna S2.1 AI Model: Complete Review & Coding Test (`af7bf2ca-380c-4aaf-954b-a213b953d6e1`)
  - Context: laguna is 2.1 is fully open and it is uploaded on hugging pace also and you can run it on Nvidia

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `32b2f92f-b402-44f9-8069-6faca3dd20c9`
(cluster `model-laguna-local`). No claims are made
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

- NotebookLM notebook [Testing Buzz by Block: The Limits of Agent Orchestration](https://notebooklm.google.com/notebook/32b2f92f-b402-44f9-8069-6faca3dd20c9)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
