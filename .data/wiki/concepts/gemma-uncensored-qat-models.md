---
title: "Gemma Uncensored QAT Models"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, gemma]
summary: >
  Community fine-tuned uncensored variants of Google's Gemma 4 26B mixture-of-experts models that leverage quantization-aware training (QAT) to enable local deployment on consumer hardware. These are separate fine-tunes built on the official Gemma 4 26B A4B instruction-tuned base model for users seeki
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 683781d4-4e8f-4ae0-a1d0-57a5f2c4c566" (WL: Canadian Politics & Trade, synced 2026-07-27)
  - "NotebookLM source 0a5ae78c-599b-4326-90f5-44dec538f505" (I Ran an Uncensored Local LLM Inside Pi Coding Agent (Qwen 3.6 + Gemma 4 uncensored live demo), synced 2026-07-27)
  - "NotebookLM source 12136ee1-05f3-443d-92db-90be5e054e84" (Gemma 4 26B A4B QAT vs non-QAT - 16GB Local LLM setup, synced 2026-07-27)
  - "NotebookLM source 3652fa42-322a-4fba-a3af-7a07760125e0" (SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS  SO CRAZY!!!, synced 2026-07-27)
  - "NotebookLM source 7bfff7e2-1df3-4d99-aaad-7b514fd2ea60" (I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me, synced 2026-07-27)
  - "NotebookLM source 8f140e7b-39a9-467f-99de-15680e68b26a" (Google QAT vs Unsloth QAT + MTP - Which Gemma 4 12B Is Actually Better?, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: gemma-uncensored-qat-models
    - level: notebook
      id: 683781d4-4e8f-4ae0-a1d0-57a5f2c4c566
      title: WL: Canadian Politics & Trade
      url: https://notebooklm.google.com/notebook/683781d4-4e8f-4ae0-a1d0-57a5f2c4c566
    - level: cluster
      id: 7
      name: gemma-uncensored-qat
relations:
  - target: wiki/concepts/google-gemma-4-qat.md
    type: related
  - target: wiki/concepts/supergemma-4.md
    type: related
  - target: wiki/concepts/mixture-of-experts.md
    type: related
---

# Gemma Uncensored QAT Models

## Decision context

**Definition:** Community fine-tuned uncensored variants of Google's Gemma 4 26B mixture-of-experts models that leverage quantization-aware training (QAT) to enable local deployment on consumer hardware. These are separate fine-tunes built on the official Gemma 4 26B A4B instruction-tuned base model for users seeking less restricted local model capabilities.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *WL: Canadian Politics & Trade*, clustered into the "gemma-uncensored-qat" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The base Gemma 4 26B A4B model utilizes a mixture-of-experts architecture where approximately 3.8-4 billion parameters are active during inference, enabling operation within smaller memory footprints
- Google's official QAT models integrate quantization directly into the training process rather than applying it post-training, which helps reduce performance degradation compared to standard post-training quantization
- Community uncensored variants like SuperGemma-4 represent fine-tunes of the official Gemma 4 26B A4B instruction-tuned model, not official Google releases
- The QAT approach allows the 26B parameter model to run in approximately 24GB of RAM or 16GB VRAM setups, compared to the 57.7GB VRAM required for the non-quantized bf16 version
- Quantization reduces memory footprint while accelerating decode speed, though standard post-training quantization typically causes performance degradation unlike QAT
- The models support native system prompt support, function calling, and context windows up to 256K tokens
- Google has released their own Q4 GGUF directly from the QAT training pipeline, while other quantization providers like Unsloth apply dynamic quantization methods to the same QAT-optimized weights

## Verifiable values

| Name | Value |
|---|---|
| total parameters | `26 billion` |
| active parameters (MoE) | `3.8-4 billion` |
| context length | `up to 256K tokens` |
| bf16 VRAM requirement | `57.7GB` |
| QAT VRAM requirement | `approximately 24GB` |
| quantization bit depth | `4-bit (Q4)` |

## Related concepts

- google-gemma-4-qat — Google Gemma 4 QAT
- supergemma-4 — SuperGemma-4
- mixture-of-experts — Mixture of Experts
- quantization-aware-training — Quantization Aware Training
- local-llm-deployment — Local LLM Deployment

## Citations (from contributing transcripts)

- **Claim:** Community uncensored variants are separate fine-tunes built on the official Gemma 4 26B A4B instruction-tuned model
  - Source: SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS SO CRAZY!!!
  - Context: this is basically a community fine-tuned uncensored version of Gemma 4 26B and the one I'm focusing on today is the Super Gemma 4 26B uncensored MLX 4-bit V2 release by Geonong on Hugging Face so to be very clear this is not an official Google release the base model is Google's Gemma 4 26B A4B instruction tuned model but this version is a separate fine-tune built for people who want a less restricted local model
- **Claim:** The mixture-of-experts design activates approximately 3.8-4 billion parameters during inference
  - Source: SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS SO CRAZY!!!
  - Context: mixture of experts design where only around 3.8 billion parameters are active during inference even t
- **Claim:** QAT integrates quantization into training rather than applying it post-training
  - Source: I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me (`7bfff7e2-1df3-4d99-aaad-7b514fd2ea60`)
  - Context: instead of simply quantizing the model after training quantization aware training integrates the quantization process directly into training so that is what they have done over here with the gemma 4 series of models
- **Claim:** The non-quantized bf16 Gemma 4 26B A4B requires 57.7GB VRAM
  - Source: I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me (`7bfff7e2-1df3-4d99-aaad-7b514fd2ea60`)
  - Context: if you go by the bf16bit format the non-quantized model it requires 57.7gb of vram to run it
- **Claim:** QAT allows the 26B model to run in approximately 24GB RAM
  - Source: I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me (`7bfff7e2-1df3-4d99-aaad-7b514fd2ea60`)
  - Context: i was surprised that i could run a 26 billion parameter model in just 24 gb of ram
- **Claim:** The official model supports up to 256K context and includes function calling capability
  - Source: SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS SO CRAZY!!!
  - Context: function calling up to 256K context and that mixture of experts design
- **Claim:** Google released Q4 GGUF directly from their QAT training pipeline
  - Source: Google QAT vs Unsloth QAT + MTP - Which Gemma 4 12B Is Actually Better? (`8f140e7b-39a9-467f-99de-15680e68b26a`)
  - Context: Google has released their own Q4 GGUF directly from the QA training pipeline unsloth took those exact same weights and applied their dynamic quantization method on top

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `683781d4-4e8f-4ae0-a1d0-57a5f2c4c566`
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

- NotebookLM notebook [WL: Canadian Politics & Trade](https://notebooklm.google.com/notebook/683781d4-4e8f-4ae0-a1d0-57a5f2c4c566)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
