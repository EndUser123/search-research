---
title: "GGUF Quantization for Large Language Models"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  GGUF (GPT-Generated Unified Format) is a quantized model format that enables efficient storage and inference of large language models by reducing model file sizes while preserving significant model capability, supported across platforms including Hugging Face, llama.cpp, and Unsloth.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 831e0613-f723-4d87-aaeb-1d4b5a061496" (Maximizing LLM Performance and Context via GPU Memory Optimization, synced 2026-07-28)
  - "Unsloth Dynamic 2.0 GGUFs" (https://unsloth.ai/docs/basics/unsloth-dynamic-2.0-ggufs, transcript synced 2026-07-28)
  - "AetherArchitectural/Community-Discussions · [llama.cpp PR#7527] GGUF Quantized KV Support - Hugging Face" (https://huggingface.co/AetherArchitectural/Community-Discussions/discussions/15, transcript synced 2026-07-28)
  - "DavidAU/Qwen3.5-9B-Claude-4.6-HighIQ-THINKING-HERETIC-UNCENSORED" (https://huggingface.co/DavidAU/Qwen3.5-9B-Claude-4.6-HighIQ-THINKING-HERETIC-UNCENSORED, transcript synced 2026-07-28)
  - "AtomicChat/ornith-9b-GGUF - Hugging Face" (https://huggingface.co/AtomicChat/ornith-9b-GGUF, transcript synced 2026-07-28)
  - "Qwen/Qwen2.5-VL-7B-Instruct - Hugging Face" (https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct, transcript synced 2026-07-28)
  - "KikoCis/Ornith-1.0-9B-Ollama-fixed-GGUF - Hugging Face" (https://huggingface.co/KikoCis/Ornith-1.0-9B-Ollama-fixed-GGUF, transcript synced 2026-07-28)
  - "Mungert/Qwen2.5-VL-32B-Instruct-GGUF - Hugging Face" (https://huggingface.co/Mungert/Qwen2.5-VL-32B-Instruct-GGUF, transcript synced 2026-07-28)
  - "usermma/Ornith-1.0-9B-OBLITERATED - Hugging Face" (https://huggingface.co/usermma/Ornith-1.0-9B-OBLITERATED, transcript synced 2026-07-28)
  - "Unsloth Dynamic 2.0 Quants - Hugging Face" (https://huggingface.co/collections/unsloth/unsloth-dynamic-20-quants, transcript synced 2026-07-28)
  - "bartowski/Qwen_Qwen2.5-VL-7B-Instruct-GGUF - Hugging Face" (https://huggingface.co/bartowski/Qwen_Qwen2.5-VL-7B-Instruct-GGUF, transcript synced 2026-07-28)
  - "Smoffyy/Qwen3.5-9B-Instruct-Pure-GGUF - Hugging Face" (https://huggingface.co/Smoffyy/Qwen3.5-9B-Instruct-Pure-GGUF?local-app=pi, transcript synced 2026-07-28)
  - "Qwen/Qwen3.5-9B - Hugging Face" (https://huggingface.co/Qwen/Qwen3.5-9B, transcript synced 2026-07-28)
  - "DeepReinforce Releases Ornith-1.0: An Open-Source Coding Model Family That Learns Its Own RL Scaffolds - MarkTechPost" (https://www.marktechpost.com/2026/06/25/deepreinforce-releases-ornith-1-0-an-open-source-coding-model-family-that-learns-its-own-rl-scaffolds/, transcript synced 2026-07-28)
  - "Kimi K2.6 - How to Run Locally | Unsloth Documentation" (https://unsloth.ai/docs/models/kimi-k2.6, transcript synced 2026-07-28)
  - "bartowski/Qwen_Qwen2.5-VL-32B-Instruct-GGUF - Hugging Face" (https://huggingface.co/bartowski/Qwen_Qwen2.5-VL-32B-Instruct-GGUF, transcript synced 2026-07-28)
  - "SC117/Ornith-1.0-9B-heretic-MTP - Hugging Face" (https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP, transcript synced 2026-07-28)
  - "Qwen Image and Edit: Local GGUF Generations with Lightning - sandner.art" (https://sandner.art/qwen-image-and-edit-local-gguf-generations-with-lightning/, transcript synced 2026-07-28)
  - "protoLabsAI/Ornith-1.0-9B-MTP-GGUF - Hugging Face" (https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF, transcript synced 2026-07-28)
  - "Haven VLM Connector - Plugins - Stash Forum" (https://discourse.stashapp.cc/t/haven-vlm-connector/5464, transcript synced 2026-07-28)
  - "mmproj-BF16.gguf · unsloth/Qwen2.5-VL-7B-Instruct-GGUF at main - Hugging Face" (https://huggingface.co/unsloth/Qwen2.5-VL-7B-Instruct-GGUF/blob/main/mmproj-BF16.gguf, transcript synced 2026-07-28)
  - "Qwen3.5 & Qwen3.6 Usage Guide - vLLM Recipes" (https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3.5.html, transcript synced 2026-07-28)
  - "Mungert/Qwen2.5-VL-3B-Instruct-GGUF - Hugging Face" (https://huggingface.co/Mungert/Qwen2.5-VL-3B-Instruct-GGUF, transcript synced 2026-07-28)
  - "KoboldCpp Inference - RWKV Language Model" (https://wiki.rwkv.com/inference/koboldcpp.html, transcript synced 2026-07-28)
  - "deepreinforce-ai/Ornith-1.0-397B-FP8 - Hugging Face" (https://huggingface.co/deepreinforce-ai/Ornith-1.0-397B-FP8, transcript synced 2026-07-28)
  - "Qwen2.5-VL-7B-Instruct download | SourceForge.net" (https://sourceforge.net/projects/qwen2-5-vl-7b-instruct/, transcript synced 2026-07-28)
  - "Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf - Hugging Face" (https://huggingface.co/Mungert/Qwen2.5-VL-7B-Instruct-GGUF/blob/main/Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf, transcript synced 2026-07-28)
  - "Qwen3.5 - How to Run Locally | Unsloth Documentation" (https://unsloth.ai/docs/models/qwen3.5, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: gguf-quantization-for-large-language-models
    - level: notebook
      id: 831e0613-f723-4d87-aaeb-1d4b5a061496
      title: Maximizing LLM Performance and Context via GPU Memory Optimization
      url: https://notebooklm.google.com/notebook/831e0613-f723-4d87-aaeb-1d4b5a061496
    - level: cluster
      id: 1
      name: https-huggingface-hugging
    - level: source_url
      url: https://unsloth.ai/docs/basics/unsloth-dynamic-2.0-ggufs
      title: Unsloth Dynamic 2.0 GGUFs
    - level: source_url
      url: https://huggingface.co/AetherArchitectural/Community-Discussions/discussions/15
      title: AetherArchitectural/Community-Discussions · [llama.cpp PR#7527] GGUF Quantized KV Support - Hugging Face
    - level: source_url
      url: https://huggingface.co/DavidAU/Qwen3.5-9B-Claude-4.6-HighIQ-THINKING-HERETIC-UNCENSORED
      title: DavidAU/Qwen3.5-9B-Claude-4.6-HighIQ-THINKING-HERETIC-UNCENSORED
    - level: source_url
      url: https://huggingface.co/AtomicChat/ornith-9b-GGUF
      title: AtomicChat/ornith-9b-GGUF - Hugging Face
    - level: source_url
      url: https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct
      title: Qwen/Qwen2.5-VL-7B-Instruct - Hugging Face
    - level: source_url
      url: https://huggingface.co/KikoCis/Ornith-1.0-9B-Ollama-fixed-GGUF
      title: KikoCis/Ornith-1.0-9B-Ollama-fixed-GGUF - Hugging Face
    - level: source_url
      url: https://huggingface.co/Mungert/Qwen2.5-VL-32B-Instruct-GGUF
      title: Mungert/Qwen2.5-VL-32B-Instruct-GGUF - Hugging Face
    - level: source_url
      url: https://huggingface.co/usermma/Ornith-1.0-9B-OBLITERATED
      title: usermma/Ornith-1.0-9B-OBLITERATED - Hugging Face
    - level: source_url
      url: https://huggingface.co/collections/unsloth/unsloth-dynamic-20-quants
      title: Unsloth Dynamic 2.0 Quants - Hugging Face
    - level: source_url
      url: https://huggingface.co/bartowski/Qwen_Qwen2.5-VL-7B-Instruct-GGUF
      title: bartowski/Qwen_Qwen2.5-VL-7B-Instruct-GGUF - Hugging Face
    - level: source_url
      url: https://huggingface.co/Smoffyy/Qwen3.5-9B-Instruct-Pure-GGUF?local-app=pi
      title: Smoffyy/Qwen3.5-9B-Instruct-Pure-GGUF - Hugging Face
    - level: source_url
      url: https://huggingface.co/Qwen/Qwen3.5-9B
      title: Qwen/Qwen3.5-9B - Hugging Face
    - level: source_url
      url: https://www.marktechpost.com/2026/06/25/deepreinforce-releases-ornith-1-0-an-open-source-coding-model-family-that-learns-its-own-rl-scaffolds/
      title: DeepReinforce Releases Ornith-1.0: An Open-Source Coding Model Family That Learns Its Own RL Scaffolds - MarkTechPost
    - level: source_url
      url: https://unsloth.ai/docs/models/kimi-k2.6
      title: Kimi K2.6 - How to Run Locally | Unsloth Documentation
    - level: source_url
      url: https://huggingface.co/bartowski/Qwen_Qwen2.5-VL-32B-Instruct-GGUF
      title: bartowski/Qwen_Qwen2.5-VL-32B-Instruct-GGUF - Hugging Face
    - level: source_url
      url: https://huggingface.co/SC117/Ornith-1.0-9B-heretic-MTP
      title: SC117/Ornith-1.0-9B-heretic-MTP - Hugging Face
    - level: source_url
      url: https://sandner.art/qwen-image-and-edit-local-gguf-generations-with-lightning/
      title: Qwen Image and Edit: Local GGUF Generations with Lightning - sandner.art
    - level: source_url
      url: https://huggingface.co/protoLabsAI/Ornith-1.0-9B-MTP-GGUF
      title: protoLabsAI/Ornith-1.0-9B-MTP-GGUF - Hugging Face
    - level: source_url
      url: https://discourse.stashapp.cc/t/haven-vlm-connector/5464
      title: Haven VLM Connector - Plugins - Stash Forum
    - level: source_url
      url: https://huggingface.co/unsloth/Qwen2.5-VL-7B-Instruct-GGUF/blob/main/mmproj-BF16.gguf
      title: mmproj-BF16.gguf · unsloth/Qwen2.5-VL-7B-Instruct-GGUF at main - Hugging Face
    - level: source_url
      url: https://docs.vllm.ai/projects/recipes/en/latest/Qwen/Qwen3.5.html
      title: Qwen3.5 & Qwen3.6 Usage Guide - vLLM Recipes
    - level: source_url
      url: https://huggingface.co/Mungert/Qwen2.5-VL-3B-Instruct-GGUF
      title: Mungert/Qwen2.5-VL-3B-Instruct-GGUF - Hugging Face
    - level: source_url
      url: https://wiki.rwkv.com/inference/koboldcpp.html
      title: KoboldCpp Inference - RWKV Language Model
    - level: source_url
      url: https://huggingface.co/deepreinforce-ai/Ornith-1.0-397B-FP8
      title: deepreinforce-ai/Ornith-1.0-397B-FP8 - Hugging Face
    - level: source_url
      url: https://sourceforge.net/projects/qwen2-5-vl-7b-instruct/
      title: Qwen2.5-VL-7B-Instruct download | SourceForge.net
    - level: source_url
      url: https://huggingface.co/Mungert/Qwen2.5-VL-7B-Instruct-GGUF/blob/main/Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf
      title: Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf - Hugging Face
    - level: source_url
      url: https://unsloth.ai/docs/models/qwen3.5
      title: Qwen3.5 - How to Run Locally | Unsloth Documentation
relations:
  - target: wiki/concepts/llama.cpp.md
    type: related
  - target: wiki/concepts/unsloth-dynamic-quantization.md
    type: related
  - target: wiki/concepts/model-quantization-techniques.md
    type: related
---

# GGUF Quantization for Large Language Models

## Decision context

**Definition:** GGUF (GPT-Generated Unified Format) is a quantized model format that enables efficient storage and inference of large language models by reducing model file sizes while preserving significant model capability, supported across platforms including Hugging Face, llama.cpp, and Unsloth.

Synthesized from **27 contributing transcripts** in NotebookLM notebook *Maximizing LLM Performance and Context via GPU Memory Optimization*, clustered into the "https-huggingface-hugging" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- GGUF format is used by llama.cpp for model quantization, with community members creating quantized versions of models such as Qwen2.5-VL in various sizes (3B, 7B, 32B parameters) and quantization levels (e.g., imatrix quantizations using llama.cpp release b5317)
- Unsloth Dynamic 2-bit quantization achieves substantial size reduction, as demonstrated by Kimi K2.6 which requires 610GB at full precision but only 350GB with Dynamic 2-bit (a 43% reduction)
- GGUF model files are distributed through Hugging Face repositories, with organizations like bartowski, Mungert, and KikoCis providing community quantizations
- The llama.cpp project implements GGUF quantized KV cache support according to community discussions and pull requests (e.g., PR #7527)
- Quantized GGUF models support multimodal capabilities when paired with corresponding mmproj files (e.g., Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf)
- Models quantized in GGUF format can run locally through Unsloth Studio or llama.cpp-based inference engines

## Verifiable values

| Name | Value |
|---|---|
| Kimi K2.6 Full Precision Disk Space | `610 GB` |
| Kimi K2.6 Dynamic 2-bit Size | `350 GB` |
| Kimi K2.6 Size Reduction | `43%` |
| Kimi K2.6 Context Length | `256K tokens` |

## Related concepts

- [[llama.cpp]] — llama.cpp
- [[unsloth-dynamic-quantization]] — Unsloth Dynamic Quantization
- [[model-quantization-techniques]] — Model Quantization Techniques
- [[hugging-face-model-hub]] — Hugging Face Model Hub
- [[vision-language-models]] — Vision-Language Models

## Citations (from contributing transcripts)

- **Claim:** GGUF format is used by llama.cpp for model quantization with community quantizations available
  - Source: bartowski/Qwen_Qwen2.5-VL-7B-Instruct-GGUF - Hugging Face (`6710c093-6d91-4744-9aed-fec0fef6a28b`)
  - Context: Llamacpp imatrix Quantizations of Qwen2.5-VL-7B-Instruct by Qwen Using llama.cpp release b5317 for quantization
- **Claim:** Unsloth Dynamic 2-bit achieves 43% size reduction (350GB from 610GB)
  - Source: Kimi K2.6 - How to Run Locally | Unsloth Documentation (`8e6b1e90-9286-4519-91c3-9854d5ed8548`)
  - Context: full precision requires 610GB of disk space Dynamic 2-bit requires 350GB (-43% size)
- **Claim:** GGUF models are distributed through Hugging Face with community quantizations
  - Source: Mungert/Qwen2.5-VL-32B-Instruct-GGUF - Hugging Face (`59df647f-24ea-4c01-949d-348c1caaccfa`)
  - Context: Llamacpp imatrix Quantizations of Qwen2.5-VL-32B-Instruct by Qwen Using llama.cpp release b5284 for quantization
- **Claim:** llama.cpp implements GGUF quantized KV cache support
  - Source: AetherArchitectural/Community-Discussions · [llama.cpp PR#7527] GGUF Quantized KV Support - Hugging Face (`14215b96-6c73-443e-92ef-8f49f1ec6107`)
  - Context: GGUF Quantized KV Support
- **Claim:** GGUF supports multimodal models with mmproj files
  - Source: Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf - Hugging Face (`f5b94290-0583-4d90-a486-472039ae7cfd`)
  - Context: Qwen2.5-VL-7B-Instruct-mmproj-f16.gguf

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `831e0613-f723-4d87-aaeb-1d4b5a061496`
(cluster `https-huggingface-hugging`). No claims are made
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
