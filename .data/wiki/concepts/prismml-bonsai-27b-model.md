---
title: "PrismML Bonsai 27B Model"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, image]
summary: >
  Bonsai 27B is a compressed large language model developed by Caltech spinout PrismML, representing an Alibaba Qwen 3.6 27B backbone reduced to under 4 GB through aggressive quantization techniques, enabling local execution on mobile devices without cloud infrastructure.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 917784eb-ef7d-40e5-b823-7bd74c2bc9bd" (WL: Multi-Agent Orchestration, synced 2026-07-27)
  - "NotebookLM source 3b213f2c-f30f-4db6-8a00-ba4ab3361df2" (Bonsai 27B Fact Checking PrismML's Biggest Claims, synced 2026-07-27)
  - "NotebookLM source 547652f6-637b-4663-b6bd-1aff544b3820" (PrismML Just Launched A 27B Phone AI Model, synced 2026-07-27)
  - "NotebookLM source 5c549b7f-ad9b-4a74-9fd6-f43a0357ff6f" (The Tiny 1.9MB Tool That's Making Microsoft's Worst Nightmare Come True — And Millions Are Using It, synced 2026-07-27)
  - "NotebookLM source 982f06ea-a83a-4b37-8421-cc2664749ef3" (Someone Just Spent a Quarter Billion Dollars on Intel Calls, synced 2026-07-27)
  - "NotebookLM source a004ba9e-958e-4318-b9b3-13b06c66a604" (😱🚀 말만 했는데 ComfyUI가 알아서 움직입니다 #soylab #컴피, synced 2026-07-27)
  - "NotebookLM source c9dce235-3a94-468c-8ead-a51687709d3a" (The Invisible Bloat Ruining Our Computers, synced 2026-07-27)
  - "NotebookLM source d4acb125-351f-4c1d-85d1-7bb76db659e1" (Qwen Image 3 Released , synced 2026-07-27)
  - "NotebookLM source e329280d-94dc-40cc-817d-71b47481368b" (A Hospital's 'Paid Day Off' Email Was Actually a Trap, synced 2026-07-27)
  - "NotebookLM source ef38cc9e-8358-414f-980b-8a911ca694cf" (XREAL AURA: This Shouldn't Be Possible in Glasses, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: prismml-bonsai-27b-model
    - level: notebook
      id: 917784eb-ef7d-40e5-b823-7bd74c2bc9bd
      title: WL: Multi-Agent Orchestration
      url: https://notebooklm.google.com/notebook/917784eb-ef7d-40e5-b823-7bd74c2bc9bd
    - level: cluster
      id: 2
      name: image-prismml-model
relations:
  - target: wiki/concepts/quantization-aware-training.md
    type: related
  - target: wiki/concepts/mobile-ai-deployment.md
    type: related
  - target: wiki/concepts/ternary-weight-networks.md
    type: related
---

# PrismML Bonsai 27B Model

## Decision context

**Definition:** Bonsai 27B is a compressed large language model developed by Caltech spinout PrismML, representing an Alibaba Qwen 3.6 27B backbone reduced to under 4 GB through aggressive quantization techniques, enabling local execution on mobile devices without cloud infrastructure.

Synthesized from **9 contributing transcripts** in NotebookLM notebook *WL: Multi-Agent Orchestration*, clustered into the "image-prismml-model" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The original FP16 Apache-licensed Qwen 3.6 27B backbone weighs approximately 54 GB in its uncompressed form [1]
- PrismML offers two compressed builds: a Ternary build near 6 GB and a 1-bit build at 3.9 GB [1]
- Quantizing trained 16-bit weights to 2 values causes quality to crater; at 4 bits the damage is tolerable; at 1 bit the model loses nearly everything the training run learned [1]
- Naive quantization at extreme compression depths does not shrink models—it lobotomizes them due to information loss [1]
- The 1-bit approach constrains weights to -1, 0, and +1 values [1]
- With weights restricted to -1, 0, and +1, matrix multiplication no longer requires multiplication operations—every term becomes addition [1]
- PrismML is based in Pasadena, California and emerged from Caltech researchers with backing from Kosal Ventures, Cberus, Google, and ongoing Samsung support [2]
- The model is marketed as the first 27B class model capable of running on a phone without GPU or cloud dependencies [2]

## Verifiable values

| Name | Value |
|---|---|
| Original FP16 model size | `54 GB` |
| Ternary compressed build size | `~6 GB` |
| 1-bit compressed build size | `3.9 GB` |
| Base model architecture | `Alibaba Qwen 3.6 27B` |
| Quantization bit depths tested | `1-bit, 4-bit, 16-bit` |
| Weight constraint values (1-bit) | `-1, 0, +1` |

## Related concepts

- quantization-aware-training — Quantization-aware training
- mobile-ai-deployment — Mobile AI deployment
- ternary-weight-networks — Ternary weight networks

## Citations (from contributing transcripts)

- **Claim:** 54 GB crushed to 3.9 GB, with two builds: Ternary near 6 GB and 1-bit at 3.9 GB
  - Source: Bonsai 27B Fact Checking PrismML's Biggest Claims (`3b213f2c-f30f-4db6-8a00-ba4ab3361df2`)
  - Context: 54 GB crushed to 3.9 prism ML calls the result the first 27B model on a phone
- **Claim:** At 1-bit quantization, the model loses nearly everything the training run learned
  - Source: Bonsai 27B Fact Checking PrismML's Biggest Claims (`3b213f2c-f30f-4db6-8a00-ba4ab3361df2`)
  - Context: at one bit you've thrown away almost everything the training run learned naive quantization at this depth doesn't shrink models it lobbotomizes them
- **Claim:** Constraining weights to -1, 0, and +1 eliminates the need for multiplication in matrix operations
  - Source: Bonsai 27B Fact Checking PrismML's Biggest Claims (`3b213f2c-f30f-4db6-8a00-ba4ab3361df2`)
  - Context: constrain weights to minus1 0 and + one and matrix multiplication stops needing multiplication every term becomes add
- **Claim:** PrismML is a Caltech spinout with backing from Kosal Ventures, Cberus, Google, and Samsung support
  - Source: PrismML Just Launched A 27B Phone AI Model (`547652f6-637b-4663-b6bd-1aff544b3820`)
  - Context: they came out of a team of Caltech researchers with backing from Kosal Ventures Cberus Google and ongoing support from Samsung
- **Claim:** The base model is Alibaba's Qwen 3.6 27B backbone released under Apache license in FP16
  - Source: Bonsai 27B Fact Checking PrismML's Biggest Claims (`3b213f2c-f30f-4db6-8a00-ba4ab3361df2`)
  - Context: Alibaba's Quen 3.627B backbone Apache licensed in FP16

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `917784eb-ef7d-40e5-b823-7bd74c2bc9bd`
(cluster `image-prismml-model`). No claims are made
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

- NotebookLM notebook [WL: Multi-Agent Orchestration](https://notebooklm.google.com/notebook/917784eb-ef7d-40e5-b823-7bd74c2bc9bd)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
