---
title: "Uncensored AI Models"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  Uncensored AI models are language models designed without content filtering or safety restrictions, allowing unrestricted responses across all query types. These models are offered through various API providers and are optimized for general-purpose local deployment.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 831e0613-f723-4d87-aaeb-1d4b5a061496" (Maximizing LLM Performance and Context via GPU Memory Optimization, synced 2026-07-28)
  - "Run Dolphin3.0-R1-Mistral-24B API (Easy Deployment & Flat-Rate Pricing) - Featherless" (https://featherless.ai/models/lactroiii/Dolphin3.0-R1-Mistral-24B, transcript synced 2026-07-28)
  - "Dolphin3.0 R1 Mistral 24B - API Pricing & Providers - OpenRouter" (https://openrouter.ai/cognitivecomputations/dolphin3.0-r1-mistral-24b, transcript synced 2026-07-28)
  - "nchapman/dolphin3.0-qwen2.5/system - Ollama" (https://ollama.com/nchapman/dolphin3.0-qwen2.5/blobs/b704be6d7802, transcript synced 2026-07-28)
  - "andrevp/Ornith-1.0-9B-Heretic-Uncensored - Featherless AI" (https://featherless.ai/models/andrevp/Ornith-1.0-9B-Heretic-Uncensored, transcript synced 2026-07-28)
  - "Uncensored AI Models 2026: Complete Guide & Rankings - MangoMind BD" (https://www.mangomindbd.com/blog/uncensored-ai-guide-2026-hub, transcript synced 2026-07-28)
  - "20 Uncensored AI Models 2026 Ranked by Real Usage - Atlas Cloud" (https://www.atlascloud.ai/blog/guides/best-uncensored-ai-models, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: uncensored-ai-models
    - level: notebook
      id: 831e0613-f723-4d87-aaeb-1d4b5a061496
      title: Maximizing LLM Performance and Context via GPU Memory Optimization
      url: https://notebooklm.google.com/notebook/831e0613-f723-4d87-aaeb-1d4b5a061496
    - level: cluster
      id: 6
      name: https-models-featherless
    - level: source_url
      url: https://featherless.ai/models/lactroiii/Dolphin3.0-R1-Mistral-24B
      title: Run Dolphin3.0-R1-Mistral-24B API (Easy Deployment & Flat-Rate Pricing) - Featherless
    - level: source_url
      url: https://openrouter.ai/cognitivecomputations/dolphin3.0-r1-mistral-24b
      title: Dolphin3.0 R1 Mistral 24B - API Pricing & Providers - OpenRouter
    - level: source_url
      url: https://ollama.com/nchapman/dolphin3.0-qwen2.5/blobs/b704be6d7802
      title: nchapman/dolphin3.0-qwen2.5/system - Ollama
    - level: source_url
      url: https://featherless.ai/models/andrevp/Ornith-1.0-9B-Heretic-Uncensored
      title: andrevp/Ornith-1.0-9B-Heretic-Uncensored - Featherless AI
    - level: source_url
      url: https://www.mangomindbd.com/blog/uncensored-ai-guide-2026-hub
      title: Uncensored AI Models 2026: Complete Guide & Rankings - MangoMind BD
    - level: source_url
      url: https://www.atlascloud.ai/blog/guides/best-uncensored-ai-models
      title: 20 Uncensored AI Models 2026 Ranked by Real Usage - Atlas Cloud
relations:
  - target: wiki/concepts/instruct-tuned-models.md
    type: related
  - target: wiki/concepts/fp8-quantization.md
    type: related
  - target: wiki/concepts/function-calling-models.md
    type: related
---

# Uncensored AI Models

## Decision context

**Definition:** Uncensored AI models are language models designed without content filtering or safety restrictions, allowing unrestricted responses across all query types. These models are offered through various API providers and are optimized for general-purpose local deployment.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *Maximizing LLM Performance and Context via GPU Memory Optimization*, clustered into the "https-models-featherless" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Dolphin3.0-R1-Mistral-24B is a 24 billion parameter instruct-tuned model with FP8 quantization and 32k context length, supporting tool calling and published on April 7, 2026
- The Dolphin3.0 R1 model was trained for 3 epochs using 800k reasoning traces from the Dolphin-R1 dataset to develop reasoning capabilities
- Dolphin 3.0 models are designed as general-purpose local models excelling in coding, math, agentic tasks, and function calling use cases
- Ornith-1.0-9B-Heretic-Uncensored is a 9 billion parameter multimodal vision-text model based on Qwen 3.5-style hybrid architecture with FP8 quantization, 32k context length, and MIT license
- Featherless AI provides uncensored models via API with flat-rate pricing and warm deployment architecture
- OpenRouter and Ollama serve as alternative providers for accessing uncensored model variants through their respective platforms

## Verifiable values

| Name | Value |
|---|---|
| Dolphin3.0-R1-Mistral-24B Context Length | `32k tokens` |
| Dolphin3.0-R1-Mistral-24B Parameters | `24B` |
| Dolphin3.0-R1 Quantization | `FP8` |
| Dolphin3.0 R1 Training Epochs | `3 epochs` |
| Dolphin3.0 R1 Training Traces | `800k reasoning traces` |
| Ornith-1.0-9B Parameters | `9B` |
| Ornith-1.0-9B Context Length | `32k tokens` |

## Related concepts

- [[instruct-tuned-models]] — Instruct-tuned Models
- [[fp8-quantization]] — FP8 Quantization
- [[function-calling-models]] — Function Calling Models
- [[mistral-architecture]] — Mistral Architecture
- [[qwen-model-family]] — Qwen Model Family

## Citations (from contributing transcripts)

- **Claim:** Dolphin3.0-R1-Mistral-24B is a 24 billion parameter model with FP8 quantization, 32k context length, and tool calling support
  - Source: Run Dolphin3.0-R1-Mistral-24B API (Easy Deployment & Flat-Rate Pricing) - Featherless (`23a365cb-63d4-4403-9ca6-51d11fe8659c`)
  - Context: Text Generation Concurrency Cost: 2 Model Size: 24B Quant: FP8 Ctx Length: 32k Tool Calling: Supported Published: Apr 7, 2026
- **Claim:** Dolphin3.0 R1 was trained for 3 epochs using 800k reasoning traces from the Dolphin-R1 dataset
  - Source: Dolphin3.0 R1 Mistral 24B - API Pricing & Providers - OpenRouter (`5169f7a7-7bed-4dc6-a9dc-d280ff3e94f3`)
  - Context: The R1 version has been trained for 3 epochs to reason using 800k reasoning traces from the Dolphin-R1 dataset
- **Claim:** Dolphin 3.0 is designed as a general-purpose local model for coding, math, agentic tasks, and function calling
  - Source: Dolphin3.0 R1 Mistral 24B - API Pricing & Providers - OpenRouter (`5169f7a7-7bed-4dc6-a9dc-d280ff3e94f3`)
  - Context: Designed to be the ultimate general purpose local model, enabling coding, math, agentic, function calling, and general use cases
- **Claim:** Ornith-1.0-9B-Heretic-Uncensored is a 9B parameter multimodal vision-text model with 32k context and MIT license
  - Source: andrevp/Ornith-1.0-9B-Heretic-Uncensored - Featherless AI (`9d584461-14b8-4af5-a4fe-07495000f017`)
  - Context: andrevp/Ornith-1.0-9B-Heretic-Uncensored is a 9 billion parameter multimodal vision-text language model... Ctx Length: 32k... License: mit
- **Claim:** Ornith-1.0-9B uses Qwen 3.5-style hybrid architecture with FP8 quantization
  - Source: andrevp/Ornith-1.0-9B-Heretic-Uncensored - Featherless AI (`9d584461-14b8-4af5-a4fe-07495000f017`)
  - Context: based on the Qwen 3.5-style hybrid architecture... Quant: FP8

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `831e0613-f723-4d87-aaeb-1d4b5a061496`
(cluster `https-models-featherless`). No claims are made
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

- NotebookLM notebook [Maximizing LLM Performance and Context via GPU Memory Optimization](https://notebooklm.google.com/notebook/831e0613-f723-4d87-aaeb-1d4b5a061496)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
