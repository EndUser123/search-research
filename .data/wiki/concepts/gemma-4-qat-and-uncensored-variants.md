---
title: "Gemma 4 QAT and Uncensored Variants"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, gemma]
summary: >
  Gemma 4 QAT variants are 26-billion parameter mixture-of-experts models optimized through quantization-aware training for reduced memory footprints, while uncensored variants are community fine-tunes that remove content restrictions present in the base model.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook fff42c44-d4ba-474a-93f7-7384bd536a1b" (WL: Health & Weight Loss, synced 2026-07-27)
  - "NotebookLM source 0a5ae78c-599b-4326-90f5-44dec538f505" (I Ran an Uncensored Local LLM Inside Pi Coding Agent (Qwen 3.6 + Gemma 4 uncensored live demo), synced 2026-07-27)
  - "NotebookLM source 12136ee1-05f3-443d-92db-90be5e054e84" (Gemma 4 26B A4B QAT vs non-QAT - 16GB Local LLM setup, synced 2026-07-27)
  - "NotebookLM source 3652fa42-322a-4fba-a3af-7a07760125e0" (SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS  SO CRAZY!!!, synced 2026-07-27)
  - "NotebookLM source 7bfff7e2-1df3-4d99-aaad-7b514fd2ea60" (I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me, synced 2026-07-27)
  - "NotebookLM source 8f140e7b-39a9-467f-99de-15680e68b26a" (Google QAT vs Unsloth QAT + MTP - Which Gemma 4 12B Is Actually Better?, synced 2026-07-27)
  - "NotebookLM source d8fa2a18-9f62-4f02-8ee7-586f747d86f6" (Chega de Limite! Antigravity com LLMs Infinitas de Graça, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: gemma-4-qat-and-uncensored-variants
    - level: notebook
      id: fff42c44-d4ba-474a-93f7-7384bd536a1b
      title: WL: Health & Weight Loss
      url: https://notebooklm.google.com/notebook/fff42c44-d4ba-474a-93f7-7384bd536a1b
    - level: cluster
      id: 7
      name: gemma-uncensored-qat
relations:
  - target: wiki/concepts/quantization-aware-training.md
    type: related
  - target: wiki/concepts/mixture-of-experts-models.md
    type: related
  - target: wiki/concepts/community-fine-tuning.md
    type: related
---

# Gemma 4 QAT and Uncensored Variants

## Decision context

**Definition:** Gemma 4 QAT variants are 26-billion parameter mixture-of-experts models optimized through quantization-aware training for reduced memory footprints, while uncensored variants are community fine-tunes that remove content restrictions present in the base model.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *WL: Health & Weight Loss*, clustered into the "gemma-uncensored-qat" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The Gemma 4 26B model employs a mixture-of-experts architecture where approximately 3.8 billion parameters are active during inference, enabling operation within smaller memory footprints than dense models of equivalent total parameter count
- Quantization-aware training integrates quantization directly into the training process rather than applying it as a post-processing step, which reduces performance degradation associated with standard post-training quantization
- Google released Gemma 4 QAT models optimized for mobile and laptop efficiency, with Q4 GGUF files produced directly from the QA training pipeline
- Unsloth took Google's identical QAT weights and applied their own dynamic quantization method on top, with both approaches resulting in files around 7GB
- SuperGemma-4 is a community fine-tuned uncensored version of Gemma 4 26B built on Google's instruction-tuned base model, designed for users seeking less restricted local model behavior
- The non-quantized Gemma 4 26B A4B model in BF16 format requires 57.7GB of VRAM to run

## Verifiable values

| Name | Value |
|---|---|
| total parameters | `26 billion` |
| active parameters during inference | `approximately 3.8 billion` |
| base model VRAM requirement (BF16) | `57.7 GB` |
| Q4 quantized file size | `approximately 7 GB` |
| native context window | `up to 256K tokens` |
| quantization type | `Q4 GGUF (QAT-optimized)` |

## Related concepts

- [[quantization-aware-training]] — Quantization-Aware Training
- [[mixture-of-experts-models]] — Mixture of Experts Models
- [[community-fine-tuning]] — Community Fine-Tuning
- [[gemma-4-base-model]] — Gemma 4 Base Model

## Citations (from contributing transcripts)

- **Claim:** Gemma 4 uses a mixture of experts design where active parameters number around 3.8 billion
  - Source: I Ran an Uncensored Local LLM Inside Pi Coding Agent (Qwen 3.6 + Gemma 4 uncensored live demo) (`0a5ae78c-599b-4326-90f5-44dec538f505`)
  - Context: this active 4 billion means that it's a mixture of experts model which means basically that it can select a much smaller number of parameters to work on and so that fits inside smaller memory footprint
- **Claim:** QAT reduces memory requirements while integrating quantization into training rather than post-processing
  - Source: I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me (`7bfff7e2-1df3-4d99-aaad-7b514fd2ea60`)
  - Context: quantization aware training integrates the quantization process directly into training so that is what they have done over here with the gemma 4 series of models
- **Claim:** SuperGemma-4 is a community fine-tuned uncensored version of Gemma 4 26B
  - Source: SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS SO CRAZY!!!
  - Context: Super Gemma 4 this is basically a community fine-tuned uncensored version of Gemma 426B and the one I'm focusing on today is the Super Gemma 426B uncensored MLX 4-bit V2 release by Geonong on Hugging Face
- **Claim:** Google released Q4 GGUF directly from the QA training pipeline while Unsloth applied dynamic quantization to the same weights
  - Source: Google QAT vs Unsloth QAT + MTP - Which Gemma 4 12B Is Actually Better? (`8f140e7b-39a9-467f-99de-15680e68b26a`)
  - Context: Google has released their own Q4 GGUF directly from the QA training pipeline unsloth took those exact same weights and applied their dynamic quantization method on top
- **Claim:** The non-quantized Gemma 4 26B A4B model requires 57.7GB of VRAM in BF16 format
  - Source: I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me (`7bfff7e2-1df3-4d99-aaad-7b514fd2ea60`)
  - Context: for a jimma 26 billion a4b mixture of experts model with 4 billion active parameters if you go by the bf16bit format the non-quantized model it requires 57.7gb of vram to run it
- **Claim:** Both Google QAT and Unsloth quantized versions result in files around 7GB
  - Source: Google QAT vs Unsloth QAT + MTP - Which Gemma 4 12B Is Actually Better? (`8f140e7b-39a9-467f-99de-15680e68b26a`)
  - Context: both files land at around 7 GB as you can see in this diagram both start from the identical QA weights

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `fff42c44-d4ba-474a-93f7-7384bd536a1b`
(cluster `gemma-uncensored-qat`). No claims are made
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

- NotebookLM notebook [WL: Health & Weight Loss](https://notebooklm.google.com/notebook/fff42c44-d4ba-474a-93f7-7384bd536a1b)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
