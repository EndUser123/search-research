---
title: "Gemma 4 Uncensored and Quantization Methods"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, gemma]
summary: >
  Gemma 4 uncensored refers to community fine-tuned versions of Google's Gemma 4 26B parameter mixture-of-experts model that remove content restrictions, while quantization-aware training (QAT) is Google's approach to reducing memory requirements for local deployment without significant quality degrad
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook af7b9263-fd59-4b81-9746-2bc4ad0c82a2" (
          I Found OpenAI’s $3B Loophole
        , synced 2026-07-27)
  - "NotebookLM source 0a5ae78c-599b-4326-90f5-44dec538f505" (I Ran an Uncensored Local LLM Inside Pi Coding Agent (Qwen 3.6 + Gemma 4 uncensored live demo), synced 2026-07-27)
  - "NotebookLM source 12136ee1-05f3-443d-92db-90be5e054e84" (Gemma 4 26B A4B QAT vs non-QAT - 16GB Local LLM setup, synced 2026-07-27)
  - "NotebookLM source 3652fa42-322a-4fba-a3af-7a07760125e0" (SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS  SO CRAZY!!!, synced 2026-07-27)
  - "NotebookLM source 7bfff7e2-1df3-4d99-aaad-7b514fd2ea60" (I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me, synced 2026-07-27)
  - "NotebookLM source 7d3f92c1-fcb9-4bf6-8328-629bf692c507" (Gemma 4 Was Broken for Agents - Google Just Fixed It, synced 2026-07-27)
  - "NotebookLM source 8f140e7b-39a9-467f-99de-15680e68b26a" (Google QAT vs Unsloth QAT + MTP - Which Gemma 4 12B Is Actually Better?, synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: gemma-4-uncensored-and-quantization-methods
    - level: notebook
      id: af7b9263-fd59-4b81-9746-2bc4ad0c82a2
      title: 
          I Found OpenAI’s $3B Loophole
        
      url: https://notebooklm.google.com/notebook/af7b9263-fd59-4b81-9746-2bc4ad0c82a2
    - level: cluster
      id: 6
      name: gemma-google-uncensored
relations:
  - target: wiki/concepts/quantization-aware-training.md
    type: related
  - target: wiki/concepts/mixture-of-experts-architecture.md
    type: related
  - target: wiki/concepts/local-llm-deployment.md
    type: related
---

# Gemma 4 Uncensored and Quantization Methods

## Decision context

**Definition:** Gemma 4 uncensored refers to community fine-tuned versions of Google's Gemma 4 26B parameter mixture-of-experts model that remove content restrictions, while quantization-aware training (QAT) is Google's approach to reducing memory requirements for local deployment without significant quality degradation.

Synthesized from **6 contributing transcripts** in NotebookLM notebook *
          I Found OpenAI’s $3B Loophole
        *, clustered into the "gemma-google-uncensored" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Gemma 4 26B utilizes a mixture-of-experts architecture where approximately 3.8 billion parameters are active during inference, allowing the model to operate within a smaller memory footprint than its full parameter count would suggest
- The non-quantized Gemma 4 26B model in bf16 format requires approximately 57.7GB of VRAM to run, making it inaccessible for most consumer hardware
- Quantization-aware training integrates the quantization process directly into training rather than applying post-training quantization, reducing performance degradation compared to standard approaches
- SuperGemma-4 is a community fine-tuned uncensored version built on Google's Gemma 4 26B A4B instruction-tuned model, designed for users seeking a less restricted local model experience
- Google has released official QAT versions optimized for mobile and laptop efficiency, with 4-bit quantized variants requiring significantly less memory
- The model supports native system prompt support, function calling up to 256K context, and is available in both official Google releases and community fine-tuned variants
- Issues with official chat templates have been identified as affecting multi-turn and agentic performance, with Google releasing fixes to address these problems

## Verifiable values

| Name | Value |
|---|---|
| Model Parameters | `26 billion` |
| Active Parameters (MoE) | `~3.8 billion` |
| VRAM Requirement (bf16) | `57.7 GB` |
| Quantization Format | `4-bit (Q4)` |
| Maximum Context Length | `256K tokens` |
| Typical RAM for Local Deployment | `16-24 GB` |

## Related concepts

- quantization-aware-training — Quantization Aware Training
- mixture-of-experts-architecture — Mixture of Experts Architecture
- local-llm-deployment — Local LLM Deployment
- community-fine-tuning — Community Fine-tuning
- chat-templates — Chat Templates

## Citations (from contributing transcripts)

- **Claim:** Gemma 4 26B uses a mixture of experts design where only around 3.8 billion parameters are active during inference
  - Source: SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS SO CRAZY!!!
  - Context: that mixture of experts design where only around 3.8 billion parameters are active during inference
- **Claim:** The non-quantized model requires 57.7GB of VRAM to run
  - Source: I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me (`7bfff7e2-1df3-4d99-aaad-7b514fd2ea60`)
  - Context: if you go by the bf16bit format the non-quantized model it requires 57.7gb of vram to run it
- **Claim:** Quantization-aware training integrates quantization directly into training to reduce performance degradation
  - Source: I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me (`7bfff7e2-1df3-4d99-aaad-7b514fd2ea60`)
  - Context: quantization aware training integrates the quantization process directly into training so that is what they have done over here with the gemma 4 series of models
- **Claim:** SuperGemma-4 is a community fine-tuned uncensored version of Gemma 4 26B
  - Source: SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS SO CRAZY!!!
  - Context: this is basically a community fine-tuned uncensored version of Gemma 426B
- **Claim:** Google released QAT models optimized for mobile and laptop efficiency
  - Source: I Ran Gemma 4 26B A4B QAT on a Laptop… The Results Shocked Me (`7bfff7e2-1df3-4d99-aaad-7b514fd2ea60`)
  - Context: google has released gemma 4 qat models now these models are optimized for mobile and laptop efficiency
- **Claim:** Issues with official chat templates were affecting multi-turn and agentic performance
  - Source: Gemma 4 Was Broken for Agents - Google Just Fixed It (`7d3f92c1-fcb9-4bf6-8328-629bf692c507`)
  - Context: there was a real problem sitting quietly in the official chat template that was hurting multi-turn and agentic performance
- **Claim:** The model supports function calling up to 256K context
  - Source: SuperGemma-4 (26B) UNCENSORED + Hermes,OpenClaw,OpenCode: THIS IS SO CRAZY!!!
  - Context: function calling up to 256K context

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `af7b9263-fd59-4b81-9746-2bc4ad0c82a2`
(cluster `gemma-google-uncensored`). No claims are made
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

- NotebookLM notebook [
          I Found OpenAI’s $3B Loophole
        ](https://notebooklm.google.com/notebook/af7b9263-fd59-4b81-9746-2bc4ad0c82a2)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
